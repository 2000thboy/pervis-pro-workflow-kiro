# -*- coding: utf-8 -*-
"""
CLIP 视觉嵌入服务

Feature: pervis-asset-tagging
Task: 7.1 CLIP 嵌入服务

支持的模型：
- Ollama llava 模型（推荐）
- HuggingFace CLIP 模型

功能：
- 图像嵌入：将关键帧图像转换为向量
- 文本嵌入：将查询文本转换为向量（与图像同空间）
- 跨模态搜索：用文本搜索图像，用图像搜索图像
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

@dataclass
class CLIPConfig:
    """CLIP 配置"""
    model_name: str = "llava:7b"
    ollama_base_url: str = "http://localhost:11434"
    dimension: int = 768
    batch_size: int = 4
    timeout: float = 60.0
    use_huggingface: bool = False  # 是否使用 HuggingFace 模型


# ============================================================
# CLIP 嵌入服务
# ============================================================

class CLIPEmbeddingService:
    """CLIP 视觉嵌入服务"""
    
    def __init__(self, config: Optional[CLIPConfig] = None):
        self.config = config or CLIPConfig()
        self._initialized = False
        self._hf_model = None
        self._hf_processor = None
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        if self.config.use_huggingface:
            await self._init_huggingface()
        else:
            # 检查 Ollama 服务
            available = await self._check_ollama_available()
            if not available:
                logger.warning("Ollama 服务不可用，尝试使用 HuggingFace")
                self.config.use_huggingface = True
                await self._init_huggingface()
        
        self._initialized = True
        logger.info(f"CLIPEmbeddingService 初始化完成，使用模型: {self.config.model_name}")
    
    async def _init_huggingface(self):
        """初始化 HuggingFace CLIP 模型"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            model_name = "openai/clip-vit-base-patch32"
            self._hf_processor = CLIPProcessor.from_pretrained(model_name)
            self._hf_model = CLIPModel.from_pretrained(model_name)
            self._hf_model.eval()
            
            # 更新维度
            self.config.dimension = 512
            self.config.model_name = model_name
            
            logger.info(f"HuggingFace CLIP 模型加载成功: {model_name}")
            
        except ImportError:
            logger.error("transformers 库未安装，请运行: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"HuggingFace CLIP 模型加载失败: {e}")
            raise
    
    async def _check_ollama_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # 检查是否有视觉模型
                    vision_models = ["llava", "bakllava", "llava-llama3"]
                    for vm in vision_models:
                        if any(vm in m for m in models):
                            self.config.model_name = next(m for m in models if vm in m)
                            return True
                    logger.warning(f"Ollama 没有视觉模型，可用模型: {models}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama 服务检查失败: {e}")
            return False
    
    async def embed_image(self, image_path: str) -> Optional[List[float]]:
        """
        图像嵌入
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            嵌入向量，失败返回 None
        """
        await self.initialize()
        
        if not os.path.exists(image_path):
            logger.error(f"图像文件不存在: {image_path}")
            return None
        
        if self.config.use_huggingface:
            return await self._embed_image_huggingface(image_path)
        else:
            return await self._embed_image_ollama(image_path)
    
    async def _embed_image_ollama(self, image_path: str) -> Optional[List[float]]:
        """使用 Ollama 进行图像嵌入"""
        try:
            # 读取图像并转为 base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # 调用 Ollama API 获取图像描述
            # 注意：Ollama 的 llava 模型不直接返回嵌入向量
            # 我们使用图像描述 + 文本嵌入的方式
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.ollama_base_url}/api/generate",
                    json={
                        "model": self.config.model_name,
                        "prompt": "Describe this image in detail for visual search indexing. Focus on: objects, colors, actions, scene type, mood, and composition.",
                        "images": [image_data],
                        "stream": False,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    description = data.get("response", "")
                    
                    # 使用文本嵌入服务获取向量
                    from .ollama_embedding import get_embedding_service
                    embedding_service = get_embedding_service()
                    embedding = await embedding_service.embed(description)
                    
                    return embedding
                else:
                    logger.error(f"Ollama API 错误: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ollama 图像嵌入失败: {e}")
            return None
    
    async def _embed_image_huggingface(self, image_path: str) -> Optional[List[float]]:
        """使用 HuggingFace CLIP 进行图像嵌入"""
        try:
            from PIL import Image
            import torch
            
            # 加载图像
            image = Image.open(image_path).convert("RGB")
            
            # 处理图像
            inputs = self._hf_processor(images=image, return_tensors="pt")
            
            # 获取图像特征
            with torch.no_grad():
                image_features = self._hf_model.get_image_features(**inputs)
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features[0].tolist()
            
        except Exception as e:
            logger.error(f"HuggingFace 图像嵌入失败: {e}")
            return None
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        文本嵌入（与图像同空间）
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量，失败返回 None
        """
        await self.initialize()
        
        if self.config.use_huggingface:
            return await self._embed_text_huggingface(text)
        else:
            # 使用 Ollama 文本嵌入
            from .ollama_embedding import get_embedding_service
            embedding_service = get_embedding_service()
            return await embedding_service.embed(text)
    
    async def _embed_text_huggingface(self, text: str) -> Optional[List[float]]:
        """使用 HuggingFace CLIP 进行文本嵌入"""
        try:
            import torch
            
            # 处理文本
            inputs = self._hf_processor(text=[text], return_tensors="pt", padding=True)
            
            # 获取文本特征
            with torch.no_grad():
                text_features = self._hf_model.get_text_features(**inputs)
                # 归一化
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features[0].tolist()
            
        except Exception as e:
            logger.error(f"HuggingFace 文本嵌入失败: {e}")
            return None
    
    async def embed_images_batch(
        self,
        image_paths: List[str],
        show_progress: bool = False,
    ) -> List[Optional[List[float]]]:
        """
        批量图像嵌入
        
        Args:
            image_paths: 图像文件路径列表
            show_progress: 是否显示进度
            
        Returns:
            嵌入向量列表
        """
        await self.initialize()
        
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            embedding = await self.embed_image(path)
            results.append(embedding)
            
            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"图像嵌入进度: {i + 1}/{total}")
        
        return results
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数 (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self.config.dimension
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config.model_name


# ============================================================
# 全局实例
# ============================================================

_clip_service: Optional[CLIPEmbeddingService] = None


def get_clip_service() -> CLIPEmbeddingService:
    """获取 CLIP 服务实例"""
    global _clip_service
    
    if _clip_service is None:
        _clip_service = CLIPEmbeddingService()
    
    return _clip_service


async def embed_image(image_path: str) -> Optional[List[float]]:
    """便捷图像嵌入函数"""
    service = get_clip_service()
    return await service.embed_image(image_path)


async def embed_text_visual(text: str) -> Optional[List[float]]:
    """便捷文本嵌入函数（视觉空间）"""
    service = get_clip_service()
    return await service.embed_text(text)
