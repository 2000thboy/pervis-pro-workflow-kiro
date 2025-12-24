"""
Agent状态管理器单元测试

需求: 1.4 - WHEN Agent执行任务时 THEN 系统 SHALL 记录所有Agent的状态和操作日志
需求: 1.5 - WHEN 用户查询系统状态时 THEN 系统Agent SHALL 提供实时的Agent状态信息

测试内容:
- 状态转换逻辑
- 状态持久化功能
"""
import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.state_manager import (
    AgentStateManager,
    AgentStateSnapshot,
    SystemStateSnapshot,
)
from app.agents.base_agent import AgentLifecycleState, AgentOperationLog
from app.core.agent_types import AgentState, AgentType


class TestAgentStateSnapshot:
    """AgentStateSnapshot数据类测试"""
    
    def test_snapshot_creation(self):
        """测试快照创建"""
        snapshot = AgentStateSnapshot(
            agent_id="test-agent-1",
            agent_type=AgentType.DIRECTOR.value,
            lifecycle_state=AgentLifecycleState.READY.value,
            work_state=AgentState.IDLE.value,
            current_task=None,
            last_activity=datetime.utcnow().isoformat(),
            capabilities=["task_management", "conflict_resolution"],
            config={"priority": "high"},
            operation_logs=[]
        )
        
        assert snapshot.agent_id == "test-agent-1"
        assert snapshot.agent_type == AgentType.DIRECTOR.value
        assert snapshot.lifecycle_state == AgentLifecycleState.READY.value
        assert snapshot.work_state == AgentState.IDLE.value
        assert snapshot.current_task is None
        assert "task_management" in snapshot.capabilities
    
    def test_snapshot_to_dict(self):
        """测试快照转换为字典"""
        snapshot = AgentStateSnapshot(
            agent_id="test-agent-1",
            agent_type=AgentType.SYSTEM.value,
            lifecycle_state=AgentLifecycleState.RUNNING.value,
            work_state=AgentState.WORKING.value,
            current_task="processing_request",
            last_activity="2024-01-01T00:00:00",
            capabilities=["search", "query"],
            config={},
            operation_logs=[]
        )
        
        data = snapshot.to_dict()
        
        assert isinstance(data, dict)
        assert data["agent_id"] == "test-agent-1"
        assert data["agent_type"] == AgentType.SYSTEM.value
        assert data["work_state"] == AgentState.WORKING.value
        assert data["current_task"] == "processing_request"
    
    def test_snapshot_from_dict(self):
        """测试从字典创建快照"""
        data = {
            "agent_id": "test-agent-2",
            "agent_type": AgentType.DAM.value,
            "lifecycle_state": AgentLifecycleState.READY.value,
            "work_state": AgentState.IDLE.value,
            "current_task": None,
            "last_activity": "2024-01-01T00:00:00",
            "capabilities": ["asset_management"],
            "config": {"storage_path": "/data"},
            "operation_logs": [],
            "snapshot_time": "2024-01-01T00:00:00"
        }
        
        snapshot = AgentStateSnapshot.from_dict(data)
        
        assert snapshot.agent_id == "test-agent-2"
        assert snapshot.agent_type == AgentType.DAM.value
        assert snapshot.config["storage_path"] == "/data"
    
    def test_snapshot_json_roundtrip(self):
        """测试JSON序列化往返"""
        original = AgentStateSnapshot(
            agent_id="test-agent-3",
            agent_type=AgentType.PM.value,
            lifecycle_state=AgentLifecycleState.RUNNING.value,
            work_state=AgentState.WORKING.value,
            current_task="archiving",
            last_activity="2024-01-01T00:00:00",
            capabilities=["project_management"],
            config={"archive_path": "/archive"},
            operation_logs=[{"operation": "test", "success": True}]
        )
        
        json_str = original.to_json()
        restored = AgentStateSnapshot.from_json(json_str)
        
        assert restored.agent_id == original.agent_id
        assert restored.agent_type == original.agent_type
        assert restored.work_state == original.work_state
        assert restored.current_task == original.current_task
        assert len(restored.operation_logs) == 1


