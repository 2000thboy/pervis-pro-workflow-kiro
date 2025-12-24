"""
Agent初始化属性测试 - 基于属性的测试验证Agent初始化完整性

Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
验证需求: Requirements 1.1 - WHEN 系统启动时 THEN 系统 SHALL 初始化所有8个Agent并建立通信连接

测试策略:
- 使用Hypothesis生成随机的Agent配置
- 验证所有Agent类型都能成功初始化
- 验证初始化后Agent与消息总线建立连接
- 验证Agent状态正确转换
"""
import pytest
import asyncio
from typing import List, Dict, Any, Optional
from hypothesis import given, strategies as st, settings, assume

from app.core.message_bus import MessageBus, Message, MessageType
from app.agents.base_agent import BaseAgent, AgentLifecycleState, AgentOperationLog
from app.core.agent_types import AgentState, AgentType
from app.core.communication_protocol import ProtocolMessage, ProtocolMessageType


# 创建一个具体的Agent实现用于测试
class TestableAgent(BaseAgent):
    """可测试的Agent实现"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, message_bus: MessageBus, **kwargs):
        super().__init__(agent_id, agent_type, message_bus, **kwargs)
        self.received_messages: List[Message] = []
        self.received_protocol_messages: List[ProtocolMessage] = []
    
    async def handle_message(self, message: Message) -> None:
        """处理普通消息"""
        self.received_messages.append(message)
        return None
    
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        self.received_protocol_messages.append(message)
        return None


# 自定义策略：生成有效的Agent ID
agent_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=50
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成Agent类型
agent_type_strategy = st.sampled_from(list(AgentType))

# 自定义策略：生成能力列表
capabilities_strategy = st.lists(
    st.text(min_size=1, max_size=30).filter(lambda x: len(x.strip()) > 0),
    min_size=0,
    max_size=5,
    unique=True
)

# 自定义策略：生成配置字典
config_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda x: len(x.strip()) > 0),
    values=st.one_of(
        st.integers(),
        st.text(max_size=50),
        st.booleans()
    ),
    min_size=0,
    max_size=5
)


class TestAgentInitializationCompleteness:
    """
    属性 1: Agent初始化完整性
    
    *对于任何*系统启动操作，所有8个Agent（导演、系统、DAM、PM、编剧、美术、市场、后端）
    都应该成功初始化并建立与消息总线的连接
    
    验证需求: Requirements 1.1
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        agent_type=agent_type_strategy,
        capabilities=capabilities_strategy,
        config=config_strategy
    )
    async def test_agent_initialization_success(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str],
        config: Dict[str, Any]
    ):
        """
        Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
        
        属性: 对于任何有效的Agent配置，Agent都应该能够成功初始化
        并且初始化后处于正确的状态
        
        验证需求: Requirements 1.1
        """
        # 创建消息总线
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建Agent
            agent = TestableAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                message_bus=bus,
                capabilities=capabilities,
                config=config
            )
            
            # 验证属性1: Agent创建后处于CREATED状态
            assert agent.lifecycle_state == AgentLifecycleState.CREATED, \
                f"新创建的Agent应该处于CREATED状态，实际为{agent.lifecycle_state}"
            
            # 验证属性2: Agent工作状态为OFFLINE
            assert agent.work_state == AgentState.OFFLINE, \
                f"新创建的Agent工作状态应该为OFFLINE，实际为{agent.work_state}"
            
            # 执行初始化
            init_success = await agent.initialize()
            
            # 验证属性3: 初始化应该成功
            assert init_success is True, "Agent初始化应该成功"
            
            # 验证属性4: 初始化后处于READY状态
            assert agent.lifecycle_state == AgentLifecycleState.READY, \
                f"初始化后Agent应该处于READY状态，实际为{agent.lifecycle_state}"
            
            # 验证属性5: 初始化后工作状态为IDLE
            assert agent.work_state == AgentState.IDLE, \
                f"初始化后Agent工作状态应该为IDLE，实际为{agent.work_state}"
            
            # 验证属性6: Agent ID正确设置
            assert agent.agent_id == agent_id, \
                f"Agent ID应该为{agent_id}，实际为{agent.agent_id}"
            
            # 验证属性7: Agent类型正确设置
            assert agent.agent_type == agent_type, \
                f"Agent类型应该为{agent_type}，实际为{agent.agent_type}"
            
            # 验证属性8: 能力列表正确设置
            assert agent.capabilities == capabilities, \
                f"能力列表应该为{capabilities}，实际为{agent.capabilities}"
            
            # 验证属性9: 配置正确设置
            assert agent.config == config, \
                f"配置应该为{config}，实际为{agent.config}"
            
            # 验证属性10: 操作日志记录了初始化
            logs = agent.get_operation_logs()
            init_logs = [l for l in logs if l["operation"] == "agent_initialized"]
            assert len(init_logs) >= 1, "应该记录初始化操作日志"
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        agent_type=agent_type_strategy
    )
    async def test_agent_start_establishes_message_bus_connection(
        self,
        agent_id: str,
        agent_type: AgentType
    ):
        """
        Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
        
        属性: 对于任何Agent，启动后应该与消息总线建立连接，
        能够接收发送到其专属主题的消息
        
        验证需求: Requirements 1.1
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建并初始化Agent
            agent = TestableAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                message_bus=bus
            )
            
            await agent.initialize()
            
            # 启动Agent
            start_success = await agent.start()
            
            # 验证属性1: 启动应该成功
            assert start_success is True, "Agent启动应该成功"
            
            # 验证属性2: 启动后处于RUNNING状态
            assert agent.lifecycle_state == AgentLifecycleState.RUNNING, \
                f"启动后Agent应该处于RUNNING状态，实际为{agent.lifecycle_state}"
            
            # 验证属性3: Agent订阅了其专属主题
            subscribers = bus.get_subscribers(f"agent.{agent_id}")
            assert agent_id in subscribers, \
                f"Agent应该订阅了其专属主题agent.{agent_id}"
            
            # 验证属性4: Agent订阅了广播主题
            broadcast_subscribers = bus.get_subscribers("agent.broadcast")
            assert agent_id in broadcast_subscribers, \
                "Agent应该订阅了广播主题"
            
            # 验证属性5: Agent订阅了类型主题
            type_subscribers = bus.get_subscribers(f"agent.type.{agent_type.value}")
            assert agent_id in type_subscribers, \
                f"Agent应该订阅了类型主题agent.type.{agent_type.value}"
            
            # 验证属性6: is_running属性正确
            assert agent.is_running is True, "is_running应该为True"
            
            # 验证属性7: is_ready属性正确
            assert agent.is_ready is True, "is_ready应该为True"
            
            # 清理
            await agent.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        agent_types=st.lists(
            agent_type_strategy,
            min_size=1,
            max_size=8,
            unique=True
        )
    )
    async def test_multiple_agents_initialization(
        self,
        agent_types: List[AgentType]
    ):
        """
        Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
        
        属性: 对于任何Agent类型组合，所有Agent都应该能够同时初始化
        并且各自独立运行，互不干扰
        
        验证需求: Requirements 1.1
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        agents: List[TestableAgent] = []
        
        try:
            # 为每种类型创建一个Agent
            for i, agent_type in enumerate(agent_types):
                agent = TestableAgent(
                    agent_id=f"test_{agent_type.value}_{i}",
                    agent_type=agent_type,
                    message_bus=bus
                )
                agents.append(agent)
            
            # 并行初始化所有Agent
            init_results = await asyncio.gather(
                *[agent.initialize() for agent in agents]
            )
            
            # 验证属性1: 所有Agent都初始化成功
            assert all(init_results), \
                f"所有Agent都应该初始化成功，结果: {init_results}"
            
            # 并行启动所有Agent
            start_results = await asyncio.gather(
                *[agent.start() for agent in agents]
            )
            
            # 验证属性2: 所有Agent都启动成功
            assert all(start_results), \
                f"所有Agent都应该启动成功，结果: {start_results}"
            
            # 验证属性3: 所有Agent都处于RUNNING状态
            for agent in agents:
                assert agent.lifecycle_state == AgentLifecycleState.RUNNING, \
                    f"Agent {agent.agent_id} 应该处于RUNNING状态"
            
            # 验证属性4: 每个Agent都有独立的订阅
            for agent in agents:
                subscribers = bus.get_subscribers(f"agent.{agent.agent_id}")
                assert agent.agent_id in subscribers, \
                    f"Agent {agent.agent_id} 应该有独立的订阅"
            
            # 验证属性5: 消息总线统计正确
            stats = bus.get_stats()
            # 每个Agent订阅3个主题 (专属主题、广播主题、类型主题)
            # 但协议也会订阅2个主题 (专属主题、广播主题)
            # 所以每个Agent实际上有5个订阅
            expected_subscriptions = len(agents) * 5
            assert stats["active_subscriptions"] == expected_subscriptions, \
                f"活跃订阅数应该为{expected_subscriptions}，实际为{stats['active_subscriptions']}"
            
        finally:
            # 清理所有Agent
            for agent in agents:
                await agent.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        agent_type=agent_type_strategy
    )
    async def test_agent_lifecycle_state_transitions(
        self,
        agent_id: str,
        agent_type: AgentType
    ):
        """
        Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
        
        属性: 对于任何Agent，生命周期状态转换应该遵循正确的顺序:
        CREATED -> INITIALIZING -> READY -> RUNNING -> STOPPED
        
        验证需求: Requirements 1.1
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建Agent
            agent = TestableAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                message_bus=bus
            )
            
            # 验证初始状态
            assert agent.lifecycle_state == AgentLifecycleState.CREATED
            
            # 初始化
            await agent.initialize()
            assert agent.lifecycle_state == AgentLifecycleState.READY
            
            # 启动
            await agent.start()
            assert agent.lifecycle_state == AgentLifecycleState.RUNNING
            
            # 暂停
            await agent.pause()
            assert agent.lifecycle_state == AgentLifecycleState.PAUSED
            
            # 恢复
            await agent.resume()
            assert agent.lifecycle_state == AgentLifecycleState.RUNNING
            
            # 停止
            await agent.stop()
            assert agent.lifecycle_state == AgentLifecycleState.STOPPED
            
            # 验证操作日志记录了所有状态转换
            logs = agent.get_operation_logs()
            operations = [l["operation"] for l in logs]
            
            assert "agent_created" in operations, "应该记录创建操作"
            assert "agent_initialized" in operations, "应该记录初始化操作"
            assert "agent_started" in operations, "应该记录启动操作"
            assert "agent_paused" in operations, "应该记录暂停操作"
            assert "agent_resumed" in operations, "应该记录恢复操作"
            assert "agent_stopped" in operations, "应该记录停止操作"
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        agent_type=agent_type_strategy
    )
    async def test_agent_status_information_completeness(
        self,
        agent_id: str,
        agent_type: AgentType
    ):
        """
        Feature: multi-agent-workflow-core, Property 1: Agent初始化完整性
        
        属性: 对于任何Agent，get_status()应该返回完整的状态信息，
        包含所有必要的字段
        
        验证需求: Requirements 1.1
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            agent = TestableAgent(
                agent_id=agent_id,
                agent_type=agent_type,
                message_bus=bus,
                capabilities=["test_capability"]
            )
            
            await agent.initialize()
            await agent.start()
            
            # 获取状态
            status = agent.get_status()
            
            # 验证所有必要字段存在
            required_fields = [
                "agent_id",
                "agent_type",
                "lifecycle_state",
                "work_state",
                "current_task",
                "last_activity",
                "capabilities",
                "is_ready",
                "is_running"
            ]
            
            for field in required_fields:
                assert field in status, f"状态信息应该包含字段: {field}"
            
            # 验证字段值正确
            assert status["agent_id"] == agent_id
            assert status["agent_type"] == agent_type.value
            assert status["lifecycle_state"] == AgentLifecycleState.RUNNING.value
            assert status["work_state"] == AgentState.IDLE.value
            assert status["is_ready"] is True
            assert status["is_running"] is True
            assert "test_capability" in status["capabilities"]
            
            await agent.stop()
            
        finally:
            await bus.stop()
