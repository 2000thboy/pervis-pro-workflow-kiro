# -*- coding: utf-8 -*-
"""
BackendAgent Property Tests

Feature: multi-agent-workflow-core
Property 26: Exception detection timeliness
Requirements: 5.1
"""
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck as HypothesisHealthCheck

from app.agents.backend_agent import (
    BackendAgent,
    ErrorRecord,
    APIEndpoint,
    HealthCheck,
    SystemMetrics,
    ErrorSeverity,
    ErrorCategory,
    HealthStatus,
    MonitoringTarget,
)
from app.core.message_bus import MessageBus


class TestBackendAgentInit:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(
            agent_id="test_backend_agent",
            message_bus=message_bus
        )
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_agent_creation(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        assert agent.agent_id == "test_agent"
        assert "error_detection" in agent.capabilities
        assert "api_monitoring" in agent.capabilities
    
    @pytest.mark.asyncio
    async def test_agent_running(self, backend_agent):
        assert backend_agent.is_running
        assert backend_agent.work_state.value == "idle"


class TestErrorRecording:
    """Property 26: Exception detection timeliness"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_record_error(self, backend_agent):
        error = await backend_agent.record_error(
            error_id="err_1",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT_ERROR,
            source="test_agent",
            message="Test error message"
        )
        assert error.id == "err_1"
        assert error.severity == ErrorSeverity.ERROR
        assert error.resolved == False
    
    @pytest.mark.asyncio
    async def test_record_agent_error(self, backend_agent):
        error = await backend_agent.record_agent_error(
            agent_id="some_agent",
            error_message="Agent failed",
            error_type="runtime_error"
        )
        assert error.category == ErrorCategory.AGENT_ERROR
        assert "some_agent" in error.source
    
    @pytest.mark.asyncio
    async def test_record_api_error(self, backend_agent):
        error = await backend_agent.record_api_error(
            endpoint="/api/test",
            method="GET",
            status_code=500,
            error_message="Internal server error"
        )
        assert error.category == ErrorCategory.API_ERROR
        assert error.severity == ErrorSeverity.ERROR
    
    @pytest.mark.asyncio
    async def test_list_errors(self, backend_agent):
        await backend_agent.record_error(
            error_id="e1", severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT_ERROR, source="a", message="m1"
        )
        await backend_agent.record_error(
            error_id="e2", severity=ErrorSeverity.WARNING,
            category=ErrorCategory.API_ERROR, source="b", message="m2"
        )
        
        errors = await backend_agent.list_errors()
        assert len(errors) == 2
    
    @pytest.mark.asyncio
    async def test_resolve_error(self, backend_agent):
        await backend_agent.record_error(
            error_id="e1", severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT_ERROR, source="a", message="m"
        )
        
        result = await backend_agent.resolve_error("e1", "Fixed")
        assert result == True
        
        error = await backend_agent.get_error("e1")
        assert error.resolved == True
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        error_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=20),
        message=st.text(min_size=1, max_size=100)
    )
    async def test_error_recording_property(self, backend_agent, error_id, message):
        """Property 26: For any error, BackendAgent shall detect and record it"""
        error = await backend_agent.record_error(
            error_id=error_id,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.UNKNOWN_ERROR,
            source="test",
            message=message
        )
        
        # Property: recorded error should be retrievable
        retrieved = await backend_agent.get_error(error_id)
        assert retrieved is not None
        assert retrieved.message == message


class TestAPIMonitoring:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_register_endpoint(self, backend_agent):
        endpoint = await backend_agent.register_endpoint(
            endpoint_id="ep_1",
            path="/api/test",
            method="GET",
            description="Test endpoint"
        )
        assert endpoint.id == "ep_1"
        assert endpoint.path == "/api/test"
    
    @pytest.mark.asyncio
    async def test_record_api_call(self, backend_agent):
        await backend_agent.register_endpoint(
            endpoint_id="ep_1", path="/api/test", method="GET"
        )
        
        result = await backend_agent.record_api_call(
            endpoint_id="ep_1",
            status_code=200,
            response_time_ms=50.0,
            success=True
        )
        assert result == True
        
        endpoint = await backend_agent.get_endpoint("ep_1")
        assert endpoint.success_count == 1
    
    @pytest.mark.asyncio
    async def test_endpoint_statistics(self, backend_agent):
        await backend_agent.register_endpoint(
            endpoint_id="ep_1", path="/api/test", method="GET"
        )
        await backend_agent.record_api_call("ep_1", 200, 50.0, True)
        await backend_agent.record_api_call("ep_1", 500, 100.0, False)
        
        stats = await backend_agent.get_endpoint_statistics("ep_1")
        assert stats["total_calls"] == 2
        assert stats["success_count"] == 1
        assert stats["error_count"] == 1


class TestHealthCheck:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_perform_health_check(self, backend_agent):
        check = await backend_agent.perform_health_check(
            target="test_service",
            target_type=MonitoringTarget.AGENT
        )
        assert check.target == "test_service"
        assert check.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_custom_health_check(self, backend_agent):
        async def custom_check():
            return {"healthy": True, "message": "OK"}
        
        check = await backend_agent.perform_health_check(
            target="custom",
            target_type=MonitoringTarget.EXTERNAL_SERVICE,
            check_function=custom_check
        )
        assert check.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_system_health(self, backend_agent):
        await backend_agent.perform_health_check(
            target="service1", target_type=MonitoringTarget.AGENT
        )
        await backend_agent.perform_health_check(
            target="service2", target_type=MonitoringTarget.DATABASE
        )
        
        health = await backend_agent.get_system_health()
        assert health["total_checks"] == 2
        assert "overall_status" in health


class TestSystemMetrics:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, backend_agent):
        metrics = await backend_agent.collect_metrics(
            active_agents=5,
            memory_usage_mb=512.0,
            cpu_usage_percent=25.0
        )
        assert metrics.active_agents == 5
        assert metrics.memory_usage_mb == 512.0
    
    @pytest.mark.asyncio
    async def test_metrics_history(self, backend_agent):
        await backend_agent.collect_metrics(active_agents=1)
        await backend_agent.collect_metrics(active_agents=2)
        await backend_agent.collect_metrics(active_agents=3)
        
        history = await backend_agent.get_metrics_history(limit=10)
        assert len(history) == 3


class TestStatistics:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def backend_agent(self, message_bus):
        agent = BackendAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, backend_agent):
        await backend_agent.record_error(
            error_id="e1", severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT_ERROR, source="a", message="m"
        )
        await backend_agent.register_endpoint(
            endpoint_id="ep_1", path="/api/test", method="GET"
        )
        
        stats = backend_agent.get_statistics()
        assert stats["total_errors"] == 1
        assert stats["total_endpoints"] == 1
