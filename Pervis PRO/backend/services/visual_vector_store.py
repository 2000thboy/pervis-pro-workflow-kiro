# -*- coding: utf-8 -*-
"""
视觉向量存储服务

Feature: pervis-asset-tagging
Task: 7.2 视觉向量存储

功能：
- 存储关键帧的 CLIP 视觉向量
- 支持视觉相似度搜索
- 支持文本到图像的跨模态搜索
- 持久化存储和加载
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class KeyFrameVector:
    """关键帧向量数据"""
    keyframe_id: str
    asset_id: str
    frame_index: int
    timestamp: float
    timecode: str
    thumbnail_path: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualSearchResult:
    """视觉搜索结果"""
    keyframe_id: str
    asset_id: str
    similarity: float
    timestamp: float
    timecode: str
    thumbnail_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# 视觉向量存储
# ============================================================

class VisualVectorStore:
    """视觉向量存储服务"""
    
    def __init__(
        self,
        dimension: int = 768,
        storage_path: Optional[str] = None,
    ):
        self.dimension = dimension
        self.storage_path = storage_path or "data/visual_vectors"
        
        # 内存存储
        self._vectors: Dict[str, KeyFrameVector] = {}
        self._asset_index: Dict[str, List[str]] = {}  # asset_id -> [keyframe_ids]
        
        # 确保存储目录存在
        os.makedirs(self.storage_path, exist_ok=True)
    
    def add(
        self,
        keyframe_id: str,
        asset_id: str,
        vector: List[float],
        frame_index: int = 0,
        timestamp: float = 0.0,
        timecode: str = "00:00:00:00",
        thumbnail_path: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加关键帧向量
        
        Args:
            keyframe_id: 关键帧 ID
            asset_id: 素材 ID
            vector: 视觉向量
            frame_index: 帧序号
            timestamp: 时间戳
            timecode: 时间码
            thumbnail_path: 缩略图路径
            metadata: 额外元数据
            
        Returns:
            是否添加成功
        """
        if len(vector) != self.dimension:
            logger.warning(
                f"向量维度不匹配: 期望 {self.dimension}, 实际 {len(vector)}"
            )
            # 尝试调整维度
            if len(vector) > self.dimension:
                vector = vector[:self.dimension]
            else:
                vector = vector + [0.0] * (self.dimension - len(vector))
        
        kf_vector = KeyFrameVector(
            keyframe_id=keyframe_id,
            asset_id=asset_id,
            frame_index=frame_index,
            timestamp=timestamp,
            timecode=timecode,
            thumbnail_path=thumbnail_path,
            vector=vector,
            metadata=metadata or {},
        )
        
        self._vectors[keyframe_id] = kf_vector
        
        # 更新素材索引
        if asset_id not in self._asset_index:
            self._asset_index[asset_id] = []
        if keyframe_id not in self._asset_index[asset_id]:
            self._asset_index[asset_id].append(keyframe_id)
        
        return True
    
    def get(self, keyframe_id: str) -> Optional[KeyFrameVector]:
        """获取关键帧向量"""
        return self._vectors.get(keyframe_id)
    
    def get_by_asset(self, asset_id: str) -> List[KeyFrameVector]:
        """获取素材的所有关键帧向量"""
        keyframe_ids = self._asset_index.get(asset_id, [])
        return [self._vectors[kf_id] for kf_id in keyframe_ids if kf_id in self._vectors]
    
    def remove(self, keyframe_id: str) -> bool:
        """删除关键帧向量"""
        if keyframe_id not in self._vectors:
            return False
        
        kf_vector = self._vectors.pop(keyframe_id)
        
        # 更新素材索引
        if kf_vector.asset_id in self._asset_index:
            self._asset_index[kf_vector.asset_id] = [
                kf_id for kf_id in self._asset_index[kf_vector.asset_id]
                if kf_id != keyframe_id
            ]
        
        return True
    
    def remove_by_asset(self, asset_id: str) -> int:
        """删除素材的所有关键帧向量"""
        keyframe_ids = self._asset_index.pop(asset_id, [])
        count = 0
        for kf_id in keyframe_ids:
            if kf_id in self._vectors:
                del self._vectors[kf_id]
                count += 1
        return count
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        asset_filter: Optional[List[str]] = None,
        min_similarity: float = 0.0,
    ) -> List[VisualSearchResult]:
        """
        搜索相似关键帧
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            asset_filter: 素材 ID 过滤列表
            min_similarity: 最小相似度阈值
            
        Returns:
            搜索结果列表
        """
        if not self._vectors:
            return []
        
        results = []
        
        for kf_id, kf_vector in self._vectors.items():
            # 素材过滤
            if asset_filter and kf_vector.asset_id not in asset_filter:
                continue
            
            # 计算相似度
            similarity = self._cosine_similarity(query_vector, kf_vector.vector)
            
            if similarity >= min_similarity:
                results.append(VisualSearchResult(
                    keyframe_id=kf_id,
                    asset_id=kf_vector.asset_id,
                    similarity=similarity,
                    timestamp=kf_vector.timestamp,
                    timecode=kf_vector.timecode,
                    thumbnail_path=kf_vector.thumbnail_path,
                    metadata=kf_vector.metadata,
                ))
        
        # 按相似度排序
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results[:top_k]
    
    async def search_by_text(
        self,
        text: str,
        top_k: int = 10,
        asset_filter: Optional[List[str]] = None,
    ) -> List[VisualSearchResult]:
        """
        文本搜索图像（跨模态）
        
        Args:
            text: 查询文本
            top_k: 返回数量
            asset_filter: 素材 ID 过滤列表
            
        Returns:
            搜索结果列表
        """
        from .clip_embedding import get_clip_service
        
        clip_service = get_clip_service()
        text_vector = await clip_service.embed_text(text)
        
        if not text_vector:
            logger.error(f"文本嵌入失败: {text}")
            return []
        
        return self.search(text_vector, top_k=top_k, asset_filter=asset_filter)
    
    async def search_by_image(
        self,
        image_path: str,
        top_k: int = 10,
        asset_filter: Optional[List[str]] = None,
    ) -> List[VisualSearchResult]:
        """
        以图搜图
        
        Args:
            image_path: 查询图像路径
            top_k: 返回数量
            asset_filter: 素材 ID 过滤列表
            
        Returns:
            搜索结果列表
        """
        from .clip_embedding import get_clip_service
        
        clip_service = get_clip_service()
        image_vector = await clip_service.embed_image(image_path)
        
        if not image_vector:
            logger.error(f"图像嵌入失败: {image_path}")
            return []
        
        return self.search(image_vector, top_k=top_k, asset_filter=asset_filter)

    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        
        # 确保维度一致
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def save(self, filename: Optional[str] = None) -> bool:
        """
        保存到文件
        
        Args:
            filename: 文件名（不含路径）
            
        Returns:
            是否保存成功
        """
        filename = filename or "visual_vectors.json"
        filepath = os.path.join(self.storage_path, filename)
        
        try:
            data = {
                "dimension": self.dimension,
                "vectors": {
                    kf_id: asdict(kf_vector)
                    for kf_id, kf_vector in self._vectors.items()
                },
                "asset_index": self._asset_index,
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"视觉向量存储已保存: {filepath}, 共 {len(self._vectors)} 条")
            return True
            
        except Exception as e:
            logger.error(f"保存视觉向量存储失败: {e}")
            return False
    
    def load(self, filename: Optional[str] = None) -> bool:
        """
        从文件加载
        
        Args:
            filename: 文件名（不含路径）
            
        Returns:
            是否加载成功
        """
        filename = filename or "visual_vectors.json"
        filepath = os.path.join(self.storage_path, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"视觉向量存储文件不存在: {filepath}")
            return False
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.dimension = data.get("dimension", self.dimension)
            self._asset_index = data.get("asset_index", {})
            
            self._vectors = {}
            for kf_id, kf_data in data.get("vectors", {}).items():
                self._vectors[kf_id] = KeyFrameVector(**kf_data)
            
            logger.info(f"视觉向量存储已加载: {filepath}, 共 {len(self._vectors)} 条")
            return True
            
        except Exception as e:
            logger.error(f"加载视觉向量存储失败: {e}")
            return False
    
    @property
    def count(self) -> int:
        """获取向量数量"""
        return len(self._vectors)
    
    @property
    def asset_count(self) -> int:
        """获取素材数量"""
        return len(self._asset_index)
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_vectors": len(self._vectors),
            "total_assets": len(self._asset_index),
            "dimension": self.dimension,
            "storage_path": self.storage_path,
        }


