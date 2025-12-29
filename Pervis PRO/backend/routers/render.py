# -*- coding: utf-8 -*-
"""
渲染 API 路由

Phase 2 Task 2.1: 视频渲染完善
- SSE 实时进度推送
- 渲染任务管理
- 渲染配置查询
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from services.render_progress_sse import (
    get_render_progress_sse,
    RenderProgressEvent,
    publish_render_progress
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# 请求模型
# ============================================================

class StartRenderRequest(BaseModel):
    """启动渲染请求"""
    timeline_id: str
    format: str = "mp4"  # mp4, mov, webm, prores
    resolution: str = "1080p"  # 720p, 1080p, 2k, 4k
    framerate: float = 30.0
    quality: str = "high"  # low, medium, high, ultra
    bitrate: Optional[int] = None
    audio_bitrate: int = 192
    include_audio: bool = True
    watermark: Optional[str] = None


class RenderConfigResponse(BaseModel):
    """渲染配置响应"""
    formats: list
    resolutions: list
    framerates: list
    quality_presets: list


# ============================================================
# SSE 进度推送
# ============================================================

@router.get("/progress/stream/{task_id}")
async def stream_render_progress(task_id: str):
    """
    SSE 流式推送单个任务的渲染进度
    
    使用方法:
    ```javascript
    const eventSource = new EventSource('/api/render/progress/stream/task_id');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data.progress);
    };
    ```
    """
    sse = get_render_progress_sse()
    
    return StreamingResponse(
        sse.subscribe(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )


@router.get("/progress/stream")
async def stream_all_render_progress():
    """
    SSE 流式推送所有渲染任务的进度
    
    适用于渲染任务列表页面，实时更新所有任务状态
    """
    sse = get_render_progress_sse()
    
    return StreamingResponse(
        sse.subscribe(None),  # None 表示订阅所有任务
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/progress/{task_id}")
async def get_render_progress(task_id: str, db: Session = Depends(get_db)):
    """
    获取渲染任务的当前进度（轮询方式）
    
    如果不支持 SSE，可以使用此端点轮询
    """
    # 先从 SSE 缓存获取
    sse = get_render_progress_sse()
    cached = sse.get_latest_progress(task_id)
    
    if cached:
        return {
            "status": "success",
            "task_id": task_id,
            "progress": {
                "status": cached.status,
                "progress": cached.progress,
                "message": cached.message,
                "current_stage": cached.current_stage,
                "elapsed_time": cached.elapsed_time,
                "estimated_remaining": cached.estimated_remaining,
                "output_path": cached.output_path,
                "file_size": cached.file_size,
                "error": cached.error,
                "timestamp": cached.timestamp.isoformat()
            }
        }
    
    # 从数据库获取
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        task_status = await render_service.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "status": "success",
            "task_id": task_id,
            "progress": task_status
        }
        
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        task_status = await render_service.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "status": "success",
            "task_id": task_id,
            "progress": task_status
        }


# ============================================================
# 渲染任务管理
# ============================================================

@router.post("/start")
async def start_render(request: StartRenderRequest, db: Session = Depends(get_db)):
    """
    启动渲染任务
    
    返回 task_id，可用于订阅进度或轮询状态
    """
    try:
        from services.render_service_enhanced import (
            get_enhanced_render_service,
            RenderOptions,
            VideoFormat,
            Resolution,
            Quality
        )
        
        render_service = get_enhanced_render_service(db)
        
        # 构建渲染选项
        try:
            video_format = VideoFormat(request.format)
        except ValueError:
            video_format = VideoFormat.MP4
        
        try:
            resolution = Resolution(request.resolution)
        except ValueError:
            resolution = Resolution.FHD_1080
        
        try:
            quality = Quality(request.quality)
        except ValueError:
            quality = Quality.HIGH
        
        options = RenderOptions(
            format=video_format,
            resolution=resolution,
            framerate=request.framerate,
            quality=quality,
            custom_bitrate=request.bitrate,
            audio_bitrate=request.audio_bitrate,
            include_audio=request.include_audio,
            watermark=request.watermark
        )
        
        # 检查渲染条件
        check_result = await render_service.check_render_requirements(
            request.timeline_id, options
        )
        
        if not check_result.get("can_render"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "无法渲染",
                    "errors": check_result.get("errors", []),
                    "warnings": check_result.get("warnings", [])
                }
            )
        
        # 启动渲染
        task_id = await render_service.start_render(request.timeline_id, options)
        
        # 发布初始进度
        await publish_render_progress(
            task_id=task_id,
            status="pending",
            progress=0,
            message="渲染任务已创建",
            current_stage="初始化"
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "渲染任务已启动",
            "sse_url": f"/api/render/progress/stream/{task_id}",
            "poll_url": f"/api/render/progress/{task_id}",
            "estimated_render_time": check_result.get("estimated_render_time"),
            "estimated_size_mb": check_result.get("estimated_size_mb"),
            "resolution": check_result.get("resolution"),
            "format": check_result.get("format")
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="渲染服务不可用"
        )
    except Exception as e:
        logger.error(f"启动渲染失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{task_id}")
async def cancel_render(task_id: str, db: Session = Depends(get_db)):
    """取消渲染任务"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        success = await render_service.cancel_render(task_id)
        
        if success:
            # 发布取消事件
            await publish_render_progress(
                task_id=task_id,
                status="cancelled",
                progress=0,
                message="渲染已取消"
            )
            return {"status": "success", "message": "任务已取消"}
        else:
            raise HTTPException(status_code=400, detail="取消失败")
            
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        success = await render_service.cancel_render(task_id)
        
        if success:
            return {"status": "success", "message": "任务已取消"}
        else:
            raise HTTPException(status_code=400, detail="取消失败")


