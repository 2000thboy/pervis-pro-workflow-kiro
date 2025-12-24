# -*- coding: utf-8 -*-
"""
性能测试模块

测试系统性能优化功能：
- 缓存性能
- 响应时间
- 资源使用

Feature: multi-agent-workflow-core
Requirements: 1.5, 7.2
"""
import asyncio
import pytest
import time
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st

from app.core.performance import (
    LRUCache,
    PerformanceMonitor,
    QueryOptimizer,
    ResourceMonitor,
    cached,
    timed,
    get_performance_monitor,
    get_agent_cache,
    get_project_cache
)


class TestLRUCache:
    """LRU缓存测试"""
    
    @pytest.mark.asyncio
    async def test_basic_get_set(self):
        """测试基本的获取和设置"""
        cache = LRUCache[str](max_size=10)
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LRUCache[str](max_size=10)
        
        result = await cache.get("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """测试LRU淘汰策略"""
        cache = LRUCache[str](max_size=3)
        
        # 添加3个条目
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # 访问key1使其成为最近使用
        await cache.get("key1")
        
        # 添加第4个条目，应该淘汰key2（最久未使用）
        await cache.set("key4", "value4")
        
        assert await cache.get("key1") == "value1"  # 仍然存在
        assert await cache.get("key2") is None      # 被淘汰
        assert await cache.get("key3") == "value3"  # 仍然存在
        assert await cache.get("key4") == "value4"  # 新添加
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """测试TTL过期"""
        cache = LRUCache[str](max_size=10, default_ttl=0.1)  # 100ms TTL
        
        await cache.set("key1", "value1")
        
        # 立即获取应该成功
        assert await cache.get("key1") == "value1"
        
        # 等待过期
        await asyncio.sleep(0.15)
        
        # 过期后应该返回None
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        cache = LRUCache[str](max_size=10)
        
        # 设置值
        await cache.set("key1", "value1")
        
        # 命中
        await cache.get("key1")
        await cache.get("key1")
        
        # 未命中
        await cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 2/3
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除"""
        cache = LRUCache[str](max_size=10)
        
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        result = await cache.delete("key1")
        assert result is True
        
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """测试清空"""
        cache = LRUCache[str](max_size=10)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert cache.size == 0
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @given(
        keys=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_cache_size_limit(self, keys):
        """属性测试: 缓存大小不超过最大限制"""
        async def run_test():
            max_size = 5
            cache = LRUCache[str](max_size=max_size)
            
            for key in keys:
                await cache.set(key, f"value_{key}")
            
            assert cache.size <= max_size
        
        asyncio.get_event_loop().run_until_complete(run_test())


class TestPerformanceMonitor:
    """性能监控器测试"""
    
    @pytest.mark.asyncio
    async def test_timer(self):
        """测试计时器"""
        monitor = PerformanceMonitor()
        
        timer_id = monitor.start_timer("test_operation")
        await asyncio.sleep(0.05)  # 50ms
        elapsed = await monitor.stop_timer(timer_id)
        
        assert elapsed >= 40  # 至少40ms（考虑误差）
        assert elapsed < 100  # 不超过100ms
    
    @pytest.mark.asyncio
    async def test_record_metric(self):
        """测试记录指标"""
        monitor = PerformanceMonitor()
        
        await monitor.record_metric(
            name="test_metric",
            value=42.5,
            unit="ms",
            tags={"operation": "test"}
        )
        
        metrics = monitor.get_metrics(name="test_metric")
        
        assert len(metrics) == 1
        assert metrics[0].name == "test_metric"
        assert metrics[0].value == 42.5
        assert metrics[0].unit == "ms"
    
    @pytest.mark.asyncio
    async def test_statistics(self):
        """测试统计计算"""
        monitor = PerformanceMonitor()
        
        # 记录多个指标
        for value in [10, 20, 30, 40, 50]:
            await monitor.record_metric("test_stat", value, "ms")
        
        stats = monitor.get_statistics("test_stat")
        
        assert stats["count"] == 5
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["avg"] == 30
    
    @pytest.mark.asyncio
    async def test_timed_decorator(self):
        """测试计时装饰器"""
        monitor = PerformanceMonitor()
        
        @timed(monitor, "decorated_function")
        async def slow_function():
            await asyncio.sleep(0.05)
            return "done"
        
        result = await slow_function()
        
        assert result == "done"
        
        metrics = monitor.get_metrics(name="decorated_function_duration")
        assert len(metrics) == 1
        assert metrics[0].value >= 40  # 至少40ms


class TestQueryOptimizer:
    """查询优化器测试"""
    
    @pytest.mark.asyncio
    async def test_record_query(self):
        """测试记录查询"""
        optimizer = QueryOptimizer()
        
        await optimizer.record_query("select_users", 50.0)
        await optimizer.record_query("select_users", 60.0)
        await optimizer.record_query("select_projects", 30.0)
        
        slow_queries = optimizer.get_slow_queries(threshold_ms=40)
        
        assert len(slow_queries) == 1
        assert slow_queries[0]["query"] == "select_users"
        assert slow_queries[0]["avg_duration_ms"] == 55.0
    
    def test_optimization_suggestions(self):
        """测试优化建议"""
        optimizer = QueryOptimizer()
        
        # 模拟慢查询
        for _ in range(10):
            asyncio.get_event_loop().run_until_complete(
                optimizer.record_query("slow_query", 200.0)
            )
        
        suggestions = optimizer.get_optimization_suggestions()
        
        assert len(suggestions) >= 1
        assert "slow_query" in suggestions[0]


class TestResourceMonitor:
    """资源监控器测试"""
    
    @pytest.mark.asyncio
    async def test_sample(self):
        """测试资源采样"""
        monitor = ResourceMonitor()
        
        sample = await monitor.sample()
        
        assert "timestamp" in sample
        assert "active_tasks" in sample
    
    @pytest.mark.asyncio
    async def test_summary(self):
        """测试资源摘要"""
        monitor = ResourceMonitor()
        
        # 采集多个样本
        for _ in range(5):
            await monitor.sample()
        
        summary = monitor.get_summary()
        
        assert summary["sample_count"] == 5
        assert "memory_mb" in summary
        assert "active_tasks" in summary


class TestCachedDecorator:
    """缓存装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_cached_function(self):
        """测试缓存装饰器"""
        cache = LRUCache[int](max_size=10)
        call_count = 0
        
        @cached(cache, key_func=lambda x: f"square_{x}")
        async def square(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * x
        
        # 第一次调用
        result1 = await square(5)
        assert result1 == 25
        assert call_count == 1
        
        # 第二次调用（应该从缓存获取）
        result2 = await square(5)
        assert result2 == 25
        assert call_count == 1  # 没有增加
        
        # 不同参数
        result3 = await square(6)
        assert result3 == 36
        assert call_count == 2


class TestPerformanceIntegration:
    """性能集成测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """测试并发缓存访问"""
        cache = LRUCache[str](max_size=100)
        
        async def worker(worker_id: int):
            for i in range(10):
                key = f"key_{worker_id}_{i}"
                await cache.set(key, f"value_{worker_id}_{i}")
                await cache.get(key)
        
        # 并发执行多个worker
        await asyncio.gather(*[worker(i) for i in range(10)])
        
        # 验证缓存状态
        stats = cache.get_stats()
        assert stats["size"] <= 100
        assert stats["hits"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """测试负载下的性能"""
        monitor = PerformanceMonitor()
        cache = LRUCache[str](max_size=1000)
        
        @timed(monitor, "cached_operation")
        @cached(cache, key_func=lambda x: f"op_{x}")
        async def operation(x: int) -> str:
            await asyncio.sleep(0.001)  # 模拟1ms操作
            return f"result_{x}"
        
        # 执行多次操作
        for i in range(100):
            await operation(i % 10)  # 重复使用10个不同的键
        
        # 检查性能
        stats = monitor.get_statistics("cached_operation_duration")
        cache_stats = cache.get_stats()
        
        # 由于缓存，平均时间应该较低
        assert stats["avg"] < 5  # 平均小于5ms
        assert cache_stats["hit_rate"] > 0.8  # 命中率超过80%


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])



# =============================================================================
# 任务 16.4: 系统并发处理能力和大数据量处理性能测试
# Feature: multi-agent-workflow-core
# Requirements: 1.5, 7.2
# =============================================================================

class TestConcurrencyPerformance:
    """
    并发处理能力测试
    
    验证系统在高并发场景下的性能表现
    Requirements: 1.5
    """
    
    @pytest.mark.asyncio
    async def test_concurrent_message_bus_operations(self):
        """测试消息总线并发操作"""
        from app.core.message_bus import MessageBus, Message, MessageType
        
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        received_messages = []
        
        async def handler(msg):
            received_messages.append(msg)
        
        # 创建多个订阅者
        for i in range(10):
            await bus.subscribe(f"agent_{i}", "test_topic", handler)
        
        # 并发发布消息
        async def publish_messages(count: int):
            for i in range(count):
                msg = Message(
                    type=MessageType.EVENT,
                    source="test",
                    content={"index": i}
                )
                await bus.publish("test_topic", msg)
        
        start_time = time.perf_counter()
        
        # 并发发布100条消息
        await asyncio.gather(*[publish_messages(10) for _ in range(10)])
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        await bus.stop()
        
        # 验证性能
        assert elapsed_ms < 5000, f"并发发布100条消息应该在5秒内完成，实际: {elapsed_ms}ms"
        
        # 验证消息都被接收（每条消息被10个订阅者接收）
        assert len(received_messages) == 1000, f"应该接收1000条消息，实际: {len(received_messages)}"
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self):
        """测试Agent并发操作"""
        from app.core.message_bus import MessageBus
        from app.core.agent_types import AgentType
        from tests.test_system_level_properties import TestableAgent
        
        bus = MessageBus()
        await bus.start()
        
        # 创建多个Agent
        agents = []
        for i in range(8):
            agent = TestableAgent(f"agent_{i}", bus)
            agents.append(agent)
        
        # 并发初始化
        start_time = time.perf_counter()
        init_results = await asyncio.gather(*[agent.initialize() for agent in agents])
        init_time = (time.perf_counter() - start_time) * 1000
        
        assert all(init_results), "所有Agent应该成功初始化"
        assert init_time < 2000, f"8个Agent并发初始化应该在2秒内完成，实际: {init_time}ms"
        
        # 并发启动
        start_time = time.perf_counter()
        start_results = await asyncio.gather(*[agent.start() for agent in agents])
        start_time_ms = (time.perf_counter() - start_time) * 1000
        
        assert all(start_results), "所有Agent应该成功启动"
        assert start_time_ms < 2000, f"8个Agent并发启动应该在2秒内完成，实际: {start_time_ms}ms"
        
        # 并发执行操作
        async def agent_work(agent, count):
            for i in range(count):
                await agent.perform_custom_operation(f"op_{i}")
        
        start_time = time.perf_counter()
        await asyncio.gather(*[agent_work(agent, 50) for agent in agents])
        work_time = (time.perf_counter() - start_time) * 1000
        
        assert work_time < 5000, f"8个Agent各执行50个操作应该在5秒内完成，实际: {work_time}ms"
        
        # 清理
        await asyncio.gather(*[agent.stop() for agent in agents])
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """测试缓存并发操作"""
        cache = LRUCache[str](max_size=1000)
        
        async def cache_worker(worker_id: int, operations: int):
            for i in range(operations):
                key = f"key_{worker_id}_{i}"
                await cache.set(key, f"value_{worker_id}_{i}")
                await cache.get(key)
                if i % 10 == 0:
                    await cache.get(f"key_{(worker_id + 1) % 10}_{i}")  # 跨worker访问
        
        start_time = time.perf_counter()
        
        # 10个worker并发执行，每个100次操作
        await asyncio.gather(*[cache_worker(i, 100) for i in range(10)])
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # 验证性能
        assert elapsed_ms < 3000, f"1000次并发缓存操作应该在3秒内完成，实际: {elapsed_ms}ms"
        
        # 验证缓存状态
        stats = cache.get_stats()
        assert stats["size"] <= 1000
        assert stats["hits"] > 0


