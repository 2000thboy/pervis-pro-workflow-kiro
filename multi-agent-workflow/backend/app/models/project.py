"""
项目数据模型
"""
from sqlalchemy import Column, String, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from .base import BaseModel


class ProjectStatus(Enum):
    """项目状态枚举"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    BEATBOARD_READY = "beatboard_ready"
    PREVIEW_READY = "preview_ready"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(BaseModel):
    """项目模型"""
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    aspect_ratio = Column(String(10), nullable=False)  # "16:9", "4:3", "1:1"
    duration = Column(Integer, nullable=False)  # 秒
    story_summary = Column(Text)
    story_content = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CREATED, nullable=False)
    
    def __repr__(self):
        return f"<Project(name={self.name}, status={self.status})>"