class TestSystemStateSnapshot:
    """SystemStateSnapshot数据类测试"""
    
    def test_system_snapshot_creation(self):
        """测试系统快照创建"""
        agent_snapshot = AgentStateSnapshot(
            agent_id="agent-1",
            agent_type=AgentType.DIRECTOR.value,
            lifecycle_state=AgentLifecycleState.READY.value,
            work_state=AgentState.IDLE.value,
            current_task=None,
            last_activity="2024-01-01T00:00:00",
            capabilities=[],
            config={},
            operation_logs=[]
        )
        
        system_snapshot = SystemStateSnapshot(
            agents={"agent-1": agent_snapshot}
        )
        
        assert len(system_snapshot.agents) == 1
        assert "agent-1" in system_snapshot.agents
        assert system_snapshot.version == "1.0"
    
    def test_system_snapshot_to_dict(self):
        """测试系统快照转换为字典"""
        agent_snapshot = AgentStateSnapshot(
            agent_id="agent-1",
            agent_type=AgentType.SYSTEM.value,
            lifecycle_state=AgentLifecycleState.RUNNING.value,
            work_state=AgentState.IDLE.value,
            current_task=None,
            last_activity="2024-01-01T00:00:00",
            capabilities=[],
            config={},
            operation_logs=[]
        )
        
        system_snapshot = SystemStateSnapshot(
            agents={"agent-1": agent_snapshot}
        )
        
        data = system_snapshot.to_dict()
        
        assert "agents" in data
        assert "snapshot_time" in data
        assert "version" in data
        assert "agent-1" in data["agents"]
    
    def test_system_snapshot_from_dict(self):
        """测试从字典创建系统快照"""
        data = {
            "agents": {
                "agent-1": {
                    "agent_id": "agent-1",
                    "agent_type": AgentType.BACKEND.value,
                    "lifecycle_state": AgentLifecycleState.READY.value,
                    "work_state": AgentState.IDLE.value,
                    "current_task": None,
                    "last_activity": "2024-01-01T00:00:00",
                    "capabilities": [],
                    "config": {},
                    "operation_logs": [],
                    "snapshot_time": "2024-01-01T00:00:00"
                }
            },
            "snapshot_time": "2024-01-01T00:00:00",
            "version": "1.0"
        }
        
        system_snapshot = SystemStateSnapshot.from_dict(data)
        
        assert len(system_snapshot.agents) == 1
        assert system_snapshot.agents["agent-1"].agent_type == AgentType.BACKEND.value


