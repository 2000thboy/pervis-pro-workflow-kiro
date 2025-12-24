"""
导演Agent - 项目总控和决策中心

需求: 1.3 - WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突
需求: 2.5 - WHEN 人工审核通过后 THEN 导演Agent SHALL 调配所有工作台开始协作

本模块实现了导演Agent，负责:
- 协调所有其他Agent的工作
- 解决Agent间的冲突
- 调配工作台和资源
- 项目总体决策
"""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .base_agent import BaseAgent, AgentLifecycleState
from ..core.message_bus import MessageBus, Message, Response
from ..core.agent_types import AgentState, AgentType
from ..core.communication_protocol import (
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
    ProtocolResponse,
)

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型枚举"""
    RESOURCE_CONFLICT = "resource_conflict"      # 资源冲突
    TASK_CONFLICT = "task_conflict"              # 任务冲突
    PRIORITY_CONFLICT = "priority_conflict"      # 优先级冲突
    DATA_CONFLICT = "data_conflict"              # 数据冲突
    WORKFLOW_CONFLICT = "workflow_conflict"      # 工作流冲突


class ConflictResolutionStrategy(Enum):
    """冲突解决策略"""
    PRIORITY_BASED = "priority_based"            # 基于优先级
    TIMESTAMP_BASED = "timestamp_based"          # 基于时间戳
    VOTING = "voting"                            # 投票决定
    DIRECTOR_DECISION = "director_decision"      # 导演直接决定
    MERGE = "merge"                              # 合并解决


@dataclass
class ConflictReport:
    """冲突报告"""
    conflict_id: str
    conflict_type: ConflictType
    reporter_agent: str
    involved_agents: List[str]
    details: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False
    resolution: Optional[Dict[str, Any]] = None
    resolution_strategy: Optional[ConflictResolutionStrategy] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "reporter_agent": self.reporter_agent,
            "involved_agents": self.involved_agents,
            "details": self.details,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "resolution_strategy": self.resolution_strategy.value if self.resolution_strategy else None
        }


@dataclass
class AgentAssignment:
    """Agent任务分配"""
    agent_id: str
    agent_type: AgentType
    task_id: str
    task_type: str
    task_data: Dict[str, Any]
    assigned_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "task_data": self.task_data,
            "assigned_at": self.assigned_at,
            "status": self.status
        }


class DirectorAgent(BaseAgent):
    """
    导演Agent - 项目总控和决策中心
    
    作为系统的核心协调者，导演Agent负责:
    - 协调所有其他Agent的工作
    - 解决Agent间的冲突（作为最终决策者）
    - 调配工作台和资源
    - 管理项目总体进度
    
    需求: 1.3 - 发生Agent冲突时作为最终决策者解决冲突
    需求: 2.5 - 人工审核通过后调配所有工作台开始协作
    """
    
    # 导演Agent的固定ID
    DIRECTOR_AGENT_ID = "director"
    
    def __init__(
        self,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化导演Agent
        
        Args:
            message_bus: 消息总线实例
            config: 配置选项
        """
        super().__init__(
            agent_id=self.DIRECTOR_AGENT_ID,
            agent_type=AgentType.DIRECTOR,
            message_bus=message_bus,
            capabilities=[
                "conflict_resolution",
                "agent_coordination",
                "task_assignment",
                "workflow_management",
                "resource_allocation"
            ],
            config=config
        )
        
        # 已注册的Agent
        self._registered_agents: Dict[str, Dict[str, Any]] = {}
        # 冲突记录
        self._conflicts: Dict[str, ConflictReport] = {}
        # 任务分配记录
        self._assignments: Dict[str, AgentAssignment] = {}
        # 冲突解决策略映射
        self._resolution_strategies: Dict[ConflictType, ConflictResolutionStrategy] = {
            ConflictType.RESOURCE_CONFLICT: ConflictResolutionStrategy.PRIORITY_BASED,
            ConflictType.TASK_CONFLICT: ConflictResolutionStrategy.DIRECTOR_DECISION,
            ConflictType.PRIORITY_CONFLICT: ConflictResolutionStrategy.DIRECTOR_DECISION,
            ConflictType.DATA_CONFLICT: ConflictResolutionStrategy.TIMESTAMP_BASED,
            ConflictType.WORKFLOW_CONFLICT: ConflictResolutionStrategy.DIRECTOR_DECISION,
        }
        # Agent优先级（用于冲突解决）
        self._agent_priorities: Dict[str, int] = {}
        
        logger.info("导演Agent创建完成")

    
    # ========================================================================
    # 生命周期钩子
    # ========================================================================
    
    async def _on_initialize(self):
        """初始化钩子"""
        # 注册冲突处理器
        self.register_message_handler(
            ProtocolMessageType.CONFLICT_REPORT,
            self._handle_conflict_report
        )
        # 注册Agent注册处理器
        self.register_message_handler(
            ProtocolMessageType.AGENT_REGISTER,
            self._handle_agent_register
        )
        # 注册任务完成处理器
        self.register_message_handler(
            ProtocolMessageType.TASK_COMPLETE,
            self._handle_task_complete
        )
        logger.info("导演Agent初始化完成")
    
    async def _on_start(self):
        """启动钩子"""
        # 订阅所有Agent的状态更新
        await self._message_bus.subscribe(
            self._agent_id,
            "agent.status",
            self._handle_agent_status_update
        )
        logger.info("导演Agent已启动，开始监听Agent状态")
    
    async def _on_stop(self):
        """停止钩子"""
        logger.info("导演Agent正在停止")
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        self._log_operation(
            "message_received",
            details={"message_id": message.id, "source": message.source}
        )
        return None
    
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        
        # 根据消息类型分发处理
        if msg_type == ProtocolMessageType.CONFLICT_REPORT:
            return await self._handle_conflict_report(message)
        elif msg_type == ProtocolMessageType.AGENT_REGISTER:
            return await self._handle_agent_register(message)
        elif msg_type == ProtocolMessageType.TASK_COMPLETE:
            return await self._handle_task_complete(message)
        elif msg_type == ProtocolMessageType.DATA_REQUEST:
            return await self._handle_data_request(message)
        
        return None

    
    # ========================================================================
    # 冲突解决 - 需求 1.3
    # ========================================================================
    
    async def _handle_conflict_report(self, message: ProtocolMessage) -> ProtocolMessage:
        """
        处理冲突报告
        
        需求: 1.3 - WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突
        """
        data = message.payload.data
        
        # 解析冲突类型
        try:
            conflict_type = ConflictType(data.get("conflict_type", "task_conflict"))
        except ValueError:
            conflict_type = ConflictType.TASK_CONFLICT
        
        # 创建冲突报告
        conflict = ConflictReport(
            conflict_id=message.header.message_id,
            conflict_type=conflict_type,
            reporter_agent=data.get("reporter", message.header.source_agent),
            involved_agents=data.get("involved_agents", []),
            details=data.get("details", {})
        )
        
        # 记录冲突
        self._conflicts[conflict.conflict_id] = conflict
        
        self._log_operation(
            "conflict_received",
            details={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict_type.value,
                "involved_agents": conflict.involved_agents
            }
        )
        
        # 解决冲突
        resolution = await self.resolve_conflict(conflict)
        
        # 返回解决方案
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data=resolution
        )
    
    async def resolve_conflict(self, conflict: ConflictReport) -> Dict[str, Any]:
        """
        解决冲突
        
        需求: 1.3 - 导演Agent作为最终决策者解决冲突
        
        Args:
            conflict: 冲突报告
            
        Returns:
            解决方案
        """
        # 确保冲突被记录
        if conflict.conflict_id not in self._conflicts:
            self._conflicts[conflict.conflict_id] = conflict
        
        # 获取解决策略
        strategy = self._resolution_strategies.get(
            conflict.conflict_type,
            ConflictResolutionStrategy.DIRECTOR_DECISION
        )
        
        resolution = {}
        
        if strategy == ConflictResolutionStrategy.PRIORITY_BASED:
            resolution = await self._resolve_by_priority(conflict)
        elif strategy == ConflictResolutionStrategy.TIMESTAMP_BASED:
            resolution = await self._resolve_by_timestamp(conflict)
        elif strategy == ConflictResolutionStrategy.VOTING:
            resolution = await self._resolve_by_voting(conflict)
        elif strategy == ConflictResolutionStrategy.MERGE:
            resolution = await self._resolve_by_merge(conflict)
        else:
            # 默认：导演直接决定
            resolution = await self._resolve_by_director_decision(conflict)
        
        # 更新冲突记录
        conflict.resolved = True
        conflict.resolution = resolution
        conflict.resolution_strategy = strategy
        
        self._log_operation(
            "conflict_resolved",
            details={
                "conflict_id": conflict.conflict_id,
                "strategy": strategy.value,
                "resolution": resolution
            }
        )
        
        # 通知相关Agent
        await self._notify_conflict_resolution(conflict)
        
        return resolution

    
    async def _resolve_by_priority(self, conflict: ConflictReport) -> Dict[str, Any]:
        """基于优先级解决冲突"""
        involved = conflict.involved_agents
        if not involved:
            return {"winner": None, "reason": "no_agents_involved"}
        
        # 获取各Agent的优先级
        priorities = {
            agent: self._agent_priorities.get(agent, 0)
            for agent in involved
        }
        
        # 选择优先级最高的Agent
        winner = max(priorities, key=priorities.get)
        
        return {
            "winner": winner,
            "reason": "highest_priority",
            "priorities": priorities
        }
    
    async def _resolve_by_timestamp(self, conflict: ConflictReport) -> Dict[str, Any]:
        """基于时间戳解决冲突（先到先得）"""
        details = conflict.details
        timestamps = details.get("timestamps", {})
        
        if not timestamps:
            # 如果没有时间戳信息，使用报告者
            return {
                "winner": conflict.reporter_agent,
                "reason": "reporter_default"
            }
        
        # 选择最早的时间戳
        winner = min(timestamps, key=timestamps.get)
        
        return {
            "winner": winner,
            "reason": "earliest_timestamp",
            "timestamps": timestamps
        }
    
    async def _resolve_by_voting(self, conflict: ConflictReport) -> Dict[str, Any]:
        """通过投票解决冲突"""
        # 简化实现：导演投票权重最高
        return {
            "winner": conflict.reporter_agent,
            "reason": "director_vote",
            "votes": {self._agent_id: conflict.reporter_agent}
        }
    
    async def _resolve_by_merge(self, conflict: ConflictReport) -> Dict[str, Any]:
        """通过合并解决冲突"""
        details = conflict.details
        
        return {
            "action": "merge",
            "merged_data": details.get("merge_suggestion", {}),
            "reason": "data_merged"
        }
    
    async def _resolve_by_director_decision(self, conflict: ConflictReport) -> Dict[str, Any]:
        """
        导演直接决定
        
        需求: 1.3 - 导演Agent作为最终决策者
        """
        involved = conflict.involved_agents
        details = conflict.details
        
        # 导演基于上下文做出决定
        decision = {
            "action": "director_decision",
            "winner": involved[0] if involved else None,
            "reason": "director_authority",
            "instructions": details.get("suggested_resolution", "proceed_with_first_agent")
        }
        
        return decision
    
    async def _notify_conflict_resolution(self, conflict: ConflictReport):
        """通知相关Agent冲突解决结果"""
        if not self._protocol or not self._protocol.is_running:
            return
        
        for agent_id in conflict.involved_agents:
            await self.send_message(
                agent_id,
                ProtocolMessageType.CONFLICT_RESOLVE,
                conflict.to_dict()
            )

    
    # ========================================================================
    # Agent调配 - 需求 2.5
    # ========================================================================
    
    async def coordinate_agents(
        self,
        project_id: str,
        agent_types: List[AgentType],
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调配Agent开始协作
        
        需求: 2.5 - WHEN 人工审核通过后 THEN 导演Agent SHALL 调配所有工作台开始协作
        
        Args:
            project_id: 项目ID
            agent_types: 需要调配的Agent类型列表
            task_data: 任务数据
            
        Returns:
            调配结果
        """
        await self.update_work_state(AgentState.WORKING, f"coordinating_project_{project_id}")
        
        results = {
            "project_id": project_id,
            "assignments": [],
            "success": True,
            "errors": []
        }
        
        for agent_type in agent_types:
            # 查找该类型的可用Agent
            available_agents = self._get_available_agents_by_type(agent_type)
            
            if not available_agents:
                results["errors"].append(f"No available agent of type {agent_type.value}")
                continue
            
            # 选择第一个可用的Agent
            target_agent = available_agents[0]
            
            # 分配任务
            assignment = await self.assign_task(
                target_agent_id=target_agent,
                task_id=f"{project_id}_{agent_type.value}",
                task_type=f"project_collaboration",
                task_data={
                    "project_id": project_id,
                    "role": agent_type.value,
                    **task_data
                }
            )
            
            if assignment:
                results["assignments"].append(assignment.to_dict())
            else:
                results["errors"].append(f"Failed to assign task to {target_agent}")
        
        if results["errors"]:
            results["success"] = len(results["assignments"]) > 0
        
        await self.update_work_state(AgentState.IDLE)
        
        self._log_operation(
            "agents_coordinated",
            details={
                "project_id": project_id,
                "agent_count": len(results["assignments"]),
                "errors": results["errors"]
            }
        )
        
        return results
    
    async def assign_task(
        self,
        target_agent_id: str,
        task_id: str,
        task_type: str,
        task_data: Dict[str, Any]
    ) -> Optional[AgentAssignment]:
        """
        分配任务给指定Agent
        
        Args:
            target_agent_id: 目标Agent ID
            task_id: 任务ID
            task_type: 任务类型
            task_data: 任务数据
            
        Returns:
            任务分配记录
        """
        # 获取Agent信息
        agent_info = self._registered_agents.get(target_agent_id)
        if not agent_info:
            logger.warning(f"Agent未注册: {target_agent_id}")
            return None
        
        # 创建分配记录
        try:
            agent_type = AgentType(agent_info.get("agent_type", "system"))
        except ValueError:
            agent_type = AgentType.SYSTEM
        
        assignment = AgentAssignment(
            agent_id=target_agent_id,
            agent_type=agent_type,
            task_id=task_id,
            task_type=task_type,
            task_data=task_data
        )
        
        # 发送任务分配消息
        success = await self.send_message(
            target_agent_id,
            ProtocolMessageType.TASK_ASSIGN,
            {
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data
            }
        )
        
        if success:
            self._assignments[task_id] = assignment
            self._log_operation(
                "task_assigned",
                details={
                    "target_agent": target_agent_id,
                    "task_id": task_id,
                    "task_type": task_type
                }
            )
            return assignment
        
        return None

    
    # ========================================================================
    # Agent注册和管理
    # ========================================================================
    
    async def _handle_agent_register(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理Agent注册请求"""
        data = message.payload.data
        agent_id = data.get("agent_id", message.header.source_agent)
        
        self._registered_agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": data.get("agent_type"),
            "capabilities": data.get("capabilities", []),
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # 设置默认优先级
        self._agent_priorities[agent_id] = data.get("priority", 1)
        
        self._log_operation(
            "agent_registered",
            details={"agent_id": agent_id, "agent_type": data.get("agent_type")}
        )
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data={"registered": True, "agent_id": agent_id}
        )
    
    async def _handle_task_complete(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理任务完成通知"""
        data = message.payload.data
        task_id = data.get("task_id")
        
        if task_id in self._assignments:
            self._assignments[task_id].status = "completed"
            
            self._log_operation(
                "task_completed",
                details={
                    "task_id": task_id,
                    "agent_id": message.header.source_agent,
                    "result": data.get("result")
                }
            )
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data={"acknowledged": True}
        )
    
    async def _handle_data_request(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理数据请求"""
        data = message.payload.data
        request_type = data.get("request_type")
        
        response_data = {}
        
        if request_type == "registered_agents":
            response_data = {"agents": list(self._registered_agents.values())}
        elif request_type == "conflicts":
            response_data = {"conflicts": [c.to_dict() for c in self._conflicts.values()]}
        elif request_type == "assignments":
            response_data = {"assignments": [a.to_dict() for a in self._assignments.values()]}
        elif request_type == "status":
            response_data = self.get_director_status()
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data=response_data
        )
    
    async def _handle_agent_status_update(self, message: Message):
        """处理Agent状态更新"""
        content = message.content
        agent_id = content.get("agent_id")
        
        if agent_id and agent_id in self._registered_agents:
            self._registered_agents[agent_id]["status"] = content.get("new_state", "unknown")
            self._registered_agents[agent_id]["last_update"] = datetime.utcnow().isoformat()
    
    def _get_available_agents_by_type(self, agent_type: AgentType) -> List[str]:
        """获取指定类型的可用Agent列表"""
        available = []
        for agent_id, info in self._registered_agents.items():
            if (info.get("agent_type") == agent_type.value and 
                info.get("status") in ["active", "idle"]):
                available.append(agent_id)
        return available

    
    # ========================================================================
    # 状态查询
    # ========================================================================
    
    def get_director_status(self) -> Dict[str, Any]:
        """获取导演Agent状态"""
        return {
            **self.get_status(),
            "registered_agents_count": len(self._registered_agents),
            "active_conflicts": len([c for c in self._conflicts.values() if not c.resolved]),
            "resolved_conflicts": len([c for c in self._conflicts.values() if c.resolved]),
            "pending_assignments": len([a for a in self._assignments.values() if a.status == "pending"]),
            "completed_assignments": len([a for a in self._assignments.values() if a.status == "completed"])
        }
    
    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取已注册的Agent列表"""
        return self._registered_agents.copy()
    
    def get_conflicts(self, resolved: Optional[bool] = None) -> List[ConflictReport]:
        """获取冲突列表"""
        conflicts = list(self._conflicts.values())
        if resolved is not None:
            conflicts = [c for c in conflicts if c.resolved == resolved]
        return conflicts
    
    def get_assignments(self, status: Optional[str] = None) -> List[AgentAssignment]:
        """获取任务分配列表"""
        assignments = list(self._assignments.values())
        if status:
            assignments = [a for a in assignments if a.status == status]
        return assignments
    
    def set_agent_priority(self, agent_id: str, priority: int):
        """设置Agent优先级"""
        self._agent_priorities[agent_id] = priority
    
    def get_agent_priority(self, agent_id: str) -> int:
        """获取Agent优先级"""
        return self._agent_priorities.get(agent_id, 0)
    
    def set_resolution_strategy(
        self,
        conflict_type: ConflictType,
        strategy: ConflictResolutionStrategy
    ):
        """设置冲突解决策略"""
        self._resolution_strategies[conflict_type] = strategy
