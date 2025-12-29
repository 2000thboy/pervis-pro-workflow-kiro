"""
导出API路由
支持剧本文档、BeatBoard图片、NLE工程和视频导出
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


# ============================================================
# 导出格式查询 API
# ============================================================

@router.get("/formats")
async def get_export_formats():
    """获取支持的导出格式列表"""
    return {
        "status": "success",
        "formats": {
            "script": {
                "name": "剧本文档",
                "formats": [
                    {"value": "docx", "label": "Word文档 (.docx)", "description": "Microsoft Word格式"},
                    {"value": "pdf", "label": "PDF文档 (.pdf)", "description": "便携式文档格式"},
                    {"value": "md", "label": "Markdown (.md)", "description": "纯文本标记格式"}
                ]
            },
            "beatboard": {
                "name": "BeatBoard图片",
                "formats": [
                    {"value": "png", "label": "PNG图片", "description": "无损压缩图片"},
                    {"value": "jpg", "label": "JPEG图片", "description": "有损压缩图片"}
                ]
            },
            "nle": {
                "name": "NLE工程",
                "formats": [
                    {"value": "fcpxml", "label": "Final Cut Pro XML", "description": "兼容FCP/Premiere/DaVinci"},
                    {"value": "edl", "label": "EDL (CMX3600)", "description": "通用剪辑决策列表"}
                ]
            },
            "video": {
                "name": "视频导出",
                "formats": [
                    {"value": "mp4", "label": "MP4 (H.264)", "description": "通用视频格式"},
                    {"value": "mov", "label": "MOV (QuickTime)", "description": "Apple QuickTime格式"},
                    {"value": "webm", "label": "WebM (VP9)", "description": "Web视频格式"}
                ],
                "resolutions": [
                    {"value": "720p", "label": "720p HD", "width": 1280, "height": 720},
                    {"value": "1080p", "label": "1080p Full HD", "width": 1920, "height": 1080},
                    {"value": "2k", "label": "2K QHD", "width": 2560, "height": 1440},
                    {"value": "4k", "label": "4K UHD", "width": 3840, "height": 2160}
                ],
                "framerates": [24, 25, 30, 60],
                "quality_presets": ["low", "medium", "high", "ultra"]
            },
            "audio": {
                "name": "音频导出",
                "formats": [
                    {"value": "mp3", "label": "MP3", "description": "通用音频格式"},
                    {"value": "wav", "label": "WAV", "description": "无损音频格式"}
                ]
            }
        }
    }


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
    format: str  # fcpxml, edl
    frame_rate: str = "24"


class BeatBoardExportRequest(BaseModel):
    project_id: str
    format: str  # png, jpg
    width: int = 1920
    height: int = 1080
    quality: int = 95
    beat_ids: Optional[List[str]] = None


class ContactSheetExportRequest(BaseModel):
    """联系表导出请求"""
    project_id: str
    format: str = "png"
    columns: int = 4
    thumbnail_width: int = 400
    thumbnail_height: int = 225
    quality: int = 95


class StoryboardZipExportRequest(BaseModel):
    """故事板ZIP导出请求"""
    project_id: str
    format: str = "png"
    width: int = 1920
    height: int = 1080
    quality: int = 95
    group_by_scene: bool = True
    include_contact_sheet: bool = True


class TimelineVideoExportRequest(BaseModel):
    """时间线视频导出请求"""
    timeline_id: str
    format: str = "mp4"  # mp4, mov, webm
    resolution: str = "1080p"  # 720p, 1080p, 2k, 4k
    framerate: int = 30  # 24, 25, 30, 60
    quality: str = "high"  # low, medium, high, ultra
    bitrate: Optional[int] = None
    audio_bitrate: int = 192


class TimelineAudioExportRequest(BaseModel):
    """时间线音频导出请求"""
    timeline_id: str
    format: str = "mp3"  # wav, mp3
    sample_rate: int = 44100
    bitrate: int = 192


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


@router.post("/contact-sheet")
async def export_contact_sheet(request: ContactSheetExportRequest, db: Session = Depends(get_db)):
    """导出联系表（Contact Sheet）"""
    exporter = ImageExporter(db)
    
    result = await exporter.export_contact_sheet(
        project_id=request.project_id,
        format=request.format,
        columns=request.columns,
        thumbnail_width=request.thumbnail_width,
        thumbnail_height=request.thumbnail_height,
        quality=request.quality
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/storyboard-zip")
async def export_storyboard_zip(request: StoryboardZipExportRequest, db: Session = Depends(get_db)):
    """导出故事板为ZIP包（按场次分组）"""
    exporter = ImageExporter(db)
    
    result = await exporter.export_storyboard_zip(
        project_id=request.project_id,
        format=request.format,
        width=request.width,
        height=request.height,
        quality=request.quality,
        group_by_scene=request.group_by_scene,
        include_contact_sheet=request.include_contact_sheet
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


# ============================================================
# NLE 工程导出 API
# ============================================================

@router.post("/nle")
async def export_nle_project(request: NLEExportRequest, db: Session = Depends(get_db)):
    """
    导出 NLE 工程文件
    
    支持格式：
    - fcpxml: Final Cut Pro XML (兼容 Premiere Pro, DaVinci Resolve)
    - edl: CMX3600 EDL (通用格式)
    """
    exporter = NLEExporter(db)
    
    if request.format.lower() == "fcpxml":
        result = await exporter.export_fcpxml(
            project_id=request.project_id,
            frame_rate=request.frame_rate
        )
    elif request.format.lower() == "edl":
        result = await exporter.export_edl_cmx3600(
            project_id=request.project_id,
            frame_rate=int(request.frame_rate)
        )
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的格式: {request.format}，支持: fcpxml, edl"
        )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


# ============================================================
# 时间线视频导出 API
# ============================================================

@router.post("/timeline/video")
async def export_timeline_video(request: TimelineVideoExportRequest, db: Session = Depends(get_db)):
    """
    导出时间线视频
    
    支持格式：mp4, mov, webm, prores
    支持分辨率：720p, 1080p, 2k, 4k
    支持帧率：23.976, 24, 25, 29.97, 30, 50, 60
    支持质量：low, medium, high, ultra
    """
    # 优先使用增强版渲染服务
    try:
        from services.render_service_enhanced import (
            get_enhanced_render_service, 
            RenderOptions, 
            VideoFormat, 
            Resolution, 
            Quality
        )
        
        render_service = get_enhanced_render_service(db)
        
        # 构建渲染选项
        options = RenderOptions(
            format=VideoFormat(request.format) if request.format in [f.value for f in VideoFormat] else VideoFormat.MP4,
            resolution=Resolution(request.resolution) if request.resolution in [r.value for r in Resolution] else Resolution.FHD_1080,
            framerate=float(request.framerate),
            quality=Quality(request.quality) if request.quality in [q.value for q in Quality] else Quality.HIGH,
            custom_bitrate=request.bitrate,
            audio_bitrate=request.audio_bitrate
        )
        
        # 检查渲染条件
        check_result = await render_service.check_render_requirements(request.timeline_id, options)
        if not check_result.get("can_render"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "无法渲染",
                    "errors": check_result.get("errors", [])
                }
            )
        
        # 启动渲染任务
        task_id = await render_service.start_render(request.timeline_id, options)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "渲染任务已启动",
            "estimated_render_time": check_result.get("estimated_render_time"),
            "estimated_size_mb": check_result.get("estimated_size_mb"),
            "resolution": check_result.get("resolution"),
            "format": check_result.get("format")
        }
        
    except ImportError:
        # 回退到原版渲染服务
        from services.render_service import RenderService
        
        render_service = RenderService(db)
        
        check_result = await render_service.check_render_requirements(request.timeline_id)
        if not check_result.get("can_render"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "无法渲染",
                    "errors": check_result.get("errors", [])
                }
            )
        
        task_id = await render_service.start_render(
            timeline_id=request.timeline_id,
            format=request.format,
            resolution=request.resolution,
            framerate=request.framerate,
            quality=request.quality,
            bitrate=request.bitrate,
            audio_bitrate=request.audio_bitrate
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "渲染任务已启动",
            "estimated_duration": check_result.get("estimated_duration"),
            "estimated_size_mb": check_result.get("estimated_size_mb")
        }


@router.get("/timeline/video/status/{task_id}")
async def get_video_export_status(task_id: str, db: Session = Depends(get_db)):
    """获取视频导出任务状态"""
    from services.render_service import RenderService
    
    render_service = RenderService(db)
    status = await render_service.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "status": "success",
        "task": status
    }


@router.post("/timeline/video/cancel/{task_id}")
async def cancel_video_export(task_id: str, db: Session = Depends(get_db)):
    """取消视频导出任务"""
    from services.render_service import RenderService
    
    render_service = RenderService(db)
    success = await render_service.cancel_render(task_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="取消任务失败")
    
    return {
        "status": "success",
        "message": "任务已取消"
    }


@router.get("/timeline/video/download/{task_id}")
async def download_video_export(task_id: str, db: Session = Depends(get_db)):
    """下载导出的视频文件"""
    from services.render_service import RenderService
    from pathlib import Path
    
    render_service = RenderService(db)
    file_path = render_service.get_download_path(task_id)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在或任务未完成")
    
    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="video/mp4"
    )


@router.get("/timeline/video/tasks")
async def list_video_export_tasks(limit: int = 50, status: Optional[str] = None, db: Session = Depends(get_db)):
    """列出视频导出任务"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        tasks = await render_service.list_tasks(limit=limit, status_filter=status)
    except ImportError:
        from services.render_service import RenderService
        render_service = RenderService(db)
        tasks = await render_service.list_tasks(limit=limit)
    
    return {
        "status": "success",
        "tasks": tasks,
        "total": len(tasks)
    }


