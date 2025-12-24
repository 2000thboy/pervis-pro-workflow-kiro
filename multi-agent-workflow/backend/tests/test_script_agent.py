"""
编剧Agent单元测试

Feature: multi-agent-workflow-core
验证需求: Requirements 3.2 - 剧本时长评估和分析功能

测试内容:
- 剧本解析功能
- 时长评估算法
- 剧本分析功能
"""
import pytest
import pytest_asyncio
import asyncio
from typing import List

from app.core.message_bus import MessageBus
from app.agents.script_agent import (
    ScriptAgent,
    Script,
    Scene,
    SceneType,
    TimeOfDay,
    DialogueLine,
    ActionLine,
    DurationEstimate,
    ScriptAnalysisResult,
)


# 测试用剧本内容
SAMPLE_SCRIPT = """
INT. COFFEE SHOP - DAY

A busy coffee shop. JOHN (30s) sits at a corner table, nervously checking his phone.

JOHN
(anxious)
She should be here by now.

The door opens. SARAH (28) walks in, looking around.

SARAH
John! Sorry I'm late.

JOHN
No problem. I just got here myself.

They embrace awkwardly.

EXT. CITY STREET - NIGHT

John and Sarah walk down a quiet street, the city lights reflecting off wet pavement.

SARAH
That was a nice dinner.

JOHN
I'm glad you enjoyed it.

They stop at a corner.

JOHN
So... same time next week?

SARAH
(smiling)
I'd like that.

INT. JOHN'S APARTMENT - CONTINUOUS

John enters his apartment, a smile on his face. He tosses his keys on the counter.

JOHN
(to himself)
Best night ever.
"""

MINIMAL_SCRIPT = """
INT. ROOM - DAY

A person sits alone.

PERSON
Hello.
"""


class TestScriptAgentBasics:
    """编剧Agent基础功能测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def script_agent(self, message_bus):
        """创建编剧Agent"""
        agent = ScriptAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, script_agent):
        """测试Agent初始化"""
        assert script_agent is not None
        assert script_agent.agent_id.startswith("script_agent_")
    
    @pytest.mark.asyncio
    async def test_parse_script_basic(self, script_agent):
        """测试基本剧本解析"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
            author="Test Author",
        )
        
        assert script is not None
        assert script.title == "Test Script"
        assert script.author == "Test Author"
        assert len(script.scenes) == 3
    
    @pytest.mark.asyncio
    async def test_parse_script_scene_types(self, script_agent):
        """测试场景类型解析"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        # 第一个场景: INT. COFFEE SHOP - DAY
        assert script.scenes[0].scene_type == SceneType.INTERIOR
        assert script.scenes[0].time_of_day == TimeOfDay.DAY
        
        # 第二个场景: EXT. CITY STREET - NIGHT
        assert script.scenes[1].scene_type == SceneType.EXTERIOR
        assert script.scenes[1].time_of_day == TimeOfDay.NIGHT
        
        # 第三个场景: INT. JOHN'S APARTMENT - CONTINUOUS
        assert script.scenes[2].scene_type == SceneType.INTERIOR
        assert script.scenes[2].time_of_day == TimeOfDay.CONTINUOUS
    
    @pytest.mark.asyncio
    async def test_parse_script_dialogues(self, script_agent):
        """测试对话解析"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        # 第一个场景应该有对话
        scene1 = script.scenes[0]
        assert len(scene1.dialogues) > 0
        
        # 检查角色列表
        assert "JOHN" in scene1.characters
        assert "SARAH" in scene1.characters
    
    @pytest.mark.asyncio
    async def test_parse_script_actions(self, script_agent):
        """测试动作描述解析"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        # 每个场景应该有动作描述
        for scene in script.scenes:
            assert len(scene.actions) > 0


class TestDurationEstimation:
    """时长评估测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def script_agent(self, message_bus):
        """创建编剧Agent"""
        agent = ScriptAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_duration_estimate_basic(self, script_agent):
        """测试基本时长评估"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        estimate = await script_agent.estimate_duration(script.script_id)
        
        assert estimate is not None
        assert estimate.total_minutes > 0
        assert estimate.total_seconds > 0
        assert estimate.scene_count == 3
    
    @pytest.mark.asyncio
    async def test_duration_estimate_dialogue_count(self, script_agent):
        """测试对话计数"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        estimate = await script_agent.estimate_duration(script.script_id)
        
        assert estimate.dialogue_count > 0
    
    @pytest.mark.asyncio
    async def test_duration_estimate_character_count(self, script_agent):
        """测试角色计数"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        estimate = await script_agent.estimate_duration(script.script_id)
        
        # 应该有JOHN, SARAH等角色
        assert estimate.character_count >= 2
    
    @pytest.mark.asyncio
    async def test_duration_estimate_breakdown(self, script_agent):
        """测试场景时长分解"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        estimate = await script_agent.estimate_duration(script.script_id)
        
        # 应该有每个场景的时长分解
        assert len(estimate.breakdown_by_scene) == 3
        
        # 所有场景时长之和应该等于总时长
        total_from_breakdown = sum(estimate.breakdown_by_scene.values())
        assert abs(total_from_breakdown - estimate.total_seconds) < 1.0
    
    @pytest.mark.asyncio
    async def test_duration_nonexistent_script(self, script_agent):
        """测试不存在的剧本"""
        with pytest.raises(ValueError) as exc_info:
            await script_agent.estimate_duration("nonexistent_id")
        
        assert "不存在" in str(exc_info.value)


