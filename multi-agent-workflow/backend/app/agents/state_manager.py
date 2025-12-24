"""
Agent状态管理器 - 状态持久化和恢复

需求: 1.4 - WHEN Agent执行任务时 THEN 系统 SHALL 记录所有Agent的状态和操作日志
需求: 1.5 - WHEN 用户查询系统状态时 THEN 系统Agent SHALL 提供实时的Agent状态信息

本模块实现了Agent状态的集中管理，包括:
- 状态持久化到存储
- 状态恢复
- 状态查询
- 状态变更通知
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from pathlib import Path
import aiofiles
import os

from ..core.agent_types import AgentState, AgentType
from .base_agent import AgentLifecycleState, AgentOperationLog

logger = logging.getLogger(__name__)


@dataclass
class AgentStateSnapshot:
    """Agent状态快照"""
    agent_id: str
    agent_type: str
    lifecycle_state: str
    work_state: str
    current_task: Optional[str]
    last_activity: str
    capabilities: List[str]
    config: Dict[str, Any]
    operation_logs: List[Dict[str, Any]]
    snapshot_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStateSnapshot":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentStateSnapshot":
        return cls.from_dict(json.loads(json_str))


@dataclass
class SystemStateSnapshot:
    """系统状态快照"""
    agents: Dict[str, AgentStateSnapshot]
    snapshot_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "snapshot_time": self.snapshot_time,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemStateSnapshot":
        agents = {
            k: AgentStateSnapshot.from_dict(v) 
            for k, v in data.get("agents", {}).items()
        }
        return cls(
            agents=agents,
            snapshot_time=data.get("snapshot_time", datetime.utcnow().isoformat()),
            version=data.get("version", "1.0")
        )


class AgentStateManager:
    """
    Agent状态管理器
    
    提供Agent状态的集中管理功能:
    - 注册和注销Agent
    - 状态更新和查询
    - 状态持久化和恢复
    - 状态变更通知
    
    需求: 1.4 - 记录所有Agent的状态和操作日志
    需求: 1.5 - 提供实时的Agent状态信息
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_persist: bool = True,
        persist_interval: float = 30.0
    ):
        """
        初始化状态管理器
        
        Args:
            storage_path: 状态存储路径
            auto_persist: 是否自动持久化
            persist_interval: 自动持久化间隔(秒)
        """
        self._storage_path = storage_path or "./data/agent_states"
        self._auto_persist = auto_persist
        self._persist_interval = persist_interval
        
        # Agent状态存储
        self._agent_states: Dict[str, AgentStateSnapshot] = {}
        # 状态变更监听器
        self._state_listeners: List[Callable[[str, AgentStateSnapshot], None]] = []
        # 锁
        self._lock = asyncio.Lock()
        # 自动持久化任务
        self._persist_task: Optional[asyncio.Task] = None
        # 运行状态
        self._running = False
        
        # 确保存储目录存在
        Path(self._storage_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Agent状态管理器初始化: storage_path={self._storage_path}")
    
    async def start(self):
        """启动状态管理器"""
        if self._running:
            return
        
        self._running = True
        
        # 尝试恢复之前的状态
        await self._load_persisted_states()
        
        # 启动自动持久化任务
        if self._auto_persist:
            self._persist_task = asyncio.create_task(self._auto_persist_loop())
        
        logger.info("Agent状态管理器已启动")
    
    async def stop(self):
        """停止状态管理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消自动持久化任务
        if self._persist_task:
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelledError:
                pass
        
        # 最终持久化
        await self.persist_all()
        
        logger.info("Agent状态管理器已停止")
    
    async def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册Agent
        
        Args:
            agent_id: Agent ID
            agent_type: Agent类型
            capabilities: 能力列表
            config: 配置
            
        Returns:
            是否注册成功
        """
        async with self._lock:
            if agent_id in self._agent_states:
                logger.warning(f"Agent已存在: {agent_id}")
                return False
            
            snapshot = AgentStateSnapshot(
                agent_id=agent_id,
                agent_type=agent_type.value,
                lifecycle_state=AgentLifecycleState.CREATED.value,
                work_state=AgentState.OFFLINE.value,
                current_task=None,
                last_activity=datetime.utcnow().isoformat(),
                capabilities=capabilities or [],
                config=config or {},
                operation_logs=[]
            )
            
            self._agent_states[agent_id] = snapshot
        
        # 通知监听器
        await self._notify_listeners(agent_id, snapshot)
        
        logger.info(f"Agent已注册: {agent_id} (类型: {agent_type.value})")
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否注销成功
        """
        async with self._lock:
            if agent_id not in self._agent_states:
                logger.warning(f"Agent不存在: {agent_id}")
                return False
            
            del self._agent_states[agent_id]
        
        logger.info(f"Agent已注销: {agent_id}")
        return True
    
    async def update_state(
        self,
        agent_id: str,
        lifecycle_state: Optional[AgentLifecycleState] = None,
        work_state: Optional[AgentState] = None,
        current_task: Optional[str] = None,
        operation_log: Optional[AgentOperationLog] = None
    ) -> bool:
        """
        更新Agent状态
        
        Args:
            agent_id: Agent ID
            lifecycle_state: 生命周期状态
            work_state: 工作状态
            current_task: 当前任务
            operation_log: 操作日志
            
        Returns:
            是否更新成功
        """
        async with self._lock:
            if agent_id not in self._agent_states:
                logger.warning(f"Agent不存在: {agent_id}")
                return False
            
            snapshot = self._agent_states[agent_id]
            
            if lifecycle_state is not None:
                snapshot.lifecycle_state = lifecycle_state.value
            
            if work_state is not None:
                snapshot.work_state = work_state.value
            
            if current_task is not None:
                snapshot.current_task = current_task
            
            snapshot.last_activity = datetime.utcnow().isoformat()
            
            if operation_log is not None:
                snapshot.operation_logs.append(operation_log.to_dict())
                # 限制日志数量
                if len(snapshot.operation_logs) > 100:
                    snapshot.operation_logs = snapshot.operation_logs[-100:]
            
            snapshot.snapshot_time = datetime.utcnow().isoformat()
        
        # 通知监听器
        await self._notify_listeners(agent_id, snapshot)
        
        logger.debug(f"Agent状态已更新: {agent_id}")
        return True
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateSnapshot]:
        """
        获取Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent状态快照
        """
        async with self._lock:
            return self._agent_states.get(agent_id)
    
    async def get_all_states(self) -> Dict[str, AgentStateSnapshot]:
        """
        获取所有Agent状态
        
        Returns:
            所有Agent状态的字典
        """
        async with self._lock:
            return self._agent_states.copy()
    
    async def get_agents_by_type(self, agent_type: AgentType) -> List[AgentStateSnapshot]:
        """
        按类型获取Agent状态
        
        Args:
            agent_type: Agent类型
            
        Returns:
            该类型的所有Agent状态列表
        """
        async with self._lock:
            return [
                s for s in self._agent_states.values()
                if s.agent_type == agent_type.value
            ]
    
    async def get_agents_by_state(self, work_state: AgentState) -> List[AgentStateSnapshot]:
        """
        按工作状态获取Agent
        
        Args:
            work_state: 工作状态
            
        Returns:
            该状态的所有Agent状态列表
        """
        async with self._lock:
            return [
                s for s in self._agent_states.values()
                if s.work_state == work_state.value
            ]
    
    def add_state_listener(self, listener: Callable[[str, AgentStateSnapshot], None]):
        """
        添加状态变更监听器
        
        Args:
            listener: 监听器函数
        """
        self._state_listeners.append(listener)
    
    def remove_state_listener(self, listener: Callable[[str, AgentStateSnapshot], None]):
        """
        移除状态变更监听器
        
        Args:
            listener: 监听器函数
        """
        if listener in self._state_listeners:
            self._state_listeners.remove(listener)
    
    async def _notify_listeners(self, agent_id: str, snapshot: AgentStateSnapshot):
        """通知所有监听器"""
        for listener in self._state_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(agent_id, snapshot)
                else:
                    listener(agent_id, snapshot)
            except Exception as e:
                logger.error(f"状态监听器错误: {e}")
    
    # ========================================================================
    # 持久化功能
    # ========================================================================
    
    async def persist_all(self) -> bool:
        """
        持久化所有Agent状态
        
        Returns:
            是否持久化成功
        """
        try:
            async with self._lock:
                system_snapshot = SystemStateSnapshot(
                    agents=self._agent_states.copy()
                )
            
            file_path = Path(self._storage_path) / "system_state.json"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(system_snapshot.to_dict(), ensure_ascii=False, indent=2))
            
            logger.debug(f"系统状态已持久化: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"状态持久化失败: {e}")
            return False
    
    async def persist_agent(self, agent_id: str) -> bool:
        """
        持久化单个Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否持久化成功
        """
        try:
            async with self._lock:
                snapshot = self._agent_states.get(agent_id)
                if not snapshot:
                    return False
            
            file_path = Path(self._storage_path) / f"agent_{agent_id}.json"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(snapshot.to_json())
            
            logger.debug(f"Agent状态已持久化: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Agent状态持久化失败: {agent_id}, 错误: {e}")
            return False
    
    async def _load_persisted_states(self):
        """加载持久化的状态"""
        try:
            file_path = Path(self._storage_path) / "system_state.json"
            
            if not file_path.exists():
                logger.info("没有找到持久化的系统状态")
                return
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            data = json.loads(content)
            system_snapshot = SystemStateSnapshot.from_dict(data)
            
            async with self._lock:
                self._agent_states = system_snapshot.agents
            
            logger.info(f"已恢复 {len(self._agent_states)} 个Agent的状态")
            
        except Exception as e:
            logger.error(f"加载持久化状态失败: {e}")
    
    async def restore_agent(self, agent_id: str) -> Optional[AgentStateSnapshot]:
        """
        恢复单个Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            恢复的状态快照
        """
        try:
            file_path = Path(self._storage_path) / f"agent_{agent_id}.json"
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            snapshot = AgentStateSnapshot.from_json(content)
            
            async with self._lock:
                self._agent_states[agent_id] = snapshot
            
            logger.info(f"Agent状态已恢复: {agent_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"恢复Agent状态失败: {agent_id}, 错误: {e}")
            return None
    
    async def _auto_persist_loop(self):
        """自动持久化循环"""
        while self._running:
            try:
                await asyncio.sleep(self._persist_interval)
                if self._running:
                    await self.persist_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动持久化错误: {e}")
    
    # ========================================================================
    # 统计和查询
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        states_count = {}
        types_count = {}
        
        for snapshot in self._agent_states.values():
            # 按状态统计
            state = snapshot.work_state
            states_count[state] = states_count.get(state, 0) + 1
            
            # 按类型统计
            agent_type = snapshot.agent_type
            types_count[agent_type] = types_count.get(agent_type, 0) + 1
        
        return {
            "total_agents": len(self._agent_states),
            "by_state": states_count,
            "by_type": types_count,
            "running": self._running,
            "auto_persist": self._auto_persist,
            "storage_path": self._storage_path
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态摘要
        
        需求: 1.5 - 提供实时的Agent状态信息
        
        Returns:
            系统状态摘要
        """
        agents_summary = []
        
        for agent_id, snapshot in self._agent_states.items():
            agents_summary.append({
                "agent_id": agent_id,
                "agent_type": snapshot.agent_type,
                "lifecycle_state": snapshot.lifecycle_state,
                "work_state": snapshot.work_state,
                "current_task": snapshot.current_task,
                "last_activity": snapshot.last_activity
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(self._agent_states),
            "agents": agents_summary,
            "stats": self.get_stats()
        }
    
    @property
    def is_running(self) -> bool:
        return self._running


# 全局状态管理器实例
state_manager = AgentStateManager()
