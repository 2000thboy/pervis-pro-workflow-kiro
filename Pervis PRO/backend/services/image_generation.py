# -*- coding: utf-8 -*-
"""
图片生成服务

支持多个图片生成后端：
1. Google Gemini Imagen (推荐，使用 GEMINI_API_KEY)
2. Replicate API (备选)

Requirements: 美术 AI 系统集成
"""
import os
import logging
import httpx
import asyncio
import base64
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# 确保加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)


class ImageStyle(Enum):
    """图片风格"""
    REALISTIC = "realistic"
    ANIME = "anime"
    CONCEPT_ART = "concept_art"
    CINEMATIC = "cinematic"
    ILLUSTRATION = "illustration"


class ImageType(Enum):
    """图片类型"""
    CHARACTER = "character"
    SCENE = "scene"
    STORYBOARD = "storyboard"
    REFERENCE = "reference"


class ImageProvider(Enum):
    """图片生成提供商"""
    GEMINI = "gemini"
    REPLICATE = "replicate"


@dataclass
class ImageGenerationRequest:
    """图片生成请求"""
    prompt: str
    image_type: ImageType = ImageType.CHARACTER
    style: ImageStyle = ImageStyle.CINEMATIC
    width: int = 1024
    height: int = 1024
    negative_prompt: str = ""
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ImageGenerationResult:
    """图片生成结果"""
    id: str
    status: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    prompt: str = ""
    image_type: str = ""
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    provider: str = "gemini"
    
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
            "error": self.error,
            "provider": self.provider
        }