@pytest.mark.asyncio
class TestAgentStateManager:
    """AgentStateManager测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def state_manager_factory(self, temp_storage_path):
        """创建状态管理器工厂"""
        managers = []
        
        async def create_manager():
            manager = AgentStateManager(
                storage_path=temp_storage_path,
                auto_persist=False
            )
            await manager.start()
            managers.append(manager)
            return manager
        
        yield create_manager
        
        # 清理
        async def cleanup():
            for m in managers:
                if m.is_running:
                    await m.stop()
        
        asyncio.get_event_loop().run_until_complete(cleanup())
    
    async def test_manager_initialization(self, temp_storage_path):
        """测试状态管理器初始化"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        
        assert not manager.is_running
        assert manager._storage_path == temp_storage_path
        
        await manager.start()
        assert manager.is_running
        
        await manager.stop()
        assert not manager.is_running
    
    async def test_register_agent(self, state_manager_factory):
        """测试Agent注册"""
        state_manager = await state_manager_factory()
        
        result = await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.DIRECTOR,
            capabilities=["task_management"],
            config={"priority": "high"}
        )
        
        assert result is True
        
        # 验证Agent已注册
        snapshot = await state_manager.get_agent_state("test-agent-1")
        assert snapshot is not None
        assert snapshot.agent_id == "test-agent-1"
        assert snapshot.agent_type == AgentType.DIRECTOR.value
        assert "task_management" in snapshot.capabilities
    
    async def test_register_duplicate_agent(self, state_manager_factory):
        """测试重复注册Agent"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.DIRECTOR
        )
        
        # 尝试重复注册
        result = await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.SYSTEM
        )
        
        assert result is False
    
    async def test_unregister_agent(self, state_manager_factory):
        """测试Agent注销"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.DIRECTOR
        )
        
        result = await state_manager.unregister_agent("test-agent-1")
        assert result is True
        
        # 验证Agent已注销
        snapshot = await state_manager.get_agent_state("test-agent-1")
        assert snapshot is None
    
    async def test_unregister_nonexistent_agent(self, state_manager_factory):
        """测试注销不存在的Agent"""
        state_manager = await state_manager_factory()
        
        result = await state_manager.unregister_agent("nonexistent-agent")
        assert result is False
    
    async def test_update_state(self, state_manager_factory):
        """测试状态更新"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.DIRECTOR
        )
        
        # 更新生命周期状态
        result = await state_manager.update_state(
            agent_id="test-agent-1",
            lifecycle_state=AgentLifecycleState.RUNNING
        )
        assert result is True
        
        snapshot = await state_manager.get_agent_state("test-agent-1")
        assert snapshot.lifecycle_state == AgentLifecycleState.RUNNING.value
    
    async def test_update_work_state(self, state_manager_factory):
        """测试工作状态更新"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.SYSTEM
        )
        
        result = await state_manager.update_state(
            agent_id="test-agent-1",
            work_state=AgentState.WORKING,
            current_task="processing_query"
        )
        assert result is True
        
        snapshot = await state_manager.get_agent_state("test-agent-1")
        assert snapshot.work_state == AgentState.WORKING.value
        assert snapshot.current_task == "processing_query"
    
    async def test_update_state_with_operation_log(self, state_manager_factory):
        """测试带操作日志的状态更新"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent(
            agent_id="test-agent-1",
            agent_type=AgentType.DAM
        )
        
        operation_log = AgentOperationLog(
            operation="asset_indexed",
            state_before=AgentState.IDLE.value,
            state_after=AgentState.WORKING.value,
            details={"asset_count": 100},
            success=True
        )
        
        result = await state_manager.update_state(
            agent_id="test-agent-1",
            work_state=AgentState.WORKING,
            operation_log=operation_log
        )
        assert result is True
        
        snapshot = await state_manager.get_agent_state("test-agent-1")
        assert len(snapshot.operation_logs) == 1
        assert snapshot.operation_logs[0]["operation"] == "asset_indexed"
    
    async def test_update_nonexistent_agent(self, state_manager_factory):
        """测试更新不存在的Agent状态"""
        state_manager = await state_manager_factory()
        
        result = await state_manager.update_state(
            agent_id="nonexistent-agent",
            work_state=AgentState.WORKING
        )
        assert result is False
    
    async def test_get_all_states(self, state_manager_factory):
        """测试获取所有Agent状态"""
        state_manager = await state_manager_factory()
        
        # 注册多个Agent
        await state_manager.register_agent("agent-1", AgentType.DIRECTOR)
        await state_manager.register_agent("agent-2", AgentType.SYSTEM)
        await state_manager.register_agent("agent-3", AgentType.DAM)
        
        all_states = await state_manager.get_all_states()
        
        assert len(all_states) == 3
        assert "agent-1" in all_states
        assert "agent-2" in all_states
        assert "agent-3" in all_states
    
    async def test_get_agents_by_type(self, state_manager_factory):
        """测试按类型获取Agent"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent("director-1", AgentType.DIRECTOR)
        await state_manager.register_agent("system-1", AgentType.SYSTEM)
        await state_manager.register_agent("system-2", AgentType.SYSTEM)
        
        system_agents = await state_manager.get_agents_by_type(AgentType.SYSTEM)
        
        assert len(system_agents) == 2
        for agent in system_agents:
            assert agent.agent_type == AgentType.SYSTEM.value
    
    async def test_get_agents_by_state(self, state_manager_factory):
        """测试按工作状态获取Agent"""
        state_manager = await state_manager_factory()
        
        await state_manager.register_agent("agent-1", AgentType.DIRECTOR)
        await state_manager.register_agent("agent-2", AgentType.SYSTEM)
        
        # 更新一个Agent为WORKING状态
        await state_manager.update_state("agent-1", work_state=AgentState.WORKING)
        
        working_agents = await state_manager.get_agents_by_state(AgentState.WORKING)
        
        assert len(working_agents) == 1
        assert working_agents[0].agent_id == "agent-1"
    
    async def test_state_listener(self, state_manager_factory):
        """测试状态变更监听器"""
        state_manager = await state_manager_factory()
        
        received_updates = []
        
        def listener(agent_id, snapshot):
            received_updates.append((agent_id, snapshot))
        
        state_manager.add_state_listener(listener)
        
        await state_manager.register_agent("agent-1", AgentType.DIRECTOR)
        await state_manager.update_state("agent-1", work_state=AgentState.WORKING)
        
        # 等待异步处理
        await asyncio.sleep(0.1)
        
        assert len(received_updates) >= 2  # 注册和更新各触发一次
        
        # 移除监听器
        state_manager.remove_state_listener(listener)
    
    async def test_async_state_listener(self, state_manager_factory):
        """测试异步状态变更监听器"""
        state_manager = await state_manager_factory()
        
        received_updates = []
        
        async def async_listener(agent_id, snapshot):
            received_updates.append((agent_id, snapshot))
        
        state_manager.add_state_listener(async_listener)
        
        await state_manager.register_agent("agent-1", AgentType.SYSTEM)
        
        # 等待异步处理
        await asyncio.sleep(0.1)
        
        assert len(received_updates) >= 1
        
        state_manager.remove_state_listener(async_listener)


