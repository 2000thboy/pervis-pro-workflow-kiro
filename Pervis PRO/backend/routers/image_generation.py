# -*- coding: utf-8 -*-
"""
图片生成 API 路由

提供 AI 图片生成接口，支持：
- 角色人设图生成
- 场景概念图生成
- 从人物小传标签生成图片
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter()


class ImageStyleEnum(str, Enum):
    """图片风格"""
    realistic = "realistic"
    anime = "anime"
    concept_art = "concept_art"
    cinematic = "cinematic"
    illustration = "illustration"


class ImageTypeEnum(str, Enum):
    """图片类型"""
    character = "character"
    scene = "scene"
    storyboard = "storyboard"
    reference = "reference"


class GenerateImageRequest(BaseModel):
    """通用图片生成请求"""
    prompt: str = Field(..., description="生成提示词")
    image_type: ImageTypeEnum = Field(ImageTypeEnum.character, description="图片类型")
    style: ImageStyleEnum = Field(ImageStyleEnum.cinematic, description="图片风格")
    width: int = Field(1024, ge=512, le=2048, description="图片宽度")
    height: int = Field(1024, ge=512, le=2048, description="图片高度")
    negative_prompt: str = Field("", description="负面提示词")
    entity_id: Optional[str] = Field(None, description="关联实体ID")
    entity_name: Optional[str] = Field(None, description="实体名称")
    tags: Dict[str, str] = Field(default_factory=dict, description="标签")


class GenerateCharacterImageRequest(BaseModel):
    """角色人设图生成请求"""
    character_name: str = Field(..., description="角色名称")
    character_bio: str = Field("", description="人物小传")
    tags: Dict[str, str] = Field(default_factory=dict, description="角色标签")
    style: ImageStyleEnum = Field(ImageStyleEnum.cinematic, description="图片风格")
    character_id: Optional[str] = Field(None, description="角色ID")


class GenerateSceneImageRequest(BaseModel):
    """场景概念图生成请求"""
    scene_name: str = Field(..., description="场景名称")
    scene_description: str = Field("", description="场景描述")
    time_of_day: str = Field("", description="时间（白天/夜晚等）")
    style: ImageStyleEnum = Field(ImageStyleEnum.cinematic, description="图片风格")
    scene_id: Optional[str] = Field(None, description="场景ID")


class ImageGenerationResponse(BaseModel):
    """图片生成响应"""
    id: str
    status: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    prompt: str = ""
    image_type: str = ""
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    error: Optional[str] = None


class ServiceStatusResponse(BaseModel):
    """服务状态响应"""
    configured: bool
    provider: str = "replicate"
    message: str


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """获取图片生成服务状态"""
    from services.image_generation import get_image_generation_service
    
    service = get_image_generation_service()
    
    return ServiceStatusResponse(
        configured=service.is_configured,
        provider=service.provider_name,
        message=f"服务已配置 ({service.provider_name})" if service.is_configured else "未配置 GEMINI_API_KEY 或 REPLICATE_API_TOKEN"
    )


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(request: GenerateImageRequest):
    """
    通用图片生成接口
    
    根据提示词生成 AI 图片
    """
    from services.image_generation import (
        get_image_generation_service,
        ImageGenerationRequest,
        ImageType,
        ImageStyle
    )
    
    service = get_image_generation_service()
    
    if not service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="图片生成服务未配置，请设置 REPLICATE_API_TOKEN"
        )
    
    try:
        result = await service.generate(ImageGenerationRequest(
            prompt=request.prompt,
            image_type=ImageType(request.image_type.value),
            style=ImageStyle(request.style.value),
            width=request.width,
            height=request.height,
            negative_prompt=request.negative_prompt,
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            tags=request.tags
        ))
        
        return ImageGenerationResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"图片生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/character", response_model=ImageGenerationResponse)
async def generate_character_image(request: GenerateCharacterImageRequest):
    """
    角色人设图生成接口
    
    根据角色名称、人物小传和标签生成人设图
    """
    from services.image_generation import get_image_generation_service, ImageStyle
    
    service = get_image_generation_service()
    
    if not service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="图片生成服务未配置，请设置 REPLICATE_API_TOKEN"
        )
    
    try:
        result = await service.generate_character_image(
            character_name=request.character_name,
            character_bio=request.character_bio,
            tags=request.tags,
            style=ImageStyle(request.style.value)
        )
        
        # 更新 entity_id
        if request.character_id:
            result.entity_id = request.character_id
        
        return ImageGenerationResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"角色图片生成失败: {e}")
        error_msg = str(e)
        # 检查是否是余额不足错误
        if "余额不足" in error_msg or "402" in error_msg or "Insufficient credit" in error_msg:
            raise HTTPException(
                status_code=402,
                detail="Replicate API 余额不足，请前往 https://replicate.com/account/billing 充值后重试"
            )
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/scene", response_model=ImageGenerationResponse)
async def generate_scene_image(request: GenerateSceneImageRequest):
    """
    场景概念图生成接口
    
    根据场景名称和描述生成概念图
    """
    from services.image_generation import get_image_generation_service, ImageStyle
    
    service = get_image_generation_service()
    
    if not service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="图片生成服务未配置，请设置 REPLICATE_API_TOKEN"
        )
    
    try:
        result = await service.generate_scene_image(
            scene_name=request.scene_name,
            scene_description=request.scene_description,
            time_of_day=request.time_of_day,
            style=ImageStyle(request.style.value)
        )
        
        if request.scene_id:
            result.entity_id = request.scene_id
        
        return ImageGenerationResponse(**result.to_dict())
        
    except Exception as e:
        logger.error(f"场景图片生成失败: {e}")
        error_msg = str(e)
        # 检查是否是余额不足错误
        if "余额不足" in error_msg or "402" in error_msg or "Insufficient credit" in error_msg:
            raise HTTPException(
                status_code=402,
                detail="Replicate API 余额不足，请前往 https://replicate.com/account/billing 充值后重试"
            )
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/task/{task_id}", response_model=ImageGenerationResponse)
async def get_task_status(task_id: str):
    """获取生成任务状态"""
    from services.image_generation import get_image_generation_service
    
    service = get_image_generation_service()
    result = service.get_task(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return ImageGenerationResponse(**result.to_dict())
