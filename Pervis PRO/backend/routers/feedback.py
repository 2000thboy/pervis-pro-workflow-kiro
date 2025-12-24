"""
反馈收集路由
Phase 2: 真实数据库存储反馈信息
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.database_service import DatabaseService
from models.base import FeedbackRequest, FeedbackResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/record", response_model=FeedbackResponse)
async def record_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    记录用户反馈
    Phase 2: 存储到数据库，为后续学习算法准备数据
    """
    
    try:
        db_service = DatabaseService(db)
        
        # 创建反馈记录
        feedback = db_service.create_feedback(
            beat_id=request.beat_id,
            asset_id=request.asset_id,
            segment_id=request.segment_id,
            action=request.action,
            context=request.context,
            query_context=getattr(request, 'query_context', None)
        )
        
        logger.info(f"记录反馈: {request.action} for asset {request.asset_id}")
        
        return FeedbackResponse(
            status="recorded",
            feedback_id=feedback.id
        )
        
    except Exception as e:
        logger.error(f"反馈记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"反馈记录失败: {str(e)}")