class ImageGenerationService:
    """
    图片生成服务
    
    优先使用 Gemini Imagen，备选 Replicate
    """
    
    STYLE_PROMPTS = {
        ImageStyle.REALISTIC: "photorealistic, highly detailed, 8k, professional photography",
        ImageStyle.ANIME: "anime style, vibrant colors, detailed illustration, studio ghibli inspired",
        ImageStyle.CONCEPT_ART: "concept art, digital painting, artstation, detailed environment",
        ImageStyle.CINEMATIC: "cinematic lighting, film still, movie scene, dramatic atmosphere",
        ImageStyle.ILLUSTRATION: "digital illustration, detailed artwork, professional illustration"
    }
    
    TYPE_PROMPTS = {
        ImageType.CHARACTER: "character portrait, full body or upper body, clear features, character design",
        ImageType.SCENE: "environment design, wide shot, atmospheric, detailed background",
        ImageType.STORYBOARD: "storyboard frame, composition, camera angle, scene layout",
        ImageType.REFERENCE: "reference image, clear details, professional quality"
    }
    
    DEFAULT_NEGATIVE = "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, logo"
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.output_dir = Path(os.getenv("STORAGE_ROOT", "data")) / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, ImageGenerationResult] = {}
        
        # 确定使用哪个提供商
        self._provider = self._detect_provider()
        logger.info(f"图片生成服务初始化，使用提供商: {self._provider}")
    
    def _detect_provider(self) -> ImageProvider:
        """检测可用的图片生成提供商"""
        # 优先使用 Gemini
        if self.gemini_api_key:
            return ImageProvider.GEMINI
        elif self.replicate_token:
            return ImageProvider.REPLICATE
        return ImageProvider.GEMINI  # 默认返回 Gemini，让后续检查报错
    
    @property
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.gemini_api_key) or bool(self.replicate_token)
    
    @property
    def provider_name(self) -> str:
        """当前提供商名称"""
        return self._provider.value
    
    def _build_prompt(self, request: ImageGenerationRequest) -> str:
        """构建完整的生成提示词"""
        parts = [request.prompt]
        
        type_prompt = self.TYPE_PROMPTS.get(request.image_type, "")
        if type_prompt:
            parts.append(type_prompt)
        
        style_prompt = self.STYLE_PROMPTS.get(request.style, "")
        if style_prompt:
            parts.append(style_prompt)
        
        if request.tags:
            tag_parts = [v for v in request.tags.values() if v and v != "未知"]
            if tag_parts:
                parts.append(", ".join(tag_parts))
        
        return ", ".join(parts)

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """生成图片"""
        task_id = str(uuid4())
        result = ImageGenerationResult(
            id=task_id,
            status="pending",
            prompt=request.prompt,
            image_type=request.image_type.value,
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            provider=self._provider.value
        )
        self._tasks[task_id] = result
        
        if not self.is_configured:
            result.status = "failed"
            result.error = "未配置图片生成 API，请在 .env 中设置 GEMINI_API_KEY"
            return result
        
        try:
            result.status = "processing"
            full_prompt = self._build_prompt(request)
            
            logger.info(f"开始生成图片: {task_id}, provider: {self._provider.value}")
            
            # 根据提供商调用不同的 API
            if self._provider == ImageProvider.GEMINI:
                image_data = await self._call_gemini_imagen(full_prompt)
            else:
                image_data = await self._call_replicate(
                    full_prompt,
                    self.DEFAULT_NEGATIVE,
                    request.width,
                    request.height
                )
            
            if image_data:
                # 保存图片
                local_path = await self._save_image(image_data, task_id, request)
                if local_path:
                    result.local_path = local_path
                    # 使用正确的 URL 路径
                    result.image_url = f"/generated-images/{Path(local_path).name}"
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
    
    async def _call_gemini_imagen(self, prompt: str) -> Optional[bytes]:
        """调用 Gemini API 生成图片
        
        使用 Gemini 2.0 Flash 实验版的原生图片生成能力
        """
        async with httpx.AsyncClient(timeout=180.0) as client:
            # 方法1: 尝试 Gemini 2.0 Flash 实验版 (支持原生图片生成)
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
            
            try:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    params={"key": self.gemini_api_key},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"Generate a high-quality image: {prompt}. Make it detailed and professional."
                            }]
                        }],
                        "generationConfig": {
                            "responseModalities": ["image", "text"]
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                image_b64 = part["inlineData"].get("data", "")
                                if image_b64:
                                    logger.info("使用 Gemini 2.0 Flash 生成图片成功")
                                    return base64.b64decode(image_b64)
                    
                    # 如果没有图片数据，可能模型不支持
                    logger.warning("Gemini 2.0 Flash 响应中没有图片数据")
                
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    logger.warning(f"Gemini 2.0 Flash 请求失败: {error_msg}")
                
            except Exception as e:
                logger.warning(f"Gemini 2.0 Flash 调用失败: {e}")
            
            # 方法2: 尝试 Imagen 3 API
            try:
                return await self._call_imagen3(prompt)
            except Exception as e:
                logger.warning(f"Imagen 3 调用失败: {e}")
            
            # 方法3: 如果 Gemini 图片生成都失败，回退到 Replicate
            if self.replicate_token:
                logger.info("回退到 Replicate API")
                return await self._call_replicate(
                    prompt,
                    self.DEFAULT_NEGATIVE,
                    1024,
                    1024
                )
            
            raise Exception("所有图片生成服务都不可用，请检查 API 配置")
    
    async def _call_imagen3(self, prompt: str) -> Optional[bytes]:
        """调用 Imagen 3 API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
            
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                params={"key": self.gemini_api_key},
                json={
                    "instances": [{"prompt": prompt}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "1:1",
                        "safetyFilterLevel": "block_few",
                        "personGeneration": "allow_adult"
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    return base64.b64decode(predictions[0]["bytesBase64Encoded"])
                return None
            elif response.status_code == 403:
                raise Exception("Imagen 3 API 未启用或无权限，请在 Google AI Studio 中启用")
            else:
                raise Exception(f"Imagen 3 API 错误: {response.status_code} - {response.text}")
    
    async def _call_replicate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int
    ) -> Optional[bytes]:
        """调用 Replicate API (备选)"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.replicate_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
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
            
            if response.status_code == 402:
                raise Exception("Replicate API 余额不足")
            
            if response.status_code != 201:
                raise Exception(f"Replicate API 错误: {response.status_code}")
            
            prediction = response.json()
            prediction_id = prediction["id"]
            
            # 轮询等待结果
            for _ in range(60):
                await asyncio.sleep(1)
                status_response = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {self.replicate_token}"}
                )
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "succeeded":
                    output = status_data.get("output", [])
                    if output:
                        # 下载图片
                        img_response = await client.get(output[0])
                        if img_response.status_code == 200:
                            return img_response.content
                    return None
                elif status == "failed":
                    raise Exception(status_data.get("error", "生成失败"))
            
            raise Exception("生成超时")
    
    async def _save_image(
        self,
        image_data: bytes,
        task_id: str,
        request: ImageGenerationRequest
    ) -> Optional[str]:
        """保存图片到本地"""
        try:
            prefix = request.entity_name or request.image_type.value
            # 清理文件名中的非法字符
            safe_prefix = "".join(c for c in prefix if c.isalnum() or c in "._- ")
            filename = f"{safe_prefix}_{task_id[:8]}.png"
            filepath = self.output_dir / filename
            filepath.write_bytes(image_data)
            return str(filepath)
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
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
        """根据角色信息生成人设图"""
        prompt_parts = [f"portrait of {character_name}"]
        
        if tags.get("gender"):
            prompt_parts.append(tags["gender"])
        if tags.get("age"):
            prompt_parts.append(f"{tags['age']} years old" if tags["age"].isdigit() else tags["age"])
        if tags.get("personality"):
            prompt_parts.append(f"with {tags['personality']} expression")
        
        if character_bio and len(character_bio) > 10:
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
        """根据场景信息生成概念图"""
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
            height=1080
        ))


# 全局服务实例
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """获取图片生成服务实例"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service
