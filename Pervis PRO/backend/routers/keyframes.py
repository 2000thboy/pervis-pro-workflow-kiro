# -*- coding: utf-8 -*-
"""
关键帧 API 路由

Feature: pervis-asset-tagging
Task: 6.4 关键帧 API

提供关键帧提取和查询的 REST API。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from models.keyframe import (
    ExtractionStrategy,
    KeyFrameConfig,
    KeyFrameData,
)
from services.keyframe_extractor import (
    ExtractionResult,
    extract_keyframes,
    get_keyframe_extractor,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keyframes", tags=["keyframes"])


# ============================================================
# 请求/响应模型
# ============================================================

class ExtractKeyframesRequest(BaseModel):
    """提取关键帧请求"""
    video_path: str = Field(..., description="视频文件路径")
    asset_id: str = Field(..., description="素材 ID")
    strategy: str = Field(default="hybrid", description="提取策略")
    max_frames: int = Field(default=20, ge=1, le=100, description="最大帧数")
    interval_seconds: float = Field(default=5.0, ge=0.5, description="固定间隔（秒）")
    generate_embeddings: bool = Field(default=False, description="是否生成视觉嵌入")


class KeyframeResponse(BaseModel):
    """关键帧响应"""
    keyframe_id: str
    asset_id: str
    frame_index: int
    timestamp: float
    timecode: str
    thumbnail_url: str
    scene_id: int
    is_scene_start: bool
    motion_score: float
    brightness: float
    has_embedding: bool


class ExtractKeyframesResponse(BaseModel):
    """提取关键帧响应"""
    success: bool
    asset_id: str
    keyframes: List[KeyframeResponse]
    total_frames: int
    duration: float
    fps: float
    extraction_time_ms: float
    error_message: str = ""


class GetKeyframesResponse(BaseModel):
    """获取关键帧列表响应"""
    asset_id: str
    keyframes: List[KeyframeResponse]
    total: int


# ============================================================
# 内存存储（简化实现）
# ============================================================

# 关键帧缓存：asset_id -> List[KeyFrameData]
_keyframe_cache: Dict[str, List[KeyFrameData]] = {}


def _keyframe_to_response(kf: KeyFrameData) -> KeyframeResponse:
    """转换为响应模型"""
    return KeyframeResponse(
        keyframe_id=kf.keyframe_id,
        asset_id=kf.asset_id,
        frame_index=kf.frame_index,
        timestamp=kf.timestamp,
        timecode=kf.timecode,
        thumbnail_url=f"/api/keyframes/{kf.keyframe_id}/thumbnail",
        scene_id=kf.scene_id,
        is_scene_start=kf.is_scene_start,
        motion_score=kf.motion_score,
        brightness=kf.brightness,
        has_embedding=kf.visual_embedding is not None,
    )


# ============================================================
# API 端点
# ============================================================

@router.post("/extract", response_model=ExtractKeyframesResponse)
async def extract_keyframes_api(request: ExtractKeyframesRequest):
    """
    提取关键帧
    
    从视频中提取关键帧，支持多种提取策略：
    - scene_change: 场景变化检测
    - interval: 固定间隔
    - motion: 动作峰值
    - hybrid: 混合策略（推荐）
    """
    try:
        # 构建配置
        strategy = ExtractionStrategy(request.strategy)
        config = KeyFrameConfig(
            strategy=strategy,
            max_frames=request.max_frames,
            interval_seconds=request.interval_seconds,
        )
        
        # 提取关键帧
        result = await extract_keyframes(
            video_path=request.video_path,
            asset_id=request.asset_id,
            config=config,
        )
        
        if result.success:
            # 缓存关键帧
            _keyframe_cache[request.asset_id] = result.keyframes
        
        return ExtractKeyframesResponse(
            success=result.success,
            asset_id=request.asset_id,
            keyframes=[_keyframe_to_response(kf) for kf in result.keyframes],
            total_frames=result.total_frames,
            duration=result.duration,
            fps=result.fps,
            extraction_time_ms=result.extraction_time_ms,
            error_message=result.error_message,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"提取关键帧失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assets/{asset_id}/keyframes", response_model=ExtractKeyframesResponse)
async def extract_asset_keyframes(
    asset_id: str,
    strategy: str = Query(default="hybrid", description="提取策略"),
    max_frames: int = Query(default=20, ge=1, le=100, description="最大帧数"),
    generate_embeddings: bool = Query(default=False, description="是否生成视觉嵌入"),
):
    """
    为指定素材提取关键帧
    
    需要素材已经存在于系统中。
    """
    # TODO: 从数据库获取素材路径
    # 这里简化处理，假设素材路径可以从 asset_id 推断
    
    raise HTTPException(
        status_code=501,
        detail="请使用 /api/keyframes/extract 端点并提供完整的视频路径"
    )


@router.get("/assets/{asset_id}/keyframes", response_model=GetKeyframesResponse)
async def get_asset_keyframes(asset_id: str):
    """
    获取素材的关键帧列表
    """
    keyframes = _keyframe_cache.get(asset_id, [])
    
    return GetKeyframesResponse(
        asset_id=asset_id,
        keyframes=[_keyframe_to_response(kf) for kf in keyframes],
        total=len(keyframes),
    )


@router.get("/{keyframe_id}/thumbnail")
async def get_keyframe_thumbnail(keyframe_id: str):
    """
    获取关键帧缩略图
    """
    # 在缓存中查找关键帧
    for asset_id, keyframes in _keyframe_cache.items():
        for kf in keyframes:
            if kf.keyframe_id == keyframe_id:
                if os.path.exists(kf.image_path):
                    return FileResponse(
                        kf.image_path,
                        media_type="image/jpeg",
                        filename=os.path.basename(kf.image_path),
                    )
                else:
                    raise HTTPException(status_code=404, detail="缩略图文件不存在")
    
    raise HTTPException(status_code=404, detail="关键帧不存在")


@router.get("/{keyframe_id}", response_model=KeyframeResponse)
async def get_keyframe(keyframe_id: str):
    """
    获取单个关键帧信息
    """
    # 在缓存中查找关键帧
    for asset_id, keyframes in _keyframe_cache.items():
        for kf in keyframes:
            if kf.keyframe_id == keyframe_id:
                return _keyframe_to_response(kf)
    
    raise HTTPException(status_code=404, detail="关键帧不存在")


@router.delete("/assets/{asset_id}/keyframes")
async def delete_asset_keyframes(asset_id: str):
    """
    删除素材的所有关键帧
    """
    if asset_id in _keyframe_cache:
        # 删除缩略图文件
        for kf in _keyframe_cache[asset_id]:
            if os.path.exists(kf.image_path):
                try:
                    os.remove(kf.image_path)
                except Exception as e:
                    logger.warning(f"删除缩略图失败: {e}")
        
        # 清除缓存
        del _keyframe_cache[asset_id]
        
        return {"success": True, "message": f"已删除素材 {asset_id} 的所有关键帧"}
    
    return {"success": True, "message": "素材没有关键帧"}


@router.get("/strategies")
async def get_extraction_strategies():
    """
    获取支持的提取策略列表
    """
    return {
        "strategies": [
            {
                "value": "scene_change",
                "name": "场景变化检测",
                "description": "基于 PySceneDetect 检测场景切换点",
            },
            {
                "value": "interval",
                "name": "固定间隔",
                "description": "每 N 秒提取一帧",
            },
            {
                "value": "motion",
                "name": "动作峰值",
                "description": "基于运动强度提取关键帧",
            },
            {
                "value": "hybrid",
                "name": "混合策略",
                "description": "场景变化 + 固定间隔补充（推荐）",
            },
        ]
    }
