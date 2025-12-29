"""
BackgroundTask 数据模型

存储后台任务信息，包括导出、渲染、AI生成等任务。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BackgroundTask(Base):
    """后台任务模型"""
    __tablename__ = "background_tasks"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 任务类型: export, render, ai_generate, asset_process
    type = Column(String(30), nullable=False, index=True)
    
    # 任务名称
    name = Column(String(200), nullable=False)
    
    # 进度 (0-100)
    progress = Column(Integer, default=0)
    
    # 状态: pending, running, completed, failed, cancelled
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    # 详情 (JSON) - 存储任务特定的数据
    details = Column(JSON, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 预计耗时（秒）
    estimated_duration = Column(Integer, nullable=True)
    
    # 关联项目
    project_id = Column(String(36), nullable=True, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "progress": self.progress,
            "status": self.status,
            "details": self.details,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_duration": self.estimated_duration,
            "project_id": self.project_id
        }
    
    @classmethod
    def create(
        cls,
        id: str,
        type: str,
        name: str,
        project_id: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "BackgroundTask":
        """创建任务实例"""
        return cls(
            id=id,
            type=type,
            name=name,
            project_id=project_id,
            estimated_duration=estimated_duration,
            details=details,
            status="pending"
        )
    
    def start(self) -> None:
        """开始任务"""
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def update_progress(self, progress: int) -> None:
        """更新进度"""
        self.progress = min(100, max(0, progress))
    
    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """完成任务"""
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.utcnow()
        if result:
            self.details = {**(self.details or {}), "result": result}
    
    def fail(self, error_message: str) -> None:
        """任务失败"""
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
