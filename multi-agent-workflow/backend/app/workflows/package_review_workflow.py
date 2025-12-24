# -*- coding: utf-8 -*-
"""
Package Review Workflow - 文件打包和审阅工作流

实现文件打包、质量审阅和最终交付功能
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowStatus,
    StepType,
)


class PackageStatus(Enum):
    """打包状态"""
    PENDING = "pending"
    PACKAGING = "packaging"
    READY = "ready"
    DELIVERED = "delivered"
    ERROR = "error"


class ReviewStatus(Enum):
    """审阅状态"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNACCEPTABLE = "unacceptable"


@dataclass
class PackageFile:
    """打包文件"""
    id: str
    name: str
    file_type: str
    size_bytes: int
    path: str
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file_type": self.file_type,
            "size_bytes": self.size_bytes,
            "path": self.path,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }


@dataclass
class Package:
    """打包结果"""
    id: str
    project_id: str
    name: str
    files: List[PackageFile] = field(default_factory=list)
    total_size_bytes: int = 0
    status: PackageStatus = PackageStatus.PENDING
    output_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "files": [f.to_dict() for f in self.files],
            "total_size_bytes": self.total_size_bytes,
            "status": self.status.value,
            "output_path": self.output_path,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ReviewItem:
    """审阅项目"""
    id: str
    category: str
    description: str
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    comments: str = ""
    reviewer: str = ""
    reviewed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "quality_level": self.quality_level.value,
            "comments": self.comments,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


@dataclass
class Review:
    """审阅结果"""
    id: str
    package_id: str
    status: ReviewStatus = ReviewStatus.PENDING
    items: List[ReviewItem] = field(default_factory=list)
    overall_quality: QualityLevel = QualityLevel.ACCEPTABLE
    summary: str = ""
    reviewer: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "package_id": self.package_id,
            "status": self.status.value,
            "items": [i.to_dict() for i in self.items],
            "overall_quality": self.overall_quality.value,
            "summary": self.summary,
            "reviewer": self.reviewer,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


