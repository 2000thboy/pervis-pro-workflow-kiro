"""
工作流数据模型
"""
from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from datetime import datetime
from .base import BaseModel


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowType(Enum):
    """工作流类型枚举"""
    PROJECT_SETUP = "project_setup"
    BEATBOARD = "beatboard"
    PREVIEW_EDIT = "preview_edit"


class WorkflowInstance(BaseModel):
    """工作流实例模型"""
    __tablename__ = "workflow_instances"
    
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)
    workflow_type = Column(SQLEnum(WorkflowType), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False)
    current_step = Column(String(100))
    steps_completed = Column(JSON, default=list)
    context = Column(JSON, default=dict)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # 关系
    project = relationship("Project", backref="workflows")
    
    def __repr__(self):
        return f"<WorkflowInstance(workflow_id={self.workflow_id}, type={self.workflow_type}, status={self.status})>"