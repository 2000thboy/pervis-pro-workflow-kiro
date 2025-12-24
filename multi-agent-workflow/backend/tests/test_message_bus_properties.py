"""
消息总线属性测试 - 基于属性的测试验证消息总线通信一致性

Feature: multi-agent-workflow-core, Property 2: 消息总线通信一致性
验证需求: Requirements 1.2 - WHEN Agent间需要数据交换时 THEN 系统 SHALL 通过统一的消息总线进行通信

测试策略:
- 使用Hypothesis生成随机的Agent ID、主题和消息内容
- 验证所有Agent间通信都必须通过消息总线进行
- 验证消息在发布后能被所有订阅者正确接收
- 验证消息内容在传输过程中保持一致性
"""
import pytest
import asyncio
from typing import List, Dict, Any, Set
from hypothesis import given, strategies as st, settings, assume

from app.core.message_bus import (
    MessageBus,
    Message,
    MessageType,
    MessagePriority,
)


# 自定义策略：生成有效的Agent ID
agent_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=50
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成有效的主题名称
topic_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-.'),
    min_size=1,
    max_size=100
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成消息内容
content_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda x: len(x.strip()) > 0),
    values=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.booleans(),
        st.none()
    ),
    min_size=0,
    max_size=10
)

# 自定义策略：生成消息优先级
priority_strategy = st.sampled_from(list(MessagePriority))


