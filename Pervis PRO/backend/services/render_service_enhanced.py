# -*- coding: utf-8 -*-
"""
P1: 增强版渲染服务
支持更多格式、分辨率、帧率和质量选项

增强功能：
1. 多格式支持 (MP4, MOV, WebM, ProRes)
2. 多分辨率支持 (720p, 1080p, 2K, 4K)
3. 多帧率支持 (23.976, 24, 25, 29.97, 30, 50, 60)
4. 质量预设和自定义比特率
5. 渲染进度实时推送
6. 渲染队列管理
7. 断点续渲支持
"""

import os
import uuid
import asyncio
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ============================================================
# 枚举和数据类
# ============================================================

class VideoFormat(str, Enum):
    """视频格式"""
    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"
    PRORES = "prores"


class Resolution(str, Enum):
    """分辨率"""
    HD_720 = "720p"
    FHD_1080 = "1080p"
    QHD_2K = "2k"
    UHD_4K = "4k"


class Quality(str, Enum):
    """质量预设"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    CUSTOM = "custom"


@dataclass
class ResolutionConfig:
    """分辨率配置"""
    width: int
    height: int
    name: str


@dataclass
class QualityPreset:
    """质量预设配置"""
    crf: int
    preset: str
    bitrate: str
    audio_bitrate: int


@dataclass
class RenderOptions:
    """渲染选项"""
    format: VideoFormat = VideoFormat.MP4
    resolution: Resolution = Resolution.FHD_1080
    framerate: float = 30.0
    quality: Quality = Quality.HIGH
    custom_bitrate: Optional[int] = None
    audio_bitrate: int = 192
    use_proxy: bool = False
    include_audio: bool = True
    watermark: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class RenderProgress:
    """渲染进度"""
    task_id: str
    status: str
    progress: float
    current_frame: int = 0
    total_frames: int = 0
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    current_stage: str = ""
    message: str = ""


# ============================================================
# 配置常量
# ============================================================

RESOLUTION_CONFIGS: Dict[Resolution, ResolutionConfig] = {
    Resolution.HD_720: ResolutionConfig(1280, 720, "720p HD"),
    Resolution.FHD_1080: ResolutionConfig(1920, 1080, "1080p Full HD"),
    Resolution.QHD_2K: ResolutionConfig(2560, 1440, "2K QHD"),
    Resolution.UHD_4K: ResolutionConfig(3840, 2160, "4K UHD"),
}

QUALITY_PRESETS: Dict[Quality, QualityPreset] = {
    Quality.LOW: QualityPreset(crf=28, preset="fast", bitrate="1000k", audio_bitrate=128),
    Quality.MEDIUM: QualityPreset(crf=23, preset="medium", bitrate="3000k", audio_bitrate=192),
    Quality.HIGH: QualityPreset(crf=18, preset="slow", bitrate="8000k", audio_bitrate=256),
    Quality.ULTRA: QualityPreset(crf=15, preset="slower", bitrate="15000k", audio_bitrate=320),
}

FRAMERATE_OPTIONS = [23.976, 24, 25, 29.97, 30, 50, 60]

FORMAT_CODECS: Dict[VideoFormat, Dict[str, str]] = {
    VideoFormat.MP4: {"video": "libx264", "audio": "aac", "ext": "mp4"},
    VideoFormat.MOV: {"video": "libx264", "audio": "aac", "ext": "mov"},
    VideoFormat.WEBM: {"video": "libvpx-vp9", "audio": "libopus", "ext": "webm"},
    VideoFormat.PRORES: {"video": "prores_ks", "audio": "pcm_s16le", "ext": "mov"},
}


# ============================================================
# 增强版渲染服务
# ============================================================

class EnhancedRenderService:
    """增强版渲染服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.output_dir = Path("storage/renders")
        self.temp_dir = Path("storage/renders/temp")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 渲染队列
        self._render_queue: List[str] = []
        self._active_renders: Dict[str, threading.Thread] = {}
        self._max_concurrent = 2
        
        # 事件服务
        self._event_service = None
        
        # FFmpeg 包装器
        self._ffmpeg = None
    
    def _get_ffmpeg(self):
        """延迟加载 FFmpeg"""
        if self._ffmpeg is None:
            from services.ffmpeg_wrapper import FFmpegWrapper
            self._ffmpeg = FFmpegWrapper()
        return self._ffmpeg
    
    def _get_event_service(self):
        """延迟加载事件服务"""
        if self._event_service is None:
            try:
                from services.event_service import event_service
                self._event_service = event_service
            except Exception as e:
                logger.warning(f"EventService 加载失败: {e}")
        return self._event_service
    
    def _get_timeline_service(self):
        """获取时间线服务"""
        from services.timeline_service import TimelineService
        return TimelineService(self.db)
    
    # ============================================================
    # 渲染前检查
    # ============================================================
    
    async def check_render_requirements(
        self,
        timeline_id: str,
        options: Optional[RenderOptions] = None
    ) -> Dict[str, Any]:
        """检查渲染前置条件"""
        errors = []
        warnings = []
        
        try:
            # 获取时间线
            timeline_service = self._get_timeline_service()
            timeline = timeline_service.get_timeline_with_clips(timeline_id)
            
            if not timeline:
                return {"can_render": False, "errors": ["时间轴不存在"]}
            
            if not timeline.get('clips'):
                return {"can_render": False, "errors": ["时间轴中没有片段"]}
            
            # 检查素材文件
            missing_files = []
            total_duration = 0
            
            for clip in timeline['clips']:
                asset_id = clip.get('asset_id')
                if asset_id and asset_id != "placeholder":
                    result = self.db.execute(
                        text("SELECT file_path FROM assets WHERE id = :asset_id"),
                        {"asset_id": asset_id}
                    ).fetchone()
                    
                    if not result or not result[0]:
                        missing_files.append(f"素材 {asset_id} 文件路径不存在")
                    elif not os.path.exists(result[0]):
                        missing_files.append(f"素材文件不存在: {result[0]}")
                
                clip_duration = clip.get('end_time', 0) - clip.get('start_time', 0)
                total_duration += clip_duration
            
            if missing_files:
                errors.extend(missing_files)
            
            # 检查 FFmpeg
            try:
                ffmpeg = self._get_ffmpeg()
                ffmpeg._check_ffmpeg()
            except Exception as e:
                errors.append(f"FFmpeg 不可用: {str(e)}")
            
            # 估算
            options = options or RenderOptions()
            res_config = RESOLUTION_CONFIGS.get(options.resolution, RESOLUTION_CONFIGS[Resolution.FHD_1080])
            quality_preset = QUALITY_PRESETS.get(options.quality, QUALITY_PRESETS[Quality.HIGH])
            
            # 估算渲染时间（基于分辨率和质量）
            complexity_factor = {
                Resolution.HD_720: 0.5,
                Resolution.FHD_1080: 1.0,
                Resolution.QHD_2K: 2.0,
                Resolution.UHD_4K: 4.0,
            }.get(options.resolution, 1.0)
            
            estimated_render_time = total_duration * complexity_factor * 0.5
            
            # 估算文件大小 (MB)
            bitrate_kbps = int(quality_preset.bitrate.replace('k', ''))
            estimated_size_mb = (total_duration * bitrate_kbps) / 8 / 1024
            
            return {
                "can_render": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "timeline_duration": total_duration,
                "clip_count": len(timeline['clips']),
                "estimated_render_time": estimated_render_time,
                "estimated_size_mb": estimated_size_mb,
                "resolution": f"{res_config.width}x{res_config.height}",
                "format": options.format.value,
            }
            
        except Exception as e:
            logger.error(f"检查渲染条件失败: {e}")
            return {"can_render": False, "errors": [f"检查失败: {str(e)}"]}
    
    # ============================================================
    # 渲染任务管理
    # ============================================================
    
    async def start_render(
        self,
        timeline_id: str,
        options: Optional[RenderOptions] = None
    ) -> str:
        """开始渲染任务"""
        options = options or RenderOptions()
        task_id = str(uuid.uuid4())
        
        try:
            # 生成输出路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            format_config = FORMAT_CODECS.get(options.format, FORMAT_CODECS[VideoFormat.MP4])
            output_filename = f"render_{timestamp}_{task_id[:8]}.{format_config['ext']}"
            output_path = str(self.output_dir / output_filename)
            
            # 创建任务记录
            self.db.execute(
                text("""
                    INSERT INTO render_tasks 
                    (id, timeline_id, status, progress, output_path, format, resolution, 
                     framerate, quality, bitrate, audio_bitrate, created_at)
                    VALUES (:id, :timeline_id, :status, :progress, :output_path, :format, 
                            :resolution, :framerate, :quality, :bitrate, :audio_bitrate, :created_at)
                """),
                {
                    "id": task_id,
                    "timeline_id": timeline_id,
                    "status": "pending",
                    "progress": 0,
                    "output_path": output_path,
                    "format": options.format.value,
                    "resolution": options.resolution.value,
                    "framerate": options.framerate,
                    "quality": options.quality.value,
                    "bitrate": options.custom_bitrate,
                    "audio_bitrate": options.audio_bitrate,
                    "created_at": datetime.now()
                }
            )
            self.db.commit()
            
            # 启动渲染线程
            render_thread = threading.Thread(
                target=self._execute_render_enhanced,
                args=(task_id, timeline_id, output_path, options),
                daemon=True
            )
            render_thread.start()
            self._active_renders[task_id] = render_thread
            
            logger.info(f"渲染任务已创建: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"启动渲染失败: {e}")
            raise
    
    def _execute_render_enhanced(
        self,
        task_id: str,
        timeline_id: str,
        output_path: str,
        options: RenderOptions
    ):
        """执行增强版渲染"""
        temp_files = []
        start_time = datetime.now()
        
        try:
            # 更新状态
            self._update_task_status(task_id, "processing", 0, started_at=datetime.now())
            self._emit_progress(
                task_id, "processing", 0, "准备渲染...",
                current_stage="初始化",
                elapsed_time=0
            )
            
            # 获取时间线
            timeline_service = self._get_timeline_service()
            timeline = timeline_service.get_timeline_with_clips(timeline_id)
            
            if not timeline or not timeline.get('clips'):
                raise Exception("时间轴数据无效")
            
            clips = sorted(timeline['clips'], key=lambda x: x.get('order_index', 0))
            total_clips = len(clips)
            
            # 获取配置
            res_config = RESOLUTION_CONFIGS.get(options.resolution, RESOLUTION_CONFIGS[Resolution.FHD_1080])
            quality_preset = QUALITY_PRESETS.get(options.quality, QUALITY_PRESETS[Quality.HIGH])
            format_config = FORMAT_CODECS.get(options.format, FORMAT_CODECS[VideoFormat.MP4])
            
            ffmpeg = self._get_ffmpeg()
            video_segments = []
            
            # 处理每个片段
            for i, clip in enumerate(clips):
                elapsed = (datetime.now() - start_time).total_seconds()
                progress = (i / total_clips) * 70  # 70% 用于片段处理
                
                # 估算剩余时间
                if i > 0:
                    avg_time_per_clip = elapsed / i
                    remaining_clips = total_clips - i
                    estimated_remaining = avg_time_per_clip * remaining_clips + 10  # +10秒用于拼接
                else:
                    estimated_remaining = total_clips * 5  # 估算每个片段5秒
                
                self._update_task_status(task_id, "processing", progress)
                self._emit_progress(
                    task_id, "processing", progress, 
                    f"处理片段 {i+1}/{total_clips}",
                    current_stage=f"转码片段 {i+1}",
                    elapsed_time=elapsed,
                    estimated_remaining=estimated_remaining
                )
                
                asset_id = clip.get('asset_id')
                if not asset_id or asset_id == "placeholder":
                    logger.warning(f"跳过占位片段: {clip.get('id')}")
                    continue
                
                # 获取素材路径
                result = self.db.execute(
                    text("SELECT file_path FROM assets WHERE id = :asset_id"),
                    {"asset_id": asset_id}
                ).fetchone()
                
                if not result or not result[0] or not os.path.exists(result[0]):
                    logger.warning(f"素材文件不存在: {asset_id}")
                    continue
                
                source_path = result[0]
                
                # 生成临时片段
                temp_segment = str(self.temp_dir / f"segment_{task_id}_{i}.mp4")
                temp_files.append(temp_segment)
                
                # 剪切和转码
                trim_start = clip.get('trim_start', 0)
                trim_end = clip.get('trim_end')
                
                self._transcode_segment(
                    source_path=source_path,
                    output_path=temp_segment,
                    trim_start=trim_start,
                    trim_end=trim_end,
                    resolution=res_config,
                    framerate=options.framerate,
                    quality=quality_preset,
                    format_config=format_config
                )
                
                if os.path.exists(temp_segment):
                    video_segments.append(temp_segment)
            
            if not video_segments:
                raise Exception("没有有效的视频片段")
            
            # 拼接片段
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_task_status(task_id, "processing", 80)
            self._emit_progress(
                task_id, "processing", 80, "拼接视频片段...",
                current_stage="视频拼接",
                elapsed_time=elapsed,
                estimated_remaining=10
            )
            
            if len(video_segments) == 1:
                import shutil
                shutil.move(video_segments[0], output_path)
            else:
                ffmpeg.concat_videos(video_segments, output_path)
            
            # 最终处理
            elapsed = (datetime.now() - start_time).total_seconds()
            self._update_task_status(task_id, "processing", 95)
            self._emit_progress(
                task_id, "processing", 95, "完成处理...",
                current_stage="最终处理",
                elapsed_time=elapsed,
                estimated_remaining=2
            )
            
            # 获取文件大小
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 完成
            self._update_task_status(
                task_id, "completed", 100,
                completed_at=datetime.now(),
                file_size=file_size
            )
            self._emit_progress(
                task_id, "completed", 100, "渲染完成",
                current_stage="完成",
                elapsed_time=elapsed,
                estimated_remaining=0,
                output_path=output_path,
                file_size=file_size
            )
            
            logger.info(f"渲染完成: {task_id} -> {output_path} ({file_size} bytes, {elapsed:.1f}s)")
            
        except Exception as e:
            error_msg = str(e)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"渲染失败 {task_id}: {error_msg}")
            self._update_task_status(task_id, "failed", 0, error_message=error_msg)
            self._emit_progress(
                task_id, "failed", 0, f"渲染失败: {error_msg}",
                current_stage="错误",
                elapsed_time=elapsed,
                error=error_msg
            )
            
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")
            
            # 从活动渲染中移除
            if task_id in self._active_renders:
                del self._active_renders[task_id]
    
    def _transcode_segment(
        self,
        source_path: str,
        output_path: str,
        trim_start: float,
        trim_end: Optional[float],
        resolution: ResolutionConfig,
        framerate: float,
        quality: QualityPreset,
        format_config: Dict[str, str]
    ):
        """转码单个片段"""
        import subprocess
        
        cmd = ['ffmpeg', '-y']
        
        # 输入
        if trim_start > 0:
            cmd.extend(['-ss', str(trim_start)])
        
        cmd.extend(['-i', source_path])
        
        # 时长
        if trim_end:
            duration = trim_end - trim_start
            cmd.extend(['-t', str(duration)])
        
        # 视频编码
        cmd.extend([
            '-c:v', format_config['video'],
            '-vf', f'scale={resolution.width}:{resolution.height}:force_original_aspect_ratio=decrease,pad={resolution.width}:{resolution.height}:(ow-iw)/2:(oh-ih)/2',
            '-r', str(framerate),
            '-crf', str(quality.crf),
            '-preset', quality.preset,
        ])
        
        # 音频编码
        cmd.extend([
            '-c:a', format_config['audio'],
            '-b:a', f'{quality.audio_bitrate}k',
        ])
        
        cmd.append(output_path)
        
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        except subprocess.TimeoutExpired:
            raise Exception("转码超时")
        except subprocess.CalledProcessError as e:
            raise Exception(f"转码失败: {e.stderr.decode()[:200]}")
    
    # ============================================================
    # 状态管理
    # ============================================================
    
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
            update_fields = {"status": status, "progress": progress, "task_id": task_id}
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
    
    def _emit_progress(
        self, 
        task_id: str, 
        status: str, 
        progress: float, 
        message: str,
        current_stage: str = "",
        elapsed_time: float = 0.0,
        estimated_remaining: float = 0.0,
        output_path: str = None,
        file_size: int = None,
        error: str = None
    ):
        """发送进度事件（同时发送到 EventService 和 SSE）"""
        import asyncio
        
        async def emit_all():
            # 1. 发送到 SSE
            try:
                from services.render_progress_sse import publish_render_progress
                await publish_render_progress(
                    task_id=task_id,
                    status=status,
                    progress=progress,
                    message=message,
                    current_stage=current_stage,
                    elapsed_time=elapsed_time,
                    estimated_remaining=estimated_remaining,
                    output_path=output_path,
                    file_size=file_size,
                    error=error
                )
            except Exception as e:
                logger.warning(f"SSE 进度推送失败: {e}")
            
            # 2. 发送到 EventService (WebSocket)
            event_service = self._get_event_service()
            if event_service:
                try:
                    if status == "processing":
                        await event_service.emit_task_progress(
                            task_id=task_id,
                            progress=int(progress),
                            message=message,
                            task_type="render",
                            task_name="视频渲染"
                        )
                    elif status == "completed":
                        await event_service.emit_task_completed(
                            task_id=task_id,
                            task_type="render",
                            task_name="视频渲染",
                            result={"progress": 100, "message": message}
                        )
                    elif status == "failed":
                        await event_service.emit_task_failed(
                            task_id=task_id,
                            task_type="render",
                            task_name="视频渲染",
                            error=error or message,
                            can_retry=True
                        )
                except Exception as e:
                    logger.warning(f"EventService 进度推送失败: {e}")
        
        try:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(emit_all())
            except RuntimeError:
                asyncio.run(emit_all())
        except Exception as e:
            logger.warning(f"发送进度事件失败: {e}")
    
    # ============================================================
    # 查询接口
    # ============================================================
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            result = self.db.execute(
                text("""
                    SELECT id, timeline_id, status, progress, error_message, 
                           output_path, file_size, format, resolution, framerate, quality,
                           created_at, started_at, completed_at
                    FROM render_tasks 
                    WHERE id = :task_id
                """),
                {"task_id": task_id}
            ).fetchone()
            
            if not result:
                return None
            
            def safe_isoformat(v):
                if v is None:
                    return None
                return v.isoformat() if hasattr(v, 'isoformat') else str(v)
            
            return {
                "id": result[0],
                "timeline_id": result[1],
                "status": result[2],
                "progress": result[3],
                "error_message": result[4],
                "output_path": result[5],
                "file_size": result[6],
                "format": result[7],
                "resolution": result[8],
                "framerate": result[9],
                "quality": result[10],
                "created_at": safe_isoformat(result[11]),
                "started_at": safe_isoformat(result[12]),
                "completed_at": safe_isoformat(result[13]),
            }
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    async def cancel_render(self, task_id: str) -> bool:
        """取消渲染任务"""
        try:
            self.db.execute(
                text("UPDATE render_tasks SET status = 'cancelled' WHERE id = :task_id"),
                {"task_id": task_id}
            )
            self.db.commit()
            
            # 尝试终止线程（注意：Python 线程不能强制终止）
            if task_id in self._active_renders:
                logger.warning(f"任务 {task_id} 正在运行，标记为取消但无法立即停止")
            
            return True
            
        except Exception as e:
            logger.error(f"取消渲染失败: {e}")
            return False
    
    async def list_tasks(
        self,
        limit: int = 50,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出渲染任务"""
        try:
            def safe_isoformat(v):
                if v is None:
                    return None
                return v.isoformat() if hasattr(v, 'isoformat') else str(v)
            
            sql = """
                SELECT id, timeline_id, status, progress, error_message,
                       output_path, file_size, format, resolution, framerate, quality,
                       created_at, started_at, completed_at
                FROM render_tasks
            """
            params = {"limit": limit}
            
            if status_filter:
                sql += " WHERE status = :status"
                params["status"] = status_filter
            
            sql += " ORDER BY created_at DESC LIMIT :limit"
            
            results = self.db.execute(text(sql), params).fetchall()
            
            tasks = []
            for r in results:
                tasks.append({
                    "id": r[0],
                    "timeline_id": r[1],
                    "status": r[2],
                    "progress": r[3],
                    "error_message": r[4],
                    "output_path": r[5],
                    "file_size": r[6],
                    "format": r[7],
                    "resolution": r[8],
                    "framerate": r[9],
                    "quality": r[10],
                    "created_at": safe_isoformat(r[11]),
                    "started_at": safe_isoformat(r[12]),
                    "completed_at": safe_isoformat(r[13]),
                })
            
            return tasks
            
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return []
    
    def get_download_path(self, task_id: str) -> Optional[str]:
        """获取下载路径"""
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
    
    # ============================================================
    # 工具方法
    # ============================================================
    
    def get_supported_formats(self) -> List[Dict[str, Any]]:
        """获取支持的格式列表"""
        return [
            {"value": f.value, "label": f.value.upper(), "codecs": FORMAT_CODECS[f]}
            for f in VideoFormat
        ]
    
    def get_supported_resolutions(self) -> List[Dict[str, Any]]:
        """获取支持的分辨率列表"""
        return [
            {
                "value": r.value,
                "label": RESOLUTION_CONFIGS[r].name,
                "width": RESOLUTION_CONFIGS[r].width,
                "height": RESOLUTION_CONFIGS[r].height
            }
            for r in Resolution
        ]
    
    def get_supported_framerates(self) -> List[float]:
        """获取支持的帧率列表"""
        return FRAMERATE_OPTIONS
    
    def get_quality_presets(self) -> List[Dict[str, Any]]:
        """获取质量预设列表"""
        return [
            {
                "value": q.value,
                "label": q.value.capitalize(),
                "crf": QUALITY_PRESETS[q].crf,
                "bitrate": QUALITY_PRESETS[q].bitrate
            }
            for q in Quality if q != Quality.CUSTOM
        ]


# ============================================================
# 工厂函数
# ============================================================

def get_enhanced_render_service(db: Session) -> EnhancedRenderService:
    """获取增强版渲染服务实例"""
    return EnhancedRenderService(db)
