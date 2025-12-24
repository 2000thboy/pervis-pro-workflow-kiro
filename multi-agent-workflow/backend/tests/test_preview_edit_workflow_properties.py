# -*- coding: utf-8 -*-
"""
PreviewEditWorkflow Property Tests

Feature: multi-agent-workflow-core
Property 19: 预演模式启动正确性
Property 20: 数据一致性保持
Requirements: 4.1, 4.2
"""
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck as HypothesisHealthCheck

from app.workflows.workflow_engine import WorkflowEngine, WorkflowStatus
from app.workflows.preview_edit_workflow import (
    PreviewEditWorkflow,
    Timeline,
    TimelineClip,
    PreviewSession,
    PreviewStatus,
    SyncStatus,
    ClientType,
)


class TestPreviewEditWorkflowBasics:
    """预演剪辑工作流基础测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PreviewEditWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self, workflow, engine):
        """测试工作流注册"""
        wf = engine.get_workflow(PreviewEditWorkflow.WORKFLOW_ID)
        assert wf is not None
        assert wf.name == "预演剪辑工作流"
    
    @pytest.mark.asyncio
    async def test_start_preview_session(self, workflow):
        """测试启动预演会话"""
        clips = [
            {"asset_id": "asset_1", "duration": 5.0, "clip_type": "video"},
            {"asset_id": "asset_2", "duration": 3.0, "clip_type": "video"},
        ]
        
        instance = await workflow.start_preview_session(
            project_id="proj_1",
            timeline_name="测试时间线",
            clips=clips
        )
        
        assert instance is not None
        assert instance.status == WorkflowStatus.PAUSED
        assert instance.context.get("timeline_id") is not None
        assert instance.context.get("preview_status") == "ready"
    
    @pytest.mark.asyncio
    async def test_approve_preview(self, workflow):
        """测试审核通过预演"""
        instance = await workflow.start_preview_session("proj_1")
        result = await workflow.approve_preview(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("finalize_status") == "completed"
    
    @pytest.mark.asyncio
    async def test_reject_preview(self, workflow):
        """测试拒绝预演"""
        instance = await workflow.start_preview_session("proj_1")
        result = await workflow.reject_preview(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("finalize_status") == "rejected"


class TestPreviewModeStartup:
    """Property 19: 预演模式启动正确性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PreviewEditWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_timeline_creation(self, workflow):
        """测试时间线创建"""
        clips = [
            {"asset_id": "a1", "duration": 5.0},
            {"asset_id": "a2", "duration": 3.0},
        ]
        
        instance = await workflow.start_preview_session("proj_1", clips=clips)
        
        timeline_id = instance.context.get("timeline_id")
        timeline = workflow.get_timeline(timeline_id)
        
        assert timeline is not None
        assert len(timeline.clips) == 2
        assert timeline.total_duration == 8.0
    
    @pytest.mark.asyncio
    async def test_preview_generation(self, workflow):
        """测试预演生成"""
        instance = await workflow.start_preview_session("proj_1")
        
        assert instance.context.get("preview_url") is not None
        assert instance.context.get("preview_status") == "ready"
    
    @pytest.mark.asyncio
    async def test_session_creation(self, workflow):
        """测试会话创建"""
        instance = await workflow.start_preview_session("proj_1")
        
        session_id = instance.context.get("session_id")
        session = workflow.get_session(session_id)
        
        assert session is not None
        assert session.status == PreviewStatus.READY
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        project_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=20),
        clip_count=st.integers(min_value=0, max_value=5)
    )
    async def test_preview_startup_correctness_property(self, engine, project_id, clip_count):
        """Property 19: 对于任何有效的项目，预演模式应该正确启动"""
        workflow = PreviewEditWorkflow(engine)
        
        clips = [
            {"asset_id": f"asset_{i}", "duration": 5.0}
            for i in range(clip_count)
        ]
        
        instance = await workflow.start_preview_session(project_id, clips=clips)
        
        # Property: 预演应该成功启动
        assert instance is not None
        assert instance.context.get("timeline_id") is not None
        assert instance.context.get("session_id") is not None
        assert instance.context.get("preview_status") == "ready"


