# -*- coding: utf-8 -*-
"""
PM_Agent 服务（项目管理 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.5 实现 PM_Agent

提供版本管理功能：
- 记录版本
- 生成版本命名
- 记录用户决策
- 获取版本显示信息

Requirements: 5.2.1, 5.2.2, 5.2.3, 5.2.4, 5.2.5, 5.2.6, 5.2.7
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ContentVersion:
    """内容版本"""
    version_id: str
    version_name: str
    version_number: int
    content_type: str  # logline, synopsis, character_bio, scene, etc.
    entity_id: Optional[str] = None  # 角色ID、场次ID等
    entity_name: Optional[str] = None
    content: Any = None
    source: str = "user"  # user, script_agent, art_agent
    status: str = "draft"  # draft, approved, rejected
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "version_name": self.version_name,
            "version_number": self.version_number,
            "content_type": self.content_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "content": self.content,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }


@dataclass
class UserDecision:
    """用户决策记录"""
    decision_id: str
    project_id: str
    decision_type: str  # approve, reject, modify, select
    target_type: str  # version, candidate, suggestion
    target_id: str
    previous_value: Any = None
    new_value: Any = None
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "project_id": self.project_id,
            "decision_type": self.decision_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class VersionDisplayInfo:
    """版本显示信息"""
    current_version: str
    version_count: int
    last_modified: str
    last_modified_by: str
    has_pending_changes: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)


class PMAgentService:
    """
    PM_Agent 服务
    
    项目管理 Agent，负责版本管理和用户决策记录
    """
    
    def __init__(self):
        # 版本存储 {project_id: {content_type: {entity_id: [versions]}}}
        self._versions: Dict[str, Dict[str, Dict[str, List[ContentVersion]]]] = {}
        # 决策存储 {project_id: [decisions]}
        self._decisions: Dict[str, List[UserDecision]] = {}
    
    def record_version(
        self,
        project_id: str,
        content_type: str,
        content: Any,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        source: str = "user"
    ) -> ContentVersion:
        """
        记录版本
        
        Args:
            project_id: 项目ID
            content_type: 内容类型
            content: 内容数据
            entity_id: 实体ID（如角色ID）
            entity_name: 实体名称
            source: 来源
        
        Returns:
            新创建的版本
        """
        # 初始化存储结构
        if project_id not in self._versions:
            self._versions[project_id] = {}
        if content_type not in self._versions[project_id]:
            self._versions[project_id][content_type] = {}
        
        entity_key = entity_id or "_default"
        if entity_key not in self._versions[project_id][content_type]:
            self._versions[project_id][content_type][entity_key] = []
        
        # 计算版本号
        existing_versions = self._versions[project_id][content_type][entity_key]
        version_number = len(existing_versions) + 1
        
        # 生成版本名称
        version_name = self.generate_version_name(
            content_type, entity_name, version_number
        )
        
        # 创建版本
        version = ContentVersion(
            version_id=f"ver_{uuid4().hex[:12]}",
            version_name=version_name,
            version_number=version_number,
            content_type=content_type,
            entity_id=entity_id,
            entity_name=entity_name,
            content=content,
            source=source
        )
        
        existing_versions.append(version)
        logger.info(f"记录版本: {version_name} (项目: {project_id})")
        
        return version
    
    def generate_version_name(
        self,
        content_type: str,
        entity_name: Optional[str],
        version_number: int
    ) -> str:
        """
        生成版本命名
        
        格式: {内容类型}_{实体名}_{版本号}
        例如: 角色_张三_v1, Logline_v2
        """
        type_names = {
            "logline": "Logline",
            "synopsis": "Synopsis",
            "character_bio": "角色",
            "scene": "场次",
            "visual_tags": "视觉标签",
            "market_analysis": "市场分析"
        }
        
        type_name = type_names.get(content_type, content_type)
        
        if entity_name:
            return f"{type_name}_{entity_name}_v{version_number}"
        else:
            return f"{type_name}_v{version_number}"
    
    def record_decision(
        self,
        project_id: str,
        decision_type: str,
        target_type: str,
        target_id: str,
        previous_value: Any = None,
        new_value: Any = None,
        reason: str = ""
    ) -> UserDecision:
        """
        记录用户决策
        
        Args:
            project_id: 项目ID
            decision_type: 决策类型 (approve, reject, modify, select)
            target_type: 目标类型 (version, candidate, suggestion)
            target_id: 目标ID
            previous_value: 之前的值
            new_value: 新值
            reason: 决策原因
        
        Returns:
            决策记录
        """
        if project_id not in self._decisions:
            self._decisions[project_id] = []
        
        decision = UserDecision(
            decision_id=f"dec_{uuid4().hex[:12]}",
            project_id=project_id,
            decision_type=decision_type,
            target_type=target_type,
            target_id=target_id,
            previous_value=previous_value,
            new_value=new_value,
            reason=reason
        )
        
        self._decisions[project_id].append(decision)
        logger.info(f"记录决策: {decision_type} on {target_type} (项目: {project_id})")
        
        return decision
    
    def get_version_display_info(
        self,
        project_id: str,
        content_type: str,
        entity_id: Optional[str] = None
    ) -> VersionDisplayInfo:
        """
        获取版本显示信息
        
        Returns:
            版本显示信息，包含当前版本、历史记录等
        """
        entity_key = entity_id or "_default"
        
        versions = (
            self._versions
            .get(project_id, {})
            .get(content_type, {})
            .get(entity_key, [])
        )
        
        if not versions:
            return VersionDisplayInfo(
                current_version="无版本",
                version_count=0,
                last_modified="",
                last_modified_by=""
            )
        
        latest = versions[-1]
        
        return VersionDisplayInfo(
            current_version=latest.version_name,
            version_count=len(versions),
            last_modified=latest.created_at.isoformat(),
            last_modified_by=latest.created_by,
            has_pending_changes=latest.status == "draft",
            history=[v.to_dict() for v in versions[-10:]]  # 最近10个版本
        )
    
    def get_version_history(
        self,
        project_id: str,
        content_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ContentVersion]:
        """获取版本历史"""
        if project_id not in self._versions:
            return []
        
        all_versions = []
        
        for ct, entities in self._versions[project_id].items():
            if content_type and ct != content_type:
                continue
            for eid, versions in entities.items():
                if entity_id and eid != entity_id:
                    continue
                all_versions.extend(versions)
        
        # 按时间倒序
        all_versions.sort(key=lambda v: v.created_at, reverse=True)
        return all_versions[:limit]
    
    def restore_version(
        self,
        project_id: str,
        version_id: str
    ) -> Optional[ContentVersion]:
        """
        恢复到历史版本
        
        创建一个新版本，内容与指定历史版本相同
        """
        # 查找版本
        target_version = None
        for ct, entities in self._versions.get(project_id, {}).items():
            for eid, versions in entities.items():
                for v in versions:
                    if v.version_id == version_id:
                        target_version = v
                        break
        
        if not target_version:
            logger.warning(f"版本不存在: {version_id}")
            return None
        
        # 创建新版本（恢复）
        new_version = self.record_version(
            project_id=project_id,
            content_type=target_version.content_type,
            content=target_version.content,
            entity_id=target_version.entity_id,
            entity_name=target_version.entity_name,
            source="restore"
        )
        
        # 记录决策
        self.record_decision(
            project_id=project_id,
            decision_type="restore",
            target_type="version",
            target_id=version_id,
            new_value=new_version.version_id,
            reason=f"恢复到版本 {target_version.version_name}"
        )
        
        return new_version
    
    def approve_version(
        self,
        project_id: str,
        version_id: str
    ) -> bool:
        """批准版本"""
        for ct, entities in self._versions.get(project_id, {}).items():
            for eid, versions in entities.items():
                for v in versions:
                    if v.version_id == version_id:
                        v.status = "approved"
                        self.record_decision(
                            project_id=project_id,
                            decision_type="approve",
                            target_type="version",
                            target_id=version_id
                        )
                        return True
        return False
    
    def reject_version(
        self,
        project_id: str,
        version_id: str,
        reason: str = ""
    ) -> bool:
        """拒绝版本"""
        for ct, entities in self._versions.get(project_id, {}).items():
            for eid, versions in entities.items():
                for v in versions:
                    if v.version_id == version_id:
                        v.status = "rejected"
                        self.record_decision(
                            project_id=project_id,
                            decision_type="reject",
                            target_type="version",
                            target_id=version_id,
                            reason=reason
                        )
                        return True
        return False
    
    def get_decision_history(
        self,
        project_id: str,
        limit: int = 100
    ) -> List[UserDecision]:
        """获取决策历史"""
        decisions = self._decisions.get(project_id, [])
        return decisions[-limit:]
    
    def check_rejected_content(
        self,
        project_id: str,
        content: Any,
        content_type: str
    ) -> Optional[str]:
        """
        检查内容是否与被拒绝的版本相似
        
        用于避免 Agent 生成被用户否决过的内容
        """
        entity_key = "_default"
        versions = (
            self._versions
            .get(project_id, {})
            .get(content_type, {})
            .get(entity_key, [])
        )
        
        for v in versions:
            if v.status == "rejected":
                # 简单比较（实际应用中可以用更复杂的相似度算法）
                if str(content) == str(v.content):
                    return f"内容与被拒绝的版本 {v.version_name} 相同"
        
        return None


# 全局服务实例
_pm_agent_service: Optional[PMAgentService] = None


def get_pm_agent_service() -> PMAgentService:
    """获取 PM_Agent 服务实例"""
    global _pm_agent_service
    if _pm_agent_service is None:
        _pm_agent_service = PMAgentService()
    return _pm_agent_service
