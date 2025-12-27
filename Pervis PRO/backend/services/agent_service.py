# -*- coding: utf-8 -*-
"""
Agent 服务层

Feature: pervis-project-wizard Phase 2
Task: 2.1 创建 AgentService 基础架构

提供 Agent 任务调度和状态管理：
- Agent 工作流程（执行 → 审核 → 返回）
- 内容来源标记（用户输入/Script_Agent/Art_Agent）
- 任务状态管理

Requirements: 5.5, 5.7, 5.9, 9.1
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentTaskStatus(str, Enum):
    """Agent 任务状态"""
    PENDING = "pending"
    WORKING = "working"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentSource(str, Enum):
    """内容来源"""
    USER = "user"
    SCRIPT_AGENT = "script_agent"
    ART_AGENT = "art_agent"
    DIRECTOR_AGENT = "director_agent"
    MARKET_AGENT = "market_agent"
    STORYBOARD_AGENT = "storyboard_agent"
    SYSTEM_AGENT = "system_agent"


@dataclass
class AgentTask:
    """Agent 任务"""
    task_id: str
    task_type: str
    agent_type: str
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    progress: float = 0.0
    message: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    review_result: Optional[Dict[str, Any]] = None
    source: ContentSource = ContentSource.USER
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "review_result": self.review_result,
            "source": self.source.value,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class ReviewResult:
    """审核结果"""
    status: str  # approved, suggestions, rejected
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0


class AgentService:
    """
    Agent 服务层
    
    管理 Agent 工作流程：
    1. 接收任务请求
    2. 分配给对应 Agent 执行
    3. Director_Agent 审核
    4. 返回结果
    """
    
    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}
        self._llm_adapter = None
        self._callbacks: Dict[str, List[Callable]] = {}
        self._event_service = None
    
    def _get_event_service(self):
        """延迟加载 EventService"""
        if self._event_service is None:
            try:
                from services.event_service import event_service
                self._event_service = event_service
            except Exception as e:
                logger.warning(f"EventService 加载失败: {e}")
        return self._event_service
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    def create_task(
        self,
        task_type: str,
        agent_type: str,
        input_data: Dict[str, Any] = None
    ) -> AgentTask:
        """创建任务"""
        task = AgentTask(
            task_id=f"task_{uuid4().hex[:12]}",
            task_type=task_type,
            agent_type=agent_type,
            input_data=input_data or {}
        )
        self._tasks[task.task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: AgentTaskStatus = None,
        progress: float = None,
        message: str = None,
        result: Any = None,
        error: str = None
    ):
        """更新任务状态"""
        task = self._tasks.get(task_id)
        if task:
            if status:
                task.status = status
            if progress is not None:
                task.progress = progress
            if message:
                task.message = message
            if result is not None:
                task.result = result
            if error:
                task.error = error
            task.updated_at = datetime.now()
            
            if status == AgentTaskStatus.COMPLETED:
                task.completed_at = datetime.now()
            
            # 触发回调
            self._trigger_callbacks(task_id, task)
            
            # 发送 WebSocket 事件
            self._emit_task_event(task)
    
    def register_callback(self, task_id: str, callback: Callable):
        """注册任务回调"""
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)
    
    def _trigger_callbacks(self, task_id: str, task: AgentTask):
        """触发回调"""
        for callback in self._callbacks.get(task_id, []):
            try:
                callback(task)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    def _emit_task_event(self, task: AgentTask):
        """发送任务事件到 WebSocket"""
        event_service = self._get_event_service()
        if not event_service:
            return
        
        try:
            # 使用 asyncio 在后台发送事件
            import asyncio
            
            async def emit():
                if task.status == AgentTaskStatus.WORKING:
                    await event_service.emit_agent_status(
                        agent_type=task.agent_type,
                        status="working",
                        message=task.message or f"{task.agent_type} 正在工作...",
                        task_id=task.task_id
                    )
                elif task.status == AgentTaskStatus.REVIEWING:
                    await event_service.emit_agent_status(
                        agent_type="director_agent",
                        status="reviewing",
                        message="Director_Agent 审核中...",
                        task_id=task.task_id
                    )
                elif task.status == AgentTaskStatus.COMPLETED:
                    await event_service.emit_agent_status(
                        agent_type=task.agent_type,
                        status="completed",
                        message=task.message or "任务完成",
                        task_id=task.task_id
                    )
                elif task.status == AgentTaskStatus.FAILED:
                    await event_service.emit_agent_status(
                        agent_type=task.agent_type,
                        status="failed",
                        message=task.error or "任务失败",
                        task_id=task.task_id
                    )
            
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(emit())
            except RuntimeError:
                # 没有运行中的事件循环，创建新的
                asyncio.run(emit())
                
        except Exception as e:
            logger.warning(f"发送任务事件失败: {e}")
    
    async def execute_task(
        self,
        task_type: str,
        agent_type: str,
        input_data: Dict[str, Any],
        skip_review: bool = False
    ) -> AgentTask:
        """
        执行 Agent 任务
        
        工作流程：
        1. 创建任务
        2. Agent 执行
        3. Director_Agent 审核（可选）
        4. 返回结果
        """
        # 创建任务
        task = self.create_task(task_type, agent_type, input_data)
        
        try:
            # 更新状态：工作中
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.WORKING,
                progress=0.1,
                message=f"{agent_type} 正在工作..."
            )
            
            # 执行任务
            result = await self._execute_agent_task(task)
            
            if result is None:
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.FAILED,
                    error="Agent 执行返回空结果"
                )
                return task
            
            task.result = result
            task.source = self._get_content_source(agent_type)
            
            # Director_Agent 审核
            if not skip_review:
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.REVIEWING,
                    progress=0.7,
                    message="Director_Agent 审核中..."
                )
                
                review_result = await self._review_result(task)
                task.review_result = review_result
            
            # 完成
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.COMPLETED,
                progress=1.0,
                message="任务完成",
                result=result
            )
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.FAILED,
                error=str(e)
            )
        
        return task
    
    async def _execute_agent_task(self, task: AgentTask) -> Optional[Any]:
        """执行具体的 Agent 任务"""
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        task_type = task.task_type
        input_data = task.input_data
        
        # 根据任务类型调用对应方法
        if task_type == "generate_logline":
            response = await adapter.generate_logline(
                input_data.get("script_content", "")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "generate_synopsis":
            response = await adapter.generate_synopsis(
                input_data.get("script_content", "")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "generate_character_bio":
            response = await adapter.generate_character_bio(
                input_data.get("character_name", ""),
                input_data.get("script_content", ""),
                input_data.get("existing_info")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "estimate_scene_duration":
            response = await adapter.estimate_scene_duration(
                input_data.get("scene_content", "")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "classify_file":
            response = await adapter.classify_file(
                input_data.get("filename", ""),
                input_data.get("file_type", ""),
                input_data.get("metadata")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "generate_visual_tags":
            response = await adapter.generate_visual_tags(
                input_data.get("description", ""),
                input_data.get("file_type", "image")
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "analyze_market":
            response = await adapter.analyze_market(
                input_data.get("project_data", {})
            )
            if response.success:
                return response.parsed_data
        
        elif task_type == "check_tag_consistency":
            response = await adapter.check_tag_consistency(
                input_data.get("tags", [])
            )
            if response.success:
                return response.parsed_data
        
        return None
    
    async def _review_result(self, task: AgentTask) -> Dict[str, Any]:
        """Director_Agent 审核结果"""
        adapter = self._get_llm_adapter()
        if not adapter:
            return {"status": "approved", "reason": "审核服务不可用，自动通过"}
        
        try:
            response = await adapter.review_content(
                content=task.result,
                content_type=task.task_type,
                project_context=task.input_data.get("project_context")
            )
            
            if response.success and response.parsed_data:
                return response.parsed_data
            
            return {"status": "approved", "reason": "审核完成"}
            
        except Exception as e:
            logger.error(f"审核失败: {e}")
            return {"status": "approved", "reason": f"审核异常: {e}"}
    
    def _get_content_source(self, agent_type: str) -> ContentSource:
        """获取内容来源"""
        source_map = {
            "script_agent": ContentSource.SCRIPT_AGENT,
            "art_agent": ContentSource.ART_AGENT,
            "director_agent": ContentSource.DIRECTOR_AGENT,
            "market_agent": ContentSource.MARKET_AGENT,
            "storyboard_agent": ContentSource.STORYBOARD_AGENT,
            "system_agent": ContentSource.SYSTEM_AGENT
        }
        return source_map.get(agent_type, ContentSource.USER)
    
    def list_tasks(
        self,
        status: AgentTaskStatus = None,
        agent_type: str = None,
        limit: int = 100
    ) -> List[AgentTask]:
        """列出任务"""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if agent_type:
            tasks = [t for t in tasks if t.agent_type == agent_type]
        
        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._tasks.get(task_id)
        if task and task.status in [AgentTaskStatus.PENDING, AgentTaskStatus.WORKING]:
            self.update_task(
                task_id,
                status=AgentTaskStatus.CANCELLED,
                message="任务已取消"
            )
            return True
        return False


# 全局服务实例
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取 Agent 服务实例"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
