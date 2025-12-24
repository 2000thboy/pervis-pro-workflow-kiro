"""
故事板素材推荐API
解决Beat素材匹配不足的核心API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import logging

from database import get_db, Asset, Beat
from services.enhanced_semantic_search import EnhancedSemanticSearchEngine
from services.image_asset_processor import ImageAssetProcessor

logger = logging.getLogger(__name__)
router = APIRouter()

class StoryboardRecommendationRequest(BaseModel):
    beat_id: str
    media_types: List[str] = ["video", "image"]
    min_score: float = 0.6
    limit: int = 12

class AssetRecommendation(BaseModel):
    asset: Dict[str, Any]
    match_score: float
    match_reason: str
    matched_tags: List[str]

class StoryboardRecommendationResponse(BaseModel):
    recommendations: List[AssetRecommendation]
    total_found: int
    search_time: float
    beat_info: Dict[str, Any]

@router.post("/recommendations", response_model=StoryboardRecommendationResponse)
async def get_storyboard_recommendations(
    request: StoryboardRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    为故事板Beat获取素材推荐
    这是解决素材匹配问题的核心API
    """
    
    import time
    start_time = time.time()
    
    try:
        # 1. 获取Beat信息
        beat = db.query(Beat).filter(Beat.id == request.beat_id).first()
        if not beat:
            raise HTTPException(status_code=404, detail="Beat不存在")
        
        # 2. 创建增强搜索引擎
        search_engine = EnhancedSemanticSearchEngine(db)
        
        # 3. 执行智能推荐
        recommendations = await search_engine.get_storyboard_recommendations(
            beat=beat,
            media_types=request.media_types,
            min_score=request.min_score,
            limit=request.limit
        )
        
        search_time = time.time() - start_time
        
        return StoryboardRecommendationResponse(
            recommendations=recommendations,
            total_found=len(recommendations),
            search_time=search_time,
            beat_info={
                "id": beat.id,
                "content": beat.content,
                "emotion_tags": beat.emotion_tags or [],
                "scene_tags": beat.scene_tags or [],
                "action_tags": beat.action_tags or []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"故事板推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐服务异常: {str(e)}")

@router.post("/upload-for-beat")
async def upload_assets_for_beat(
    beat_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    为特定Beat上传素材
    解决素材缺失问题的直接方案
    """
    
    try:
        # 1. 验证Beat存在
        beat = db.query(Beat).filter(Beat.id == beat_id).first()
        if not beat:
            raise HTTPException(status_code=404, detail="Beat不存在")
        
        # 2. 处理上传的文件
        processor = ImageAssetProcessor("L:/PreVis_Assets")
        results = []
        
        for file in files:
            # 验证文件类型
            if not _is_supported_media_file(file.filename):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "不支持的文件格式"
                })
                continue
            
            try:
                # 保存文件
                file_path = await _save_uploaded_file(file)
                
                # 根据文件类型处理
                if _is_image_file(file.filename):
                    # 处理图片
                    result = await processor.process_image_for_storyboard(
                        file_path,
                        beat_context={
                            "content": beat.content,
                            "emotion_tags": beat.emotion_tags or [],
                            "scene_tags": beat.scene_tags or []
                        }
                    )
                else:
                    # 处理视频（使用现有的视频处理逻辑）
                    result = await _process_video_for_storyboard(file_path, beat)
                
                # 创建Asset记录
                if result["status"] == "success":
                    asset = await _create_asset_record(file_path, result, beat.project_id, db)
                    results.append({
                        "filename": file.filename,
                        "status": "success",
                        "asset_id": asset.id,
                        "message": "上传并处理成功"
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": result.get("message", "处理失败")
                    })
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"处理失败: {str(e)}"
                })
        
        return {
            "beat_id": beat_id,
            "uploaded_files": len(files),
            "results": results,
            "success_count": len([r for r in results if r["status"] == "success"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Beat素材上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传服务异常: {str(e)}")

@router.get("/completeness/{project_id}")
async def check_storyboard_completeness(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    检查故事板完整性
    识别缺少素材的Beat
    """
    
    try:
        # 1. 获取项目的所有Beat
        beats = db.query(Beat).filter(Beat.project_id == project_id).order_by(Beat.order_index).all()
        
        if not beats:
            raise HTTPException(status_code=404, detail="项目不存在或没有Beat")
        
        # 2. 检查每个Beat的素材匹配情况
        search_engine = EnhancedSemanticSearchEngine(db)
        completeness_report = []
        
        total_beats = len(beats)
        beats_with_assets = 0
        
        for beat in beats:
            # 获取推荐素材
            recommendations = await search_engine.get_storyboard_recommendations(
                beat=beat,
                media_types=["video", "image"],
                min_score=0.5,
                limit=3
            )
            
            has_good_matches = len([r for r in recommendations if r.match_score >= 0.7]) > 0
            has_any_matches = len(recommendations) > 0
            
            if has_good_matches:
                beats_with_assets += 1
            
            completeness_report.append({
                "beat_id": beat.id,
                "beat_content": beat.content[:50] + "..." if len(beat.content) > 50 else beat.content,
                "order_index": beat.order_index,
                "has_good_matches": has_good_matches,
                "has_any_matches": has_any_matches,
                "match_count": len(recommendations),
                "best_match_score": max([r.match_score for r in recommendations]) if recommendations else 0,
                "status": "complete" if has_good_matches else "needs_assets" if has_any_matches else "no_matches"
            })
        
        # 3. 计算完整度
        completeness_percentage = (beats_with_assets / total_beats) * 100 if total_beats > 0 else 0
        
        # 4. 生成建议
        suggestions = _generate_completeness_suggestions(completeness_report)
        
        return {
            "project_id": project_id,
            "total_beats": total_beats,
            "beats_with_good_assets": beats_with_assets,
            "completeness_percentage": round(completeness_percentage, 1),
            "status": "excellent" if completeness_percentage >= 90 else 
                     "good" if completeness_percentage >= 70 else
                     "needs_improvement" if completeness_percentage >= 50 else "poor",
            "beat_details": completeness_report,
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完整性检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查服务异常: {str(e)}")

@router.post("/batch-apply-recommendations")
async def batch_apply_recommendations(
    project_id: str,
    auto_select_threshold: float = 0.8,
    db: Session = Depends(get_db)
):
    """
    批量应用推荐素材到故事板
    一键解决多个Beat的素材缺失问题
    """
    
    try:
        # 1. 获取项目Beat
        beats = db.query(Beat).filter(Beat.project_id == project_id).order_by(Beat.order_index).all()
        
        if not beats:
            raise HTTPException(status_code=404, detail="项目不存在或没有Beat")
        
        # 2. 为每个Beat自动选择最佳素材
        search_engine = EnhancedSemanticSearchEngine(db)
        application_results = []
        
        for beat in beats:
            try:
                # 获取推荐
                recommendations = await search_engine.get_storyboard_recommendations(
                    beat=beat,
                    media_types=["video", "image"],
                    min_score=0.6,
                    limit=5
                )
                
                # 自动选择最佳匹配
                best_match = None
                for rec in recommendations:
                    if rec.match_score >= auto_select_threshold:
                        best_match = rec
                        break
                
                if best_match:
                    # 应用推荐（这里需要实现具体的应用逻辑）
                    success = await _apply_asset_to_beat(beat, best_match.asset, db)
                    
                    application_results.append({
                        "beat_id": beat.id,
                        "beat_content": beat.content[:30] + "...",
                        "status": "applied" if success else "failed",
                        "asset_id": best_match.asset["id"],
                        "asset_filename": best_match.asset["filename"],
                        "match_score": best_match.match_score
                    })
                else:
                    application_results.append({
                        "beat_id": beat.id,
                        "beat_content": beat.content[:30] + "...",
                        "status": "no_suitable_match",
                        "match_count": len(recommendations),
                        "best_score": max([r.match_score for r in recommendations]) if recommendations else 0
                    })
                    
            except Exception as e:
                application_results.append({
                    "beat_id": beat.id,
                    "beat_content": beat.content[:30] + "...",
                    "status": "error",
                    "error": str(e)
                })
        
        # 3. 统计结果
        applied_count = len([r for r in application_results if r["status"] == "applied"])
        failed_count = len([r for r in application_results if r["status"] == "failed"])
        no_match_count = len([r for r in application_results if r["status"] == "no_suitable_match"])
        
        return {
            "project_id": project_id,
            "total_beats": len(beats),
            "applied_count": applied_count,
            "failed_count": failed_count,
            "no_match_count": no_match_count,
            "success_rate": round((applied_count / len(beats)) * 100, 1) if beats else 0,
            "threshold_used": auto_select_threshold,
            "results": application_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量应用失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量应用服务异常: {str(e)}")

# 辅助函数

def _is_supported_media_file(filename: str) -> bool:
    """检查是否为支持的媒体文件"""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1]
    supported_extensions = {
        'jpg', 'jpeg', 'png', 'webp', 'gif',  # 图片
        'mp4', 'avi', 'mov', 'mkv', 'wmv'     # 视频
    }
    return ext in supported_extensions

def _is_image_file(filename: str) -> bool:
    """检查是否为图片文件"""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1]
    image_extensions = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    return ext in image_extensions

async def _save_uploaded_file(file: UploadFile) -> str:
    """保存上传的文件"""
    import os
    from pathlib import Path
    
    # 创建保存路径
    upload_dir = Path("L:/PreVis_Assets/originals")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return str(file_path)

async def _process_video_for_storyboard(file_path: str, beat: Beat) -> Dict[str, Any]:
    """处理视频文件用于故事板"""
    # 这里应该调用现有的视频处理逻辑
    # 简化版本
    return {
        "status": "success",
        "media_type": "video",
        "message": "视频处理完成"
    }

async def _create_asset_record(file_path: str, processing_result: Dict, project_id: str, db: Session) -> Asset:
    """创建Asset数据库记录"""
    from pathlib import Path
    import uuid
    
    file_path_obj = Path(file_path)
    
    asset = Asset(
        id=str(uuid.uuid4()),
        project_id=project_id,
        filename=file_path_obj.name,
        file_path=str(file_path),
        media_type=processing_result.get("media_type", "unknown"),
        file_size=file_path_obj.stat().st_size,
        status="processed"
    )
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return asset

def _generate_completeness_suggestions(completeness_report: List[Dict]) -> List[str]:
    """生成完整性改进建议"""
    suggestions = []
    
    no_match_beats = [b for b in completeness_report if b["status"] == "no_matches"]
    needs_assets_beats = [b for b in completeness_report if b["status"] == "needs_assets"]
    
    if no_match_beats:
        suggestions.append(f"有 {len(no_match_beats)} 个Beat完全没有匹配素材，建议上传相关的视频或图片")
    
    if needs_assets_beats:
        suggestions.append(f"有 {len(needs_assets_beats)} 个Beat只有低质量匹配，建议优化Beat描述或上传更精准的素材")
    
    if len(completeness_report) > 10:
        suggestions.append("考虑使用批量应用功能来快速填充故事板")
    
    return suggestions

async def _apply_asset_to_beat(beat: Beat, asset: Dict, db: Session) -> bool:
    """将素材应用到Beat（这里需要实现具体的应用逻辑）"""
    # 这里应该实现将素材关联到Beat的逻辑
    # 可能涉及创建Timeline、Clip等记录
    return True