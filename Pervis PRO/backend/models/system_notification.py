"""
SystemNotification 数据模型

存储系统通知，包括任务通知、警告、错误等。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SystemNotification(Base):
    """系统通知模型"""
    __tablename__ = "system_notifications"
    
    # 主键
    id = Column(String(36), primary_key=True)
    
    # 通知类型: task, warning, error, info
    type = Column(String(20), nullable=False, index=True)
    
    # 通知级别: critical, warning, info
    level = Column(String(20), nullable=False, default="info", index=True)
    
    # 通知内容
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # 操作建议 (JSON)
    # 格式: {"type": "button|link|manual", "label": "...", "action": "...", "url": "...", "instructions": "..."}
    action = Column(JSON, nullable=True)
    
    # 状态
    is_read = Column(Boolean, default=False, index=True)
    
    # 关联信息
    task_id = Column(String(36), nullable=True, index=True)
    agent_type = Column(String(50), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type,
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "action": self.action,
            "is_read": self.is_read,
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def create(
        cls,
        id: str,
        type: str,
        level: str,
        title: str,
        message: str,
        action: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> "SystemNotification":
        """创建通知实例"""
        return cls(
            id=id,
            type=type,
            level=level,
            title=title,
            message=message,
            action=action,
            task_id=task_id,
            agent_type=agent_type
        )
