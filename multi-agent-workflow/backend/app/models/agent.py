"""
Agent数据模型
"""
from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, JSON
from datetime import datetime
from .base import BaseModel

# 从core导入枚举，避免重复定义
from ..core.agent_types import AgentState, AgentType


class Agent(BaseModel):
    """Agent模型"""
    __tablename__ = "agents"
    
    agent_id = Column(String(50), unique=True, nullable=False, index=True)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    state = Column(SQLEnum(AgentState), default=AgentState.IDLE, nullable=False)
    current_task = Column(String(255))
    last_activity = Column(DateTime, default=datetime.utcnow)
    capabilities = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<Agent(agent_id={self.agent_id}, type={self.agent_type}, state={self.state})>"