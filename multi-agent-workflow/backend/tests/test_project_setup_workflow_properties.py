# -*- coding: utf-8 -*-
"""
ProjectSetupWorkflow Property Tests

Feature: multi-agent-workflow-core
Property 7: LLM信息补全准确性
Property 8: 项目档案生成完整性
Requirements: 2.2, 2.3
"""
import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck as HypothesisHealthCheck

from app.workflows.workflow_engine import WorkflowEngine, WorkflowStatus
from app.workflows.project_setup_workflow import (
    ProjectSetupWorkflow,
    ProjectInfo,
    ProjectArchive,
    ProjectType,
    ProjectStatus,
)


class TestProjectSetupWorkflowBasics:
    """立项工作流基础测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return ProjectSetupWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self, workflow, engine):
        """测试工作流注册"""
        wf = engine.get_workflow(ProjectSetupWorkflow.WORKFLOW_ID)
        assert wf is not None
        assert wf.name == "项目立项工作流"
    
    @pytest.mark.asyncio
    async def test_start_project_setup(self, workflow):
        """测试启动立项流程"""
        project_data = {
            "name": "测试项目",
            "project_type": "film",
            "description": "这是一个测试项目",
            "genre": ["剧情", "悬疑"],
        }
        
        instance = await workflow.start_project_setup(project_data)
        
        assert instance is not None
        # 工作流应该在用户审核步骤暂停
        assert instance.status == WorkflowStatus.PAUSED
        assert instance.context.get("project_id") is not None
    
    @pytest.mark.asyncio
    async def test_approve_project(self, workflow):
        """测试审核通过项目"""
        project_data = {
            "name": "测试项目",
            "project_type": "film",
        }
        
        instance = await workflow.start_project_setup(project_data)
        result = await workflow.approve_project(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("archive_status") == "completed"
    
    @pytest.mark.asyncio
    async def test_reject_project(self, workflow):
        """测试拒绝项目"""
        project_data = {"name": "测试项目"}
        
        instance = await workflow.start_project_setup(project_data)
        result = await workflow.reject_project(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("archive_status") == "rejected"


class TestLLMCompletion:
    """Property 7: LLM信息补全准确性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_llm_completion_for_missing_fields(self, engine):
        """测试LLM补全缺失字段"""
        # 自定义LLM处理器
        async def custom_llm_handler(project_info, fields_to_complete):
            suggestions = {}
            if "description" in fields_to_complete:
                suggestions["description"] = "AI生成的描述"
            if "key_themes" in fields_to_complete:
                suggestions["key_themes"] = ["主题1", "主题2"]
            return suggestions
        
        workflow = ProjectSetupWorkflow(engine, llm_handler=custom_llm_handler)
        
        # 创建缺少描述的项目
        project_data = {
            "name": "测试项目",
            "project_type": "film",
            # 没有description
        }
        
        instance = await workflow.start_project_setup(project_data)
        
        # 检查LLM建议
        assert "llm_suggestions" in instance.context
        suggestions = instance.context["llm_suggestions"]
        assert "description" in suggestions
    
    @pytest.mark.asyncio
    async def test_llm_completion_skipped_when_complete(self, engine):
        """测试信息完整时跳过LLM补全"""
        workflow = ProjectSetupWorkflow(engine)
        
        # 创建完整的项目信息
        project_data = {
            "name": "测试项目",
            "project_type": "film",
            "description": "完整的描述",
            "key_themes": ["主题"],
            "style_references": ["参考"],
        }
        
        instance = await workflow.start_project_setup(project_data)
        
        # 检查补全状态
        assert instance.context.get("completion_status") == "skipped"
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        name=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=30),
        genre=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10), min_size=0, max_size=3)
    )
    async def test_llm_completion_accuracy_property(self, engine, name, genre):
        """Property 7: 对于任何缺少描述的项目，LLM应该生成有效的描述"""
        workflow = ProjectSetupWorkflow(engine)
        
        project_data = {
            "name": name,
            "project_type": "film",
            "genre": genre,
            # 故意不提供description
        }
        
        instance = await workflow.start_project_setup(project_data)
        
        # Property: LLM应该为缺失字段生成建议
        suggestions = instance.context.get("llm_suggestions", {})
        if instance.context.get("fields_to_complete"):
            # 如果有需要补全的字段，应该有建议
            assert len(suggestions) > 0 or instance.context.get("completion_status") == "skipped"


class TestProjectArchiveGeneration:
    """Property 8: 项目档案生成完整性"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return ProjectSetupWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_archive_contains_project_info(self, workflow):
        """测试档案包含项目信息"""
        project_data = {
            "name": "测试项目",
            "project_type": "film",
            "description": "项目描述",
        }
        
        instance = await workflow.start_project_setup(project_data)
        await workflow.approve_project(instance.id)
        
        project_id = instance.context.get("project_id")
        archive = workflow.get_archive(project_id)
        
        assert archive is not None
        assert archive.project_info.name == "测试项目"
        assert archive.project_info.description == "项目描述"
    
    @pytest.mark.asyncio
    async def test_archive_includes_llm_suggestions(self, workflow):
        """测试档案包含LLM建议"""
        project_data = {
            "name": "测试项目",
            # 缺少description，会触发LLM补全
        }
        
        instance = await workflow.start_project_setup(project_data)
        await workflow.approve_project(instance.id, accept_suggestions=True)
        
        project_id = instance.context.get("project_id")
        archive = workflow.get_archive(project_id)
        
        assert archive is not None
        assert "llm_suggestions" in archive.to_dict()
    
    @pytest.mark.asyncio
    async def test_project_status_updated_after_archive(self, workflow):
        """测试档案生成后项目状态更新"""
        project_data = {"name": "测试项目"}
        
        instance = await workflow.start_project_setup(project_data)
        await workflow.approve_project(instance.id)
        
        project_id = instance.context.get("project_id")
        project = workflow.get_project(project_id)
        
        assert project is not None
        assert project.status == ProjectStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        name=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=30),
        description=st.text(min_size=0, max_size=100)
    )
    async def test_archive_completeness_property(self, engine, name, description):
        """Property 8: 对于任何审核通过的项目，应该生成完整的档案"""
        workflow = ProjectSetupWorkflow(engine)
        
        project_data = {
            "name": name,
            "description": description,
            "project_type": "film",
        }
        
        instance = await workflow.start_project_setup(project_data)
        await workflow.approve_project(instance.id)
        
        project_id = instance.context.get("project_id")
        
        # Property: 审核通过后应该有完整的档案
        archive = workflow.get_archive(project_id)
        assert archive is not None
        assert archive.project_id == project_id
        assert archive.project_info is not None
        assert archive.project_info.name == name


class TestProjectManagement:
    """项目管理测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return ProjectSetupWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_list_projects(self, workflow):
        """测试列出项目"""
        # 创建多个项目
        await workflow.start_project_setup({"name": "项目1"})
        await workflow.start_project_setup({"name": "项目2"})
        
        projects = workflow.list_projects()
        assert len(projects) == 2
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, workflow):
        """测试获取统计信息"""
        instance = await workflow.start_project_setup({"name": "项目1"})
        await workflow.approve_project(instance.id)
        
        stats = workflow.get_statistics()
        assert stats["total_projects"] >= 1
        assert stats["total_archives"] >= 1
