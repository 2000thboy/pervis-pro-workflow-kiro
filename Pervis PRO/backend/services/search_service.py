# -*- coding: utf-8 -*-
"""
混合搜索服务

Feature: pervis-asset-tagging
Task: 3.1 实现搜索策略

支持的搜索模式：
- TAG_ONLY: 仅标签匹配
- VECTOR_ONLY: 仅向量搜索
- HYBRID: 混合搜索（默认）
- FILTER_THEN_RANK: 先过滤后排序

混合搜索权重：
- 默认 tag_weight=0.4, vector_weight=0.6
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .ollama_embedding import (
    OllamaEmbeddingService,
    cosine_similarity,
    get_embedding_service,
)
from .milvus_store import (
    BaseVideoStore,
    MemoryVideoStore,
    SearchResult,
    VideoSegment,
    get_video_store,
)

logger = logging.getLogger(__name__)


# ============================================================
# 搜索模式
# ============================================================

class SearchMode(str, Enum):
    """搜索模式"""
    TAG_ONLY = "TAG_ONLY"           # 仅标签匹配
    VECTOR_ONLY = "VECTOR_ONLY"     # 仅向量搜索
    HYBRID = "HYBRID"               # 混合搜索
    FILTER_THEN_RANK = "FILTER_THEN_RANK"  # 先过滤后排序


# ============================================================
# 搜索请求和响应
# ============================================================

@dataclass
class SearchRequest:
    """搜索请求"""
    query: str = ""                          # 查询文本
    tags: Dict[str, Any] = field(default_factory=dict)  # 标签过滤
    mode: SearchMode = SearchMode.HYBRID     # 搜索模式
    tag_weight: float = 0.4                  # 标签权重
    vector_weight: float = 0.6               # 向量权重
    top_k: int = 5                           # 返回数量
    min_score: float = 0.0                   # 最低分数阈值
    
    # 召回配置
    tag_recall_k: int = 50                   # 标签召回数量
    vector_recall_k: int = 50                # 向量召回数量
    merge_k: int = 20                        # 融合后数量


@dataclass
class SearchResultItem:
    """搜索结果项"""
    segment_id: str
    video_path: str
    score: float
    tag_score: float = 0.0
    vector_score: float = 0.0
    tags: Dict[str, Any] = field(default_factory=dict)
    thumbnail: str = ""
    description: str = ""
    match_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "video_path": self.video_path,
            "score": round(self.score, 4),
            "tag_score": round(self.tag_score, 4),
            "vector_score": round(self.vector_score, 4),
            "tags": self.tags,
            "thumbnail": self.thumbnail,
            "description": self.description,
            "match_reason": self.match_reason,
        }


@dataclass
class SearchResponse:
    """搜索响应"""
    results: List[SearchResultItem]
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
# 标签匹配器
# ============================================================

class TagMatcher:
    """标签匹配器"""
    
    # 标签权重
    TAG_WEIGHTS = {
        # L1 一级标签
        "scene_type": 1.0,
        "time_of_day": 1.0,
        "shot_size": 1.0,
        # L2 二级标签
        "camera_move": 0.8,
        "action_type": 0.8,
        "mood": 0.8,
        # L3 三级标签
        "characters": 0.6,
        "props": 0.6,
        "vfx": 0.6,
        "environment": 0.6,
        # L4 四级标签
        "free_tags": 0.4,
        "source_work": 0.4,
        "summary": 0.4,  # 描述摘要
    }
    
    @classmethod
    def match_score(
        cls,
        segment_tags: Dict[str, Any],
        query_tags: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算标签匹配分数"""
        if not query_tags:
            return 0.0, "无查询标签"
        
        score = 0.0
        total_weight = 0.0
        matched_fields = []
        
        for field, query_value in query_tags.items():
            if field not in cls.TAG_WEIGHTS:
                continue
            
            weight = cls.TAG_WEIGHTS[field]
            total_weight += weight
            
            segment_value = segment_tags.get(field)
            
            if segment_value is None:
                continue
            
            # 列表类型（L3 标签）
            if isinstance(query_value, list) and isinstance(segment_value, list):
                if query_value and segment_value:
                    intersection = set(query_value) & set(segment_value)
                    if intersection:
                        match_ratio = len(intersection) / len(query_value)
                        score += weight * match_ratio
                        matched_fields.append(f"{field}({len(intersection)})")
            
            # 单值类型（L1, L2 标签）
            elif query_value == segment_value and query_value not in ["UNKNOWN", "未知", ""]:
                score += weight
                matched_fields.append(field)
        
        final_score = score / total_weight if total_weight > 0 else 0.0
        match_reason = f"标签匹配: {', '.join(matched_fields)}" if matched_fields else "无匹配"
        
        return final_score, match_reason


