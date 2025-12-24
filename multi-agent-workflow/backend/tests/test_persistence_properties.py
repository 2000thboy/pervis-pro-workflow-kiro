# -*- coding: utf-8 -*-
"""
数据持久化服务属性测试

Feature: multi-agent-workflow-core
Property 37: 中间状态保存实时性
Property 38: 数据存储规范一致性
Requirements: 7.2, 7.3, 7.5
"""
import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck as HypothesisHealthCheck
from datetime import datetime

from app.core.persistence import (
    PersistenceService,
    PersistenceConfig,
    StorageProvider,
    ProjectData,
    WorkflowStateData,
    AgentStateData,
    MemoryStorage,
)


class TestPersistenceServiceBasics:
    """持久化服务基础测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        """创建内存持久化服务"""
        config = PersistenceConfig.memory()
        service = PersistenceService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service.is_initialized
        assert service.config.provider == StorageProvider.MEMORY
    
    @pytest.mark.asyncio
    async def test_create_project(self, service):
        """测试创建项目"""
        project = await service.create_project(
            name="测试项目",
            description="这是一个测试项目",
            aspect_ratio="16:9",
            duration=120
        )
        
        assert project is not None
        assert project.id is not None
        assert project.name == "测试项目"
        assert project.status == "created"
    
    @pytest.mark.asyncio
    async def test_get_project(self, service):
        """测试获取项目"""
        created = await service.create_project(name="测试")
        
        retrieved = await service.get_project(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "测试"
    
    @pytest.mark.asyncio
    async def test_update_project(self, service):
        """测试更新项目"""
        project = await service.create_project(name="原始名称")
        
        updated = await service.update_project(
            project.id,
            name="新名称",
            status="in_progress"
        )
        
        assert updated is not None
        assert updated.name == "新名称"
        assert updated.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_delete_project(self, service):
        """测试删除项目"""
        project = await service.create_project(name="待删除")
        
        result = await service.delete_project(project.id)
        assert result == True
        
        retrieved = await service.get_project(project.id)
        assert retrieved is None


class TestProjectSearch:
    """
    项目检索测试
    
    验证需求: Requirements 7.5
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = PersistenceConfig.memory()
        service = PersistenceService(config)
        await service.initialize()
        
        # 创建测试项目
        await service.create_project(
            name="城市夜景短片",
            description="关于城市夜生活的纪录片",
            story_summary="探索城市夜晚的魅力"
        )
        await service.create_project(
            name="森林探险",
            description="自然纪录片",
            story_summary="深入原始森林"
        )
        await service.create_project(
            name="城市建筑",
            description="现代建筑设计",
            story_summary="城市建筑之美"
        )
        
        return service
    
    @pytest.mark.asyncio
    async def test_search_by_name(self, service):
        """测试按名称搜索"""
        results = await service.search_projects("城市")
        
        assert len(results) >= 2
        for r in results:
            assert "城市" in r.name or "城市" in r.description or "城市" in r.story_summary
    
    @pytest.mark.asyncio
    async def test_search_by_description(self, service):
        """测试按描述搜索"""
        results = await service.search_projects("纪录片")
        
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_search_limit(self, service):
        """测试搜索结果限制"""
        results = await service.search_projects("城市", limit=1)
        
        assert len(results) <= 1
    
    @pytest.mark.asyncio
    async def test_list_projects_by_status(self, service):
        """测试按状态列出项目"""
        # 更新一个项目状态
        projects = await service.list_projects()
        if projects:
            await service.update_project(projects[0].id, status="completed")
        
        completed = await service.list_projects(status="completed")
        created = await service.list_projects(status="created")
        
        assert len(completed) >= 1
        assert len(created) >= 2