class TestLargeDataPerformance:
    """
    大数据量处理性能测试
    
    验证系统处理大量数据时的性能表现
    Requirements: 7.2
    """
    
    @pytest.mark.asyncio
    async def test_large_message_history(self):
        """测试大量消息历史处理"""
        from app.core.message_bus import MessageBus, Message, MessageType
        
        bus = MessageBus(max_history=10000)
        await bus.start()
        
        async def handler(msg):
            pass
        
        await bus.subscribe("test_agent", "test_topic", handler)
        
        # 发布大量消息
        start_time = time.perf_counter()
        
        for i in range(5000):
            msg = Message(
                type=MessageType.EVENT,
                source="test",
                content={"index": i, "data": "x" * 100}  # 每条消息约100字节
            )
            await bus.publish("test_topic", msg)
        
        publish_time = (time.perf_counter() - start_time) * 1000
        
        # 验证发布性能
        assert publish_time < 10000, f"发布5000条消息应该在10秒内完成，实际: {publish_time}ms"
        
        # 测试历史查询性能
        start_time = time.perf_counter()
        history = bus.get_history(limit=1000)
        query_time = (time.perf_counter() - start_time) * 1000
        
        assert len(history) == 1000
        assert query_time < 100, f"查询1000条历史应该在100ms内完成，实际: {query_time}ms"
        
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_large_cache_operations(self):
        """测试大容量缓存操作"""
        cache = LRUCache[str](max_size=5000, default_ttl=60)
        
        # 填充缓存
        start_time = time.perf_counter()
        
        for i in range(5000):
            await cache.set(f"key_{i}", f"value_{i}" * 10)  # 每个值约60字节
        
        fill_time = (time.perf_counter() - start_time) * 1000
        
        assert fill_time < 5000, f"填充5000个缓存条目应该在5秒内完成，实际: {fill_time}ms"
        assert cache.size == 5000
        
        # 测试随机访问性能
        import random
        
        start_time = time.perf_counter()
        
        for _ in range(10000):
            key = f"key_{random.randint(0, 4999)}"
            await cache.get(key)
        
        access_time = (time.perf_counter() - start_time) * 1000
        
        assert access_time < 3000, f"10000次随机访问应该在3秒内完成，实际: {access_time}ms"
        
        # 验证命中率
        stats = cache.get_stats()
        assert stats["hit_rate"] > 0.9, f"命中率应该超过90%，实际: {stats['hit_rate']}"
    
    @pytest.mark.asyncio
    async def test_large_operation_logs(self):
        """测试大量操作日志处理"""
        from app.core.message_bus import MessageBus
        from tests.test_system_level_properties import TestableAgent
        
        bus = MessageBus()
        agent = TestableAgent("test_agent", bus)
        
        # 生成大量操作日志
        start_time = time.perf_counter()
        
        for i in range(1000):
            await agent.perform_custom_operation(
                f"operation_{i}",
                {"data": f"value_{i}", "index": i}
            )
        
        log_time = (time.perf_counter() - start_time) * 1000
        
        assert log_time < 3000, f"记录1000条操作日志应该在3秒内完成，实际: {log_time}ms"
        
        # 测试日志查询性能
        start_time = time.perf_counter()
        logs = agent.get_operation_logs(limit=500)
        query_time = (time.perf_counter() - start_time) * 1000
        
        assert len(logs) == 500
        assert query_time < 100, f"查询500条日志应该在100ms内完成，实际: {query_time}ms"
    
    @pytest.mark.asyncio
    async def test_large_ai_usage_records(self):
        """测试大量AI使用记录处理"""
        from app.core.llm_service import LLMService, LLMConfig, LLMMessage, LLMRole
        
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        service.clear_usage_records()
        
        # 生成大量AI使用记录
        start_time = time.perf_counter()
        
        for i in range(500):
            messages = [LLMMessage(role=LLMRole.USER, content=f"测试提示 {i}")]
            await service.chat(messages, operation=f"test_op_{i % 10}")
        
        record_time = (time.perf_counter() - start_time) * 1000
        
        assert record_time < 5000, f"记录500条AI使用记录应该在5秒内完成，实际: {record_time}ms"
        
        # 测试统计计算性能
        start_time = time.perf_counter()
        stats = service.get_usage_statistics()
        stats_time = (time.perf_counter() - start_time) * 1000
        
        assert stats["total_requests"] == 500
        assert stats_time < 100, f"计算统计应该在100ms内完成，实际: {stats_time}ms"
        
        # 验证操作类型统计
        assert len(stats["operations"]) == 10  # 10种不同的操作类型


