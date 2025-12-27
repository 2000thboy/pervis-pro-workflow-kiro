"""
PM Agent - 项目管理Agent

需求: 2.6 - WHEN 项目完成时 THEN PM_Agent SHALL 执行项目归档流程
需求: 7.1 - WHEN 项目创建时 THEN 系统 SHALL 自动创建标准化的项目文件夹结构
需求: 7.4 - WHEN 项目归档时 THEN PM_Agent SHALL 整理所有相关文件到归档目录

本模块实现项目管理Agent，负责项目生命周期管理、文件整理和归档功能。
新增版本管理功能（0-Fix.5）：版本记录、版本命名、用户决策记录。
"""
import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from .base_agent import BaseAgent
from ..core.message_bus import MessageBus, Message, Response
from ..core.communication_protocol import (
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
)
from ..core.agent_types import AgentType, AgentState

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """项目状态"""
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 活跃
    ON_HOLD = "on_hold"       # 暂停
    COMPLETED = "completed"   # 已完成
    ARCHIVED = "archived"     # 已归档


class ProjectPhase(Enum):
    """项目阶段"""
    SETUP = "setup"           # 立项阶段
    BEATBOARD = "beatboard"   # Beatboard阶段
    PREVIEW = "preview"       # 预演阶段
    REVIEW = "review"         # 审阅阶段
    EXPORT = "export"         # 导出阶段
    ARCHIVE = "archive"       # 归档阶段


@dataclass
class Project:
    """项目数据模型"""
    project_id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT
    phase: ProjectPhase = ProjectPhase.SETUP
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    archived_at: Optional[str] = None
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    folder_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "archived_at": self.archived_at,
            "owner": self.owner,
            "tags": self.tags,
            "metadata": self.metadata,
            "folder_path": self.folder_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            status=ProjectStatus(data.get("status", "draft")),
            phase=ProjectPhase(data.get("phase", "setup")),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            archived_at=data.get("archived_at"),
            owner=data.get("owner", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            folder_path=data.get("folder_path"),
        )


@dataclass
class ArchiveResult:
    """归档结果"""
    success: bool
    project_id: str
    archive_path: Optional[str] = None
    files_archived: int = 0
    total_size_bytes: int = 0
    error: Optional[str] = None
    archived_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "archive_path": self.archive_path,
            "files_archived": self.files_archived,
            "total_size_bytes": self.total_size_bytes,
            "error": self.error,
            "archived_at": self.archived_at,
        }


@dataclass
class ContentVersion:
    """
    内容版本记录（0-Fix.5）
    
    记录项目中各类内容的版本历史，支持版本命名规则。
    """
    version_id: str
    project_id: str
    content_type: str  # logline, synopsis, character_bio, scene, etc.
    entity_name: str   # 实体名称（如角色名、场次号）
    version_number: int
    content: Any
    source: str = "user"  # user, script_agent, art_agent, etc.
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_current: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "project_id": self.project_id,
            "content_type": self.content_type,
            "entity_name": self.entity_name,
            "version_number": self.version_number,
            "content": self.content,
            "source": self.source,
            "created_at": self.created_at,
            "is_current": self.is_current,
            "metadata": self.metadata,
        }
    
    @property
    def display_name(self) -> str:
        """生成显示名称，如：角色_张三_v1"""
        return f"{self.content_type}_{self.entity_name}_v{self.version_number}"
    
    @property
    def filename(self) -> str:
        """生成文件名，如：角色_张三_v1.json"""
        return f"{self.display_name}.json"


@dataclass
class UserDecision:
    """
    用户决策记录（0-Fix.5）
    
    记录用户对 Agent 生成内容的接受/拒绝决策。
    """
    decision_id: str
    project_id: str
    version_id: str  # 关联的版本ID
    decision_type: str  # accept, reject, modify
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "project_id": self.project_id,
            "version_id": self.version_id,
            "decision_type": self.decision_type,
            "reason": self.reason,
            "created_at": self.created_at,
            "user_id": self.user_id,
        }