class TestWorkflowStatePersistence:
    """
    工作流状态持久化测试
    
    Property 37: 中间状态保存实时性
    验证需求: Requirements 7.2
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = PersistenceConfig.memory()
        service = PersistenceService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_save_workflow_state(self, service):
        """测试保存工作流状态"""
        state = await service.save_workflow_state(
            workflow_id="wf_001",
            workflow_type="project_setup",
            project_id="proj_001",
            status="running",
            current_step="collect_info",
            context={"step": 1}
        )
        
        assert state is not None
        assert state.id == "wf_001"
        assert state.status == "running"
        assert state.started_at is not None
    
    @pytest.mark.asyncio
    async def test_update_workflow_state(self, service):
        """测试更新工作流状态"""
        # 创建初始状态
        await service.save_workflow_state(
            workflow_id="wf_002",
            workflow_type="beatboard",
            project_id="proj_001",
            status="running",
            current_step="step1"
        )
        
        # 更新状态
        updated = await service.save_workflow_state(
            workflow_id="wf_002",
            workflow_type="beatboard",
            project_id="proj_001",
            status="paused",
            current_step="step2",
            steps_completed=["step1"]
        )
        
        assert updated.status == "paused"
        assert updated.current_step == "step2"
        assert "step1" in updated.steps_completed
    
    @pytest.mark.asyncio
    async def test_workflow_completion(self, service):
        """测试工作流完成"""
        await service.save_workflow_state(
            workflow_id="wf_003",
            workflow_type="preview_edit",
            project_id="proj_001",
            status="running"
        )
        
        completed = await service.save_workflow_state(
            workflow_id="wf_003",
            workflow_type="preview_edit",
            project_id="proj_001",
            status="completed"
        )
        
        assert completed.status == "completed"
        assert completed.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_list_workflow_states_by_project(self, service):
        """测试按项目列出工作流状态"""
        await service.save_workflow_state(
            workflow_id="wf_a1",
            workflow_type="project_setup",
            project_id="proj_a",
            status="completed"
        )
        await service.save_workflow_state(
            workflow_id="wf_a2",
            workflow_type="beatboard",
            project_id="proj_a",
            status="running"
        )
        await service.save_workflow_state(
            workflow_id="wf_b1",
            workflow_type="project_setup",
            project_id="proj_b",
            status="running"
        )
        
        proj_a_workflows = await service.list_workflow_states(project_id="proj_a")
        
        assert len(proj_a_workflows) == 2
        assert all(w.project_id == "proj_a" for w in proj_a_workflows)
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        workflow_type=st.sampled_from(["project_setup", "beatboard", "preview_edit"]),
        status=st.sampled_from(["pending", "running", "paused", "completed", "failed"]),
        current_step=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz_')
    )
    async def test_workflow_state_persistence_property(self, service, workflow_type, status, current_step):
        """
        Property 37: 中间状态保存实时性
        
        对于任何工作流进行中的操作，系统应该实时保存所有中间状态
        """
        workflow_id = f"wf_{hash(current_step) % 10000}"
        
        state = await service.save_workflow_state(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            project_id="test_proj",
            status=status,
            current_step=current_step
        )
        
        # 验证：状态应该被保存
        assert state is not None
        assert state.status == status
        assert state.current_step == current_step
        
        # 验证：可以立即检索到保存的状态
        retrieved = await service.get_workflow_state(workflow_id)
        assert retrieved is not None
        assert retrieved.status == status


class TestAgentStatePersistence:
    """
    Agent状态持久化测试
    
    Property 38: 数据存储规范一致性
    验证需求: Requirements 7.3
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = PersistenceConfig.memory()
        service = PersistenceService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_save_agent_state(self, service):
        """测试保存Agent状态"""
        state = await service.save_agent_state(
            agent_id="director_001",
            agent_type="director",
            state="working",
            current_task="协调项目",
            capabilities=["coordinate", "resolve_conflicts"]
        )
        
        assert state is not None
        assert state.agent_id == "director_001"
        assert state.state == "working"
    
    @pytest.mark.asyncio
    async def test_update_agent_state(self, service):
        """测试更新Agent状态"""
        await service.save_agent_state(
            agent_id="system_001",
            agent_type="system",
            state="idle"
        )
        
        updated = await service.update_agent_state(
            agent_id="system_001",
            state="working",
            current_task="处理用户请求"
        )
        
        assert updated is not None
        assert updated.state == "working"
        assert updated.current_task == "处理用户请求"
    
    @pytest.mark.asyncio
    async def test_list_all_agent_states(self, service):
        """测试列出所有Agent状态"""
        await service.save_agent_state(agent_id="agent_1", agent_type="director", state="idle")
        await service.save_agent_state(agent_id="agent_2", agent_type="system", state="working")
        await service.save_agent_state(agent_id="agent_3", agent_type="dam", state="idle")
        
        states = await service.list_agent_states()
        
        assert len(states) == 3
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        agent_type=st.sampled_from(["director", "system", "dam", "pm", "script", "art", "market", "backend"]),
        state=st.sampled_from(["idle", "working", "waiting", "error", "offline"])
    )
    async def test_agent_state_persistence_property(self, service, agent_type, state):
        """
        Property 38: 数据存储规范一致性
        
        对于任何Agent产生的数据，都应该按照统一规范进行存储
        """
        agent_id = f"{agent_type}_{hash(state) % 1000}"
        
        saved = await service.save_agent_state(
            agent_id=agent_id,
            agent_type=agent_type,
            state=state
        )
        
        # 验证：数据应该按规范存储
        assert saved is not None
        assert saved.agent_id == agent_id
        assert saved.agent_type == agent_type
        assert saved.state == state
        
        # 验证：可以检索到存储的数据
        retrieved = await service.get_agent_state(agent_id)
        assert retrieved is not None
        assert retrieved.agent_type == agent_type


