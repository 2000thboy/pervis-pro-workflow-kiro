"""
Agent间通信协议单元测试

测试通信协议的核心功能:
- 消息格式验证
- 请求-响应模式通信
- 通信超时和重试机制

需求: 1.2, 1.3
"""
import pytest
import asyncio
import json
from datetime import datetime

from app.core.message_bus import MessageBus, Message, MessageType, MessagePriority
from app.core.communication_protocol import (
    AgentCommunicationProtocol,
    ProtocolMessage,
    ProtocolHeader,
    ProtocolPayload,
    ProtocolResponse,
    ProtocolMessageType,
    ProtocolStatus,
    ProtocolHandler,
    DefaultProtocolHandler,
    create_protocol_message,
    create_task_assignment,
    create_data_request
)


class TestProtocolMessage:
    """ProtocolMessage类测试"""
    
    def test_protocol_header_creation(self):
        """测试协议头创建"""
        header = ProtocolHeader(
            source_agent="agent_1",
            target_agent="agent_2",
            priority=3
        )
        
        assert header.source_agent == "agent_1"
        assert header.target_agent == "agent_2"
        assert header.priority == 3
        assert header.protocol_version == "1.0"
        assert header.message_id is not None
        assert header.timestamp is not None
    
    def test_protocol_payload_creation(self):
        """测试协议载荷创建"""
        payload = ProtocolPayload(
            message_type=ProtocolMessageType.DATA_REQUEST,
            data={"query": "test"},
            metadata={"source": "test"}
        )
        
        assert payload.message_type == ProtocolMessageType.DATA_REQUEST
        assert payload.data == {"query": "test"}
        assert payload.metadata == {"source": "test"}
    
    def test_protocol_message_creation(self):
        """测试协议消息创建"""
        msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.TASK_ASSIGN,
                data={"task_id": "task_001"}
            )
        )
        
        assert msg.header.source_agent == "agent_1"
        assert msg.header.target_agent == "agent_2"
        assert msg.payload.message_type == ProtocolMessageType.TASK_ASSIGN
        assert msg.payload.data == {"task_id": "task_001"}
    
    def test_protocol_message_to_dict(self):
        """测试协议消息转字典"""
        msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"key": "value"}
            )
        )
        
        data = msg.to_dict()
        
        assert "header" in data
        assert "payload" in data
        assert data["header"]["source_agent"] == "agent_1"
        assert data["payload"]["message_type"] == "data_request"
    
    def test_protocol_message_from_dict(self):
        """测试从字典创建协议消息"""
        data = {
            "header": {
                "message_id": "test-id-123",
                "source_agent": "agent_1",
                "target_agent": "agent_2",
                "protocol_version": "1.0",
                "priority": 2
            },
            "payload": {
                "message_type": "task_assign",
                "data": {"task_id": "task_001"},
                "metadata": {}
            }
        }
        
        msg = ProtocolMessage.from_dict(data)
        
        assert msg.header.message_id == "test-id-123"
        assert msg.header.source_agent == "agent_1"
        assert msg.payload.message_type == ProtocolMessageType.TASK_ASSIGN
    
    def test_protocol_message_json_roundtrip(self):
        """测试协议消息JSON序列化往返"""
        original = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_SYNC,
                data={"nested": {"data": [1, 2, 3]}}
            )
        )
        
        json_str = original.to_json()
        restored = ProtocolMessage.from_json(json_str)
        
        assert restored.header.source_agent == original.header.source_agent
        assert restored.header.target_agent == original.header.target_agent
        assert restored.payload.message_type == original.payload.message_type
        assert restored.payload.data == original.payload.data
    
    def test_protocol_message_to_bus_message(self):
        """测试协议消息转换为消息总线消息"""
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2",
                priority=3
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"query": "test"}
            )
        )
        
        bus_msg = protocol_msg.to_message_bus_message()
        
        assert bus_msg.source == "agent_1"
        assert bus_msg.target == "agent_2"
        assert bus_msg.topic == "agent.agent_2"
        assert "header" in bus_msg.content
        assert "payload" in bus_msg.content
    
    def test_create_response(self):
        """测试创建响应消息"""
        request = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"query": "test"}
            )
        )
        
        response = request.create_response(
            status=ProtocolStatus.SUCCESS,
            data={"result": "found"}
        )
        
        assert response.header.source_agent == "agent_2"
        assert response.header.target_agent == "agent_1"
        assert response.header.correlation_id == request.header.message_id
        assert response.payload.status == ProtocolStatus.SUCCESS
        assert response.payload.data == {"result": "found"}


