# -*- coding: utf-8 -*-
"""
Project Setup Workflow - 立项工作流

实现项目立项流程，包括信息收集、LLM补全、项目档案生成
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowStatus,
    StepType,
)


class ProjectType(Enum):
    """项目类型"""
    FILM = "film"
    TV_SERIES = "tv_series"
    SHORT_FILM = "short_film"
    DOCUMENTARY = "documentary"
    ANIMATION = "animation"
    COMMERCIAL = "commercial"


class ProjectStatus(Enum):
    """项目状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ProjectInfo:
    """项目信息"""
    id: str
    name: str
    project_type: ProjectType = ProjectType.FILM
    description: str = ""
    genre: List[str] = field(default_factory=list)
    target_audience: str = ""
    estimated_duration: int = 0  # 分钟
    budget_level: str = ""  # low, medium, high
    style_references: List[str] = field(default_factory=list)
    key_themes: List[str] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "project_type": self.project_type.value,
            "description": self.description,
            "genre": self.genre,
            "target_audience": self.target_audience,
            "estimated_duration": self.estimated_duration,
            "budget_level": self.budget_level,
            "style_references": self.style_references,
            "key_themes": self.key_themes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectInfo":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            project_type=ProjectType(data.get("project_type", "film")),
            description=data.get("description", ""),
            genre=data.get("genre", []),
            target_audience=data.get("target_audience", ""),
            estimated_duration=data.get("estimated_duration", 0),
            budget_level=data.get("budget_level", ""),
            style_references=data.get("style_references", []),
            key_themes=data.get("key_themes", []),
            status=ProjectStatus(data.get("status", "draft")),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProjectArchive:
    """项目档案"""
    project_id: str
    project_info: ProjectInfo
    llm_suggestions: Dict[str, Any] = field(default_factory=dict)
    team_assignments: Dict[str, str] = field(default_factory=dict)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_info": self.project_info.to_dict(),
            "llm_suggestions": self.llm_suggestions,
            "team_assignments": self.team_assignments,
            "milestones": self.milestones,
            "resources": self.resources,
            "created_at": self.created_at.isoformat(),
        }


