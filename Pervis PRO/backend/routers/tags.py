"""
标签管理API路由
支持标签层级管理和权重调整
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from database import get_db
from services.tag_manager import TagManager

router = APIRouter()


# 请求模型
class TagHierarchyUpdate(BaseModel):
    asset_id: str
    tag_id: str
    parent_id: Optional[str] = None
    order: int = 0


class TagWeightUpdate(BaseModel):
    asset_id: str
    tag_id: str
    weight: float = Field(..., ge=0.0, le=1.0)


class BatchTagUpdate(BaseModel):
    asset_id: str
    updates: List[dict]


# API端点
@router.get("/{asset_id}")
async def get_video_tags(asset_id: str, db: Session = Depends(get_db)):
    """获取视频的所有标签"""
    manager = TagManager(db)
    result = await manager.get_video_tags(asset_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.put("/hierarchy")
async def update_tag_hierarchy(request: TagHierarchyUpdate, db: Session = Depends(get_db)):
    """更新标签层级"""
    manager = TagManager(db)
    result = await manager.update_tag_hierarchy(
        asset_id=request.asset_id,
        tag_id=request.tag_id,
        parent_tag_id=request.parent_id,
        order=request.order
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.put("/weight")
async def update_tag_weight(request: TagWeightUpdate, db: Session = Depends(get_db)):
    """更新标签权重"""
    manager = TagManager(db)
    result = await manager.update_tag_weight(
        asset_id=request.asset_id,
        tag_id=request.tag_id,
        weight=request.weight
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/batch-update")
async def batch_update_tags(request: BatchTagUpdate, db: Session = Depends(get_db)):
    """批量更新标签"""
    manager = TagManager(db)
    result = await manager.batch_update_tags(
        asset_id=request.asset_id,
        updates=request.updates
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result
