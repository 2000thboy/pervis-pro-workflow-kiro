"""
转录API路由
Phase 4: 音频转录相关的API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.database_service import DatabaseService
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# 延迟导入AudioTranscriber，避免启动时因依赖问题失败
try:
    from services.audio_transcriber import AudioTranscriber
    TRANSCRIBER_AVAILABLE = True
except Exception as e:
    logger.warning(f"AudioTranscriber导入失败，转录功能将不可用: {e}")
    TRANSCRIBER_AVAILABLE = False
    AudioTranscriber = None

router = APIRouter(prefix="/api/transcription", tags=["transcription"])

class TranscriptionRequest(BaseModel):
    asset_id: str
    force_retranscribe: bool = False

class TranscriptionSearchRequest(BaseModel):
    query: str
    limit: int = 10

@router.post("/transcribe/{asset_id}")
async def transcribe_asset(
    asset_id: str,
    request: TranscriptionRequest = None,
    db: Session = Depends(get_db)
):
    """
    为指定资产进行音频转录
    """
    
    if not TRANSCRIBER_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="转录服务暂不可用 - Whisper依赖未安装"
        )
    
    try:
        db_service = DatabaseService(db)
        transcriber = AudioTranscriber()
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 检查是否已有转录数据
        existing_transcription = db_service.get_transcription_data(asset_id)
        if existing_transcription and not (request and request.force_retranscribe):
            return {
                "status": "success",
                "message": "转录数据已存在",
                "transcription": existing_transcription
            }
        
        # 检查音频文件是否存在
        if not asset.file_path:
            raise HTTPException(status_code=400, detail="资产文件路径不存在")
        
        # 构建音频文件路径 (假设音频文件在audio目录下)
        import os
        audio_path = asset.file_path.replace("/originals/", "/audio/").replace(".mp4", ".wav")
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="音频文件不存在")
        
        # 执行转录
        result = await transcriber.transcribe_audio(audio_path, asset_id)
        
        if result["status"] == "success":
            # 存储转录数据
            transcription_data = result["transcription"]
            db_service.store_transcription_data(asset_id, transcription_data)
            
            return {
                "status": "success",
                "message": "转录完成",
                "transcription": transcription_data,
                "processing_info": result.get("processing_info", {})
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "转录失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转录处理失败: {str(e)}")

@router.get("/status/{asset_id}")
async def get_transcription_status(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    获取资产的转录状态
    """
    
    try:
        db_service = DatabaseService(db)
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 获取转录数据
        transcription_data = db_service.get_transcription_data(asset_id)
        
        if transcription_data:
            return {
                "status": "completed",
                "has_transcription": True,
                "language": transcription_data.get("language", "unknown"),
                "duration": transcription_data.get("duration", 0),
                "segments_count": len(transcription_data.get("segments", [])),
                "statistics": transcription_data.get("statistics", {})
            }
        else:
            return {
                "status": "not_transcribed",
                "has_transcription": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")

@router.get("/data/{asset_id}")
async def get_transcription_data(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    获取资产的完整转录数据
    """
    
    try:
        db_service = DatabaseService(db)
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 获取转录数据
        transcription_data = db_service.get_transcription_data(asset_id)
        
        if not transcription_data:
            raise HTTPException(status_code=404, detail="转录数据不存在")
        
        return {
            "status": "success",
            "transcription": transcription_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据获取失败: {str(e)}")

@router.post("/search")
async def search_transcription_text(
    request: TranscriptionSearchRequest,
    db: Session = Depends(get_db)
):
    """
    在转录文本中搜索关键词
    """
    
    try:
        db_service = DatabaseService(db)
        
        # 执行搜索
        results = db_service.search_transcription_text(request.query, request.limit)
        
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "total_matches": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/model/info")
async def get_model_info():
    """
    获取转录模型信息
    """
    
    if not TRANSCRIBER_AVAILABLE:
        return {
            "status": "unavailable",
            "model_info": {"available": False, "reason": "Whisper dependencies not installed"},
            "supported_languages": []
        }
    
    try:
        transcriber = AudioTranscriber()
        model_info = transcriber.get_model_info()
        
        return {
            "status": "success",
            "model_info": model_info,
            "supported_languages": transcriber.get_supported_languages()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型信息获取失败: {str(e)}")

@router.post("/estimate")
async def estimate_processing_time(
    duration: float
):
    """
    估算转录处理时间
    """
    
    if not TRANSCRIBER_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "转录服务不可用",
            "audio_duration": duration,
            "estimated_processing_time": 0
        }
    
    try:
        transcriber = AudioTranscriber()
        estimated_time = transcriber.estimate_processing_time(duration)
        
        return {
            "status": "success",
            "audio_duration": duration,
            "estimated_processing_time": estimated_time,
            "model_size": transcriber.model_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"时间估算失败: {str(e)}")