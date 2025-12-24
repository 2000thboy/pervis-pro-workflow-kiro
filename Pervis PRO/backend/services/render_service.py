"""
渲染服务 - 完整实现版本
支持真实的视频渲染和输出
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import uuid
import os
import asyncio
import threading
from datetime import datetime
from pathlib import Path

from .ffmpeg_wrapper import FFmpegWrapper
from .timeline_service import TimelineService

logger = logging.getLogger(__name__)


class RenderTask:
    """渲染任务数据类"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.timeline_id = data.get('timeline_id')
        self.status = data.get('status', 'pending')
        self.progress = data.get('progress', 0)
        self.error_message = data.get('error_message')
        self.output_path = data.get('output_path')
        self.file_size = data.get('file_size')
        self.created_at = data.get('created_at')
        self.started_at = data.get('started_at')
        self.completed_at = data.get('completed_at')
        self.render_options = data.get('render_options', {})


class RenderService:
    """渲染服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ffmpeg = FFmpegWrapper()
        self.timeline_service = TimelineService(db)
        self.output_dir = Path("storage/renders")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 渲染质量预设
        self.quality_presets = {
            'low': {'crf': 28, 'preset': 'fast', 'bitrate': '1000k'},
            'medium': {'crf': 23, 'preset': 'medium', 'bitrate': '3000k'},
            'high': {'crf': 18, 'preset': 'slow', 'bitrate': '8000k'},
            'ultra': {'crf': 15, 'preset': 'slower', 'bitrate': '15000k'}
        }
    
    async def check_render_requirements(self, timeline_id: str) -> Dict[str, Any]:
        """检查渲染前置条件"""
        try:
            # 获取时间轴数据
            timeline = self.timeline_service.get_timeline_with_clips(timeline_id)
            if not timeline:
                return {
                    "can_render": False,
                    "errors": ["时间轴不存在"]
                }
            
            if not timeline.get('clips'):
                return {
                    "can_render": False,
                    "errors": ["时间轴中没有片段"]
                }
            
            # 检查素材文件是否存在
            missing_files = []
            total_duration = 0
            
            for clip in timeline['clips']:
                asset_id = clip.get('asset_id')
                if asset_id:
                    # 查询素材文件路径
                    result = self.db.execute(
                        text("SELECT file_path FROM assets WHERE id = :asset_id"),
                        {"asset_id": asset_id}
                    ).fetchone()
                    
                    if not result or not result[0]:
                        missing_files.append(f"素材 {asset_id} 文件路径不存在")
                    elif not os.path.exists(result[0]):
                        missing_files.append(f"素材文件不存在: {result[0]}")
                
                # 计算总时长
                clip_duration = clip.get('end_time', 0) - clip.get('start_time', 0)
                total_duration += clip_duration
            
            if missing_files:
                return {
                    "can_render": False,
                    "errors": missing_files
                }
            
            # 估算渲染时间和文件大小
            estimated_duration = max(total_duration * 0.5, 10)  # 至少10秒
            estimated_size_mb = total_duration * 2  # 大约每秒2MB
            
            return {
                "can_render": True,
                "timeline_duration": total_duration,
                "clip_count": len(timeline['clips']),
                "estimated_duration": estimated_duration,
                "estimated_size_mb": estimated_size_mb
            }
            
        except Exception as e:
            logger.error(f"检查渲染条件失败: {e}")
            return {
                "can_render": False,
                "errors": [f"检查失败: {str(e)}"]
            }
    
    async def start_render(
        self,
        timeline_id: str,
        format: str = "mp4",
        resolution: str = "1080p",
        framerate: int = 30,
        quality: str = "high",
        bitrate: Optional[int] = None,
        audio_bitrate: int = 192,
        use_proxy: bool = False
    ) -> str:
        """开始渲染任务"""
        try:
            task_id = str(uuid.uuid4())
            
            # 创建渲染任务记录
            render_options = {
                "format": format,
                "resolution": resolution,
                "framerate": framerate,
                "quality": quality,
                "bitrate": bitrate,
                "audio_bitrate": audio_bitrate,
                "use_proxy": use_proxy
            }
            
            # 生成输出文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"render_{timestamp}_{task_id[:8]}.{format}"
            output_path = str(self.output_dir / output_filename)
            
            # 插入任务记录 - 使用数据库模型字段
            self.db.execute(
                text("""
                    INSERT INTO render_tasks 
                    (id, timeline_id, status, progress, output_path, format, resolution, framerate, quality, bitrate, audio_bitrate, created_at)
                    VALUES (:id, :timeline_id, :status, :progress, :output_path, :format, :resolution, :framerate, :quality, :bitrate, :audio_bitrate, :created_at)
                """),
                {
                    "id": task_id,
                    "timeline_id": timeline_id,
                    "status": "pending",
                    "progress": 0,
                    "output_path": output_path,
                    "format": format,
                    "resolution": resolution,
                    "framerate": framerate,
                    "quality": quality,
                    "bitrate": bitrate,
                    "audio_bitrate": audio_bitrate,
                    "created_at": datetime.now()
                }
            )
            self.db.commit()
            
            # 在后台线程中执行渲染
            threading.Thread(
                target=self._execute_render,
                args=(task_id, timeline_id, output_path, render_options),
                daemon=True
            ).start()
            
            logger.info(f"渲染任务已创建: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"启动渲染失败: {e}")
            raise
    
    def _execute_render(self, task_id: str, timeline_id: str, output_path: str, options: dict):
        """执行渲染（在后台线程中运行）"""
        try:
            # 更新状态为处理中
            self._update_task_status(task_id, "processing", 0, started_at=datetime.now())
            
            # 获取时间轴数据
            timeline = self.timeline_service.get_timeline_with_clips(timeline_id)
            if not timeline or not timeline.get('clips'):
                raise Exception("时间轴数据无效")
            
            clips = timeline['clips']
            clips.sort(key=lambda x: x.get('order_index', 0))
            
            # 准备临时文件列表
            temp_files = []
            video_segments = []
            
            try:
                # 处理每个片段
                for i, clip in enumerate(clips):
                    progress = (i / len(clips)) * 80  # 80%用于片段处理
                    self._update_task_status(task_id, "processing", progress)
                    
                    # 获取素材文件路径
                    result = self.db.execute(
                        text("SELECT file_path FROM assets WHERE id = :asset_id"),
                        {"asset_id": clip['asset_id']}
                    ).fetchone()
                    
                    if not result or not result[0]:
                        raise Exception(f"素材文件不存在: {clip['asset_id']}")
                    
                    source_path = result[0]
                    
                    # 生成临时片段文件
                    temp_segment = str(self.output_dir / f"temp_segment_{task_id}_{i}.mp4")
                    temp_files.append(temp_segment)
                    
                    # 剪切片段
                    trim_start = clip.get('trim_start', 0)
                    trim_end = clip.get('trim_end')
                    
                    if trim_end:
                        # 剪切指定范围
                        self.ffmpeg.trim_video(
                            source_path,
                            trim_start,
                            trim_end,
                            temp_segment
                        )
                    else:
                        # 使用整个文件
                        import shutil
                        shutil.copy2(source_path, temp_segment)
                    
                    video_segments.append(temp_segment)
                
                # 拼接所有片段
                self._update_task_status(task_id, "processing", 85)
                
                if len(video_segments) == 1:
                    # 只有一个片段，直接移动
                    import shutil
                    shutil.move(video_segments[0], output_path)
                else:
                    # 拼接多个片段
                    self.ffmpeg.concat_videos(video_segments, output_path)
                
                # 获取输出文件大小
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                
                # 更新为完成状态
                self._update_task_status(
                    task_id, 
                    "completed", 
                    100, 
                    completed_at=datetime.now(),
                    file_size=file_size
                )
                
                logger.info(f"渲染完成: {task_id} -> {output_path}")
                
            finally:
                # 清理临时文件
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {e}")
                        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"渲染失败 {task_id}: {error_msg}")
            self._update_task_status(task_id, "failed", 0, error_message=error_msg)
    
    def _update_task_status(
        self, 
        task_id: str, 
        status: str, 
        progress: float,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None
    ):
        """更新任务状态"""
        try:
            update_fields = {
                "status": status,
                "progress": progress,
                "task_id": task_id
            }
            
            update_sql = "UPDATE render_tasks SET status = :status, progress = :progress"
            
            if started_at:
                update_fields["started_at"] = started_at
                update_sql += ", started_at = :started_at"
            
            if completed_at:
                update_fields["completed_at"] = completed_at
                update_sql += ", completed_at = :completed_at"
            
            if error_message:
                update_fields["error_message"] = error_message
                update_sql += ", error_message = :error_message"
            
            if file_size is not None:
                update_fields["file_size"] = file_size
                update_sql += ", file_size = :file_size"
            
            update_sql += " WHERE id = :task_id"
            
            self.db.execute(text(update_sql), update_fields)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            result = self.db.execute(
                text("""
                    SELECT id, timeline_id, status, progress, error_message, 
                           output_path, file_size, created_at, started_at, completed_at
                    FROM render_tasks 
                    WHERE id = :task_id
                """),
                {"task_id": task_id}
            ).fetchone()
            
            if not result:
                return None
            
            # 安全处理日期字段
            def safe_isoformat(date_value):
                if date_value is None:
                    return None
                if hasattr(date_value, 'isoformat'):
                    return date_value.isoformat()
                return str(date_value)  # 如果已经是字符串，直接返回
            
            return {
                "id": result[0],
                "timeline_id": result[1],
                "status": result[2],
                "progress": result[3],
                "error_message": result[4],
                "output_path": result[5],
                "file_size": result[6],
                "created_at": safe_isoformat(result[7]),
                "started_at": safe_isoformat(result[8]),
                "completed_at": safe_isoformat(result[9])
            }
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    async def cancel_render(self, task_id: str) -> bool:
        """取消渲染任务"""
        try:
            # 更新状态为已取消
            self.db.execute(
                text("UPDATE render_tasks SET status = 'cancelled' WHERE id = :task_id"),
                {"task_id": task_id}
            )
            self.db.commit()
            
            logger.info(f"渲染任务已取消: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消渲染失败: {e}")
            return False
    
    async def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出渲染任务"""
        try:
            # 安全处理日期字段
            def safe_isoformat(date_value):
                if date_value is None:
                    return None
                if hasattr(date_value, 'isoformat'):
                    return date_value.isoformat()
                return str(date_value)  # 如果已经是字符串，直接返回
            
            results = self.db.execute(
                text("""
                    SELECT id, timeline_id, status, progress, error_message,
                           output_path, file_size, created_at, started_at, completed_at
                    FROM render_tasks 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            tasks = []
            for result in results:
                tasks.append({
                    "id": result[0],
                    "timeline_id": result[1],
                    "status": result[2],
                    "progress": result[3],
                    "error_message": result[4],
                    "output_path": result[5],
                    "file_size": result[6],
                    "created_at": safe_isoformat(result[7]),
                    "started_at": safe_isoformat(result[8]),
                    "completed_at": safe_isoformat(result[9])
                })
            
            return tasks
            
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return []
    
    def get_download_path(self, task_id: str) -> Optional[str]:
        """获取下载文件路径"""
        try:
            result = self.db.execute(
                text("SELECT output_path, status FROM render_tasks WHERE id = :task_id"),
                {"task_id": task_id}
            ).fetchone()
            
            if result and result[1] == 'completed' and result[0]:
                if os.path.exists(result[0]):
                    return result[0]
            
            return None
            
        except Exception as e:
            logger.error(f"获取下载路径失败: {e}")
            return None
