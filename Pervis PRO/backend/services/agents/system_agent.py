# -*- coding: utf-8 -*-
"""
System_Agent 服务（系统校验 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.8 实现 System_Agent

提供系统校验功能：
- 导出前全面校验
- 标签一致性检查
- 标签匹配百分比
- API 健康检查
- 页面错误检查

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """校验问题"""
    issue_id: str
    severity: str  # error, warning, info
    category: str  # tag, content, api, page
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "field": self.field,
            "suggestion": self.suggestion
        }


@dataclass
class TagConsistencyResult:
    """标签一致性检查结果"""
    is_consistent: bool
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "conflicts": self.conflicts,
            "suggestions": self.suggestions
        }


@dataclass
class TagMatchResult:
    """标签匹配结果"""
    query_tags: List[str]
    matched_assets: int
    total_assets: int
    match_percentage: float
    unmatched_tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_tags": self.query_tags,
            "matched_assets": self.matched_assets,
            "total_assets": self.total_assets,
            "match_percentage": self.match_percentage,
            "unmatched_tags": self.unmatched_tags
        }


@dataclass
class APIHealthResult:
    """API 健康检查结果"""
    endpoint: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "error": self.error
        }


@dataclass
class ValidationResult:
    """完整校验结果"""
    validation_id: str
    project_id: str
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    tag_consistency: Optional[TagConsistencyResult] = None
    api_health: List[APIHealthResult] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "project_id": self.project_id,
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "tag_consistency": self.tag_consistency.to_dict() if self.tag_consistency else None,
            "api_health": [h.to_dict() for h in self.api_health],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "created_at": self.created_at.isoformat()
        }


class SystemAgentService:
    """
    System_Agent 服务
    
    系统校验 Agent，负责导出前校验和系统健康检查
    """
    
    # 矛盾标签对
    CONFLICTING_TAGS = [
        ("室内", "室外"),
        ("白天", "夜晚"),
        ("现代", "古代"),
        ("喜剧", "悲剧"),
        ("动作", "静态"),
        ("明亮", "黑暗"),
        ("安静", "嘈杂"),
    ]
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self._base_url = base_url
        self._llm_adapter = None
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    async def validate_before_export(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        导出前全面校验
        
        检查项目数据完整性、标签一致性、API 可用性等
        """
        result = ValidationResult(
            validation_id=f"val_{uuid4().hex[:12]}",
            project_id=project_id,
            is_valid=True
        )
        
        # 1. 内容完整性检查
        content_issues = self._check_content_completeness(project_data)
        result.issues.extend(content_issues)
        
        # 2. 标签一致性检查
        tags = self._extract_all_tags(project_data)
        tag_result = self.check_tag_consistency(tags)
        result.tag_consistency = tag_result
        
        if not tag_result.is_consistent:
            for conflict in tag_result.conflicts:
                result.issues.append(ValidationIssue(
                    issue_id=f"tag_{uuid4().hex[:8]}",
                    severity="warning",
                    category="tag",
                    message=f"标签冲突: {conflict.get('tag1')} 与 {conflict.get('tag2')}",
                    suggestion=conflict.get("suggestion")
                ))
        
        # 3. API 健康检查
        api_results = await self.check_api_health()
        result.api_health = api_results
        
        for api in api_results:
            if api.status == "unhealthy":
                result.issues.append(ValidationIssue(
                    issue_id=f"api_{uuid4().hex[:8]}",
                    severity="error",
                    category="api",
                    message=f"API 不可用: {api.endpoint}",
                    suggestion="请检查后端服务是否正常运行"
                ))
        
        # 统计错误和警告
        result.error_count = sum(1 for i in result.issues if i.severity == "error")
        result.warning_count = sum(1 for i in result.issues if i.severity == "warning")
        result.is_valid = result.error_count == 0
        
        return result
    
    def _check_content_completeness(
        self,
        project_data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """检查内容完整性"""
        issues = []
        
        # 必填字段
        required_fields = [
            ("title", "项目标题"),
            ("project_type", "项目类型"),
        ]
        
        for field, name in required_fields:
            if not project_data.get(field):
                issues.append(ValidationIssue(
                    issue_id=f"req_{uuid4().hex[:8]}",
                    severity="error",
                    category="content",
                    message=f"缺少必填字段: {name}",
                    field=field,
                    suggestion=f"请填写{name}"
                ))
        
        # 建议字段
        recommended_fields = [
            ("logline", "一句话概要"),
            ("synopsis", "故事概要"),
        ]
        
        for field, name in recommended_fields:
            if not project_data.get(field):
                issues.append(ValidationIssue(
                    issue_id=f"rec_{uuid4().hex[:8]}",
                    severity="warning",
                    category="content",
                    message=f"建议填写: {name}",
                    field=field,
                    suggestion=f"填写{name}可以获得更好的 AI 辅助"
                ))
        
        # 场次检查
        scenes = project_data.get("scenes", [])
        if not scenes:
            issues.append(ValidationIssue(
                issue_id=f"scene_{uuid4().hex[:8]}",
                severity="warning",
                category="content",
                message="未定义场次",
                field="scenes",
                suggestion="添加场次信息以便进行故事板制作"
            ))
        else:
            for i, scene in enumerate(scenes):
                if not scene.get("description") and not scene.get("action"):
                    issues.append(ValidationIssue(
                        issue_id=f"scene_{uuid4().hex[:8]}",
                        severity="info",
                        category="content",
                        message=f"场次 {i+1} 缺少描述",
                        field=f"scenes[{i}].description"
                    ))
        
        return issues
    
    def _extract_all_tags(self, project_data: Dict[str, Any]) -> List[str]:
        """提取所有标签"""
        tags = []
        
        # 项目标签
        tags.extend(project_data.get("tags", []))
        
        # 角色标签
        for char in project_data.get("characters", []):
            char_tags = char.get("tags", {})
            if isinstance(char_tags, dict):
                tags.extend(char_tags.values())
            elif isinstance(char_tags, list):
                tags.extend(char_tags)
        
        # 场次标签
        for scene in project_data.get("scenes", []):
            tags.extend(scene.get("tags", []))
        
        # 素材标签
        for asset in project_data.get("assets", []):
            tags.extend(asset.get("tags", []))
        
        return list(set(tags))
    
    def check_tag_consistency(self, tags: List[str]) -> TagConsistencyResult:
        """
        检查标签一致性
        
        检测矛盾的标签组合
        """
        conflicts = []
        suggestions = []
        
        tags_lower = [t.lower() for t in tags]
        
        for tag1, tag2 in self.CONFLICTING_TAGS:
            if tag1 in tags_lower and tag2 in tags_lower:
                conflicts.append({
                    "tag1": tag1,
                    "tag2": tag2,
                    "suggestion": f"'{tag1}' 和 '{tag2}' 通常不会同时出现，请确认是否正确"
                })
        
        # 检查重复标签（不同大小写）
        seen = {}
        for tag in tags:
            lower = tag.lower()
            if lower in seen and seen[lower] != tag:
                suggestions.append(f"标签大小写不一致: '{seen[lower]}' vs '{tag}'")
            seen[lower] = tag
        
        return TagConsistencyResult(
            is_consistent=len(conflicts) == 0,
            conflicts=conflicts,
            suggestions=suggestions
        )
    
    async def check_tag_match_percentage(
        self,
        query_tags: List[str],
        asset_tags_list: List[List[str]]
    ) -> TagMatchResult:
        """
        检查标签匹配百分比
        
        预搜索标签与素材 TAG 的匹配情况
        """
        total_assets = len(asset_tags_list)
        if total_assets == 0:
            return TagMatchResult(
                query_tags=query_tags,
                matched_assets=0,
                total_assets=0,
                match_percentage=0.0,
                unmatched_tags=query_tags
            )
        
        matched_count = 0
        unmatched_tags = set(query_tags)
        
        for asset_tags in asset_tags_list:
            asset_tags_lower = [t.lower() for t in asset_tags]
            
            # 检查是否有任何查询标签匹配
            for qt in query_tags:
                if qt.lower() in asset_tags_lower:
                    matched_count += 1
                    unmatched_tags.discard(qt)
                    break
        
        return TagMatchResult(
            query_tags=query_tags,
            matched_assets=matched_count,
            total_assets=total_assets,
            match_percentage=(matched_count / total_assets) * 100,
            unmatched_tags=list(unmatched_tags)
        )
    
    async def check_api_health(self) -> List[APIHealthResult]:
        """
        检查 API 健康状态
        
        检测前后端接口是否正常
        """
        endpoints = [
            "/api/health",
            "/api/wizard/health",
            "/api/projects",
        ]
        
        results = []
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    start = datetime.now()
                    response = await client.get(f"{self._base_url}{endpoint}")
                    elapsed = (datetime.now() - start).total_seconds() * 1000
                    
                    if response.status_code == 200:
                        status = "healthy"
                    elif response.status_code < 500:
                        status = "degraded"
                    else:
                        status = "unhealthy"
                    
                    results.append(APIHealthResult(
                        endpoint=endpoint,
                        status=status,
                        response_time_ms=elapsed
                    ))
                    
                except httpx.TimeoutException:
                    results.append(APIHealthResult(
                        endpoint=endpoint,
                        status="unhealthy",
                        response_time_ms=5000,
                        error="请求超时"
                    ))
                except Exception as e:
                    results.append(APIHealthResult(
                        endpoint=endpoint,
                        status="unhealthy",
                        response_time_ms=0,
                        error=str(e)
                    ))
        
        return results
    
    async def check_page_errors(
        self,
        page_url: str
    ) -> List[ValidationIssue]:
        """
        检查页面错误
        
        检测展示页面是否有 bug 或报错
        （简化实现，实际应使用 Playwright 等工具）
        """
        issues = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(page_url)
                
                if response.status_code != 200:
                    issues.append(ValidationIssue(
                        issue_id=f"page_{uuid4().hex[:8]}",
                        severity="error",
                        category="page",
                        message=f"页面返回错误状态码: {response.status_code}",
                        suggestion="检查页面路由和服务器配置"
                    ))
                
                # 检查常见错误标记
                content = response.text.lower()
                error_markers = [
                    ("error", "页面包含错误信息"),
                    ("exception", "页面包含异常信息"),
                    ("undefined", "页面可能有未定义变量"),
                    ("null", "页面可能有空值错误"),
                ]
                
                for marker, message in error_markers:
                    if f"'{marker}'" in content or f'"{marker}"' in content:
                        issues.append(ValidationIssue(
                            issue_id=f"page_{uuid4().hex[:8]}",
                            severity="warning",
                            category="page",
                            message=message,
                            suggestion="检查浏览器控制台获取详细错误信息"
                        ))
                        break
                        
        except Exception as e:
            issues.append(ValidationIssue(
                issue_id=f"page_{uuid4().hex[:8]}",
                severity="error",
                category="page",
                message=f"无法访问页面: {str(e)}",
                suggestion="确保前端服务正在运行"
            ))
        
        return issues
    
    def get_validation_summary(
        self,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """获取校验摘要"""
        return {
            "is_valid": result.is_valid,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "info_count": sum(1 for i in result.issues if i.severity == "info"),
            "api_status": "healthy" if all(
                h.status == "healthy" for h in result.api_health
            ) else "degraded",
            "tag_consistent": result.tag_consistency.is_consistent if result.tag_consistency else True,
            "can_export": result.is_valid
        }


# 全局服务实例
_system_agent_service: Optional[SystemAgentService] = None


def get_system_agent_service(base_url: str = "http://localhost:8000") -> SystemAgentService:
    """获取 System_Agent 服务实例"""
    global _system_agent_service
    if _system_agent_service is None:
        _system_agent_service = SystemAgentService(base_url)
    return _system_agent_service
