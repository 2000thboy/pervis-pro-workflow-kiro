"""
Pervis PRO 核心模块

包含:
- MessageBus: Agent间消息总线
- AgentTypes: Agent类型和状态定义
- CommunicationProtocol: Agent通信协议
- BaseAgent: Agent基类
"""

from .message_bus import (
    MessageBus,
    Message,
    MessageType,
    MessagePriority,
    Response,
    Subscription,
    message_bus
)

from .agent_types import (
    AgentState,
    AgentType
)

from .communication_protocol import (
    AgentCommunicationProtocol,
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
    ProtocolHeader,
    ProtocolPayload,
    ProtocolResponse,
    ProtocolHandler,
    DefaultProtocolHandler,
    create_protocol_message,
    create_task_assignment,
    create_data_request
)

from .base_agent import (
    BaseAgent,
    AgentLifecycleState,
    AgentOperationLog
)

__all__ = [
    # Message Bus
    'MessageBus',
    'Message',
    'MessageType',
    'MessagePriority',
    'Response',
    'Subscription',
    'message_bus',
    # Agent Types
    'AgentState',
    'AgentType',
    # Communication Protocol
    'AgentCommunicationProtocol',
    'ProtocolMessage',
    'ProtocolMessageType',
    'ProtocolStatus',
    'ProtocolHeader',
    'ProtocolPayload',
    'ProtocolResponse',
    'ProtocolHandler',
    'DefaultProtocolHandler',
    'create_protocol_message',
    'create_task_assignment',
    'create_data_request',
    # Base Agent
    'BaseAgent',
    'AgentLifecycleState',
    'AgentOperationLog',
]
