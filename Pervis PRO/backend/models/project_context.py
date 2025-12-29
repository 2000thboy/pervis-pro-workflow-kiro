# -*- coding: utf-8 -*-
"""
项目上下文相关模型

Phase 3: 后端数据模型
Task 3.4: ProjectContext 相关模型

包含：
- ProjectSpecs: 项目规格（时长、画幅、帧率、分辨率）
- StyleContext: 艺术风格上下文
- ContentVersion: 版本记录
- UserDecision: 用户决策记录
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

class VersionStatus(str, Enum):
    """版本状态"""
    DRAFT = "draft"             # 草稿
    PENDING = "pending"         # 待审核
    APPROVED = "approved"       # 已批准
    REJECTED = "rejected"       # 已拒绝
    SUPERSEDED = "superseded"   # 已被替代


class DecisionType(str, Enum):
    """决策类型"""
    ACCEPT = "accept"           # 接受
    REJECT = "reject"           # 拒绝
    MODIFY = "modify"           # 修改
    DEFER = "defer"             # 延迟
    RESTORE = "restore"         # 恢复


class ContentType(str, Enum):
    """内容类型"""
    LOGLINE = "logline"
    SYNOPSIS = "synopsis"
    CHARACTER = "character"
    SCENE = "scene"
    REFERENCE = "reference"
    TAG = "tag"
    STYLE = "style"


# ============================================================================
# SQLAlchemy 模型
# ============================================================================

class ProjectSpecs(Base):
    """项目规格表"""
    __tablename__ = "project_specs"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, unique=True)
    
    # 基本规格
    duration_minutes = Column(Float)
    aspect_ratio = Column(String(20), default="16:9")
    frame_rate = Column(Float, default=24.0)
    resolution = Column(String(20), default="1920x1080")
    
    # 音频规格
    audio_sample_rate = Column(Integer, default=48000)
    audio_channels = Column(Integer, default=2)
    audio_bitrate = Column(Integer, default=320)
    
    # 视频规格
    video_codec = Column(String(50), default="H.264")
    video_bitrate = Column(Integer)
    color_space = Column(String(50), default="Rec.709")
    
    # 输出格式
    output_format = Column(String(20), default="mp4")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


class StyleContext(Base):
    """艺术风格上下文表"""
    __tablename__ = "style_contexts"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    
    # 视觉风格
    visual_style = Column(String(100))  # 写实、卡通、赛博朋克等
    color_palette = Column(JSON, default=list)  # 主色调列表
    lighting_style = Column(String(100))  # 自然光、高对比、柔和等
    
    # 对标项目
    reference_projects = Column(JSON, default=list)
    # 示例: [{"name": "银翼杀手", "aspects": ["色调", "氛围"]}]
    
    # 风格标签
    style_tags = Column(JSON, default=list)
    # 示例: ["科幻", "黑暗", "未来感"]
    
    # 摄影风格
    cinematography_style = Column(String(100))
    camera_movement = Column(JSON, default=list)  # 手持、稳定器、轨道等
    
    # 剪辑风格
    editing_style = Column(String(100))  # 快节奏、慢节奏、蒙太奇等
    transition_preferences = Column(JSON, default=list)
    
    # 确认状态
    is_confirmed = Column(Integer, default=0)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(String)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ContentVersion(Base):
    """内容版本表"""
    __tablename__ = "content_versions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    
    # 版本信息
    version_name = Column(String(255), nullable=False)  # 角色_张三_v1
    version_number = Column(Integer, nullable=False)
    
    # 内容信息
    content_type = Column(String(50), nullable=False)  # logline, character, scene, etc.
    entity_id = Column(String)  # 实体ID（如角色ID、场次ID）
    entity_name = Column(String(255))  # 实体名称
    
    # 内容数据
    content = Column(JSON, nullable=False)
    content_hash = Column(String(64))  # 内容哈希，用于检测变化
    
    # 来源信息
    source = Column(String(50), default="user")  # user, script_agent, art_agent, etc.
    source_task_id = Column(String)  # 关联的 Agent 任务ID
    
    # 状态
    status = Column(String(50), default=VersionStatus.DRAFT.value)
    
    # 审核信息
    reviewed_by = Column(String)  # director_agent 或 user
    review_result = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


class UserDecision(Base):
    """用户决策表"""
    __tablename__ = "user_decisions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    
    # 决策信息
    decision_type = Column(String(50), nullable=False)  # accept, reject, modify, etc.
    
    # 关联内容
    content_type = Column(String(50))
    content_id = Column(String)  # 版本ID 或 实体ID
    version_id = Column(String)  # 关联的版本ID
    
    # 决策详情
    decision_data = Column(JSON, default=dict)
    # 示例: {
    #   "action": "reject",
    #   "reason": "角色性格不符合设定",
    #   "suggestions": ["更加内向", "减少对话"]
    # }
    
    # 上下文
    context = Column(JSON, default=dict)
    # 示例: {
    #   "previous_version": "v1",
    #   "agent_suggestions": [...],
    #   "user_notes": "..."
    # }
    
    # 用户信息
    user_id = Column(String)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


# ============================================================================
# Pydantic 模型（API 请求/响应）
# ============================================================================

class ProjectSpecsCreate(BaseModel):
    """创建项目规格请求"""
    project_id: str
    duration_minutes: Optional[float] = None
    aspect_ratio: str = "16:9"
    frame_rate: float = 24.0
    resolution: str = "1920x1080"
    audio_sample_rate: int = 48000
    video_codec: str = "H.264"
    output_format: str = "mp4"


class ProjectSpecsResponse(BaseModel):
    """项目规格响应"""
    id: str
    project_id: str
    duration_minutes: Optional[float] = None
    aspect_ratio: str
    frame_rate: float
    resolution: str
    audio_sample_rate: int
    audio_channels: int
    video_codec: str
    color_space: str
    output_format: str
    created_at: str
    updated_at: str
    
    model_config = ConfigDict(from_attributes=True)


class StyleContextCreate(BaseModel):
    """创建风格上下文请求"""
    project_id: str
    visual_style: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)
    lighting_style: Optional[str] = None
    reference_projects: List[Dict[str, Any]] = Field(default_factory=list)
    style_tags: List[str] = Field(default_factory=list)
    cinematography_style: Optional[str] = None
    editing_style: Optional[str] = None


class StyleContextResponse(BaseModel):
    """风格上下文响应"""
    id: str
    project_id: str
    visual_style: Optional[str] = None
    color_palette: List[str]
    lighting_style: Optional[str] = None
    reference_projects: List[Dict[str, Any]]
    style_tags: List[str]
    cinematography_style: Optional[str] = None
    editing_style: Optional[str] = None
    is_confirmed: bool
    confirmed_at: Optional[str] = None
    created_at: str
    updated_at: str
    
    model_config = ConfigDict(from_attributes=True)


class ContentVersionCreate(BaseModel):
    """创建内容版本请求"""
    project_id: str
    content_type: ContentType
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    content: Dict[str, Any]
    source: str = "user"


class ContentVersionResponse(BaseModel):
    """内容版本响应"""
    id: str
    project_id: str
    version_name: str
    version_number: int
    content_type: ContentType
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    content: Dict[str, Any]
    source: str
    status: VersionStatus
    reviewed_by: Optional[str] = None
    review_result: Dict[str, Any]
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)


class VersionDisplayInfo(BaseModel):
    """版本显示信息"""
    current_version: str
    version_count: int
    last_modified: str
    last_modified_by: str
    has_pending_changes: bool
    history: List[Dict[str, Any]]


class UserDecisionCreate(BaseModel):
    """创建用户决策请求"""
    project_id: str
    decision_type: DecisionType
    content_type: Optional[ContentType] = None
    content_id: Optional[str] = None
    version_id: Optional[str] = None
    decision_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class UserDecisionResponse(BaseModel):
    """用户决策响应"""
    id: str
    project_id: str
    decision_type: DecisionType
    content_type: Optional[ContentType] = None
    content_id: Optional[str] = None
    version_id: Optional[str] = None
    decision_data: Dict[str, Any]
    context: Dict[str, Any]
    user_id: Optional[str] = None
    created_at: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 辅助函数
# ============================================================================

def generate_version_name(content_type: str, entity_name: Optional[str], version_number: int) -> str:
    """生成版本命名"""
    type_names = {
        "logline": "Logline",
        "synopsis": "Synopsis",
        "character": "角色",
        "scene": "场次",
        "reference": "参考",
        "tag": "标签",
        "style": "风格"
    }
    
    type_name = type_names.get(content_type, content_type)
    
    if entity_name:
        return f"{type_name}_{entity_name}_v{version_number}"
    else:
        return f"{type_name}_v{version_number}"


def get_next_version_number(existing_versions: List[ContentVersion], content_type: str, entity_id: Optional[str] = None) -> int:
    """获取下一个版本号"""
    matching_versions = [
        v for v in existing_versions
        if v.content_type == content_type and v.entity_id == entity_id
    ]
    
    if not matching_versions:
        return 1
    
    max_version = max(v.version_number for v in matching_versions)
    return max_version + 1


def check_version_conflict(content_hash: str, existing_versions: List[ContentVersion]) -> bool:
    """检查版本是否有冲突（内容相同）"""
    for version in existing_versions:
        if version.content_hash == content_hash:
            return True
    return False