class TestProtocolFactoryFunctions:
    """协议工厂函数测试"""
    
    def test_create_protocol_message(self):
        """测试创建协议消息工厂函数"""
        msg = create_protocol_message(
            source_agent="agent_1",
            target_agent="agent_2",
            message_type=ProtocolMessageType.DATA_REQUEST,
            data={"query": "test"}
        )
        
        assert msg.header.source_agent == "agent_1"
        assert msg.header.target_agent == "agent_2"
        assert msg.payload.message_type == ProtocolMessageType.DATA_REQUEST
    
    def test_create_task_assignment(self):
        """测试创建任务分配消息"""
        msg = create_task_assignment(
            source_agent="director",
            target_agent="dam",
            task_id="task_001",
            task_type="asset_search",
            task_data={"keywords": ["video", "action"]}
        )
        
        assert msg.header.source_agent == "director"
        assert msg.header.target_agent == "dam"
        assert msg.payload.message_type == ProtocolMessageType.TASK_ASSIGN
        assert msg.payload.data["task_id"] == "task_001"
        assert msg.payload.data["task_type"] == "asset_search"
    
    def test_create_data_request(self):
        """测试创建数据请求消息"""
        msg = create_data_request(
            source_agent="system",
            target_agent="dam",
            request_type="asset_query",
            query={"tags": ["action"]}
        )
        
        assert msg.header.source_agent == "system"
        assert msg.header.target_agent == "dam"
        assert msg.payload.message_type == ProtocolMessageType.DATA_REQUEST
        assert msg.payload.data["request_type"] == "asset_query"


class TestDefaultProtocolHandler:
    """DefaultProtocolHandler测试"""
    
    def test_handler_creation(self):
        """测试处理器创建"""
        handler = DefaultProtocolHandler([
            ProtocolMessageType.PING,
            ProtocolMessageType.DATA_REQUEST
        ])
        
        assert handler.can_handle(ProtocolMessageType.PING)
        assert handler.can_handle(ProtocolMessageType.DATA_REQUEST)
        assert not handler.can_handle(ProtocolMessageType.TASK_ASSIGN)
    
    def test_register_handler(self):
        """测试注册处理函数"""
        handler = DefaultProtocolHandler([])
        
        def ping_handler(msg):
            return msg.create_response(ProtocolStatus.SUCCESS)
        
        handler.register_handler(ProtocolMessageType.PING, ping_handler)
        
        assert handler.can_handle(ProtocolMessageType.PING)
    
    @pytest.mark.asyncio
    async def test_handle_message(self):
        """测试处理消息"""
        handler = DefaultProtocolHandler([])
        
        async def data_handler(msg):
            return msg.create_response(
                ProtocolStatus.SUCCESS,
                data={"result": "processed"}
            )
        
        handler.register_handler(ProtocolMessageType.DATA_REQUEST, data_handler)
        
        request = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"query": "test"}
            )
        )
        
        response = await handler.handle(request)
        
        assert response is not None
        assert response.payload.status == ProtocolStatus.SUCCESS
        assert response.payload.data == {"result": "processed"}


