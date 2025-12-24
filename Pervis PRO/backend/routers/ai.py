"""
AI 服务路由
提供标签生成、资产描述、粗剪分析等 AI 功能的 API 端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from services.llm_provider import get_llm_provider, check_ai_services, LLMConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])


# ==================== 请求/响应模型 ====================

class GenerateTagsRequest(BaseModel):
    """标签生成请求"""
    content: str = Field(..., description="Beat/场景内容")


class GenerateTagsResponse(BaseModel):
    """标签生成响应"""
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class GenerateDescriptionRequest(BaseModel):
    """资产描述生成请求"""
    asset_id: str = Field(..., description="资产ID")
    filename: str = Field(..., description="文件名")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class GenerateDescriptionResponse(BaseModel):
    """资产描述生成响应"""
    status: str
    description: str


class RoughCutRequest(BaseModel):
    """AI 粗剪请求"""
    script_content: str = Field(..., description="剧本内容")
    video_tags: Dict[str, Any] = Field(..., description="视频标签数据")


class RoughCutResponse(BaseModel):
    """AI 粗剪响应"""
    status: str
    inPoint: Optional[float] = None
    outPoint: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    message: Optional[str] = None


# ==================== API 端点 ====================

@router.post("/generate-tags", response_model=GenerateTagsResponse)
async def generate_tags(request: GenerateTagsRequest):
    """
    生成 Beat 标签
    
    基于剧本内容使用 AI 生成结构化标签，包括：
    - scene_slug: 场景标识
    - location_type: 位置类型 (INT/EXT)
    - time_of_day: 时间 (DAY/NIGHT/DAWN/DUSK)
    - primary_emotion: 主要情绪
    - key_action: 关键动作
    - visual_notes: 视觉备注
    - shot_type: 镜头类型
    """
    try:
        provider = get_llm_provider()
        result = await provider.generate_beat_tags(request.content)
        
        if result.get("status") == "error":
            return GenerateTagsResponse(
                status="error",
                message=result.get("message", "标签生成失败")
            )
        
        return GenerateTagsResponse(
            status="success",
            data=result.get("data", result)
        )
        
    except ValueError as e:
        logger.error(f"AI Configuration Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Generate tags failed: {e}")
        raise HTTPException(status_code=500, detail=f"标签生成失败: {str(e)}")


@router.post("/generate-description", response_model=GenerateDescriptionResponse)
async def generate_description(request: GenerateDescriptionRequest):
    """
    生成资产描述
    
    基于文件名和元数据使用 AI 生成视频素材的描述文字
    """
    try:
        provider = get_llm_provider()
        description = await provider.generate_asset_description(
            request.filename,
            request.metadata
        )
        
        return GenerateDescriptionResponse(
            status="success",
            description=description
        )
        
    except ValueError as e:
        logger.error(f"AI Configuration Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Generate description failed: {e}")
        raise HTTPException(status_code=500, detail=f"描述生成失败: {str(e)}")


@router.post("/rough-cut", response_model=RoughCutResponse)
async def rough_cut_analysis(request: RoughCutRequest):
    """
    AI 粗剪分析
    
    基于剧本内容和视频标签，使用 AI 分析并推荐最佳的入出点
    返回：
    - inPoint: 入点时间（秒）
    - outPoint: 出点时间（秒）
    - confidence: 置信度 (0-1)
    - reason: AI 生成的推荐理由
    """
    try:
        provider = get_llm_provider()
        result = await provider.analyze_rough_cut(
            request.script_content,
            request.video_tags
        )
        
        if result.get("status") == "error":
            return RoughCutResponse(
                status="error",
                message=result.get("message", "粗剪分析失败")
            )
        
        data = result.get("data", result)
        return RoughCutResponse(
            status="success",
            inPoint=data.get("inPoint"),
            outPoint=data.get("outPoint"),
            confidence=data.get("confidence"),
            reason=data.get("reason")
        )
        
    except ValueError as e:
        logger.error(f"AI Configuration Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Rough cut analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"粗剪分析失败: {str(e)}")


@router.get("/health")
async def ai_health_check():
    """
    AI 服务健康检查
    
    检查 AI 服务是否可用
    """
    try:
        provider = get_llm_provider()
        provider_type = type(provider).__name__
        
        return {
            "status": "healthy",
            "provider": provider_type,
            "message": f"AI 服务正常 ({provider_type})"
        }
        
    except ValueError as e:
        return {
            "status": "unhealthy",
            "provider": None,
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "provider": None,
            "message": f"AI 服务异常: {str(e)}"
        }


@router.get("/services")
async def get_ai_services_status():
    """
    获取所有 AI 服务的状态
    
    返回 Ollama 和 Gemini 服务的可用性信息，
    供前端显示服务选择界面
    """
    try:
        services = await check_ai_services()
        return {
            "status": "success",
            "services": services
        }
    except Exception as e:
        logger.error(f"检查 AI 服务状态失败: {e}")
        return {
            "status": "error",
            "message": f"检查服务状态失败: {str(e)}",
            "services": None
        }


class SwitchProviderRequest(BaseModel):
    """切换 AI 服务请求"""
    provider: str = Field(..., description="目标服务: ollama, gemini, auto")


@router.post("/switch-provider")
async def switch_ai_provider(request: SwitchProviderRequest):
    """
    切换 AI 服务提供者
    
    注意: 此操作仅在当前会话生效，重启后会恢复为 .env 配置
    如需永久更改，请修改 .env 文件中的 LLM_PROVIDER
    """
    valid_providers = ["ollama", "local", "gemini", "auto"]
    
    if request.provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"无效的服务类型。支持: {', '.join(valid_providers)}"
        )
    
    # 更新运行时配置
    old_provider = LLMConfig.PROVIDER
    LLMConfig.PROVIDER = request.provider.lower()
    
    # 验证新配置是否可用
    try:
        provider = get_llm_provider()
        provider_type = type(provider).__name__
        
        return {
            "status": "success",
            "message": f"已切换到 {provider_type}",
            "previous_provider": old_provider,
            "current_provider": request.provider,
            "note": "此更改仅在当前会话生效，重启后恢复为 .env 配置"
        }
    except Exception as e:
        # 回滚配置
        LLMConfig.PROVIDER = old_provider
        raise HTTPException(
            status_code=500,
            detail=f"切换失败: {str(e)}。已回滚到 {old_provider}"
        )
