# -*- coding: utf-8 -*-
"""
BeatboardWorkflow Property Tests

Feature: multi-agent-workflow-core
Property 12: 场次分析准确性
Property 17: 素材装配正确性
Requirements: 3.1, 3.6
"""
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck as HypothesisHealthCheck

from app.workflows.workflow_engine import WorkflowEngine, WorkflowStatus
from app.workflows.beatboard_workflow import (
    BeatboardWorkflow,
    Beatboard,
    BeatboardItem,
    SceneAnalysis,
    SceneType,
    ShotType,
)


class TestBeatboardWorkflowBasics:
    """故事板工作流基础测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return BeatboardWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self, workflow, engine):
        """测试工作流注册"""
        wf = engine.get_workflow(BeatboardWorkflow.WORKFLOW_ID)
        assert wf is not None
        assert wf.name == "故事板工作流"
    
    @pytest.mark.asyncio
    async def test_start_beatboard_creation(self, workflow):
        """测试启动故事板创建"""
        script = """
场景1 - 内景 - 办公室 - 日
张三走进办公室。
张三：早上好！
李四：你好！
"""
        instance = await workflow.start_beatboard_creation("proj_1", script)
        
        assert instance is not None
        assert instance.status == WorkflowStatus.PAUSED
        assert instance.context.get("total_scenes") >= 1
    
    @pytest.mark.asyncio
    async def test_approve_beatboard(self, workflow):
        """测试审核通过故事板"""
        script = "场景1 - 测试场景\n内容"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        result = await workflow.approve_beatboard(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("assemble_status") == "completed"
    
    @pytest.mark.asyncio
    async def test_reject_beatboard(self, workflow):
        """测试拒绝故事板"""
        script = "场景1 - 测试场景"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        result = await workflow.reject_beatboard(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("assemble_status") == "rejected"


class TestSceneAnalysis:
    """Property 12: 场次分析准确性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return BeatboardWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_scene_parsing(self, workflow):
        """测试场景解析"""
        script = """
INT. 办公室 - 日
张三坐在桌前。

EXT. 街道 - 夜
李四走在路上。
"""
        instance = await workflow.start_beatboard_creation("proj_1", script)
        
        parsed_scenes = instance.context.get("parsed_scenes", [])
        assert len(parsed_scenes) == 2
    
    @pytest.mark.asyncio
    async def test_scene_type_detection(self, workflow):
        """测试场景类型检测"""
        script = "INT. 室内场景\n内容"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        
        parsed_scenes = instance.context.get("parsed_scenes", [])
        assert len(parsed_scenes) >= 1
        assert parsed_scenes[0]["scene_type"] == "interior"
    
    @pytest.mark.asyncio
    async def test_dialogue_detection(self, workflow):
        """测试对话检测"""
        script = """
场景1 - 办公室
张三：你好！
李四：早上好！
王五：大家好！
"""
        instance = await workflow.start_beatboard_creation("proj_1", script)
        
        analyzed_scenes = instance.context.get("analyzed_scenes", [])
        assert len(analyzed_scenes) >= 1
        # 应该检测到对话
        assert analyzed_scenes[0].get("dialogue_count", 0) >= 1
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        scene_count=st.integers(min_value=1, max_value=5),
        location=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=20)
    )
    async def test_scene_analysis_accuracy_property(self, engine, scene_count, location):
        """Property 12: 对于任何有效的剧本，场次分析应该正确识别场景数量"""
        workflow = BeatboardWorkflow(engine)
        
        # 生成包含指定数量场景的剧本
        scenes = []
        for i in range(scene_count):
            scenes.append(f"场景{i+1} - {location}{i+1}\n内容{i+1}")
        script = "\n\n".join(scenes)
        
        instance = await workflow.start_beatboard_creation("proj_test", script)
        
        # Property: 解析的场景数量应该等于输入的场景数量
        parsed_scenes = instance.context.get("parsed_scenes", [])
        assert len(parsed_scenes) == scene_count


class TestAssetAssembly:
    """Property 17: 素材装配正确性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return BeatboardWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_asset_matching(self, workflow):
        """测试素材匹配"""
        script = "场景1 - 办公室\n内容"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        
        asset_matches = instance.context.get("asset_matches", {})
        assert len(asset_matches) >= 1
    
    @pytest.mark.asyncio
    async def test_beatboard_assembly(self, workflow):
        """测试故事板装配"""
        script = "场景1 - 办公室\n内容"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        await workflow.approve_beatboard(instance.id)
        
        beatboard_id = instance.context.get("beatboard_id")
        beatboard = workflow.get_beatboard(beatboard_id)
        
        assert beatboard is not None
        assert len(beatboard.scenes) >= 1
        assert len(beatboard.items) >= 1
    
    @pytest.mark.asyncio
    async def test_beatboard_duration_calculation(self, workflow):
        """测试故事板时长计算"""
        script = """
场景1 - 办公室
内容1

场景2 - 街道
内容2
"""
        instance = await workflow.start_beatboard_creation("proj_1", script)
        await workflow.approve_beatboard(instance.id)
        
        beatboard_id = instance.context.get("beatboard_id")
        beatboard = workflow.get_beatboard(beatboard_id)
        
        assert beatboard is not None
        assert beatboard.total_duration > 0
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        project_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=20)
    )
    async def test_asset_assembly_correctness_property(self, engine, project_id):
        """Property 17: 对于任何审核通过的故事板，素材装配应该正确关联"""
        workflow = BeatboardWorkflow(engine)
        
        script = "场景1 - 测试场景\n测试内容"
        
        instance = await workflow.start_beatboard_creation(project_id, script)
        await workflow.approve_beatboard(instance.id)
        
        beatboard_id = instance.context.get("beatboard_id")
        beatboard = workflow.get_beatboard(beatboard_id)
        
        # Property: 故事板应该正确关联项目
        assert beatboard is not None
        assert beatboard.project_id == project_id
        
        # Property: 每个故事板项目应该关联到场景
        for item in beatboard.items:
            assert item.scene_id is not None
            # 场景应该存在于故事板中
            scene_ids = [s.scene_id for s in beatboard.scenes]
            assert item.scene_id in scene_ids


class TestBeatboardManagement:
    """故事板管理测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return BeatboardWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_list_beatboards(self, workflow):
        """测试列出故事板"""
        script = "场景1 - 测试"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        await workflow.approve_beatboard(instance.id)
        
        beatboards = workflow.list_beatboards()
        assert len(beatboards) >= 1
    
    @pytest.mark.asyncio
    async def test_list_beatboards_by_project(self, workflow):
        """测试按项目列出故事板"""
        script = "场景1 - 测试"
        
        instance = await workflow.start_beatboard_creation("proj_specific", script)
        await workflow.approve_beatboard(instance.id)
        
        beatboards = workflow.list_beatboards(project_id="proj_specific")
        assert len(beatboards) >= 1
        assert all(b.project_id == "proj_specific" for b in beatboards)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, workflow):
        """测试获取统计信息"""
        script = "场景1 - 测试"
        
        instance = await workflow.start_beatboard_creation("proj_1", script)
        await workflow.approve_beatboard(instance.id)
        
        stats = workflow.get_statistics()
        assert stats["total_beatboards"] >= 1
        assert stats["total_scenes"] >= 1