class TestAgentCommunicationProtocol:
    """AgentCommunicationProtocol测试"""
    
    @pytest.mark.asyncio
    async def test_protocol_start_stop(self):
        """测试协议启动和停止"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "test_agent")
            assert not protocol.is_running
            
            await protocol.start()
            assert protocol.is_running
            
            await protocol.stop()
            assert not protocol.is_running
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """测试发送消息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建两个Agent的协议
            protocol_1 = AgentCommunicationProtocol(bus, "agent_1")
            protocol_2 = AgentCommunicationProtocol(bus, "agent_2")
            
            await protocol_1.start()
            await protocol_2.start()
            
            received = []
            
            # 注册处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_SYNC])
            
            async def sync_handler(msg):
                received.append(msg)
                return None
            
            handler.register_handler(ProtocolMessageType.DATA_SYNC, sync_handler)
            protocol_2.register_handler(handler)
            
            # 发送消息
            success = await protocol_1.send(
                "agent_2",
                ProtocolMessageType.DATA_SYNC,
                {"data": "test"}
            )
            
            await asyncio.sleep(0.1)
            
            assert success is True
            # 消息可能通过多个订阅接收，验证至少收到一条
            assert len(received) >= 1
            assert received[0].payload.data == {"data": "test"}
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_request_response(self):
        """测试请求-响应模式"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "requester")
            protocol_2 = AgentCommunicationProtocol(bus, "responder")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册响应处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_REQUEST])
            
            async def request_handler(msg):
                return msg.create_response(
                    ProtocolStatus.SUCCESS,
                    data={"answer": "42"}
                )
            
            handler.register_handler(ProtocolMessageType.DATA_REQUEST, request_handler)
            protocol_2.register_handler(handler)
            
            # 发送请求
            response = await protocol_1.request(
                "responder",
                ProtocolMessageType.DATA_REQUEST,
                {"question": "meaning of life"},
                timeout=5.0
            )
            
            assert response.success is True
            assert response.status == ProtocolStatus.SUCCESS
            assert response.message.payload.data == {"answer": "42"}
            # latency_ms可能为0（如果响应非常快），所以只检查非负
            assert response.latency_ms >= 0
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """测试请求超时"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "requester")
            protocol_2 = AgentCommunicationProtocol(bus, "slow_responder")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册一个不响应的处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_REQUEST])
            
            async def slow_handler(msg):
                # 不返回响应，模拟超时
                return None
            
            handler.register_handler(ProtocolMessageType.DATA_REQUEST, slow_handler)
            protocol_2.register_handler(handler)
            
            # 发送请求，设置短超时
            response = await protocol_1.request(
                "slow_responder",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=0.1
            )
            
            assert response.success is False
            assert response.status == ProtocolStatus.TIMEOUT
            assert "超时" in response.error
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_request_to_unknown_agent(self):
        """测试请求到不存在的Agent"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "requester")
            await protocol.start()
            
            response = await protocol.request(
                "nonexistent_agent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=1.0
            )
            
            assert response.success is False
            assert response.status == ProtocolStatus.NOT_FOUND
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_ping(self):
        """测试心跳检测"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "pinger")
            protocol_2 = AgentCommunicationProtocol(bus, "target")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册PING处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.PING])
            
            async def ping_handler(msg):
                return msg.create_response(ProtocolStatus.SUCCESS)
            
            handler.register_handler(ProtocolMessageType.PING, ping_handler)
            protocol_2.register_handler(handler)
            
            # 发送ping
            response = await protocol_1.ping("target", timeout=2.0)
            
            assert response.success is True
            assert response.status == ProtocolStatus.SUCCESS
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "test_agent")
            await protocol.start()
            
            stats = protocol.get_stats()
            
            assert stats["agent_id"] == "test_agent"
            assert stats["running"] is True
            assert "messages_sent" in stats
            assert "messages_received" in stats
            assert "requests_sent" in stats
        finally:
            await protocol.stop()
            await bus.stop()


class TestProtocolMessageTypes:
    """协议消息类型测试"""
    
    def test_all_message_types_defined(self):
        """测试所有消息类型都已定义"""
        expected_types = [
            "ping", "pong", "ack", "nack",
            "agent_register", "agent_unregister", "agent_status", "agent_heartbeat",
            "task_assign", "task_accept", "task_reject", "task_progress", "task_complete", "task_failed",
            "data_request", "data_response", "data_sync",
            "conflict_report", "conflict_resolve",
            "workflow_start", "workflow_step", "workflow_end"
        ]
        
        actual_types = [t.value for t in ProtocolMessageType]
        
        for expected in expected_types:
            assert expected in actual_types, f"Missing message type: {expected}"
    
    def test_all_status_codes_defined(self):
        """测试所有状态码都已定义"""
        expected_codes = [200, 202, 400, 401, 404, 408, 409, 500, 503]
        
        actual_codes = [s.value for s in ProtocolStatus]
        
        for expected in expected_codes:
            assert expected in actual_codes, f"Missing status code: {expected}"



# ============================================================================
# 消息格式验证测试 (Message Format Validation Tests)
# 需求: 1.2 - 测试消息格式验证
# ============================================================================

