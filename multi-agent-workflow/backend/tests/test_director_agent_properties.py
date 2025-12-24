"""
导演Agent属性测试 - 基于属性的测试验证导演Agent冲突解决权威性

Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
验证需求: Requirements 1.3 - WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突

测试策略:
- 使用Hypothesis生成随机的冲突场景
- 验证导演Agent能够解决所有类型的冲突
- 验证冲突解决结果的一致性和权威性
"""
import pytest
import asyncio
import uuid
from typing import List, Dict, Any
from hypothesis import given, strategies as st, settings, assume

from app.core.message_bus import MessageBus
from app.agents.director_agent import (
    DirectorAgent,
    ConflictType,
    ConflictResolutionStrategy,
    ConflictReport,
)
from app.core.agent_types import AgentType


# 自定义策略：生成冲突类型
conflict_type_strategy = st.sampled_from(list(ConflictType))

# 自定义策略：生成Agent ID列表
agent_ids_strategy = st.lists(
    st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
        min_size=1,
        max_size=30
    ).filter(lambda x: len(x.strip()) > 0),
    min_size=1,
    max_size=5,
    unique=True
)

# 自定义策略：生成冲突详情
conflict_details_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda x: len(x.strip()) > 0),
    values=st.one_of(st.integers(), st.text(max_size=50), st.booleans()),
    min_size=0,
    max_size=5
)


