"""
图片导出服务
支持PNG和JPG格式的BeatBoard导出
增强功能：联系表导出、按场次分组、ZIP打包
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
import zipfile
import os
import math
from datetime import datetime
from sqlalchemy.orm import Session

from PIL import Image, ImageDraw, ImageFont

from database import Project, Beat, ExportHistory


class ImageExporter:
    """图片导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
    async def export_beatboard_image(
        self,
        project_id: str,
        format: str = "png",
        width: int = 1920,
        height: int = 1080,
        quality: int = 95,
        beat_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """导出BeatBoard为图片"""
        try:
            # 加载项目数据
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "message": "项目不存在"}
            
            # 加载Beat数据
            if beat_ids:
                beats = self.db.query(Beat).filter(
                    Beat.project_id == project_id,
                    Beat.id.in_(beat_ids)
                ).order_by(Beat.order_index).all()
            else:
                beats = self.db.query(Beat).filter(
                    Beat.project_id == project_id
                ).order_by(Beat.order_index).all()
            
            if not beats:
                return {"status": "error", "message": "没有找到Beat数据"}
            
            # 创建图片
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            try:
                title_font = ImageFont.truetype("msyh.ttc", 48)
                heading_font = ImageFont.truetype("msyh.ttc", 32)
                body_font = ImageFont.truetype("msyh.ttc", 24)
                small_font = ImageFont.truetype("msyh.ttc", 18)
            except:
                title_font = ImageFont.load_default()
                heading_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # 绘制标题
            title_text = project.title
            draw.text((width//2, 60), title_text, fill='#fbbf24', font=title_font, anchor='mm')
            
            # 计算Beat卡片布局
            beat_width = 500
            beat_height = 280
            margin = 40
            cols = 3
            
            # 绘制Beat卡片
            for i, beat in enumerate(beats):
                row = i // cols
                col = i % cols
                
                x = margin + col * (beat_width + margin)
                y = 150 + row * (beat_height + margin)
                
                # 绘制卡片背景
                draw.rectangle([x, y, x + beat_width, y + beat_height], 
                             fill='#2d2d2d', outline='#fbbf24', width=2)
                
                # Beat标题
                beat_title = f"Beat {beat.order_index + 1}"
                draw.text((x + 20, y + 20), beat_title, fill='#f3f4f6', font=heading_font)
                
                # Beat内容（截取前50个字符）
                content = beat.content[:50] + "..." if beat.content and len(beat.content) > 50 else beat.content or ""
                draw.text((x + 20, y + 70), content, fill='#d1d5db', font=body_font)
                
                # 时长
                if beat.duration:
                    draw.text((x + 20, y + 105), f"时长: {beat.duration}秒", 
                            fill='#d1d5db', font=body_font)
                
                # 标签（前3个）
                all_tags = []
                if beat.emotion_tags:
                    all_tags.extend(beat.emotion_tags[:2])
                if beat.scene_tags:
                    all_tags.extend(beat.scene_tags[:2])
                
                if all_tags:
                    tags_text = ", ".join(all_tags[:3])
                    if len(all_tags) > 3:
                        tags_text += "..."
                    draw.text((x + 20, y + 180), tags_text, fill='#9ca3af', font=small_font)
                
                # 情绪指示器
                if beat.emotion_tags and len(beat.emotion_tags) > 0:
                    emotion_colors = {
                        '紧张': '#f59e0b',
                        '恐惧': '#ef4444',
                        '平静': '#10b981',
                        '压迫': '#8b5cf6',
                        '决心': '#3b82f6'
                    }
                    color = '#6b7280'  # 默认颜色
                    for emotion in beat.emotion_tags:
                        if emotion in emotion_colors:
                            color = emotion_colors[emotion]
                            break
                    draw.ellipse([x + beat_width - 60, y + 20, x + beat_width - 20, y + 60], fill=color)
            
            # 保存图片
            file_format = format.lower()
            filename = f"{project_id}_beatboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"
            file_path = self.export_dir / filename
            
            if file_format == "png":
                img.save(str(file_path), 'PNG', quality=quality)
            elif file_format in ["jpg", "jpeg"]:
                img.save(str(file_path), 'JPEG', quality=quality)
            else:
                return {"status": "error", "message": f"不支持的格式: {format}"}
            
            # 记录导出历史
            export_record = ExportHistory(
                id=str(uuid.uuid4()),
                project_id=project_id,
                export_type="beatboard_image",
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_format=file_format,
                options={
                    "width": width,
                    "height": height,
                    "quality": quality,
                    "beat_count": len(beats)
                },
                status="completed",
                created_at=datetime.now()
            )
            self.db.add(export_record)
            self.db.commit()
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "width": width,
                "height": height,
                "export_id": export_record.id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"图片导出失败: {str(e)}"
            }


    async def export_contact_sheet(
        self,
        project_id: str,
        format: str = "png",
        columns: int = 4,
        thumbnail_width: int = 400,
        thumbnail_height: int = 225,
        quality: int = 95
    ) -> Dict[str, Any]:
        """
        导出联系表（Contact Sheet）
        生成包含所有镜头缩略图的单页概览图
        
        Args:
            project_id: 项目ID
            format: 输出格式 (png/jpg)
            columns: 每行镜头数
            thumbnail_width: 缩略图宽度
            thumbnail_height: 缩略图高度
            quality: 图片质量
        """
        try:
            # 加载项目数据
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "message": "项目不存在"}
            
            # 加载Beat数据
            beats = self.db.query(Beat).filter(
                Beat.project_id == project_id
            ).order_by(Beat.order_index).all()
            
            if not beats:
                return {"status": "error", "message": "没有找到Beat数据"}
            
            # 计算布局
            total_beats = len(beats)
            rows = math.ceil(total_beats / columns)
            
            margin = 20
            header_height = 100
            footer_height = 50
            
            # 计算总尺寸
            total_width = columns * thumbnail_width + (columns + 1) * margin
            total_height = header_height + rows * thumbnail_height + (rows + 1) * margin + footer_height
            
            # 创建图片
            img = Image.new('RGB', (total_width, total_height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            try:
                title_font = ImageFont.truetype("msyh.ttc", 36)
                label_font = ImageFont.truetype("msyh.ttc", 14)
                small_font = ImageFont.truetype("msyh.ttc", 12)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # 绘制标题
            title_text = f"{project.title} - 联系表"
            draw.text((total_width // 2, 50), title_text, fill='#fbbf24', font=title_font, anchor='mm')
            
            # 绘制每个Beat缩略图
            for i, beat in enumerate(beats):
                row = i // columns
                col = i % columns
                
                x = margin + col * (thumbnail_width + margin)
                y = header_height + margin + row * (thumbnail_height + margin)
                
                # 绘制缩略图背景
                draw.rectangle([x, y, x + thumbnail_width, y + thumbnail_height], 
                             fill='#2d2d2d', outline='#3d3d3d', width=1)
                
                # 如果有素材缩略图，加载并绘制
                if beat.main_asset_id:
                    try:
                        from database import Asset
                        asset = self.db.query(Asset).filter(Asset.id == beat.main_asset_id).first()
                        if asset and asset.thumbnail_url:
                            thumb_path = Path(asset.thumbnail_url)
                            if thumb_path.exists():
                                thumb_img = Image.open(str(thumb_path))
                                thumb_img = thumb_img.resize((thumbnail_width - 4, thumbnail_height - 30))
                                img.paste(thumb_img, (x + 2, y + 2))
                    except Exception as e:
                        pass  # 忽略缩略图加载错误
                
                # 绘制Beat编号
                beat_label = f"#{beat.order_index + 1}"
                draw.text((x + 5, y + thumbnail_height - 25), beat_label, fill='#fbbf24', font=label_font)
                
                # 绘制时长
                if beat.duration:
                    duration_text = f"{beat.duration}s"
                    draw.text((x + thumbnail_width - 40, y + thumbnail_height - 25), 
                            duration_text, fill='#9ca3af', font=small_font)
            
            # 绘制页脚
            footer_text = f"共 {total_beats} 个镜头 | 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            draw.text((total_width // 2, total_height - 25), footer_text, 
                     fill='#6b7280', font=small_font, anchor='mm')
            
            # 保存图片
            file_format = format.lower()
            filename = f"{project_id}_contact_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"
            file_path = self.export_dir / filename
            
            if file_format == "png":
                img.save(str(file_path), 'PNG', quality=quality)
            elif file_format in ["jpg", "jpeg"]:
                img.save(str(file_path), 'JPEG', quality=quality)
            else:
                return {"status": "error", "message": f"不支持的格式: {format}"}
            
            # 记录导出历史
            export_record = ExportHistory(
                id=str(uuid.uuid4()),
                project_id=project_id,
                export_type="contact_sheet",
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_format=file_format,
                options={
                    "columns": columns,
                    "thumbnail_width": thumbnail_width,
                    "thumbnail_height": thumbnail_height,
                    "beat_count": total_beats
                },
                status="completed",
                created_at=datetime.now()
            )
            self.db.add(export_record)
            self.db.commit()
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "width": total_width,
                "height": total_height,
                "beat_count": total_beats,
                "export_id": export_record.id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"联系表导出失败: {str(e)}"
            }

    async def export_storyboard_zip(
        self,
        project_id: str,
        format: str = "png",
        width: int = 1920,
        height: int = 1080,
        quality: int = 95,
        group_by_scene: bool = True,
        include_contact_sheet: bool = True
    ) -> Dict[str, Any]:
        """
        导出故事板为 ZIP 包
        按场次分组，包含联系表
        
        Args:
            project_id: 项目ID
            format: 图片格式 (png/jpg)
            width: 图片宽度
            height: 图片高度
            quality: 图片质量
            group_by_scene: 是否按场次分组
            include_contact_sheet: 是否包含联系表
        """
        try:
            # 加载项目数据
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "message": "项目不存在"}
            
            # 加载Beat数据
            beats = self.db.query(Beat).filter(
                Beat.project_id == project_id
            ).order_by(Beat.order_index).all()
            
            if not beats:
                return {"status": "error", "message": "没有找到Beat数据"}
            
            # 创建临时目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_dir = self.export_dir / f"temp_{project_id}_{timestamp}"
            temp_dir.mkdir(exist_ok=True)
            
            exported_files = []
            
            try:
                # 按场次分组
                if group_by_scene:
                    scenes = {}
                    for beat in beats:
                        scene_slug = beat.scene_slug or "未分类"
                        if scene_slug not in scenes:
                            scenes[scene_slug] = []
                        scenes[scene_slug].append(beat)
                    
                    # 为每个场次创建文件夹
                    for scene_name, scene_beats in scenes.items():
                        # 清理场次名称（移除非法字符）
                        safe_scene_name = "".join(c for c in scene_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        if not safe_scene_name:
                            safe_scene_name = "scene"
                        
                        scene_dir = temp_dir / safe_scene_name
                        scene_dir.mkdir(exist_ok=True)
                        
                        # 导出每个Beat
                        for beat in scene_beats:
                            beat_file = await self._export_single_beat(
                                beat, scene_dir, format, width, height, quality
                            )
                            if beat_file:
                                exported_files.append(beat_file)
                else:
                    # 不分组，直接导出
                    for beat in beats:
                        beat_file = await self._export_single_beat(
                            beat, temp_dir, format, width, height, quality
                        )
                        if beat_file:
                            exported_files.append(beat_file)
                
                # 生成联系表
                if include_contact_sheet:
                    contact_result = await self.export_contact_sheet(
                        project_id, format, columns=4, quality=quality
                    )
                    if contact_result["status"] == "success":
                        # 复制联系表到临时目录
                        import shutil
                        contact_src = Path(contact_result["file_path"])
                        contact_dst = temp_dir / f"00_contact_sheet.{format}"
                        shutil.copy(str(contact_src), str(contact_dst))
                        exported_files.insert(0, str(contact_dst))
                
                # 创建 ZIP 文件
                zip_filename = f"{project_id}_storyboard_{timestamp}.zip"
                zip_path = self.export_dir / zip_filename
                
                with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in exported_files:
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
                
                # 记录导出历史
                export_record = ExportHistory(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    export_type="storyboard_zip",
                    file_path=str(zip_path),
                    file_size=zip_path.stat().st_size,
                    file_format="zip",
                    options={
                        "format": format,
                        "width": width,
                        "height": height,
                        "quality": quality,
                        "group_by_scene": group_by_scene,
                        "include_contact_sheet": include_contact_sheet,
                        "file_count": len(exported_files)
                    },
                    status="completed",
                    created_at=datetime.now()
                )
                self.db.add(export_record)
                self.db.commit()
                
                return {
                    "status": "success",
                    "file_path": str(zip_path),
                    "file_size": zip_path.stat().st_size,
                    "file_count": len(exported_files),
                    "export_id": export_record.id
                }
                
            finally:
                # 清理临时目录
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(str(temp_dir), ignore_errors=True)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"故事板ZIP导出失败: {str(e)}"
            }

    async def _export_single_beat(
        self,
        beat: Beat,
        output_dir: Path,
        format: str,
        width: int,
        height: int,
        quality: int
    ) -> Optional[str]:
        """导出单个Beat为图片"""
        try:
            # 创建图片
            img = Image.new('RGB', (width, height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            try:
                title_font = ImageFont.truetype("msyh.ttc", 48)
                body_font = ImageFont.truetype("msyh.ttc", 28)
                small_font = ImageFont.truetype("msyh.ttc", 20)
            except:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # 如果有素材，尝试加载
            if beat.main_asset_id:
                try:
                    from database import Asset
                    asset = self.db.query(Asset).filter(Asset.id == beat.main_asset_id).first()
                    if asset and asset.file_path:
                        asset_path = Path(asset.file_path)
                        if asset_path.exists() and asset_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            asset_img = Image.open(str(asset_path))
                            asset_img = asset_img.resize((width, height))
                            img.paste(asset_img, (0, 0))
                            # 添加半透明遮罩
                            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 128))
                            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                            draw = ImageDraw.Draw(img)
                except Exception:
                    pass
            
            # 绘制Beat信息
            beat_title = f"Beat {beat.order_index + 1}"
            if beat.scene_slug:
                beat_title = f"{beat.scene_slug} - Beat {beat.order_index + 1}"
            
            draw.text((width // 2, 80), beat_title, fill='#fbbf24', font=title_font, anchor='mm')
            
            # 绘制内容
            if beat.content:
                # 自动换行
                content = beat.content
                max_chars_per_line = 50
                lines = []
                for i in range(0, len(content), max_chars_per_line):
                    lines.append(content[i:i+max_chars_per_line])
                
                y_offset = 200
                for line in lines[:8]:  # 最多8行
                    draw.text((width // 2, y_offset), line, fill='#f3f4f6', font=body_font, anchor='mm')
                    y_offset += 40
            
            # 绘制时长和标签
            info_y = height - 100
            if beat.duration:
                draw.text((100, info_y), f"时长: {beat.duration}秒", fill='#9ca3af', font=small_font)
            
            # 标签
            all_tags = []
            if beat.emotion_tags:
                all_tags.extend(beat.emotion_tags[:3])
            if beat.scene_tags:
                all_tags.extend(beat.scene_tags[:3])
            
            if all_tags:
                tags_text = " | ".join(all_tags[:5])
                draw.text((width - 100, info_y), tags_text, fill='#9ca3af', font=small_font, anchor='rm')
            
            # 保存图片
            filename = f"beat_{beat.order_index + 1:03d}.{format}"
            file_path = output_dir / filename
            
            if format.lower() == "png":
                img.save(str(file_path), 'PNG', quality=quality)
            else:
                img.save(str(file_path), 'JPEG', quality=quality)
            
            return str(file_path)
            
        except Exception as e:
            print(f"导出Beat失败: {e}")
            return None