# ============================================================
# 全局实例
# ============================================================

_visual_store: Optional[VisualVectorStore] = None


def get_visual_store(storage_path: Optional[str] = None) -> VisualVectorStore:
    """获取视觉向量存储实例"""
    global _visual_store
    
    if _visual_store is None:
        _visual_store = VisualVectorStore(storage_path=storage_path)
        # 尝试加载已有数据
        _visual_store.load()
    
    return _visual_store


async def add_keyframe_vector(
    keyframe_id: str,
    asset_id: str,
    image_path: str,
    frame_index: int = 0,
    timestamp: float = 0.0,
    timecode: str = "00:00:00:00",
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    便捷函数：添加关键帧向量（自动生成嵌入）
    
    Args:
        keyframe_id: 关键帧 ID
        asset_id: 素材 ID
        image_path: 图像路径
        frame_index: 帧序号
        timestamp: 时间戳
        timecode: 时间码
        metadata: 额外元数据
        
    Returns:
        是否添加成功
    """
    from .clip_embedding import get_clip_service
    
    clip_service = get_clip_service()
    vector = await clip_service.embed_image(image_path)
    
    if not vector:
        logger.error(f"图像嵌入失败: {image_path}")
        return False
    
    store = get_visual_store()
    return store.add(
        keyframe_id=keyframe_id,
        asset_id=asset_id,
        vector=vector,
        frame_index=frame_index,
        timestamp=timestamp,
        timecode=timecode,
        thumbnail_path=image_path,
        metadata=metadata,
    )
