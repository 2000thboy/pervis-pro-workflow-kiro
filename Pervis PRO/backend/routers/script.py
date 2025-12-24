"""
剧本处理路由
Phase 2: 集成真实的Gemini AI服务和数据库
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.base import ScriptAnalysisRequest, ScriptAnalysisResponse
from services.script_processor import ScriptProcessor
from database import get_db
from pydantic import BaseModel

router = APIRouter()

@router.post("/analyze", response_model=ScriptAnalysisResponse)
async def analyze_script(request: ScriptAnalysisRequest, db: Session = Depends(get_db)):
    """
    剧本分析接口
    Phase 2: 使用Gemini AI进行真实的剧本分析
    """
    
    processor = ScriptProcessor(db)
    result = await processor.analyze_script(request)
    return result

class DemoScriptRequest(BaseModel):
    topic: str = "random"

class DemoScriptResponse(BaseModel):
    title: str
    logline: str
    synopsis: str
    script_content: str

@router.post("/demo", response_model=DemoScriptResponse)
async def generate_demo_script(request: DemoScriptRequest):
    """
    Generate a demo script using the active LLM provider.
    """
    from services.llm_provider import get_llm_provider
    provider = get_llm_provider()
    
    try:
        result = await provider.generate_demo_script(request.topic)
        
        if result.get("status") == "error":
             return DemoScriptResponse(
                title="AI生成失败",
                logline=result.get("message", "未知错误"),
                synopsis="请检查后台日志或稍后重试。",
                script_content=""
            )

        # Ensure result has keys, fallback if AI returns weird stuff
        return DemoScriptResponse(
            title=result.get("title", "生成的剧本"),
            logline=result.get("logline", "无Logline"),
            synopsis=result.get("synopsis", "无梗概"),
            script_content=result.get("script_content", "") or result.get("script", "")
        )
    except Exception as e:
        return DemoScriptResponse(
            title="System Error",
            logline="Generation Failed",
            synopsis=str(e),
            script_content=""
        )