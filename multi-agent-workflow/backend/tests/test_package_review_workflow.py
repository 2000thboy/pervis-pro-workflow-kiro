# -*- coding: utf-8 -*-
"""
PackageReviewWorkflow Tests

Feature: multi-agent-workflow-core
Requirements: 4.6, 4.7
"""
import pytest
import pytest_asyncio

from app.workflows.workflow_engine import WorkflowEngine, WorkflowStatus
from app.workflows.package_review_workflow import (
    PackageReviewWorkflow,
    Package,
    PackageFile,
    PackageStatus,
    Review,
    ReviewStatus,
    QualityLevel,
)


class TestPackageReviewWorkflowBasics:
    """打包审阅工作流基础测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PackageReviewWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_workflow_registration(self, workflow, engine):
        """测试工作流注册"""
        wf = engine.get_workflow(PackageReviewWorkflow.WORKFLOW_ID)
        assert wf is not None
        assert wf.name == "文件打包审阅工作流"
    
    @pytest.mark.asyncio
    async def test_start_package_review(self, workflow):
        """测试启动打包审阅"""
        files = [
            {"name": "video.mp4", "file_type": "video", "size_bytes": 1000000, "path": "/videos/video.mp4"},
            {"name": "audio.mp3", "file_type": "audio", "size_bytes": 500000, "path": "/audio/audio.mp3"},
        ]
        
        instance = await workflow.start_package_review(
            project_id="proj_1",
            files=files,
            package_name="测试打包"
        )
        
        assert instance is not None
        assert instance.status == WorkflowStatus.PAUSED
        assert instance.context.get("package_id") is not None
        assert instance.context.get("quality_status") == "checked"
    
    @pytest.mark.asyncio
    async def test_approve_delivery(self, workflow):
        """测试审核通过交付"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        result = await workflow.approve_delivery(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("delivery_status") == "completed"
    
    @pytest.mark.asyncio
    async def test_reject_delivery(self, workflow):
        """测试拒绝交付"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        result = await workflow.reject_delivery(instance.id)
        
        assert result == True
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.context.get("delivery_status") == "rejected"


class TestPackageCreation:
    """打包创建测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PackageReviewWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_file_collection(self, workflow):
        """测试文件收集"""
        files = [
            {"name": "file1.mp4", "file_type": "video", "size_bytes": 1000},
            {"name": "file2.mp4", "file_type": "video", "size_bytes": 2000},
        ]
        
        instance = await workflow.start_package_review("proj_1", files)
        
        assert instance.context.get("total_files") == 2
        assert instance.context.get("total_size_bytes") == 3000
    
    @pytest.mark.asyncio
    async def test_package_creation(self, workflow):
        """测试打包创建"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        
        package_id = instance.context.get("package_id")
        package = workflow.get_package(package_id)
        
        assert package is not None
        assert package.status == PackageStatus.READY
        assert len(package.files) == 1
    
    @pytest.mark.asyncio
    async def test_package_output_path(self, workflow):
        """测试打包输出路径"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        
        assert instance.context.get("output_path") is not None


class TestQualityReview:
    """质量审阅测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PackageReviewWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_quality_check(self, workflow):
        """测试质量检查"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        
        review_id = instance.context.get("review_id")
        review = workflow.get_review(review_id)
        
        assert review is not None
        assert len(review.items) >= 1
    
    @pytest.mark.asyncio
    async def test_overall_quality(self, workflow):
        """测试整体质量评估"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        
        assert instance.context.get("overall_quality") is not None
    
    @pytest.mark.asyncio
    async def test_review_status_after_approval(self, workflow):
        """测试审核后审阅状态"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        await workflow.approve_delivery(instance.id)
        
        review_id = instance.context.get("review_id")
        review = workflow.get_review(review_id)
        
        assert review.status == ReviewStatus.APPROVED
        assert review.completed_at is not None


class TestPackageManagement:
    """打包管理测试"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        engine = WorkflowEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    @pytest_asyncio.fixture
    async def workflow(self, engine):
        return PackageReviewWorkflow(engine)
    
    @pytest.mark.asyncio
    async def test_list_packages(self, workflow):
        """测试列出打包"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        await workflow.start_package_review("proj_1", files)
        await workflow.start_package_review("proj_2", files)
        
        packages = workflow.list_packages()
        assert len(packages) >= 2
    
    @pytest.mark.asyncio
    async def test_list_packages_by_project(self, workflow):
        """测试按项目列出打包"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        await workflow.start_package_review("proj_specific", files)
        
        packages = workflow.list_packages(project_id="proj_specific")
        assert len(packages) >= 1
        assert all(p.project_id == "proj_specific" for p in packages)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, workflow):
        """测试获取统计信息"""
        files = [{"name": "test.txt", "file_type": "text", "size_bytes": 100, "path": "/test.txt"}]
        
        instance = await workflow.start_package_review("proj_1", files)
        await workflow.approve_delivery(instance.id)
        
        stats = workflow.get_statistics()
        assert stats["total_packages"] >= 1
        assert stats["delivered_packages"] >= 1
        assert stats["total_reviews"] >= 1
        assert stats["approved_reviews"] >= 1
