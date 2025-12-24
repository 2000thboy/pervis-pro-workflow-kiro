"""
AutoCut API路由
提供自动剪辑编排服务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel

from database import get_db
from services.autocut_orchestrator import AutoCutOrchestrator
from models.base import Beat

router = APIRouter(prefix="/api/autocut", tags=["autocut"])


class AutoCutRequest(BaseModel):
    """自动剪辑请求"""
    project_id: str = "default_project"  # 添加默认值
    beat_ids: List[str] = []  # 添加默认值
    beats: List[dict]  # 前端直接传递的beats数据
    available_assets: List[dict]  # 前端直接传递的assets数据


class AutoCutResponse(BaseModel):
    """自动剪辑响应"""
    status: str
    timeline: dict
    decisions: List[dict]
    processing_time: float


@router.post("/generate", response_model=AutoCutResponse)
async def generate_autocut_timeline(
    request: AutoCutRequest,
    db: Session = Depends(get_db)
):
    """
    生成自动剪辑时间轴
    
    这是MVP的核心API：
    1. 接收Beat列表
    2. 调用AutoCut Orchestrator
    3. 返回智能生成的时间轴
    """
    try:
        # 1. 处理Beat数据 - 支持前端直接传递或从数据库获取
        beats = []
        
        # 如果前端直接传递了beats数据，优先使用
        if request.beats:
            for beat_data in request.beats:
                # 处理标签字段：如果是字符串则转换为列表
                def parse_tags(tag_value):
                    if isinstance(tag_value, str):
                        return [tag_value] if tag_value else []
                    elif isinstance(tag_value, list):
                        return tag_value
                    else:
                        return []
                
                beat = Beat(
                    id=beat_data.get("id", f"beat_{len(beats)}"),
                    content=beat_data.get("content", ""),
                    emotion_tags=parse_tags(beat_data.get("emotion_tags", [])),
                    scene_tags=parse_tags(beat_data.get("scene_tags", [])),
                    action_tags=parse_tags(beat_data.get("action_tags", [])),
                    cinematography_tags=parse_tags(beat_data.get("cinematography_tags", [])),
                    duration=beat_data.get("duration", 3.0)
                )
                beats.append(beat)
        
        # 如果没有直接传递beats，从数据库获取
        elif request.beat_ids:
            for beat_id in request.beat_ids:
                result = db.execute(
                    text("""
                        SELECT id, content, emotion_tags, scene_tags, action_tags, 
                               cinematography_tags, duration
                        FROM beats 
                        WHERE id = :beat_id
                    """),
                    {"beat_id": beat_id}
                ).fetchone()
                
                if result:
                    # 处理标签字段：如果是字符串则转换为列表
                    def parse_tags(tag_value):
                        if isinstance(tag_value, str):
                            return [tag_value] if tag_value else []
                        elif isinstance(tag_value, list):
                            return tag_value
                        else:
                            return []
                    
                    beat = Beat(
                        id=result[0],
                        content=result[1],
                        emotion_tags=parse_tags(result[2]),
                        scene_tags=parse_tags(result[3]),
                        action_tags=parse_tags(result[4]),
                        cinematography_tags=parse_tags(result[5]),
                        duration=result[6]
                    )
                    beats.append(beat)
        
        if not beats:
            raise HTTPException(status_code=400, detail="未提供Beat数据")
        
        # 2. 处理素材数据 - 支持前端直接传递或从数据库获取
        available_assets = []
        
        # 如果前端直接传递了assets数据，优先使用
        if request.available_assets:
            available_assets = request.available_assets
        else:
            # 从数据库获取可用素材
            assets_result = db.execute(
                text("""
                    SELECT id, filename, mime_type, file_path 
                    FROM assets 
                    WHERE mime_type = 'video/mp4' 
                      AND file_path IS NOT NULL 
                      AND processing_status = 'completed'
                    LIMIT 50
                """)
            ).fetchall()
            
            available_assets = [
                {
                    "id": row[0],
                    "filename": row[1],
                    "mime_type": row[2],
                    "file_path": row[3]
                }
                for row in assets_result
            ]
        
        if not available_assets:
            raise HTTPException(status_code=400, detail="素材库为空")
        
        # 3. 调用AutoCut Orchestrator
        orchestrator = AutoCutOrchestrator(db)
        result = await orchestrator.generate_timeline(beats, available_assets)
        
        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "自动剪辑失败"))
        
        return AutoCutResponse(
            status=result["status"],
            timeline=result["timeline"],
            decisions=result["decisions"],
            processing_time=result["processing_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动剪辑失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AutoCut Orchestrator",
        "version": "1.0.0"
    }
