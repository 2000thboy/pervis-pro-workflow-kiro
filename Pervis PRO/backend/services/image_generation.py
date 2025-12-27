# -*- coding: utf-8 -*-
"""
图片生成服务

集成 Replicate API 进行 AI 图片生成，支持：
- 角色人设图生成
- 场景概念图生成
- 基于人物小传标签生成图片

Requirements: 美术 AI 系统集成
"""
import os
import logging
import httpx
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ImageStyle(Enum):
    """图片风格"""
    REALISTIC = "realistic"           # 写实风格
    ANIME = "anime"                   # 动漫风格
    CONCEPT_ART = "concept_art"       # 概念艺术
    CINEMATIC = "cinematic"           # 电影风格
    ILLUSTRATION = "illustration"     # 插画风格


class ImageType(Enum):
    """图片类型"""
    CHARACTER = "character"           # 角色人设
    SCENE = "scene"                   # 场景概念
    STORYBOARD = "storyboard"         # 故事板
    REFERENCE = "reference"           # 参考图


@dataclass
class ImageGenerationRequest:
    """图片生成请求"""
    prompt: str                                    # 生成提示词
    image_type: ImageType = ImageType.CHARACTER   # 图片类型
    style: ImageStyle = ImageStyle.CINEMATIC      # 风格
    width: int = 1024                             # 宽度
    height: int = 1024                            # 高度
    negative_prompt: str = ""                     # 负面提示词
    entity_id: Optional[str] = None               # 关联实体ID（角色/场景）
    entity_name: Optional[str] = None             # 实体名称
    tags: Dict[str, str] = field(default_factory=dict)  # 标签


@dataclass
class ImageGenerationResult:
    """图片生成结果"""
    id: str
    status: str  # pending, processing, completed, failed
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    prompt: str = ""
    image_type: str = ""
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "image_url": self.image_url,
            "local_path": self.local_path,
            "thumbnail_path": self.thumbnail_path,
            "prompt": self.prompt,
            "image_type": self.image_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "created_at": self.created_at.isoformat(),
            "error": self.error
        }


