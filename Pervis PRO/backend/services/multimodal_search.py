# -*- coding: utf-8 -*-
"""
多模态搜索服务

Feature: pervis-asset-tagging
Task: 8.1 多模态搜索服务

支持的搜索模式：
- TEXT_ONLY: 仅文本语义搜索
- VISUAL_ONLY: 仅视觉相似搜索
- TAG_ONLY: 仅标签匹配
- MULTIMODAL: 多模态融合（默认）

融合权重：
- 默认 text=0.3, visual=0.4, tag=0.3
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# 多模态搜索模式
# ============================================================

class MultimodalSearchMode(str, Enum):
    """多模态搜索模式"""
    TEXT_ONLY = "TEXT_ONLY"         # 仅文本语义搜索
    VISUAL_ONLY = "VISUAL_ONLY"     # 仅视觉相似搜索
    TAG_ONLY = "TAG_ONLY"           # 仅标签匹配
    MULTIMODAL = "MULTIMODAL"       # 多模态融合


# ============================================================
# 数据结构
# ============================================================

@dataclass
class MultimodalWeights:
    """多模态权重配置"""
    text: float = 0.3
    visual: float = 0.4
    tag: float = 0.3
    
    def normalize(self):
        """归一化权重"""
        total = self.text + self.visual + self.tag
        if total > 0:
            self.text /= total
            self.visual /= total
            self.tag /= total


@dataclass
class KeyFrameMatch:
    """关键帧匹配结果"""
    keyframe_id: str
    timestamp: float
    timecode: str
    thumbnail_path: str
    similarity: float
    suggested_in_point: float = 0.0
    suggested_out_point: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyframe_id": self.keyframe_id,
            "timestamp": round(self.timestamp, 2),
            "timecode": self.timecode,
            "thumbnail_path": self.thumbnail_path,
            "similarity": round(self.similarity, 4),
            "suggested_in_point": round(self.suggested_in_point, 2),
            "suggested_out_point": round(self.suggested_out_point, 2),
        }


@dataclass
class MultimodalSearchResult:
    """多模态搜索结果"""
    asset_id: str
    asset_path: str
    final_score: float
    text_score: float = 0.0
    visual_score: float = 0.0
    tag_score: float = 0.0
    tags: Dict[str, Any] = field(default_factory=dict)
    thumbnail: str = ""
    description: str = ""
    matched_keyframes: List[KeyFrameMatch] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_path": self.asset_path,
            "final_score": round(self.final_score, 4),
            "text_score": round(self.text_score, 4),
            "visual_score": round(self.visual_score, 4),
            "tag_score": round(self.tag_score, 4),
            "tags": self.tags,
            "thumbnail": self.thumbnail,
            "description": self.description,
            "matched_keyframes": [kf.to_dict() for kf in self.matched_keyframes],
        }


@dataclass
class MultimodalSearchRequest:
    """多模态搜索请求"""
    query: str = ""                              # 查询文本
    tags: Dict[str, Any] = field(default_factory=dict)  # 标签过滤
    mode: MultimodalSearchMode = MultimodalSearchMode.MULTIMODAL
    weights: MultimodalWeights = field(default_factory=MultimodalWeights)
    top_k: int = 5
    min_score: float = 0.0
    include_keyframes: bool = True               # 是否返回关键帧
    max_keyframes_per_asset: int = 3             # 每个素材最多返回的关键帧数


@dataclass
class MultimodalSearchResponse:
    """多模态搜索响应"""
    results: List[MultimodalSearchResult]
    total: int
    search_time_ms: float
    mode: str
    query: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "search_time_ms": round(self.search_time_ms, 2),
            "mode": self.mode,
            "query": self.query,
        }


# ============================================================
# 多模态搜索服务
# ============================================================

class MultimodalSearchService:
    """多模态搜索服务"""
    
    def __init__(self):
        self._initialized = False
        self._text_search_service = None
        self._visual_store = None
        self._clip_service = None
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        # 初始化文本搜索服务
        from .search_service import get_search_service
        self._text_search_service = get_search_service()
        await self._text_search_service.initialize()
        
        # 初始化视觉向量存储
        from .visual_vector_store import get_visual_store
        self._visual_store = get_visual_store()
        
        # 初始化 CLIP 服务
        from .clip_embedding import get_clip_service
        self._clip_service = get_clip_service()
        
        self._initialized = True
        logger.info("MultimodalSearchService 初始化完成")
    
    async def search(
        self,
        request: MultimodalSearchRequest
    ) -> MultimodalSearchResponse:
        """执行多模态搜索"""
        await self.initialize()
        
        start_time = time.time()
        
        # 归一化权重
        request.weights.normalize()
        
        # 根据模式执行搜索
        if request.mode == MultimodalSearchMode.TEXT_ONLY:
            results = await self._search_text_only(request)
        elif request.mode == MultimodalSearchMode.VISUAL_ONLY:
            results = await self._search_visual_only(request)
        elif request.mode == MultimodalSearchMode.TAG_ONLY:
            results = await self._search_tag_only(request)
        else:  # MULTIMODAL
            results = await self._search_multimodal(request)
        
        # 过滤低分结果
        if request.min_score > 0:
            results = [r for r in results if r.final_score >= request.min_score]
        
        # 限制返回数量
        results = results[:request.top_k]
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return MultimodalSearchResponse(
            results=results,
            total=len(results),
            search_time_ms=elapsed_ms,
            mode=request.mode.value,
            query=request.query,
        )

    
    async def _search_text_only(
        self,
        request: MultimodalSearchRequest
    ) -> List[MultimodalSearchResult]:
        """仅文本语义搜索"""
        from .search_service import SearchRequest, SearchMode
        
        text_request = SearchRequest(
            query=request.query,
            tags=request.tags,
            mode=SearchMode.VECTOR_ONLY,
            top_k=request.top_k * 2,
        )
        
        response = await self._text_search_service.search(text_request)
        
        results = []
        for item in response.results:
            result = MultimodalSearchResult(
                asset_id=item.segment_id,
                asset_path=item.video_path,
                final_score=item.score,
                text_score=item.vector_score,
                visual_score=0.0,
                tag_score=item.tag_score,
                tags=item.tags,
                thumbnail=item.thumbnail,
                description=item.description,
            )
            
            # 添加关键帧
            if request.include_keyframes:
                result.matched_keyframes = await self._get_keyframes_for_asset(
                    item.segment_id,
                    request.max_keyframes_per_asset
                )
            
            results.append(result)
        
        return results
    
    async def _search_visual_only(
        self,
        request: MultimodalSearchRequest
    ) -> List[MultimodalSearchResult]:
        """仅视觉相似搜索"""
        if not request.query:
            return []
        
        # 使用 CLIP 进行文本到图像搜索
        visual_results = await self._visual_store.search_by_text(
            request.query,
            top_k=request.top_k * 3,
        )
        
        # 按素材聚合结果
        asset_scores: Dict[str, List[Tuple[float, Any]]] = {}
        for vr in visual_results:
            if vr.asset_id not in asset_scores:
                asset_scores[vr.asset_id] = []
            asset_scores[vr.asset_id].append((vr.similarity, vr))
        
        results = []
        for asset_id, scores in asset_scores.items():
            # 取最高分作为素材分数
            max_score = max(s[0] for s in scores)
            
            # 获取素材信息
            segment = await self._get_segment_info(asset_id)
            
            result = MultimodalSearchResult(
                asset_id=asset_id,
                asset_path=segment.get("video_path", "") if segment else "",
                final_score=max_score,
                text_score=0.0,
                visual_score=max_score,
                tag_score=0.0,
                tags=segment.get("tags", {}) if segment else {},
                thumbnail=segment.get("thumbnail", "") if segment else "",
                description=segment.get("description", "") if segment else "",
            )
            
            # 添加匹配的关键帧
            if request.include_keyframes:
                keyframes = []
                for score, vr in sorted(scores, key=lambda x: x[0], reverse=True):
                    if len(keyframes) >= request.max_keyframes_per_asset:
                        break
                    keyframes.append(KeyFrameMatch(
                        keyframe_id=vr.keyframe_id,
                        timestamp=vr.timestamp,
                        timecode=vr.timecode,
                        thumbnail_path=vr.thumbnail_path,
                        similarity=score,
                        suggested_in_point=max(0, vr.timestamp - 2.0),
                        suggested_out_point=vr.timestamp + 3.0,
                    ))
                result.matched_keyframes = keyframes
            
            results.append(result)
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results
    
    async def _search_tag_only(
        self,
        request: MultimodalSearchRequest
    ) -> List[MultimodalSearchResult]:
        """仅标签匹配"""
        from .search_service import SearchRequest, SearchMode
        
        tag_request = SearchRequest(
            query="",
            tags=request.tags,
            mode=SearchMode.TAG_ONLY,
            top_k=request.top_k * 2,
        )
        
        response = await self._text_search_service.search(tag_request)
        
        results = []
        for item in response.results:
            result = MultimodalSearchResult(
                asset_id=item.segment_id,
                asset_path=item.video_path,
                final_score=item.score,
                text_score=0.0,
                visual_score=0.0,
                tag_score=item.tag_score,
                tags=item.tags,
                thumbnail=item.thumbnail,
                description=item.description,
            )
            
            if request.include_keyframes:
                result.matched_keyframes = await self._get_keyframes_for_asset(
                    item.segment_id,
                    request.max_keyframes_per_asset
                )
            
            results.append(result)
        
        return results
    
    async def _search_multimodal(
        self,
        request: MultimodalSearchRequest
    ) -> List[MultimodalSearchResult]:
        """多模态融合搜索"""
        # 并行执行三种搜索
        tasks = []
        
        # 文本搜索
        if request.query and request.weights.text > 0:
            tasks.append(("text", self._search_text_only(request)))
        
        # 视觉搜索
        if request.query and request.weights.visual > 0:
            tasks.append(("visual", self._search_visual_only(request)))
        
        # 标签搜索
        if request.tags and request.weights.tag > 0:
            tasks.append(("tag", self._search_tag_only(request)))
        
        if not tasks:
            return []
        
        # 执行搜索
        task_results = await asyncio.gather(
            *[t[1] for t in tasks],
            return_exceptions=True
        )
        
        # 收集结果
        search_results: Dict[str, Dict[str, Any]] = {}
        
        for i, (search_type, _) in enumerate(tasks):
            results = task_results[i]
            if isinstance(results, Exception):
                logger.error(f"{search_type} 搜索异常: {results}")
                continue
            
            for result in results:
                if result.asset_id not in search_results:
                    search_results[result.asset_id] = {
                        "asset_path": result.asset_path,
                        "tags": result.tags,
                        "thumbnail": result.thumbnail,
                        "description": result.description,
                        "text_score": 0.0,
                        "visual_score": 0.0,
                        "tag_score": 0.0,
                        "keyframes": [],
                    }
                
                data = search_results[result.asset_id]
                
                if search_type == "text":
                    data["text_score"] = max(data["text_score"], result.text_score)
                elif search_type == "visual":
                    data["visual_score"] = max(data["visual_score"], result.visual_score)
                    # 合并关键帧
                    existing_kf_ids = {kf.keyframe_id for kf in data["keyframes"]}
                    for kf in result.matched_keyframes:
                        if kf.keyframe_id not in existing_kf_ids:
                            data["keyframes"].append(kf)
                elif search_type == "tag":
                    data["tag_score"] = max(data["tag_score"], result.tag_score)
        
        # 计算最终分数并构建结果
        final_results = []
        for asset_id, data in search_results.items():
            final_score = (
                request.weights.text * data["text_score"] +
                request.weights.visual * data["visual_score"] +
                request.weights.tag * data["tag_score"]
            )
            
            # 排序关键帧
            keyframes = sorted(
                data["keyframes"],
                key=lambda x: x.similarity,
                reverse=True
            )[:request.max_keyframes_per_asset]
            
            final_results.append(MultimodalSearchResult(
                asset_id=asset_id,
                asset_path=data["asset_path"],
                final_score=final_score,
                text_score=data["text_score"],
                visual_score=data["visual_score"],
                tag_score=data["tag_score"],
                tags=data["tags"],
                thumbnail=data["thumbnail"],
                description=data["description"],
                matched_keyframes=keyframes if request.include_keyframes else [],
            ))
        
        final_results.sort(key=lambda x: x.final_score, reverse=True)
        return final_results
    
    async def _get_segment_info(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """获取素材信息"""
        try:
            from .milvus_store import get_video_store
            store = get_video_store()
            segment = await store.get(segment_id)
            if segment:
                return {
                    "video_path": segment.video_path,
                    "tags": segment.tags,
                    "thumbnail": segment.thumbnail_path or "",
                    "description": segment.description or "",
                }
        except Exception as e:
            logger.error(f"获取素材信息失败: {e}")
        return None
    
    async def _get_keyframes_for_asset(
        self,
        asset_id: str,
        max_count: int = 3
    ) -> List[KeyFrameMatch]:
        """获取素材的关键帧"""
        keyframes = []
        
        try:
            kf_vectors = self._visual_store.get_by_asset(asset_id)
            
            for kf in kf_vectors[:max_count]:
                keyframes.append(KeyFrameMatch(
                    keyframe_id=kf.keyframe_id,
                    timestamp=kf.timestamp,
                    timecode=kf.timecode,
                    thumbnail_path=kf.thumbnail_path,
                    similarity=1.0,  # 默认相似度
                    suggested_in_point=max(0, kf.timestamp - 2.0),
                    suggested_out_point=kf.timestamp + 3.0,
                ))
        except Exception as e:
            logger.debug(f"获取关键帧失败: {e}")
        
        return keyframes
    
    async def search_by_image(
        self,
        image_path: str,
        top_k: int = 10,
    ) -> List[MultimodalSearchResult]:
        """以图搜图"""
        await self.initialize()
        
        visual_results = await self._visual_store.search_by_image(
            image_path,
            top_k=top_k * 3,
        )
        
        # 按素材聚合
        asset_scores: Dict[str, List[Tuple[float, Any]]] = {}
        for vr in visual_results:
            if vr.asset_id not in asset_scores:
                asset_scores[vr.asset_id] = []
            asset_scores[vr.asset_id].append((vr.similarity, vr))
        
        results = []
        for asset_id, scores in asset_scores.items():
            max_score = max(s[0] for s in scores)
            segment = await self._get_segment_info(asset_id)
            
            keyframes = []
            for score, vr in sorted(scores, key=lambda x: x[0], reverse=True)[:3]:
                keyframes.append(KeyFrameMatch(
                    keyframe_id=vr.keyframe_id,
                    timestamp=vr.timestamp,
                    timecode=vr.timecode,
                    thumbnail_path=vr.thumbnail_path,
                    similarity=score,
                    suggested_in_point=max(0, vr.timestamp - 2.0),
                    suggested_out_point=vr.timestamp + 3.0,
                ))
            
            results.append(MultimodalSearchResult(
                asset_id=asset_id,
                asset_path=segment.get("video_path", "") if segment else "",
                final_score=max_score,
                text_score=0.0,
                visual_score=max_score,
                tag_score=0.0,
                tags=segment.get("tags", {}) if segment else {},
                thumbnail=segment.get("thumbnail", "") if segment else "",
                description=segment.get("description", "") if segment else "",
                matched_keyframes=keyframes,
            ))
        
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]


# ============================================================
# 全局实例
# ============================================================

_multimodal_service: Optional[MultimodalSearchService] = None


def get_multimodal_search_service() -> MultimodalSearchService:
    """获取多模态搜索服务实例"""
    global _multimodal_service
    
    if _multimodal_service is None:
        _multimodal_service = MultimodalSearchService()
    
    return _multimodal_service


async def multimodal_search(
    query: str = "",
    tags: Dict[str, Any] = None,
    mode: str = "MULTIMODAL",
    top_k: int = 5,
    weights: Dict[str, float] = None,
    include_keyframes: bool = True,
) -> MultimodalSearchResponse:
    """便捷多模态搜索函数"""
    service = get_multimodal_search_service()
    
    weight_config = MultimodalWeights()
    if weights:
        weight_config.text = weights.get("text", 0.3)
        weight_config.visual = weights.get("visual", 0.4)
        weight_config.tag = weights.get("tag", 0.3)
    
    request = MultimodalSearchRequest(
        query=query,
        tags=tags or {},
        mode=MultimodalSearchMode(mode),
        weights=weight_config,
        top_k=top_k,
        include_keyframes=include_keyframes,
    )
    
    return await service.search(request)
