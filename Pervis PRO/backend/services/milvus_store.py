# -*- coding: utf-8 -*-
"""
Milvus 视频素材存储服务

Feature: pervis-project-wizard Phase 1
Task: 1.1 创建 MilvusVideoStore

提供视频片段的向量存储和搜索功能：
- 创建集合和索引
- 插入视频片段
- 向量搜索
- 标签搜索

Requirements: 17.2, 17.3, 17.4
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

logger = logging.getLogger(__name__)


class VectorStoreType(str, Enum):
    """向量存储类型"""
    MILVUS = "milvus"
    CHROMA = "chroma"
    MEMORY = "memory"


@dataclass
class VideoSegment:
    """视频片段数据"""
    segment_id: str
    video_id: str
    video_path: str
    start_time: float  # 秒
    end_time: float    # 秒
    duration: float    # 秒
    
    # 标签
    tags: Dict[str, Any] = field(default_factory=dict)
    
    # 向量嵌入
    embedding: Optional[List[float]] = None
    
    # 元数据
    thumbnail_path: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "video_id": self.video_id,
            "video_path": self.video_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "thumbnail_path": self.thumbnail_path,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SearchResult:
    """搜索结果"""
    segment: VideoSegment
    score: float
    match_reason: str = ""


class BaseVideoStore(ABC):
    """视频存储基类"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化存储"""
        pass
    
    @abstractmethod
    async def insert(self, segment: VideoSegment) -> bool:
        """插入视频片段"""
        pass
    
    @abstractmethod
    async def insert_batch(self, segments: List[VideoSegment]) -> int:
        """批量插入"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        pass
    
    @abstractmethod
    async def search_by_tags(
        self, 
        tags: Dict[str, Any], 
        top_k: int = 5
    ) -> List[SearchResult]:
        """标签搜索"""
        pass
    
    @abstractmethod
    async def get(self, segment_id: str) -> Optional[VideoSegment]:
        """获取片段"""
        pass
    
    @abstractmethod
    async def delete(self, segment_id: str) -> bool:
        """删除片段"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """获取总数"""
        pass


class MemoryVideoStore(BaseVideoStore):
    """内存视频存储（用于测试和开发）
    
    支持从 JSON 缓存文件加载预索引的素材数据，解决后端重启后数据丢失的问题。
    """
    
    # 默认缓存文件路径
    DEFAULT_CACHE_PATH = None  # 将在初始化时设置
    
    def __init__(self, cache_path: str = None):
        self._segments: Dict[str, VideoSegment] = {}
        self._initialized = False
        self._cache_path = cache_path
    
    async def initialize(self) -> bool:
        """初始化存储，自动加载缓存数据"""
        self._initialized = True
        
        # 尝试加载缓存数据
        loaded_count = await self._load_from_cache()
        
        if loaded_count > 0:
            logger.info(f"MemoryVideoStore 初始化完成，已加载 {loaded_count} 条缓存数据")
        else:
            logger.info("MemoryVideoStore 初始化完成（无缓存数据）")
        
        return True
    
    async def _load_from_cache(self) -> int:
        """从缓存文件加载数据"""
        import json
        import os
        from pathlib import Path
        
        # 确定缓存文件路径
        cache_paths = []
        
        if self._cache_path:
            cache_paths.append(self._cache_path)
        
        # 默认缓存路径（相对于 backend 目录）
        backend_dir = Path(__file__).parent.parent
        project_dir = backend_dir.parent
        
        default_paths = [
            project_dir / "data" / "segments_cache.json",  # 新的完整数据缓存
            project_dir / "data" / "index_cache_v2.json",  # 旧的索引缓存（仅哈希映射）
        ]
        cache_paths.extend(default_paths)
        
        for cache_path in cache_paths:
            if not os.path.exists(cache_path):
                continue
            
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 检查数据格式
                if isinstance(data, dict):
                    # 新格式：包含完整 VideoSegment 数据
                    if "segments" in data:
                        segments_data = data["segments"]
                        for seg_data in segments_data:
                            segment = self._dict_to_segment(seg_data)
                            if segment:
                                self._segments[segment.segment_id] = segment
                        logger.info(f"从 {cache_path} 加载了 {len(self._segments)} 条素材数据")
                        return len(self._segments)
                    
                    # 旧格式：仅哈希到 segment_id 的映射，无法恢复完整数据
                    elif all(isinstance(v, str) for v in data.values()):
                        logger.warning(f"缓存文件 {cache_path} 是旧格式（仅索引映射），无法加载完整数据")
                        logger.warning("请重新运行 batch_asset_indexing_v2.py 生成新格式缓存")
                        continue
                
            except Exception as e:
                logger.error(f"加载缓存文件 {cache_path} 失败: {e}")
                continue
        
        return 0
    
    def _dict_to_segment(self, data: Dict[str, Any]) -> Optional[VideoSegment]:
        """将字典转换为 VideoSegment 对象"""
        try:
            return VideoSegment(
                segment_id=data.get("segment_id", ""),
                video_id=data.get("video_id", ""),
                video_path=data.get("video_path", ""),
                start_time=data.get("start_time", 0),
                end_time=data.get("end_time", 0),
                duration=data.get("duration", 0),
                tags=data.get("tags", {}),
                embedding=data.get("embedding"),
                thumbnail_path=data.get("thumbnail_path"),
                description=data.get("description"),
            )
        except Exception as e:
            logger.error(f"转换 VideoSegment 失败: {e}")
            return None
    
    async def save_to_cache(self, cache_path: str = None) -> bool:
        """保存数据到缓存文件"""
        import json
        from pathlib import Path
        
        if cache_path is None:
            backend_dir = Path(__file__).parent.parent
            project_dir = backend_dir.parent
            cache_path = project_dir / "data" / "segments_cache.json"
        
        try:
            # 确保目录存在
            Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为可序列化的格式
            segments_data = []
            for segment in self._segments.values():
                seg_dict = segment.to_dict()
                seg_dict["embedding"] = segment.embedding  # 保留嵌入向量
                segments_data.append(seg_dict)
            
            data = {
                "version": "2.0",
                "count": len(segments_data),
                "segments": segments_data
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存 {len(segments_data)} 条素材数据到 {cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    async def insert(self, segment: VideoSegment) -> bool:
        self._segments[segment.segment_id] = segment
        return True
    
    async def insert_batch(self, segments: List[VideoSegment]) -> int:
        count = 0
        for segment in segments:
            if await self.insert(segment):
                count += 1
        return count
    
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索（余弦相似度）"""
        results = []
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)
        
        if query_norm == 0:
            return []
        
        for segment in self._segments.values():
            if segment.embedding is None:
                continue
            
            # 应用过滤器
            if filters and not self._match_filters(segment, filters):
                continue
            
            # 计算余弦相似度
            seg_vec = np.array(segment.embedding)
            seg_norm = np.linalg.norm(seg_vec)
            
            if seg_norm == 0:
                continue
            
            similarity = np.dot(query_vec, seg_vec) / (query_norm * seg_norm)
            results.append(SearchResult(
                segment=segment,
                score=float(similarity),
                match_reason="向量相似度匹配"
            ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def search_by_tags(
        self, 
        tags: Dict[str, Any], 
        top_k: int = 5
    ) -> List[SearchResult]:
        """标签搜索"""
        results = []
        
        for segment in self._segments.values():
            match_count = 0
            total_tags = len(tags)
            
            for key, value in tags.items():
                if key in segment.tags:
                    if isinstance(value, list):
                        # 列表匹配（任一匹配即可）
                        if any(v in segment.tags.get(key, []) for v in value):
                            match_count += 1
                    elif segment.tags.get(key) == value:
                        match_count += 1
            
            if match_count > 0:
                score = match_count / total_tags if total_tags > 0 else 0
                results.append(SearchResult(
                    segment=segment,
                    score=score,
                    match_reason=f"标签匹配 {match_count}/{total_tags}"
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def get(self, segment_id: str) -> Optional[VideoSegment]:
        return self._segments.get(segment_id)
    
    async def delete(self, segment_id: str) -> bool:
        if segment_id in self._segments:
            del self._segments[segment_id]
            return True
        return False
    
    async def count(self) -> int:
        return len(self._segments)
    
    def _match_filters(self, segment: VideoSegment, filters: Dict[str, Any]) -> bool:
        """检查片段是否匹配过滤器"""
        for key, value in filters.items():
            if key == "video_id" and segment.video_id != value:
                return False
            if key == "min_duration" and segment.duration < value:
                return False
            if key == "max_duration" and segment.duration > value:
                return False
            if key in segment.tags:
                if isinstance(value, list):
                    if not any(v in segment.tags.get(key, []) for v in value):
                        return False
                elif segment.tags.get(key) != value:
                    return False
        return True


class MilvusVideoStore(BaseVideoStore):
    """Milvus 视频存储"""
    
    COLLECTION_NAME = "video_segments"
    EMBEDDING_DIM = 384  # sentence-transformers 默认维度
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 19530,
        collection_name: str = None
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name or self.COLLECTION_NAME
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化 Milvus 连接和集合"""
        try:
            from pymilvus import MilvusClient, DataType
            
            # 连接 Milvus
            self._client = MilvusClient(uri=f"http://{self.host}:{self.port}")
            
            # 检查集合是否存在
            if not self._client.has_collection(self.collection_name):
                await self._create_collection()
            
            self._initialized = True
            logger.info(f"MilvusVideoStore 初始化完成: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"MilvusVideoStore 初始化失败: {e}")
            return False
    
    async def _create_collection(self):
        """创建集合和索引"""
        from pymilvus import DataType
        
        # 定义 Schema
        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=True
        )
        
        # 添加字段
        schema.add_field("segment_id", DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field("video_id", DataType.VARCHAR, max_length=64)
        schema.add_field("video_path", DataType.VARCHAR, max_length=512)
        schema.add_field("start_time", DataType.FLOAT)
        schema.add_field("end_time", DataType.FLOAT)
        schema.add_field("duration", DataType.FLOAT)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=self.EMBEDDING_DIM)
        
        # 创建索引
        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128}
        )
        
        # 创建集合
        self._client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params
        )
        
        logger.info(f"Milvus 集合创建完成: {self.collection_name}")
    
    async def insert(self, segment: VideoSegment) -> bool:
        """插入视频片段"""
        if not self._initialized:
            return False
        
        try:
            data = {
                "segment_id": segment.segment_id,
                "video_id": segment.video_id,
                "video_path": segment.video_path,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.duration,
                "embedding": segment.embedding or [0.0] * self.EMBEDDING_DIM,
                "tags": segment.tags,
                "thumbnail_path": segment.thumbnail_path or "",
                "description": segment.description or ""
            }
            
            self._client.insert(
                collection_name=self.collection_name,
                data=[data]
            )
            return True
            
        except Exception as e:
            logger.error(f"插入失败: {e}")
            return False
    
    async def insert_batch(self, segments: List[VideoSegment]) -> int:
        """批量插入"""
        if not self._initialized or not segments:
            return 0
        
        try:
            data_list = []
            for segment in segments:
                data_list.append({
                    "segment_id": segment.segment_id,
                    "video_id": segment.video_id,
                    "video_path": segment.video_path,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "duration": segment.duration,
                    "embedding": segment.embedding or [0.0] * self.EMBEDDING_DIM,
                    "tags": segment.tags,
                    "thumbnail_path": segment.thumbnail_path or "",
                    "description": segment.description or ""
                })
            
            result = self._client.insert(
                collection_name=self.collection_name,
                data=data_list
            )
            return len(data_list)
            
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return 0
    
    async def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        if not self._initialized:
            return []
        
        try:
            # 构建过滤表达式
            filter_expr = None
            if filters:
                conditions = []
                if "video_id" in filters:
                    conditions.append(f'video_id == "{filters["video_id"]}"')
                if "min_duration" in filters:
                    conditions.append(f'duration >= {filters["min_duration"]}')
                if "max_duration" in filters:
                    conditions.append(f'duration <= {filters["max_duration"]}')
                if conditions:
                    filter_expr = " and ".join(conditions)
            
            results = self._client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k,
                filter=filter_expr,
                output_fields=["segment_id", "video_id", "video_path", 
                              "start_time", "end_time", "duration",
                              "tags", "thumbnail_path", "description"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    entity = hit.get("entity", {})
                    segment = VideoSegment(
                        segment_id=entity.get("segment_id", ""),
                        video_id=entity.get("video_id", ""),
                        video_path=entity.get("video_path", ""),
                        start_time=entity.get("start_time", 0),
                        end_time=entity.get("end_time", 0),
                        duration=entity.get("duration", 0),
                        tags=entity.get("tags", {}),
                        thumbnail_path=entity.get("thumbnail_path"),
                        description=entity.get("description")
                    )
                    search_results.append(SearchResult(
                        segment=segment,
                        score=hit.get("distance", 0),
                        match_reason="向量相似度匹配"
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def search_by_tags(
        self, 
        tags: Dict[str, Any], 
        top_k: int = 5
    ) -> List[SearchResult]:
        """标签搜索（使用过滤器）"""
        if not self._initialized:
            return []
        
        # 标签搜索需要先获取所有数据再过滤
        # Milvus 的动态字段过滤有限制，这里使用简化实现
        try:
            # 获取所有数据
            results = self._client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["segment_id", "video_id", "video_path",
                              "start_time", "end_time", "duration",
                              "tags", "thumbnail_path", "description"],
                limit=1000
            )
            
            search_results = []
            for entity in results:
                segment_tags = entity.get("tags", {})
                match_count = 0
                total_tags = len(tags)
                
                for key, value in tags.items():
                    if key in segment_tags:
                        if isinstance(value, list):
                            if any(v in segment_tags.get(key, []) for v in value):
                                match_count += 1
                        elif segment_tags.get(key) == value:
                            match_count += 1
                
                if match_count > 0:
                    segment = VideoSegment(
                        segment_id=entity.get("segment_id", ""),
                        video_id=entity.get("video_id", ""),
                        video_path=entity.get("video_path", ""),
                        start_time=entity.get("start_time", 0),
                        end_time=entity.get("end_time", 0),
                        duration=entity.get("duration", 0),
                        tags=segment_tags,
                        thumbnail_path=entity.get("thumbnail_path"),
                        description=entity.get("description")
                    )
                    score = match_count / total_tags if total_tags > 0 else 0
                    search_results.append(SearchResult(
                        segment=segment,
                        score=score,
                        match_reason=f"标签匹配 {match_count}/{total_tags}"
                    ))
            
            search_results.sort(key=lambda x: x.score, reverse=True)
            return search_results[:top_k]
            
        except Exception as e:
            logger.error(f"标签搜索失败: {e}")
            return []
    
    async def get(self, segment_id: str) -> Optional[VideoSegment]:
        """获取片段"""
        if not self._initialized:
            return None
        
        try:
            results = self._client.query(
                collection_name=self.collection_name,
                filter=f'segment_id == "{segment_id}"',
                output_fields=["segment_id", "video_id", "video_path",
                              "start_time", "end_time", "duration",
                              "tags", "thumbnail_path", "description"]
            )
            
            if results:
                entity = results[0]
                return VideoSegment(
                    segment_id=entity.get("segment_id", ""),
                    video_id=entity.get("video_id", ""),
                    video_path=entity.get("video_path", ""),
                    start_time=entity.get("start_time", 0),
                    end_time=entity.get("end_time", 0),
                    duration=entity.get("duration", 0),
                    tags=entity.get("tags", {}),
                    thumbnail_path=entity.get("thumbnail_path"),
                    description=entity.get("description")
                )
            return None
            
        except Exception as e:
            logger.error(f"获取失败: {e}")
            return None
    
    async def delete(self, segment_id: str) -> bool:
        """删除片段"""
        if not self._initialized:
            return False
        
        try:
            self._client.delete(
                collection_name=self.collection_name,
                filter=f'segment_id == "{segment_id}"'
            )
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False
    
    async def count(self) -> int:
        """获取总数"""
        if not self._initialized:
            return 0
        
        try:
            stats = self._client.get_collection_stats(self.collection_name)
            return stats.get("row_count", 0)
        except Exception as e:
            logger.error(f"获取数量失败: {e}")
            return 0


# 全局存储实例
_video_store: Optional[BaseVideoStore] = None


def get_video_store(store_type: VectorStoreType = VectorStoreType.MEMORY, cache_path: str = None) -> BaseVideoStore:
    """获取视频存储实例
    
    Args:
        store_type: 存储类型
        cache_path: 缓存文件路径（仅对 MEMORY 类型有效）
    
    Returns:
        视频存储实例
    """
    global _video_store
    
    if _video_store is None:
        if store_type == VectorStoreType.MILVUS:
            _video_store = MilvusVideoStore()
        else:
            _video_store = MemoryVideoStore(cache_path=cache_path)
    
    return _video_store


async def get_initialized_video_store(store_type: VectorStoreType = VectorStoreType.MEMORY, cache_path: str = None) -> BaseVideoStore:
    """获取已初始化的视频存储实例（推荐使用）
    
    自动初始化存储并加载缓存数据。
    
    Args:
        store_type: 存储类型
        cache_path: 缓存文件路径
    
    Returns:
        已初始化的视频存储实例
    """
    store = get_video_store(store_type, cache_path)
    if not store._initialized:
        await store.initialize()
    return store


def set_video_store(store: BaseVideoStore):
    """设置视频存储实例"""
    global _video_store
    _video_store = store
