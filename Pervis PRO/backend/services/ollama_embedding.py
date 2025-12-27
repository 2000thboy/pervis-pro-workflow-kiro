# -*- coding: utf-8 -*-
"""
Ollama 嵌入服务

Feature: pervis-asset-tagging
Task: 2.1 实现 Ollama 嵌入服务

支持的嵌入模型：
- nomic-embed-text (768 维)
- bge-m3 (1024 维，中文优化)
- mxbai-embed-large (1024 维)

使用 Ollama 本地服务生成嵌入向量，绕过 NumPy 2.x 兼容性问题。
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# 支持的嵌入模型及其维度
EMBEDDING_MODELS = {
    "nomic-embed-text": 768,
    "bge-m3": 1024,
    "mxbai-embed-large": 1024,
    "all-minilm": 384,
}

# 默认模型优先级
DEFAULT_MODEL_PRIORITY = ["nomic-embed-text", "bge-m3", "mxbai-embed-large", "all-minilm"]


# ============================================================
# 嵌入缓存
# ============================================================

@dataclass
class EmbeddingCache:
    """嵌入缓存"""
    cache_path: Path
    max_size: int = 10000
    _cache: Dict[str, List[float]] = None
    _dirty: bool = False
    
    def __post_init__(self):
        self._cache = {}
        self._load()
    
    def _load(self):
        """加载缓存"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"加载嵌入缓存: {len(self._cache)} 条")
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
                self._cache = {}
    
    def save(self):
        """保存缓存"""
        if not self._dirty:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
            self._dirty = False
            logger.info(f"保存嵌入缓存: {len(self._cache)} 条")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def get(self, key: str) -> Optional[List[float]]:
        """获取缓存"""
        return self._cache.get(key)
    
    def set(self, key: str, value: List[float]):
        """设置缓存"""
        if len(self._cache) >= self.max_size:
            # 简单的 LRU：删除前 10%
            keys_to_remove = list(self._cache.keys())[:self.max_size // 10]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[key] = value
        self._dirty = True
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache


# ============================================================
# Ollama 嵌入服务
# ============================================================

class OllamaEmbeddingService:
    """Ollama 嵌入服务"""
    
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = None,
        cache_path: str = None,
        timeout: int = 60
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
        # 缓存
        if cache_path:
            self._cache = EmbeddingCache(Path(cache_path))
        else:
            self._cache = None
        
        # 状态
        self._available = None
        self._model_dim = None
        self._session = None
    
    async def _get_session(self):
        """获取 HTTP 会话"""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def close(self):
        """关闭会话"""
        if self._session:
            await self._session.close()
            self._session = None
        if self._cache:
            self._cache.save()
    
    async def check_available(self) -> Tuple[bool, Optional[str]]:
        """检查服务可用性，返回 (是否可用, 可用模型名)"""
        if self._available is not None:
            return self._available, self.model
        
        try:
            session = await self._get_session()
            
            # 获取已安装的模型列表
            async with session.get(f"{self.base_url}/api/tags") as resp:
                if resp.status != 200:
                    logger.warning(f"Ollama 服务不可用: HTTP {resp.status}")
                    self._available = False
                    return False, None
                
                data = await resp.json()
                installed_models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                logger.info(f"Ollama 已安装模型: {installed_models}")
            
            # 如果指定了模型，检查是否可用
            if self.model:
                model_base = self.model.split(":")[0]
                if model_base in installed_models or self.model in installed_models:
                    self._available = True
                    self._model_dim = EMBEDDING_MODELS.get(model_base, 768)
                    return True, self.model
                else:
                    logger.warning(f"指定的嵌入模型 {self.model} 未安装")
            
            # 按优先级查找可用模型
            for model in DEFAULT_MODEL_PRIORITY:
                if model in installed_models:
                    self.model = model
                    self._available = True
                    self._model_dim = EMBEDDING_MODELS.get(model, 768)
                    logger.info(f"使用嵌入模型: {model} (维度: {self._model_dim})")
                    return True, model
            
            # 没有找到嵌入模型
            logger.warning(f"没有找到可用的嵌入模型，请安装: ollama pull nomic-embed-text")
            self._available = False
            return False, None
            
        except Exception as e:
            logger.error(f"检查 Ollama 服务失败: {e}")
            self._available = False
            return False, None
    
    @property
    def dimension(self) -> int:
        """获取嵌入维度"""
        if self._model_dim:
            return self._model_dim
        if self.model:
            model_base = self.model.split(":")[0]
            return EMBEDDING_MODELS.get(model_base, 768)
        return 768
    
    async def embed(self, text: str) -> Optional[List[float]]:
        """生成单个文本的嵌入向量"""
        # 检查缓存
        if self._cache and text in self._cache:
            return self._cache.get(text)
        
        # 检查服务可用性
        available, _ = await self.check_available()
        if not available:
            return None
        
        try:
            session = await self._get_session()
            
            async with session.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"嵌入请求失败: {resp.status} - {error_text}")
                    return None
                
                data = await resp.json()
                embedding = data.get("embedding")
                
                if embedding:
                    # 缓存结果
                    if self._cache:
                        self._cache.set(text, embedding)
                    return embedding
                
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"嵌入请求超时: {text[:50]}...")
            return None
        except Exception as e:
            logger.error(f"嵌入请求异常: {e}")
            return None
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
        show_progress: bool = False
    ) -> List[Optional[List[float]]]:
        """批量生成嵌入向量"""
        results = []
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.embed(text) for text in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"批量嵌入异常: {result}")
                    results.append(None)
                else:
                    results.append(result)
            
            if show_progress:
                progress = min(i + batch_size, total)
                print(f"   嵌入进度: {progress}/{total} ({progress/total*100:.1f}%)")
        
        return results
    
    def save_cache(self):
        """保存缓存"""
        if self._cache:
            self._cache.save()


# ============================================================
# 余弦相似度计算（纯 Python，避免 NumPy 2.x 问题）
# ============================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def cosine_similarity_batch(
    query_vec: List[float],
    vectors: List[List[float]]
) -> List[float]:
    """批量计算余弦相似度"""
    return [cosine_similarity(query_vec, vec) for vec in vectors]


def top_k_similar(
    query_vec: List[float],
    vectors: List[Tuple[str, List[float]]],  # [(id, vector), ...]
    k: int = 5
) -> List[Tuple[str, float]]:
    """找出 Top K 最相似的向量"""
    similarities = []
    for id_, vec in vectors:
        if vec:
            sim = cosine_similarity(query_vec, vec)
            similarities.append((id_, sim))
    
    # 按相似度降序排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:k]


# ============================================================
# 全局实例
# ============================================================

_embedding_service: Optional[OllamaEmbeddingService] = None


def get_embedding_service(
    model: str = None,
    cache_path: str = None
) -> OllamaEmbeddingService:
    """获取嵌入服务实例"""
    global _embedding_service
    
    if _embedding_service is None:
        # 默认缓存路径
        if cache_path is None:
            cache_path = str(Path(__file__).parent.parent.parent / "data" / "embedding_cache.json")
        
        _embedding_service = OllamaEmbeddingService(
            model=model or os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            cache_path=cache_path
        )
    
    return _embedding_service


async def embed_text(text: str) -> Optional[List[float]]:
    """便捷函数：生成文本嵌入"""
    service = get_embedding_service()
    return await service.embed(text)


async def embed_texts(texts: List[str]) -> List[Optional[List[float]]]:
    """便捷函数：批量生成文本嵌入"""
    service = get_embedding_service()
    return await service.embed_batch(texts)
