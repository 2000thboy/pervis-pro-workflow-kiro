"""
系统监控单元测试

验证需求: Requirements 1.4, 5.1
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st, HealthCheck as HypothesisHealthCheck

from app.core.monitoring import (
    SystemMonitor,
    HealthStatus,
    ComponentType,
    HealthCheckResult,
    SystemMetrics,
    OperationLog,
    get_system_monitor,
    set_system_monitor
)


# ============== Fixtures ==============

@pytest.fixture
def monitor():
    """创建系统监控器实例"""
    m = SystemMonitor(log_dir="./data/test_logs/monitoring")
    yield m
    m.clear_history()


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============== 健康检查测试 ==============

class TestHealthCheck:
    """健康检查测试"""
    
    def test_register_health_check(self, monitor):
        """测试注册健康检查"""
        def check_func():
            return True
        
        monitor.register_health_check(
            "test_component",
            ComponentType.AGENT,
            check_func
        )
        
        assert "test_component" in monitor._health_checks
    
    @pytest.mark.asyncio
    async def test_check_component_health_success(self, monitor):
        """测试健康检查成功"""
        def check_func():
            return True
        
        monitor.register_health_check(
            "healthy_component",
            ComponentType.AGENT,
            check_func
        )
        
        result = await monitor.check_component_health("healthy_component")
        
        assert result is not None
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"
    
    @pytest.mark.asyncio
    async def test_check_component_health_failure(self, monitor):
        """测试健康检查失败"""
        def check_func():
            return False
        
        monitor.register_health_check(
            "unhealthy_component",
            ComponentType.DATABASE,
            check_func
        )
        
        result = await monitor.check_component_health("unhealthy_component")
        
        assert result is not None
        assert result.status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_check_component_health_exception(self, monitor):
        """测试健康检查异常"""
        def check_func():
            raise Exception("Connection failed")
        
        monitor.register_health_check(
            "error_component",
            ComponentType.REDIS,
            check_func
        )
        
        result = await monitor.check_component_health("error_component")
        
        assert result is not None
        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in result.message
    
    @pytest.mark.asyncio
    async def test_check_all_health(self, monitor):
        """测试检查所有组件健康状态"""
        monitor.register_health_check("comp1", ComponentType.AGENT, lambda: True)
        monitor.register_health_check("comp2", ComponentType.DATABASE, lambda: True)
        monitor.register_health_check("comp3", ComponentType.API_SERVER, lambda: False)
        
        results = await monitor.check_all_health()
        
        assert len(results) == 3
        assert results["comp1"].status == HealthStatus.HEALTHY
        assert results["comp2"].status == HealthStatus.HEALTHY
        assert results["comp3"].status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_overall_health_healthy(self, monitor):
        """测试整体健康状态 - 健康"""
        monitor.register_health_check("comp1", ComponentType.AGENT, lambda: True)
        monitor.register_health_check("comp2", ComponentType.DATABASE, lambda: True)
        
        await monitor.check_all_health()
        
        assert monitor.get_overall_health() == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_get_overall_health_unhealthy(self, monitor):
        """测试整体健康状态 - 不健康"""
        monitor.register_health_check("comp1", ComponentType.AGENT, lambda: True)
        monitor.register_health_check("comp2", ComponentType.DATABASE, lambda: False)
        
        await monitor.check_all_health()
        
        assert monitor.get_overall_health() == HealthStatus.UNHEALTHY
    
    def test_get_overall_health_unknown(self, monitor):
        """测试整体健康状态 - 未知"""
        assert monitor.get_overall_health() == HealthStatus.UNKNOWN


# ============== 系统指标测试 ==============

class TestSystemMetrics:
    """系统指标测试"""
    
    def test_collect_system_metrics(self, monitor):
        """测试收集系统指标"""
        metrics = monitor.collect_system_metrics()
        
        assert metrics is not None
        assert isinstance(metrics.cpu_percent, float)
        assert isinstance(metrics.memory_percent, float)
        assert isinstance(metrics.disk_percent, float)
        assert metrics.timestamp is not None
    
    def test_metrics_history(self, monitor):
        """测试指标历史记录"""
        # 收集多次指标
        for _ in range(5):
            monitor.collect_system_metrics()
        
        history = monitor.get_metrics_history()
        assert len(history) == 5
    
    def test_metrics_history_limit(self, monitor):
        """测试指标历史限制"""
        for _ in range(10):
            monitor.collect_system_metrics()
        
        history = monitor.get_metrics_history(limit=5)
        assert len(history) == 5
    
    def test_get_average_metrics(self, monitor):
        """测试获取平均指标"""
        for _ in range(5):
            monitor.collect_system_metrics()
        
        avg = monitor.get_average_metrics()
        
        assert avg is not None
        assert "avg_cpu_percent" in avg
        assert "avg_memory_percent" in avg
        assert "sample_count" in avg
        assert avg["sample_count"] == 5


# ============== 操作日志测试 ==============

class TestOperationLog:
    """
    操作日志测试
    
    验证需求: Requirements 1.4
    """
    
    def test_log_operation_success(self, monitor):
        """测试记录成功操作"""
        log = monitor.log_operation(
            operation="create_project",
            status="success",
            duration_ms=150.5,
            agent_id="pm_agent",
            details={"project_id": "proj_001"}
        )
        
        assert log.log_id.startswith("LOG-")
        assert log.operation == "create_project"
        assert log.status == "success"
        assert log.agent_id == "pm_agent"
        assert log.duration_ms == 150.5
    
    def test_log_operation_error(self, monitor):
        """测试记录错误操作"""
        log = monitor.log_operation(
            operation="process_asset",
            status="error",
            duration_ms=50.0,
            agent_id="dam_agent",
            error_message="File not found"
        )
        
        assert log.status == "error"
        assert log.error_message == "File not found"
    
    def test_get_operation_logs(self, monitor):
        """测试查询操作日志"""
        monitor.log_operation("op1", "success", 100.0, agent_id="agent1")
        monitor.log_operation("op2", "error", 50.0, agent_id="agent2")
        monitor.log_operation("op3", "success", 75.0, agent_id="agent1")
        
        # 查询所有日志
        all_logs = monitor.get_operation_logs()
        assert len(all_logs) == 3
        
        # 按Agent过滤
        agent1_logs = monitor.get_operation_logs(agent_id="agent1")
        assert len(agent1_logs) == 2
        
        # 按状态过滤
        error_logs = monitor.get_operation_logs(status="error")
        assert len(error_logs) == 1
    
    def test_get_operation_statistics(self, monitor):
        """测试获取操作统计"""
        monitor.log_operation("op1", "success", 100.0, agent_id="agent1")
        monitor.log_operation("op2", "success", 150.0, agent_id="agent1")
        monitor.log_operation("op3", "error", 50.0, agent_id="agent2")
        
        stats = monitor.get_operation_statistics()
        
        assert stats["total_operations"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1
        assert stats["success_rate"] == 2/3
        assert "by_agent" in stats
        assert "by_operation" in stats
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        operations=st.lists(
            st.tuples(
                st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=20),
                st.sampled_from(["success", "error", "pending"]),
                st.floats(min_value=0.1, max_value=1000.0)
            ),
            min_size=1,
            max_size=20
        )
    )
    def test_operation_log_completeness_property(self, monitor, operations):
        """
        属性测试: Agent操作日志完整性
        
        Feature: multi-agent-workflow-core, Property 4: Agent操作日志完整性
        验证需求: Requirements 1.4
        
        对于任何Agent执行的任务，系统都应该记录完整的状态变化和操作日志
        """
        monitor.clear_history()
        
        # 记录所有操作
        for op_name, status, duration in operations:
            monitor.log_operation(
                operation=op_name,
                status=status,
                duration_ms=duration,
                agent_id="test_agent"
            )
        
        # 验证日志完整性
        logs = monitor.get_operation_logs()
        assert len(logs) == len(operations)
        
        # 每个日志都应该有完整信息
        for log in logs:
            assert log.log_id is not None
            assert log.timestamp is not None
            assert log.operation is not None
            assert log.status is not None
            assert log.duration_ms >= 0


# ============== 报告生成测试 ==============

class TestReportGeneration:
    """报告生成测试"""
    
    @pytest.mark.asyncio
    async def test_generate_health_report(self, monitor):
        """测试生成健康报告"""
        # 注册一些组件
        monitor.register_health_check("agent1", ComponentType.AGENT, lambda: True)
        monitor.register_health_check("db", ComponentType.DATABASE, lambda: True)
        
        # 执行健康检查
        await monitor.check_all_health()
        
        # 记录一些操作
        monitor.log_operation("test_op", "success", 100.0)
        
        # 生成报告
        report = monitor.generate_health_report()
        
        assert "timestamp" in report
        assert "overall_health" in report
        assert "components" in report
        assert "current_metrics" in report
        assert "operation_statistics_1h" in report


# ============== 全局实例测试 ==============

class TestGlobalInstance:
    """全局实例测试"""
    
    def test_get_system_monitor(self):
        """测试获取全局监控器"""
        monitor = get_system_monitor()
        assert monitor is not None
        assert isinstance(monitor, SystemMonitor)
    
    def test_set_system_monitor(self):
        """测试设置全局监控器"""
        custom_monitor = SystemMonitor()
        set_system_monitor(custom_monitor)
        
        monitor = get_system_monitor()
        assert monitor is custom_monitor


# ============== 监控任务测试 ==============

class TestMonitoringTask:
    """监控任务测试"""
    
    def test_is_running_initial(self, monitor):
        """测试初始运行状态"""
        assert monitor.is_running() is False
    
    def test_stop_monitoring(self, monitor):
        """测试停止监控"""
        monitor._is_running = True
        monitor.stop_monitoring()
        assert monitor.is_running() is False
    
    def test_clear_history(self, monitor):
        """测试清除历史"""
        monitor.log_operation("test", "success", 100.0)
        monitor.collect_system_metrics()
        
        monitor.clear_history()
        
        assert len(monitor._operation_logs) == 0
        assert len(monitor._metrics_history) == 0
