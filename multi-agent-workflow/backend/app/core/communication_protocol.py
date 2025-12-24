"""
Agent间通信协议实现

需求: 1.2 - WHEN Agent间需要数据交换时 THEN 系统 SHALL 通过统一的消息总线进行通信
需求: 1.3 - WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突

本模块定义了Agent间通信的统一消息格式和协议，实现请求-响应模式通信。
"""
import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Union

from .message_bus import MessageBus, Message, MessageType, MessagePriority, Response

logger = logging.getLogger(__name__)


# ============================================================================
# 协议消息类型定义
# ============================================================================

class ProtocolMessageType(Enum):
    """协议消息类型"""
    # 基础通信
    PING = "ping"                          # 心跳检测
    PONG = "pong"                          # 心跳响应
    ACK = "ack"                            # 确认消息
    NACK = "nack"                          # 否定确认
    
    # Agent生命周期
    AGENT_REGISTER = "agent_register"      # Agent注册
    AGENT_UNREGISTER = "agent_unregister"  # Agent注销
    AGENT_STATUS = "agent_status"          # Agent状态更新
    AGENT_HEARTBEAT = "agent_heartbeat"    # Agent心跳
    
    # 任务相关
    TASK_ASSIGN = "task_assign"            # 任务分配
    TASK_ACCEPT = "task_accept"            # 任务接受
    TASK_REJECT = "task_reject"            # 任务拒绝
    TASK_PROGRESS = "task_progress"        # 任务进度
    TASK_COMPLETE = "task_complete"        # 任务完成
    TASK_FAILED = "task_failed"            # 任务失败
    
    # 数据交换
    DATA_REQUEST = "data_request"          # 数据请求
    DATA_RESPONSE = "data_response"        # 数据响应
    DATA_SYNC = "data_sync"                # 数据同步
    
    # 冲突解决
    CONFLICT_REPORT = "conflict_report"    # 冲突报告
    CONFLICT_RESOLVE = "conflict_resolve"  # 冲突解决
    
    # 工作流
    WORKFLOW_START = "workflow_start"      # 工作流启动
    WORKFLOW_STEP = "workflow_step"        # 工作流步骤
    WORKFLOW_END = "workflow_end"          # 工作流结束


class ProtocolStatus(Enum):
    """协议状态码"""
    SUCCESS = 200
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    TIMEOUT = 408
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ============================================================================
# 协议消息数据结构
# ============================================================================

