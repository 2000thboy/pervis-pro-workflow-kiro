"""
多模态搜索API路由
Phase 4: 融合文本、音频、视觉的综合搜索API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.multimodal_search import MultimodalSearchService as MultimodalSearchEngine
from services.visual_processor import VisualProcessor
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])

class MultimodalSearchRequest(BaseModel):
    query: str
    beat_id: Optional[str] = None
    search_modes: Optional[List[str]] = None  # ['semantic', 'transcription', 'visual']
    weights: Optional[Dict[str, float]] = None  # {'semantic': 0.4, 'transcription': 0.3, 'visual': 0.3}
    fuzziness: float = 0.7
    limit: int = 10

class VisualSearchRequest(BaseModel):
    query: str
    visual_tags: Optional[Dict[str, str]] = None
    limit: int = 10

class VisualAnalysisRequest(BaseModel):
    asset_id: str
    sample_interval: float = 2.0
    force_reanalyze: bool = False

@router.post("/search")
async def multimodal_search(
    request: MultimodalSearchRequest,
    db: Session = Depends(get_db)
):
    """
    多模态综合搜索
    """
    
    try:
        search_engine = MultimodalSearchEngine(db)
        
        result = await search_engine.multimodal_search(
            query=request.query,
            beat_id=request.beat_id,
            search_modes=request.search_modes,
            weights=request.weights,
            fuzziness=request.fuzziness,
            limit=request.limit
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多模态搜索失败: {str(e)}")

@router.post("/search/beatboard")
async def beatboard_media_search(
    request: MultimodalSearchRequest,
    db: Session = Depends(get_db)
):
    """
    BeatBoard专用的媒体推荐搜索
    同时搜索视频和图片，返回统一格式的结果
    """
    
    try:
        search_engine = MultimodalSearchEngine(db)
        
        # 执行多模态搜索（主要是视频）
        multimodal_result = await search_engine.multimodal_search(
            query=request.query,
            beat_id=request.beat_id,
            search_modes=request.search_modes or ['semantic', 'transcription', 'visual'],
            weights=request.weights or {'semantic': 0.4, 'transcription': 0.3, 'visual': 0.3},
            fuzziness=request.fuzziness,
            limit=request.limit // 2  # 一半给视频
        )
        
        # 执行图片搜索
        from services.image_search_engine import ImageSearchEngine
        
        image_search_engine = ImageSearchEngine(db)
        image_results = await image_search_engine.search_by_text(
            query=request.query,
            project_id="default",  # 可以从请求中获取
            limit=request.limit // 2,  # 一半给图片
            similarity_threshold=0.3
        )
        
        # 合并结果
        combined_results = []
        
        # 添加视频结果
        if multimodal_result.get("status") == "success" and multimodal_result.get("results"):
            for result in multimodal_result["results"]:
                combined_results.append({
                    "id": result["asset_id"],
                    "type": "video",
                    "filename": result["filename"],
                    "thumbnail_url": result.get("thumbnail_url"),
                    "proxy_url": result.get("proxy_url"),
                    "original_url": result.get("proxy_url", f"/assets/videos/{result['asset_id']}"),
                    "similarity_score": result.get("final_score", 0.5),
                    "match_reason": result.get("multimodal_reason", "多模态匹配"),
                    "match_details": result.get("match_details", {}),
                    "metadata": {
                        "match_modes": result.get("match_modes", []),
                        "type": "video"
                    }
                })
        
        # 添加图片结果
        for result in image_results:
            combined_results.append({
                "id": result.id,
                "type": "image",
                "filename": result.filename,
                "thumbnail_url": result.thumbnail_url,
                "original_url": result.original_url,
                "similarity_score": result.similarity_score,
                "match_reason": result.match_reason,
                "tags": result.tags,
                "color_palette": result.color_palette,
                "metadata": {
                    "width": result.metadata.get("width"),
                    "height": result.metadata.get("height"),
                    "file_size": result.metadata.get("file_size"),
                    "type": "image"
                }
            })
        
        # 按相似度排序
        combined_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # 限制结果数量
        combined_results = combined_results[:request.limit]
        
        return {
            "status": "success",
            "query": request.query,
            "total_results": len(combined_results),
            "video_results": len([r for r in combined_results if r["type"] == "video"]),
            "image_results": len([r for r in combined_results if r["type"] == "image"]),
            "results": combined_results
        }
        
    except Exception as e:
        logger.error(f"BeatBoard媒体搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"媒体搜索失败: {str(e)}")

@router.post("/search/visual")
async def visual_search(
    request: VisualSearchRequest,
    db: Session = Depends(get_db)
):
    """
    纯视觉特征搜索
    """
    
    try:
        search_engine = MultimodalSearchEngine(db)
        
        # 构建查询意图
        query_intent = {
            "primary_intent": "visual",
            "visual_keywords": request.query.split(),
            "audio_keywords": [],
            "emotion_keywords": [],
            "scene_keywords": [],
            "action_keywords": [],
            "technical_keywords": []
        }
        
        # 执行视觉搜索
        visual_results = await search_engine._search_visual_content(
            request.query, query_intent, request.limit
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results": visual_results,
            "total_matches": len(visual_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视觉搜索失败: {str(e)}")

@router.post("/analyze/visual/{asset_id}")
async def analyze_visual_features(
    asset_id: str,
    request: VisualAnalysisRequest = None,
    db: Session = Depends(get_db)
):
    """
    为指定资产进行视觉特征分析
    """
    
    try:
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(db)
        visual_processor = VisualProcessor()
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 检查是否已有视觉分析数据
        existing_visual_data = db_service.get_visual_data(asset_id)
        if existing_visual_data and not (request and request.force_reanalyze):
            return {
                "status": "success",
                "message": "视觉分析数据已存在",
                "visual_analysis": existing_visual_data
            }
        
        # 检查视频文件是否存在
        if not asset.file_path:
            raise HTTPException(status_code=400, detail="资产文件路径不存在")
        
        # 执行视觉分析
        sample_interval = request.sample_interval if request else 2.0
        result = await visual_processor.extract_visual_features(
            asset.file_path, asset_id, sample_interval
        )
        
        if result["status"] == "success":
            # 存储视觉分析数据
            visual_data = result["visual_analysis"]
            db_service.store_visual_data(asset_id, visual_data)
            
            return {
                "status": "success",
                "message": "视觉分析完成",
                "visual_analysis": visual_data
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "视觉分析失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视觉分析处理失败: {str(e)}")

@router.get("/visual/status/{asset_id}")
async def get_visual_analysis_status(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    获取资产的视觉分析状态
    """
    
    try:
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(db)
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 获取视觉分析数据
        visual_data = db_service.get_visual_data(asset_id)
        
        if visual_data:
            visual_summary = visual_data.get("visual_description", {}).get("visual_summary", {})
            
            return {
                "status": "completed",
                "has_visual_analysis": True,
                "duration": visual_data.get("duration", 0),
                "keyframes_count": visual_data.get("keyframes_count", 0),
                "sample_interval": visual_data.get("sample_interval", 2.0),
                "visual_summary": visual_summary
            }
        else:
            return {
                "status": "not_analyzed",
                "has_visual_analysis": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")

@router.get("/visual/data/{asset_id}")
async def get_visual_analysis_data(
    asset_id: str,
    include_keyframes: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取资产的完整视觉分析数据
    """
    
    try:
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(db)
        
        # 检查资产是否存在
        asset = db_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 获取视觉分析数据
        visual_data = db_service.get_visual_data(asset_id)
        
        if not visual_data:
            raise HTTPException(status_code=404, detail="视觉分析数据不存在")
        
        # 如果不需要关键帧数据，移除以减少响应大小
        if not include_keyframes and "keyframes" in visual_data:
            visual_data_copy = visual_data.copy()
            visual_data_copy["keyframes"] = []
            visual_data_copy["keyframes_summary"] = f"共{len(visual_data['keyframes'])}个关键帧"
            visual_data = visual_data_copy
        
        return {
            "status": "success",
            "visual_analysis": visual_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据获取失败: {str(e)}")

@router.get("/model/info")
async def get_multimodal_model_info():
    """
    获取多模态模型信息
    """
    
    try:
        visual_processor = VisualProcessor()
        visual_info = visual_processor.get_model_info()
        
        # 获取其他模型信息
        from services.audio_transcriber import AudioTranscriber
        from services.semantic_search import SemanticSearchEngine
        from database import get_db
        
        audio_transcriber = AudioTranscriber()
        audio_info = audio_transcriber.get_model_info()
        
        db = next(get_db())
        semantic_search = SemanticSearchEngine(db)
        
        return {
            "status": "success",
            "multimodal_capabilities": {
                "visual_analysis": visual_info,
                "audio_transcription": audio_info,
                "semantic_search": {
                    "available": True,
                    "model": "sentence-transformers",
                    "features": ["text_embedding", "similarity_search"]
                }
            },
            "supported_search_modes": ["semantic", "transcription", "visual"],
            "default_weights": {
                "semantic": 0.4,
                "transcription": 0.3,
                "visual": 0.3
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型信息获取失败: {str(e)}")

@router.post("/estimate")
async def estimate_multimodal_processing_time(
    video_duration: float,
    enable_transcription: bool = True,
    enable_visual_analysis: bool = True,
    sample_interval: float = 2.0
):
    """
    估算多模态处理时间
    """
    
    try:
        total_time = 0
        breakdown = {}
        
        # 基础视频处理时间
        base_processing = video_duration * 0.1
        total_time += base_processing
        breakdown["video_processing"] = base_processing
        
        # 转录处理时间
        if enable_transcription:
            from services.audio_transcriber import AudioTranscriber
            transcriber = AudioTranscriber()
            transcription_time = transcriber.estimate_processing_time(video_duration)
            total_time += transcription_time
            breakdown["transcription"] = transcription_time
        
        # 视觉分析处理时间
        if enable_visual_analysis:
            visual_processor = VisualProcessor()
            visual_time = visual_processor.estimate_processing_time(video_duration, sample_interval)
            total_time += visual_time
            breakdown["visual_analysis"] = visual_time
        
        # 向量化时间
        vectorization_time = video_duration * 0.05
        total_time += vectorization_time
        breakdown["vectorization"] = vectorization_time
        
        return {
            "status": "success",
            "video_duration": video_duration,
            "total_estimated_time": total_time,
            "processing_breakdown": breakdown,
            "configuration": {
                "transcription_enabled": enable_transcription,
                "visual_analysis_enabled": enable_visual_analysis,
                "sample_interval": sample_interval
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"时间估算失败: {str(e)}")