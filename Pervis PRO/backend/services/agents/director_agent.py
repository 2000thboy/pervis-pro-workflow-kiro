# -*- coding: utf-8 -*-
"""
Director_Agent 服务（导演 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.4 实现 Director_Agent

提供审核相关的 AI 功能：
- 审核其他 Agent 输出（只输出建议）
- 规则校验（内容不为空、字数合理、格式正确）
- 项目规格一致性检查
- 艺术风格一致性检查（LLM）
- 历史版本对比（避免改回被否决版本）

Requirements: 2.3, 5.1.1-5.1.7
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ProjectSpecs:
    """项目规格"""
    duration: int = 0  # 时长（秒）
    aspect_ratio: str = "16:9"  # 画幅
    frame_rate: int = 24  # 帧率
    resolution: str = "1920x1080"  # 分辨率
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
            "frame_rate": self.frame_rate,
            "resolution": self.resolution
        }


@dataclass
class StyleContext:
    """艺术风格上下文"""
    description: str = ""
    reference_projects: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    mood: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "reference_projects": self.reference_projects,
            "color_palette": self.color_palette,
            "mood": self.mood
        }


@dataclass
class VersionRecord:
    """版本记录"""
    version_id: str
    content_type: str
    content: Any
    agent: str
    version: int
    created_at: datetime = field(default_factory=datetime.now)
    decision: str = ""  # accepted, rejected, modified


@dataclass
class ProjectContext:
    """项目上下文"""
    project_id: str
    specs: ProjectSpecs = field(default_factory=ProjectSpecs)
    style: StyleContext = field(default_factory=StyleContext)
    version_history: List[VersionRecord] = field(default_factory=list)
    user_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "specs": self.specs.to_dict(),
            "style": self.style.to_dict(),
            "version_count": len(self.version_history),
            "decision_count": len(self.user_decisions)
        }


@dataclass
class ReviewResult:
    """审核结果"""
    status: str  # approved, suggestions, rejected
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.9
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "suggestions": self.suggestions,
            "reason": self.reason,
            "confidence": self.confidence
        }


class DirectorAgentService:
    """
    Director_Agent 服务
    
    导演 Agent，负责审核其他 Agent 的输出
    具有项目记忆，包括项目规格、艺术风格、历史版本
    """
    
    # 内容类型的字数限制
    CONTENT_LIMITS = {
        "logline": (10, 100),
        "synopsis": (100, 1000),
        "character_bio": (50, 500),
        "scene_description": (20, 300),
        "visual_tags": (5, 50),
    }
    
    def __init__(self):
        self._llm_adapter = None
        self._project_contexts: Dict[str, ProjectContext] = {}
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    def get_project_context(self, project_id: str) -> ProjectContext:
        """获取项目上下文"""
        if project_id not in self._project_contexts:
            self._project_contexts[project_id] = ProjectContext(project_id=project_id)
        return self._project_contexts[project_id]
    
    def set_project_specs(self, project_id: str, specs: ProjectSpecs):
        """设置项目规格"""
        context = self.get_project_context(project_id)
        context.specs = specs
    
    def set_style_context(self, project_id: str, style: StyleContext):
        """设置艺术风格上下文"""
        context = self.get_project_context(project_id)
        context.style = style
    
    def add_version_record(
        self,
        project_id: str,
        content_type: str,
        content: Any,
        agent: str
    ) -> VersionRecord:
        """添加版本记录"""
        context = self.get_project_context(project_id)
        
        # 计算版本号
        existing_versions = [
            v for v in context.version_history 
            if v.content_type == content_type
        ]
        version = len(existing_versions) + 1
        
        record = VersionRecord(
            version_id=f"ver_{uuid4().hex[:8]}",
            content_type=content_type,
            content=content,
            agent=agent,
            version=version
        )
        context.version_history.append(record)
        return record
    
    def record_user_decision(
        self,
        project_id: str,
        version_id: str,
        decision: str,
        feedback: str = ""
    ):
        """记录用户决策"""
        context = self.get_project_context(project_id)
        
        # 更新版本记录
        for record in context.version_history:
            if record.version_id == version_id:
                record.decision = decision
                break
        
        # 添加决策记录
        context.user_decisions.append({
            "version_id": version_id,
            "decision": decision,
            "feedback": feedback,
            "created_at": datetime.now().isoformat()
        })
    
    async def review(
        self,
        result: Any,
        task_type: str,
        project_id: str = None
    ) -> ReviewResult:
        """
        审核 Agent 输出结果
        
        审核流程：
        1. 规则校验
        2. 项目规格一致性检查
        3. 艺术风格一致性检查
        4. 历史版本对比
        """
        review = ReviewResult(status="approved")
        
        # 1. 规则校验
        rule_result = self._check_rules(result, task_type)
        review.passed_checks.extend(rule_result.get("passed", []))
        review.failed_checks.extend(rule_result.get("failed", []))
        
        if rule_result.get("failed"):
            review.status = "rejected"
            review.reason = "规则校验未通过"
            return review
        
        # 获取项目上下文
        context = None
        if project_id:
            context = self.get_project_context(project_id)
        
        # 2. 项目规格一致性检查
        if context:
            spec_result = self._check_project_specs(result, context.specs, task_type)
            review.passed_checks.extend(spec_result.get("passed", []))
            if spec_result.get("suggestions"):
                review.suggestions.extend(spec_result["suggestions"])
        
        # 3. 艺术风格一致性检查（使用 LLM）
        if context and context.style.description:
            style_result = await self._check_style_consistency(result, context.style)
            if style_result:
                if not style_result.get("is_consistent", True):
                    review.suggestions.extend(style_result.get("suggestions", []))
        
        # 4. 历史版本对比
        if context and context.version_history:
            history_result = await self._compare_with_history(
                result, task_type, context
            )
            if history_result:
                review.suggestions.extend(history_result.get("suggestions", []))
        
        # 确定最终状态
        if review.suggestions:
            review.status = "suggestions"
            review.reason = "审核通过，但有改进建议"
        else:
            review.reason = "审核通过"
        
        return review
    
    def _check_rules(self, result: Any, task_type: str) -> Dict[str, List[str]]:
        """规则校验"""
        passed = []
        failed = []
        
        # 检查内容不为空
        if result is None:
            failed.append("内容为空")
            return {"passed": passed, "failed": failed}
        
        passed.append("内容不为空")
        
        # 检查字数
        content_str = str(result)
        if isinstance(result, dict):
            # 提取主要内容
            for key in ["logline", "synopsis", "bio", "description", "summary"]:
                if key in result:
                    content_str = str(result[key])
                    break
        
        limits = self.CONTENT_LIMITS.get(task_type)
        if limits:
            min_len, max_len = limits
            content_len = len(content_str)
            if content_len < min_len:
                failed.append(f"内容过短（{content_len} < {min_len}）")
            elif content_len > max_len:
                failed.append(f"内容过长（{content_len} > {max_len}）")
            else:
                passed.append(f"字数合理（{content_len}）")
        
        return {"passed": passed, "failed": failed}
    
    def _check_project_specs(
        self,
        result: Any,
        specs: ProjectSpecs,
        task_type: str
    ) -> Dict[str, Any]:
        """检查项目规格一致性"""
        passed = []
        suggestions = []
        
        if isinstance(result, dict):
            # 检查时长
            if "duration" in result or "estimated_duration" in result:
                duration = result.get("duration") or result.get("estimated_duration", 0)
                if specs.duration > 0 and duration > specs.duration * 1.2:
                    suggestions.append(f"估算时长（{duration}秒）超过项目设定（{specs.duration}秒）")
                else:
                    passed.append("时长符合项目设定")
        
        return {"passed": passed, "suggestions": suggestions}
    
    async def _check_style_consistency(
        self,
        result: Any,
        style: StyleContext
    ) -> Optional[Dict[str, Any]]:
        """检查艺术风格一致性（使用 LLM）"""
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            response = await adapter.check_style_consistency(result, style.to_dict())
            if response.success and response.parsed_data:
                return response.parsed_data
        except Exception as e:
            logger.error(f"风格一致性检查失败: {e}")
        
        return None
    
    async def _compare_with_history(
        self,
        result: Any,
        task_type: str,
        context: ProjectContext
    ) -> Optional[Dict[str, Any]]:
        """对比历史版本"""
        # 获取同类型的历史版本
        history = [
            v for v in context.version_history
            if v.content_type == task_type
        ]
        
        if not history:
            return None
        
        # 检查是否与被否决的版本相似
        rejected_versions = [
            v for v in history if v.decision == "rejected"
        ]
        
        suggestions = []
        for rejected in rejected_versions:
            # 简单的相似度检查（可以用 LLM 增强）
            if self._is_similar(result, rejected.content):
                suggestions.append(
                    f"当前内容与之前被否决的版本 v{rejected.version} 相似，"
                    "请注意避免重复之前的问题"
                )
        
        return {"suggestions": suggestions} if suggestions else None
    
    def _is_similar(self, content1: Any, content2: Any) -> bool:
        """简单的相似度检查"""
        str1 = str(content1).lower()
        str2 = str(content2).lower()
        
        # 简单的字符串相似度
        if len(str1) == 0 or len(str2) == 0:
            return False
        
        # 计算共同字符比例
        common = set(str1) & set(str2)
        similarity = len(common) / max(len(set(str1)), len(set(str2)))
        
        return similarity > 0.8
    
    async def get_review_suggestions(
        self,
        result: Any,
        task_type: str,
        project_id: str = None
    ) -> List[str]:
        """获取具体改进建议"""
        review = await self.review(result, task_type, project_id)
        return review.suggestions


# 全局服务实例
_director_agent_service: Optional[DirectorAgentService] = None


def get_director_agent_service() -> DirectorAgentService:
    """获取 Director_Agent 服务实例"""
    global _director_agent_service
    if _director_agent_service is None:
        _director_agent_service = DirectorAgentService()
    return _director_agent_service