@router.get("/tasks")
async def list_render_tasks(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """列出渲染任务"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        tasks = await render_service.list_tasks(limit=limit, status_filter=status)
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        tasks = await render_service.list_tasks(limit=limit)
    
    return {
        "status": "success",
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/tasks/active")
async def list_active_render_tasks(db: Session = Depends(get_db)):
    """列出活跃的渲染任务（进行中）"""
    sse = get_render_progress_sse()
    active_tasks = sse.get_all_active_tasks()
    
    return {
        "status": "success",
        "tasks": [
            {
                "task_id": task_id,
                "status": event.status,
                "progress": event.progress,
                "message": event.message,
                "current_stage": event.current_stage
            }
            for task_id, event in active_tasks.items()
        ],
        "total": len(active_tasks)
    }


@router.get("/download/{task_id}")
async def download_render_result(task_id: str, db: Session = Depends(get_db)):
    """下载渲染结果"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        file_path = render_service.get_download_path(task_id)
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        file_path = render_service.get_download_path(task_id)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在或任务未完成")
    
    from pathlib import Path
    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="video/mp4"
    )


# ============================================================
# 渲染配置
# ============================================================

@router.get("/config")
async def get_render_config(db: Session = Depends(get_db)):
    """获取渲染配置选项"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        
        return {
            "status": "success",
            "formats": render_service.get_supported_formats(),
            "resolutions": render_service.get_supported_resolutions(),
            "framerates": render_service.get_supported_framerates(),
            "quality_presets": render_service.get_quality_presets()
        }
    except ImportError:
        # 回退到基础配置
        return {
            "status": "success",
            "formats": [
                {"value": "mp4", "label": "MP4 (H.264)", "codecs": {"video": "libx264", "audio": "aac"}},
                {"value": "mov", "label": "MOV (QuickTime)", "codecs": {"video": "libx264", "audio": "aac"}},
                {"value": "webm", "label": "WebM (VP9)", "codecs": {"video": "libvpx-vp9", "audio": "libopus"}}
            ],
            "resolutions": [
                {"value": "720p", "label": "720p HD", "width": 1280, "height": 720},
                {"value": "1080p", "label": "1080p Full HD", "width": 1920, "height": 1080},
                {"value": "2k", "label": "2K QHD", "width": 2560, "height": 1440},
                {"value": "4k", "label": "4K UHD", "width": 3840, "height": 2160}
            ],
            "framerates": [23.976, 24, 25, 29.97, 30, 50, 60],
            "quality_presets": [
                {"value": "low", "label": "Low", "crf": 28, "bitrate": "1000k"},
                {"value": "medium", "label": "Medium", "crf": 23, "bitrate": "3000k"},
                {"value": "high", "label": "High", "crf": 18, "bitrate": "8000k"},
                {"value": "ultra", "label": "Ultra", "crf": 15, "bitrate": "15000k"}
            ]
        }


@router.get("/check/{timeline_id}")
async def check_render_requirements(timeline_id: str, db: Session = Depends(get_db)):
    """检查渲染前置条件"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        result = await render_service.check_render_requirements(timeline_id)
        
        return {
            "status": "success",
            "timeline_id": timeline_id,
            "check_result": result
        }
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        result = await render_service.check_render_requirements(timeline_id)
        
        return {
            "status": "success",
            "timeline_id": timeline_id,
            "check_result": result
        }