class TestMessageBusCommunicationConsistency:
    """
    属性 2: 消息总线通信一致性
    
    *对于任何*Agent间的数据交换，通信都应该通过统一的消息总线进行，
    不存在直接的点对点通信
    
    验证需求: Requirements 1.2
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        source_agent=agent_id_strategy,
        subscriber_agents=st.lists(agent_id_strategy, min_size=1, max_size=5, unique=True),
        topic=topic_strategy,
        content=content_strategy
    )
    async def test_all_communication_through_message_bus(
        self,
        source_agent: str,
        subscriber_agents: List[str],
        topic: str,
        content: Dict[str, Any]
    ):
        """
        Feature: multi-agent-workflow-core, Property 2: 消息总线通信一致性
        
        属性: 对于任何源Agent发送的消息，所有订阅该主题的Agent都应该
        通过消息总线接收到完全相同的消息内容
        
        验证需求: Requirements 1.2
        """
        # 确保源Agent不在订阅者列表中
        assume(source_agent not in subscriber_agents)
        
        # 创建消息总线实例
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        try:
            # 记录每个订阅者收到的消息
            received_messages: Dict[str, List[Message]] = {
                agent: [] for agent in subscriber_agents
            }
            
            # 为每个订阅者创建处理函数并订阅
            for agent_id in subscriber_agents:
                async def create_handler(aid):
                    async def handler(msg: Message):
                        received_messages[aid].append(msg)
                    return handler
                
                handler = await create_handler(agent_id)
                await bus.subscribe(agent_id, topic, handler)
            
            # 发送消息
            original_message = Message(
                source=source_agent,
                topic=topic,
                content=content,
                type=MessageType.EVENT
            )
            
            delivered_count = await bus.publish(topic, original_message)
            
            # 等待异步处理完成
            await asyncio.sleep(0.1)
            
            # 验证属性1: 所有订阅者都收到了消息
            assert delivered_count == len(subscriber_agents), \
                f"消息应该被投递给所有{len(subscriber_agents)}个订阅者，实际投递{delivered_count}个"
            
            # 验证属性2: 每个订阅者收到的消息内容与原始消息一致
            for agent_id in subscriber_agents:
                assert len(received_messages[agent_id]) == 1, \
                    f"Agent {agent_id} 应该收到1条消息，实际收到{len(received_messages[agent_id])}条"
                
                received = received_messages[agent_id][0]
                
                # 验证消息内容一致性
                assert received.content == content, \
                    f"Agent {agent_id} 收到的消息内容不一致"
                assert received.source == source_agent, \
                    f"Agent {agent_id} 收到的消息源不一致"
                assert received.topic == topic, \
                    f"Agent {agent_id} 收到的消息主题不一致"
            
            # 验证属性3: 消息历史记录正确
            history = bus.get_history(topic=topic)
            assert len(history) == 1, "消息历史应该记录1条消息"
            assert history[0].content == content, "历史记录的消息内容应该一致"
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        agents=st.lists(agent_id_strategy, min_size=2, max_size=4, unique=True),
        topics=st.lists(topic_strategy, min_size=1, max_size=2, unique=True),
        message_count=st.integers(min_value=1, max_value=5)
    )
    async def test_message_bus_is_single_communication_channel(
        self,
        agents: List[str],
        topics: List[str],
        message_count: int
    ):
        """
        Feature: multi-agent-workflow-core, Property 2: 消息总线通信一致性
        
        属性: 对于任何多Agent系统，所有消息交换都必须通过统一的消息总线，
        消息总线的统计信息应该准确反映所有通信活动
        
        验证需求: Requirements 1.2
        """
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        try:
            # 记录所有收到的消息
            all_received: List[Message] = []
            
            # 所有Agent订阅所有主题
            for agent_id in agents:
                for topic in topics:
                    async def create_handler():
                        async def handler(msg: Message):
                            all_received.append(msg)
                        return handler
                    
                    handler = await create_handler()
                    await bus.subscribe(agent_id, topic, handler)
            
            # 每个Agent向每个主题发送消息
            total_messages_sent = 0
            expected_deliveries = 0
            
            for sender in agents:
                for topic in topics:
                    for i in range(message_count):
                        msg = Message(
                            source=sender,
                            content={"sender": sender, "topic": topic, "index": i}
                        )
                        delivered = await bus.publish(topic, msg)
                        total_messages_sent += 1
                        expected_deliveries += len(agents)  # 每条消息应该被所有订阅者收到
            
            await asyncio.sleep(0.2)
            
            # 验证统计信息
            stats = bus.get_stats()
            
            # 验证属性: 消息总线统计准确反映所有通信
            assert stats["messages_published"] == total_messages_sent, \
                f"发布消息数应为{total_messages_sent}，实际为{stats['messages_published']}"
            
            assert stats["messages_delivered"] == expected_deliveries, \
                f"投递消息数应为{expected_deliveries}，实际为{stats['messages_delivered']}"
            
            # 验证所有消息都通过消息总线传递
            assert len(all_received) == expected_deliveries, \
                f"收到的消息数应为{expected_deliveries}，实际为{len(all_received)}"
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        source=agent_id_strategy,
        target=agent_id_strategy,
        content=content_strategy
    )
    async def test_direct_messages_go_through_bus(
        self,
        source: str,
        target: str,
        content: Dict[str, Any]
    ):
        """
        Feature: multi-agent-workflow-core, Property 2: 消息总线通信一致性
        
        属性: 即使是点对点的直接消息，也必须通过消息总线进行路由，
        确保没有绕过消息总线的直接通信
        
        验证需求: Requirements 1.2
        """
        assume(source != target)
        
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        try:
            received_messages: List[Message] = []
            
            # 目标Agent订阅一个主题
            async def handler(msg: Message):
                received_messages.append(msg)
            
            await bus.subscribe(target, "direct_channel", handler)
            
            # 发送直接消息
            msg = Message(
                source=source,
                content=content,
                type=MessageType.DIRECT
            )
            
            success = await bus.send_direct(target, msg)
            await asyncio.sleep(0.1)
            
            # 验证属性: 直接消息通过消息总线传递
            assert success is True, "直接消息应该成功发送"
            assert len(received_messages) == 1, "目标Agent应该收到1条消息"
            
            # 验证消息类型被正确标记为DIRECT
            assert received_messages[0].type == MessageType.DIRECT, \
                "消息类型应该是DIRECT"
            
            # 验证消息内容一致
            assert received_messages[0].content == content, \
                "消息内容应该保持一致"
            assert received_messages[0].target == target, \
                "消息目标应该正确设置"
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        content=content_strategy,
        priority=priority_strategy
    )
    async def test_message_integrity_through_bus(
        self,
        content: Dict[str, Any],
        priority: MessagePriority
    ):
        """
        Feature: multi-agent-workflow-core, Property 2: 消息总线通信一致性
        
        属性: 消息通过消息总线传输后，其所有属性（内容、优先级等）
        应该保持完整性，不发生任何改变
        
        验证需求: Requirements 1.2
        """
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        try:
            received: List[Message] = []
            
            async def handler(msg: Message):
                received.append(msg)
            
            await bus.subscribe("receiver", "integrity_test", handler)
            
            # 创建带有所有属性的消息
            original = Message(
                source="sender",
                topic="integrity_test",
                content=content,
                priority=priority,
                type=MessageType.EVENT
            )
            original_id = original.id
            original_timestamp = original.timestamp
            
            await bus.publish("integrity_test", original)
            await asyncio.sleep(0.1)
            
            # 验证消息完整性
            assert len(received) == 1, "应该收到1条消息"
            
            msg = received[0]
            assert msg.id == original_id, "消息ID应该保持不变"
            assert msg.content == content, "消息内容应该保持不变"
            assert msg.priority == priority, "消息优先级应该保持不变"
            assert msg.source == "sender", "消息源应该保持不变"
            assert msg.timestamp == original_timestamp, "消息时间戳应该保持不变"
            
        finally:
            await bus.stop()