@dataclass
class ProtocolHeader:
    """协议消息头"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_agent: str = ""
    target_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: int = 30  # 消息生存时间(秒)
    priority: int = 2  # 1-4, 对应MessagePriority
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolHeader":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProtocolPayload:
    """协议消息载荷"""
    message_type: ProtocolMessageType = ProtocolMessageType.DATA_REQUEST
    status: Optional[ProtocolStatus] = None
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_type": self.message_type.value,
            "status": self.status.value if self.status else None,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolPayload":
        return cls(
            message_type=ProtocolMessageType(data.get("message_type", "data_request")),
            status=ProtocolStatus(data["status"]) if data.get("status") else None,
            data=data.get("data", {}),
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ProtocolMessage:
    """
    统一协议消息格式
    
    所有Agent间的通信都使用此格式，确保消息格式的一致性和可追溯性。
    """
    header: ProtocolHeader = field(default_factory=ProtocolHeader)
    payload: ProtocolPayload = field(default_factory=ProtocolPayload)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProtocolMessage":
        return cls(
            header=ProtocolHeader.from_dict(data.get("header", {})),
            payload=ProtocolPayload.from_dict(data.get("payload", {}))
        )
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "ProtocolMessage":
        return cls.from_dict(json.loads(json_str))
    
    def to_message_bus_message(self) -> Message:
        """转换为消息总线消息格式"""
        return Message(
            id=self.header.message_id,
            type=MessageType.REQUEST if self.payload.message_type in [
                ProtocolMessageType.DATA_REQUEST,
                ProtocolMessageType.TASK_ASSIGN,
                ProtocolMessageType.CONFLICT_REPORT
            ] else MessageType.EVENT,
            source=self.header.source_agent,
            target=self.header.target_agent,
            topic=f"agent.{self.header.target_agent}" if self.header.target_agent else "agent.broadcast",
            content=self.to_dict(),
            priority=MessagePriority(self.header.priority),
            correlation_id=self.header.correlation_id,
            reply_to=self.header.reply_to
        )
    
    @classmethod
    def from_message_bus_message(cls, msg: Message) -> "ProtocolMessage":
        """从消息总线消息格式转换"""
        return cls.from_dict(msg.content)
    
    def create_response(
        self,
        status: ProtocolStatus,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> "ProtocolMessage":
        """创建响应消息"""
        response_type = ProtocolMessageType.DATA_RESPONSE
        if self.payload.message_type == ProtocolMessageType.TASK_ASSIGN:
            response_type = ProtocolMessageType.TASK_ACCEPT if status == ProtocolStatus.SUCCESS else ProtocolMessageType.TASK_REJECT
        elif self.payload.message_type == ProtocolMessageType.PING:
            response_type = ProtocolMessageType.PONG
        elif self.payload.message_type == ProtocolMessageType.CONFLICT_REPORT:
            response_type = ProtocolMessageType.CONFLICT_RESOLVE
        
        return ProtocolMessage(
            header=ProtocolHeader(
                source_agent=self.header.target_agent or "",
                target_agent=self.header.source_agent,
                correlation_id=self.header.message_id,
                reply_to=self.header.reply_to
            ),
            payload=ProtocolPayload(
                message_type=response_type,
                status=status,
                data=data or {},
                error=error
            )
        )


# ============================================================================
# 协议响应数据结构
# ============================================================================

@dataclass
class ProtocolResponse:
    """协议响应"""
    success: bool
    status: ProtocolStatus
    message: Optional[ProtocolMessage] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "message": self.message.to_dict() if self.message else None,
            "error": self.error,
            "latency_ms": self.latency_ms
        }


# ============================================================================
# 通信协议处理器接口
# ============================================================================

class ProtocolHandler(ABC):
    """协议处理器抽象基类"""
    
    @abstractmethod
    async def handle(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息并返回响应"""
        pass
    
    @abstractmethod
    def can_handle(self, message_type: ProtocolMessageType) -> bool:
        """检查是否能处理指定类型的消息"""
        pass


