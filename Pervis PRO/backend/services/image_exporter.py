"""
图片导出服务
支持PNG和JPG格式的BeatBoard导出
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
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