class ImageGenerationService:
    """
    图片生成服务
    
    使用 Replicate API 生成 AI 图片
    """
    
    # 风格提示词映射
    STYLE_PROMPTS = {
        ImageStyle.REALISTIC: "photorealistic, highly detailed, 8k, professional photography",
        ImageStyle.ANIME: "anime style, vibrant colors, detailed illustration, studio ghibli inspired",
        ImageStyle.CONCEPT_ART: "concept art, digital painting, artstation, detailed environment",
        ImageStyle.CINEMATIC: "cinematic lighting, film still, movie scene, dramatic atmosphere",
        ImageStyle.ILLUSTRATION: "digital illustration, detailed artwork, professional illustration"
    }
    
    # 类型提示词映射
    TYPE_PROMPTS = {
        ImageType.CHARACTER: "character portrait, full body or upper body, clear features, character design",
        ImageType.SCENE: "environment design, wide shot, atmospheric, detailed background",
        ImageType.STORYBOARD: "storyboard frame, composition, camera angle, scene layout",
        ImageType.REFERENCE: "reference image, clear details, professional quality"
    }
    
    # 默认负面提示词
    DEFAULT_NEGATIVE = "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, logo"
    
    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.output_dir = Path(os.getenv("STORAGE_ROOT", "data")) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成任务缓存
        self._tasks: Dict[str, ImageGenerationResult] = {}
    
    @property
    def is_configured(self) -> bool:
        """检查是否已配置 API Token"""
        return bool(self.api_token)
    
    def _build_prompt(self, request: ImageGenerationRequest) -> str:
        """构建完整的生成提示词"""
        parts = []
        
        # 主提示词
        parts.append(request.prompt)
        
        # 添加类型提示
        type_prompt = self.TYPE_PROMPTS.get(request.image_type, "")
        if type_prompt:
            parts.append(type_prompt)
        
        # 添加风格提示
        style_prompt = self.STYLE_PROMPTS.get(request.style, "")
        if style_prompt:
            parts.append(style_prompt)
        
        # 从标签构建额外提示
        if request.tags:
            tag_parts = []
            for key, value in request.tags.items():
                if value and value != "未知":
                    tag_parts.append(f"{value}")
            if tag_parts:
                parts.append(", ".join(tag_parts))
        
        return ", ".join(parts)
    
    def _build_negative_prompt(self, request: ImageGenerationRequest) -> str:
        """构建负面提示词"""
        negative = request.negative_prompt or self.DEFAULT_NEGATIVE
        
        # 角色图额外负面提示
        if request.image_type == ImageType.CHARACTER:
            negative += ", multiple people, crowd, group shot"
        
        return negative

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        生成图片
        
        Args:
            request: 图片生成请求
        
        Returns:
            图片生成结果
        """
        task_id = str(uuid4())
        result = ImageGenerationResult(
            id=task_id,
            status="pending",
            prompt=request.prompt,
            image_type=request.image_type.value,
            entity_id=request.entity_id,
            entity_name=request.entity_name
        )
        self._tasks[task_id] = result
        
        if not self.is_configured:
            result.status = "failed"
            result.error = "未配置 REPLICATE_API_TOKEN，请在 .env 中设置"
            return result
        
        try:
            result.status = "processing"
            
            # 构建提示词
            full_prompt = self._build_prompt(request)
            negative_prompt = self._build_negative_prompt(request)
            
            logger.info(f"开始生成图片: {task_id}, prompt: {full_prompt[:100]}...")
            
            # 调用 Replicate API
            image_url = await self._call_replicate(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                width=request.width,
                height=request.height
            )
            
            if image_url:
                result.image_url = image_url
                
                # 下载并保存到本地
                local_path = await self._download_image(image_url, task_id, request)
                if local_path:
                    result.local_path = local_path
                    result.thumbnail_path = await self._create_thumbnail(local_path)
                
                result.status = "completed"
                logger.info(f"图片生成完成: {task_id}")
            else:
                result.status = "failed"
                result.error = "API 返回空结果"
                
        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            result.status = "failed"
            result.error = str(e)
        
        return result
    
    async def _call_replicate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int
    ) -> Optional[str]:
        """调用 Replicate API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 创建预测
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",  # SDXL
                    "input": {
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "width": width,
                        "height": height,
                        "num_outputs": 1,
                        "scheduler": "K_EULER",
                        "num_inference_steps": 30,
                        "guidance_scale": 7.5
                    }
                }
            )
            
            if response.status_code != 201:
                raise Exception(f"API 错误: {response.status_code} - {response.text}")
            
            prediction = response.json()
            prediction_id = prediction["id"]
            
            # 轮询等待结果
            for _ in range(60):  # 最多等待 60 秒
                await asyncio.sleep(1)
                
                status_response = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {self.api_token}"}
                )
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "succeeded":
                    output = status_data.get("output", [])
                    return output[0] if output else None
                elif status == "failed":
                    raise Exception(status_data.get("error", "生成失败"))
            
            raise Exception("生成超时")
    
    async def _download_image(
        self,
        url: str,
        task_id: str,
        request: ImageGenerationRequest
    ) -> Optional[str]:
        """下载图片到本地"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    # 构建文件名
                    prefix = request.entity_name or request.image_type.value
                    filename = f"{prefix}_{task_id[:8]}.png"
                    filepath = self.output_dir / filename
                    
                    filepath.write_bytes(response.content)
                    return str(filepath)
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
        return None
    
    async def _create_thumbnail(self, image_path: str) -> Optional[str]:
        """创建缩略图"""
        try:
            from PIL import Image
            
            thumb_path = Path(image_path).with_suffix(".thumb.jpg")
            with Image.open(image_path) as img:
                img.thumbnail((256, 256))
                img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path)
        except Exception as e:
            logger.warning(f"创建缩略图失败: {e}")
        return None
    
    def get_task(self, task_id: str) -> Optional[ImageGenerationResult]:
        """获取生成任务状态"""
        return self._tasks.get(task_id)
    
    async def generate_character_image(
        self,
        character_name: str,
        character_bio: str,
        tags: Dict[str, str],
        style: ImageStyle = ImageStyle.CINEMATIC
    ) -> ImageGenerationResult:
        """
        根据角色信息生成人设图
        
        Args:
            character_name: 角色名称
            character_bio: 人物小传
            tags: 角色标签 (gender, age, role 等)
            style: 图片风格
        """
        # 从标签和小传构建提示词
        prompt_parts = [f"portrait of {character_name}"]
        
        # 添加标签信息
        if tags.get("gender"):
            prompt_parts.append(tags["gender"])
        if tags.get("age"):
            prompt_parts.append(f"{tags['age']} years old" if tags["age"].isdigit() else tags["age"])
        if tags.get("personality"):
            prompt_parts.append(f"with {tags['personality']} expression")
        
        # 从小传提取外貌描述（简化处理）
        if character_bio and len(character_bio) > 10:
            # 取小传前100字作为参考
            prompt_parts.append(character_bio[:100])
        
        prompt = ", ".join(prompt_parts)
        
        return await self.generate(ImageGenerationRequest(
            prompt=prompt,
            image_type=ImageType.CHARACTER,
            style=style,
            entity_name=character_name,
            tags=tags
        ))
    
    async def generate_scene_image(
        self,
        scene_name: str,
        scene_description: str,
        time_of_day: str = "",
        style: ImageStyle = ImageStyle.CINEMATIC
    ) -> ImageGenerationResult:
        """
        根据场景信息生成概念图
        
        Args:
            scene_name: 场景名称
            scene_description: 场景描述
            time_of_day: 时间（白天/夜晚等）
            style: 图片风格
        """
        prompt_parts = [scene_description or scene_name]
        
        if time_of_day:
            prompt_parts.append(f"{time_of_day} lighting")
        
        prompt = ", ".join(prompt_parts)
        
        return await self.generate(ImageGenerationRequest(
            prompt=prompt,
            image_type=ImageType.SCENE,
            style=style,
            entity_name=scene_name,
            width=1920,
            height=1080  # 场景用宽屏比例
        ))


# 全局服务实例
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """获取图片生成服务实例"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service