class TestPerformanceMetrics:
    """
    性能指标收集测试
    
    验证性能监控系统的准确性
    """
    
    @pytest.mark.asyncio
    async def test_metrics_collection_overhead(self):
        """测试指标收集的开销"""
        monitor = PerformanceMonitor()
        
        # 测试无监控的基准时间
        start_time = time.perf_counter()
        for _ in range(1000):
            pass
        baseline_time = (time.perf_counter() - start_time) * 1000
        
        # 测试有监控的时间
        start_time = time.perf_counter()
        for i in range(1000):
            await monitor.record_metric(f"metric_{i}", i, "count")
        monitored_time = (time.perf_counter() - start_time) * 1000
        
        # 监控开销应该合理
        overhead = monitored_time - baseline_time
        assert overhead < 2000, f"1000次指标记录的开销应该小于2秒，实际: {overhead}ms"
    
    @pytest.mark.asyncio
    async def test_statistics_accuracy(self):
        """测试统计准确性"""
        monitor = PerformanceMonitor()
        
        # 记录已知值
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for v in values:
            await monitor.record_metric("test_metric", v, "ms")
        
        stats = monitor.get_statistics("test_metric")
        
        # 验证统计准确性
        assert stats["count"] == 10
        assert stats["min"] == 10
        assert stats["max"] == 100
        assert stats["avg"] == 55
        # p50 是第5个元素（索引5），值为60（因为索引从0开始，int(10*0.5)=5）
        assert stats["p50"] in [50, 60]  # 中位数（取决于实现）