# 标准项目文件夹结构
STANDARD_FOLDER_STRUCTURE = [
    "assets/images",
    "assets/videos",
    "assets/audio",
    "assets/documents",
    "scripts",
    "beatboards",
    "previews",
    "exports",
    "archive",
    "temp",
]


class PMAgent(BaseAgent):
    """
    项目管理Agent
    
    负责:
    - 项目生命周期管理
    - 项目文件夹结构创建
    - 项目归档和文件整理
    - 项目状态跟踪
    - 版本管理（0-Fix.5）：版本记录、版本命名、用户决策记录
    
    需求: 2.6, 7.1, 7.4
    """
    
    def __init__(
        self,
        message_bus: MessageBus,
        agent_id: str = "pm_agent",
        base_path: str = "./projects",
        archive_path: str = "./archive",
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PM,
            message_bus=message_bus,
            capabilities=[
                "project_management",
                "folder_creation",
                "file_organization",
                "project_archiving",
                "version_management",    # 0-Fix.5: 版本管理
                "decision_tracking",     # 0-Fix.5: 决策跟踪
            ]
        )
        
        self._base_path = Path(base_path)
        self._archive_path = Path(archive_path)
        self._projects: Dict[str, Project] = {}
        self._active_archives: Set[str] = set()
        
        # 0-Fix.5: 版本管理存储
        self._versions: Dict[str, ContentVersion] = {}  # version_id -> ContentVersion
        self._decisions: Dict[str, UserDecision] = {}   # decision_id -> UserDecision
        # 版本计数器：{project_id}_{content_type}_{entity_name} -> count
        self._version_counters: Dict[str, int] = {}
        
        logger.info(f"PMAgent初始化: base_path={base_path}, archive_path={archive_path}")
    
    async def _on_initialize(self):
        """初始化钩子"""
        # 确保基础目录存在
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._archive_path.mkdir(parents=True, exist_ok=True)
        
        # 注册消息处理器
        self.register_message_handler(
            ProtocolMessageType.TASK_REQUEST,
            self._handle_task_request
        )
        
        logger.info("PMAgent初始化完成")
    
    async def _on_start(self):
        """启动钩子"""
        # 订阅项目相关主题
        sub_id = await self._message_bus.subscribe(
            self._agent_id,
            "project.*",
            self._handle_message
        )
        self._subscription_ids.add(sub_id)
        
        logger.info("PMAgent启动完成")
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        content = message.content
        action = content.get("action", "")
        
        if action == "create_project":
            result = await self.create_project(
                project_id=content.get("project_id", ""),
                name=content.get("name", ""),
                description=content.get("description", ""),
                owner=content.get("owner", ""),
                tags=content.get("tags", []),
            )
            return Response(
                success=result is not None,
                message_id=message.id,
                data=result.to_dict() if result else None,
            )
        
        elif action == "archive_project":
            result = await self.archive_project(content.get("project_id", ""))
            return Response(
                success=result.success,
                message_id=message.id,
                data=result.to_dict(),
                error=result.error,
            )
        
        elif action == "get_project":
            project = self.get_project(content.get("project_id", ""))
            return Response(
                success=project is not None,
                message_id=message.id,
                data=project.to_dict() if project else None,
            )
        
        elif action == "list_projects":
            projects = self.list_projects(
                status=content.get("status"),
                phase=content.get("phase"),
            )
            return Response(
                success=True,
                message_id=message.id,
                data={"projects": [p.to_dict() for p in projects]},
            )
        
        return None
    
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        data = message.payload.data
        
        if msg_type == ProtocolMessageType.TASK_REQUEST:
            return await self._handle_task_request(message)
        
        return message.create_response(
            ProtocolStatus.NOT_FOUND,
            error=f"未知的消息类型: {msg_type.value}"
        )
    
    async def _handle_task_request(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理任务请求"""
        data = message.payload.data
        task_type = data.get("task_type", "")
        
        if task_type == "create_project":
            result = await self.create_project(
                project_id=data.get("project_id", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                owner=data.get("owner", ""),
                tags=data.get("tags", []),
            )
            return message.create_response(
                ProtocolStatus.SUCCESS if result else ProtocolStatus.INTERNAL_ERROR,
                data=result.to_dict() if result else None,
            )
        
        elif task_type == "archive_project":
            result = await self.archive_project(data.get("project_id", ""))
            return message.create_response(
                ProtocolStatus.SUCCESS if result.success else ProtocolStatus.INTERNAL_ERROR,
                data=result.to_dict(),
                error=result.error,
            )
        
        return message.create_response(
            ProtocolStatus.BAD_REQUEST,
            error=f"未知的任务类型: {task_type}"
        )

    # ========================================================================
    # 项目管理功能
    # ========================================================================
    
    async def create_project(
        self,
        project_id: str,
        name: str,
        description: str = "",
        owner: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Project]:
        """
        创建新项目
        
        需求: 7.1 - WHEN 项目创建时 THEN 系统 SHALL 自动创建标准化的项目文件夹结构
        
        Args:
            project_id: 项目ID
            name: 项目名称
            description: 项目描述
            owner: 项目所有者
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            创建的项目对象，失败返回None
        """
        if not project_id or not name:
            logger.error("创建项目失败: project_id和name不能为空")
            return None
        
        if project_id in self._projects:
            logger.error(f"创建项目失败: 项目ID已存在 {project_id}")
            return None
        
        await self.update_work_state(AgentState.WORKING, f"创建项目: {name}")
        
        try:
            # 创建项目文件夹
            project_path = self._base_path / project_id
            folder_created = self._create_folder_structure(project_path)
            
            if not folder_created:
                logger.error(f"创建项目文件夹失败: {project_path}")
                return None
            
            # 创建项目对象
            project = Project(
                project_id=project_id,
                name=name,
                description=description,
                status=ProjectStatus.DRAFT,
                phase=ProjectPhase.SETUP,
                owner=owner,
                tags=tags or [],
                metadata=metadata or {},
                folder_path=str(project_path),
            )
            
            self._projects[project_id] = project
            
            self._log_operation(
                "project_created",
                details={
                    "project_id": project_id,
                    "name": name,
                    "folder_path": str(project_path),
                }
            )
            
            logger.info(f"项目创建成功: {project_id} - {name}")
            
            # 广播项目创建事件
            await self.broadcast_message(
                ProtocolMessageType.AGENT_STATUS,
                {
                    "event": "project_created",
                    "project": project.to_dict(),
                }
            )
            
            return project
            
        except Exception as e:
            logger.error(f"创建项目异常: {e}")
            self._log_operation(
                "project_creation_failed",
                success=False,
                error=str(e),
            )
            return None
        
        finally:
            await self.update_work_state(AgentState.IDLE)
    
    def _create_folder_structure(self, project_path: Path) -> bool:
        """
        创建标准化项目文件夹结构
        
        需求: 7.1 - 自动创建标准化的项目文件夹结构
        
        Args:
            project_path: 项目根目录
            
        Returns:
            是否创建成功
        """
        try:
            for folder in STANDARD_FOLDER_STRUCTURE:
                folder_path = project_path / folder
                folder_path.mkdir(parents=True, exist_ok=True)
            
            # 创建项目配置文件
            config_file = project_path / "project.json"
            if not config_file.exists():
                config_file.write_text("{}")
            
            logger.debug(f"项目文件夹结构创建完成: {project_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建文件夹结构失败: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self._projects.get(project_id)
    
    def list_projects(
        self,
        status: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> List[Project]:
        """
        列出项目
        
        Args:
            status: 状态过滤
            phase: 阶段过滤
            
        Returns:
            项目列表
        """
        projects = list(self._projects.values())
        
        if status:
            try:
                status_enum = ProjectStatus(status)
                projects = [p for p in projects if p.status == status_enum]
            except ValueError:
                pass
        
        if phase:
            try:
                phase_enum = ProjectPhase(phase)
                projects = [p for p in projects if p.phase == phase_enum]
            except ValueError:
                pass
        
        return projects
    
    async def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
    ) -> bool:
        """更新项目状态"""
        project = self._projects.get(project_id)
        if not project:
            return False
        
        old_status = project.status
        project.status = status
        project.updated_at = datetime.utcnow().isoformat()
        
        self._log_operation(
            "project_status_updated",
            state_before=old_status.value,
            state_after=status.value,
            details={"project_id": project_id},
        )
        
        return True
    
    async def update_project_phase(
        self,
        project_id: str,
        phase: ProjectPhase,
    ) -> bool:
        """更新项目阶段"""
        project = self._projects.get(project_id)
        if not project:
            return False
        
        old_phase = project.phase
        project.phase = phase
        project.updated_at = datetime.utcnow().isoformat()
        
        self._log_operation(
            "project_phase_updated",
            state_before=old_phase.value,
            state_after=phase.value,
            details={"project_id": project_id},
        )
        
        return True
    
    # ========================================================================
    # 项目归档功能
    # ========================================================================
    
    async def archive_project(self, project_id: str) -> ArchiveResult:
        """
        归档项目
        
        需求: 2.6 - WHEN 项目完成时 THEN PM_Agent SHALL 执行项目归档流程
        需求: 7.4 - WHEN 项目归档时 THEN PM_Agent SHALL 整理所有相关文件到归档目录
        
        Args:
            project_id: 项目ID
            
        Returns:
            归档结果
        """
        project = self._projects.get(project_id)
        if not project:
            return ArchiveResult(
                success=False,
                project_id=project_id,
                error=f"项目不存在: {project_id}",
            )
        
        if project_id in self._active_archives:
            return ArchiveResult(
                success=False,
                project_id=project_id,
                error="项目正在归档中",
            )
        
        if project.status == ProjectStatus.ARCHIVED:
            return ArchiveResult(
                success=False,
                project_id=project_id,
                error="项目已归档",
            )
        
        self._active_archives.add(project_id)
        await self.update_work_state(AgentState.WORKING, f"归档项目: {project.name}")
        
        try:
            # 创建归档目录
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{project_id}_{timestamp}"
            archive_dir = self._archive_path / archive_name
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制项目文件到归档目录
            source_path = Path(project.folder_path) if project.folder_path else None
            files_archived = 0
            total_size = 0
            
            if source_path and source_path.exists():
                files_archived, total_size = self._copy_files_to_archive(
                    source_path, archive_dir
                )
            
            # 更新项目状态
            project.status = ProjectStatus.ARCHIVED
            project.phase = ProjectPhase.ARCHIVE
            project.archived_at = datetime.utcnow().isoformat()
            project.updated_at = project.archived_at
            
            result = ArchiveResult(
                success=True,
                project_id=project_id,
                archive_path=str(archive_dir),
                files_archived=files_archived,
                total_size_bytes=total_size,
                archived_at=project.archived_at,
            )
            
            self._log_operation(
                "project_archived",
                details={
                    "project_id": project_id,
                    "archive_path": str(archive_dir),
                    "files_archived": files_archived,
                    "total_size_bytes": total_size,
                }
            )
            
            logger.info(f"项目归档成功: {project_id} -> {archive_dir}")
            
            # 广播归档完成事件
            await self.broadcast_message(
                ProtocolMessageType.AGENT_STATUS,
                {
                    "event": "project_archived",
                    "result": result.to_dict(),
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"项目归档失败: {e}")
            self._log_operation(
                "project_archive_failed",
                success=False,
                error=str(e),
                details={"project_id": project_id},
            )
            return ArchiveResult(
                success=False,
                project_id=project_id,
                error=str(e),
            )
        
        finally:
            self._active_archives.discard(project_id)
            await self.update_work_state(AgentState.IDLE)
    
    def _copy_files_to_archive(
        self,
        source: Path,
        destination: Path,
    ) -> tuple[int, int]:
        """
        复制文件到归档目录
        
        Args:
            source: 源目录
            destination: 目标目录
            
        Returns:
            (文件数量, 总大小)
        """
        files_count = 0
        total_size = 0
        
        try:
            for item in source.rglob("*"):
                if item.is_file():
                    # 计算相对路径
                    rel_path = item.relative_to(source)
                    dest_file = destination / rel_path
                    
                    # 创建目标目录
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(item, dest_file)
                    
                    files_count += 1
                    total_size += item.stat().st_size
            
            return files_count, total_size
            
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return files_count, total_size
    
    def get_archive_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取归档信息"""
        project = self._projects.get(project_id)
        if not project or project.status != ProjectStatus.ARCHIVED:
            return None
        
        return {
            "project_id": project_id,
            "archived_at": project.archived_at,
            "status": project.status.value,
        }
    
    # ========================================================================
    # 文件整理功能
    # ========================================================================
    
    async def organize_project_files(self, project_id: str) -> bool:
        """
        整理项目文件
        
        将项目中的文件按类型整理到对应的文件夹
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否整理成功
        """
        project = self._projects.get(project_id)
        if not project or not project.folder_path:
            return False
        
        await self.update_work_state(AgentState.WORKING, f"整理文件: {project.name}")
        
        try:
            project_path = Path(project.folder_path)
            
            # 文件类型映射
            type_mapping = {
                ".jpg": "assets/images",
                ".jpeg": "assets/images",
                ".png": "assets/images",
                ".gif": "assets/images",
                ".mp4": "assets/videos",
                ".mov": "assets/videos",
                ".avi": "assets/videos",
                ".mp3": "assets/audio",
                ".wav": "assets/audio",
                ".pdf": "assets/documents",
                ".doc": "assets/documents",
                ".docx": "assets/documents",
                ".txt": "scripts",
            }
            
            # 整理根目录下的文件
            for item in project_path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in type_mapping:
                        dest_folder = project_path / type_mapping[ext]
                        dest_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(item), str(dest_folder / item.name))
            
            self._log_operation(
                "files_organized",
                details={"project_id": project_id},
            )
            
            return True
            
        except Exception as e:
            logger.error(f"文件整理失败: {e}")
            return False
        
        finally:
            await self.update_work_state(AgentState.IDLE)
    
    def validate_project_structure(self, project_id: str) -> Dict[str, Any]:
        """
        验证项目文件夹结构
        
        Args:
            project_id: 项目ID
            
        Returns:
            验证结果
        """
        project = self._projects.get(project_id)
        if not project or not project.folder_path:
            return {"valid": False, "error": "项目不存在或无文件夹"}
        
        project_path = Path(project.folder_path)
        missing_folders = []
        existing_folders = []
        
        for folder in STANDARD_FOLDER_STRUCTURE:
            folder_path = project_path / folder
            if folder_path.exists():
                existing_folders.append(folder)
            else:
                missing_folders.append(folder)
        
        return {
            "valid": len(missing_folders) == 0,
            "project_id": project_id,
            "existing_folders": existing_folders,
            "missing_folders": missing_folders,
            "completeness": len(existing_folders) / len(STANDARD_FOLDER_STRUCTURE),
        }
    
    # ========================================================================
    # 版本管理功能（0-Fix.5）
    # ========================================================================
    
    def generate_version_name(
        self,
        content_type: str,
        entity_name: str,
        version_number: int
    ) -> str:
        """
        生成版本命名（0-Fix.5）
        
        生成格式：{content_type}_{entity_name}_v{version_number}
        例如：角色_张三_v1
        
        Args:
            content_type: 内容类型（角色、场次、logline 等）
            entity_name: 实体名称（角色名、场次号等）
            version_number: 版本号
        
        Returns:
            版本名称字符串
        """
        # 清理实体名称中的特殊字符
        safe_name = "".join(c for c in entity_name if c.isalnum() or c in "_-")
        if not safe_name:
            safe_name = "unnamed"
        
        return f"{content_type}_{safe_name}_v{version_number}"
    
    def record_version(
        self,
        project_id: str,
        content_type: str,
        entity_name: str,
        content: Any,
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentVersion:
        """
        记录版本（0-Fix.5）
        
        为项目中的内容创建新版本记录。
        
        Args:
            project_id: 项目ID
            content_type: 内容类型（logline, synopsis, character_bio, scene 等）
            entity_name: 实体名称（角色名、场次号等）
            content: 内容数据
            source: 来源（user, script_agent, art_agent 等）
            metadata: 额外元数据
        
        Returns:
            创建的 ContentVersion 对象
        """
        # 生成版本计数器键
        counter_key = f"{project_id}_{content_type}_{entity_name}"
        
        # 获取并递增版本号
        current_count = self._version_counters.get(counter_key, 0)
        new_version_number = current_count + 1
        self._version_counters[counter_key] = new_version_number
        
        # 将之前的版本标记为非当前
        for v in self._versions.values():
            if (v.project_id == project_id and 
                v.content_type == content_type and 
                v.entity_name == entity_name and
                v.is_current):
                v.is_current = False
        
        # 生成版本ID
        version_id = f"{project_id}_{content_type}_{entity_name}_v{new_version_number}"
        
        # 创建版本记录
        version = ContentVersion(
            version_id=version_id,
            project_id=project_id,
            content_type=content_type,
            entity_name=entity_name,
            version_number=new_version_number,
            content=content,
            source=source,
            is_current=True,
            metadata=metadata or {}
        )
        
        self._versions[version_id] = version
        
        self._log_operation(
            "version_recorded",
            details={
                "version_id": version_id,
                "project_id": project_id,
                "content_type": content_type,
                "entity_name": entity_name,
                "version_number": new_version_number,
                "source": source
            }
        )
        
        logger.info(f"记录版本: {version.display_name}")
        
        return version
    
    def record_decision(
        self,
        project_id: str,
        version_id: str,
        decision_type: str,
        reason: str = "",
        user_id: str = ""
    ) -> UserDecision:
        """
        记录用户决策（0-Fix.5）
        
        记录用户对某个版本的接受/拒绝决策。
        
        Args:
            project_id: 项目ID
            version_id: 版本ID
            decision_type: 决策类型（accept, reject, modify）
            reason: 决策原因
            user_id: 用户ID
        
        Returns:
            创建的 UserDecision 对象
        """
        # 生成决策ID
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        decision_id = f"decision_{project_id}_{timestamp}"
        
        decision = UserDecision(
            decision_id=decision_id,
            project_id=project_id,
            version_id=version_id,
            decision_type=decision_type,
            reason=reason,
            user_id=user_id
        )
        
        self._decisions[decision_id] = decision
        
        self._log_operation(
            "decision_recorded",
            details={
                "decision_id": decision_id,
                "project_id": project_id,
                "version_id": version_id,
                "decision_type": decision_type,
                "reason": reason
            }
        )
        
        logger.info(f"记录决策: {decision_type} for {version_id}")
        
        return decision
    
    def get_version_display_info(
        self,
        project_id: str,
        content_type: Optional[str] = None,
        entity_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取版本显示信息（0-Fix.5）
        
        获取项目的版本历史信息，用于前端显示。
        
        Args:
            project_id: 项目ID
            content_type: 内容类型过滤（可选）
            entity_name: 实体名称过滤（可选）
        
        Returns:
            版本显示信息：
            {
                "project_id": "xxx",
                "total_versions": 10,
                "current_versions": [...],
                "version_history": [...],
                "decisions": [...]
            }
        """
        # 过滤版本
        versions = [
            v for v in self._versions.values()
            if v.project_id == project_id
        ]
        
        if content_type:
            versions = [v for v in versions if v.content_type == content_type]
        
        if entity_name:
            versions = [v for v in versions if v.entity_name == entity_name]
        
        # 分离当前版本和历史版本
        current_versions = [v for v in versions if v.is_current]
        history_versions = [v for v in versions if not v.is_current]
        
        # 按时间排序
        history_versions.sort(key=lambda v: v.created_at, reverse=True)
        
        # 获取相关决策
        decisions = [
            d for d in self._decisions.values()
            if d.project_id == project_id
        ]
        decisions.sort(key=lambda d: d.created_at, reverse=True)
        
        return {
            "project_id": project_id,
            "total_versions": len(versions),
            "current_versions": [v.to_dict() for v in current_versions],
            "version_history": [v.to_dict() for v in history_versions[:20]],  # 最近20条
            "decisions": [d.to_dict() for d in decisions[:20]],  # 最近20条
            "filters": {
                "content_type": content_type,
                "entity_name": entity_name
            }
        }
    
    def get_version(self, version_id: str) -> Optional[ContentVersion]:
        """获取指定版本"""
        return self._versions.get(version_id)
    
    def get_current_version(
        self,
        project_id: str,
        content_type: str,
        entity_name: str
    ) -> Optional[ContentVersion]:
        """获取当前版本"""
        for v in self._versions.values():
            if (v.project_id == project_id and
                v.content_type == content_type and
                v.entity_name == entity_name and
                v.is_current):
                return v
        return None
    
    def get_version_history(
        self,
        project_id: str,
        content_type: str,
        entity_name: str
    ) -> List[ContentVersion]:
        """获取版本历史"""
        versions = [
            v for v in self._versions.values()
            if (v.project_id == project_id and
                v.content_type == content_type and
                v.entity_name == entity_name)
        ]
        versions.sort(key=lambda v: v.version_number, reverse=True)
        return versions
    
    def restore_version(self, version_id: str) -> Optional[ContentVersion]:
        """
        恢复到指定版本
        
        将指定版本设为当前版本。
        
        Args:
            version_id: 要恢复的版本ID
        
        Returns:
            恢复后的版本，如果失败返回 None
        """
        version = self._versions.get(version_id)
        if not version:
            return None
        
        # 将同类型的其他版本标记为非当前
        for v in self._versions.values():
            if (v.project_id == version.project_id and
                v.content_type == version.content_type and
                v.entity_name == version.entity_name):
                v.is_current = False
        
        # 将目标版本设为当前
        version.is_current = True
        
        self._log_operation(
            "version_restored",
            details={
                "version_id": version_id,
                "project_id": version.project_id,
                "content_type": version.content_type,
                "entity_name": version.entity_name
            }
        )
        
        logger.info(f"恢复版本: {version.display_name}")
        
        return version
    
    def save_version_to_file(
        self,
        version_id: str,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        将版本保存到文件
        
        Args:
            version_id: 版本ID
            output_dir: 输出目录（可选，默认使用项目目录）
        
        Returns:
            保存的文件路径，如果失败返回 None
        """
        version = self._versions.get(version_id)
        if not version:
            return None
        
        # 确定输出目录
        if output_dir:
            out_path = Path(output_dir)
        else:
            project = self._projects.get(version.project_id)
            if project and project.folder_path:
                out_path = Path(project.folder_path) / "versions"
            else:
                out_path = self._base_path / version.project_id / "versions"
        
        out_path.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = out_path / version.filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(version.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"版本保存到文件: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"保存版本文件失败: {e}")
            return None
    
    def provide_context_to_director(
        self,
        project_id: str,
        content_type: str,
        entity_name: str
    ) -> Dict[str, Any]:
        """
        为 Director_Agent 提供历史对比数据（0-Fix.5）
        
        Args:
            project_id: 项目ID
            content_type: 内容类型
            entity_name: 实体名称
        
        Returns:
            历史对比数据
        """
        # 获取版本历史
        versions = self.get_version_history(project_id, content_type, entity_name)
        
        # 获取相关决策
        version_ids = {v.version_id for v in versions}
        decisions = [
            d for d in self._decisions.values()
            if d.version_id in version_ids
        ]
        
        # 分析被拒绝的版本
        rejected_versions = []
        for d in decisions:
            if d.decision_type == "reject":
                v = self._versions.get(d.version_id)
                if v:
                    rejected_versions.append({
                        "version": v.to_dict(),
                        "reason": d.reason,
                        "rejected_at": d.created_at
                    })
        
        return {
            "project_id": project_id,
            "content_type": content_type,
            "entity_name": entity_name,
            "total_versions": len(versions),
            "current_version": versions[0].to_dict() if versions else None,
            "rejected_versions": rejected_versions,
            "decision_count": len(decisions),
            "accept_count": len([d for d in decisions if d.decision_type == "accept"]),
            "reject_count": len([d for d in decisions if d.decision_type == "reject"])
        }
