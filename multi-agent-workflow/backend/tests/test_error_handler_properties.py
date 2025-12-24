"""
错误处理框架属性测试

验证需求: Requirements 5.1, 5.2, 5.5
属性 27: API监控有效性
属性 30: 路径验证记录完整性
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st, HealthCheck as HypothesisHealthCheck

from app.core.error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorRecord,
    ErrorCategory,
    ErrorSeverity,
    RecoveryAction,
    PathValidationResult,
    APIMonitoringResult,
    get_error_handler,
    set_error_handler
)


# ============== Fixtures ==============

@pytest.fixture
def error_handler():
    """创建错误处理器实例"""
    handler = ErrorHandler(log_dir="./data/test_logs/errors")
    yield handler
    handler.clear_errors()


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============== 基础功能测试 ==============

class TestErrorHandlerBasics:
    """错误处理器基础功能测试"""
    
    def test_handler_initialization(self, error_handler):
        """测试处理器初始化"""
        assert error_handler is not None
        assert error_handler._error_records == {}
        assert len(error_handler._recovery_strategies) > 0
    
    def test_generate_error_id(self, error_handler):
        """测试错误ID生成"""
        id1 = error_handler._generate_error_id()
        id2 = error_handler._generate_error_id()
        
        assert id1.startswith("ERR-")
        assert id2.startswith("ERR-")
        assert id1 != id2
    
    def test_default_recovery_strategies(self, error_handler):
        """测试默认恢复策略"""
        assert error_handler.get_recovery_strategy(ErrorCategory.AGENT_ERROR) == RecoveryAction.RESTART_AGENT
        assert error_handler.get_recovery_strategy(ErrorCategory.COMMUNICATION_ERROR) == RecoveryAction.RETRY
        assert error_handler.get_recovery_strategy(ErrorCategory.WORKFLOW_ERROR) == RecoveryAction.NOTIFY_USER
    
    def test_set_recovery_strategy(self, error_handler):
        """测试设置恢复策略"""
        error_handler.set_recovery_strategy(ErrorCategory.AGENT_ERROR, RecoveryAction.ABORT)
        assert error_handler.get_recovery_strategy(ErrorCategory.AGENT_ERROR) == RecoveryAction.ABORT
    
    def test_register_handler(self, error_handler):
        """测试注册错误处理器"""
        handler_called = []
        
        def custom_handler(context):
            handler_called.append(context.error_id)
        
        error_handler.register_handler(ErrorCategory.AGENT_ERROR, custom_handler)
        assert ErrorCategory.AGENT_ERROR in error_handler._error_handlers
        assert custom_handler in error_handler._error_handlers[ErrorCategory.AGENT_ERROR]


# ============== 错误处理测试 ==============

class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_handle_error(self, error_handler):
        """测试基本错误处理"""
        error = ValueError("Test error")
        
        context = await error_handler.handle_error(
            error=error,
            category=ErrorCategory.DATA_ERROR,
            source="test_source",
            severity=ErrorSeverity.ERROR
        )
        
        assert context.error_id.startswith("ERR-")
        assert context.category == ErrorCategory.DATA_ERROR
        assert context.severity == ErrorSeverity.ERROR
        assert context.source == "test_source"
        assert context.exception_type == "ValueError"
        assert "Test error" in context.message
    
    @pytest.mark.asyncio
    async def test_handle_agent_error(self, error_handler):
        """
        测试Agent错误处理
        
        验证需求: Requirements 5.1
        """
        error = RuntimeError("Agent crashed")
        
        context = await error_handler.handle_agent_error(
            agent_id="director_agent",
            error=error,
            task_id="task_001"
        )
        
        assert context.category == ErrorCategory.AGENT_ERROR
        assert context.source == "director_agent"
        assert context.metadata["agent_id"] == "director_agent"
        assert context.metadata["task_id"] == "task_001"
        assert context.recovery_action == RecoveryAction.RESTART_AGENT
    
    @pytest.mark.asyncio
    async def test_handle_communication_error(self, error_handler):
        """测试通信错误处理"""
        error = ConnectionError("Connection refused")
        
        context = await error_handler.handle_communication_error(
            source="agent_a",
            target="agent_b",
            error=error
        )
        
        assert context.category == ErrorCategory.COMMUNICATION_ERROR
        assert "agent_a" in context.source
        assert "agent_b" in context.source
        assert context.recovery_action == RecoveryAction.RETRY
    
    @pytest.mark.asyncio
    async def test_handle_workflow_error(self, error_handler):
        """测试工作流错误处理"""
        error = Exception("Workflow step failed")
        
        context = await error_handler.handle_workflow_error(
            workflow_id="wf_001",
            step_id="step_3",
            error=error
        )
        
        assert context.category == ErrorCategory.WORKFLOW_ERROR
        assert context.source == "wf_001"
        assert context.metadata["step_id"] == "step_3"
        assert context.recovery_action == RecoveryAction.NOTIFY_USER
    
    @pytest.mark.asyncio
    async def test_handle_api_error(self, error_handler):
        """
        测试API错误处理
        
        验证需求: Requirements 5.2
        """
        error = Exception("Internal server error")
        
        context = await error_handler.handle_api_error(
            endpoint="/api/projects",
            method="POST",
            error=error,
            status_code=500
        )
        
        assert context.category == ErrorCategory.API_ERROR
        assert "POST" in context.source
        assert "/api/projects" in context.source
        assert context.metadata["status_code"] == 500


# ============== API监控测试 ==============

class TestAPIMonitoring:
    """
    API监控测试
    
    属性 27: API监控有效性
    验证需求: Requirements 5.2
    """
    
    def test_record_api_call_success(self, error_handler):
        """测试记录成功的API调用"""
        result = error_handler.record_api_call(
            endpoint="/api/projects",
            method="GET",
            status_code=200,
            response_time_ms=50.5
        )
        
        assert result.is_success is True
        assert result.status_code == 200
        assert result.response_time_ms == 50.5
        assert result.error_message is None
    
    def test_record_api_call_failure(self, error_handler):
        """测试记录失败的API调用"""
        result = error_handler.record_api_call(
            endpoint="/api/projects",
            method="POST",
            status_code=500,
            response_time_ms=100.0,
            error_message="Internal server error"
        )
        
        assert result.is_success is False
        assert result.status_code == 500
        assert result.error_message == "Internal server error"
    
    def test_get_api_monitoring_results(self, error_handler):
        """测试获取API监控结果"""
        # 记录多个API调用
        error_handler.record_api_call("/api/projects", "GET", 200, 50.0)
        error_handler.record_api_call("/api/projects", "POST", 201, 100.0)
        error_handler.record_api_call("/api/agents", "GET", 200, 30.0)
        
        # 获取所有结果
        all_results = error_handler.get_api_monitoring_results()
        assert len(all_results) == 3
        
        # 按端点过滤
        project_results = error_handler.get_api_monitoring_results(endpoint="/api/projects")
        assert len(project_results) == 2
    
    def test_get_api_error_rate(self, error_handler):
        """测试计算API错误率"""
        # 记录混合的API调用
        error_handler.record_api_call("/api/test", "GET", 200, 50.0)
        error_handler.record_api_call("/api/test", "GET", 200, 50.0)
        error_handler.record_api_call("/api/test", "GET", 500, 50.0)
        error_handler.record_api_call("/api/test", "GET", 404, 50.0)
        
        error_rate = error_handler.get_api_error_rate()
        assert error_rate == 0.5  # 2 errors out of 4 calls
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        status_codes=st.lists(
            st.integers(min_value=100, max_value=599),
            min_size=1,
            max_size=20
        )
    )
    def test_api_monitoring_property(self, error_handler, status_codes):
        """
        属性测试: API监控有效性
        
        Feature: multi-agent-workflow-core, Property 27: API监控有效性
        验证需求: Requirements 5.2
        
        对于任何API调用记录，错误率计算应该准确反映失败调用的比例
        """
        error_handler.clear_errors()
        
        # 记录所有API调用
        for i, code in enumerate(status_codes):
            error_handler.record_api_call(
                endpoint=f"/api/test/{i}",
                method="GET",
                status_code=code,
                response_time_ms=50.0
            )
        
        # 计算预期错误率 (4xx 和 5xx 视为错误)
        error_count = sum(1 for code in status_codes if code >= 400)
        expected_rate = error_count / len(status_codes)
        
        # 验证错误率
        actual_rate = error_handler.get_api_error_rate()
        assert abs(actual_rate - expected_rate) < 0.001


# ============== 路径验证测试 ==============

class TestPathValidation:
    """
    路径验证测试
    
    属性 30: 路径验证记录完整性
    验证需求: Requirements 5.5
    """
    
    def test_validate_existing_path(self, error_handler, tmp_path):
        """测试验证存在的路径"""
        # 创建临时文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = error_handler.validate_path(str(test_file))
        
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_validate_nonexistent_path(self, error_handler):
        """测试验证不存在的路径"""
        result = error_handler.validate_path("/nonexistent/path/file.txt")
        
        assert result.is_valid is False
        assert "does not exist" in result.error_message
        assert result.suggested_fix is not None
    
    def test_validate_path_extension(self, error_handler, tmp_path):
        """测试验证文件扩展名"""
        # 创建临时文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = error_handler.validate_path(
            str(test_file),
            allowed_extensions=[".mp4", ".mov"]
        )
        
        assert result.is_valid is False
        assert "Invalid file extension" in result.error_message
    
    def test_validate_path_invalid_chars(self, error_handler):
        """测试验证包含非法字符的路径"""
        result = error_handler.validate_path(
            "/path/to/file<test>.txt",
            must_exist=False
        )
        
        assert result.is_valid is False
        assert "invalid character" in result.error_message.lower()
    
    def test_get_path_validation_results(self, error_handler, tmp_path):
        """测试获取路径验证结果"""
        # 创建有效路径
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("content")
        
        # 验证多个路径
        error_handler.validate_path(str(valid_file))
        error_handler.validate_path("/invalid/path.txt")
        
        # 获取所有结果
        all_results = error_handler.get_path_validation_results()
        assert len(all_results) == 2
        
        # 获取无效结果
        invalid_results = error_handler.get_path_validation_results(invalid_only=True)
        assert len(invalid_results) == 1
    
    @pytest.mark.asyncio
    async def test_handle_path_error(self, error_handler):
        """
        测试路径错误处理
        
        验证需求: Requirements 5.5
        """
        error = FileNotFoundError("File not found")
        
        context = await error_handler.handle_path_error(
            path="/missing/file.txt",
            error=error,
            suggested_fix="Create the file or check the path"
        )
        
        assert context.category == ErrorCategory.PATH_ERROR
        assert context.metadata["path"] == "/missing/file.txt"
        assert context.metadata["suggested_fix"] is not None
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        paths=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789/_-.', min_size=1, max_size=50),
            min_size=1,
            max_size=10
        )
    )
    def test_path_validation_property(self, error_handler, paths):
        """
        属性测试: 路径验证记录完整性
        
        Feature: multi-agent-workflow-core, Property 30: 路径验证记录完整性
        验证需求: Requirements 5.5
        
        对于任何路径验证操作，系统应该记录完整的验证结果
        """
        error_handler.clear_errors()
        
        # 验证所有路径
        for path in paths:
            error_handler.validate_path(f"/test/{path}", must_exist=False)
        
        # 验证记录完整性
        results = error_handler.get_path_validation_results()
        assert len(results) == len(paths)
        
        # 每个结果都应该有路径信息
        for result in results:
            assert result.path is not None
            assert isinstance(result.is_valid, bool)


# ============== 错误查询测试 ==============

class TestErrorQuery:
    """错误查询测试"""
    
    @pytest.mark.asyncio
    async def test_get_error(self, error_handler):
        """测试获取单个错误"""
        error = ValueError("Test error")
        context = await error_handler.handle_error(
            error=error,
            category=ErrorCategory.DATA_ERROR,
            source="test"
        )
        
        record = error_handler.get_error(context.error_id)
        assert record is not None
        assert record.context.error_id == context.error_id
    
    @pytest.mark.asyncio
    async def test_get_errors_by_category(self, error_handler):
        """测试按分类查询错误"""
        await error_handler.handle_error(
            ValueError("Error 1"),
            ErrorCategory.DATA_ERROR,
            "source1"
        )
        await error_handler.handle_error(
            RuntimeError("Error 2"),
            ErrorCategory.AGENT_ERROR,
            "source2"
        )
        
        data_errors = error_handler.get_errors(category=ErrorCategory.DATA_ERROR)
        assert len(data_errors) == 1
        assert data_errors[0].context.category == ErrorCategory.DATA_ERROR
    
    @pytest.mark.asyncio
    async def test_resolve_error(self, error_handler):
        """测试解决错误"""
        error = ValueError("Test error")
        context = await error_handler.handle_error(
            error=error,
            category=ErrorCategory.DATA_ERROR,
            source="test"
        )
        
        # 解决错误
        result = error_handler.resolve_error(context.error_id, "Fixed manually")
        assert result is True
        
        # 验证状态
        record = error_handler.get_error(context.error_id)
        assert record.context.resolved is True
        assert record.context.resolved_at is not None
        assert record.context.metadata["resolution_note"] == "Fixed manually"
    
    @pytest.mark.asyncio
    async def test_get_error_statistics(self, error_handler):
        """测试获取错误统计"""
        await error_handler.handle_error(
            ValueError("Error 1"),
            ErrorCategory.DATA_ERROR,
            "source1",
            ErrorSeverity.ERROR
        )
        await error_handler.handle_error(
            RuntimeError("Error 2"),
            ErrorCategory.AGENT_ERROR,
            "source2",
            ErrorSeverity.CRITICAL
        )
        
        stats = error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 2
        assert stats["unresolved"] == 2
        assert "data_error" in stats["by_category"]
        assert "agent_error" in stats["by_category"]
    
    def test_clear_errors(self, error_handler):
        """测试清除错误"""
        error_handler.record_api_call("/api/test", "GET", 200, 50.0)
        error_handler.validate_path("/test/path", must_exist=False)
        
        count = error_handler.clear_errors()
        
        assert error_handler.get_api_monitoring_results() == []
        assert error_handler.get_path_validation_results() == []


# ============== 全局实例测试 ==============

class TestGlobalInstance:
    """全局实例测试"""
    
    def test_get_error_handler(self):
        """测试获取全局错误处理器"""
        handler = get_error_handler()
        assert handler is not None
        assert isinstance(handler, ErrorHandler)
    
    def test_set_error_handler(self):
        """测试设置全局错误处理器"""
        custom_handler = ErrorHandler()
        set_error_handler(custom_handler)
        
        handler = get_error_handler()
        assert handler is custom_handler
