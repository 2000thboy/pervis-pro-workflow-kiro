"""
系统Agent属性测试 - 基于属性的测试验证系统状态查询实时性

Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
验证需求: Requirements 1.5 - WHEN 用户查询系统状态时 THEN 系统Agent SHALL 提供实时的Agent状态信息

测试策略:
- 使用Hypothesis生成随机的Agent状态更新
- 验证系统Agent能够实时反映所有Agent的状态
- 验证状态查询的准确性和完整性
"""
import pytest
import asyncio
import uuid
from typing import List, Dict, Any
from hypothesis import given, strategies as st, settings, assume

from app.core.message_bus import MessageBus
from app.agents.system_agent import (
    SystemAgent,
    SearchType,
    SearchResult,
)
from app.core.agent_types import AgentState, AgentType


# 自定义策略：生成Agent ID
agent_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=30
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成Agent类型
agent_type_strategy = st.sampled_from(list(AgentType))

# 自定义策略：生成Agent状态
agent_state_strategy = st.sampled_from(list(AgentState))

# 自定义策略：生成搜索查询
search_query_strategy = st.text(min_size=1, max_size=50).filter(lambda x: len(x.strip()) > 0)


class TestSystemAgentStatusQuery:
    """
    属性 5: 系统状态查询实时性
    
    *对于任何*用户的状态查询请求，系统Agent应该返回所有Agent的实时准确状态信息
    
    验证需求: Requirements 1.5
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        agent_type=agent_type_strategy,
        work_state=agent_state_strategy
    )
    async def test_status_update_reflected_immediately(
        self,
        agent_id: str,
        agent_type: AgentType,
        work_state: AgentState
    ):
        """
        Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
        
        属性: 对于任何Agent状态更新，系统Agent应该立即反映该更新
        
        验证需求: Requirements 1.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建系统Agent
            system_agent = SystemAgent(message_bus=bus)
            await system_agent.initialize()
            await system_agent.start()
            
            # 更新Agent状态
            status_info = {
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "work_state": work_state.value,
                "current_task": "test_task"
            }
            system_agent.update_agent_status(agent_id, status_info)
            
            # 查询状态
            queried_status = system_agent.get_agent_status(agent_id)
            
            # 验证属性1: 状态被正确存储
            assert queried_status is not None, "状态应该被存储"
            
            # 验证属性2: Agent ID正确
            assert queried_status.get("agent_id") == agent_id, \
                f"Agent ID应该为{agent_id}"
            
            # 验证属性3: Agent类型正确
            assert queried_status.get("agent_type") == agent_type.value, \
                f"Agent类型应该为{agent_type.value}"
            
            # 验证属性4: 工作状态正确
            assert queried_status.get("work_state") == work_state.value, \
                f"工作状态应该为{work_state.value}"
            
            # 验证属性5: 有更新时间戳
            assert "last_update" in queried_status, "应该有更新时间戳"
            
            await system_agent.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_count=st.integers(min_value=1, max_value=10)
    )
    async def test_all_agents_status_query(
        self,
        agent_count: int
    ):
        """
        Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
        
        属性: 对于任意数量的Agent，系统Agent应该能够返回所有Agent的状态
        
        验证需求: Requirements 1.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            system_agent = SystemAgent(message_bus=bus)
            await system_agent.initialize()
            await system_agent.start()
            
            # 添加多个Agent状态
            agent_types = list(AgentType)
            for i in range(agent_count):
                agent_id = f"test_agent_{i}"
                agent_type = agent_types[i % len(agent_types)]
                
                system_agent.update_agent_status(agent_id, {
                    "agent_id": agent_id,
                    "agent_type": agent_type.value,
                    "work_state": AgentState.IDLE.value
                })
            
            # 查询所有状态
            all_status = system_agent.get_all_agent_status()
            
            # 验证属性1: 返回的状态数量正确
            assert all_status["total_agents"] == agent_count, \
                f"应该有{agent_count}个Agent状态，实际有{all_status['total_agents']}个"
            
            # 验证属性2: 所有Agent都在结果中
            agents = all_status["agents"]
            for i in range(agent_count):
                agent_id = f"test_agent_{i}"
                assert agent_id in agents, f"Agent {agent_id} 应该在结果中"
            
            # 验证属性3: 有最后更新时间
            assert all_status["last_update"] is not None, "应该有最后更新时间"
            
            await system_agent.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        agent_id=agent_id_strategy,
        updates=st.lists(
            st.sampled_from(list(AgentState)),
            min_size=2,
            max_size=5
        )
    )
    async def test_status_updates_sequence(
        self,
        agent_id: str,
        updates: List[AgentState]
    ):
        """
        Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
        
        属性: 对于任何状态更新序列，系统Agent应该始终反映最新的状态
        
        验证需求: Requirements 1.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            system_agent = SystemAgent(message_bus=bus)
            await system_agent.initialize()
            await system_agent.start()
            
            # 执行一系列状态更新
            for state in updates:
                system_agent.update_agent_status(agent_id, {
                    "agent_id": agent_id,
                    "agent_type": AgentType.SYSTEM.value,
                    "work_state": state.value
                })
            
            # 查询最终状态
            final_status = system_agent.get_agent_status(agent_id)
            
            # 验证属性: 最终状态是最后一次更新的状态
            expected_state = updates[-1].value
            assert final_status.get("work_state") == expected_state, \
                f"最终状态应该是{expected_state}，实际是{final_status.get('work_state')}"
            
            await system_agent.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        query=search_query_strategy
    )
    async def test_search_returns_results(
        self,
        query: str
    ):
        """
        Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
        
        属性: 对于任何搜索查询，系统Agent应该返回有效的搜索结果列表
        
        验证需求: Requirements 8.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            system_agent = SystemAgent(message_bus=bus)
            await system_agent.initialize()
            await system_agent.start()
            
            # 添加一些可搜索的数据
            system_agent.update_agent_status("test_agent", {
                "agent_id": "test_agent",
                "agent_type": AgentType.SYSTEM.value,
                "work_state": AgentState.IDLE.value
            })
            
            # 执行搜索
            results = await system_agent.search(query, SearchType.ALL, limit=10)
            
            # 验证属性1: 结果是列表
            assert isinstance(results, list), "搜索结果应该是列表"
            
            # 验证属性2: 结果数量不超过限制
            assert len(results) <= 10, "结果数量不应超过限制"
            
            # 验证属性3: 每个结果都是SearchResult类型
            for result in results:
                assert isinstance(result, SearchResult), "每个结果应该是SearchResult类型"
            
            await system_agent.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        user_id=agent_id_strategy
    )
    async def test_session_management(
        self,
        user_id: str
    ):
        """
        Feature: multi-agent-workflow-core, Property 5: 系统状态查询实时性
        
        属性: 对于任何用户，系统Agent应该能够创建和管理会话
        
        验证需求: Requirements 8.1
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            system_agent = SystemAgent(message_bus=bus)
            await system_agent.initialize()
            await system_agent.start()
            
            # 创建会话
            session = system_agent.create_session(user_id, {"test": True})
            
            # 验证属性1: 会话被创建
            assert session is not None, "会话应该被创建"
            
            # 验证属性2: 会话ID存在
            assert session.session_id is not None, "会话ID应该存在"
            
            # 验证属性3: 用户ID正确
            assert session.user_id == user_id, f"用户ID应该是{user_id}"
            
            # 验证属性4: 可以获取会话
            retrieved_session = system_agent.get_session(session.session_id)
            assert retrieved_session is not None, "应该能够获取会话"
            assert retrieved_session.session_id == session.session_id, "会话ID应该匹配"
            
            # 验证属性5: 可以关闭会话
            closed = system_agent.close_session(session.session_id)
            assert closed is True, "应该能够关闭会话"
            
            # 验证属性6: 关闭后无法获取会话
            closed_session = system_agent.get_session(session.session_id)
            assert closed_session is None, "关闭后不应该能获取会话"
            
            await system_agent.stop()
            
        finally:
            await bus.stop()
