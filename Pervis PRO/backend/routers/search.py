# -*- coding: utf-8 -*-
"""
搜索 API 路由

Feature: pervis-asset-tagging
Task: 3.3 搜索 API

提供素材搜索接口：
- POST /api/search - 混合搜索
- GET /api/search/stats - 搜索统计
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.search_service import (
    HybridSearchService,
    SearchMode,
    SearchRequest,
    SearchResponse,
    get_search_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class SearchRequestModel(BaseModel):
    """搜索请求模型"""
    query: str = Field(default="", description="查询文本")
    tags: Dict[str, Any] = Field(default_factory=dict, description="标签过滤")
    mode: str = Field(default="HYBRID", description="搜索模式: TAG_ONLY, VECTOR_ONLY, HYBRID, FILTER_THEN_RANK")
    tag_weight: float = Field(default=0.4, ge=0, le=1, description="标签权重")
    vector_weight: float = Field(default=0.6, ge=0, le=1, description="向量权重")
    top_k: int = Field(default=5, ge=1, le=100, description="返回数量")
    min_score: float = Field(default=0.0, ge=0, le=1, description="最低分数阈值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "炭治郎使用水之呼吸战斗",
                "tags": {
                    "action_type": "FIGHT",
                    "characters": ["炭治郎"]
                },
                "mode": "HYBRID",
                "tag_weight": 0.4,
                "vector_weight": 0.6,
                "top_k": 5
            }
        }


class SearchResultItemModel(BaseModel):
    """搜索结果项模型"""
    segment_id: str
    video_path: str
    score: float
    tag_score: float
    vector_score: float
    tags: Dict[str, Any]
    thumbnail: str
    description: str
    match_reason: str


class SearchResponseModel(BaseModel):
    """搜索响应模型"""
    results: List[SearchResultItemModel]
    total: int
    search_time_ms: float
    mode: str
    query: str


class SearchStatsModel(BaseModel):
    """搜索统计模型"""
    total_assets: int
    indexed_assets: int
    embedding_coverage: float
    tag_coverage: Dict[str, float]


# ============================================================
# API 端点
# ============================================================

@router.post("", response_model=SearchResponseModel)
async def search_assets(request: SearchRequestModel):
    """
    搜索素材
    
    支持的搜索模式：
    - TAG_ONLY: 仅标签匹配
    - VECTOR_ONLY: 仅向量搜索
    - HYBRID: 混合搜索（默认）
    - FILTER_THEN_RANK: 先过滤后排序
    
    标签字段：
    - L1: scene_type, time_of_day, shot_size
    - L2: camera_move, action_type, mood
    - L3: characters, props, vfx, environment
    - L4: free_tags, source_work
    """
    try:
        service = get_search_service()
        
        # 验证搜索模式
        try:
            mode = SearchMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的搜索模式: {request.mode}，支持: TAG_ONLY, VECTOR_ONLY, HYBRID, FILTER_THEN_RANK"
            )
        
        # 构建搜索请求
        search_request = SearchRequest(
            query=request.query,
            tags=request.tags,
            mode=mode,
            tag_weight=request.tag_weight,
            vector_weight=request.vector_weight,
            top_k=request.top_k,
            min_score=request.min_score,
        )
        
        # 执行搜索
        response = await service.search(search_request)
        
        return response.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/stats", response_model=SearchStatsModel)
async def get_search_stats():
    """获取搜索统计信息"""
    try:
        service = get_search_service()
        await service.initialize()
        
        store = service.video_store
        total = await store.count()
        
        # 统计嵌入覆盖率
        embedded_count = 0
        tag_stats = {
            "scene_type": 0,
            "time_of_day": 0,
            "shot_size": 0,
            "camera_move": 0,
            "action_type": 0,
            "mood": 0,
            "characters": 0,
            "vfx": 0,
        }
        
        if hasattr(store, '_segments'):
            for segment in store._segments.values():
                if segment.embedding:
                    embedded_count += 1
                
                tags = segment.tags
                for field in tag_stats:
                    value = tags.get(field)
                    if value and value not in ["UNKNOWN", "未知", ""]:
                        if isinstance(value, list) and value:
                            tag_stats[field] += 1
                        elif not isinstance(value, list):
                            tag_stats[field] += 1
        
        # 计算覆盖率
        embedding_coverage = embedded_count / total if total > 0 else 0
        tag_coverage = {
            field: count / total if total > 0 else 0
            for field, count in tag_stats.items()
        }
        
        return {
            "total_assets": total,
            "indexed_assets": total,
            "embedding_coverage": round(embedding_coverage, 4),
            "tag_coverage": {k: round(v, 4) for k, v in tag_coverage.items()},
        }
        
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/quick")
async def quick_search(
    query: str,
    top_k: int = 5,
    mode: str = "HYBRID"
):
    """
    快速搜索（简化接口）
    
    直接使用查询文本进行搜索，自动解析标签。
    """
    try:
        service = get_search_service()
        
        # 简单的标签解析
        tags = {}
        query_lower = query.lower()
        
        # 动作类型
        if any(k in query for k in ["战斗", "打斗", "攻击"]):
            tags["action_type"] = "FIGHT"
        elif any(k in query for k in ["追逐", "追"]):
            tags["action_type"] = "CHASE"
        elif any(k in query for k in ["对话", "说话"]):
            tags["action_type"] = "DIALOGUE"
        
        # 情绪
        if any(k in query for k in ["热血", "燃"]):
            tags["mood"] = "EPIC"
        elif any(k in query for k in ["悲伤", "哭"]):
            tags["mood"] = "SAD"
        elif any(k in query for k in ["紧张", "危险"]):
            tags["mood"] = "TENSE"
        
        # 角色
        characters = []
        for char in ["炭治郎", "善逸", "伊之助", "弥豆子", "义勇"]:
            if char in query:
                characters.append(char)
        if characters:
            tags["characters"] = characters
        
        # 构建请求
        search_request = SearchRequest(
            query=query,
            tags=tags,
            mode=SearchMode(mode),
            top_k=top_k,
        )
        
        response = await service.search(search_request)
        
        return {
            "query": query,
            "parsed_tags": tags,
            "results": response.to_dict()["results"],
            "total": response.total,
            "search_time_ms": response.search_time_ms,
        }
        
    except Exception as e:
        logger.error(f"快速搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ============================================================
# 多模态搜索 API
# ============================================================

class MultimodalWeightsModel(BaseModel):
    """多模态权重模型"""
    text: float = Field(default=0.3, ge=0, le=1, description="文本权重")
    visual: float = Field(default=0.4, ge=0, le=1, description="视觉权重")
    tag: float = Field(default=0.3, ge=0, le=1, description="标签权重")


class KeyFrameMatchModel(BaseModel):
    """关键帧匹配模型"""
    keyframe_id: str
    timestamp: float
    timecode: str
    thumbnail_path: str
    similarity: float
    suggested_in_point: float
    suggested_out_point: float


class MultimodalSearchRequestModel(BaseModel):
    """多模态搜索请求模型"""
    query: str = Field(default="", description="查询文本")
    tags: Dict[str, Any] = Field(default_factory=dict, description="标签过滤")
    mode: str = Field(default="MULTIMODAL", description="搜索模式: TEXT_ONLY, VISUAL_ONLY, TAG_ONLY, MULTIMODAL")
    weights: MultimodalWeightsModel = Field(default_factory=MultimodalWeightsModel, description="权重配置")
    top_k: int = Field(default=5, ge=1, le=100, description="返回数量")
    min_score: float = Field(default=0.0, ge=0, le=1, description="最低分数阈值")
    include_keyframes: bool = Field(default=True, description="是否返回关键帧")
    max_keyframes_per_asset: int = Field(default=3, ge=1, le=10, description="每个素材最多返回的关键帧数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "炭治郎使用水之呼吸战斗",
                "tags": {"action_type": "FIGHT"},
                "mode": "MULTIMODAL",
                "weights": {"text": 0.3, "visual": 0.4, "tag": 0.3},
                "top_k": 5,
                "include_keyframes": True
            }
        }


class MultimodalSearchResultModel(BaseModel):
    """多模态搜索结果模型"""
    asset_id: str
    asset_path: str
    final_score: float
    text_score: float
    visual_score: float
    tag_score: float
    tags: Dict[str, Any]
    thumbnail: str
    description: str
    matched_keyframes: List[KeyFrameMatchModel]


class MultimodalSearchResponseModel(BaseModel):
    """多模态搜索响应模型"""
    results: List[MultimodalSearchResultModel]
    total: int
    search_time_ms: float
    mode: str
    query: str


@router.post("/multimodal", response_model=MultimodalSearchResponseModel)
async def multimodal_search_assets(request: MultimodalSearchRequestModel):
    """
    多模态搜索素材
    
    支持的搜索模式：
    - TEXT_ONLY: 仅文本语义搜索
    - VISUAL_ONLY: 仅视觉相似搜索
    - TAG_ONLY: 仅标签匹配
    - MULTIMODAL: 多模态融合（默认）
    
    返回结果包含：
    - 素材信息
    - 各维度分数（文本、视觉、标签）
    - 匹配的关键帧及建议的入出点
    """
    try:
        from services.multimodal_search import (
            MultimodalSearchService,
            MultimodalSearchMode,
            MultimodalSearchRequest,
            MultimodalWeights,
            get_multimodal_search_service,
        )
        
        service = get_multimodal_search_service()
        
        # 验证搜索模式
        try:
            mode = MultimodalSearchMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的搜索模式: {request.mode}，支持: TEXT_ONLY, VISUAL_ONLY, TAG_ONLY, MULTIMODAL"
            )
        
        # 构建权重配置
        weights = MultimodalWeights(
            text=request.weights.text,
            visual=request.weights.visual,
            tag=request.weights.tag,
        )
        
        # 构建搜索请求
        search_request = MultimodalSearchRequest(
            query=request.query,
            tags=request.tags,
            mode=mode,
            weights=weights,
            top_k=request.top_k,
            min_score=request.min_score,
            include_keyframes=request.include_keyframes,
            max_keyframes_per_asset=request.max_keyframes_per_asset,
        )
        
        # 执行搜索
        response = await service.search(search_request)
        
        return response.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多模态搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"多模态搜索失败: {str(e)}")


@router.post("/by-image")
async def search_by_image(
    image_path: str,
    top_k: int = 10,
):
    """
    以图搜图
    
    使用图像进行视觉相似度搜索，返回相似的素材和关键帧。
    
    Args:
        image_path: 查询图像路径
        top_k: 返回数量
    """
    try:
        from services.multimodal_search import get_multimodal_search_service
        
        service = get_multimodal_search_service()
        results = await service.search_by_image(image_path, top_k=top_k)
        
        return {
            "results": [r.to_dict() for r in results],
            "total": len(results),
            "query_image": image_path,
        }
        
    except Exception as e:
        logger.error(f"以图搜图失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"以图搜图失败: {str(e)}")


@router.get("/visual/stats")
async def get_visual_search_stats():
    """获取视觉搜索统计信息"""
    try:
        from services.visual_vector_store import get_visual_store
        
        store = get_visual_store()
        stats = store.stats()
        
        return {
            "total_keyframe_vectors": stats["total_vectors"],
            "total_assets_with_visual": stats["total_assets"],
            "vector_dimension": stats["dimension"],
            "storage_path": stats["storage_path"],
        }
        
    except Exception as e:
        logger.error(f"获取视觉搜索统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
