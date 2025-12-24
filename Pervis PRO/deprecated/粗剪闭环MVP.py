#!/usr/bin/env python3
"""
粗剪闭环MVP - 最短路径实现
从BeatBoard到最终粗剪视频的完整流程
"""

import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import SessionLocal, init_database, Project, Beat, Asset, Timeline, Clip, RenderTask
from services.timeline_service import TimelineService, ClipData
from services.render_service import RenderService, RenderOptions

def log(message):
    """日志输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

class RoughCutMVP:
    """粗剪闭环MVP实现"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.project_id = None
        self.timeline_id = None
        self.render_task_id = None
        self.analysis_log = []
    
    def __del__(self):
        if self.db:
            self.db.close()
    
    def step1_create_test_project_with_beats(self) -> bool:
        """步骤1: 创建测试项目和Beats"""
        log("📋 步骤1: 创建测试项目和Beats")
        
        try:
            # 创建项目
            self.project_id = str(uuid.uuid4())
            project = Project(
                id=self.project_id,
                title="粗剪闭环测试项目",
                logline="测试从BeatBoard到粗剪视频的完整流程",
                current_stage="editing"
            )
            self.db.add(project)
            
            # 创建测试Beats
            beats_data = [
                {
                    "content": "开场：城市夜景，霓虹灯闪烁",
                    "duration": 5.0,
                    "emotion_tags": ["神秘", "紧张"],
                    "scene_tags": ["城市", "夜晚", "户外"]
                },
                {
                    "content": "主角登场：特写镜头，表情坚毅",
                    "duration": 3.0,
                    "emotion_tags": ["坚定", "严肃"],
                    "scene_tags": ["特写", "人物"]
                },
                {
                    "content": "动作场面：追逐戏，快速剪辑",
                    "duration": 8.0,
                    "emotion_tags": ["紧张", "刺激"],
                    "scene_tags": ["动作", "追逐", "户外"]
                }
            ]
            
            for i, beat_data in enumerate(beats_data):
                beat = Beat(
                    id=str(uuid.uuid4()),
                    project_id=self.project_id,
                    order_index=i,
                    content=beat_data["content"],
                    duration=beat_data["duration"],
                    emotion_tags=beat_data["emotion_tags"],
                    scene_tags=beat_data["scene_tags"],
                    action_tags=[]
                )
                self.db.add(beat)
            
            self.db.commit()
            
            beats_count = self.db.query(Beat).filter(Beat.project_id == self.project_id).count()
            log(f"✅ 项目创建成功: {self.project_id}")
            log(f"✅ Beats创建成功: {beats_count} 个")
            
            return True
            
        except Exception as e:
            log(f"❌ 步骤1失败: {e}")
            self.db.rollback()
            return False
    
    def step2_find_or_create_assets(self) -> bool:
        """步骤2: 查找或创建测试素材"""
        log("\n📋 步骤2: 查找可用素材")
        
        try:
            # 查找L盘的视频文件
            originals_path = Path("L:/PreVis_Assets/originals")
            
            if not originals_path.exists():
                log("❌ 素材目录不存在")
                return False
            
            # 查找前3个视频文件
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
            video_files = []
            
            for file_path in originals_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                    video_files.append(file_path)
                    if len(video_files) >= 3:
                        break
            
            if len(video_files) < 3:
                log(f"⚠️  只找到 {len(video_files)} 个视频文件，需要至少3个")
                # 继续使用找到的文件
            
            log(f"✅ 找到 {len(video_files)} 个视频文件")
            
            # 为每个视频创建Asset记录
            for i, video_file in enumerate(video_files):
                asset_id = str(uuid.uuid4())
                asset = Asset(
                    id=asset_id,
                    project_id=self.project_id,
                    filename=video_file.name,
                    file_path=str(video_file),
                    media_type="video",
                    file_size=video_file.stat().st_size,
                    status="ready"
                )
                self.db.add(asset)
                log(f"   ✅ Asset {i+1}: {video_file.name[:50]}")
            
            self.db.commit()
            
            assets_count = self.db.query(Asset).filter(Asset.project_id == self.project_id).count()
            log(f"✅ 素材记录创建成功: {assets_count} 个")
            
            return assets_count > 0
            
        except Exception as e:
            log(f"❌ 步骤2失败: {e}")
            self.db.rollback()
            return False
    
    def step3_create_timeline_from_beats(self) -> bool:
        """步骤3: 从Beats创建Timeline和Clips"""
        log("\n📋 步骤3: 从Beats创建Timeline")
        
        try:
            # 创建Timeline
            timeline_service = TimelineService(self.db)
            timeline = timeline_service.create_timeline(
                project_id=self.project_id,
                name="粗剪时间轴"
            )
            self.timeline_id = timeline.id
            log(f"✅ Timeline创建成功: {self.timeline_id}")
            
            # 获取Beats和Assets
            beats = self.db.query(Beat).filter(
                Beat.project_id == self.project_id
            ).order_by(Beat.order_index).all()
            
            assets = self.db.query(Asset).filter(
                Asset.project_id == self.project_id
            ).all()
            
            if not beats or not assets:
                log("❌ 缺少Beats或Assets")
                return False
            
            log(f"   📊 Beats数量: {len(beats)}")
            log(f"   📊 Assets数量: {len(assets)}")
            
            # 为每个Beat创建Clip
            current_time = 0.0
            clips_created = 0
            
            for i, beat in enumerate(beats):
                # 选择素材（简单轮询）
                asset = assets[i % len(assets)]
                
                # 创建Clip数据
                clip_data = ClipData({
                    'asset_id': asset.id,
                    'start_time': current_time,
                    'end_time': current_time + beat.duration,
                    'trim_start': 0.0,
                    'trim_end': min(beat.duration, 10.0),  # 最多取10秒
                    'volume': 1.0,
                    'is_muted': 0,
                    'order_index': i,
                    'clip_metadata': {
                        'beat_id': beat.id,
                        'beat_content': beat.content,
                        'beat_tags': {
                            'emotion': beat.emotion_tags or [],
                            'scene': beat.scene_tags or []
                        }
                    }
                })
                
                # 添加Clip
                clip = timeline_service.add_clip(self.timeline_id, clip_data)
                clips_created += 1
                
                # 记录分析日志
                self.analysis_log.append({
                    "beat_index": i,
                    "beat_id": beat.id,
                    "beat_content": beat.content,
                    "clip_id": clip.id,
                    "asset_id": asset.id,
                    "asset_filename": asset.filename,
                    "start_time": current_time,
                    "end_time": current_time + beat.duration,
                    "duration": beat.duration,
                    "reason": f"为Beat {i+1} 选择素材 {asset.filename[:30]}，基于顺序匹配"
                })
                
                log(f"   ✅ Clip {i+1}: Beat[{beat.content[:30]}...] -> Asset[{asset.filename[:30]}...]")
                
                current_time += beat.duration
            
            log(f"✅ Clips创建成功: {clips_created} 个")
            log(f"✅ 总时长: {current_time:.1f} 秒")
            
            return True
            
        except Exception as e:
            log(f"❌ 步骤3失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step4_render_rough_cut(self) -> bool:
        """步骤4: 渲染粗剪视频"""
        log("\n📋 步骤4: 渲染粗剪视频")
        
        try:
            render_service = RenderService(self.db)
            
            # 检查渲染前置条件
            log("   🔍 检查渲染前置条件...")
            requirements = render_service.check_render_requirements(self.timeline_id)
            
            if not requirements['can_render']:
                log("❌ 渲染前置条件不满足:")
                for error in requirements['errors']:
                    log(f"   • {error}")
                return False
            
            log("   ✅ 渲染前置条件满足")
            
            # 配置渲染选项
            render_options = RenderOptions({
                'format': 'mp4',
                'resolution': '720p',
                'framerate': 30,
                'quality': 'medium',
                'use_proxy': False  # 使用原始文件
            })
            
            # 启动渲染
            log("   🎬 开始渲染...")
            self.render_task_id = render_service.start_render(
                timeline_id=self.timeline_id,
                options=render_options
            )
            
            log(f"✅ 渲染任务创建: {self.render_task_id}")
            
            # 检查渲染状态
            status = render_service.get_render_status(self.render_task_id)
            
            if status['status'] == 'completed':
                log(f"✅ 渲染完成: {status['output_path']}")
                log(f"   📊 文件大小: {status['file_size'] / 1024 / 1024:.1f} MB")
                return True
            elif status['status'] == 'failed':
                log(f"❌ 渲染失败: {status.get('error_message', '未知错误')}")
                return False
            else:
                log(f"⏳ 渲染状态: {status['status']} ({status['progress']:.1f}%)")
                return True
            
        except Exception as e:
            log(f"❌ 步骤4失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step5_generate_analysis_log(self) -> bool:
        """步骤5: 生成剪辑分析日志"""
        log("\n📋 步骤5: 生成剪辑分析日志")
        
        try:
            # 获取渲染结果
            render_service = RenderService(self.db)
            render_result = render_service.get_render_result(self.render_task_id)
            
            if not render_result:
                log("⚠️  渲染尚未完成，生成部分日志")
            
            # 构建分析日志
            analysis_report = {
                "project_id": self.project_id,
                "timeline_id": self.timeline_id,
                "render_task_id": self.render_task_id,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_beats": len(self.analysis_log),
                    "total_clips": len(self.analysis_log),
                    "total_duration": sum(item["duration"] for item in self.analysis_log),
                    "output_file": render_result["output_path"] if render_result else "渲染中..."
                },
                "beat_to_clip_mapping": self.analysis_log,
                "render_info": render_result if render_result else {"status": "processing"}
            }
            
            # 保存日志文件
            log_filename = f"rough_cut_analysis_{self.project_id[:8]}.json"
            log_path = Path("exports") / log_filename
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_report, f, ensure_ascii=False, indent=2)
            
            log(f"✅ 分析日志已生成: {log_path}")
            
            # 打印摘要
            log("\n📊 剪辑分析摘要:")
            log(f"   • 项目ID: {self.project_id}")
            log(f"   • Beat数量: {analysis_report['summary']['total_beats']}")
            log(f"   • Clip数量: {analysis_report['summary']['total_clips']}")
            log(f"   • 总时长: {analysis_report['summary']['total_duration']:.1f} 秒")
            
            log("\n📋 Beat到Clip映射:")
            for item in self.analysis_log:
                log(f"   Beat {item['beat_index']+1}: {item['beat_content'][:40]}...")
                log(f"      → Clip: {item['asset_filename'][:40]}...")
                log(f"      → 时间: {item['start_time']:.1f}s - {item['end_time']:.1f}s")
                log(f"      → 原因: {item['reason']}")
            
            return True
            
        except Exception as e:
            log(f"❌ 步骤5失败: {e}")
            return False
    
    def step6_verify_output(self) -> bool:
        """步骤6: 验证输出文件"""
        log("\n📋 步骤6: 验证粗剪视频输出")
        
        try:
            render_service = RenderService(self.db)
            render_result = render_service.get_render_result(self.render_task_id)
            
            if not render_result:
                log("❌ 渲染任务未完成")
                return False
            
            output_path = Path(render_result["output_path"])
            
            if not output_path.exists():
                log(f"❌ 输出文件不存在: {output_path}")
                return False
            
            file_size_mb = output_path.stat().st_size / 1024 / 1024
            
            log(f"✅ 粗剪视频已生成:")
            log(f"   • 文件路径: {output_path}")
            log(f"   • 文件大小: {file_size_mb:.1f} MB")
            log(f"   • 格式: {render_result['format']}")
            log(f"   • 分辨率: {render_result['resolution']}")
            
            # 验证文件可播放
            from services.ffmpeg_wrapper import ffmpeg_wrapper
            video_info = ffmpeg_wrapper.get_video_info(str(output_path))
            
            log(f"   • 视频时长: {video_info.duration:.1f} 秒")
            log(f"   • 视频分辨率: {video_info.width}x{video_info.height}")
            log(f"   • 帧率: {video_info.fps} fps")
            
            log("\n🎉 粗剪闭环验证成功！")
            log(f"\n🎬 可以播放粗剪视频: {output_path}")
            
            return True
            
        except Exception as e:
            log(f"❌ 步骤6失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_complete_flow(self) -> bool:
        """运行完整的粗剪闭环流程"""
        log("🚀 开始粗剪闭环MVP测试")
        log("=" * 70)
        
        # 初始化数据库
        init_database()
        
        # 执行各个步骤
        if not self.step1_create_test_project_with_beats():
            return False
        
        if not self.step2_find_or_create_assets():
            return False
        
        if not self.step3_create_timeline_from_beats():
            return False
        
        if not self.step4_render_rough_cut():
            return False
        
        if not self.step5_generate_analysis_log():
            return False
        
        if not self.step6_verify_output():
            return False
        
        log("\n" + "=" * 70)
        log("🎉 粗剪闭环MVP测试完成！")
        log("=" * 70)
        
        return True

def main():
    """主函数"""
    mvp = RoughCutMVP()
    
    try:
        success = mvp.run_complete_flow()
        
        if success:
            log("\n✅ 粗剪闭环MVP验证通过")
            log("   • BeatBoard → Clips ✓")
            log("   • Clips → Timeline ✓")
            log("   • Timeline → 粗剪视频 ✓")
            log("   • 剪辑分析日志 ✓")
            return 0
        else:
            log("\n❌ 粗剪闭环MVP验证失败")
            return 1
            
    except Exception as e:
        log(f"\n❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())