class PackageReviewWorkflow:
    """文件打包和审阅工作流"""
    
    WORKFLOW_ID = "package_review"
    WORKFLOW_NAME = "文件打包审阅工作流"
    
    def __init__(
        self,
        engine: WorkflowEngine,
        packager: Optional[Callable] = None,
        quality_checker: Optional[Callable] = None
    ):
        self.engine = engine
        self.packager = packager or self._default_packager
        self.quality_checker = quality_checker or self._default_quality_checker
        self._packages: Dict[str, Package] = {}
        self._reviews: Dict[str, Review] = {}
        
        # 注册工作流
        self._register_workflow()
    
    def _register_workflow(self) -> None:
        """注册打包审阅工作流"""
        workflow = WorkflowDefinition(
            id=self.WORKFLOW_ID,
            name=self.WORKFLOW_NAME,
            description="文件打包和质量审阅流程"
        )
        
        # Step 1: 收集文件
        step1 = WorkflowStep(
            id="collect_files",
            name="收集文件",
            step_type=StepType.TASK,
            handler=self._collect_files_handler,
            next_steps=["package_files"]
        )
        
        # Step 2: 打包文件
        step2 = WorkflowStep(
            id="package_files",
            name="打包文件",
            step_type=StepType.TASK,
            handler=self._package_files_handler,
            next_steps=["quality_check"]
        )
        
        # Step 3: 质量检查
        step3 = WorkflowStep(
            id="quality_check",
            name="质量检查",
            step_type=StepType.TASK,
            handler=self._quality_check_handler,
            next_steps=["user_review"]
        )
        
        # Step 4: 用户审阅
        step4 = WorkflowStep(
            id="user_review",
            name="用户审阅",
            step_type=StepType.WAIT,
            next_steps=["finalize_delivery"]
        )
        
        # Step 5: 完成交付
        step5 = WorkflowStep(
            id="finalize_delivery",
            name="完成交付",
            step_type=StepType.TASK,
            handler=self._finalize_delivery_handler
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        workflow.add_step(step5)
        
        self.engine.register_workflow(workflow)

    
    # 步骤处理器
    async def _collect_files_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """收集文件"""
        project_id = context.get("project_id", str(uuid.uuid4()))
        files_data = context.get("files", [])
        
        collected_files = []
        total_size = 0
        
        for file_data in files_data:
            file = PackageFile(
                id=str(uuid.uuid4()),
                name=file_data.get("name", "unknown"),
                file_type=file_data.get("file_type", "unknown"),
                size_bytes=file_data.get("size_bytes", 0),
                path=file_data.get("path", ""),
            )
            collected_files.append(file)
            total_size += file.size_bytes
        
        return {
            "project_id": project_id,
            "collected_files": [f.to_dict() for f in collected_files],
            "total_files": len(collected_files),
            "total_size_bytes": total_size,
            "collect_status": "completed"
        }
    
    async def _package_files_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """打包文件"""
        project_id = context.get("project_id")
        collected_files = context.get("collected_files", [])
        package_name = context.get("package_name", f"package_{project_id[:8]}")
        
        # 创建打包
        package_id = str(uuid.uuid4())
        package = Package(
            id=package_id,
            project_id=project_id,
            name=package_name,
            status=PackageStatus.PACKAGING,
        )
        
        # 添加文件
        for file_data in collected_files:
            file = PackageFile(
                id=file_data.get("id", str(uuid.uuid4())),
                name=file_data.get("name", ""),
                file_type=file_data.get("file_type", ""),
                size_bytes=file_data.get("size_bytes", 0),
                path=file_data.get("path", ""),
            )
            package.files.append(file)
            package.total_size_bytes += file.size_bytes
        
        # 执行打包
        package_result = await self.packager(package)
        
        package.status = PackageStatus.READY
        package.output_path = package_result.get("output_path", f"/packages/{package_id}")
        self._packages[package_id] = package
        
        return {
            "package_id": package_id,
            "package": package.to_dict(),
            "package_status": "ready",
            "output_path": package.output_path,
        }
    
    async def _quality_check_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """质量检查"""
        package_id = context.get("package_id")
        package = self._packages.get(package_id)
        
        if not package:
            return {"quality_status": "error", "error": "Package not found"}
        
        # 创建审阅
        review_id = str(uuid.uuid4())
        review = Review(
            id=review_id,
            package_id=package_id,
            status=ReviewStatus.IN_REVIEW,
        )
        
        # 执行质量检查
        check_result = await self.quality_checker(package)
        
        # 添加审阅项目
        for item_data in check_result.get("items", []):
            item = ReviewItem(
                id=str(uuid.uuid4()),
                category=item_data.get("category", "general"),
                description=item_data.get("description", ""),
                quality_level=QualityLevel(item_data.get("quality_level", "acceptable")),
                comments=item_data.get("comments", ""),
            )
            review.items.append(item)
        
        review.overall_quality = QualityLevel(check_result.get("overall_quality", "acceptable"))
        review.summary = check_result.get("summary", "")
        self._reviews[review_id] = review
        
        return {
            "review_id": review_id,
            "review": review.to_dict(),
            "quality_status": "checked",
            "overall_quality": review.overall_quality.value,
        }
    
    async def _finalize_delivery_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """完成交付"""
        package_id = context.get("package_id")
        review_id = context.get("review_id")
        user_approved = context.get("user_approved", True)
        
        package = self._packages.get(package_id)
        review = self._reviews.get(review_id)
        
        if not package or not review:
            return {"delivery_status": "error", "error": "Package or review not found"}
        
        if user_approved:
            package.status = PackageStatus.DELIVERED
            review.status = ReviewStatus.APPROVED
            review.completed_at = datetime.now()
            return {
                "delivery_status": "completed",
                "package_id": package_id,
                "output_path": package.output_path,
            }
        else:
            review.status = ReviewStatus.REJECTED
            review.completed_at = datetime.now()
            return {
                "delivery_status": "rejected",
                "package_id": package_id,
            }

    
    # 默认处理器
    async def _default_packager(self, package: Package) -> Dict[str, Any]:
        """默认打包器"""
        return {
            "output_path": f"/packages/{package.id}.zip",
            "format": "zip",
            "compressed_size": int(package.total_size_bytes * 0.7),
        }
    
    async def _default_quality_checker(self, package: Package) -> Dict[str, Any]:
        """默认质量检查器"""
        items = [
            {
                "category": "completeness",
                "description": "文件完整性检查",
                "quality_level": "good",
                "comments": f"共{len(package.files)}个文件",
            },
            {
                "category": "format",
                "description": "文件格式检查",
                "quality_level": "acceptable",
                "comments": "格式符合要求",
            },
        ]
        
        return {
            "items": items,
            "overall_quality": "good",
            "summary": "质量检查通过",
        }
    
    # 公共API
    async def start_package_review(
        self,
        project_id: str,
        files: List[Dict[str, Any]],
        package_name: Optional[str] = None
    ) -> Optional[WorkflowInstance]:
        """启动打包审阅流程"""
        instance = await self.engine.create_instance(
            self.WORKFLOW_ID,
            context={
                "project_id": project_id,
                "files": files,
                "package_name": package_name,
            }
        )
        
        if instance:
            await self.engine.start_instance(instance.id)
        
        return instance
    
    async def approve_delivery(self, instance_id: str) -> bool:
        """审核通过交付"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": True}
        )
    
    async def reject_delivery(self, instance_id: str) -> bool:
        """拒绝交付"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": False}
        )
    
    # 查询API
    def get_package(self, package_id: str) -> Optional[Package]:
        """获取打包"""
        return self._packages.get(package_id)
    
    def get_review(self, review_id: str) -> Optional[Review]:
        """获取审阅"""
        return self._reviews.get(review_id)
    
    def list_packages(self, project_id: Optional[str] = None) -> List[Package]:
        """列出打包"""
        packages = list(self._packages.values())
        if project_id:
            packages = [p for p in packages if p.project_id == project_id]
        return packages
    
    def list_reviews(self, status: Optional[ReviewStatus] = None) -> List[Review]:
        """列出审阅"""
        reviews = list(self._reviews.values())
        if status:
            reviews = [r for r in reviews if r.status == status]
        return reviews
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        packages = list(self._packages.values())
        reviews = list(self._reviews.values())
        return {
            "total_packages": len(packages),
            "delivered_packages": len([p for p in packages if p.status == PackageStatus.DELIVERED]),
            "total_reviews": len(reviews),
            "approved_reviews": len([r for r in reviews if r.status == ReviewStatus.APPROVED]),
        }