class TestScriptAnalysis:
    """剧本分析测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def script_agent(self, message_bus):
        """创建编剧Agent"""
        agent = ScriptAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_analyze_script_basic(self, script_agent):
        """测试基本剧本分析"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        assert result is not None
        assert result.script_id == script.script_id
        assert result.title == "Test Script"
        assert result.scene_count == 3
    
    @pytest.mark.asyncio
    async def test_analyze_script_character_list(self, script_agent):
        """测试角色列表"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        assert len(result.character_list) >= 2
        assert "JOHN" in result.character_list
        assert "SARAH" in result.character_list
    
    @pytest.mark.asyncio
    async def test_analyze_script_ratios(self, script_agent):
        """测试对话/动作占比"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        # 占比应该在0-1之间
        assert 0 <= result.dialogue_ratio <= 1
        assert 0 <= result.action_ratio <= 1
        
        # 两者之和应该接近1
        assert abs(result.dialogue_ratio + result.action_ratio - 1.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_analyze_script_scores(self, script_agent):
        """测试评分"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        # 评分应该在0-1之间
        assert 0 <= result.pacing_score <= 1
        assert 0 <= result.complexity_score <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_script_recommendations(self, script_agent):
        """测试建议生成"""
        script = await script_agent.parse_script(
            content=MINIMAL_SCRIPT,
            title="Minimal Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        # 对于简单剧本，应该有一些建议
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_analyze_script_duration_included(self, script_agent):
        """测试分析结果包含时长评估"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        result = await script_agent.analyze_script(script.script_id)
        
        assert result.duration_estimate is not None
        assert result.duration_estimate.total_minutes > 0


class TestSceneRetrieval:
    """场景检索测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def script_agent(self, message_bus):
        """创建编剧Agent"""
        agent = ScriptAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_get_scene_by_number(self, script_agent):
        """测试按编号获取场景"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        scene = script_agent.get_scene(script.script_id, 1)
        
        assert scene is not None
        assert scene.scene_number == 1
        assert "COFFEE SHOP" in scene.location.upper()
    
    @pytest.mark.asyncio
    async def test_get_scene_nonexistent(self, script_agent):
        """测试获取不存在的场景"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        scene = script_agent.get_scene(script.script_id, 999)
        
        assert scene is None
    
    @pytest.mark.asyncio
    async def test_get_script(self, script_agent):
        """测试获取剧本"""
        script = await script_agent.parse_script(
            content=SAMPLE_SCRIPT,
            title="Test Script",
        )
        
        retrieved = script_agent.get_script(script.script_id)
        
        assert retrieved is not None
        assert retrieved.script_id == script.script_id
    
    @pytest.mark.asyncio
    async def test_get_all_scripts(self, script_agent):
        """测试获取所有剧本"""
        await script_agent.parse_script(content=SAMPLE_SCRIPT, title="Script 1")
        await script_agent.parse_script(content=MINIMAL_SCRIPT, title="Script 2")
        
        all_scripts = script_agent.get_all_scripts()
        
        assert len(all_scripts) == 2


class TestMessageHandling:
    """消息处理测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def script_agent(self, message_bus):
        """创建编剧Agent"""
        agent = ScriptAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_handle_parse_script_message(self, script_agent):
        """测试解析剧本消息"""
        response = await script_agent.handle_message({
            "action": "parse_script",
            "content": SAMPLE_SCRIPT,
            "title": "Test Script",
        })
        
        assert response["success"] is True
        assert "script_id" in response
        assert response["scene_count"] == 3
    
    @pytest.mark.asyncio
    async def test_handle_estimate_duration_message(self, script_agent):
        """测试时长评估消息"""
        # 先解析剧本
        parse_response = await script_agent.handle_message({
            "action": "parse_script",
            "content": SAMPLE_SCRIPT,
            "title": "Test Script",
        })
        
        # 评估时长
        response = await script_agent.handle_message({
            "action": "estimate_duration",
            "script_id": parse_response["script_id"],
        })
        
        assert response["success"] is True
        assert response["total_minutes"] > 0
    
    @pytest.mark.asyncio
    async def test_handle_analyze_script_message(self, script_agent):
        """测试分析剧本消息"""
        # 先解析剧本
        parse_response = await script_agent.handle_message({
            "action": "parse_script",
            "content": SAMPLE_SCRIPT,
            "title": "Test Script",
        })
        
        # 分析剧本
        response = await script_agent.handle_message({
            "action": "analyze_script",
            "script_id": parse_response["script_id"],
        })
        
        assert response["success"] is True
        assert "analysis" in response
    
    @pytest.mark.asyncio
    async def test_handle_unknown_action(self, script_agent):
        """测试未知操作"""
        response = await script_agent.handle_message({
            "action": "unknown_action",
        })
        
        assert "error" in response
