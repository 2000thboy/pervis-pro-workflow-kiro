# -*- coding: utf-8 -*-
"""
项目立项向导草稿模型

Phase 3: 后端数据模型
Task 3.1: ProjectWizardDraft 模型

保存用户建档进度和字段状态
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

# 导入数据库基类
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


# ============================================================================
# 枚举类型
# ============================================================================

class WizardStep(str, Enum):
    """向导步骤"""
    BASIC_INFO = "basic_info"           # Step 1: 基本信息
    SCRIPT_IMPORT = "script_import"     # Step 2: 剧本导入
    CHARACTER_SETUP = "character_setup" # Step 3: 角色设定
    SCENE_PLANNING = "scene_planning"   # Step 4: 场次规划
    REFERENCES = "references"           # Step 5: 参考资料
    CONFIRMATION = "confirmation"       # Step 6: 确认提交


class FieldStatus(str, Enum):
    """字段状态"""
    EMPTY = "empty"                     # 未填写
    USER_INPUT = "user_input"           # 用户输入
    AI_GENERATED = "ai_generated"       # AI 生成
    AI_PENDING = "ai_pending"           # AI 生成中
    AI_REVIEWED = "ai_reviewed"         # AI 生成已审核
    USER_CONFIRMED = "user_confirmed"   # 用户已确认


class DraftStatus(str, Enum):
    """草稿状态"""
    DRAFT = "draft"                     # 草稿
    IN_PROGRESS = "in_progress"         # 进行中
    PENDING_REVIEW = "pending_review"   # 待审核
    COMPLETED = "completed"             # 已完成
    ARCHIVED = "archived"               # 已归档


# ============================================================================
# SQLAlchemy 模型
# ============================================================================

class ProjectWizardDraft(Base):
    """项目立项向导草稿表"""
    __tablename__ = "project_wizard_drafts"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)  # 关联的项目ID（完成后创建）
    user_id = Column(String, nullable=True)     # 用户ID
    
    # 进度信息
    current_step = Column(String(50), default=WizardStep.BASIC_INFO.value)
    completion_percentage = Column(Float, default=0.0)
    status = Column(String(50), default=DraftStatus.DRAFT.value)
    
    # 字段状态（JSON 存储每个字段的状态）
    field_status = Column(JSON, default=dict)
    # 示例: {
    #   "title": "user_input",
    #   "logline": "ai_generated",
    #   "synopsis": "ai_pending",
    #   "characters": {"张三": "user_confirmed", "李四": "ai_generated"}
    # }
    
    # 草稿数据（JSON 存储所有表单数据）
    draft_data = Column(JSON, default=dict)
    # 示例: {
    #   "basic_info": {"title": "...", "project_type": "..."},
    #   "script": {"content": "...", "parsed_scenes": [...]},
    #   "characters": [...],
    #   "scenes": [...],
    #   "references": [...]
    # }
    
    # Agent 任务记录
    agent_tasks = Column(JSON, default=list)
    # 示例: [
    #   {"task_id": "...", "agent": "script_agent", "status": "completed"},
    #   {"task_id": "...", "agent": "director_agent", "status": "reviewing"}
    # ]
    
    # 审核记录
    review_history = Column(JSON, default=list)
    # 示例: [
    #   {"timestamp": "...", "agent": "director_agent", "status": "approved", "suggestions": []}
    # ]
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_saved_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


# ============================================================================
# Pydantic 模型（API 请求/响应）
# ============================================================================

class FieldStatusInfo(BaseModel):
    """字段状态信息"""
    field_name: str
    status: FieldStatus
    source: Optional[str] = None  # 来源 Agent
    last_modified: Optional[str] = None
    version: int = 1


class WizardDraftCreate(BaseModel):
    """创建草稿请求"""
    user_id: Optional[str] = None
    initial_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WizardDraftUpdate(BaseModel):
    """更新草稿请求"""
    current_step: Optional[WizardStep] = None
    draft_data: Optional[Dict[str, Any]] = None
    field_status: Optional[Dict[str, str]] = None


class WizardDraftResponse(BaseModel):
    """草稿响应"""
    id: str
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    current_step: WizardStep
    completion_percentage: float
    status: DraftStatus
    field_status: Dict[str, Any]
    draft_data: Dict[str, Any]
    agent_tasks: List[Dict[str, Any]]
    review_history: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    last_saved_at: str
    
    model_config = ConfigDict(from_attributes=True)


class WizardProgressResponse(BaseModel):
    """向导进度响应"""
    draft_id: str
    current_step: WizardStep
    completion_percentage: float
    steps_completed: List[WizardStep]
    steps_remaining: List[WizardStep]
    field_summary: Dict[str, int]  # {"empty": 5, "user_input": 3, "ai_generated": 2}
    estimated_time_remaining: Optional[int] = None  # 分钟


# ============================================================================
# 辅助函数
# ============================================================================

def calculate_completion_percentage(draft_data: Dict[str, Any], field_status: Dict[str, str]) -> float:
    """计算完成度百分比"""
    # 定义必填字段和权重
    required_fields = {
        "title": 10,
        "project_type": 10,
        "script_content": 20,
        "logline": 10,
        "synopsis": 10,
        "characters": 15,
        "scenes": 15,
        "references": 10
    }
    
    total_weight = sum(required_fields.values())
    completed_weight = 0
    
    for field, weight in required_fields.items():
        status = field_status.get(field, FieldStatus.EMPTY.value)
        if status in [FieldStatus.USER_INPUT.value, FieldStatus.USER_CONFIRMED.value, 
                      FieldStatus.AI_REVIEWED.value]:
            completed_weight += weight
        elif status == FieldStatus.AI_GENERATED.value:
            completed_weight += weight * 0.8  # AI 生成但未确认算 80%
        elif status == FieldStatus.AI_PENDING.value:
            completed_weight += weight * 0.3  # 生成中算 30%
    
    return round((completed_weight / total_weight) * 100, 1)


def get_steps_status(current_step: WizardStep) -> tuple:
    """获取步骤完成状态"""
    all_steps = list(WizardStep)
    current_index = all_steps.index(current_step)
    
    completed = all_steps[:current_index]
    remaining = all_steps[current_index + 1:]
    
    return completed, remaining