class TestSystemPerformanceBenchmark:
    """
    系统性能基准测试
    
    综合测试系统整体性能
    """
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance(self):
        """端到端性能测试"""
        from app.core.message_bus import MessageBus, Message, MessageType
        from app.core.llm_service import LLMService, LLMConfig, LLMMessage, LLMRole
        from tests.test_system_level_properties import TestableAgent
        
        # 初始化组件
        bus = MessageBus(max_history=1000)
        await bus.start()
        
        llm_service = LLMService(LLMConfig.mock())
        await llm_service.initialize()
        
        cache = LRUCache[str](max_size=500)
        monitor = PerformanceMonitor()
        
        # 创建Agent
        agents = [TestableAgent(f"agent_{i}", bus) for i in range(4)]
        for agent in agents:
            await agent.initialize()
            await agent.start()
        
        # 模拟工作负载
        start_time = time.perf_counter()
        
        async def workload():
            # Agent操作
            for agent in agents:
                await agent.perform_custom_operation("test_op")
            
            # 消息发布
            msg = Message(type=MessageType.EVENT, source="test", content={"test": True})
            await bus.publish("test_topic", msg)
            
            # LLM调用
            messages = [LLMMessage(role=LLMRole.USER, content="测试")]
            await llm_service.chat(messages, operation="test")
            
            # 缓存操作
            await cache.set("test_key", "test_value")
            await cache.get("test_key")
        
        # 执行100次工作负载
        for _ in range(100):
            await workload()
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # 清理
        for agent in agents:
            await agent.stop()
        await bus.stop()
        
        # 验证整体性能
        assert total_time < 15000, f"100次完整工作负载应该在15秒内完成，实际: {total_time}ms"
        
        # 输出性能报告
        print(f"\n=== 性能基准测试报告 ===")
        print(f"总执行时间: {total_time:.2f}ms")
        print(f"平均每次工作负载: {total_time/100:.2f}ms")
        print(f"缓存命中率: {cache.get_stats()['hit_rate']:.2%}")
        print(f"AI调用次数: {llm_service.get_usage_statistics()['total_requests']}")