@router.get("/timeline/video/config")
async def get_video_export_config(db: Session = Depends(get_db)):
    """获取视频导出配置选项"""
    try:
        from services.render_service_enhanced import get_enhanced_render_service
        render_service = get_enhanced_render_service(db)
        
        return {
            "status": "success",
            "formats": render_service.get_supported_formats(),
            "resolutions": render_service.get_supported_resolutions(),
            "framerates": render_service.get_supported_framerates(),
            "quality_presets": render_service.get_quality_presets()
        }
    except ImportError:
        # 回退到基础配置
        return {
            "status": "success",
            "formats": [
                {"value": "mp4", "label": "MP4"},
                {"value": "mov", "label": "MOV"},
                {"value": "webm", "label": "WebM"}
            ],
            "resolutions": [
                {"value": "720p", "label": "720p HD", "width": 1280, "height": 720},
                {"value": "1080p", "label": "1080p Full HD", "width": 1920, "height": 1080},
                {"value": "2k", "label": "2K QHD", "width": 2560, "height": 1440},
                {"value": "4k", "label": "4K UHD", "width": 3840, "height": 2160}
            ],
            "framerates": [24, 25, 30, 60],
            "quality_presets": [
                {"value": "low", "label": "Low", "bitrate": "1000k"},
                {"value": "medium", "label": "Medium", "bitrate": "3000k"},
                {"value": "high", "label": "High", "bitrate": "8000k"},
                {"value": "ultra", "label": "Ultra", "bitrate": "15000k"}
            ]
        }


# ============================================================
# 时间线音频导出 API
# ============================================================

@router.post("/timeline/audio")
async def export_timeline_audio(request: TimelineAudioExportRequest, db: Session = Depends(get_db)):
    """
    导出时间线音频
    
    支持格式：wav, mp3
    """
    from services.audio_exporter import AudioExporter, AudioExportOptions, AudioFormat
    
    exporter = AudioExporter(db)
    
    # 构建导出选项
    options = AudioExportOptions(
        format=AudioFormat(request.format) if request.format in [f.value for f in AudioFormat] else AudioFormat.MP3,
        sample_rate=request.sample_rate,
        bitrate=request.bitrate
    )
    
    result = await exporter.export_timeline_audio(request.timeline_id, options)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result
