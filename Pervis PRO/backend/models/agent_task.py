# -*- coding: utf-8 -*-
"""
Agent 任务模型

Phase 3: 后端数据模型
Task 3.3: AgentTask 模型

记录 Agent 任务状态、进度和错误信息
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

# 导入数据库基类
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


# ============================================================================
# 枚举类型
# ============================================================================

class AgentType(str, Enum):
    """Agent 类型"""
    SCRIPT_AGENT = "script_agent"
    ART_AGENT = "art_agent"
    DIRECTOR_AGENT = "director_agent"
    PM_AGENT = "pm_agent"
    STORYBOARD_AGENT = "storyboard_agent"
    MARKET_AGENT = "market_agent"
    SYSTEM_AGENT = "system_agent"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"         # 等待执行
    WORKING = "working"         # 执行中
    REVIEWING = "reviewing"     # 审核中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消
    RETRYING = "retrying"       # 重试中


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# SQLAlchemy 模型
# ============================================================================

class AgentTask(Base):
    """Agent 任务表"""
    __tablename__ = "agent_tasks"
    
    id = Column(String, primary_key=True)
    
    # 关联信息
    project_id = Column(String, nullable=True)
    draft_id = Column(String, nullable=True)
    parent_task_id = Column(String, nullable=True)  # 父任务（用于任务链）
    
    # Agent 信息
    agent_type = Column(String(50), nullable=False)
    task_type = Column(String(100), nullable=False)  # parse_script, generate_logline, review, etc.
    
    # 任务状态
    status = Column(String(50), default=TaskStatus.PENDING.value)
    priority = Column(String(20), default=TaskPriority.NORMAL.value)
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    
    # 输入输出
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    
    # 错误信息
    error_message = Column(Text)
    error_details = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 执行信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # 审核信息（Director_Agent 审核结果）
    review_status = Column(String(50))  # approved, suggestions, rejected
    review_result = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


class AgentTaskLog(Base):
    """Agent 任务日志表"""
    __tablename__ = "agent_task_logs"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False)
    
    # 日志信息
    log_level = Column(String(20), default="info")  # debug, info, warning, error
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Pydantic 模型（API 请求/响应）
# ============================================================================

class TaskCreate(BaseModel):
    """创建任务请求"""
    project_id: Optional[str] = None
    draft_id: Optional[str] = None
    agent_type: AgentType
    task_type: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL


class TaskUpdate(BaseModel):
    """更新任务请求"""
    status: Optional[TaskStatus] = None
    progress: Optional[float] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    project_id: Optional[str] = None
    draft_id: Optional[str] = None
    agent_type: AgentType
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    progress: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    review_status: Optional[str] = None
    review_result: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态响应（简化版）"""
    task_id: str
    status: TaskStatus
    progress: float
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int
    pending_count: int
    working_count: int
    completed_count: int
    failed_count: int


class TaskLogEntry(BaseModel):
    """任务日志条目"""
    id: str
    task_id: str
    log_level: str
    message: str
    details: Dict[str, Any]
    timestamp: str


class TaskRetryRequest(BaseModel):
    """重试任务请求"""
    task_id: str
    reset_input: bool = False
    new_input_data: Optional[Dict[str, Any]] = None


# ============================================================================
# 辅助函数
# ============================================================================

def get_agent_display_name(agent_type: AgentType) -> str:
    """获取 Agent 显示名称"""
    names = {
        AgentType.SCRIPT_AGENT: "编剧 Agent",
        AgentType.ART_AGENT: "美术 Agent",
        AgentType.DIRECTOR_AGENT: "导演 Agent",
        AgentType.PM_AGENT: "项目助理",
        AgentType.STORYBOARD_AGENT: "故事板 Agent",
        AgentType.MARKET_AGENT: "市场 Agent",
        AgentType.SYSTEM_AGENT: "系统 Agent"
    }
    return names.get(agent_type, str(agent_type))


def get_status_message(status: TaskStatus, agent_type: AgentType) -> str:
    """获取状态消息"""
    agent_name = get_agent_display_name(agent_type)
    
    messages = {
        TaskStatus.PENDING: f"{agent_name} 等待执行...",
        TaskStatus.WORKING: f"{agent_name} 正在工作...",
        TaskStatus.REVIEWING: f"导演 Agent 审核中...",
        TaskStatus.COMPLETED: f"{agent_name} 完成",
        TaskStatus.FAILED: f"{agent_name} 执行失败",
        TaskStatus.CANCELLED: f"{agent_name} 已取消",
        TaskStatus.RETRYING: f"{agent_name} 重试中..."
    }
    return messages.get(status, str(status))


def calculate_task_duration(started_at: datetime, completed_at: datetime) -> float:
    """计算任务耗时（秒）"""
    if started_at and completed_at:
        return (completed_at - started_at).total_seconds()
    return 0.0
