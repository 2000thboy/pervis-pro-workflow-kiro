# -*- coding: utf-8 -*-
"""
导出历史清理服务
定时清理超过 7 天的导出文件
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ExportCleanupService:
    """导出文件清理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dirs = [
            Path("exports"),
            Path("storage/exports"),
            Path("storage/renders"),
        ]
        self.retention_days = 7  # 保留天数
    
    async def cleanup_old_exports(self) -> Dict[str, Any]:
        """
        清理超过保留期的导出文件
        
        Returns:
            清理结果统计
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_files = 0
        deleted_records = 0
        freed_space = 0
        errors = []
        
        try:
            # 1. 清理数据库中的过期记录
            old_exports = self.db.execute(
                text("""
                    SELECT id, file_path, file_size 
                    FROM export_history 
                    WHERE created_at < :cutoff_date
                """),
                {"cutoff_date": cutoff_date}
            ).fetchall()
            
            for export in old_exports:
                export_id = export[0]
                file_path = export[1]
                file_size = export[2] or 0
                
                # 删除文件
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                        freed_space += file_size
                        logger.info(f"已删除导出文件: {file_path}")
                    except Exception as e:
                        errors.append(f"删除文件失败 {file_path}: {e}")
                
                # 更新数据库记录状态
                self.db.execute(
                    text("""
                        UPDATE export_history 
                        SET status = 'expired', file_path = NULL 
                        WHERE id = :id
                    """),
                    {"id": export_id}
                )
                deleted_records += 1
            
            self.db.commit()
            
            # 2. 清理渲染任务的过期文件
            old_renders = self.db.execute(
                text("""
                    SELECT id, output_path, file_size 
                    FROM render_tasks 
                    WHERE created_at < :cutoff_date AND status = 'completed'
                """),
                {"cutoff_date": cutoff_date}
            ).fetchall()
            
            for render in old_renders:
                render_id = render[0]
                output_path = render[1]
                file_size = render[2] or 0
                
                if output_path and os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                        deleted_files += 1
                        freed_space += file_size
                        logger.info(f"已删除渲染文件: {output_path}")
                    except Exception as e:
                        errors.append(f"删除渲染文件失败 {output_path}: {e}")
                
                # 更新状态
                self.db.execute(
                    text("""
                        UPDATE render_tasks 
                        SET status = 'expired', output_path = NULL 
                        WHERE id = :id
                    """),
                    {"id": render_id}
                )
            
            self.db.commit()
            
            # 3. 清理孤立文件（数据库中没有记录的文件）
            for export_dir in self.export_dirs:
                if not export_dir.exists():
                    continue
                
                for file_path in export_dir.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    # 检查文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        # 检查是否在数据库中有记录
                        record = self.db.execute(
                            text("""
                                SELECT id FROM export_history WHERE file_path = :path
                                UNION
                                SELECT id FROM render_tasks WHERE output_path = :path
                            """),
                            {"path": str(file_path)}
                        ).fetchone()
                        
                        if not record:
                            # 孤立文件，删除
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                deleted_files += 1
                                freed_space += file_size
                                logger.info(f"已删除孤立文件: {file_path}")
                            except Exception as e:
                                errors.append(f"删除孤立文件失败 {file_path}: {e}")
            
            result = {
                "status": "success",
                "deleted_files": deleted_files,
                "deleted_records": deleted_records,
                "freed_space_mb": round(freed_space / 1024 / 1024, 2),
                "errors": errors,
                "retention_days": self.retention_days,
                "cutoff_date": cutoff_date.isoformat()
            }
            
            logger.info(f"导出清理完成: 删除 {deleted_files} 个文件, 释放 {result['freed_space_mb']} MB")
            return result
            
        except Exception as e:
            logger.error(f"导出清理失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "deleted_files": deleted_files,
                "deleted_records": deleted_records,
                "freed_space_mb": round(freed_space / 1024 / 1024, 2),
                "errors": errors
            }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        total_size = 0
        file_count = 0
        
        for export_dir in self.export_dirs:
            if not export_dir.exists():
                continue
            
            for file_path in export_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        # 获取数据库记录数
        export_count = self.db.execute(
            text("SELECT COUNT(*) FROM export_history")
        ).scalar() or 0
        
        render_count = self.db.execute(
            text("SELECT COUNT(*) FROM render_tasks")
        ).scalar() or 0
        
        return {
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "file_count": file_count,
            "export_records": export_count,
            "render_records": render_count,
            "retention_days": self.retention_days
        }


# 后台清理任务
_cleanup_task = None


async def start_cleanup_scheduler(db_factory):
    """启动定时清理任务"""
    global _cleanup_task
    
    async def cleanup_loop():
        while True:
            try:
                # 每天凌晨 3 点执行清理
                now = datetime.now()
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次清理任务将在 {next_run} 执行")
                
                await asyncio.sleep(wait_seconds)
                
                # 执行清理
                db = db_factory()
                try:
                    service = ExportCleanupService(db)
                    result = await service.cleanup_old_exports()
                    logger.info(f"定时清理完成: {result}")
                finally:
                    db.close()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务异常: {e}")
                await asyncio.sleep(3600)  # 出错后等待 1 小时重试
    
    _cleanup_task = asyncio.create_task(cleanup_loop())
    return _cleanup_task


def stop_cleanup_scheduler():
    """停止定时清理任务"""
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        _cleanup_task = None
