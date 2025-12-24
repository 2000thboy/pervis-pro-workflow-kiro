"""
批量处理API路由
Phase 4: 批量上传、队列管理、性能监控
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from services.batch_processor import get_batch_processor, TaskPriority
from services.database_service import DatabaseService
from models.base import AssetCreate
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import os

router = APIRouter(prefix="/api/batch", tags=["batch"])

class BatchUploadResponse(BaseModel):
    task_ids: List[str]
    total_files: int
    estimated_processing_time: float

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    result: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: float

@router.post("/upload", response_model=BatchUploadResponse)
async def batch_upload_assets(
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    priority: str = Form("normal"),  # low, normal, high, urgent
    enable_transcription: bool = Form(True),
    enable_visual_analysis: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    批量上传资产文件
    """
    
    try:
        if not files:
            raise HTTPException(status_code=400, detail="没有上传文件")
        
        if len(files) > 50:  # 限制批量上传数量
            raise HTTPException(status_code=400, detail="批量上传文件数量不能超过50个")
        
        # 解析优先级
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)
        
        db_service = DatabaseService(db)
        batch_processor = get_batch_processor()
        
        task_ids = []
        total_estimated_time = 0.0
        
        for file in files:
            # 验证文件类型
            if not file.filename:
                continue
            
            # 创建资产记录
            asset_data = AssetCreate(
                project_id=project_id,
                filename=file.filename,
                mime_type=file.content_type or "application/octet-stream",
                source="batch_upload"
            )
            
            asset = db_service.create_asset(asset_data)
            
            # 保存上传文件到临时位置
            temp_file_path = await _save_uploaded_file(file)
            
            # 提交视频处理任务
            video_task_id = await batch_processor.submit_task(
                task_type="video_processing",
                asset_id=asset.id,
                file_path=temp_file_path,
                parameters={
                    "enable_transcription": enable_transcription,
                    "enable_visual_analysis": enable_visual_analysis
                },
                priority=task_priority
            )
            
            task_ids.append(video_task_id)
            
            # 估算处理时间 (简化版本)
            estimated_time = 60.0  # 基础处理时间
            if enable_transcription:
                estimated_time += 30.0
            if enable_visual_analysis:
                estimated_time += 45.0
            
            total_estimated_time += estimated_time
        
        return BatchUploadResponse(
            task_ids=task_ids,
            total_files=len(task_ids),
            estimated_processing_time=total_estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    
    try:
        batch_processor = get_batch_processor()
        task_status = await batch_processor.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskStatusResponse(
            task_id=task_status["id"],
            status=task_status["status"],
            progress=task_status["progress"],
            result=task_status.get("result"),
            error=task_status.get("error"),
            processing_time=task_status.get("processing_time", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")

@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消任务
    """
    
    try:
        batch_processor = get_batch_processor()
        success = await batch_processor.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无法取消")
        
        return {
            "status": "success",
            "message": f"任务 {task_id} 已取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务取消失败: {str(e)}")

@router.get("/queue/status")
async def get_queue_status():
    """
    获取队列状态
    """
    
    try:
        batch_processor = get_batch_processor()
        status = await batch_processor.get_queue_status()
        
        return {
            "status": "success",
            "queue_status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"队列状态查询失败: {str(e)}")

@router.get("/tasks/history")
async def get_task_history(limit: int = 100):
    """
    获取任务历史
    """
    
    try:
        if limit > 1000:
            limit = 1000  # 限制最大查询数量
        
        batch_processor = get_batch_processor()
        history = await batch_processor.get_task_history(limit)
        
        return {
            "status": "success",
            "tasks": history,
            "total_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务历史查询失败: {str(e)}")

@router.post("/queue/cleanup")
async def cleanup_old_tasks(max_age_hours: int = 24):
    """
    清理旧任务
    """
    
    try:
        if max_age_hours < 1 or max_age_hours > 168:  # 1小时到1周
            raise HTTPException(status_code=400, detail="清理时间范围必须在1-168小时之间")
        
        batch_processor = get_batch_processor()
        cleaned_count = await batch_processor.cleanup_old_tasks(max_age_hours)
        
        return {
            "status": "success",
            "message": f"清理了 {cleaned_count} 个旧任务",
            "cleaned_count": cleaned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务清理失败: {str(e)}")

@router.get("/stats")
async def get_processing_stats():
    """
    获取处理统计信息
    """
    
    try:
        batch_processor = get_batch_processor()
        queue_status = await batch_processor.get_queue_status()
        
        # 获取系统资源信息
        import psutil
        
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
        
        return {
            "status": "success",
            "processing_stats": queue_status["stats"],
            "system_stats": system_stats,
            "queue_info": {
                "queue_size": queue_status["queue_size"],
                "running_tasks": queue_status["running_tasks"],
                "active_workers": queue_status["active_workers"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")

@router.post("/process/asset/{asset_id}")
async def process_single_asset(
    asset_id: str,
    task_type: str,  # video_processing, transcription, visual_analysis
    priority: str = "normal",
    parameters: Optional[Dict] = None,
    db: Session = Depends(get_db)
):
    """
    处理单个资产
    """
    
    try:
        # 验证任务类型
        valid_task_types = ["video_processing", "transcription", "visual_analysis"]
        if task_type not in valid_task_types:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的任务类型，支持的类型: {valid_task_types}"
            )
        
        # 解析优先级
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)
        
        # 检查资产是否存在
        db_service = DatabaseService(db)
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        if not asset.file_path:
            raise HTTPException(status_code=400, detail="资产文件路径不存在")
        
        # 提交任务
        batch_processor = get_batch_processor()
        task_id = await batch_processor.submit_task(
            task_type=task_type,
            asset_id=asset_id,
            file_path=asset.file_path,
            parameters=parameters or {},
            priority=task_priority
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": f"任务已提交: {task_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")

async def _save_uploaded_file(file: UploadFile) -> str:
    """保存上传文件到临时位置"""
    
    # 创建临时文件
    suffix = os.path.splitext(file.filename)[1] if file.filename else ""
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    
    try:
        # 读取并写入文件内容
        content = await file.read()
        with os.fdopen(temp_fd, 'wb') as temp_file:
            temp_file.write(content)
        
        return temp_path
        
    except Exception:
        # 如果出错，清理临时文件
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise