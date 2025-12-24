"""
美术Agent单元测试

Feature: multi-agent-workflow-core
验证需求: Requirements 6.3 - 角色设计和视觉元素管理

测试内容:
- 角色设计管理
- 视觉元素管理
- 设计建议生成
- 色彩调色板管理
"""
import pytest
import pytest_asyncio
import asyncio
from typing import List

from app.core.message_bus import MessageBus
from app.agents.art_agent import (
    ArtAgent,
    CharacterDesign,
    VisualElement,
    ColorPalette,
    DesignCategory,
    DesignStatus,
    StyleType,
    DesignSuggestion,
    StyleReference,
)


class TestArtAgentBasics:
    """美术Agent基础功能测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, art_agent):
        """测试Agent初始化"""
        assert art_agent is not None
        assert art_agent.agent_id.startswith("art_agent_")
    
    @pytest.mark.asyncio
    async def test_agent_is_running(self, art_agent):
        """测试Agent运行状态"""
        assert art_agent.is_running


class TestCharacterDesign:
    """角色设计测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_create_character(self, art_agent):
        """测试创建角色"""
        character = await art_agent.create_character(
            name="Hero",
            description="Main protagonist",
            age="25",
            gender="Male",
            personality="Brave and kind",
            appearance="Tall with dark hair",
        )
        
        assert character is not None
        assert character.name == "Hero"
        assert character.description == "Main protagonist"
        assert character.age == "25"
        assert character.status == DesignStatus.DRAFT
    
    @pytest.mark.asyncio
    async def test_update_character(self, art_agent):
        """测试更新角色"""
        character = await art_agent.create_character(
            name="Hero",
            description="Original description",
        )
        
        updated = await art_agent.update_character(
            character.character_id,
            description="Updated description",
            personality="New personality",
        )
        
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.personality == "New personality"
    
    @pytest.mark.asyncio
    async def test_get_character(self, art_agent):
        """测试获取角色"""
        character = await art_agent.create_character(name="Test Character")
        
        retrieved = art_agent.get_character(character.character_id)
        
        assert retrieved is not None
        assert retrieved.character_id == character.character_id
        assert retrieved.name == "Test Character"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_character(self, art_agent):
        """测试获取不存在的角色"""
        retrieved = art_agent.get_character("nonexistent_id")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_get_all_characters(self, art_agent):
        """测试获取所有角色"""
        await art_agent.create_character(name="Character 1")
        await art_agent.create_character(name="Character 2")
        await art_agent.create_character(name="Character 3")
        
        all_characters = art_agent.get_all_characters()
        
        assert len(all_characters) == 3
    
    @pytest.mark.asyncio
    async def test_search_characters(self, art_agent):
        """测试搜索角色"""
        await art_agent.create_character(name="Hero", personality="brave")
        await art_agent.create_character(name="Villain", personality="cunning")
        await art_agent.create_character(name="Sidekick", personality="loyal")
        
        results = art_agent.search_characters("brave")
        
        assert len(results) == 1
        assert results[0].name == "Hero"


class TestVisualElements:
    """视觉元素测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_create_visual_element(self, art_agent):
        """测试创建视觉元素"""
        element = await art_agent.create_visual_element(
            name="Forest Background",
            category=DesignCategory.ENVIRONMENT,
            description="Dense forest scene",
            tags=["nature", "forest", "outdoor"],
            style=StyleType.REALISTIC,
        )
        
        assert element is not None
        assert element.name == "Forest Background"
        assert element.category == DesignCategory.ENVIRONMENT
        assert "forest" in element.tags
    
    @pytest.mark.asyncio
    async def test_get_elements_by_category(self, art_agent):
        """测试按类别获取元素"""
        await art_agent.create_visual_element(
            name="Element 1",
            category=DesignCategory.CHARACTER,
        )
        await art_agent.create_visual_element(
            name="Element 2",
            category=DesignCategory.ENVIRONMENT,
        )
        await art_agent.create_visual_element(
            name="Element 3",
            category=DesignCategory.CHARACTER,
        )
        
        char_elements = art_agent.get_elements_by_category(DesignCategory.CHARACTER)
        
        assert len(char_elements) == 2
    
    @pytest.mark.asyncio
    async def test_search_elements(self, art_agent):
        """测试搜索元素"""
        await art_agent.create_visual_element(
            name="Mountain Scene",
            category=DesignCategory.ENVIRONMENT,
            tags=["mountain", "outdoor"],
        )
        await art_agent.create_visual_element(
            name="City Street",
            category=DesignCategory.ENVIRONMENT,
            tags=["urban", "street"],
        )
        
        results = art_agent.search_elements("mountain")
        
        assert len(results) == 1
        assert results[0].name == "Mountain Scene"


class TestColorPalette:
    """色彩调色板测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_create_color_palette(self, art_agent):
        """测试创建调色板"""
        palette = await art_agent.create_color_palette(
            name="Warm Sunset",
            colors=["#FF6B6B", "#FFA07A", "#FFD700"],
            description="Warm sunset colors",
            mood="Romantic",
        )
        
        assert palette is not None
        assert palette.name == "Warm Sunset"
        assert len(palette.colors) == 3
        assert palette.mood == "Romantic"
    
    @pytest.mark.asyncio
    async def test_palette_add_color(self, art_agent):
        """测试添加颜色"""
        palette = await art_agent.create_color_palette(
            name="Test Palette",
            colors=["#FF0000"],
        )
        
        palette.add_color("#00FF00")
        
        assert len(palette.colors) == 2
        assert "#00FF00" in palette.colors
    
    @pytest.mark.asyncio
    async def test_palette_remove_color(self, art_agent):
        """测试移除颜色"""
        palette = await art_agent.create_color_palette(
            name="Test Palette",
            colors=["#FF0000", "#00FF00", "#0000FF"],
        )
        
        result = palette.remove_color("#00FF00")
        
        assert result is True
        assert len(palette.colors) == 2
        assert "#00FF00" not in palette.colors
    
    @pytest.mark.asyncio
    async def test_get_all_palettes(self, art_agent):
        """测试获取所有调色板"""
        await art_agent.create_color_palette(name="Palette 1")
        await art_agent.create_color_palette(name="Palette 2")
        
        all_palettes = art_agent.get_all_palettes()
        
        assert len(all_palettes) == 2



class TestDesignSuggestions:
    """设计建议测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_generate_character_suggestions(self, art_agent):
        """测试生成角色设计建议"""
        # 创建一个没有调色板的角色
        await art_agent.create_character(name="Test Character")
        
        suggestions = await art_agent.generate_suggestions(DesignCategory.CHARACTER)
        
        assert len(suggestions) > 0
        assert any("调色板" in s.title for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_generate_color_suggestions(self, art_agent):
        """测试生成色彩建议"""
        # 没有调色板时应该建议创建
        suggestions = await art_agent.generate_suggestions(DesignCategory.COLOR)
        
        assert len(suggestions) > 0
        assert any("主色调" in s.title for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_generate_environment_suggestions(self, art_agent):
        """测试生成环境设计建议"""
        suggestions = await art_agent.generate_suggestions(DesignCategory.ENVIRONMENT)
        
        assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_get_suggestions_by_category(self, art_agent):
        """测试按类别获取建议"""
        await art_agent.generate_suggestions(DesignCategory.CHARACTER)
        await art_agent.generate_suggestions(DesignCategory.COLOR)
        
        char_suggestions = art_agent.get_suggestions(DesignCategory.CHARACTER)
        
        assert all(s.category == DesignCategory.CHARACTER for s in char_suggestions)


class TestStyleReferences:
    """风格参考测试"""
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        """创建消息总线"""
        bus = MessageBus(max_history=100)
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_add_style_reference(self, art_agent):
        """测试添加风格参考"""
        reference = await art_agent.add_style_reference(
            name="Studio Ghibli Style",
            style_type=StyleType.ANIME,
            description="Soft colors and detailed backgrounds",
            source="Studio Ghibli films",
            tags=["anime", "ghibli", "soft"],
        )
        
        assert reference is not None
        assert reference.name == "Studio Ghibli Style"
        assert reference.style_type == StyleType.ANIME
    
    @pytest.mark.asyncio
    async def test_get_references_by_style(self, art_agent):
        """测试按风格获取参考"""
        await art_agent.add_style_reference(
            name="Reference 1",
            style_type=StyleType.ANIME,
        )
        await art_agent.add_style_reference(
            name="Reference 2",
            style_type=StyleType.REALISTIC,
        )
        await art_agent.add_style_reference(
            name="Reference 3",
            style_type=StyleType.ANIME,
        )
        
        anime_refs = art_agent.get_references_by_style(StyleType.ANIME)
        
        assert len(anime_refs) == 2


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
    async def art_agent(self, message_bus):
        """创建美术Agent"""
        agent = ArtAgent(message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_handle_create_character_message(self, art_agent):
        """测试创建角色消息"""
        response = await art_agent.handle_message({
            "action": "create_character",
            "name": "Test Hero",
            "description": "A brave hero",
        })
        
        assert response["success"] is True
        assert "character_id" in response
        assert response["name"] == "Test Hero"
    
    @pytest.mark.asyncio
    async def test_handle_get_character_message(self, art_agent):
        """测试获取角色消息"""
        # 先创建角色
        create_response = await art_agent.handle_message({
            "action": "create_character",
            "name": "Test Character",
        })
        
        # 获取角色
        response = await art_agent.handle_message({
            "action": "get_character",
            "character_id": create_response["character_id"],
        })
        
        assert response["success"] is True
        assert response["character"]["name"] == "Test Character"
    
    @pytest.mark.asyncio
    async def test_handle_create_element_message(self, art_agent):
        """测试创建元素消息"""
        response = await art_agent.handle_message({
            "action": "create_element",
            "name": "Test Element",
            "category": "environment",
            "tags": ["test", "element"],
        })
        
        assert response["success"] is True
        assert "element_id" in response
    
    @pytest.mark.asyncio
    async def test_handle_create_palette_message(self, art_agent):
        """测试创建调色板消息"""
        response = await art_agent.handle_message({
            "action": "create_palette",
            "name": "Test Palette",
            "colors": ["#FF0000", "#00FF00"],
            "mood": "Energetic",
        })
        
        assert response["success"] is True
        assert "palette_id" in response
    
    @pytest.mark.asyncio
    async def test_handle_get_suggestions_message(self, art_agent):
        """测试获取建议消息"""
        response = await art_agent.handle_message({
            "action": "get_suggestions",
            "category": "color",
        })
        
        assert response["success"] is True
        assert "suggestions" in response
    
    @pytest.mark.asyncio
    async def test_handle_unknown_action(self, art_agent):
        """测试未知操作"""
        response = await art_agent.handle_message({
            "action": "unknown_action",
        })
        
        assert "error" in response