class TestDirectorAgentConflictResolution:
    """
    属性 3: 导演Agent冲突解决权威性
    
    *对于任何*Agent间的冲突情况，导演Agent应该作为最终决策者成功解决冲突
    
    验证需求: Requirements 1.3
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        conflict_type=conflict_type_strategy,
        involved_agents=agent_ids_strategy,
        details=conflict_details_strategy
    )
    async def test_director_resolves_all_conflict_types(
        self,
        conflict_type: ConflictType,
        involved_agents: List[str],
        details: Dict[str, Any]
    ):
        """
        Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
        
        属性: 对于任何类型的冲突，导演Agent都应该能够成功解决
        并返回有效的解决方案
        
        验证需求: Requirements 1.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            # 创建导演Agent
            director = DirectorAgent(message_bus=bus)
            await director.initialize()
            await director.start()
            
            # 创建冲突报告
            conflict = ConflictReport(
                conflict_id=str(uuid.uuid4()),
                conflict_type=conflict_type,
                reporter_agent=involved_agents[0] if involved_agents else "test_agent",
                involved_agents=involved_agents,
                details=details
            )
            
            # 解决冲突
            resolution = await director.resolve_conflict(conflict)
            
            # 验证属性1: 解决方案不为空
            assert resolution is not None, "冲突解决方案不应为空"
            
            # 验证属性2: 解决方案是字典类型
            assert isinstance(resolution, dict), "解决方案应该是字典类型"
            
            # 验证属性3: 冲突被标记为已解决
            assert conflict.resolved is True, "冲突应该被标记为已解决"
            
            # 验证属性4: 解决策略被记录
            assert conflict.resolution_strategy is not None, "解决策略应该被记录"
            
            # 验证属性5: 解决方案被记录
            assert conflict.resolution is not None, "解决方案应该被记录到冲突报告中"
            
            await director.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        conflict_type=conflict_type_strategy,
        agent_count=st.integers(min_value=2, max_value=8)
    )
    async def test_director_authority_in_conflict_resolution(
        self,
        conflict_type: ConflictType,
        agent_count: int
    ):
        """
        Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
        
        属性: 对于任何冲突，导演Agent的决定应该是最终的、权威的
        无论涉及多少个Agent
        
        验证需求: Requirements 1.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            director = DirectorAgent(message_bus=bus)
            await director.initialize()
            await director.start()
            
            # 生成涉及的Agent列表
            involved_agents = [f"agent_{i}" for i in range(agent_count)]
            
            # 创建冲突
            conflict = ConflictReport(
                conflict_id=str(uuid.uuid4()),
                conflict_type=conflict_type,
                reporter_agent=involved_agents[0],
                involved_agents=involved_agents,
                details={"test": True}
            )
            
            # 解决冲突
            resolution = await director.resolve_conflict(conflict)
            
            # 验证属性1: 解决方案包含决策信息
            assert resolution is not None, "必须有解决方案"
            
            # 验证属性2: 冲突记录在导演Agent中
            conflicts = director.get_conflicts()
            assert len(conflicts) >= 1, "冲突应该被记录"
            
            # 验证属性3: 解决的冲突可以被查询
            resolved_conflicts = director.get_conflicts(resolved=True)
            assert len(resolved_conflicts) >= 1, "已解决的冲突应该可以被查询"
            
            # 验证属性4: 操作日志记录了冲突解决
            logs = director.get_operation_logs()
            conflict_logs = [l for l in logs if "conflict" in l["operation"]]
            assert len(conflict_logs) >= 1, "应该记录冲突相关的操作日志"
            
            await director.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        priorities=st.lists(
            st.integers(min_value=1, max_value=10),
            min_size=2,
            max_size=5
        )
    )
    async def test_priority_based_conflict_resolution(
        self,
        priorities: List[int]
    ):
        """
        Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
        
        属性: 对于基于优先级的冲突解决，优先级最高的Agent应该获胜
        
        验证需求: Requirements 1.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            director = DirectorAgent(message_bus=bus)
            await director.initialize()
            await director.start()
            
            # 创建Agent并设置优先级
            agents = [f"agent_{i}" for i in range(len(priorities))]
            for agent_id, priority in zip(agents, priorities):
                director.set_agent_priority(agent_id, priority)
            
            # 设置资源冲突使用优先级策略
            director.set_resolution_strategy(
                ConflictType.RESOURCE_CONFLICT,
                ConflictResolutionStrategy.PRIORITY_BASED
            )
            
            # 创建资源冲突
            conflict = ConflictReport(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.RESOURCE_CONFLICT,
                reporter_agent=agents[0],
                involved_agents=agents,
                details={}
            )
            
            # 解决冲突
            resolution = await director.resolve_conflict(conflict)
            
            # 验证属性: 优先级最高的Agent获胜
            expected_winner = agents[priorities.index(max(priorities))]
            assert resolution.get("winner") == expected_winner, \
                f"优先级最高的Agent应该获胜，期望{expected_winner}，实际{resolution.get('winner')}"
            
            await director.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        conflict_count=st.integers(min_value=1, max_value=10)
    )
    async def test_multiple_conflicts_resolution(
        self,
        conflict_count: int
    ):
        """
        Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
        
        属性: 对于任意数量的冲突，导演Agent都应该能够逐一解决
        
        验证需求: Requirements 1.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            director = DirectorAgent(message_bus=bus)
            await director.initialize()
            await director.start()
            
            # 创建多个冲突
            conflicts = []
            for i in range(conflict_count):
                conflict = ConflictReport(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=list(ConflictType)[i % len(ConflictType)],
                    reporter_agent=f"agent_{i}",
                    involved_agents=[f"agent_{i}", f"agent_{i+1}"],
                    details={"index": i}
                )
                conflicts.append(conflict)
            
            # 解决所有冲突
            resolutions = []
            for conflict in conflicts:
                resolution = await director.resolve_conflict(conflict)
                resolutions.append(resolution)
            
            # 验证属性1: 所有冲突都被解决
            assert len(resolutions) == conflict_count, "所有冲突都应该有解决方案"
            
            # 验证属性2: 所有冲突都被标记为已解决
            for conflict in conflicts:
                assert conflict.resolved is True, "所有冲突都应该被标记为已解决"
            
            # 验证属性3: 导演Agent记录了所有冲突
            recorded_conflicts = director.get_conflicts()
            assert len(recorded_conflicts) == conflict_count, \
                f"应该记录{conflict_count}个冲突，实际记录{len(recorded_conflicts)}个"
            
            await director.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        strategy=st.sampled_from(list(ConflictResolutionStrategy))
    )
    async def test_resolution_strategy_consistency(
        self,
        strategy: ConflictResolutionStrategy
    ):
        """
        Feature: multi-agent-workflow-core, Property 3: 导演Agent冲突解决权威性
        
        属性: 对于任何解决策略，导演Agent都应该一致地应用该策略
        
        验证需求: Requirements 1.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            director = DirectorAgent(message_bus=bus)
            await director.initialize()
            await director.start()
            
            # 设置所有冲突类型使用相同策略
            for conflict_type in ConflictType:
                director.set_resolution_strategy(conflict_type, strategy)
            
            # 创建冲突
            conflict = ConflictReport(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.TASK_CONFLICT,
                reporter_agent="agent_1",
                involved_agents=["agent_1", "agent_2"],
                details={}
            )
            
            # 解决冲突
            await director.resolve_conflict(conflict)
            
            # 验证属性: 使用了指定的策略
            assert conflict.resolution_strategy == strategy, \
                f"应该使用策略{strategy}，实际使用{conflict.resolution_strategy}"
            
            await director.stop()
            
        finally:
            await bus.stop()
