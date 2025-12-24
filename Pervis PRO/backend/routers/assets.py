"""
素材管理路由
Phase 2: 集成AssetProcessor服务进行真实文件处理
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from services.asset_processor import AssetProcessor
from models.base import AssetUploadResponse, AssetStatusResponse, AssetSegment, ProcessingStatus
import asyncio
from typing import List, Optional

router = APIRouter()

@router.post("/upload", response_model=AssetUploadResponse)
async def upload_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: str = "default_project",  # Phase 2: 使用默认项目
    db: Session = Depends(get_db)
):
    """
    素材上传接口
    Phase 2: 真实文件处理，异步后台任务
    """
    
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 检查文件大小 (限制100MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过100MB")
    
    # 创建AssetProcessor实例
    asset_processor = AssetProcessor(db)
    
    # 启动后台处理任务
    background_tasks.add_task(
        asset_processor.process_uploaded_file,
        file,
        project_id
    )
    
    # 立即返回上传确认
    return AssetUploadResponse(
        asset_id="processing",  # 临时ID，实际ID在后台生成
        status=ProcessingStatus.UPLOADED,
        estimated_processing_time=180  # 3分钟预估
    )

@router.get("/{asset_id}/status", response_model=AssetStatusResponse)
async def get_asset_status(asset_id: str, db: Session = Depends(get_db)):
    """
    查询素材处理状态
    Phase 2: 从数据库获取真实处理状态
    """
    
    asset_processor = AssetProcessor(db)
    
    try:
        status_data = asset_processor.get_asset_status(asset_id)
        
        if status_data["status"] == "error":
            return AssetStatusResponse(
                status=ProcessingStatus.ERROR,
                progress=0,
                error_message=status_data.get("message", "处理失败")
            )
        
        # 转换segments格式
        segments = []
        for seg in status_data.get("segments", []):
            segments.append(AssetSegment(
                id=seg["id"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                description=seg["description"],
                tags=seg["tags"]
            ))
        
        # 映射处理状态
        status_mapping = {
            "uploaded": ProcessingStatus.UPLOADED,
            "processing": ProcessingStatus.PROCESSING,
            "completed": ProcessingStatus.COMPLETED,
            "error": ProcessingStatus.ERROR
        }
        
        return AssetStatusResponse(
            status=status_mapping.get(status_data["status"], ProcessingStatus.ERROR),
            progress=status_data.get("progress", 0),
            proxy_url=status_data.get("proxy_url"),
            thumbnail_url=status_data.get("thumbnail_url"),
            segments=segments
        )
        
    except Exception as e:
        return AssetStatusResponse(
            status=ProcessingStatus.ERROR,
            progress=0,
            error_message=f"查询状态失败: {str(e)}"
        )

@router.get("/list")
async def list_assets(
    project_id: Optional[str] = Query(None, description="项目ID"),
    limit: int = Query(20, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取素材列表 - 前端集成修复
    重定向到现有的search端点
    """
    try:
        return await search_assets(query=None, limit=limit, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取素材列表失败: {str(e)}")


@router.get("/search")
async def search_assets(
    query: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(10, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    搜索素材
    简单的素材列表和搜索功能
    """
    try:
        # 构建SQL查询
        if query:
            # 有搜索关键词时进行模糊搜索
            sql = text("""
                SELECT id, filename, mime_type, file_path, thumbnail_path, 
                       processing_status, tags, created_at
                FROM assets 
                WHERE filename LIKE :query OR tags LIKE :query
                ORDER BY created_at DESC 
                LIMIT :limit
            """)
            result = db.execute(sql, {"query": f"%{query}%", "limit": limit})
        else:
            # 无搜索关键词时返回所有素材
            sql = text("""
                SELECT id, filename, mime_type, file_path, thumbnail_path,
                       processing_status, tags, created_at
                FROM assets 
                ORDER BY created_at DESC 
                LIMIT :limit
            """)
            result = db.execute(sql, {"limit": limit})
        
        assets = []
        for row in result:
            # 模拟duration字段（从文件名或标签中提取）
            duration = 5.0  # 默认5秒
            if "conversation" in row[1].lower():
                duration = 12.0
            elif "street" in row[1].lower():
                duration = 8.0
            elif "close" in row[1].lower():
                duration = 4.0
            elif "office" in row[1].lower():
                duration = 6.0
            
            asset = {
                "id": row[0],
                "filename": row[1],
                "mime_type": row[2] or "video/mp4",
                "file_path": row[3],
                "thumbnail_path": row[4],
                "processing_status": row[5] or "completed",
                "tags": row[6] or "[]",
                "created_at": row[7],
                "duration": duration  # 添加duration字段
            }
            assets.append(asset)
        
        return assets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{asset_id}")
async def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """获取单个素材详情"""
    try:
        result = db.execute(
            text("SELECT * FROM assets WHERE id = :asset_id"),
            {"asset_id": asset_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="素材不存在")
        
        return {
            "id": result[0],
            "filename": result[2],
            "mime_type": result[3],
            "file_path": result[5],
            "thumbnail_path": result[6],
            "processing_status": result[7],
            "tags": result[9] or "[]",
            "created_at": result[12]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取素材失败: {str(e)}")