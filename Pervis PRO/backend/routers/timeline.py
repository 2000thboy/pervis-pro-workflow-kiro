"""
时间线API路由
Phase 5: 时间线编辑和素材组织
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from services.timeline_service import TimelineService, ClipData

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


# Pydantic模型
class TimelineCreate(BaseModel):
    project_id: str
    name: str = "主时间轴"


class TimelineResponse(BaseModel):
    id: str
    project_id: str
    name: str
    duration: float
    created_at: Optional[str]
    updated_at: Optional[str]


class ClipCreate(BaseModel):
    asset_id: str
    start_time: float
    end_time: float
    trim_start: float = 0.0
    trim_end: Optional[float] = None
    volume: float = 1.0
    is_muted: int = 0
    audio_fade_in: float = 0.0
    audio_fade_out: float = 0.0
    transition_type: Optional[str] = None
    transition_duration: float = 0.0
    order_index: int = 0
    clip_metadata: dict = {}


class ClipUpdate(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None
    volume: Optional[float] = None
    is_muted: Optional[int] = None
    audio_fade_in: Optional[float] = None
    audio_fade_out: Optional[float] = None
    transition_type: Optional[str] = None
    transition_duration: Optional[float] = None
    order_index: Optional[int] = None
    clip_metadata: Optional[dict] = None


class ClipReorder(BaseModel):
    clip_order: List[str]


class AutoCutTimelineCreate(BaseModel):
    project_id: str
    autocut_timeline: dict
    name: str = "AutoCut智能时间轴"


@router.post("/create", response_model=TimelineResponse)
def create_timeline(
    data: TimelineCreate,
    db: Session = Depends(get_db)
):
    """创建新的时间轴"""
    try:
        service = TimelineService(db)
        timeline = service.create_timeline(
            project_id=data.project_id,
            name=data.name
        )
        
        return TimelineResponse(
            id=timeline.id,
            project_id=timeline.project_id,
            name=timeline.name,
            duration=timeline.duration,
            created_at=timeline.created_at.isoformat() if timeline.created_at else None,
            updated_at=timeline.updated_at.isoformat() if timeline.updated_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_timelines(
    project_id: Optional[str] = Query(None, description="项目ID"),
    limit: int = Query(20, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取时间轴列表 - 前端集成修复
    """
    try:
        from sqlalchemy import text
        
        sql = text("""
            SELECT id, project_id, name, duration, created_at, updated_at
            FROM timelines 
            ORDER BY created_at DESC 
            LIMIT :limit
        """)
        result = db.execute(sql, {"limit": limit})
        
        timelines = []
        for row in result:
            timelines.append({
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "duration": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            })
        
        return timelines
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间轴列表失败: {str(e)}")


@router.get("/{timeline_id}")
def get_timeline(
    timeline_id: str,
    db: Session = Depends(get_db)
):
    """获取时间轴及其所有片段"""
    service = TimelineService(db)
    timeline = service.get_timeline_with_clips(timeline_id)
    
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    return timeline


@router.post("/{timeline_id}/clips")
def add_clip(
    timeline_id: str,
    data: ClipCreate,
    db: Session = Depends(get_db)
):
    """添加片段到时间轴"""
    try:
        service = TimelineService(db)
        clip_data = ClipData(data.dict())
        clip = service.add_clip(timeline_id, clip_data)
        
        return {
            "id": clip.id,
            "timeline_id": clip.timeline_id,
            "asset_id": clip.asset_id,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "trim_start": clip.trim_start,
            "trim_end": clip.trim_end,
            "volume": clip.volume,
            "is_muted": clip.is_muted,
            "audio_fade_in": clip.audio_fade_in,
            "audio_fade_out": clip.audio_fade_out,
            "transition_type": clip.transition_type,
            "transition_duration": clip.transition_duration,
            "order_index": clip.order_index,
            "clip_metadata": clip.clip_metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/clips/{clip_id}")
def update_clip(
    clip_id: str,
    data: ClipUpdate,
    db: Session = Depends(get_db)
):
    """更新片段属性"""
    try:
        service = TimelineService(db)
        
        # 只包含非None的字段
        updates = {k: v for k, v in data.dict().items() if v is not None}
        
        clip = service.update_clip(clip_id, updates)
        
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        return {
            "id": clip.id,
            "timeline_id": clip.timeline_id,
            "asset_id": clip.asset_id,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "trim_start": clip.trim_start,
            "trim_end": clip.trim_end,
            "volume": clip.volume,
            "is_muted": clip.is_muted,
            "audio_fade_in": clip.audio_fade_in,
            "audio_fade_out": clip.audio_fade_out,
            "transition_type": clip.transition_type,
            "transition_duration": clip.transition_duration,
            "order_index": clip.order_index,
            "clip_metadata": clip.clip_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clips/{clip_id}")
def delete_clip(
    clip_id: str,
    db: Session = Depends(get_db)
):
    """删除片段"""
    service = TimelineService(db)
    success = service.delete_clip(clip_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return {"message": "Clip deleted successfully"}


@router.post("/{timeline_id}/clips/reorder")
def reorder_clips(
    timeline_id: str,
    data: ClipReorder,
    db: Session = Depends(get_db)
):
    """重新排序片段"""
    service = TimelineService(db)
    success = service.reorder_clips(timeline_id, data.clip_order)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reorder clips")
    
    return {"message": "Clips reordered successfully"}


@router.post("/create-from-autocut", response_model=TimelineResponse)
async def create_timeline_from_autocut(
    data: AutoCutTimelineCreate,
    db: Session = Depends(get_db)
):
    """
    从AutoCut Orchestrator决策创建时间轴
    
    这是MVP的核心端点：强制使用智能决策结果
    """
    try:
        service = TimelineService(db)
        timeline = await service.create_timeline_from_autocut(
            project_id=data.project_id,
            autocut_timeline=data.autocut_timeline,
            name=data.name
        )
        
        return TimelineResponse(
            id=timeline.id,
            project_id=timeline.project_id,
            name=timeline.name,
            duration=timeline.duration,
            created_at=timeline.created_at.isoformat() if timeline.created_at else None,
            updated_at=timeline.updated_at.isoformat() if timeline.updated_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AutoCut时间轴创建失败: {str(e)}")


@router.get("/{timeline_id}/validate")
def validate_timeline(
    timeline_id: str,
    db: Session = Depends(get_db)
):
    """验证时间轴完整性"""
    service = TimelineService(db)
    result = service.validate_timeline(timeline_id)
    
    return result