class TestDataConsistency:
    """Property 20: 数据一致性保持"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PreviewEditWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_client_connection(self, workflow):
        """测试客户端连接"""
        instance = await workflow.start_preview_session("proj_1")
        session_id = instance.context.get("session_id")
        
        client = workflow.connect_client(session_id, ClientType.WEB)
        
        assert client is not None
        assert client.sync_status == SyncStatus.SYNCED
        
        session = workflow.get_session(session_id)
        assert client.id in session.connected_clients
    
    @pytest.mark.asyncio
    async def test_client_disconnection(self, workflow):
        """测试客户端断开"""
        instance = await workflow.start_preview_session("proj_1")
        session_id = instance.context.get("session_id")
        
        client = workflow.connect_client(session_id, ClientType.WEB)
        result = workflow.disconnect_client(client.id)
        
        assert result == True
        
        session = workflow.get_session(session_id)
        assert client.id not in session.connected_clients
    
    @pytest.mark.asyncio
    async def test_client_sync(self, workflow):
        """测试客户端同步"""
        instance = await workflow.start_preview_session("proj_1")
        session_id = instance.context.get("session_id")
        
        client = workflow.connect_client(session_id, ClientType.DESKTOP)
        result = workflow.sync_client(client.id)
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_timeline_update_triggers_sync(self, workflow):
        """测试时间线更新触发同步"""
        instance = await workflow.start_preview_session("proj_1")
        timeline_id = instance.context.get("timeline_id")
        session_id = instance.context.get("session_id")
        
        # 连接客户端
        workflow.connect_client(session_id, ClientType.WEB)
        
        # 更新时间线
        workflow.update_timeline(timeline_id, {"name": "新名称"})
        
        # 检查同步状态
        session = workflow.get_session(session_id)
        assert session.sync_status == SyncStatus.OUT_OF_SYNC
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        client_count=st.integers(min_value=1, max_value=5)
    )
    async def test_data_consistency_property(self, engine, client_count):
        """Property 20: 对于任何数量的客户端，数据应该保持一致"""
        workflow = PreviewEditWorkflow(engine)
        
        instance = await workflow.start_preview_session("proj_test")
        session_id = instance.context.get("session_id")
        timeline_id = instance.context.get("timeline_id")
        
        # 连接多个客户端
        clients = []
        for i in range(client_count):
            client_type = [ClientType.WEB, ClientType.DESKTOP, ClientType.MOBILE][i % 3]
            client = workflow.connect_client(session_id, client_type)
            clients.append(client)
        
        # Property: 所有客户端应该连接到同一个会话
        session = workflow.get_session(session_id)
        assert len(session.connected_clients) == client_count
        
        # 更新时间线
        workflow.update_timeline(timeline_id, {"name": "更新后"})
        
        # Property: 更新后会话应该标记为需要同步
        assert session.sync_status == SyncStatus.OUT_OF_SYNC


class TestPreviewManagement:
    """预演管理测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PreviewEditWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, workflow):
        """测试列出会话"""
        await workflow.start_preview_session("proj_1")
        await workflow.start_preview_session("proj_2")
        
        sessions = workflow.list_sessions()
        assert len(sessions) >= 2
    
    @pytest.mark.asyncio
    async def test_list_sessions_by_timeline(self, workflow):
        """测试按时间线列出会话"""
        instance = await workflow.start_preview_session("proj_1")
        timeline_id = instance.context.get("timeline_id")
        
        sessions = workflow.list_sessions(timeline_id=timeline_id)
        assert len(sessions) >= 1
        assert all(s.timeline_id == timeline_id for s in sessions)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, workflow):
        """测试获取统计信息"""
        instance = await workflow.start_preview_session("proj_1")
        session_id = instance.context.get("session_id")
        workflow.connect_client(session_id, ClientType.WEB)
        
        stats = workflow.get_statistics()
        assert stats["total_timelines"] >= 1
        assert stats["total_sessions"] >= 1
        assert stats["total_clients"] >= 1
