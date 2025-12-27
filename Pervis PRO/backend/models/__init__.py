# -*- coding: utf-8 -*-
"""
模型模块初始化文件

Phase 3: 后端数据模型
"""

# 基础模型
from .base import (
    ProcessingStatus,
    Beat,
    Character,
    ScriptAnalysisRequest,
    ScriptAnalysisResponse,
    AssetUploadResponse,
    AssetSegment,
    AssetStatusResponse,
    SearchQuery,
    SearchResult,
    SearchResponse,
    FeedbackRequest,
    FeedbackResponse,
    ProjectCreate,
    ProjectResponse,
    BeatCreate,
    BeatResponse,
    AssetCreate,
    AssetResponse
)

# 项目立项向导模型
from .wizard_draft import (
    WizardStep,
    FieldStatus,
    DraftStatus,
    ProjectWizardDraft,
    WizardDraftCreate,
    WizardDraftUpdate,
    WizardDraftResponse,
    WizardProgressResponse,
    calculate_completion_percentage,
    get_steps_status
)

# 项目模板模型
from .project_template import (
    TemplateType,
    ProjectCategory,
    ProjectTemplate,
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    SYSTEM_TEMPLATES,
    get_system_templates,
    get_template_by_category
)

# Agent 任务模型
from .agent_task import (
    AgentType,
    TaskStatus,
    TaskPriority,
    AgentTask,
    AgentTaskLog,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskLogEntry,
    TaskRetryRequest,
    get_agent_display_name,
    get_status_message,
    calculate_task_duration
)

# 项目上下文模型
from .project_context import (
    VersionStatus,
    DecisionType,
    ContentType,
    ProjectSpecs,
    StyleContext,
    ContentVersion,
    UserDecision,
    ProjectSpecsCreate,
    ProjectSpecsResponse,
    StyleContextCreate,
    StyleContextResponse,
    ContentVersionCreate,
    ContentVersionResponse,
    VersionDisplayInfo,
    UserDecisionCreate,
    UserDecisionResponse,
    generate_version_name,
    get_next_version_number,
    check_version_conflict
)

# 关键帧模型
from .keyframe import (
    ExtractionStrategy,
    KeyFrameConfig,
    KeyFrameData,
    KeyFrame,
    KeyFrameExtractionJob,
    frame_to_timecode,
    timestamp_to_timecode,
    timecode_to_timestamp,
    generate_keyframe_id
)

__all__ = [
    # 基础模型
    "ProcessingStatus",
    "Beat",
    "Character",
    "ScriptAnalysisRequest",
    "ScriptAnalysisResponse",
    "AssetUploadResponse",
    "AssetSegment",
    "AssetStatusResponse",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "FeedbackRequest",
    "FeedbackResponse",
    "ProjectCreate",
    "ProjectResponse",
    "BeatCreate",
    "BeatResponse",
    "AssetCreate",
    "AssetResponse",
    
    # 向导模型
    "WizardStep",
    "FieldStatus",
    "DraftStatus",
    "ProjectWizardDraft",
    "WizardDraftCreate",
    "WizardDraftUpdate",
    "WizardDraftResponse",
    "WizardProgressResponse",
    "calculate_completion_percentage",
    "get_steps_status",
    
    # 模板模型
    "TemplateType",
    "ProjectCategory",
    "ProjectTemplate",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateListResponse",
    "SYSTEM_TEMPLATES",
    "get_system_templates",
    "get_template_by_category",
    
    # Agent 任务模型
    "AgentType",
    "TaskStatus",
    "TaskPriority",
    "AgentTask",
    "AgentTaskLog",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskStatusResponse",
    "TaskListResponse",
    "TaskLogEntry",
    "TaskRetryRequest",
    "get_agent_display_name",
    "get_status_message",
    "calculate_task_duration",
    
    # 项目上下文模型
    "VersionStatus",
    "DecisionType",
    "ContentType",
    "ProjectSpecs",
    "StyleContext",
    "ContentVersion",
    "UserDecision",
    "ProjectSpecsCreate",
    "ProjectSpecsResponse",
    "StyleContextCreate",
    "StyleContextResponse",
    "ContentVersionCreate",
    "ContentVersionResponse",
    "VersionDisplayInfo",
    "UserDecisionCreate",
    "UserDecisionResponse",
    "generate_version_name",
    "get_next_version_number",
    "check_version_conflict",
    
    # 关键帧模型
    "ExtractionStrategy",
    "KeyFrameConfig",
    "KeyFrameData",
    "KeyFrame",
    "KeyFrameExtractionJob",
    "frame_to_timecode",
    "timestamp_to_timecode",
    "timecode_to_timestamp",
    "generate_keyframe_id"
]