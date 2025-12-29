# -*- coding: utf-8 -*-
"""
增强版搜索服务

Phase 2 Task 2.2: 素材搜索优化
- TF-IDF 标签匹配算法
- Jaccard 相似度支持
- 批量向量查询优化
- 搜索结果排序与去重
"""

import asyncio
import logging
import math
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .search_service import (
    SearchMode,
    SearchRequest,
    SearchResultItem,
    SearchResponse,
    HybridSearchService,
    get_search_service as get_base_search_service,
)
from .ollama_embedding import (
    OllamaEmbeddingService,
    cosine_similarity,
    get_embedding_service,
)
from .milvus_store import (
    BaseVideoStore,
    MemoryVideoStore,
    get_video_store,
)

logger = logging.getLogger(__name__)


# ============================================================
# TF-IDF 标签匹配器
# ============================================================

class TFIDFTagMatcher:
    """
    TF-IDF 标签匹配器
    
    使用 TF-IDF 算法计算标签相似度，比简单权重匹配更准确
    """
    
    def __init__(self):
        # 文档频率缓存 (tag -> 出现在多少文档中)
        self._document_freq: Dict[str, int] = {}
        # 总文档数
        self._total_docs: int = 0
        # IDF 缓存
        self._idf_cache: Dict[str, float] = {}
        # 是否已初始化
        self._initialized = False
    
    def build_index(self, segments: List[Dict[str, Any]]):
        """
        构建 TF-IDF 索引
        
        Args:
            segments: 所有片段的标签数据
        """
        self._document_freq.clear()
        self._idf_cache.clear()
        self._total_docs = len(segments)
        
        if self._total_docs == 0:
            return
        
        # 统计文档频率
        for segment in segments:
            tags = segment.get("tags", {})
            seen_terms = set()
            
            for field, value in tags.items():
                if isinstance(value, list):
                    for v in value:
                        term = f"{field}:{v}"
                        seen_terms.add(term)
                elif value and value not in ["UNKNOWN", "未知", ""]:
                    term = f"{field}:{value}"
                    seen_terms.add(term)
            
            for term in seen_terms:
                self._document_freq[term] = self._document_freq.get(term, 0) + 1
        
        # 计算 IDF
        for term, df in self._document_freq.items():
            # IDF = log(N / df) + 1 (平滑处理)
            self._idf_cache[term] = math.log(self._total_docs / df) + 1
        
        self._initialized = True
        logger.info(f"TF-IDF 索引构建完成: {self._total_docs} 文档, {len(self._document_freq)} 词项")
    
    def compute_tf(self, tags: Dict[str, Any]) -> Dict[str, float]:
        """计算词频 (TF)"""
        tf: Dict[str, float] = {}
        total_terms = 0
        
        for field, value in tags.items():
            if isinstance(value, list):
                for v in value:
                    term = f"{field}:{v}"
                    tf[term] = tf.get(term, 0) + 1
                    total_terms += 1
            elif value and value not in ["UNKNOWN", "未知", ""]:
                term = f"{field}:{value}"
                tf[term] = tf.get(term, 0) + 1
                total_terms += 1
        
        # 归一化
        if total_terms > 0:
            for term in tf:
                tf[term] /= total_terms
        
        return tf
    
    def compute_tfidf(self, tags: Dict[str, Any]) -> Dict[str, float]:
        """计算 TF-IDF 向量"""
        tf = self.compute_tf(tags)
        tfidf: Dict[str, float] = {}
        
        for term, tf_value in tf.items():
            idf = self._idf_cache.get(term, 1.0)  # 未知词项 IDF=1
            tfidf[term] = tf_value * idf
        
        return tfidf
    
    def cosine_similarity(
        self,
        tfidf1: Dict[str, float],
        tfidf2: Dict[str, float]
    ) -> float:
        """计算两个 TF-IDF 向量的余弦相似度"""
        if not tfidf1 or not tfidf2:
            return 0.0
        
        # 计算点积
        dot_product = sum(
            tfidf1.get(term, 0) * tfidf2.get(term, 0)
            for term in set(tfidf1.keys()) | set(tfidf2.keys())
        )
        
        # 计算模长
        norm1 = math.sqrt(sum(v ** 2 for v in tfidf1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in tfidf2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def match_score(
        self,
        segment_tags: Dict[str, Any],
        query_tags: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        计算 TF-IDF 匹配分数
        
        Returns:
            (score, match_reason)
        """
        if not query_tags:
            return 0.0, "无查询标签"
        
        segment_tfidf = self.compute_tfidf(segment_tags)
        query_tfidf = self.compute_tfidf(query_tags)
        
        score = self.cosine_similarity(segment_tfidf, query_tfidf)
        
        # 找出匹配的词项
        matched_terms = [
            term.split(":")[0]
            for term in query_tfidf.keys()
            if term in segment_tfidf
        ]
        
        match_reason = f"TF-IDF 匹配: {', '.join(set(matched_terms))}" if matched_terms else "无匹配"
        
        return score, match_reason


# ============================================================
# Jaccard 相似度计算
# ============================================================

class JaccardMatcher:
    """Jaccard 相似度匹配器"""
    
    @staticmethod
    def extract_terms(tags: Dict[str, Any]) -> Set[str]:
        """提取标签词项集合"""
        terms = set()
        
        for field, value in tags.items():
            if isinstance(value, list):
                for v in value:
                    if v and v not in ["UNKNOWN", "未知", ""]:
                        terms.add(f"{field}:{v}")
            elif value and value not in ["UNKNOWN", "未知", ""]:
                terms.add(f"{field}:{value}")
        
        return terms
    
    @classmethod
    def similarity(
        cls,
        tags1: Dict[str, Any],
        tags2: Dict[str, Any]
    ) -> float:
        """
        计算 Jaccard 相似度
        
        J(A, B) = |A ∩ B| / |A ∪ B|
        """
        terms1 = cls.extract_terms(tags1)
        terms2 = cls.extract_terms(tags2)
        
        if not terms1 or not terms2:
            return 0.0
        
        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)
        
        return intersection / union if union > 0 else 0.0
    
    @classmethod
    def match_score(
        cls,
        segment_tags: Dict[str, Any],
        query_tags: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算 Jaccard 匹配分数"""
        if not query_tags:
            return 0.0, "无查询标签"
        
        score = cls.similarity(segment_tags, query_tags)
        
        # 找出匹配的词项
        segment_terms = cls.extract_terms(segment_tags)
        query_terms = cls.extract_terms(query_tags)
        matched = segment_terms & query_terms
        
        matched_fields = [term.split(":")[0] for term in matched]
        match_reason = f"Jaccard 匹配: {', '.join(set(matched_fields))}" if matched_fields else "无匹配"
        
        return score, match_reason


# ============================================================
# 增强版搜索服务
# ============================================================

class MatchAlgorithm(str, Enum):
    """标签匹配算法"""
    WEIGHT = "weight"      # 简单权重 (原始)
    JACCARD = "jaccard"    # Jaccard 相似度
    TFIDF = "tfidf"        # TF-IDF


@dataclass
class EnhancedSearchRequest(SearchRequest):
    """增强版搜索请求"""
    match_algorithm: MatchAlgorithm = MatchAlgorithm.TFIDF
    deduplicate: bool = True           # 是否去重
    dedupe_threshold: float = 0.95     # 去重阈值
    batch_size: int = 100              # 批量查询大小


class EnhancedSearchService(HybridSearchService):
    """
    增强版搜索服务
    
    优化点：
    1. TF-IDF / Jaccard 标签匹配
    2. 批量向量查询
    3. 结果去重
    4. 更智能的排序
    """
    
    def __init__(
        self,
        video_store: BaseVideoStore = None,
        embedding_service: OllamaEmbeddingService = None
    ):
        super().__init__(video_store, embedding_service)
        self._tfidf_matcher = TFIDFTagMatcher()
        self._index_built = False
    
    async def initialize(self):
        """初始化服务"""
        await super().initialize()
        
        # 构建 TF-IDF 索引
        if not self._index_built:
            await self._build_tfidf_index()
    
    async def _build_tfidf_index(self):
        """构建 TF-IDF 索引"""
        if isinstance(self.video_store, MemoryVideoStore):
            segments = [
                {"tags": seg.tags}
                for seg in self.video_store._segments.values()
            ]
            self._tfidf_matcher.build_index(segments)
            self._index_built = True
    
    async def search_enhanced(
        self,
        request: EnhancedSearchRequest
    ) -> SearchResponse:
        """增强版搜索"""
        await self.initialize()
        
        start_time = time.time()
        
        # 根据模式执行搜索
        if request.mode == SearchMode.TAG_ONLY:
            results = await self._search_by_tags_enhanced(request)
        elif request.mode == SearchMode.VECTOR_ONLY:
            results = await self._search_by_vector_batch(request)
        elif request.mode == SearchMode.FILTER_THEN_RANK:
            results = await self._filter_then_rank_enhanced(request)
        else:  # HYBRID
            results = await self._hybrid_search_enhanced(request)
        
        # 去重
        if request.deduplicate:
            results = self._deduplicate_results(results, request.dedupe_threshold)
        
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
    
    async def _search_by_tags_enhanced(
        self,
        request: EnhancedSearchRequest
    ) -> List[SearchResultItem]:
        """增强版标签搜索"""
        if not request.tags:
            return []
        
        results = []
        
        if isinstance(self.video_store, MemoryVideoStore):
            for segment_id, segment in self.video_store._segments.items():
                # 根据算法计算分数
                if request.match_algorithm == MatchAlgorithm.TFIDF:
                    tag_score, match_reason = self._tfidf_matcher.match_score(
                        segment.tags, request.tags
                    )
                elif request.match_algorithm == MatchAlgorithm.JACCARD:
                    tag_score, match_reason = JaccardMatcher.match_score(
                        segment.tags, request.tags
                    )
                else:
                    # 使用原始权重匹配
                    from .search_service import TagMatcher
                    tag_score, match_reason = TagMatcher.match_score(
                        segment.tags, request.tags
                    )
                
                if tag_score > 0:
                    results.append(SearchResultItem(
                        segment_id=segment.segment_id,
                        video_path=segment.video_path,
                        score=tag_score,
                        tag_score=tag_score,
                        vector_score=0.0,
                        tags=segment.tags,
                        thumbnail=segment.thumbnail_path or "",
                        description=segment.description or "",
                        match_reason=match_reason,
                    ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.tag_recall_k]
    
    async def _search_by_vector_batch(
        self,
        request: EnhancedSearchRequest
    ) -> List[SearchResultItem]:
        """批量向量搜索"""
        if not request.query:
            return []
        
        # 生成查询嵌入
        query_embedding = await self.embedding_service.embed(request.query)
        if not query_embedding:
            logger.warning("无法生成查询嵌入")
            return []
        
        # 批量搜索
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
    
    async def _hybrid_search_enhanced(
        self,
        request: EnhancedSearchRequest
    ) -> List[SearchResultItem]:
        """增强版混合搜索"""
        # 并行执行
        tag_task = self._search_by_tags_enhanced(request) if request.tags else asyncio.coroutine(lambda: [])()
        vector_task = self._search_by_vector_batch(request) if request.query else asyncio.coroutine(lambda: [])()
        
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
        
        # 结果融合 (RRF - Reciprocal Rank Fusion)
        merged = self._rrf_fusion(
            tag_results,
            vector_results,
            request.tag_weight,
            request.vector_weight
        )
        
        return merged[:request.merge_k]
    
    def _rrf_fusion(
        self,
        tag_results: List[SearchResultItem],
        vector_results: List[SearchResultItem],
        tag_weight: float,
        vector_weight: float,
        k: int = 60
    ) -> List[SearchResultItem]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        
        RRF(d) = Σ 1 / (k + rank(d))
        """
        scores: Dict[str, float] = {}
        items: Dict[str, SearchResultItem] = {}
        
        # 标签结果排名
        for rank, item in enumerate(tag_results):
            rrf_score = tag_weight / (k + rank + 1)
            scores[item.segment_id] = scores.get(item.segment_id, 0) + rrf_score
            if item.segment_id not in items:
                items[item.segment_id] = item
            else:
                items[item.segment_id].tag_score = item.tag_score
        
        # 向量结果排名
        for rank, item in enumerate(vector_results):
            rrf_score = vector_weight / (k + rank + 1)
            scores[item.segment_id] = scores.get(item.segment_id, 0) + rrf_score
            if item.segment_id not in items:
                items[item.segment_id] = item
            else:
                items[item.segment_id].vector_score = item.vector_score
        
        # 更新最终分数
        results = []
        for segment_id, rrf_score in scores.items():
            item = items[segment_id]
            item.score = rrf_score
            item.match_reason = f"RRF 融合 (标签:{item.tag_score:.2f}, 向量:{item.vector_score:.2f})"
            results.append(item)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _filter_then_rank_enhanced(
        self,
        request: EnhancedSearchRequest
    ) -> List[SearchResultItem]:
        """增强版先过滤后排序"""
        # 先用标签过滤
        if request.tags:
            tag_results = await self._search_by_tags_enhanced(request)
            candidate_ids = {r.segment_id for r in tag_results}
        else:
            candidate_ids = None
        
        # 再用向量排序
        if request.query:
            query_embedding = await self.embedding_service.embed(request.query)
            if not query_embedding:
                return tag_results if request.tags else []
            
            results = []
            
            if isinstance(self.video_store, MemoryVideoStore):
                # 批量计算相似度
                batch_segments = []
                for segment_id, segment in self.video_store._segments.items():
                    if candidate_ids is not None and segment_id not in candidate_ids:
                        continue
                    if segment.embedding:
                        batch_segments.append(segment)
                
                # 批量处理
                for i in range(0, len(batch_segments), request.batch_size):
                    batch = batch_segments[i:i + request.batch_size]
                    
                    for segment in batch:
                        vector_score = cosine_similarity(query_embedding, segment.embedding)
                        
                        # 计算标签分数
                        tag_score = 0.0
                        if request.tags:
                            if request.match_algorithm == MatchAlgorithm.TFIDF:
                                tag_score, _ = self._tfidf_matcher.match_score(
                                    segment.tags, request.tags
                                )
                            elif request.match_algorithm == MatchAlgorithm.JACCARD:
                                tag_score, _ = JaccardMatcher.match_score(
                                    segment.tags, request.tags
                                )
                        
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
    
    def _deduplicate_results(
        self,
        results: List[SearchResultItem],
        threshold: float = 0.95
    ) -> List[SearchResultItem]:
        """
        去重结果
        
        基于标签相似度去重，保留分数最高的
        """
        if not results:
            return results
        
        deduplicated = []
        seen_tags: List[Dict[str, Any]] = []
        
        for item in results:
            is_duplicate = False
            
            for seen in seen_tags:
                similarity = JaccardMatcher.similarity(item.tags, seen)
                if similarity >= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(item)
                seen_tags.append(item.tags)
        
        return deduplicated
    
    async def rebuild_index(self):
        """重建索引"""
        self._index_built = False
        await self._build_tfidf_index()


# ============================================================
# 全局实例
# ============================================================

_enhanced_search_service: Optional[EnhancedSearchService] = None


def get_enhanced_search_service() -> EnhancedSearchService:
    """获取增强版搜索服务实例"""
    global _enhanced_search_service
    
    if _enhanced_search_service is None:
        _enhanced_search_service = EnhancedSearchService()
    
    return _enhanced_search_service


async def search_enhanced(
    query: str = "",
    tags: Dict[str, Any] = None,
    mode: str = "HYBRID",
    match_algorithm: str = "tfidf",
    top_k: int = 5,
    tag_weight: float = 0.4,
    vector_weight: float = 0.6,
    deduplicate: bool = True
) -> SearchResponse:
    """便捷增强搜索函数"""
    service = get_enhanced_search_service()
    
    request = EnhancedSearchRequest(
        query=query,
        tags=tags or {},
        mode=SearchMode(mode),
        match_algorithm=MatchAlgorithm(match_algorithm),
        top_k=top_k,
        tag_weight=tag_weight,
        vector_weight=vector_weight,
        deduplicate=deduplicate,
    )
    
    return await service.search_enhanced(request)
