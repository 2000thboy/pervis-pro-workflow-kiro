"""
导出API路由
支持剧本文档和BeatBoard图片导出
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from services.document_exporter import DocumentExporter
from services.image_exporter import ImageExporter
from services.nle_exporter import NLEExporter

router = APIRouter()


# 请求模型
class ScriptExportRequest(BaseModel):
    project_id: str
    format: str  # docx, pdf, md
    include_beats: bool = True
    include_tags: bool = True
    include_metadata: bool = True
    template: Optional[str] = "professional"

class NLEExportRequest(BaseModel):
    project_id: str
    format: str # xml, edl
    frame_rate: str = "24"


class BeatBoardExportRequest(BaseModel):
    project_id: str
    format: str  # png, jpg
    width: int = 1920
    height: int = 1080
    quality: int = 95
    beat_ids: Optional[List[str]] = None


# API端点
@router.post("/script")
async def export_script(request: ScriptExportRequest, db: Session = Depends(get_db)):
    """导出剧本文档"""
    exporter = DocumentExporter(db)
    
    if request.format.lower() == "docx":
        result = await exporter.export_script_docx(
            project_id=request.project_id,
            include_beats=request.include_beats,
            include_tags=request.include_tags,
            include_metadata=request.include_metadata
        )
    elif request.format.lower() == "pdf":
        result = await exporter.export_script_pdf(
            project_id=request.project_id,
            template=request.template,
            include_beats=request.include_beats,
            include_tags=request.include_tags
        )
    elif request.format.lower() == "md":
        result = await exporter.export_script_markdown(
            project_id=request.project_id,
            include_beats=request.include_beats,
            include_tags=request.include_tags
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {request.format}")
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/beatboard")
async def export_beatboard(request: BeatBoardExportRequest, db: Session = Depends(get_db)):
    """导出BeatBoard图片"""
    exporter = ImageExporter(db)
    
    result = await exporter.export_beatboard_image(
        project_id=request.project_id,
        format=request.format,
        width=request.width,
        height=request.height,
        quality=request.quality,
        beat_ids=request.beat_ids
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.get("/download/{export_id}")
async def download_export(export_id: str, db: Session = Depends(get_db)):
    """下载导出的文件"""
    from database import ExportHistory
    
    export_record = db.query(ExportHistory).filter(ExportHistory.id == export_id).first()
    
    if not export_record:
        raise HTTPException(status_code=404, detail="导出记录不存在")
    
    from pathlib import Path
    file_path = Path(export_record.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.get("/history/{project_id}")
async def get_export_history(project_id: str, db: Session = Depends(get_db)):
    """获取项目的导出历史"""
    from database import ExportHistory
    
    history = db.query(ExportHistory).filter(
        ExportHistory.project_id == project_id
    ).order_by(ExportHistory.created_at.desc()).all()
    
    return {
        "status": "success",
        "project_id": project_id,
        "history": [
            {
                "id": h.id,
                "export_type": h.export_type,
                "file_format": h.file_format,
                "file_size": h.file_size,
                "status": h.status,
                "created_at": h.created_at
            }
            for h in history
        ]
    }