@pytest.mark.asyncio
class TestAgentStateManagerPersistence:
    """状态管理器持久化功能测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    async def test_persist_all(self, temp_storage_path):
        """测试持久化所有状态"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        # 注册Agent
        await manager.register_agent("agent-1", AgentType.DIRECTOR)
        await manager.register_agent("agent-2", AgentType.SYSTEM)
        
        # 持久化
        result = await manager.persist_all()
        assert result is True
        
        # 验证文件存在
        file_path = Path(temp_storage_path) / "system_state.json"
        assert file_path.exists()
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "agents" in data
        assert "agent-1" in data["agents"]
        assert "agent-2" in data["agents"]
        
        await manager.stop()
    
    async def test_persist_single_agent(self, temp_storage_path):
        """测试持久化单个Agent状态"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        await manager.register_agent("agent-1", AgentType.DAM)
        
        result = await manager.persist_agent("agent-1")
        assert result is True
        
        # 验证文件存在
        file_path = Path(temp_storage_path) / "agent_agent-1.json"
        assert file_path.exists()
        
        await manager.stop()
    
    async def test_persist_nonexistent_agent(self, temp_storage_path):
        """测试持久化不存在的Agent"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        result = await manager.persist_agent("nonexistent")
        assert result is False
        
        await manager.stop()
    
    async def test_restore_states_on_start(self, temp_storage_path):
        """测试启动时恢复状态"""
        # 第一个管理器：创建并持久化状态
        manager1 = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager1.start()
        
        await manager1.register_agent("agent-1", AgentType.DIRECTOR)
        await manager1.update_state("agent-1", work_state=AgentState.WORKING)
        await manager1.persist_all()
        await manager1.stop()
        
        # 第二个管理器：应该恢复状态
        manager2 = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager2.start()
        
        snapshot = await manager2.get_agent_state("agent-1")
        assert snapshot is not None
        assert snapshot.agent_id == "agent-1"
        assert snapshot.work_state == AgentState.WORKING.value
        
        await manager2.stop()
    
    async def test_restore_single_agent(self, temp_storage_path):
        """测试恢复单个Agent状态"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        # 注册并持久化
        await manager.register_agent("agent-1", AgentType.PM)
        await manager.update_state(
            "agent-1",
            work_state=AgentState.WORKING,
            current_task="archiving"
        )
        await manager.persist_agent("agent-1")
        
        # 注销Agent
        await manager.unregister_agent("agent-1")
        
        # 恢复Agent
        snapshot = await manager.restore_agent("agent-1")
        
        assert snapshot is not None
        assert snapshot.agent_id == "agent-1"
        assert snapshot.work_state == AgentState.WORKING.value
        assert snapshot.current_task == "archiving"
        
        await manager.stop()
    
    async def test_restore_nonexistent_agent(self, temp_storage_path):
        """测试恢复不存在的Agent"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        snapshot = await manager.restore_agent("nonexistent")
        assert snapshot is None
        
        await manager.stop()