class ProjectSetupWorkflow:
    """立项工作流"""
    
    WORKFLOW_ID = "project_setup"
    WORKFLOW_NAME = "项目立项工作流"
    
    def __init__(
        self,
        engine: WorkflowEngine,
        llm_handler: Optional[Callable] = None
    ):
        self.engine = engine
        self.llm_handler = llm_handler or self._default_llm_handler
        self._projects: Dict[str, ProjectInfo] = {}
        self._archives: Dict[str, ProjectArchive] = {}
        
        # 注册工作流
        self._register_workflow()
    
    def _register_workflow(self) -> None:
        """注册立项工作流"""
        workflow = WorkflowDefinition(
            id=self.WORKFLOW_ID,
            name=self.WORKFLOW_NAME,
            description="项目立项流程，包括信息收集、LLM补全、档案生成"
        )
        
        # Step 1: 收集基础信息
        step1 = WorkflowStep(
            id="collect_info",
            name="收集项目信息",
            step_type=StepType.TASK,
            handler=self._collect_info_handler,
            next_steps=["validate_info"]
        )
        
        # Step 2: 验证信息
        step2 = WorkflowStep(
            id="validate_info",
            name="验证项目信息",
            step_type=StepType.TASK,
            handler=self._validate_info_handler,
            next_steps=["llm_completion"]
        )
        
        # Step 3: LLM补全
        step3 = WorkflowStep(
            id="llm_completion",
            name="LLM信息补全",
            step_type=StepType.TASK,
            handler=self._llm_completion_handler,
            next_steps=["user_review"]
        )
        
        # Step 4: 用户审核
        step4 = WorkflowStep(
            id="user_review",
            name="用户审核",
            step_type=StepType.WAIT,
            next_steps=["generate_archive"]
        )
        
        # Step 5: 生成档案
        step5 = WorkflowStep(
            id="generate_archive",
            name="生成项目档案",
            step_type=StepType.TASK,
            handler=self._generate_archive_handler
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        workflow.add_step(step5)
        
        self.engine.register_workflow(workflow)

    
    # 步骤处理器
    async def _collect_info_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """收集项目信息"""
        project_data = context.get("project_data", {})
        
        # 创建项目信息
        project = ProjectInfo(
            id=str(uuid.uuid4()),
            name=project_data.get("name", "未命名项目"),
            project_type=ProjectType(project_data.get("project_type", "film")),
            description=project_data.get("description", ""),
            genre=project_data.get("genre", []),
            target_audience=project_data.get("target_audience", ""),
            estimated_duration=project_data.get("estimated_duration", 0),
            budget_level=project_data.get("budget_level", "medium"),
            style_references=project_data.get("style_references", []),
            key_themes=project_data.get("key_themes", []),
        )
        
        self._projects[project.id] = project
        
        return {
            "project_id": project.id,
            "project_info": project.to_dict(),
            "collection_status": "completed"
        }
    
    async def _validate_info_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """验证项目信息"""
        project_info = context.get("project_info", {})
        
        validation_errors = []
        validation_warnings = []
        
        # 必填字段检查
        if not project_info.get("name"):
            validation_errors.append("项目名称不能为空")
        
        # 建议字段检查
        if not project_info.get("description"):
            validation_warnings.append("建议添加项目描述")
        
        if not project_info.get("genre"):
            validation_warnings.append("建议指定项目类型/风格")
        
        if not project_info.get("target_audience"):
            validation_warnings.append("建议指定目标受众")
        
        # 计算需要LLM补全的字段
        fields_to_complete = []
        if not project_info.get("description"):
            fields_to_complete.append("description")
        if not project_info.get("key_themes"):
            fields_to_complete.append("key_themes")
        if not project_info.get("style_references"):
            fields_to_complete.append("style_references")
        
        return {
            "validation_passed": len(validation_errors) == 0,
            "validation_errors": validation_errors,
            "validation_warnings": validation_warnings,
            "fields_to_complete": fields_to_complete,
        }
    
    async def _llm_completion_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """LLM信息补全"""
        project_info = context.get("project_info", {})
        fields_to_complete = context.get("fields_to_complete", [])
        
        if not fields_to_complete:
            return {"llm_suggestions": {}, "completion_status": "skipped"}
        
        # 调用LLM进行补全
        suggestions = await self.llm_handler(project_info, fields_to_complete)
        
        return {
            "llm_suggestions": suggestions,
            "completion_status": "completed"
        }
    
    async def _generate_archive_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成项目档案"""
        project_id = context.get("project_id")
        project_info_data = context.get("project_info", {})
        llm_suggestions = context.get("llm_suggestions", {})
        user_approved = context.get("user_approved", True)
        
        if not user_approved:
            return {"archive_status": "rejected"}
        
        # 应用LLM建议（如果用户接受）
        if llm_suggestions and context.get("accept_suggestions", True):
            if "description" in llm_suggestions and not project_info_data.get("description"):
                project_info_data["description"] = llm_suggestions["description"]
            if "key_themes" in llm_suggestions and not project_info_data.get("key_themes"):
                project_info_data["key_themes"] = llm_suggestions["key_themes"]
            if "style_references" in llm_suggestions and not project_info_data.get("style_references"):
                project_info_data["style_references"] = llm_suggestions["style_references"]
        
        # 创建项目档案
        project_info = ProjectInfo.from_dict(project_info_data)
        project_info.status = ProjectStatus.IN_PROGRESS
        project_info.updated_at = datetime.now()
        
        archive = ProjectArchive(
            project_id=project_id,
            project_info=project_info,
            llm_suggestions=llm_suggestions,
        )
        
        self._archives[project_id] = archive
        self._projects[project_id] = project_info
        
        return {
            "archive_id": project_id,
            "archive": archive.to_dict(),
            "archive_status": "completed"
        }

    
    # 默认LLM处理器
    async def _default_llm_handler(
        self,
        project_info: Dict[str, Any],
        fields_to_complete: List[str]
    ) -> Dict[str, Any]:
        """默认LLM处理器（模拟）"""
        suggestions = {}
        
        name = project_info.get("name", "")
        genre = project_info.get("genre", [])
        
        if "description" in fields_to_complete:
            genre_str = "、".join(genre) if genre else "影视"
            suggestions["description"] = f"《{name}》是一部{genre_str}作品，讲述了一个引人入胜的故事。"
        
        if "key_themes" in fields_to_complete:
            suggestions["key_themes"] = ["成长", "冒险", "友情"]
        
        if "style_references" in fields_to_complete:
            suggestions["style_references"] = ["经典叙事风格", "现代视觉语言"]
        
        return suggestions
    
    # 公共API
    async def start_project_setup(
        self,
        project_data: Dict[str, Any]
    ) -> Optional[WorkflowInstance]:
        """启动立项流程"""
        instance = await self.engine.create_instance(
            self.WORKFLOW_ID,
            context={"project_data": project_data}
        )
        
        if instance:
            await self.engine.start_instance(instance.id)
        
        return instance
    
    async def approve_project(
        self,
        instance_id: str,
        accept_suggestions: bool = True
    ) -> bool:
        """审核通过项目"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={
                "user_approved": True,
                "accept_suggestions": accept_suggestions
            }
        )
    
    async def reject_project(self, instance_id: str) -> bool:
        """拒绝项目"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": False}
        )
    
    def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        """获取项目信息"""
        return self._projects.get(project_id)
    
    def get_archive(self, project_id: str) -> Optional[ProjectArchive]:
        """获取项目档案"""
        return self._archives.get(project_id)
    
    def list_projects(self, status: Optional[ProjectStatus] = None) -> List[ProjectInfo]:
        """列出项目"""
        projects = list(self._projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return projects
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        projects = list(self._projects.values())
        return {
            "total_projects": len(projects),
            "draft_projects": len([p for p in projects if p.status == ProjectStatus.DRAFT]),
            "in_progress_projects": len([p for p in projects if p.status == ProjectStatus.IN_PROGRESS]),
            "completed_projects": len([p for p in projects if p.status == ProjectStatus.COMPLETED]),
            "total_archives": len(self._archives),
        }
