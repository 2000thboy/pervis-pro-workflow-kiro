"""
存储管理路由
负责扫描外部路径(NAS/本地磁盘)并索引素材
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from database import get_db, Asset
from models.base import ProcessingStatus
import os
from pathlib import Path
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

class ScanRequest(BaseModel):
    path: str
    recursive: bool = True

class ScanResponse(BaseModel):
    message: str
    scanned_count: int
    new_assets: int
    errors: List[str]

SUPPORTED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.jpg', '.png'}

async def scan_directory_task(path: str, recursive: bool, db: Session):
    """后台任务：扫描目录并入库"""
    logger.info(f"开始扫描目录: {path}")
    new_count = 0
    scanned_count = 0
    
    try:
        # 规范化路径
        base_path = Path(path).resolve()
        if not base_path.exists():
            logger.error(f"路径不存在: {path}")
            return
            
        # 遍历生成器
        iterator = base_path.rglob("*") if recursive else base_path.glob("*")
        
        for file_path in iterator:
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                scanned_count += 1
                
                try:
                    # 检查是否已存在 (通过绝对路径)
                    # 注意：这里可能性能一般，生产环境应优化为批量查询或BloomFilter
                    exists = db.query(Asset).filter(Asset.file_path == str(file_path)).first()
                    
                    if not exists:
                        # 创建新资产记录
                        file_stat = file_path.stat()
                        
                        # 简单推断类型
                        mime_type = "application/octet-stream"
                        if file_path.suffix.lower() in {'.mp4', '.mov', '.avi', '.mkv'}:
                            mime_type = "video/mp4" # 简化
                        elif file_path.suffix.lower() in {'.jpg', '.png'}:
                            mime_type = "image/jpeg"
                            
                        new_asset = Asset(
                            id=str(uuid.uuid4()),
                            project_id="default_project",
                            filename=file_path.name,
                            file_path=str(file_path),
                            mime_type=mime_type,
                            file_size=file_stat.st_size,
                            processing_status=ProcessingStatus.COMPLETED, # 外部素材默认为完成
                            # 对于外部素材，我们暂时没有缩略图，后续可以是另一个任务生成
                            thumbnail_path=None, 
                            created_at=datetime.fromtimestamp(file_stat.st_ctime),
                            updated_at=datetime.now()
                        )
                        db.add(new_asset)
                        new_count += 1
                        
                        # 每100个提交一次，避免事务过大
                        if new_count % 100 == 0:
                            db.commit()
                            
                except Exception as e:
                    logger.error(f"处理文件出错 {file_path}: {e}")
                    continue
                    
        db.commit()
        logger.info(f"扫描完成: {path}. 扫描: {scanned_count}, 新增: {new_count}")
        
    except Exception as e:
        logger.error(f"扫描任务失败: {e}")
    finally:
        db.close() # 确保后台任务关闭Session

@router.post("/scan", response_model=ScanResponse)
async def scan_storage(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    扫描指定路径并索引素材
    """
    if not os.path.exists(request.path):
        raise HTTPException(status_code=400, detail=f"路径不存在: {request.path}")
    
    # 立即返回，任务后台执行
    # 注意：为了要在后台任务中使用db，我们需要创建一个新的Session或者小心处理生命周期
    # Fastapi的Depends(get_db)产生的session在请求结束时会关闭。
    # 对于后台任务，我们最好手动创建session，或者确保session在任务结束前不关闭。
    # 这里为了简单，我们传递当前的db，但在生产中这可能导致 "Session check out is not active" 错误。
    # 更稳妥的做法是让后台任务自己创建 SessionLocal()。
    
    # 修正：不传递 request db，让任务自己管理连接，或者使用简单的同步处理（如果文件少）。
    # 考虑到 "Index-in-Place" 可能涉及大量文件，还是需要后台。
    
    # 由于我们不能在这里直接传 db (它会被关闭)，我们暂时用简单的同步方式测试，
    # 或者我们接受这个限制：演示环境文件不多。
    # 为了稳健，我们这里稍微简化，假设用户不会一次扫描 10万个文件。
    # 改为同步扫描一部分? 不，还是后台好。
    # 我们将在 task 内部创建 Session。
    
    from database import SessionLocal
    def run_scan_safe(path, recursive):
        bg_db = SessionLocal()
        try:
            # 这是一个同步包装器，去调用异步代码有点麻烦，直接写同步逻辑
            # 把 async scan_directory_task 改为同步逻辑即可 (SQLAlchemy 也是同步的)
            import asyncio
            # Running async function in thread...
            # 其实 scan_directory_task 本身没有 await，是同步代码。去掉 async 关键字。
            scan_directory_task_sync(path, recursive, bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(run_scan_safe, request.path, request.recursive)

    return ScanResponse(
        message="扫描任务已启动",
        scanned_count=0,
        new_assets=0,
        errors=[]
    )

def scan_directory_task_sync(path: str, recursive: bool, db: Session):
    """同步版本的扫描逻辑"""
    # 逻辑同上，只是去掉了 async
    logger.info(f"开始后台扫描: {path}")
    new_count = 0
    scanned_count = 0
    try:
        base_path = Path(path).resolve()
        iterator = base_path.rglob("*") if recursive else base_path.glob("*")
        for file_path in iterator:
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                scanned_count += 1
                try:
                    exists = db.query(Asset).filter(Asset.file_path == str(file_path)).first()
                    if not exists:
                        file_stat = file_path.stat()
                        mime_type = "video/mp4" # Simplified
                        if file_path.suffix.lower() in {'.jpg', '.png'}: mime_type = "image/jpeg"
                        
                        new_asset = Asset(
                            id=str(uuid.uuid4()),
                            project_id="default_project",
                            filename=file_path.name,
                            file_path=str(file_path),
                            mime_type=mime_type,
                            file_size=file_stat.st_size,
                            processing_status=ProcessingStatus.COMPLETED,
                            thumbnail_path=None,
                            created_at=datetime.fromtimestamp(file_stat.st_ctime),
                            updated_at=datetime.now()
                        )
                        db.add(new_asset)
                        new_count += 1
                        if new_count % 50 == 0: db.commit()
                except Exception as e:
                    logger.error(f"File error: {e}")
        db.commit()
    except Exception as e:
        logger.error(f"Scan error: {e}")