@pytest.mark.asyncio
class TestAgentStateManagerStats:
    """状态管理器统计功能测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    async def test_get_stats(self, temp_storage_path):
        """测试获取统计信息"""
        state_manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await state_manager.start()
        
        await state_manager.register_agent("director-1", AgentType.DIRECTOR)
        await state_manager.register_agent("system-1", AgentType.SYSTEM)
        await state_manager.register_agent("system-2", AgentType.SYSTEM)
        
        await state_manager.update_state("director-1", work_state=AgentState.WORKING)
        
        stats = state_manager.get_stats()
        
        assert stats["total_agents"] == 3
        assert stats["running"] is True
        assert AgentType.DIRECTOR.value in stats["by_type"]
        assert AgentType.SYSTEM.value in stats["by_type"]
        assert stats["by_type"][AgentType.SYSTEM.value] == 2
        
        await state_manager.stop()
    
    async def test_get_system_status(self, temp_storage_path):
        """测试获取系统状态摘要"""
        state_manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await state_manager.start()
        
        await state_manager.register_agent("agent-1", AgentType.DIRECTOR)
        await state_manager.register_agent("agent-2", AgentType.SYSTEM)
        
        await state_manager.update_state(
            "agent-1",
            lifecycle_state=AgentLifecycleState.RUNNING,
            work_state=AgentState.WORKING,
            current_task="coordinating"
        )
        
        status = state_manager.get_system_status()
        
        assert "timestamp" in status
        assert status["total_agents"] == 2
        assert len(status["agents"]) == 2
        
        # 验证Agent摘要信息
        agent_1_summary = next(
            (a for a in status["agents"] if a["agent_id"] == "agent-1"),
            None
        )
        assert agent_1_summary is not None
        assert agent_1_summary["work_state"] == AgentState.WORKING.value
        assert agent_1_summary["current_task"] == "coordinating"
        
        await state_manager.stop()


@pytest.mark.asyncio
class TestAgentStateManagerOperationLogs:
    """操作日志限制测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    async def test_operation_log_limit(self, temp_storage_path):
        """测试操作日志数量限制"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        await manager.register_agent("agent-1", AgentType.DIRECTOR)
        
        # 添加超过100条日志
        for i in range(150):
            log = AgentOperationLog(
                operation=f"operation_{i}",
                success=True
            )
            await manager.update_state(
                "agent-1",
                operation_log=log
            )
        
        snapshot = await manager.get_agent_state("agent-1")
        
        # 验证日志数量被限制在100条
        assert len(snapshot.operation_logs) <= 100
        
        await manager.stop()


@pytest.mark.asyncio
class TestAgentStateManagerEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def temp_storage_path(self):
        """创建临时存储路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    async def test_start_already_running(self, temp_storage_path):
        """测试重复启动"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        
        await manager.start()
        await manager.start()  # 重复启动应该无害
        
        assert manager.is_running
        
        await manager.stop()
    
    async def test_stop_not_running(self, temp_storage_path):
        """测试停止未运行的管理器"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        
        await manager.stop()  # 停止未运行的管理器应该无害
        
        assert not manager.is_running
    
    async def test_concurrent_operations(self, temp_storage_path):
        """测试并发操作"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        # 并发注册多个Agent
        tasks = [
            manager.register_agent(f"agent-{i}", AgentType.SYSTEM)
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        
        # 所有注册应该成功
        assert all(results)
        
        all_states = await manager.get_all_states()
        assert len(all_states) == 10
        
        await manager.stop()
    
    async def test_listener_error_handling(self, temp_storage_path):
        """测试监听器错误处理"""
        manager = AgentStateManager(
            storage_path=temp_storage_path,
            auto_persist=False
        )
        await manager.start()
        
        def error_listener(agent_id, snapshot):
            raise Exception("Listener error")
        
        manager.add_state_listener(error_listener)
        
        # 注册Agent不应该因为监听器错误而失败
        result = await manager.register_agent("agent-1", AgentType.DIRECTOR)
        assert result is True
        
        manager.remove_state_listener(error_listener)
        await manager.stop()
