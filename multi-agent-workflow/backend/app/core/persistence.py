# -*- coding: utf-8 -*-
"""
数据持久化服务模块

提供统一的数据持久化接口，支持：
- 项目数据存储和检索
- 工作流状态保存
- Agent状态持久化
- 素材信息管理

Feature: multi-agent-workflow-core
Requirements: 7.2, 7.3, 7.5
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import uuid4

logger = logging.getLogger(__name__)

T = TypeVar('T')


class StorageProvider(Enum):
    """存储提供商"""
    MEMORY = "memory"  # 内存存储（用于测试）
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class ProjectData:
    """项目数据"""
    id: str
    name: str
    description: str = ""
    aspect_ratio: str = "16:9"
    duration: int = 0
    story_summary: str = ""
    story_content: str = ""
    status: str = "created"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "story_summary": self.story_summary,
            "story_content": self.story_content,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectData":
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            aspect_ratio=data.get("aspect_ratio", "16:9"),
            duration=data.get("duration", 0),
            story_summary=data.get("story_summary", ""),
            story_content=data.get("story_content", ""),
            status=data.get("status", "created"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class WorkflowStateData:
    """工作流状态数据"""
    id: str
    workflow_type: str
    project_id: str
    status: str = "pending"
    current_step: str = ""
    steps_completed: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "project_id": self.project_id,
            "status": self.status,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "context": self.context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStateData":
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        return cls(
            id=data["id"],
            workflow_type=data["workflow_type"],
            project_id=data["project_id"],
            status=data.get("status", "pending"),
            current_step=data.get("current_step", ""),
            steps_completed=data.get("steps_completed", []),
            context=data.get("context", {}),
            started_at=started_at,
            completed_at=completed_at,
            error_message=data.get("error_message")
        )


@dataclass
class AgentStateData:
    """Agent状态数据"""
    agent_id: str
    agent_type: str
    state: str = "idle"
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    capabilities: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state,
            "current_task": self.current_task,
            "last_activity": self.last_activity.isoformat(),
            "capabilities": self.capabilities,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStateData":
        last_activity = data.get("last_activity")
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            state=data.get("state", "idle"),
            current_task=data.get("current_task"),
            last_activity=last_activity or datetime.now(),
            capabilities=data.get("capabilities", []),
            config=data.get("config", {})
        )


@dataclass
class AssetData:
    """素材数据"""
    id: str
    name: str
    file_path: str
    asset_type: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_size: int = 0
    checksum: str = ""
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "asset_type": self.asset_type,
            "tags": self.tags,
            "metadata": self.metadata,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat()
        }


class BaseStorage(ABC):
    """存储基类"""
    
    @abstractmethod
    async def save_project(self, project: ProjectData) -> str:
        pass
    
    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[ProjectData]:
        pass
    
    @abstractmethod
    async def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProjectData]:
        pass
    
    @abstractmethod
    async def search_projects(
        self,
        query: str,
        limit: int = 20
    ) -> List[ProjectData]:
        pass
    
    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        pass
    
    @abstractmethod
    async def save_workflow_state(self, state: WorkflowStateData) -> str:
        pass
    
    @abstractmethod
    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowStateData]:
        pass
    
    @abstractmethod
    async def list_workflow_states(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[WorkflowStateData]:
        pass
    
    @abstractmethod
    async def save_agent_state(self, state: AgentStateData) -> str:
        pass
    
    @abstractmethod
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateData]:
        pass
    
    @abstractmethod
    async def list_agent_states(self) -> List[AgentStateData]:
        pass


class MemoryStorage(BaseStorage):
    """内存存储（用于测试）"""
    
    def __init__(self):
        self._projects: Dict[str, ProjectData] = {}
        self._workflows: Dict[str, WorkflowStateData] = {}
        self._agents: Dict[str, AgentStateData] = {}
        self._assets: Dict[str, AssetData] = {}
    
    async def save_project(self, project: ProjectData) -> str:
        project.updated_at = datetime.now()
        self._projects[project.id] = project
        return project.id
    
    async def get_project(self, project_id: str) -> Optional[ProjectData]:
        return self._projects.get(project_id)
    
    async def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProjectData]:
        projects = list(self._projects.values())
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        # 按更新时间排序
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        
        return projects[offset:offset + limit]
    
    async def search_projects(
        self,
        query: str,
        limit: int = 20
    ) -> List[ProjectData]:
        query_lower = query.lower()
        results = []
        
        for project in self._projects.values():
            if (query_lower in project.name.lower() or
                query_lower in project.description.lower() or
                query_lower in project.story_summary.lower()):
                results.append(project)
        
        # 按相关性排序（名称匹配优先）
        results.sort(key=lambda p: (
            0 if query_lower in p.name.lower() else 1,
            -p.updated_at.timestamp()
        ))
        
        return results[:limit]
    
    async def delete_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False
    
    async def save_workflow_state(self, state: WorkflowStateData) -> str:
        self._workflows[state.id] = state
        return state.id
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowStateData]:
        return self._workflows.get(workflow_id)
    
    async def list_workflow_states(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[WorkflowStateData]:
        workflows = list(self._workflows.values())
        
        if project_id:
            workflows = [w for w in workflows if w.project_id == project_id]
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        return workflows
    
    async def save_agent_state(self, state: AgentStateData) -> str:
        state.last_activity = datetime.now()
        self._agents[state.agent_id] = state
        return state.agent_id
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateData]:
        return self._agents.get(agent_id)
    
    async def list_agent_states(self) -> List[AgentStateData]:
        return list(self._agents.values())
    
    # 素材相关方法
    async def save_asset(self, asset: AssetData) -> str:
        self._assets[asset.id] = asset
        return asset.id
    
    async def get_asset(self, asset_id: str) -> Optional[AssetData]:
        return self._assets.get(asset_id)
    
    async def list_assets(
        self,
        project_id: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> List[AssetData]:
        assets = list(self._assets.values())
        
        if project_id:
            assets = [a for a in assets if a.project_id == project_id]
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        
        return assets
    
    async def clear(self):
        """清空所有数据"""
        self._projects.clear()
        self._workflows.clear()
        self._agents.clear()
        self._assets.clear()


@dataclass
class PersistenceConfig:
    """持久化配置"""
    provider: StorageProvider
    database_url: Optional[str] = None
    
    @classmethod
    def memory(cls) -> "PersistenceConfig":
        return cls(provider=StorageProvider.MEMORY)
    
    @classmethod
    def sqlite(cls, path: str = "data/app.db") -> "PersistenceConfig":
        return cls(
            provider=StorageProvider.SQLITE,
            database_url=f"sqlite:///{path}"
        )
    
    @classmethod
    def postgresql(cls, url: str) -> "PersistenceConfig":
        return cls(
            provider=StorageProvider.POSTGRESQL,
            database_url=url
        )


class PersistenceService:
    """
    数据持久化服务
    
    提供统一的数据持久化接口，支持：
    - 项目数据的CRUD操作
    - 工作流状态的实时保存
    - Agent状态的持久化
    - 历史项目检索
    """
    
    def __init__(self, config: Optional[PersistenceConfig] = None):
        self.config = config or PersistenceConfig.memory()
        self._storage: Optional[BaseStorage] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化持久化服务"""
        self._storage = self._create_storage()
        self._initialized = True
        logger.info(f"持久化服务初始化完成: provider={self.config.provider.value}")
        return True
    
    def _create_storage(self) -> BaseStorage:
        """创建存储实例"""
        if self.config.provider == StorageProvider.MEMORY:
            return MemoryStorage()
        # 其他存储类型可以在这里扩展
        return MemoryStorage()
    
    @property
    def storage(self) -> BaseStorage:
        if self._storage is None:
            self._storage = self._create_storage()
        return self._storage
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    # === 项目管理 (Requirements 7.5) ===
    
    async def create_project(
        self,
        name: str,
        description: str = "",
        aspect_ratio: str = "16:9",
        duration: int = 0,
        story_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectData:
        """
        创建新项目
        
        Args:
            name: 项目名称
            description: 项目描述
            aspect_ratio: 画幅比例
            duration: 时长（秒）
            story_summary: 故事概要
            metadata: 额外元数据
        
        Returns:
            创建的项目数据
        """
        project = ProjectData(
            id=str(uuid4()),
            name=name,
            description=description,
            aspect_ratio=aspect_ratio,
            duration=duration,
            story_summary=story_summary,
            status="created",
            metadata=metadata or {}
        )
        
        await self.storage.save_project(project)
        logger.info(f"项目创建成功: id={project.id}, name={name}")
        
        return project
    
    async def get_project(self, project_id: str) -> Optional[ProjectData]:
        """获取项目"""
        return await self.storage.get_project(project_id)
    
    async def update_project(
        self,
        project_id: str,
        **updates
    ) -> Optional[ProjectData]:
        """
        更新项目
        
        Args:
            project_id: 项目ID
            **updates: 要更新的字段
        
        Returns:
            更新后的项目数据
        """
        project = await self.storage.get_project(project_id)
        if not project:
            return None
        
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now()
        await self.storage.save_project(project)
        
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        return await self.storage.delete_project(project_id)
    
    async def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProjectData]:
        """
        列出项目
        
        Args:
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            项目列表
        """
        return await self.storage.list_projects(status, limit, offset)
    
    async def search_projects(
        self,
        query: str,
        limit: int = 20
    ) -> List[ProjectData]:
        """
        搜索项目（Requirements 7.5）
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            匹配的项目列表
        """
        return await self.storage.search_projects(query, limit)
    
    async def archive_project(self, project_id: str) -> Optional[ProjectData]:
        """归档项目"""
        return await self.update_project(project_id, status="archived")
    
    # === 工作流状态管理 (Requirements 7.2) ===
    
    async def save_workflow_state(
        self,
        workflow_id: str,
        workflow_type: str,
        project_id: str,
        status: str,
        current_step: str = "",
        steps_completed: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> WorkflowStateData:
        """
        保存工作流状态（实时保存中间状态）
        
        Args:
            workflow_id: 工作流ID
            workflow_type: 工作流类型
            project_id: 项目ID
            status: 状态
            current_step: 当前步骤
            steps_completed: 已完成步骤
            context: 上下文数据
            error_message: 错误信息
        
        Returns:
            保存的工作流状态
        """
        # 检查是否已存在
        existing = await self.storage.get_workflow_state(workflow_id)
        
        if existing:
            state = existing
            state.status = status
            state.current_step = current_step
            if steps_completed is not None:
                state.steps_completed = steps_completed
            if context is not None:
                state.context = context
            state.error_message = error_message
            
            if status == "completed":
                state.completed_at = datetime.now()
        else:
            state = WorkflowStateData(
                id=workflow_id,
                workflow_type=workflow_type,
                project_id=project_id,
                status=status,
                current_step=current_step,
                steps_completed=steps_completed or [],
                context=context or {},
                started_at=datetime.now(),
                error_message=error_message
            )
        
        await self.storage.save_workflow_state(state)
        logger.debug(f"工作流状态已保存: id={workflow_id}, status={status}")
        
        return state
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowStateData]:
        """获取工作流状态"""
        return await self.storage.get_workflow_state(workflow_id)
    
    async def list_workflow_states(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[WorkflowStateData]:
        """列出工作流状态"""
        return await self.storage.list_workflow_states(project_id, status)
    
    # === Agent状态管理 (Requirements 7.3) ===
    
    async def save_agent_state(
        self,
        agent_id: str,
        agent_type: str,
        state: str = "idle",
        current_task: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> AgentStateData:
        """
        保存Agent状态
        
        Args:
            agent_id: Agent ID
            agent_type: Agent类型
            state: 状态
            current_task: 当前任务
            capabilities: 能力列表
            config: 配置
        
        Returns:
            保存的Agent状态
        """
        agent_state = AgentStateData(
            agent_id=agent_id,
            agent_type=agent_type,
            state=state,
            current_task=current_task,
            capabilities=capabilities or [],
            config=config or {}
        )
        
        await self.storage.save_agent_state(agent_state)
        
        return agent_state
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateData]:
        """获取Agent状态"""
        return await self.storage.get_agent_state(agent_id)
    
    async def list_agent_states(self) -> List[AgentStateData]:
        """列出所有Agent状态"""
        return await self.storage.list_agent_states()
    
    async def update_agent_state(
        self,
        agent_id: str,
        state: str,
        current_task: Optional[str] = None
    ) -> Optional[AgentStateData]:
        """更新Agent状态"""
        existing = await self.storage.get_agent_state(agent_id)
        if not existing:
            return None
        
        existing.state = state
        existing.current_task = current_task
        existing.last_activity = datetime.now()
        
        await self.storage.save_agent_state(existing)
        
        return existing
    
    # === 统计和管理 ===
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        projects = await self.storage.list_projects()
        workflows = await self.storage.list_workflow_states()
        agents = await self.storage.list_agent_states()
        
        # 按状态统计项目
        project_by_status: Dict[str, int] = {}
        for p in projects:
            project_by_status[p.status] = project_by_status.get(p.status, 0) + 1
        
        # 按状态统计工作流
        workflow_by_status: Dict[str, int] = {}
        for w in workflows:
            workflow_by_status[w.status] = workflow_by_status.get(w.status, 0) + 1
        
        # 按状态统计Agent
        agent_by_state: Dict[str, int] = {}
        for a in agents:
            agent_by_state[a.state] = agent_by_state.get(a.state, 0) + 1
        
        return {
            "provider": self.config.provider.value,
            "total_projects": len(projects),
            "projects_by_status": project_by_status,
            "total_workflows": len(workflows),
            "workflows_by_status": workflow_by_status,
            "total_agents": len(agents),
            "agents_by_state": agent_by_state
        }


# 全局持久化服务实例
_persistence_service: Optional[PersistenceService] = None


def get_persistence_service() -> PersistenceService:
    """获取全局持久化服务实例"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = PersistenceService()
    return _persistence_service


def set_persistence_service(service: PersistenceService):
    """设置全局持久化服务实例"""
    global _persistence_service
    _persistence_service = service