class TestProjectDataModel:
    """项目数据模型测试"""
    
    def test_project_to_dict(self):
        """测试项目转字典"""
        project = ProjectData(
            id="proj_001",
            name="测试项目",
            description="描述",
            aspect_ratio="16:9",
            duration=120,
            status="created"
        )
        
        d = project.to_dict()
        
        assert d["id"] == "proj_001"
        assert d["name"] == "测试项目"
        assert "created_at" in d
    
    def test_project_from_dict(self):
        """测试从字典创建项目"""
        data = {
            "id": "proj_002",
            "name": "从字典创建",
            "description": "测试",
            "aspect_ratio": "4:3",
            "duration": 60,
            "status": "in_progress"
        }
        
        project = ProjectData.from_dict(data)
        
        assert project.id == "proj_002"
        assert project.name == "从字典创建"
        assert project.aspect_ratio == "4:3"


class TestWorkflowStateDataModel:
    """工作流状态数据模型测试"""
    
    def test_workflow_state_to_dict(self):
        """测试工作流状态转字典"""
        state = WorkflowStateData(
            id="wf_001",
            workflow_type="project_setup",
            project_id="proj_001",
            status="running",
            current_step="step1",
            steps_completed=["init"],
            context={"key": "value"}
        )
        
        d = state.to_dict()
        
        assert d["id"] == "wf_001"
        assert d["status"] == "running"
        assert d["steps_completed"] == ["init"]
    
    def test_workflow_state_from_dict(self):
        """测试从字典创建工作流状态"""
        data = {
            "id": "wf_002",
            "workflow_type": "beatboard",
            "project_id": "proj_001",
            "status": "completed",
            "current_step": "done",
            "steps_completed": ["step1", "step2"]
        }
        
        state = WorkflowStateData.from_dict(data)
        
        assert state.id == "wf_002"
        assert state.status == "completed"


class TestStatistics:
    """统计功能测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = PersistenceConfig.memory()
        service = PersistenceService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, service):
        """测试获取统计信息"""
        # 创建一些数据
        await service.create_project(name="项目1")
        await service.create_project(name="项目2")
        project = await service.create_project(name="项目3")
        await service.update_project(project.id, status="completed")
        
        await service.save_workflow_state(
            workflow_id="wf1",
            workflow_type="project_setup",
            project_id="p1",
            status="completed"
        )
        await service.save_workflow_state(
            workflow_id="wf2",
            workflow_type="beatboard",
            project_id="p1",
            status="running"
        )
        
        await service.save_agent_state(agent_id="a1", agent_type="director", state="idle")
        await service.save_agent_state(agent_id="a2", agent_type="system", state="working")
        
        stats = await service.get_statistics()
        
        assert stats["total_projects"] == 3
        assert stats["total_workflows"] == 2
        assert stats["total_agents"] == 2
        assert "projects_by_status" in stats
        assert "workflows_by_status" in stats
        assert "agents_by_state" in stats


class TestPersistenceConfig:
    """持久化配置测试"""
    
    def test_memory_config(self):
        """测试内存配置"""
        config = PersistenceConfig.memory()
        
        assert config.provider == StorageProvider.MEMORY
    
    def test_sqlite_config(self):
        """测试SQLite配置"""
        config = PersistenceConfig.sqlite("test.db")
        
        assert config.provider == StorageProvider.SQLITE
        assert "test.db" in config.database_url
    
    def test_postgresql_config(self):
        """测试PostgreSQL配置"""
        config = PersistenceConfig.postgresql("postgresql://localhost/test")
        
        assert config.provider == StorageProvider.POSTGRESQL
        assert config.database_url == "postgresql://localhost/test"