# ============================================================
# 混合搜索服务
# ============================================================

class HybridSearchService:
    """混合搜索服务"""
    
    def __init__(
        self,
        video_store: BaseVideoStore = None,
        embedding_service: OllamaEmbeddingService = None
    ):
        self.video_store = video_store
        self.embedding_service = embedding_service
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        # 初始化视频存储
        if self.video_store is None:
            self.video_store = get_video_store()
        
        if not hasattr(self.video_store, '_initialized') or not self.video_store._initialized:
            await self.video_store.initialize()
        
        # 初始化嵌入服务
        if self.embedding_service is None:
            self.embedding_service = get_embedding_service()
        
        self._initialized = True
        logger.info("HybridSearchService 初始化完成")
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """执行搜索"""
        await self.initialize()
        
        start_time = time.time()
        
        # 根据模式执行搜索
        if request.mode == SearchMode.TAG_ONLY:
            results = await self._search_by_tags(request)
        elif request.mode == SearchMode.VECTOR_ONLY:
            results = await self._search_by_vector(request)
        elif request.mode == SearchMode.FILTER_THEN_RANK:
            results = await self._filter_then_rank(request)
        else:  # HYBRID
            results = await self._hybrid_search(request)
        
        # 过滤低分结果
        if request.min_score > 0:
            results = [r for r in results if r.score >= request.min_score]
        
        # 限制返回数量
        results = results[:request.top_k]
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total=len(results),
            search_time_ms=elapsed_ms,
            mode=request.mode.value,
            query=request.query,
        )
    
    async def _search_by_tags(self, request: SearchRequest) -> List[SearchResultItem]:
        """仅标签搜索"""
        if not request.tags:
            return []
        
        # 使用存储的标签搜索
        store_results = await self.video_store.search_by_tags(
            request.tags,
            top_k=request.tag_recall_k
        )
        
        results = []
        for sr in store_results:
            tag_score, match_reason = TagMatcher.match_score(
                sr.segment.tags,
                request.tags
            )
            results.append(SearchResultItem(
                segment_id=sr.segment.segment_id,
                video_path=sr.segment.video_path,
                score=tag_score,
                tag_score=tag_score,
                vector_score=0.0,
                tags=sr.segment.tags,
                thumbnail=sr.segment.thumbnail_path or "",
                description=sr.segment.description or "",
                match_reason=match_reason,
            ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _search_by_vector(self, request: SearchRequest) -> List[SearchResultItem]:
        """仅向量搜索"""
        if not request.query:
            return []
        
        # 生成查询嵌入
        query_embedding = await self.embedding_service.embed(request.query)
        if not query_embedding:
            logger.warning("无法生成查询嵌入")
            return []
        
        # 向量搜索
        store_results = await self.video_store.search(
            query_embedding,
            top_k=request.vector_recall_k
        )
        
        results = []
        for sr in store_results:
            results.append(SearchResultItem(
                segment_id=sr.segment.segment_id,
                video_path=sr.segment.video_path,
                score=sr.score,
                tag_score=0.0,
                vector_score=sr.score,
                tags=sr.segment.tags,
                thumbnail=sr.segment.thumbnail_path or "",
                description=sr.segment.description or "",
                match_reason=f"向量相似度: {sr.score:.4f}",
            ))
        
        return results
    
    async def _hybrid_search(self, request: SearchRequest) -> List[SearchResultItem]:
        """混合搜索"""
        # 并行执行标签搜索和向量搜索
        async def empty_list():
            return []
        
        tag_task = self._search_by_tags(request) if request.tags else empty_list()
        vector_task = self._search_by_vector(request) if request.query else empty_list()
        
        tag_results, vector_results = await asyncio.gather(
            tag_task,
            vector_task,
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(tag_results, Exception):
            logger.error(f"标签搜索异常: {tag_results}")
            tag_results = []
        if isinstance(vector_results, Exception):
            logger.error(f"向量搜索异常: {vector_results}")
            vector_results = []
        
        # 结果融合
        merged: Dict[str, SearchResultItem] = {}
        
        # 添加标签结果
        for item in tag_results:
            merged[item.segment_id] = item
        
        # 合并向量结果
        for item in vector_results:
            if item.segment_id in merged:
                # 已存在，更新向量分数
                existing = merged[item.segment_id]
                existing.vector_score = item.vector_score
            else:
                # 新增
                merged[item.segment_id] = item
        
        # 计算最终分数
        results = []
        for item in merged.values():
            item.score = (
                request.tag_weight * item.tag_score +
                request.vector_weight * item.vector_score
            )
            
            # 更新匹配原因
            reasons = []
            if item.tag_score > 0:
                reasons.append(f"标签:{item.tag_score:.2f}")
            if item.vector_score > 0:
                reasons.append(f"向量:{item.vector_score:.2f}")
            item.match_reason = f"混合搜索 ({', '.join(reasons)})"
            
            results.append(item)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.merge_k]
    
    async def _filter_then_rank(self, request: SearchRequest) -> List[SearchResultItem]:
        """先过滤后排序"""
        # 先用标签过滤
        if request.tags:
            tag_results = await self._search_by_tags(request)
            candidate_ids = {r.segment_id for r in tag_results}
        else:
            candidate_ids = None
        
        # 再用向量排序
        if request.query:
            query_embedding = await self.embedding_service.embed(request.query)
            if not query_embedding:
                return tag_results if request.tags else []
            
            # 获取候选集的向量
            results = []
            
            if isinstance(self.video_store, MemoryVideoStore):
                for segment_id, segment in self.video_store._segments.items():
                    # 过滤
                    if candidate_ids is not None and segment_id not in candidate_ids:
                        continue
                    
                    if segment.embedding:
                        vector_score = cosine_similarity(query_embedding, segment.embedding)
                        
                        # 计算标签分数
                        tag_score = 0.0
                        if request.tags:
                            tag_score, _ = TagMatcher.match_score(segment.tags, request.tags)
                        
                        # 混合分数
                        final_score = (
                            request.tag_weight * tag_score +
                            request.vector_weight * vector_score
                        )
                        
                        results.append(SearchResultItem(
                            segment_id=segment.segment_id,
                            video_path=segment.video_path,
                            score=final_score,
                            tag_score=tag_score,
                            vector_score=vector_score,
                            tags=segment.tags,
                            thumbnail=segment.thumbnail_path or "",
                            description=segment.description or "",
                            match_reason=f"过滤排序 (标签:{tag_score:.2f}, 向量:{vector_score:.2f})",
                        ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:request.merge_k]
        
        return tag_results if request.tags else []


# ============================================================
# 全局实例
# ============================================================

_search_service: Optional[HybridSearchService] = None


def get_search_service() -> HybridSearchService:
    """获取搜索服务实例"""
    global _search_service
    
    if _search_service is None:
        _search_service = HybridSearchService()
    
    return _search_service


async def search(
    query: str = "",
    tags: Dict[str, Any] = None,
    mode: str = "HYBRID",
    top_k: int = 5,
    tag_weight: float = 0.4,
    vector_weight: float = 0.6
) -> SearchResponse:
    """便捷搜索函数"""
    service = get_search_service()
    
    request = SearchRequest(
        query=query,
        tags=tags or {},
        mode=SearchMode(mode),
        top_k=top_k,
        tag_weight=tag_weight,
        vector_weight=vector_weight,
    )
    
    return await service.search(request)
