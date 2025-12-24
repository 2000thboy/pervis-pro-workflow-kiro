"""
分析API路由
提供素材分析功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from services.analysis_log_service import AnalysisLogService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    asset_id: str
    analysis_type: str = "full"


@router.post("/start")
async def start_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """开始素材分析"""
    try:
        service = AnalysisLogService(db)
        result = await service.start_analysis(
            asset_id=request.asset_id,
            analysis_type=request.analysis_type
        )
        
        return {
            "status": "success",
            "analysis_id": result.get("id"),
            "message": "分析任务已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{analysis_id}")
async def get_analysis_status(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """获取分析任务状态"""
    try:
        service = AnalysisLogService(db)
        status = await service.get_analysis_status(analysis_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_analysis_logs(
    asset_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取分析日志"""
    try:
        service = AnalysisLogService(db)
        logs = await service.get_logs(asset_id=asset_id)
        
        return {
            "status": "success",
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
