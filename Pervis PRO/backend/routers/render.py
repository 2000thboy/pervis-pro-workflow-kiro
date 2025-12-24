"""
渲染API路由
提供视频渲染功能
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import os

from database import get_db
from services.render_service import RenderService

router = APIRouter(prefix="/api/render", tags=["render"])


class RenderRequest(BaseModel):
    timeline_id: str
    format: str = "mp4"
    resolution: str = "1080p"
    framerate: int = 30
    quality: str = "high"
    bitrate: Optional[int] = None
    audio_bitrate: int = 192
    use_proxy: bool = False


@router.get("/{timeline_id}/check")
async def check_render_requirements(
    timeline_id: str,
    db: Session = Depends(get_db)
):
    """检查渲染前置条件"""
    try:
        service = RenderService(db)
        requirements = await service.check_render_requirements(timeline_id)
        
        return {
            "status": "success",
            **requirements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_render(
    request: RenderRequest,
    db: Session = Depends(get_db)
):
    """开始渲染任务"""
    try:
        service = RenderService(db)
        task_id = await service.start_render(
            timeline_id=request.timeline_id,
            format=request.format,
            resolution=request.resolution,
            framerate=request.framerate,
            quality=request.quality,
            bitrate=request.bitrate,
            audio_bitrate=request.audio_bitrate,
            use_proxy=request.use_proxy
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "渲染任务已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status")
async def get_render_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取渲染任务状态"""
    try:
        service = RenderService(db)
        status = await service.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_render(
    task_id: str,
    db: Session = Depends(get_db)
):
    """取消渲染任务"""
    try:
        service = RenderService(db)
        success = await service.cancel_render(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="取消失败")
        
        return {
            "status": "success",
            "message": "任务已取消"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/download")
async def download_render(
    task_id: str,
    db: Session = Depends(get_db)
):
    """下载渲染结果"""
    try:
        service = RenderService(db)
        file_path = service.get_download_path(task_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在或渲染未完成")
        
        filename = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_render_tasks(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """列出所有渲染任务"""
    try:
        service = RenderService(db)
        tasks = await service.list_tasks(limit)
        return {
            "status": "success",
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
