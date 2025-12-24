"""
BaseAgent基类 - Agent生命周期管理、状态管理和消息处理

需求: 1.1 - WHEN 系统启动时 THEN 系统 SHALL 初始化所有8个Agent并建立通信连接
需求: 1.4 - WHEN Agent执行任务时 THEN 系统 SHALL 记录所有Agent的状态和操作日志

本模块实现了所有Agent的基类，提供统一的生命周期管理、状态管理和消息处理接口。
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from ..core.message_bus import MessageBus, Message, MessageType, Response
from ..core.communication_protocol import (
    AgentCommunicationProtocol,
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
    ProtocolHandler,
    DefaultProtocolHandler,
)
from ..core.agent_types import AgentState, AgentType

logger = logging.getLogger(__name__)


class AgentLifecycleState(Enum):
    """Agent生命周期状态"""
    CREATED = "created"           # 已创建，未初始化
    INITIALIZING = "initializing" # 正在初始化
    READY = "ready"               # 就绪，可以工作
    RUNNING = "running"           # 运行中
    PAUSED = "paused"             # 已暂停
    STOPPING = "stopping"         # 正在停止
    STOPPED = "stopped"           # 已停止
    ERROR = "error"               # 错误状态


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


@dataclass
class AgentCapability:
    """Agent能力定义"""
    name: str
    description: str
    handler: Optional[Callable] = None
    enabled: bool = True


class BaseAgent(ABC):
    """
    Agent基类 - 所有Agent的抽象基类
    
    提供统一的Agent接口，包括:
    - 生命周期管理 (初始化、启动、暂停、停止)
    - 状态管理 (状态转换、状态查询)
    - 消息处理 (接收、发送、响应)
    - 操作日志记录
    
    需求: 1.1 - 系统启动时初始化所有Agent并建立通信连接
    需求: 1.4 - Agent执行任务时记录所有状态和操作日志
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        message_bus: MessageBus,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识符
            agent_type: Agent类型
            message_bus: 消息总线实例
            capabilities: Agent能力列表
            config: Agent配置
        """
        self._agent_id = agent_id
        self._agent_type = agent_type
        self._message_bus = message_bus
        self._capabilities = capabilities or []
        self._config = config or {}
        
        # 生命周期状态
        self._lifecycle_state = AgentLifecycleState.CREATED
        # 工作状态
        self._work_state = AgentState.OFFLINE
        # 当前任务
        self._current_task: Optional[str] = None
        # 最后活动时间
        self._last_activity = datetime.utcnow()
        # 操作日志
        self._operation_logs: List[AgentOperationLog] = []
        self._max_logs = 1000
        
        # 通信协议
        self._protocol: Optional[AgentCommunicationProtocol] = None
        # 消息处理器
        self._message_handlers: Dict[ProtocolMessageType, Callable] = {}
        # 订阅ID列表
        self._subscription_ids: Set[str] = set()
        
        # 初始化锁
        self._state_lock = asyncio.Lock()
        
        # 记录创建日志
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
        """获取Agent ID"""
        return self._agent_id
    
    @property
    def agent_type(self) -> AgentType:
        """获取Agent类型"""
        return self._agent_type
    
    @property
    def lifecycle_state(self) -> AgentLifecycleState:
        """获取生命周期状态"""
        return self._lifecycle_state
    
    @property
    def work_state(self) -> AgentState:
        """获取工作状态"""
        return self._work_state
    
    @property
    def current_task(self) -> Optional[str]:
        """获取当前任务"""
        return self._current_task
    
    @property
    def last_activity(self) -> datetime:
        """获取最后活动时间"""
        return self._last_activity
    
    @property
    def capabilities(self) -> List[str]:
        """获取能力列表"""
        return self._capabilities.copy()
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config.copy()
    
    @property
    def is_ready(self) -> bool:
        """检查Agent是否就绪"""
        return self._lifecycle_state in [
            AgentLifecycleState.READY,
            AgentLifecycleState.RUNNING
        ]
    
    @property
    def is_running(self) -> bool:
        """检查Agent是否运行中"""
        return self._lifecycle_state == AgentLifecycleState.RUNNING
    
    # ========================================================================
    # 生命周期管理
    # ========================================================================
    
    async def initialize(self) -> bool:
        """
        初始化Agent
        
        执行Agent的初始化逻辑，包括:
        - 建立与消息总线的连接
        - 初始化通信协议
        - 注册消息处理器
        - 执行子类特定的初始化
        
        Returns:
            是否初始化成功
        """
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.CREATED:
                logger.warning(f"Agent {self._agent_id} 无法初始化: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.INITIALIZING
        
        try:
            # 初始化通信协议
            self._protocol = AgentCommunicationProtocol(
                self._message_bus,
                self._agent_id
            )
            
            # 注册默认消息处理器
            await self._register_default_handlers()
            
            # 执行子类特定的初始化
            await self._on_initialize()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.READY
                self._work_state = AgentState.IDLE
            
            self._log_operation(
                "agent_initialized",
                state_before=old_state.value,
                state_after=AgentLifecycleState.READY.value
            )
            
            logger.info(f"Agent初始化完成: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
                self._work_state = AgentState.ERROR
            
            self._log_operation(
                "agent_initialization_failed",
                state_before=old_state.value,
                state_after=AgentLifecycleState.ERROR.value,
                success=False,
                error=str(e)
            )
            
            logger.error(f"Agent初始化失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def start(self) -> bool:
        """
        启动Agent
        
        启动Agent的运行，包括:
        - 启动通信协议
        - 订阅相关主题
        - 执行子类特定的启动逻辑
        
        Returns:
            是否启动成功
        """
        async with self._state_lock:
            if self._lifecycle_state not in [AgentLifecycleState.READY, AgentLifecycleState.PAUSED]:
                logger.warning(f"Agent {self._agent_id} 无法启动: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
        
        try:
            # 启动通信协议
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
            
            # 订阅Agent类型主题
            sub_id = await self._message_bus.subscribe(
                self._agent_id,
                f"agent.type.{self._agent_type.value}",
                self._handle_message
            )
            self._subscription_ids.add(sub_id)
            
            # 执行子类特定的启动逻辑
            await self._on_start()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.RUNNING
                self._work_state = AgentState.IDLE
            
            self._update_activity()
            self._log_operation(
                "agent_started",
                state_before=old_state.value,
                state_after=AgentLifecycleState.RUNNING.value
            )
            
            logger.info(f"Agent启动完成: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
                self._work_state = AgentState.ERROR
            
            self._log_operation(
                "agent_start_failed",
                state_before=old_state.value,
                state_after=AgentLifecycleState.ERROR.value,
                success=False,
                error=str(e)
            )
            
            logger.error(f"Agent启动失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def pause(self) -> bool:
        """
        暂停Agent
        
        Returns:
            是否暂停成功
        """
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.RUNNING:
                logger.warning(f"Agent {self._agent_id} 无法暂停: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.PAUSED
            self._work_state = AgentState.WAITING
        
        try:
            await self._on_pause()
            
            self._log_operation(
                "agent_paused",
                state_before=old_state.value,
                state_after=AgentLifecycleState.PAUSED.value
            )
            
            logger.info(f"Agent已暂停: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
            
            self._log_operation(
                "agent_pause_failed",
                success=False,
                error=str(e)
            )
            
            logger.error(f"Agent暂停失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def resume(self) -> bool:
        """
        恢复Agent
        
        Returns:
            是否恢复成功
        """
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.PAUSED:
                logger.warning(f"Agent {self._agent_id} 无法恢复: 当前状态 {self._lifecycle_state}")
                return False
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.RUNNING
            self._work_state = AgentState.IDLE
        
        try:
            await self._on_resume()
            
            self._update_activity()
            self._log_operation(
                "agent_resumed",
                state_before=old_state.value,
                state_after=AgentLifecycleState.RUNNING.value
            )
            
            logger.info(f"Agent已恢复: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
            
            self._log_operation(
                "agent_resume_failed",
                success=False,
                error=str(e)
            )
            
            logger.error(f"Agent恢复失败: {self._agent_id}, 错误: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        停止Agent
        
        停止Agent的运行，包括:
        - 取消所有订阅
        - 停止通信协议
        - 执行子类特定的停止逻辑
        
        Returns:
            是否停止成功
        """
        async with self._state_lock:
            if self._lifecycle_state in [AgentLifecycleState.STOPPED, AgentLifecycleState.STOPPING]:
                return True
            
            old_state = self._lifecycle_state
            self._lifecycle_state = AgentLifecycleState.STOPPING
        
        try:
            # 执行子类特定的停止逻辑
            await self._on_stop()
            
            # 取消所有订阅
            await self._message_bus.unsubscribe_all(self._agent_id)
            self._subscription_ids.clear()
            
            # 停止通信协议
            if self._protocol:
                await self._protocol.stop()
            
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.STOPPED
                self._work_state = AgentState.OFFLINE
            
            self._log_operation(
                "agent_stopped",
                state_before=old_state.value,
                state_after=AgentLifecycleState.STOPPED.value
            )
            
            logger.info(f"Agent已停止: {self._agent_id}")
            return True
            
        except Exception as e:
            async with self._state_lock:
                self._lifecycle_state = AgentLifecycleState.ERROR
            
            self._log_operation(
                "agent_stop_failed",
                success=False,
                error=str(e)
            )
            
            logger.error(f"Agent停止失败: {self._agent_id}, 错误: {e}")
            return False

    # ========================================================================
    # 状态管理
    # ========================================================================
    
    async def update_work_state(self, new_state: AgentState, task: Optional[str] = None) -> bool:
        """
        更新工作状态
        
        Args:
            new_state: 新的工作状态
            task: 当前任务描述
            
        Returns:
            是否更新成功
        """
        async with self._state_lock:
            if self._lifecycle_state != AgentLifecycleState.RUNNING:
                logger.warning(f"Agent {self._agent_id} 无法更新状态: 未运行")
                return False
            
            old_state = self._work_state
            self._work_state = new_state
            self._current_task = task
        
        self._update_activity()
        self._log_operation(
            "state_updated",
            state_before=old_state.value,
            state_after=new_state.value,
            details={"task": task}
        )
        
        # 广播状态变更
        await self._broadcast_state_change(old_state, new_state)
        
        logger.debug(f"Agent {self._agent_id} 状态更新: {old_state.value} -> {new_state.value}")
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取Agent状态信息
        
        Returns:
            状态信息字典
        """
        return {
            "agent_id": self._agent_id,
            "agent_type": self._agent_type.value,
            "lifecycle_state": self._lifecycle_state.value,
            "work_state": self._work_state.value,
            "current_task": self._current_task,
            "last_activity": self._last_activity.isoformat(),
            "capabilities": self._capabilities,
            "is_ready": self.is_ready,
            "is_running": self.is_running
        }
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def _handle_message(self, message: Message) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        self._update_activity()
        
        try:
            # 尝试解析为协议消息
            if "header" in message.content and "payload" in message.content:
                protocol_msg = ProtocolMessage.from_dict(message.content)
                await self._handle_protocol_message(protocol_msg)
            else:
                # 处理普通消息
                await self.handle_message(message)
                
        except Exception as e:
            logger.error(f"Agent {self._agent_id} 消息处理错误: {e}")
            self._log_operation(
                "message_handling_error",
                success=False,
                error=str(e),
                details={"message_id": message.id}
            )
    
    async def _handle_protocol_message(self, message: ProtocolMessage) -> None:
        """处理协议消息"""
        msg_type = message.payload.message_type
        
        # 查找注册的处理器
        handler = self._message_handlers.get(msg_type)
        if handler:
            try:
                response = await handler(message)
                if response:
                    await self._send_protocol_response(response)
            except Exception as e:
                logger.error(f"协议消息处理错误: {e}")
                # 发送错误响应
                error_response = message.create_response(
                    ProtocolStatus.INTERNAL_ERROR,
                    error=str(e)
                )
                await self._send_protocol_response(error_response)
        else:
            # 调用子类的处理方法
            response = await self.handle_protocol_message(message)
            if response:
                await self._send_protocol_response(response)
    
    async def _send_protocol_response(self, response: ProtocolMessage):
        """发送协议响应"""
        if response.header.target_agent and self._protocol:
            await self._protocol.send(
                response.header.target_agent,
                response.payload.message_type,
                response.payload.data,
                metadata=response.payload.metadata
            )
    
    async def _register_default_handlers(self):
        """注册默认消息处理器"""
        # 心跳处理
        self._message_handlers[ProtocolMessageType.PING] = self._handle_ping
        # 状态查询处理
        self._message_handlers[ProtocolMessageType.AGENT_STATUS] = self._handle_status_query
    
    async def _handle_ping(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理心跳消息"""
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data={
                "agent_id": self._agent_id,
                "status": self._work_state.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _handle_status_query(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理状态查询"""
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data=self.get_status()
        )
    
    def register_message_handler(
        self,
        message_type: ProtocolMessageType,
        handler: Callable[[ProtocolMessage], Optional[ProtocolMessage]]
    ):
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        self._message_handlers[message_type] = handler
        logger.debug(f"Agent {self._agent_id} 注册处理器: {message_type.value}")
    
    # ========================================================================
    # 消息发送
    # ========================================================================
    
    async def send_message(
        self,
        target_agent: str,
        message_type: ProtocolMessageType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送消息到目标Agent
        
        Args:
            target_agent: 目标Agent ID
            message_type: 消息类型
            data: 消息数据
            metadata: 元数据
            
        Returns:
            是否发送成功
        """
        if not self._protocol or not self._protocol.is_running:
            logger.warning(f"Agent {self._agent_id} 无法发送消息: 协议未运行")
            return False
        
        self._update_activity()
        success = await self._protocol.send(target_agent, message_type, data, metadata)
        
        self._log_operation(
            "message_sent",
            details={
                "target": target_agent,
                "type": message_type.value,
                "success": success
            },
            success=success
        )
        
        return success
    
    async def broadcast_message(
        self,
        message_type: ProtocolMessageType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        广播消息到所有Agent
        
        Args:
            message_type: 消息类型
            data: 消息数据
            metadata: 元数据
            
        Returns:
            成功投递的Agent数量
        """
        if not self._protocol or not self._protocol.is_running:
            logger.warning(f"Agent {self._agent_id} 无法广播消息: 协议未运行")
            return 0
        
        self._update_activity()
        count = await self._protocol.broadcast(message_type, data, metadata)
        
        self._log_operation(
            "message_broadcast",
            details={
                "type": message_type.value,
                "delivered_count": count
            }
        )
        
        return count
    
    async def request(
        self,
        target_agent: str,
        message_type: ProtocolMessageType,
        data: Dict[str, Any],
        timeout: float = 30.0
    ) -> Response:
        """
        发送请求并等待响应
        
        Args:
            target_agent: 目标Agent ID
            message_type: 消息类型
            data: 请求数据
            timeout: 超时时间
            
        Returns:
            响应对象
        """
        if not self._protocol or not self._protocol.is_running:
            return Response(
                success=False,
                message_id="",
                error="协议未运行"
            )
        
        self._update_activity()
        response = await self._protocol.request(target_agent, message_type, data, timeout)
        
        self._log_operation(
            "request_sent",
            details={
                "target": target_agent,
                "type": message_type.value,
                "success": response.success,
                "latency_ms": response.latency_ms
            },
            success=response.success
        )
        
        return Response(
            success=response.success,
            message_id=response.message.header.message_id if response.message else "",
            data=response.message.payload.data if response.message else None,
            error=response.error
        )
    
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
        """
        记录操作日志
        
        需求: 1.4 - WHEN Agent执行任务时 THEN 系统 SHALL 记录所有Agent的状态和操作日志
        """
        log = AgentOperationLog(
            operation=operation,
            state_before=state_before,
            state_after=state_after,
            details=details or {},
            success=success,
            error=error
        )
        
        self._operation_logs.append(log)
        
        # 限制日志数量
        if len(self._operation_logs) > self._max_logs:
            self._operation_logs = self._operation_logs[-self._max_logs:]
    
    def get_operation_logs(
        self,
        limit: int = 100,
        operation_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取操作日志
        
        Args:
            limit: 返回数量限制
            operation_filter: 操作类型过滤
            
        Returns:
            日志列表
        """
        logs = self._operation_logs
        
        if operation_filter:
            logs = [l for l in logs if l.operation == operation_filter]
        
        return [l.to_dict() for l in logs[-limit:]]
    
    def _update_activity(self):
        """更新最后活动时间"""
        self._last_activity = datetime.utcnow()
    
    # ========================================================================
    # 抽象方法 - 子类必须实现
    # ========================================================================
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Optional[Response]:
        """
        处理普通消息 - 子类必须实现
        
        Args:
            message: 消息对象
            
        Returns:
            可选的响应对象
        """
        pass
    
    @abstractmethod
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """
        处理协议消息 - 子类必须实现
        
        Args:
            message: 协议消息对象
            
        Returns:
            可选的响应消息
        """
        pass
    
    # ========================================================================
    # 可选的生命周期钩子 - 子类可以覆盖
    # ========================================================================
    
    async def _on_initialize(self):
        """初始化钩子 - 子类可以覆盖"""
        pass
    
    async def _on_start(self):
        """启动钩子 - 子类可以覆盖"""
        pass
    
    async def _on_pause(self):
        """暂停钩子 - 子类可以覆盖"""
        pass
    
    async def _on_resume(self):
        """恢复钩子 - 子类可以覆盖"""
        pass
    
    async def _on_stop(self):
        """停止钩子 - 子类可以覆盖"""
        pass
    
    # ========================================================================
    # 字符串表示
    # ========================================================================
    
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"id={self._agent_id}, "
            f"type={self._agent_type.value}, "
            f"lifecycle={self._lifecycle_state.value}, "
            f"work={self._work_state.value})>"
        )
