"""
图片管理API路由
处理图片上传、查询、删除和搜索功能
"""

import os
import json
import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, ImageAsset, ImageVector
from services.image_processor import ImageProcessor
from services.image_analyzer import ImageAnalyzer
from services.image_search_engine import ImageSearchEngine, ImageSearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])

# 初始化服务
image_processor = ImageProcessor()
image_analyzer = ImageAnalyzer()  # CLIP模型可用，但会自动fallback到Mock模式

# Pydantic模型
class ImageUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None

class ImageSearchRequest(BaseModel):
    query: str
    project_id: str
    limit: int = 10
    similarity_threshold: float = 0.3

class ImageTagSearchRequest(BaseModel):
    tags: List[str]
    project_id: str
    match_mode: str = "any"  # "any" or "all"
    limit: int = 10

class ImageColorSearchRequest(BaseModel):
    color: str  # 十六进制颜色值
    project_id: str
    tolerance: float = 0.3
    limit: int = 10

class ImageInfo(BaseModel):
    id: str
    filename: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    original_url: str
    tags: Optional[Dict[str, List[str]]]
    color_palette: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_status: str
    created_at: datetime

@router.post("/upload", response_model=List[ImageUploadResponse])
async def upload_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传图片文件"""
    try:
        logger.info(f"开始上传 {len(files)} 个图片文件到项目 {project_id}")
        
        results = []
        
        for file in files:
            try:
                # 验证文件类型
                if not file.content_type or not file.content_type.startswith('image/'):
                    results.append(ImageUploadResponse(
                        id="",
                        filename=file.filename or "unknown",
                        status="error",
                        error="不支持的文件类型"
                    ))
                    continue
                
                # 读取文件内容
                file_content = await file.read()
                
                # 处理图片
                process_result = await image_processor.process_image(
                    file_content, file.filename or "unknown", project_id
                )
                
                if process_result.get("processing_status") == "completed":
                    # 创建数据库记录
                    image_asset = ImageAsset(
                        id=process_result["id"],
                        project_id=project_id,
                        filename=process_result["filename"],
                        original_path=process_result["original_path"],
                        thumbnail_path=process_result.get("thumbnail_path"),
                        mime_type=file.content_type,
                        file_size=process_result["metadata"].get("file_size", 0),
                        width=process_result["metadata"].get("width", 0),
                        height=process_result["metadata"].get("height", 0),
                        processing_status="pending"
                    )
                    
                    db.add(image_asset)
                    db.commit()
                    
                    # 启动后台分析任务
                    background_tasks.add_task(
                        analyze_image_background,
                        image_asset.id,
                        process_result["original_path"]
                    )
                    
                    results.append(ImageUploadResponse(
                        id=image_asset.id,
                        filename=image_asset.filename,
                        status="uploaded",
                        thumbnail_url=image_asset.thumbnail_path
                    ))
                    
                    logger.info(f"图片上传成功: {file.filename}")
                    
                else:
                    results.append(ImageUploadResponse(
                        id="",
                        filename=file.filename or "unknown",
                        status="error",
                        error=process_result.get("error", "处理失败")
                    ))
                    
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")
                results.append(ImageUploadResponse(
                    id="",
                    filename=file.filename or "unknown",
                    status="error",
                    error=str(e)
                ))
        
        success_count = sum(1 for r in results if r.status == "uploaded")
        logger.info(f"图片上传完成: {success_count}/{len(files)} 成功")
        
        return results
        
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/{image_id}", response_model=ImageInfo)
async def get_image_info(image_id: str, db: Session = Depends(get_db)):
    """获取图片详细信息"""
    try:
        image = db.query(ImageAsset).filter(ImageAsset.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return ImageInfo(
            id=image.id,
            filename=image.filename,
            description=image.description,
            thumbnail_url=image.thumbnail_path,
            original_url=image.original_path,
            tags=image.tags,
            color_palette=image.color_palette,
            metadata={
                "width": image.width or 0,
                "height": image.height or 0,
                "file_size": image.file_size or 0,
                "mime_type": image.mime_type
            },
            processing_status=image.processing_status,
            created_at=image.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.get("/project/{project_id}")
async def list_project_images(
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目中的图片列表"""
    try:
        query = db.query(ImageAsset).filter(ImageAsset.project_id == project_id)
        
        if status:
            query = query.filter(ImageAsset.processing_status == status)
        
        total = query.count()
        images = query.offset(skip).limit(limit).all()
        
        image_list = []
        for image in images:
            image_list.append({
                "id": image.id,
                "filename": image.filename,
                "thumbnail_url": image.thumbnail_path,
                "processing_status": image.processing_status,
                "created_at": image.created_at,
                "metadata": {
                    "width": image.width or 0,
                    "height": image.height or 0,
                    "file_size": image.file_size or 0
                }
            })
        
        return {
            "images": image_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"获取图片列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(image_id: str, db: Session = Depends(get_db)):
    """删除图片"""
    try:
        image = db.query(ImageAsset).filter(ImageAsset.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 删除相关的向量数据
        db.query(ImageVector).filter(ImageVector.image_id == image_id).delete()
        
        # 删除文件
        try:
            image_processor.delete_image_files(image.original_path, image.thumbnail_path)
        except Exception as e:
            logger.warning(f"删除文件失败: {e}")
        
        # 删除数据库记录
        db.delete(image)
        db.commit()
        
        logger.info(f"图片删除成功: {image_id}")
        return {"message": "图片删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_images_by_text(
    request: ImageSearchRequest,
    db: Session = Depends(get_db)
):
    """基于文本搜索图片"""
    try:
        search_engine = ImageSearchEngine(db)
        
        results = await search_engine.search_by_text(
            query=request.query,
            project_id=request.project_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        # 转换为字典格式
        search_results = []
        for result in results:
            search_results.append({
                "id": result.id,
                "filename": result.filename,
                "description": result.description,
                "thumbnail_url": result.thumbnail_url,
                "original_url": result.original_url,
                "similarity_score": result.similarity_score,
                "match_reason": result.match_reason,
                "tags": result.tags,
                "color_palette": result.color_palette,
                "metadata": result.metadata
            })
        
        logger.info(f"文本搜索完成: 查询'{request.query}', 找到{len(results)}个结果")
        return search_results
        
    except Exception as e:
        logger.error(f"文本搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/search/similar")
async def search_similar_images(
    image: UploadFile = File(...),
    project_id: str = Form(...),
    limit: int = Form(10),
    similarity_threshold: float = Form(0.5),
    db: Session = Depends(get_db)
):
    """基于图片搜索相似图片"""
    try:
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            search_engine = ImageSearchEngine(db)
            
            results = await search_engine.search_by_image(
                reference_image_path=temp_path,
                project_id=project_id,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # 转换为字典格式
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "filename": result.filename,
                    "description": result.description,
                    "thumbnail_url": result.thumbnail_url,
                    "original_url": result.original_url,
                    "similarity_score": result.similarity_score,
                    "match_reason": result.match_reason,
                    "tags": result.tags,
                    "color_palette": result.color_palette,
                    "metadata": result.metadata
                })
            
            logger.info(f"相似图片搜索完成: 找到{len(results)}个结果")
            return search_results
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"相似图片搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/search/tags")
async def search_images_by_tags(
    request: ImageTagSearchRequest,
    db: Session = Depends(get_db)
):
    """基于标签搜索图片"""
    try:
        search_engine = ImageSearchEngine(db)
        
        results = await search_engine.search_by_tags(
            tags=request.tags,
            project_id=request.project_id,
            match_mode=request.match_mode,
            limit=request.limit
        )
        
        # 转换为字典格式
        search_results = []
        for result in results:
            search_results.append({
                "id": result.id,
                "filename": result.filename,
                "description": result.description,
                "thumbnail_url": result.thumbnail_url,
                "original_url": result.original_url,
                "similarity_score": result.similarity_score,
                "match_reason": result.match_reason,
                "tags": result.tags,
                "color_palette": result.color_palette,
                "metadata": result.metadata
            })
        
        logger.info(f"标签搜索完成: 标签{request.tags}, 找到{len(results)}个结果")
        return search_results
        
    except Exception as e:
        logger.error(f"标签搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/search/color")
async def search_images_by_color(
    request: ImageColorSearchRequest,
    db: Session = Depends(get_db)
):
    """基于颜色搜索图片"""
    try:
        search_engine = ImageSearchEngine(db)
        
        results = await search_engine.search_by_color(
            target_color=request.color,
            project_id=request.project_id,
            tolerance=request.tolerance,
            limit=request.limit
        )
        
        # 转换为字典格式
        search_results = []
        for result in results:
            search_results.append({
                "id": result.id,
                "filename": result.filename,
                "description": result.description,
                "thumbnail_url": result.thumbnail_url,
                "original_url": result.original_url,
                "similarity_score": result.similarity_score,
                "match_reason": result.match_reason,
                "tags": result.tags,
                "color_palette": result.color_palette,
                "metadata": result.metadata
            })
        
        logger.info(f"颜色搜索完成: 颜色{request.color}, 找到{len(results)}个结果")
        return search_results
        
    except Exception as e:
        logger.error(f"颜色搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/file/{image_id}")
async def get_image_file(image_id: str, type: str = "thumbnail", db: Session = Depends(get_db)):
    """获取图片文件"""
    try:
        image = db.query(ImageAsset).filter(ImageAsset.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        if type == "thumbnail" and image.thumbnail_path:
            file_path = image.thumbnail_path
        elif type == "original" and image.original_path:
            file_path = image.original_path
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            media_type=image.mime_type or "image/jpeg",
            filename=image.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.get("/stats/storage")
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        stats = image_processor.get_storage_stats()
        return stats
        
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

# 后台任务
async def analyze_image_background(image_id: str, image_path: str):
    """后台分析图片任务"""
    try:
        logger.info(f"开始后台分析图片: {image_id}")
        
        # 分析图片
        analysis_result = await image_analyzer.analyze_image(image_path)
        
        # 更新数据库
        db = next(get_db())
        try:
            image = db.query(ImageAsset).filter(ImageAsset.id == image_id).first()
            if image:
                image.description = analysis_result.description
                image.tags = analysis_result.tags
                image.color_palette = analysis_result.color_palette
                image.processing_status = "completed"
                image.processing_progress = 100.0
                
                db.commit()
                
                # 保存向量数据
                if analysis_result.clip_vector:
                    clip_vector = ImageVector(
                        image_id=image_id,
                        vector_type="clip",
                        vector_data=json.dumps(analysis_result.clip_vector),
                        content_text="",
                        model_version="ViT-B/32",
                        confidence_score=analysis_result.confidence_score,
                        vector_dimension=len(analysis_result.clip_vector)
                    )
                    db.add(clip_vector)
                
                # 保存描述向量
                if analysis_result.description:
                    # 这里需要将描述向量化，暂时跳过
                    pass
                
                db.commit()
                logger.info(f"图片分析完成: {image_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"后台分析图片失败: {e}")
        
        # 更新错误状态
        db = next(get_db())
        try:
            image = db.query(ImageAsset).filter(ImageAsset.id == image_id).first()
            if image:
                image.processing_status = "failed"
                image.error_message = str(e)
                db.commit()
        finally:
            db.close()