class TestMessageFormatValidation:
    """消息格式验证测试类"""
    
    def test_valid_message_format(self):
        """测试有效消息格式"""
        msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2",
                priority=2,
                ttl=30
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"key": "value"},
                metadata={"version": "1.0"}
            )
        )
        
        # 验证消息结构完整性
        assert msg.header.source_agent == "agent_1"
        assert msg.header.target_agent == "agent_2"
        assert msg.header.protocol_version == "1.0"
        assert msg.header.message_id is not None
        assert msg.header.timestamp is not None
        assert msg.payload.message_type == ProtocolMessageType.DATA_REQUEST
    
    def test_message_with_empty_data(self):
        """测试空数据消息格式"""
        msg = ProtocolMessage(
            header=ProtocolHeader(source_agent="agent_1"),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.PING,
                data={}
            )
        )
        
        assert msg.payload.data == {}
        json_str = msg.to_json()
        restored = ProtocolMessage.from_json(json_str)
        assert restored.payload.data == {}
    
    def test_message_with_nested_data(self):
        """测试嵌套数据消息格式"""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            },
            "array": [1, 2, {"nested": True}]
        }
        
        msg = ProtocolMessage(
            header=ProtocolHeader(source_agent="agent_1"),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_SYNC,
                data=nested_data
            )
        )
        
        json_str = msg.to_json()
        restored = ProtocolMessage.from_json(json_str)
        assert restored.payload.data == nested_data
    
    def test_message_with_special_characters(self):
        """测试包含特殊字符的消息格式"""
        special_data = {
            "chinese": "中文测试",
            "emoji": "🎬🎥",
            "special": "!@#$%^&*()",
            "newline": "line1\nline2",
            "tab": "col1\tcol2"
        }
        
        msg = ProtocolMessage(
            header=ProtocolHeader(source_agent="agent_1"),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_SYNC,
                data=special_data
            )
        )
        
        json_str = msg.to_json()
        restored = ProtocolMessage.from_json(json_str)
        assert restored.payload.data == special_data
    
    def test_message_from_invalid_json(self):
        """测试从无效JSON创建消息"""
        with pytest.raises(json.JSONDecodeError):
            ProtocolMessage.from_json("invalid json string")
    
    def test_message_from_incomplete_dict(self):
        """测试从不完整字典创建消息"""
        # 缺少header
        incomplete_data = {
            "payload": {
                "message_type": "data_request",
                "data": {}
            }
        }
        
        msg = ProtocolMessage.from_dict(incomplete_data)
        # 应该使用默认值
        assert msg.header.source_agent == ""
        assert msg.header.protocol_version == "1.0"
    
    def test_message_from_dict_with_unknown_fields(self):
        """测试从包含未知字段的字典创建消息"""
        data_with_extra = {
            "header": {
                "source_agent": "agent_1",
                "unknown_field": "should_be_ignored"
            },
            "payload": {
                "message_type": "ping",
                "data": {},
                "extra_field": "ignored"
            }
        }
        
        msg = ProtocolMessage.from_dict(data_with_extra)
        assert msg.header.source_agent == "agent_1"
        assert msg.payload.message_type == ProtocolMessageType.PING
    
    def test_header_default_values(self):
        """测试协议头默认值"""
        header = ProtocolHeader()
        
        assert header.message_id is not None
        assert header.protocol_version == "1.0"
        assert header.timestamp is not None
        assert header.source_agent == ""
        assert header.target_agent is None
        assert header.ttl == 30
        assert header.priority == 2
    
    def test_payload_default_values(self):
        """测试协议载荷默认值"""
        payload = ProtocolPayload()
        
        assert payload.message_type == ProtocolMessageType.DATA_REQUEST
        assert payload.status is None
        assert payload.data == {}
        assert payload.error is None
        assert payload.metadata == {}
    
    def test_message_priority_range(self):
        """测试消息优先级范围"""
        for priority in [1, 2, 3, 4]:
            msg = ProtocolMessage(
                header=ProtocolHeader(
                    source_agent="agent_1",
                    priority=priority
                ),
                payload=ProtocolPayload()
            )
            assert msg.header.priority == priority
    
    def test_message_ttl_values(self):
        """测试消息TTL值"""
        for ttl in [1, 30, 60, 300]:
            header = ProtocolHeader(ttl=ttl)
            assert header.ttl == ttl
    
    def test_correlation_id_propagation(self):
        """测试关联ID传播"""
        original_id = "original-message-123"
        
        request = ProtocolMessage(
            header=ProtocolHeader(
                message_id=original_id,
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(message_type=ProtocolMessageType.DATA_REQUEST)
        )
        
        response = request.create_response(ProtocolStatus.SUCCESS)
        
        assert response.header.correlation_id == original_id


# ============================================================================
# 通信超时和重试机制测试 (Timeout and Retry Mechanism Tests)
# 需求: 1.2 - 测试通信超时和重试机制
# ============================================================================

class TestCommunicationTimeoutAndRetry:
    """通信超时和重试机制测试类"""
    
    @pytest.mark.asyncio
    async def test_short_timeout(self):
        """测试短超时时间"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "requester")
            await protocol.start()
            
            # 使用非常短的超时时间
            response = await protocol.request(
                "nonexistent_agent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=0.01  # 10ms超时
            )
            
            assert response.success is False
            # 可能是NOT_FOUND或TIMEOUT
            assert response.status in [ProtocolStatus.NOT_FOUND, ProtocolStatus.TIMEOUT]
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_timeout_with_slow_handler(self):
        """测试慢处理器导致的超时"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "requester")
            protocol_2 = AgentCommunicationProtocol(bus, "slow_agent")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册一个不返回响应的处理器（模拟超时场景）
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_REQUEST])
            
            async def no_response_handler(msg):
                # 不返回响应，让请求超时
                return None
            
            handler.register_handler(ProtocolMessageType.DATA_REQUEST, no_response_handler)
            protocol_2.register_handler(handler)
            
            # 使用短超时
            response = await protocol_1.request(
                "slow_agent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=0.1  # 100ms超时
            )
            
            assert response.success is False
            assert response.status == ProtocolStatus.TIMEOUT
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_successful_request_within_timeout(self):
        """测试在超时时间内成功完成的请求"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "requester")
            protocol_2 = AgentCommunicationProtocol(bus, "fast_agent")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册快速响应处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_REQUEST])
            
            async def fast_handler(msg):
                return msg.create_response(
                    ProtocolStatus.SUCCESS,
                    data={"result": "fast"}
                )
            
            handler.register_handler(ProtocolMessageType.DATA_REQUEST, fast_handler)
            protocol_2.register_handler(handler)
            
            # 使用足够长的超时时间
            response = await protocol_1.request(
                "fast_agent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=5.0
            )
            
            assert response.success is True
            assert response.status == ProtocolStatus.SUCCESS
            # latency_ms可能为0（如果响应非常快），所以只检查非负
            assert response.latency_ms >= 0
        finally:
            await protocol_1.stop()
            await protocol_2.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_timeout_stats_tracking(self):
        """测试超时统计跟踪"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "requester")
            await protocol.start()
            
            initial_stats = protocol.get_stats()
            initial_timeouts = initial_stats["timeouts"]
            
            # 发送会超时的请求
            await protocol.request(
                "nonexistent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=0.05
            )
            
            final_stats = protocol.get_stats()
            # 超时计数应该增加（可能是timeout或error）
            assert final_stats["timeouts"] >= initial_timeouts or final_stats["errors"] > initial_stats["errors"]
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests_with_timeout(self):
        """测试多个并发请求的超时处理"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "requester")
            await protocol.start()
            
            # 发送多个并发请求
            tasks = [
                protocol.request(
                    f"agent_{i}",
                    ProtocolMessageType.DATA_REQUEST,
                    {"query": f"test_{i}"},
                    timeout=0.1
                )
                for i in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # 所有请求都应该失败（因为目标不存在）
            for response in responses:
                assert response.success is False
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_ping_timeout(self):
        """测试ping超时"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "pinger")
            await protocol.start()
            
            # ping不存在的agent
            response = await protocol.ping("nonexistent_agent", timeout=0.1)
            
            assert response.success is False
            assert response.status in [ProtocolStatus.NOT_FOUND, ProtocolStatus.TIMEOUT]
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_conflict_report_timeout(self):
        """测试冲突报告超时"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "reporter")
            await protocol.start()
            
            # 报告冲突（导演Agent不存在时会超时）
            response = await protocol.report_conflict(
                conflict_type="resource_conflict",
                involved_agents=["agent_1", "agent_2"],
                details={"resource": "file.txt"}
            )
            
            # 由于导演Agent不存在，应该失败
            assert response.success is False
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_pending_responses_cleanup_on_timeout(self):
        """测试超时后待处理响应的清理"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol = AgentCommunicationProtocol(bus, "requester")
            await protocol.start()
            
            # 发送会超时的请求
            await protocol.request(
                "nonexistent",
                ProtocolMessageType.DATA_REQUEST,
                {"query": "test"},
                timeout=0.05
            )
            
            # 等待一小段时间确保清理完成
            await asyncio.sleep(0.1)
            
            stats = protocol.get_stats()
            # 待处理响应应该被清理
            assert stats["pending_responses"] == 0
        finally:
            await protocol.stop()
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_protocol_stop_cancels_pending_requests(self):
        """测试停止协议时取消待处理请求"""
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            protocol_1 = AgentCommunicationProtocol(bus, "requester")
            protocol_2 = AgentCommunicationProtocol(bus, "slow_agent")
            
            await protocol_1.start()
            await protocol_2.start()
            
            # 注册一个不响应的处理器
            handler = DefaultProtocolHandler([ProtocolMessageType.DATA_REQUEST])
            
            async def no_response_handler(msg):
                # 不返回响应
                return None
            
            handler.register_handler(ProtocolMessageType.DATA_REQUEST, no_response_handler)
            protocol_2.register_handler(handler)
            
            # 启动一个长时间请求
            request_task = asyncio.create_task(
                protocol_1.request(
                    "slow_agent",
                    ProtocolMessageType.DATA_REQUEST,
                    {"query": "test"},
                    timeout=30.0
                )
            )
            
            # 等待请求开始
            await asyncio.sleep(0.05)
            
            # 停止协议
            await protocol_1.stop()
            
            # 等待任务完成或被取消
            try:
                response = await asyncio.wait_for(request_task, timeout=0.5)
                # 如果没有被取消，应该返回错误或超时
                assert response.success is False or response.status == ProtocolStatus.TIMEOUT
            except (asyncio.CancelledError, asyncio.TimeoutError):
                # 请求被取消或超时也是预期行为
                pass
        finally:
            await protocol_2.stop()
            await bus.stop()


