# -*- coding: utf-8 -*-
"""
WorkflowEngine Property Tests

Feature: multi-agent-workflow-core
Property 6: 立项工作流触发一致性
Requirements: 2.1
"""
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck as HypothesisHealthCheck

from app.workflows.workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowStatus,
    StepStatus,
    StepType,
)


class TestWorkflowEngineBasics:
    """工作流引擎基础测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        engine = WorkflowEngine()
        assert not engine.is_running
        await engine.start()
        assert engine.is_running
        await engine.stop()
        assert not engine.is_running
    
    @pytest.mark.asyncio
    async def test_register_workflow(self, engine):
        workflow = WorkflowDefinition(
            id="test_workflow",
            name="Test Workflow",
            description="A test workflow"
        )
        engine.register_workflow(workflow)
        
        retrieved = engine.get_workflow("test_workflow")
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, engine):
        workflow1 = WorkflowDefinition(id="wf1", name="Workflow 1")
        workflow2 = WorkflowDefinition(id="wf2", name="Workflow 2")
        
        engine.register_workflow(workflow1)
        engine.register_workflow(workflow2)
        
        workflows = engine.list_workflows()
        assert len(workflows) == 2
    
    @pytest.mark.asyncio
    async def test_unregister_workflow(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Workflow 1")
        engine.register_workflow(workflow)
        
        result = engine.unregister_workflow("wf1")
        assert result == True
        assert engine.get_workflow("wf1") is None


class TestWorkflowDefinition:
    """工作流定义测试"""
    
    def test_add_step(self):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step = WorkflowStep(
            id="step1",
            name="Step 1",
            step_type=StepType.TASK
        )
        workflow.add_step(step)
        
        assert workflow.start_step == "step1"
        assert workflow.get_step("step1") is not None
    
    def test_get_next_steps(self):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step1 = WorkflowStep(
            id="step1",
            name="Step 1",
            step_type=StepType.TASK,
            next_steps=["step2", "step3"]
        )
        workflow.add_step(step1)
        
        next_steps = workflow.get_next_steps("step1")
        assert next_steps == ["step2", "step3"]
    
    def test_workflow_to_dict(self):
        workflow = WorkflowDefinition(
            id="wf1",
            name="Test",
            description="Test workflow"
        )
        step = WorkflowStep(id="s1", name="Step", step_type=StepType.TASK)
        workflow.add_step(step)
        
        data = workflow.to_dict()
        assert data["id"] == "wf1"
        assert data["name"] == "Test"
        assert "s1" in data["steps"]


class TestWorkflowInstance:
    """工作流实例测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_create_instance(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step = WorkflowStep(id="s1", name="Step", step_type=StepType.TASK)
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1", {"key": "value"})
        assert instance is not None
        assert instance.workflow_id == "wf1"
        assert instance.context["key"] == "value"
        assert instance.status == WorkflowStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_instance_unknown_workflow(self, engine):
        instance = await engine.create_instance("unknown")
        assert instance is None
    
    @pytest.mark.asyncio
    async def test_list_instances(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step = WorkflowStep(id="s1", name="Step", step_type=StepType.TASK)
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        await engine.create_instance("wf1")
        await engine.create_instance("wf1")
        
        instances = engine.list_instances()
        assert len(instances) == 2
        
        instances = engine.list_instances(workflow_id="wf1")
        assert len(instances) == 2


class TestWorkflowExecution:
    """工作流执行测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_start_instance(self, engine):
        # 创建简单工作流
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        async def handler(context, metadata):
            return {"result": "done"}
        
        step = WorkflowStep(
            id="s1",
            name="Step 1",
            step_type=StepType.TASK,
            handler=handler
        )
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        result = await engine.start_instance(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("result") == "done"
    
    @pytest.mark.asyncio
    async def test_multi_step_workflow(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        async def step1_handler(context, metadata):
            return {"step1": "done"}
        
        async def step2_handler(context, metadata):
            return {"step2": "done"}
        
        step1 = WorkflowStep(
            id="s1", name="Step 1", step_type=StepType.TASK,
            handler=step1_handler, next_steps=["s2"]
        )
        step2 = WorkflowStep(
            id="s2", name="Step 2", step_type=StepType.TASK,
            handler=step2_handler
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("step1") == "done"
        assert instance.context.get("step2") == "done"
    
    @pytest.mark.asyncio
    async def test_agent_call_step(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        step = WorkflowStep(
            id="s1", name="Agent Step", step_type=StepType.AGENT_CALL,
            agent_type="test_agent"
        )
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        # 注册Agent处理器
        async def agent_handler(context, metadata):
            return {"agent_result": "success"}
        
        engine.register_agent_handler("test_agent", agent_handler)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("agent_result") == "success"
    
    @pytest.mark.asyncio
    async def test_wait_step_pauses_workflow(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        step1 = WorkflowStep(
            id="s1", name="Wait Step", step_type=StepType.WAIT,
            next_steps=["s2"]
        )
        step2 = WorkflowStep(
            id="s2", name="Final Step", step_type=StepType.TASK
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        assert instance.status == WorkflowStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_resume_paused_workflow(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        step1 = WorkflowStep(
            id="s1", name="Wait Step", step_type=StepType.WAIT,
            next_steps=["s2"]
        )
        step2 = WorkflowStep(
            id="s2", name="Final Step", step_type=StepType.TASK
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        # 恢复工作流
        result = await engine.resume_instance(instance.id, {"user_input": "data"})
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("user_input") == "data"


class TestWorkflowTriggerConsistency:
    """Property 6: 立项工作流触发一致性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        workflow_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=20),
        workflow_name=st.text(min_size=1, max_size=50)
    )
    async def test_workflow_trigger_consistency(self, engine, workflow_id, workflow_name):
        """Property 6: 对于任何有效的工作流定义，触发后应该一致地启动"""
        # 创建工作流
        workflow = WorkflowDefinition(id=workflow_id, name=workflow_name)
        
        async def simple_handler(context, metadata):
            return {"executed": True}
        
        step = WorkflowStep(
            id="start",
            name="Start Step",
            step_type=StepType.TASK,
            handler=simple_handler
        )
        workflow.add_step(step)
        
        # 注册工作流
        engine.register_workflow(workflow)
        
        # 创建并启动实例
        instance = await engine.create_instance(workflow_id)
        assert instance is not None
        
        result = await engine.start_instance(instance.id)
        
        # Property: 工作流应该成功启动并完成
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("executed") == True
        
        # 清理
        engine.unregister_workflow(workflow_id)
    
    @pytest.mark.asyncio
    async def test_cancel_instance(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step = WorkflowStep(
            id="s1", name="Wait", step_type=StepType.WAIT,
            next_steps=["s2"]
        )
        step2 = WorkflowStep(id="s2", name="End", step_type=StepType.TASK)
        workflow.add_step(step)
        workflow.add_step(step2)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        result = await engine.cancel_instance(instance.id)
        assert result == True
        assert instance.status == WorkflowStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_step_failure_handling(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        async def failing_handler(context, metadata):
            raise Exception("Step failed")
        
        step = WorkflowStep(
            id="s1", name="Failing Step", step_type=StepType.TASK,
            handler=failing_handler, retry_count=0
        )
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        assert instance.status == WorkflowStatus.FAILED
        assert instance.error is not None
    
    @pytest.mark.asyncio
    async def test_step_retry(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        
        call_count = {"count": 0}
        
        async def retry_handler(context, metadata):
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise Exception("Temporary failure")
            return {"success": True}
        
        step = WorkflowStep(
            id="s1", name="Retry Step", step_type=StepType.TASK,
            handler=retry_handler, retry_count=2
        )
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        instance = await engine.create_instance("wf1")
        await engine.start_instance(instance.id)
        
        assert instance.status == WorkflowStatus.COMPLETED
        assert call_count["count"] == 2


class TestWorkflowStatistics:
    """工作流统计测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, engine):
        workflow = WorkflowDefinition(id="wf1", name="Test")
        step = WorkflowStep(id="s1", name="Step", step_type=StepType.TASK)
        workflow.add_step(step)
        engine.register_workflow(workflow)
        
        await engine.create_instance("wf1")
        instance2 = await engine.create_instance("wf1")
        await engine.start_instance(instance2.id)
        
        stats = engine.get_statistics()
        assert stats["total_workflows"] == 1
        assert stats["total_instances"] == 2
        assert stats["completed_instances"] == 1
