# -*- coding: utf-8 -*-
"""
系统级属性测试

验证系统级别的正确性属性：
- 属性 4: Agent操作日志完整性
- 属性 35: AI使用记录完整性

Feature: multi-agent-workflow-core
Requirements: 1.4, 6.5
"""
import asyncio
import pytest
from datetime import datetime
from hypothesis import given, settings, strategies as st
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# 导入被测试的模块
from app.core.message_bus import MessageBus, Message, MessageType
from app.core.agent_types import AgentType, AgentState
from app.core.llm_service import (
    LLMService, LLMConfig, LLMProvider, LLMMessage, LLMRole,
    AIUsageRecord
)
from app.agents.base_agent import BaseAgent, AgentOperationLog, AgentLifecycleState


# =============================================================================
# 测试用具体Agent实现
# =============================================================================

class TestableAgent(BaseAgent):
    """可测试的Agent实现"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.SYSTEM,
            message_bus=message_bus,
            capabilities=["test"]
        )
        self._custom_operations: List[str] = []
    
    async def _on_initialize(self) -> bool:
        """初始化回调"""
        return True
    
    async def _on_start(self) -> bool:
        """启动回调"""
        return True
    
    async def _on_pause(self) -> bool:
        """暂停回调"""
        return True
    
    async def _on_resume(self) -> bool:
        """恢复回调"""
        return True
    
    async def _on_stop(self) -> bool:
        """停止回调"""
        return True
    
    async def handle_message(self, message: Message) -> Optional[Any]:
        """处理消息"""
        self._log_operation(
            "message_handled",
            details={"message_id": message.id, "type": message.type.value}
        )
        return {"status": "handled"}
    
    async def handle_protocol_message(self, message: Any) -> Optional[Any]:
        """处理协议消息"""
        self._log_operation(
            "protocol_message_handled",
            details={"message": str(message)}
        )
        return None
    
    async def perform_custom_operation(self, operation_name: str, details: Dict[str, Any] = None):
        """执行自定义操作并记录日志"""
        self._custom_operations.append(operation_name)
        self._log_operation(
            operation_name,
            details=details or {},
            success=True
        )
    
    async def perform_failing_operation(self, operation_name: str, error_msg: str):
        """执行失败的操作并记录日志"""
        self._log_operation(
            operation_name,
            details={"attempted": True},
            success=False,
            error=error_msg
        )
    
    def get_custom_operations(self) -> List[str]:
        """获取自定义操作列表"""
        return self._custom_operations.copy()


# =============================================================================
# 策略定义
# =============================================================================

# 操作名称策略 - 使用显式ASCII字符集
operation_name_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz_',
    min_size=3,
    max_size=30
)

# 操作详情策略
operation_details_strategy = st.dictionaries(
    keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=1, max_size=20),
    values=st.one_of(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789 ', min_size=0, max_size=50),
        st.integers(min_value=-1000, max_value=1000),
        st.booleans()
    ),
    min_size=0,
    max_size=5
)

# 操作序列策略
operation_sequence_strategy = st.lists(
    st.tuples(operation_name_strategy, operation_details_strategy),
    min_size=1,
    max_size=20
)

# AI操作类型策略
ai_operation_strategy = st.sampled_from([
    "chat", "complete", "generate", "validate", "analyze",
    "assist_script", "assist_art", "advice_market"
])

# 提示文本策略
prompt_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789 .,!?',
    min_size=10,
    max_size=200
)


# =============================================================================
# 属性 4: Agent操作日志完整性
# Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
# 验证需求: Requirements 1.4
# =============================================================================

class TestAgentOperationLogCompleteness:
    """
    属性 4: Agent操作日志完整性
    
    *对于任何*Agent执行的任务，系统都应该记录完整的状态变化和操作日志
    **验证需求: Requirements 1.4**
    """
    
    @pytest.fixture
    def message_bus(self):
        """创建消息总线"""
        return MessageBus()
    
    @pytest.fixture
    def agent(self, message_bus):
        """创建测试Agent"""
        return TestableAgent("test-agent-001", message_bus)
    
    @given(operations=operation_sequence_strategy)
    @settings(max_examples=100, deadline=None)
    def test_all_operations_are_logged(self, operations):
        """
        属性测试: 所有操作都应该被记录到日志中
        
        Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
        验证需求: Requirements 1.4
        """
        async def run_test():
            message_bus = MessageBus()
            agent = TestableAgent("test-agent", message_bus)
            
            # 执行所有操作
            for op_name, op_details in operations:
                await agent.perform_custom_operation(op_name, op_details)
            
            # 获取操作日志
            logs = agent.get_operation_logs()
            logged_operations = [log["operation"] for log in logs]
            
            # 验证: 每个执行的操作都应该在日志中
            for op_name, _ in operations:
                assert op_name in logged_operations, \
                    f"操作 '{op_name}' 应该被记录在日志中"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(
        operation_name=operation_name_strategy,
        details=operation_details_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_log_contains_required_fields(self, operation_name, details):
        """
        属性测试: 每条日志都应该包含必要的字段
        
        Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
        验证需求: Requirements 1.4
        """
        async def run_test():
            message_bus = MessageBus()
            agent = TestableAgent("test-agent", message_bus)
            
            # 执行操作
            await agent.perform_custom_operation(operation_name, details)
            
            # 获取最新日志
            logs = agent.get_operation_logs(limit=1)
            assert len(logs) >= 1, "应该至少有一条日志"
            
            latest_log = logs[-1]
            
            # 验证必要字段存在
            required_fields = ["timestamp", "operation", "success"]
            for field in required_fields:
                assert field in latest_log, f"日志应该包含字段 '{field}'"
            
            # 验证操作名称正确
            assert latest_log["operation"] == operation_name, \
                "日志中的操作名称应该与执行的操作一致"
            
            # 验证时间戳格式有效
            try:
                datetime.fromisoformat(latest_log["timestamp"])
            except ValueError:
                pytest.fail("时间戳格式应该是有效的ISO格式")
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(
        success_ops=st.lists(operation_name_strategy, min_size=1, max_size=5),
        fail_ops=st.lists(
            st.tuples(operation_name_strategy, st.text(min_size=5, max_size=50)),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_success_and_failure_both_logged(self, success_ops, fail_ops):
        """
        属性测试: 成功和失败的操作都应该被记录
        
        Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
        验证需求: Requirements 1.4
        """
        async def run_test():
            message_bus = MessageBus()
            agent = TestableAgent("test-agent", message_bus)
            
            # 执行成功的操作
            for op_name in success_ops:
                await agent.perform_custom_operation(op_name)
            
            # 执行失败的操作
            for op_name, error_msg in fail_ops:
                await agent.perform_failing_operation(op_name, error_msg)
            
            # 获取所有日志
            logs = agent.get_operation_logs()
            
            # 统计成功和失败的日志
            success_logs = [l for l in logs if l.get("success", True)]
            failure_logs = [l for l in logs if not l.get("success", True)]
            
            # 验证: 成功操作被记录
            success_op_names = [l["operation"] for l in success_logs]
            for op_name in success_ops:
                assert op_name in success_op_names, \
                    f"成功操作 '{op_name}' 应该被记录"
            
            # 验证: 失败操作被记录
            failure_op_names = [l["operation"] for l in failure_logs]
            for op_name, _ in fail_ops:
                assert op_name in failure_op_names, \
                    f"失败操作 '{op_name}' 应该被记录"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(num_operations=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100, deadline=None)
    def test_log_order_preserved(self, num_operations):
        """
        属性测试: 日志应该按时间顺序保存
        
        Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
        验证需求: Requirements 1.4
        """
        async def run_test():
            message_bus = MessageBus()
            agent = TestableAgent("test-agent", message_bus)
            
            # 执行一系列操作
            for i in range(num_operations):
                await agent.perform_custom_operation(f"operation_{i}")
            
            # 获取日志
            logs = agent.get_operation_logs()
            
            # 验证日志按时间顺序排列
            timestamps = [l["timestamp"] for l in logs]
            for i in range(len(timestamps) - 1):
                assert timestamps[i] <= timestamps[i + 1], \
                    "日志应该按时间顺序排列"
        
        asyncio.get_event_loop().run_until_complete(run_test())



# =============================================================================
# 属性 35: AI使用记录完整性
# Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
# 验证需求: Requirements 6.5
# =============================================================================

class TestAIUsageRecordCompleteness:
    """
    属性 35: AI使用记录完整性
    
    *对于任何*AI辅助操作，系统应该完整记录AI使用情况用于MVP验证
    **验证需求: Requirements 6.5**
    """
    
    @pytest.fixture
    def llm_service(self):
        """创建LLM服务（使用Mock配置）"""
        config = LLMConfig.mock()
        service = LLMService(config)
        return service
    
    @given(
        operation=ai_operation_strategy,
        prompt=prompt_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_all_ai_operations_recorded(self, operation, prompt):
        """
        属性测试: 所有AI操作都应该被记录
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行AI操作
            messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
            await service.chat(messages, operation=operation)
            
            # 获取使用记录
            records = service.get_usage_records()
            
            # 验证: 操作被记录
            assert len(records) >= 1, "AI操作应该被记录"
            
            # 验证: 记录包含正确的操作类型
            operations_recorded = [r.operation for r in records]
            assert operation in operations_recorded, \
                f"操作 '{operation}' 应该被记录"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(
        operations=st.lists(
            st.tuples(ai_operation_strategy, prompt_strategy),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_usage_record_contains_required_fields(self, operations):
        """
        属性测试: 每条AI使用记录都应该包含必要的字段
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行多个AI操作
            for operation, prompt in operations:
                messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
                await service.chat(messages, operation=operation)
            
            # 获取使用记录
            records = service.get_usage_records()
            
            # 验证每条记录包含必要字段
            for record in records:
                assert record.id is not None, "记录应该有ID"
                assert record.provider is not None, "记录应该有提供商信息"
                assert record.model is not None, "记录应该有模型信息"
                assert record.operation is not None, "记录应该有操作类型"
                assert record.created_at is not None, "记录应该有创建时间"
                assert isinstance(record.success, bool), "记录应该有成功状态"
                assert isinstance(record.tokens_used, int), "记录应该有token使用量"
                assert isinstance(record.duration_ms, float), "记录应该有执行时长"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(num_operations=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100, deadline=None)
    def test_usage_statistics_accurate(self, num_operations):
        """
        属性测试: 使用统计应该准确反映实际使用情况
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行指定数量的操作
            for i in range(num_operations):
                messages = [LLMMessage(role=LLMRole.USER, content=f"测试提示 {i}")]
                await service.chat(messages, operation="test_operation")
            
            # 获取统计信息
            stats = service.get_usage_statistics()
            
            # 验证: 总请求数正确
            assert stats["total_requests"] == num_operations, \
                f"总请求数应该是 {num_operations}，实际是 {stats['total_requests']}"
            
            # 验证: 成功请求数 + 失败请求数 = 总请求数
            assert stats["successful_requests"] + stats["failed_requests"] == stats["total_requests"], \
                "成功请求数 + 失败请求数 应该等于 总请求数"
            
            # 验证: 操作统计存在
            assert "operations" in stats, "统计应该包含操作分类"
            assert "test_operation" in stats["operations"], \
                "统计应该包含执行的操作类型"
            assert stats["operations"]["test_operation"] == num_operations, \
                f"操作计数应该是 {num_operations}"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(
        success_count=st.integers(min_value=1, max_value=10),
        fail_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_success_and_failure_both_recorded(self, success_count, fail_count):
        """
        属性测试: 成功和失败的AI操作都应该被记录
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行成功的操作
            for i in range(success_count):
                messages = [LLMMessage(role=LLMRole.USER, content=f"成功测试 {i}")]
                await service.chat(messages, operation="success_op")
            
            # 模拟失败的操作 - 通过设置客户端不可用
            service.client.set_available(False)
            
            for i in range(fail_count):
                messages = [LLMMessage(role=LLMRole.USER, content=f"失败测试 {i}")]
                try:
                    await service.chat(messages, operation="fail_op")
                except ConnectionError:
                    pass  # 预期的错误
            
            # 获取统计
            stats = service.get_usage_statistics()
            
            # 验证: 成功操作被记录
            assert stats["successful_requests"] == success_count, \
                f"成功请求数应该是 {success_count}"
            
            # 验证: 失败操作被记录
            assert stats["failed_requests"] == fail_count, \
                f"失败请求数应该是 {fail_count}"
            
            # 验证: 总数正确
            assert stats["total_requests"] == success_count + fail_count, \
                "总请求数应该等于成功数 + 失败数"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(
        operations=st.lists(
            ai_operation_strategy,
            min_size=2,
            max_size=15
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_operation_type_tracking(self, operations):
        """
        属性测试: 不同类型的AI操作应该被分别追踪
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行不同类型的操作
            for operation in operations:
                messages = [LLMMessage(role=LLMRole.USER, content="测试")]
                await service.chat(messages, operation=operation)
            
            # 获取统计
            stats = service.get_usage_statistics()
            
            # 计算每种操作的预期次数
            expected_counts = {}
            for op in operations:
                expected_counts[op] = expected_counts.get(op, 0) + 1
            
            # 验证: 每种操作类型的计数正确
            for op, expected_count in expected_counts.items():
                actual_count = stats["operations"].get(op, 0)
                assert actual_count == expected_count, \
                    f"操作 '{op}' 的计数应该是 {expected_count}，实际是 {actual_count}"
        
        asyncio.get_event_loop().run_until_complete(run_test())
    
    @given(prompt=prompt_strategy)
    @settings(max_examples=100, deadline=None)
    def test_prompt_summary_recorded(self, prompt):
        """
        属性测试: AI使用记录应该包含提示摘要
        
        Feature: multi-agent-workflow-core, Property 35: AI使用记录完整性
        验证需求: Requirements 6.5
        """
        async def run_test():
            config = LLMConfig.mock()
            service = LLMService(config)
            await service.initialize()
            
            # 清空之前的记录
            service.clear_usage_records()
            
            # 执行操作
            messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
            await service.chat(messages, operation="test")
            
            # 获取记录
            records = service.get_usage_records()
            assert len(records) >= 1, "应该有记录"
            
            record = records[-1]
            
            # 验证: 提示摘要存在
            assert record.prompt_summary is not None, "应该记录提示摘要"
            
            # 验证: 提示摘要是原始提示的前缀（截断到100字符）
            expected_summary = prompt[:100]
            assert record.prompt_summary == expected_summary, \
                "提示摘要应该是原始提示的前100个字符"
        
        asyncio.get_event_loop().run_until_complete(run_test())


# =============================================================================
# 集成测试: Agent操作日志与AI使用记录的协同
# =============================================================================

class TestSystemLevelIntegration:
    """系统级集成测试"""
    
    @given(
        agent_ops=st.lists(operation_name_strategy, min_size=1, max_size=5),
        ai_ops=st.lists(ai_operation_strategy, min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_agent_and_ai_logs_independent(self, agent_ops, ai_ops):
        """
        属性测试: Agent操作日志和AI使用记录应该独立维护
        
        Feature: multi-agent-workflow-core
        验证需求: Requirements 1.4, 6.5
        """
        async def run_test():
            # 创建Agent
            message_bus = MessageBus()
            agent = TestableAgent("test-agent", message_bus)
            
            # 创建LLM服务
            config = LLMConfig.mock()
            llm_service = LLMService(config)
            await llm_service.initialize()
            llm_service.clear_usage_records()
            
            # 执行Agent操作
            for op in agent_ops:
                await agent.perform_custom_operation(op)
            
            # 执行AI操作
            for op in ai_ops:
                messages = [LLMMessage(role=LLMRole.USER, content="测试")]
                await llm_service.chat(messages, operation=op)
            
            # 获取日志和记录
            agent_logs = agent.get_operation_logs()
            ai_records = llm_service.get_usage_records()
            
            # 验证: Agent日志数量正确（包含创建日志）
            agent_op_logs = [l for l in agent_logs if l["operation"] in agent_ops]
            assert len(agent_op_logs) == len(agent_ops), \
                f"Agent操作日志数量应该是 {len(agent_ops)}"
            
            # 验证: AI记录数量正确
            assert len(ai_records) == len(ai_ops), \
                f"AI使用记录数量应该是 {len(ai_ops)}"
            
            # 验证: 两者独立（Agent日志不包含AI操作，反之亦然）
            agent_op_names = {l["operation"] for l in agent_logs}
            ai_op_names = {r.operation for r in ai_records}
            
            # Agent日志不应该包含AI操作类型
            for ai_op in ai_ops:
                if ai_op not in agent_ops:  # 排除名称碰巧相同的情况
                    assert ai_op not in agent_op_names or ai_op in agent_ops, \
                        "Agent日志不应该包含AI操作"
        
        asyncio.get_event_loop().run_until_complete(run_test())


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