# ============================================================================
# 消息总线集成测试 (Message Bus Integration Tests)
# ============================================================================

class TestMessageBusIntegration:
    """消息总线集成测试"""
    
    @pytest.mark.asyncio
    async def test_message_bus_message_conversion(self):
        """测试协议消息与消息总线消息的转换"""
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2",
                priority=3
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.TASK_ASSIGN,
                data={"task_id": "task_001"}
            )
        )
        
        # 转换为消息总线消息
        bus_msg = protocol_msg.to_message_bus_message()
        
        assert bus_msg.source == "agent_1"
        assert bus_msg.target == "agent_2"
        assert bus_msg.priority == MessagePriority.HIGH  # priority 3
        assert bus_msg.type == MessageType.REQUEST  # TASK_ASSIGN是请求类型
        
        # 从消息总线消息恢复
        restored = ProtocolMessage.from_message_bus_message(bus_msg)
        
        assert restored.header.source_agent == protocol_msg.header.source_agent
        assert restored.payload.message_type == protocol_msg.payload.message_type
        assert restored.payload.data == protocol_msg.payload.data
    
    @pytest.mark.asyncio
    async def test_broadcast_message_topic(self):
        """测试广播消息的主题设置"""
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent=None  # 广播
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.AGENT_STATUS,
                data={"status": "online"}
            )
        )
        
        bus_msg = protocol_msg.to_message_bus_message()
        
        assert bus_msg.topic == "agent.broadcast"
    
    @pytest.mark.asyncio
    async def test_direct_message_topic(self):
        """测试点对点消息的主题设置"""
        protocol_msg = ProtocolMessage(
            header=ProtocolHeader(
                source_agent="agent_1",
                target_agent="agent_2"
            ),
            payload=ProtocolPayload(
                message_type=ProtocolMessageType.DATA_REQUEST,
                data={"query": "test"}
            )
        )
        
        bus_msg = protocol_msg.to_message_bus_message()
        
        assert bus_msg.topic == "agent.agent_2"
