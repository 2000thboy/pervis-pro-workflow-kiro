"""
BaseAgent基类 - Agent生命周期管理、状态管理和消息处理

为 Pervis PRO 适配的 Agent 基类，提供:
- 生命周期管理 (初始化、启动、暂停、停止)
- 状态管理 (状态转换、状态查询)
- 消息处理 (接收、发送、响应)
- 操作日志记录
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .message_bus import MessageBus, Message, Response, message_bus
from .communication_protocol import (
    AgentCommunicationProtocol,
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
)
from .agent_types import AgentState, AgentType

logger = logging.getLogger(__name__)


class AgentLifecycleState(Enum):
    """Agent生命周期状态"""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentOperationLog:
    """Agent操作日志记录"""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    operation: str = ""
    state_before: Optional[str] = None
    state_after: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "details": self.details,
            "success": self.success,
            "error": self.error
        }


class BaseAgent(ABC):
    """
    Agent基类 - 所有Agent的抽象基类
    
    提供统一的Agent接口，包括:
    - 生命周期管理 (初始化、启动、暂停、停止)
    - 状态管理 (状态转换、状态查询)
    - 消息处理 (接收、发送、响应)
    - 操作日志记录
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        message_bus_instance: Optional[MessageBus] = None,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self._agent_id = agent_id
        self._agent_type = agent_type
        self._message_bus = message_bus_instance or message_bus
        self._capabilities = capabilities or []
        self._config = config or {}
        
        # 生命周期状态
        self._lifecycle_state = AgentLifecycleState.CREATED
        # 工作状态
        self._work_state = AgentState.OFFLINE
        # 当前任务
        self._current_task: Optional[str] = None
        self._current_task_progress: float = 0.0
        # 最后活动时间
        self._last_activity = datetime.utcnow()
        # 操作日志
        self._operation_logs: List[AgentOperationLog] = []
        self._max_logs = 500
        
        # 通信协议
        self._protocol: Optional[AgentCommunicationProtocol] = None
        # 消息处理器
        self._message_handlers: Dict[ProtocolMessageType, Callable] = {}
        # 订阅ID列表
        self._subscription_ids: Set[str] = set()
        
        # 初始化锁
        self._state_lock = asyncio.Lock()
        
        self._log_operation("agent_created", details={
            "agent_id": agent_id,
            "agent_type": agent_type.value,
            "capabilities": capabilities
        })
        
        logger.info(f"Agent创建: {agent_id} (类型: {agent_type.value})")
    
    # ========================================================================
    # 属性访问器
    # ========================================================================
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> AgentType:
        return self._agent_type
    
    @property
    def lifecycle_state(self) -> AgentLifecycleState:
        return self._lifecycle_state
    
    @property
    def work_state(self) -> AgentState:
        return self._work_state
    
    @property
    def current_task(self) -> Optional[str]:
        return self._current_task
    
    @property
    def task_progress(self) -> float:
        return self._current_task_progress
    
    @property
    def is_ready(self) -> bool:
        return self._lifecycle_state in [AgentLifecycleState.READY, AgentLifecycleState.RUNNING]
    
    @property
    def is_running(self) -> bool:
        return self._lifecycle_state == AgentLifecycleState.RUNNING
    
    # ========================================================================
    # 生命周期管理
    # ========================================================================
    
    async def initialize(self) -> bool:
        """初始化Agent"""
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.CREATED:
                logger.warning(f"Agent {self._agent_id} 无法初始化: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.INITIALIZING
        
        try:
            # 初始化通信协议
            self._protocol = AgentCommunicationProtocol(self._message_bus, self._agent_id)
            
            # 注册默认消息处理器
            await self._register_default_handlers()
            
            # 执行子类特定的初始化
            await self._on_initialize()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.READY
                self._work_state = AgentState.IDLE
            
            self._log_operation("agent_initialized", state_before=old_state.value, state_after=AgentLifecycleState.READY.value)
            logger.info(f"Agent初始化完成: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
                self._work_state = AgentState.ERROR
            
            self._log_operation("agent_initialization_failed", success=False, error=str(e))
            logger.error(f"Agent初始化失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def start(self) -> bool:
        """启动Agent"""
        async with self._state_lock:
            if self._lifecycle_state not in [AgentLifecycleState.READY, AgentLifecycleState.PAUSED]:
                logger.warning(f"Agent {self._agent_id} 无法启动: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
        
        try:
            if self._protocol:
                await self._protocol.start()
            
            # 订阅Agent专属主题
            sub_id = await self._message_bus.subscribe(
                self._agent_id,
                f"agent.{self._agent_id}",
                self._handle_message
            )
            self._subscription_ids.add(sub_id)
            
            # 订阅广播主题
            sub_id = await self._message_bus.subscribe(
                self._agent_id,
                "agent.broadcast",
                self._handle_message
            )
            self._subscription_ids.add(sub_id)
            
            await self._on_start()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.RUNNING
                self._work_state = AgentState.IDLE
            
            self._update_activity()
            self._log_operation("agent_started", state_before=old_state.value, state_after=AgentLifecycleState.RUNNING.value)
            logger.info(f"Agent启动完成: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
            
            self._log_operation("agent_start_failed", success=False, error=str(e))
            logger.error(f"Agent启动失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止Agent"""
        async with self._state_lock:
            if self._lifecycle_state in [AgentLifecycleState.STOPPED, AgentLifecycleState.STOPPING]:
                return True
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.STOPPING
        
        try:
            await self._on_stop()
            await self._message_bus.unsubscribe_all(self._agent_id)
            self._subscription_ids.clear()
            
            if self._protocol:
                await self._protocol.stop()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.STOPPED
                self._work_state = AgentState.OFFLINE
            
            self._log_operation("agent_stopped", state_before=old_state.value, state_after=AgentLifecycleState.STOPPED.value)
            logger.info(f"Agent已停止: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
            
            self._log_operation("agent_stop_failed", success=False, error=str(e))
            logger.error(f"Agent停止失败: {self._agent_id}, 错误: {e}")
            return False
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    async def update_work_state(
        self, 
        new_state: AgentState, 
        task: Optional[str] = None,
        progress: float = 0.0
    ) -> bool:
        """更新工作状态"""
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.RUNNING:
                return False
            
            old_state = self._work_state
            self._work_state = new_state
            self._current_task = task
            self._current_task_progress = progress
        
        self._update_activity()
        self._log_operation("state_updated", state_before=old_state.value, state_after=new_state.value, details={"task": task, "progress": progress})
        
        # 广播状态变更
        await self._broadcast_state_change(old_state, new_state)
        return True
    
    async def _broadcast_state_change(self, old_state: AgentState, new_state: AgentState):
        """广播状态变更消息"""
        if self._protocol and self._protocol.is_running:
            await self._protocol.broadcast(
                ProtocolMessageType.AGENT_STATUS,
                {
                    "agent_id": self._agent_id,
                    "agent_type": self._agent_type.value,
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "current_task": self._current_task,
                    "progress": self._current_task_progress,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态信息"""
        return {
            "agent_id": self._agent_id,
            "agent_type": self._agent_type.value,
            "lifecycle_state": self._lifecycle_state.value,
            "work_state": self._work_state.value,
            "current_task": self._current_task,
            "progress": self._current_task_progress,
            "last_activity": self._last_activity.isoformat(),
            "capabilities": self._capabilities,
            "is_ready": self.is_ready,
            "is_running": self.is_running
        }
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def _handle_message(self, message: Message) -> None:
        """处理接收到的消息"""
        self._update_activity()
        
        try:
            if "header" in message.content and "payload" in message.content:
                protocol_msg = ProtocolMessage.from_dict(message.content)
                await self._handle_protocol_message(protocol_msg)
            else:
                await self.handle_message(message)
                
        except Exception as e:
            logger.error(f"Agent {self._agent_id} 消息处理错误: {e}")
    
    async def _handle_protocol_message(self, message: ProtocolMessage) -> None:
        """处理协议消息"""
        msg_type = message.payload.message_type
        handler = self._message_handlers.get(msg_type)
        
        if handler:
            try:
                response = await handler(message)
                if response:
                    await self._send_protocol_response(response)
            except Exception as e:
                logger.error(f"协议消息处理错误: {e}")
        else:
            response = await self.handle_protocol_message(message)
            if response:
                await self._send_protocol_response(response)
    
    async def _send_protocol_response(self, response: ProtocolMessage):
        """发送协议响应"""
        if response.header.target_agent and self._protocol:
            await self._protocol.send(
                response.header.target_agent,
                response.payload.message_type,
                response.payload.data
            )
    
    async def _register_default_handlers(self):
        """注册默认消息处理器"""
        self._message_handlers[ProtocolMessageType.PING] = self._handle_ping
        self._message_handlers[ProtocolMessageType.AGENT_STATUS] = self._handle_status_query
    
    async def _handle_ping(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理心跳消息"""
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data={"agent_id": self._agent_id, "status": self._work_state.value}
        )
    
    async def _handle_status_query(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理状态查询"""
        return message.create_response(ProtocolStatus.SUCCESS, data=self.get_status())
    
    # ========================================================================
    # 消息发送
    # ========================================================================
    
    async def send_message(
        self,
        target_agent: str,
        message_type: ProtocolMessageType,
        data: Dict[str, Any]
    ) -> bool:
        """发送消息到目标Agent"""
        if not self._protocol or not self._protocol.is_running:
            return False
        
        self._update_activity()
        return await self._protocol.send(target_agent, message_type, data)
    
    async def broadcast_message(
        self,
        message_type: ProtocolMessageType,
        data: Dict[str, Any]
    ) -> int:
        """广播消息到所有Agent"""
        if not self._protocol or not self._protocol.is_running:
            return 0
        
        self._update_activity()
        return await self._protocol.broadcast(message_type, data)
    
    # ========================================================================
    # 日志记录
    # ========================================================================
    
    def _log_operation(
        self,
        operation: str,
        state_before: Optional[str] = None,
        state_after: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """记录操作日志"""
        log = AgentOperationLog(
            operation=operation,
            state_before=state_before,
            state_after=state_after,
            details=details or {},
            success=success,
            error=error
        )
        
        self._operation_logs.append(log)
        if len(self._operation_logs) > self._max_logs:
            self._operation_logs = self._operation_logs[-self._max_logs:]
    
    def get_operation_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取操作日志"""
        return [l.to_dict() for l in self._operation_logs[-limit:]]
    
    def _update_activity(self):
        """更新最后活动时间"""
        self._last_activity = datetime.utcnow()
    
    # ========================================================================
    # 抽象方法 - 子类必须实现
    # ========================================================================
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息 - 子类必须实现"""
        pass
    
    @abstractmethod
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息 - 子类必须实现"""
        pass
    
    # ========================================================================
    # 可选的生命周期钩子 - 子类可以覆盖
    # ========================================================================
    
    async def _on_initialize(self):
        """初始化钩子"""
        pass
    
    async def _on_start(self):
        """启动钩子"""
        pass
    
    async def _on_stop(self):
        """停止钩子"""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self._agent_id}, type={self._agent_type.value}, state={self._work_state.value})>"
