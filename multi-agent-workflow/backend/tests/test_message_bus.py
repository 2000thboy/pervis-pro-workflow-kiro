"""
消息总线单元测试

测试MessageBus类的核心功能:
- 发布/订阅模式
- 消息路由和分发
- 请求-响应模式
"""
import pytest
import asyncio
from datetime import datetime

from app.core.message_bus import (
    MessageBus,
    Message,
    Response,
    MessageType,
    MessagePriority,
    Subscription
)


class TestMessage:
    """Message类测试"""
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = Message(
            source="agent_1",
            topic="test_topic",
            content={"key": "value"}
        )
        
        assert msg.source == "agent_1"
        assert msg.topic == "test_topic"
        assert msg.content == {"key": "value"}
        assert msg.type == MessageType.EVENT
        assert msg.priority == MessagePriority.NORMAL
        assert msg.id is not None
        assert msg.timestamp is not None
    
    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = Message(
            source="agent_1",
            topic="test_topic",
            content={"data": 123}
        )
        
        data = msg.to_dict()
        
        assert data["source"] == "agent_1"
        assert data["topic"] == "test_topic"
        assert data["content"] == {"data": 123}
        assert data["type"] == "event"
        assert data["priority"] == 2
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        data = {
            "id": "test-id-123",
            "type": "command",
            "source": "agent_2",
            "topic": "commands",
            "content": {"action": "start"},
            "priority": 3
        }
        
        msg = Message.from_dict(data)
        
        assert msg.id == "test-id-123"
        assert msg.type == MessageType.COMMAND
        assert msg.source == "agent_2"
        assert msg.topic == "commands"
        assert msg.content == {"action": "start"}
        assert msg.priority == MessagePriority.HIGH
    
    def test_message_json_roundtrip(self):
        """测试消息JSON序列化往返"""
        original = Message(
            source="agent_1",
            topic="test",
            content={"nested": {"data": [1, 2, 3]}}
        )
        
        json_str = original.to_json()
        restored = Message.from_json(json_str)
        
        assert restored.source == original.source
        assert restored.topic == original.topic
        assert restored.content == original.content


class TestMessageBusBasic:
    """MessageBus基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_bus_start_stop(self):
        """测试消息总线启动和停止"""
        bus = MessageBus(max_history=100)
        assert not bus.is_running
        
        await bus.start()
        assert bus.is_running
        
        await bus.stop()
        assert not bus.is_running
    
    @pytest.mark.asyncio
    async def test_subscribe(self):
        """测试订阅功能"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            received = []
            
            async def handler(msg):
                received.append(msg)
            
            sub_id = await bus.subscribe("agent_1", "test_topic", handler)
            
            assert sub_id is not None
            assert "agent_1" in bus.get_subscribers("test_topic")
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """测试取消订阅"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def handler(msg):
                pass
            
            sub_id = await bus.subscribe("agent_1", "test_topic", handler)
            assert "agent_1" in bus.get_subscribers("test_topic")
            
            result = await bus.unsubscribe(sub_id)
            assert result is True
            assert "agent_1" not in bus.get_subscribers("test_topic")
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_all(self):
        """测试取消所有订阅"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def handler(msg):
                pass
            
            await bus.subscribe("agent_1", "topic_1", handler)
            await bus.subscribe("agent_1", "topic_2", handler)
            await bus.subscribe("agent_1", "topic_3", handler)
            
            count = await bus.unsubscribe_all("agent_1")
            
            assert count == 3
            assert "agent_1" not in bus.get_subscribers("topic_1")
            assert "agent_1" not in bus.get_subscribers("topic_2")
            assert "agent_1" not in bus.get_subscribers("topic_3")
        finally:
            await bus.stop()



class TestMessageBusPublishSubscribe:
    """发布/订阅模式测试"""
    
    @pytest.mark.asyncio
    async def test_publish_single_subscriber(self):
        """测试单个订阅者接收消息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            received = []
            
            async def handler(msg):
                received.append(msg)
            
            await bus.subscribe("agent_1", "events", handler)
            
            msg = Message(source="agent_2", content={"event": "test"})
            count = await bus.publish("events", msg)
            
            await asyncio.sleep(0.1)
            
            assert count == 1
            assert len(received) == 1
            assert received[0].content == {"event": "test"}
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers(self):
        """测试多个订阅者接收消息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            received_1 = []
            received_2 = []
            
            async def handler_1(msg):
                received_1.append(msg)
            
            async def handler_2(msg):
                received_2.append(msg)
            
            await bus.subscribe("agent_1", "events", handler_1)
            await bus.subscribe("agent_2", "events", handler_2)
            
            msg = Message(source="agent_3", content={"data": "shared"})
            count = await bus.publish("events", msg)
            
            await asyncio.sleep(0.1)
            
            assert count == 2
            assert len(received_1) == 1
            assert len(received_2) == 1
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        """测试无订阅者时发布消息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            msg = Message(source="agent_1", content={"data": "test"})
            count = await bus.publish("empty_topic", msg)
            
            assert count == 0
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_with_filter(self):
        """测试带过滤器的订阅"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            received = []
            
            async def handler(msg):
                received.append(msg)
            
            def filter_high_priority(msg):
                return msg.priority == MessagePriority.HIGH
            
            await bus.subscribe(
                "agent_1", "events", handler, 
                filter_func=filter_high_priority
            )
            
            # 发送普通优先级消息
            msg_normal = Message(
                source="agent_2", 
                content={"type": "normal"},
                priority=MessagePriority.NORMAL
            )
            await bus.publish("events", msg_normal)
            
            # 发送高优先级消息
            msg_high = Message(
                source="agent_2", 
                content={"type": "high"},
                priority=MessagePriority.HIGH
            )
            await bus.publish("events", msg_high)
            
            await asyncio.sleep(0.1)
            
            # 只应该收到高优先级消息
            assert len(received) == 1
            assert received[0].content == {"type": "high"}
        finally:
            await bus.stop()


