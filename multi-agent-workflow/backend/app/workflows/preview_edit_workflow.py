# -*- coding: utf-8 -*-
"""
Preview Edit Workflow - 预演剪辑工作流

实现预演生成、多端同步和剪辑预览功能
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


class PreviewStatus(Enum):
    """预演状态"""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class SyncStatus(Enum):
    """同步状态"""
    SYNCED = "synced"
    SYNCING = "syncing"
    OUT_OF_SYNC = "out_of_sync"
    ERROR = "error"


class ClientType(Enum):
    """客户端类型"""
    WEB = "web"
    DESKTOP = "desktop"
    MOBILE = "mobile"


@dataclass
class TimelineClip:
    """时间线片段"""
    id: str
    asset_id: str
    start_time: float  # 秒
    end_time: float    # 秒
    duration: float    # 秒
    track: int
    clip_type: str     # video, audio, image
    transitions: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "track": self.track,
            "clip_type": self.clip_type,
            "transitions": self.transitions,
            "effects": self.effects,
            "metadata": self.metadata,
        }


@dataclass
class Timeline:
    """时间线"""
    id: str
    project_id: str
    name: str
    clips: List[TimelineClip] = field(default_factory=list)
    total_duration: float = 0.0
    frame_rate: float = 24.0
    resolution: str = "1920x1080"
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "clips": [c.to_dict() for c in self.clips],
            "total_duration": self.total_duration,
            "frame_rate": self.frame_rate,
            "resolution": self.resolution,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PreviewSession:
    """预演会话"""
    id: str
    timeline_id: str
    status: PreviewStatus = PreviewStatus.PENDING
    current_time: float = 0.0
    playback_speed: float = 1.0
    connected_clients: List[str] = field(default_factory=list)
    sync_status: SyncStatus = SyncStatus.SYNCED
    preview_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timeline_id": self.timeline_id,
            "status": self.status.value,
            "current_time": self.current_time,
            "playback_speed": self.playback_speed,
            "connected_clients": self.connected_clients,
            "sync_status": self.sync_status.value,
            "preview_url": self.preview_url,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ClientConnection:
    """客户端连接"""
    id: str
    client_type: ClientType
    session_id: str
    connected_at: datetime = field(default_factory=datetime.now)
    last_sync: datetime = field(default_factory=datetime.now)
    sync_status: SyncStatus = SyncStatus.SYNCED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_type": self.client_type.value,
            "session_id": self.session_id,
            "connected_at": self.connected_at.isoformat(),
            "last_sync": self.last_sync.isoformat(),
            "sync_status": self.sync_status.value,
        }


class PreviewEditWorkflow:
    """预演剪辑工作流"""
    
    WORKFLOW_ID = "preview_edit"
    WORKFLOW_NAME = "预演剪辑工作流"
    
    def __init__(
        self,
        engine: WorkflowEngine,
        preview_generator: Optional[Callable] = None
    ):
        self.engine = engine
        self.preview_generator = preview_generator or self._default_preview_generator
        self._timelines: Dict[str, Timeline] = {}
        self._sessions: Dict[str, PreviewSession] = {}
        self._clients: Dict[str, ClientConnection] = {}
        
        # 注册工作流
        self._register_workflow()
    
    def _register_workflow(self) -> None:
        """注册预演剪辑工作流"""
        workflow = WorkflowDefinition(
            id=self.WORKFLOW_ID,
            name=self.WORKFLOW_NAME,
            description="预演剪辑流程，包括时间线创建、预演生成、多端同步"
        )
        
        # Step 1: 创建时间线
        step1 = WorkflowStep(
            id="create_timeline",
            name="创建时间线",
            step_type=StepType.TASK,
            handler=self._create_timeline_handler,
            next_steps=["generate_preview"]
        )
        
        # Step 2: 生成预演
        step2 = WorkflowStep(
            id="generate_preview",
            name="生成预演",
            step_type=StepType.TASK,
            handler=self._generate_preview_handler,
            next_steps=["setup_sync"]
        )
        
        # Step 3: 设置同步
        step3 = WorkflowStep(
            id="setup_sync",
            name="设置多端同步",
            step_type=StepType.TASK,
            handler=self._setup_sync_handler,
            next_steps=["user_review"]
        )
        
        # Step 4: 用户审核
        step4 = WorkflowStep(
            id="user_review",
            name="用户审核预演",
            step_type=StepType.WAIT,
            next_steps=["finalize_preview"]
        )
        
        # Step 5: 完成预演
        step5 = WorkflowStep(
            id="finalize_preview",
            name="完成预演",
            step_type=StepType.TASK,
            handler=self._finalize_preview_handler
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        workflow.add_step(step5)
        
        self.engine.register_workflow(workflow)
    
    # 步骤处理器
    async def _create_timeline_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建时间线"""
        project_id = context.get("project_id", str(uuid.uuid4()))
        timeline_name = context.get("timeline_name", "默认时间线")
        clips_data = context.get("clips", [])
        
        timeline_id = str(uuid.uuid4())
        timeline = Timeline(
            id=timeline_id,
            project_id=project_id,
            name=timeline_name,
            frame_rate=context.get("frame_rate", 24.0),
            resolution=context.get("resolution", "1920x1080"),
        )
        
        # 添加片段
        total_duration = 0.0
        for i, clip_data in enumerate(clips_data):
            clip = TimelineClip(
                id=str(uuid.uuid4()),
                asset_id=clip_data.get("asset_id", ""),
                start_time=clip_data.get("start_time", total_duration),
                end_time=clip_data.get("end_time", total_duration + clip_data.get("duration", 5.0)),
                duration=clip_data.get("duration", 5.0),
                track=clip_data.get("track", 0),
                clip_type=clip_data.get("clip_type", "video"),
            )
            timeline.clips.append(clip)
            total_duration = max(total_duration, clip.end_time)
        
        timeline.total_duration = total_duration
        self._timelines[timeline_id] = timeline
        
        return {
            "timeline_id": timeline_id,
            "timeline": timeline.to_dict(),
            "timeline_status": "created"
        }

    
    async def _generate_preview_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成预演"""
        timeline_id = context.get("timeline_id")
        timeline = self._timelines.get(timeline_id)
        
        if not timeline:
            return {"preview_status": "error", "error": "Timeline not found"}
        
        # 创建预演会话
        session_id = str(uuid.uuid4())
        session = PreviewSession(
            id=session_id,
            timeline_id=timeline_id,
            status=PreviewStatus.GENERATING,
        )
        
        # 生成预演
        preview_result = await self.preview_generator(timeline)
        
        session.status = PreviewStatus.READY
        session.preview_url = preview_result.get("preview_url")
        self._sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "session": session.to_dict(),
            "preview_status": "ready",
            "preview_url": session.preview_url,
        }
    
    async def _setup_sync_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """设置多端同步"""
        session_id = context.get("session_id")
        session = self._sessions.get(session_id)
        
        if not session:
            return {"sync_status": "error", "error": "Session not found"}
        
        # 初始化同步状态
        session.sync_status = SyncStatus.SYNCED
        
        return {
            "sync_enabled": True,
            "sync_status": "ready",
            "session_id": session_id,
        }
    
    async def _finalize_preview_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """完成预演"""
        session_id = context.get("session_id")
        user_approved = context.get("user_approved", True)
        
        session = self._sessions.get(session_id)
        if not session:
            return {"finalize_status": "error", "error": "Session not found"}
        
        if user_approved:
            session.status = PreviewStatus.COMPLETED
            return {
                "finalize_status": "completed",
                "session_id": session_id,
            }
        else:
            session.status = PreviewStatus.ERROR
            return {
                "finalize_status": "rejected",
                "session_id": session_id,
            }
    
    # 默认预演生成器
    async def _default_preview_generator(self, timeline: Timeline) -> Dict[str, Any]:
        """默认预演生成器"""
        return {
            "preview_url": f"/preview/{timeline.id}",
            "duration": timeline.total_duration,
            "format": "mp4",
        }

    
    # 公共API
    async def start_preview_session(
        self,
        project_id: str,
        timeline_name: str = "默认时间线",
        clips: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[WorkflowInstance]:
        """启动预演会话"""
        instance = await self.engine.create_instance(
            self.WORKFLOW_ID,
            context={
                "project_id": project_id,
                "timeline_name": timeline_name,
                "clips": clips or [],
            }
        )
        
        if instance:
            await self.engine.start_instance(instance.id)
        
        return instance
    
    async def approve_preview(self, instance_id: str) -> bool:
        """审核通过预演"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": True}
        )
    
    async def reject_preview(self, instance_id: str) -> bool:
        """拒绝预演"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": False}
        )
    
    # 客户端连接管理
    def connect_client(
        self,
        session_id: str,
        client_type: ClientType
    ) -> Optional[ClientConnection]:
        """连接客户端"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        client_id = str(uuid.uuid4())
        client = ClientConnection(
            id=client_id,
            client_type=client_type,
            session_id=session_id,
        )
        
        self._clients[client_id] = client
        session.connected_clients.append(client_id)
        
        return client
    
    def disconnect_client(self, client_id: str) -> bool:
        """断开客户端"""
        client = self._clients.get(client_id)
        if not client:
            return False
        
        session = self._sessions.get(client.session_id)
        if session and client_id in session.connected_clients:
            session.connected_clients.remove(client_id)
        
        del self._clients[client_id]
        return True
    
    def sync_client(self, client_id: str) -> bool:
        """同步客户端"""
        client = self._clients.get(client_id)
        if not client:
            return False
        
        client.last_sync = datetime.now()
        client.sync_status = SyncStatus.SYNCED
        return True
    
    # 时间线操作
    def get_timeline(self, timeline_id: str) -> Optional[Timeline]:
        """获取时间线"""
        return self._timelines.get(timeline_id)
    
    def update_timeline(self, timeline_id: str, updates: Dict[str, Any]) -> bool:
        """更新时间线"""
        timeline = self._timelines.get(timeline_id)
        if not timeline:
            return False
        
        if "name" in updates:
            timeline.name = updates["name"]
        if "frame_rate" in updates:
            timeline.frame_rate = updates["frame_rate"]
        if "resolution" in updates:
            timeline.resolution = updates["resolution"]
        
        timeline.version += 1
        timeline.updated_at = datetime.now()
        
        # 标记所有连接的客户端需要同步
        for session in self._sessions.values():
            if session.timeline_id == timeline_id:
                session.sync_status = SyncStatus.OUT_OF_SYNC
        
        return True
    
    # 会话管理
    def get_session(self, session_id: str) -> Optional[PreviewSession]:
        """获取预演会话"""
        return self._sessions.get(session_id)
    
    def list_sessions(self, timeline_id: Optional[str] = None) -> List[PreviewSession]:
        """列出预演会话"""
        sessions = list(self._sessions.values())
        if timeline_id:
            sessions = [s for s in sessions if s.timeline_id == timeline_id]
        return sessions
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        sessions = list(self._sessions.values())
        return {
            "total_timelines": len(self._timelines),
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.status == PreviewStatus.READY]),
            "total_clients": len(self._clients),
        }
