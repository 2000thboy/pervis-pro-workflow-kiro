"""
PM Agent属性测试 - 基于属性的测试验证项目归档完整性

Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
验证需求: Requirements 2.6 - WHEN 项目完成时 THEN PM_Agent SHALL 执行项目归档流程

测试策略:
- 使用Hypothesis生成随机的项目数据
- 验证PM Agent能够正确创建项目和文件夹结构
- 验证项目归档流程的完整性
"""
import pytest
import asyncio
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from hypothesis import given, strategies as st, settings, HealthCheck

from app.core.message_bus import MessageBus
from app.agents.pm_agent import (
    PMAgent,
    Project,
    ProjectStatus,
    ProjectPhase,
    ArchiveResult,
    STANDARD_FOLDER_STRUCTURE,
)


# 自定义策略：生成有效的项目ID (ASCII字母数字和下划线)
project_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
    min_size=3,
    max_size=30
).filter(lambda x: len(x.strip()) > 0 and x[0].isalpha())

# 自定义策略：生成项目名称
project_name_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-',
    min_size=1,
    max_size=50
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成标签
tag_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=1,
    max_size=20
).filter(lambda x: len(x.strip()) > 0)


class TestPMAgentProjectArchiving:
    """
    属性 11: 项目归档完整性
    
    *对于任何*已完成的项目，PM_Agent应该能够执行完整的归档流程
    
    验证需求: Requirements 2.6
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        project_id=project_id_strategy,
        project_name=project_name_strategy,
    )
    async def test_project_creation_creates_folder_structure(
        self,
        project_id: str,
        project_name: str,
    ):
        """
        Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
        
        属性: 对于任何项目创建请求，PM Agent应该创建完整的标准文件夹结构
        
        验证需求: Requirements 7.1
        """
        # 创建临时目录
        base_dir = tempfile.mkdtemp()
        archive_dir = tempfile.mkdtemp()
        
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            pm_agent = PMAgent(
                message_bus=bus,
                base_path=base_dir,
                archive_path=archive_dir,
            )
            await pm_agent.initialize()
            await pm_agent.start()
            
            # 创建项目
            project = await pm_agent.create_project(
                project_id=project_id,
                name=project_name,
            )
            
            # 验证属性1: 项目创建成功
            assert project is not None, "项目应该创建成功"
            assert project.project_id == project_id
            assert project.name == project_name
            
            # 验证属性2: 文件夹结构完整
            project_path = Path(project.folder_path)
            assert project_path.exists(), "项目文件夹应该存在"
            
            for folder in STANDARD_FOLDER_STRUCTURE:
                folder_path = project_path / folder
                assert folder_path.exists(), f"标准文件夹 {folder} 应该存在"
            
            await pm_agent.stop()
            
        finally:
            await bus.stop()
            # 清理临时目录
            shutil.rmtree(base_dir, ignore_errors=True)
            shutil.rmtree(archive_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        project_id=project_id_strategy,
        project_name=project_name_strategy,
    )
    async def test_project_archiving_preserves_all_files(
        self,
        project_id: str,
        project_name: str,
    ):
        """
        Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
        
        属性: 对于任何项目归档操作，所有项目文件应该被完整保存到归档目录
        
        验证需求: Requirements 2.6, 7.4
        """
        base_dir = tempfile.mkdtemp()
        archive_dir = tempfile.mkdtemp()
        
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            pm_agent = PMAgent(
                message_bus=bus,
                base_path=base_dir,
                archive_path=archive_dir,
            )
            await pm_agent.initialize()
            await pm_agent.start()
            
            # 创建项目
            project = await pm_agent.create_project(
                project_id=project_id,
                name=project_name,
            )
            assert project is not None
            
            # 在项目中创建一些测试文件
            project_path = Path(project.folder_path)
            test_files = [
                project_path / "assets/images/test.jpg",
                project_path / "scripts/script.txt",
            ]
            
            for test_file in test_files:
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text(f"test content for {test_file.name}")
            
            # 执行归档
            result = await pm_agent.archive_project(project_id)
            
            # 验证属性1: 归档成功
            assert result.success is True, f"归档应该成功: {result.error}"
            assert result.archive_path is not None
            
            # 验证属性2: 归档目录存在
            archive_path = Path(result.archive_path)
            assert archive_path.exists(), "归档目录应该存在"
            
            # 验证属性3: 所有文件都被归档
            assert result.files_archived >= len(test_files), \
                f"归档文件数量应该至少为 {len(test_files)}"
            
            # 验证属性4: 项目状态更新为已归档
            archived_project = pm_agent.get_project(project_id)
            assert archived_project.status == ProjectStatus.ARCHIVED
            
            await pm_agent.stop()
            
        finally:
            await bus.stop()
            shutil.rmtree(base_dir, ignore_errors=True)
            shutil.rmtree(archive_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        project_id=project_id_strategy,
    )
    async def test_duplicate_archive_prevented(
        self,
        project_id: str,
    ):
        """
        Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
        
        属性: 已归档的项目不能重复归档
        
        验证需求: Requirements 2.6
        """
        base_dir = tempfile.mkdtemp()
        archive_dir = tempfile.mkdtemp()
        
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            pm_agent = PMAgent(
                message_bus=bus,
                base_path=base_dir,
                archive_path=archive_dir,
            )
            await pm_agent.initialize()
            await pm_agent.start()
            
            # 创建并归档项目
            project = await pm_agent.create_project(
                project_id=project_id,
                name="Test Project",
            )
            assert project is not None
            
            # 第一次归档
            result1 = await pm_agent.archive_project(project_id)
            assert result1.success is True
            
            # 第二次归档应该失败
            result2 = await pm_agent.archive_project(project_id)
            assert result2.success is False, "重复归档应该失败"
            assert "已归档" in result2.error or "archived" in result2.error.lower()
            
            await pm_agent.stop()
            
        finally:
            await bus.stop()
            shutil.rmtree(base_dir, ignore_errors=True)
            shutil.rmtree(archive_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        project_id=project_id_strategy,
        project_name=project_name_strategy,
        tags=st.lists(tag_strategy, min_size=0, max_size=5, unique=True),
    )
    async def test_project_metadata_preserved(
        self,
        project_id: str,
        project_name: str,
        tags: List[str],
    ):
        """
        Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
        
        属性: 项目的所有元数据在创建和归档过程中应该被保留
        
        验证需求: Requirements 2.6
        """
        base_dir = tempfile.mkdtemp()
        archive_dir = tempfile.mkdtemp()
        
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            pm_agent = PMAgent(
                message_bus=bus,
                base_path=base_dir,
                archive_path=archive_dir,
            )
            await pm_agent.initialize()
            await pm_agent.start()
            
            # 创建项目
            project = await pm_agent.create_project(
                project_id=project_id,
                name=project_name,
                description="Test description",
                owner="test_owner",
                tags=tags,
            )
            
            assert project is not None
            
            # 验证元数据保留
            assert project.project_id == project_id
            assert project.name == project_name
            assert project.description == "Test description"
            assert project.owner == "test_owner"
            assert set(project.tags) == set(tags)
            
            # 归档后验证元数据仍然保留
            await pm_agent.archive_project(project_id)
            
            archived_project = pm_agent.get_project(project_id)
            assert archived_project.project_id == project_id
            assert archived_project.name == project_name
            assert archived_project.description == "Test description"
            assert archived_project.owner == "test_owner"
            assert set(archived_project.tags) == set(tags)
            assert archived_project.archived_at is not None
            
            await pm_agent.stop()
            
        finally:
            await bus.stop()
            shutil.rmtree(base_dir, ignore_errors=True)
            shutil.rmtree(archive_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        project_id=project_id_strategy,
    )
    async def test_archive_nonexistent_project_fails(
        self,
        project_id: str,
    ):
        """
        Feature: multi-agent-workflow-core, Property 11: 项目归档完整性
        
        属性: 归档不存在的项目应该返回错误
        
        验证需求: Requirements 2.6
        """
        base_dir = tempfile.mkdtemp()
        archive_dir = tempfile.mkdtemp()
        
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            pm_agent = PMAgent(
                message_bus=bus,
                base_path=base_dir,
                archive_path=archive_dir,
            )
            await pm_agent.initialize()
            await pm_agent.start()
            
            # 尝试归档不存在的项目
            result = await pm_agent.archive_project(project_id)
            
            # 验证属性: 归档应该失败
            assert result.success is False
            assert result.error is not None
            assert "不存在" in result.error or "not exist" in result.error.lower()
            
            await pm_agent.stop()
            
        finally:
            await bus.stop()
            shutil.rmtree(base_dir, ignore_errors=True)
            shutil.rmtree(archive_dir, ignore_errors=True)