class DefaultProtocolHandler(ProtocolHandler):
    """默认协议处理器"""
    
    def __init__(self, supported_types: List[ProtocolMessageType]):
        self._supported_types = set(supported_types)
        self._handlers: Dict[ProtocolMessageType, Callable] = {}
    
    def register_handler(
        self,
        message_type: ProtocolMessageType,
        handler: Callable[[ProtocolMessage], Optional[ProtocolMessage]]
    ):
        """注册消息类型处理函数"""
        self._handlers[message_type] = handler
        self._supported_types.add(message_type)
    
    async def handle(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        handler = self._handlers.get(message.payload.message_type)
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(message)
            return handler(message)
        return None
    
    def can_handle(self, message_type: ProtocolMessageType) -> bool:
        return message_type in self._supported_types


# ============================================================================
# Agent通信协议类
# ============================================================================

class AgentCommunicationProtocol:
    """
    Agent间通信协议
    
    提供统一的Agent间通信接口，封装消息总线的底层细节，
    实现请求-响应模式通信和消息格式验证。
    
    功能:
    - 统一消息格式和协议
    - 请求-响应模式通信
    - 消息验证和错误处理
    - 通信统计和监控
    """
    
    def __init__(self, message_bus: MessageBus, agent_id: str):
        self._message_bus = message_bus
        self._agent_id = agent_id
        self._handlers: Dict[ProtocolMessageType, ProtocolHandler] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "requests_sent": 0,
            "responses_received": 0,
            "errors": 0,
            "timeouts": 0
        }
        self._running = False
        self._subscription_id: Optional[str] = None
        
        logger.info(f"Agent通信协议初始化: {agent_id}")
    
    async def start(self):
        """启动通信协议"""
        if self._running:
            return
        
        # 订阅Agent专属主题
        self._subscription_id = await self._message_bus.subscribe(
            self._agent_id,
            f"agent.{self._agent_id}",
            self._handle_incoming_message
        )
        
        # 订阅广播主题
        await self._message_bus.subscribe(
            self._agent_id,
            "agent.broadcast",
            self._handle_incoming_message
        )
        
        self._running = True
        logger.info(f"Agent通信协议已启动: {self._agent_id}")
    
    async def stop(self):
        """停止通信协议"""
        if not self._running:
            return
        
        # 取消所有订阅
        await self._message_bus.unsubscribe_all(self._agent_id)
        
        # 取消所有待处理的响应
        for future in self._pending_responses.values():
            if not future.done():
                future.cancel()
        self._pending_responses.clear()
        
        self._running = False
        logger.info(f"Agent通信协议已停止: {self._agent_id}")
    
    def register_handler(self, handler: ProtocolHandler):
        """注册协议处理器"""
        for msg_type in ProtocolMessageType:
            if handler.can_handle(msg_type):
                self._handlers[msg_type] = handler
                logger.debug(f"注册处理器: {msg_type.value} -> {handler.__class__.__name__}")
    
    async def _handle_incoming_message(self, msg: Message):
        """处理接收到的消息"""
        try:
            protocol_msg = ProtocolMessage.from_message_bus_message(msg)
            self._stats["messages_received"] += 1
            
            # 检查是否是响应消息
            if protocol_msg.header.correlation_id:
                future = self._pending_responses.get(protocol_msg.header.correlation_id)
                if future and not future.done():
                    future.set_result(protocol_msg)
                    self._stats["responses_received"] += 1
                    return
            
            # 查找并调用处理器
            handler = self._handlers.get(protocol_msg.payload.message_type)
            if handler:
                response = await handler.handle(protocol_msg)
                if response:
                    await self._send_response(response)
            else:
                logger.warning(f"未找到处理器: {protocol_msg.payload.message_type}")
                
        except Exception as e:
            logger.error(f"处理消息错误: {e}")
            self._stats["errors"] += 1
    
    async def _send_response(self, response: ProtocolMessage):
        """发送响应消息"""
        if response.header.target_agent:
            bus_msg = response.to_message_bus_message()
            await self._message_bus.send_direct(response.header.target_agent, bus_msg)
    
    async def send(
        self,
        target_agent: str,
        message_type: ProtocolMessageType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        priority: int = 2
    ) -> bool:
        """
        发送消息到目标Agent
        
        Args:
            target_agent: 目标Agent ID
            message_type: 消息类型
            data: 消息数据
            metadata: 元数据
            priority: 优先级 (1-4)
            
        Returns:
            是否发送成功
        """
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent=self._agent_id,
                target_agent=target_agent,
                priority=priority
            ),
            payload=ProtocolPayload(
                message_type=message_type,
                data=data,
                metadata=metadata or {}
            )
        )
        
        bus_msg = protocol_msg.to_message_bus_message()
        success = await self._message_bus.send_direct(target_agent, bus_msg)
        
        if success:
            self._stats["messages_sent"] += 1
        else:
            self._stats["errors"] += 1
            
        return success
    
    async def broadcast(
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
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent=self._agent_id,
                target_agent=None
            ),
            payload=ProtocolPayload(
                message_type=message_type,
                data=data,
                metadata=metadata or {}
            )
        )
        
        bus_msg = protocol_msg.to_message_bus_message()
        count = await self._message_bus.broadcast(bus_msg)
        self._stats["messages_sent"] += 1
        
        return count
    
    async def request(
        self,
        target_agent: str,
        message_type: ProtocolMessageType,
        data: Dict[str, Any],
        timeout: float = 30.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProtocolResponse:
        """
        发送请求并等待响应 (请求-响应模式)
        
        Args:
            target_agent: 目标Agent ID
            message_type: 消息类型
            data: 请求数据
            timeout: 超时时间(秒)
            metadata: 元数据
            
        Returns:
            协议响应对象
        """
        start_time = datetime.utcnow()
        
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent=self._agent_id,
                target_agent=target_agent,
                reply_to=self._agent_id
            ),
            payload=ProtocolPayload(
                message_type=message_type,
                data=data,
                metadata=metadata or {}
            )
        )
        
        # 创建Future等待响应
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_responses[protocol_msg.header.message_id] = future
        
        try:
            # 发送请求
            bus_msg = protocol_msg.to_message_bus_message()
            success = await self._message_bus.send_direct(target_agent, bus_msg)
            
            if not success:
                return ProtocolResponse(
                    success=False,
                    status=ProtocolStatus.NOT_FOUND,
                    error=f"无法发送请求到Agent: {target_agent}"
                )
            
            self._stats["requests_sent"] += 1
            
            # 等待响应
            response_msg = await asyncio.wait_for(future, timeout=timeout)
            
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000
            
            return ProtocolResponse(
                success=response_msg.payload.status == ProtocolStatus.SUCCESS if response_msg.payload.status else True,
                status=response_msg.payload.status or ProtocolStatus.SUCCESS,
                message=response_msg,
                latency_ms=latency
            )
            
        except asyncio.TimeoutError:
            self._stats["timeouts"] += 1
            return ProtocolResponse(
                success=False,
                status=ProtocolStatus.TIMEOUT,
                error=f"请求超时 ({timeout}秒)"
            )
        except Exception as e:
            self._stats["errors"] += 1
            return ProtocolResponse(
                success=False,
                status=ProtocolStatus.INTERNAL_ERROR,
                error=str(e)
            )
        finally:
            self._pending_responses.pop(protocol_msg.header.message_id, None)
    
    async def ping(self, target_agent: str, timeout: float = 5.0) -> ProtocolResponse:
        """
        发送心跳检测
        
        Args:
            target_agent: 目标Agent ID
            timeout: 超时时间(秒)
            
        Returns:
            协议响应对象
        """
        return await self.request(
            target_agent,
            ProtocolMessageType.PING,
            {"timestamp": datetime.utcnow().isoformat()},
            timeout=timeout
        )
    
    async def report_conflict(
        self,
        conflict_type: str,
        involved_agents: List[str],
        details: Dict[str, Any]
    ) -> ProtocolResponse:
        """
        向导演Agent报告冲突
        
        需求: 1.3 - WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突
        
        Args:
            conflict_type: 冲突类型
            involved_agents: 涉及的Agent列表
            details: 冲突详情
            
        Returns:
            协议响应对象
        """
        return await self.request(
            "director",  # 导演Agent ID
            ProtocolMessageType.CONFLICT_REPORT,
            {
                "conflict_type": conflict_type,
                "involved_agents": involved_agents,
                "details": details,
                "reporter": self._agent_id
            },
            timeout=60.0  # 冲突解决可能需要更长时间
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取通信统计信息"""
        return {
            **self._stats,
            "agent_id": self._agent_id,
            "running": self._running,
            "pending_responses": len(self._pending_responses)
        }
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def is_running(self) -> bool:
        return self._running


# ============================================================================
# 便捷工厂函数
# ============================================================================

def create_protocol_message(
    source_agent: str,
    target_agent: Optional[str],
    message_type: ProtocolMessageType,
    data: Dict[str, Any],
    **kwargs
) -> ProtocolMessage:
    """创建协议消息的便捷函数"""
    return ProtocolMessage(
        header=ProtocolHeader(
            source_agent=source_agent,
            target_agent=target_agent,
            **{k: v for k, v in kwargs.items() if k in ProtocolHeader.__dataclass_fields__}
        ),
        payload=ProtocolPayload(
            message_type=message_type,
            data=data,
            **{k: v for k, v in kwargs.items() if k in ProtocolPayload.__dataclass_fields__}
        )
    )


def create_task_assignment(
    source_agent: str,
    target_agent: str,
    task_id: str,
    task_type: str,
    task_data: Dict[str, Any]
) -> ProtocolMessage:
    """创建任务分配消息"""
    return create_protocol_message(
        source_agent=source_agent,
        target_agent=target_agent,
        message_type=ProtocolMessageType.TASK_ASSIGN,
        data={
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data
        }
    )


def create_data_request(
    source_agent: str,
    target_agent: str,
    request_type: str,
    query: Dict[str, Any]
) -> ProtocolMessage:
    """创建数据请求消息"""
    return create_protocol_message(
        source_agent=source_agent,
        target_agent=target_agent,
        message_type=ProtocolMessageType.DATA_REQUEST,
        data={
            "request_type": request_type,
            "query": query
        }
    )
