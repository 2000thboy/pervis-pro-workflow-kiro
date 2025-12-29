# -*- coding: utf-8 -*-
"""
项目模板模型

Phase 3: 后端数据模型
Task 3.2: ProjectTemplate 模型

支持系统预设模板和用户自定义模板
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

# 导入数据库基类
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


# ============================================================================
# 枚举类型
# ============================================================================

class TemplateType(str, Enum):
    """模板类型"""
    SYSTEM = "system"       # 系统预设
    USER = "user"           # 用户自定义
    SHARED = "shared"       # 共享模板


class ProjectCategory(str, Enum):
    """项目类别"""
    SHORT_FILM = "short_film"       # 短片
    ADVERTISEMENT = "advertisement" # 广告
    MUSIC_VIDEO = "music_video"     # MV
    FEATURE_FILM = "feature_film"   # 长片
    DOCUMENTARY = "documentary"     # 纪录片
    ANIMATION = "animation"         # 动画
    CUSTOM = "custom"               # 自定义


# ============================================================================
# SQLAlchemy 模型
# ============================================================================

class ProjectTemplate(Base):
    """项目模板表"""
    __tablename__ = "project_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 模板类型
    template_type = Column(String(50), default=TemplateType.USER.value)
    category = Column(String(50), default=ProjectCategory.CUSTOM.value)
    
    # 模板配置
    default_values = Column(JSON, default=dict)
    # 示例: {
    #   "duration_minutes": 5,
    #   "aspect_ratio": "16:9",
    #   "frame_rate": 24,
    #   "resolution": "1920x1080"
    # }
    
    # 预设字段
    preset_fields = Column(JSON, default=dict)
    # 示例: {
    #   "project_type": "short_film",
    #   "style_tags": ["现代", "都市"],
    #   "target_audience": "年轻人"
    # }
    
    # 向导配置
    wizard_config = Column(JSON, default=dict)
    # 示例: {
    #   "skip_steps": [],
    #   "required_fields": ["title", "script_content"],
    #   "optional_fields": ["references"],
    #   "auto_generate": ["logline", "synopsis"]
    # }
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    
    # 所有者
    owner_id = Column(String, nullable=True)  # 系统模板为 null
    is_public = Column(Integer, default=0)    # 是否公开
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 元数据
    extra_data = Column(JSON, default=dict)


# ============================================================================
# Pydantic 模型（API 请求/响应）
# ============================================================================

class TemplateDefaultValues(BaseModel):
    """模板默认值"""
    duration_minutes: Optional[float] = None
    aspect_ratio: str = "16:9"
    frame_rate: float = 24.0
    resolution: str = "1920x1080"
    audio_sample_rate: int = 48000
    color_space: str = "Rec.709"


class TemplateWizardConfig(BaseModel):
    """向导配置"""
    skip_steps: List[str] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=lambda: ["title"])
    optional_fields: List[str] = Field(default_factory=list)
    auto_generate: List[str] = Field(default_factory=list)
    default_agents: List[str] = Field(default_factory=lambda: ["script_agent", "director_agent"])


class TemplateCreate(BaseModel):
    """创建模板请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: ProjectCategory = ProjectCategory.CUSTOM
    default_values: Optional[TemplateDefaultValues] = None
    preset_fields: Optional[Dict[str, Any]] = None
    wizard_config: Optional[TemplateWizardConfig] = None
    is_public: bool = False


class TemplateUpdate(BaseModel):
    """更新模板请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProjectCategory] = None
    default_values: Optional[TemplateDefaultValues] = None
    preset_fields: Optional[Dict[str, Any]] = None
    wizard_config: Optional[TemplateWizardConfig] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    """模板响应"""
    id: str
    name: str
    description: Optional[str] = None
    template_type: TemplateType
    category: ProjectCategory
    default_values: Dict[str, Any]
    preset_fields: Dict[str, Any]
    wizard_config: Dict[str, Any]
    usage_count: int
    owner_id: Optional[str] = None
    is_public: bool
    created_at: str
    updated_at: str
    
    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[TemplateResponse]
    total: int
    system_count: int
    user_count: int


# ============================================================================
# 系统预设模板
# ============================================================================

SYSTEM_TEMPLATES = [
    {
        "id": "tpl_short_film",
        "name": "短片模板",
        "description": "适用于 5-30 分钟的短片项目",
        "template_type": TemplateType.SYSTEM.value,
        "category": ProjectCategory.SHORT_FILM.value,
        "default_values": {
            "duration_minutes": 15,
            "aspect_ratio": "2.39:1",
            "frame_rate": 24,
            "resolution": "1920x1080"
        },
        "preset_fields": {
            "project_type": "short_film",
            "style_tags": ["电影感", "叙事"]
        },
        "wizard_config": {
            "skip_steps": [],
            "required_fields": ["title", "script_content", "logline"],
            "auto_generate": ["synopsis", "character_bio"]
        }
    },
    {
        "id": "tpl_advertisement",
        "name": "广告模板",
        "description": "适用于 15-60 秒的商业广告",
        "template_type": TemplateType.SYSTEM.value,
        "category": ProjectCategory.ADVERTISEMENT.value,
        "default_values": {
            "duration_minutes": 0.5,
            "aspect_ratio": "16:9",
            "frame_rate": 30,
            "resolution": "1920x1080"
        },
        "preset_fields": {
            "project_type": "advertisement",
            "style_tags": ["商业", "快节奏"]
        },
        "wizard_config": {
            "skip_steps": ["scene_planning"],
            "required_fields": ["title", "logline"],
            "auto_generate": ["visual_tags"]
        }
    },
    {
        "id": "tpl_music_video",
        "name": "MV 模板",
        "description": "适用于音乐视频项目",
        "template_type": TemplateType.SYSTEM.value,
        "category": ProjectCategory.MUSIC_VIDEO.value,
        "default_values": {
            "duration_minutes": 4,
            "aspect_ratio": "16:9",
            "frame_rate": 24,
            "resolution": "1920x1080"
        },
        "preset_fields": {
            "project_type": "music_video",
            "style_tags": ["视觉", "节奏感"]
        },
        "wizard_config": {
            "skip_steps": ["script_import"],
            "required_fields": ["title"],
            "auto_generate": ["visual_tags", "mood_tags"]
        }
    },
    {
        "id": "tpl_feature_film",
        "name": "长片模板",
        "description": "适用于 60 分钟以上的长片项目",
        "template_type": TemplateType.SYSTEM.value,
        "category": ProjectCategory.FEATURE_FILM.value,
        "default_values": {
            "duration_minutes": 90,
            "aspect_ratio": "2.39:1",
            "frame_rate": 24,
            "resolution": "3840x2160"
        },
        "preset_fields": {
            "project_type": "feature_film",
            "style_tags": ["电影", "叙事", "专业"]
        },
        "wizard_config": {
            "skip_steps": [],
            "required_fields": ["title", "script_content", "logline", "synopsis"],
            "auto_generate": ["character_bio", "scene_breakdown"]
        }
    }
]


def get_system_templates() -> List[Dict[str, Any]]:
    """获取系统预设模板"""
    return SYSTEM_TEMPLATES


def get_template_by_category(category: ProjectCategory) -> Optional[Dict[str, Any]]:
    """根据类别获取系统模板"""
    for template in SYSTEM_TEMPLATES:
        if template["category"] == category.value:
            return template
    return None