class TestMessageBusDirectMessaging:
    """点对点消息测试"""
    
    @pytest.mark.asyncio
    async def test_send_direct(self):
        """测试点对点消息发送"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            received = []
            
            async def handler(msg):
                received.append(msg)
            
            await bus.subscribe("target_agent", "direct", handler)
            
            msg = Message(source="sender_agent", content={"direct": True})
            success = await bus.send_direct("target_agent", msg)
            
            await asyncio.sleep(0.1)
            
            assert success is True
            assert len(received) == 1
            assert received[0].type == MessageType.DIRECT
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_send_direct_unknown_target(self):
        """测试发送到未知目标"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            msg = Message(source="sender", content={"data": "test"})
            success = await bus.send_direct("unknown_agent", msg)
            
            assert success is False
        finally:
            await bus.stop()


class TestMessageBusRequestResponse:
    """请求-响应模式测试"""
    
    @pytest.mark.asyncio
    async def test_send_response(self):
        """测试发送响应功能"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建一个pending request
            correlation_id = "test-correlation-123"
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            bus._pending_requests[correlation_id] = future
            
            # 发送响应
            result = await bus.send_response(
                correlation_id,
                {"result": "success"}
            )
            
            assert result is True
            assert future.done()
            assert future.result() == {"result": "success"}
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_request_response_timeout(self):
        """测试请求超时"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def slow_responder(msg):
                # 不发送响应，模拟超时
                pass
            
            await bus.subscribe("slow_agent", "requests", slow_responder)
            
            request = Message(source="requester", content={"query": "test"})
            
            response = await bus.request_response(
                "slow_agent", request, timeout=0.1
            )
            
            assert response.success is False
            assert "超时" in response.error
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_request_response_no_target(self):
        """测试请求到不存在的目标"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            request = Message(source="requester", content={"query": "test"})
            
            response = await bus.request_response(
                "nonexistent_agent", request, timeout=1.0
            )
            
            assert response.success is False
            assert "无法发送请求" in response.error
        finally:
            await bus.stop()


class TestMessageBusHistory:
    """消息历史测试"""
    
    @pytest.mark.asyncio
    async def test_message_history(self):
        """测试消息历史记录"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def handler(msg):
                pass
            
            await bus.subscribe("agent_1", "events", handler)
            
            # 发送多条消息
            for i in range(5):
                msg = Message(source=f"agent_{i}", content={"index": i})
                await bus.publish("events", msg)
            
            history = bus.get_history(limit=10)
            
            assert len(history) == 5
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_history_filter_by_topic(self):
        """测试按主题过滤历史"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def handler(msg):
                pass
            
            await bus.subscribe("agent_1", "topic_a", handler)
            await bus.subscribe("agent_1", "topic_b", handler)
            
            await bus.publish("topic_a", Message(source="a", content={}))
            await bus.publish("topic_b", Message(source="b", content={}))
            await bus.publish("topic_a", Message(source="a", content={}))
            
            history_a = bus.get_history(topic="topic_a")
            history_b = bus.get_history(topic="topic_b")
            
            assert len(history_a) == 2
            assert len(history_b) == 1
        finally:
            await bus.stop()


class TestMessageBusStats:
    """统计信息测试"""
    
    @pytest.mark.asyncio
    async def test_stats(self):
        """测试统计信息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            async def handler(msg):
                pass
            
            await bus.subscribe("agent_1", "events", handler)
            await bus.subscribe("agent_2", "events", handler)
            
            msg = Message(source="sender", content={})
            await bus.publish("events", msg)
            
            stats = bus.get_stats()
            
            assert stats["messages_published"] == 1
            assert stats["messages_delivered"] == 2
            assert stats["active_subscriptions"] == 2
            assert "events" in stats["topics"]
        finally:
            await bus.stop()
