"""
美术Agent (ArtAgent) - 提供视觉设计支持

Feature: multi-agent-workflow-core
验证需求: Requirements 6.3 - 角色设计和视觉元素管理

主要功能:
- 角色设计管理
- 视觉元素管理
- 设计建议生成
- 风格参考管理
- LLM 集成：视觉标签生成、参考资料分类（0-Fix.3）
"""
import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.core.agent_types import AgentType
from app.core.message_bus import MessageBus

# 类型检查时导入，运行时延迟加载
if TYPE_CHECKING:
    from services.agent_llm_adapter import AgentLLMAdapter


class DesignCategory(str, Enum):
    """设计类别"""
    CHARACTER = "character"      # 角色设计
    ENVIRONMENT = "environment"  # 环境设计
    PROP = "prop"               # 道具设计
    COSTUME = "costume"         # 服装设计
    COLOR = "color"             # 色彩设计
    LIGHTING = "lighting"       # 灯光设计


class DesignStatus(str, Enum):
    """设计状态"""
    DRAFT = "draft"           # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    REVIEW = "review"         # 审核中
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"     # 已拒绝
    ARCHIVED = "archived"     # 已归档


class StyleType(str, Enum):
    """风格类型"""
    REALISTIC = "realistic"     # 写实
    STYLIZED = "stylized"       # 风格化
    CARTOON = "cartoon"         # 卡通
    ANIME = "anime"             # 动漫
    MINIMALIST = "minimalist"   # 极简
    ABSTRACT = "abstract"       # 抽象


@dataclass
class ColorPalette:
    """色彩调色板"""
    palette_id: str
    name: str
    colors: List[str] = field(default_factory=list)  # 十六进制颜色值
    description: str = ""
    mood: str = ""  # 情绪/氛围
    
    def add_color(self, color: str) -> None:
        """添加颜色"""
        if color not in self.colors:
            self.colors.append(color)
    
    def remove_color(self, color: str) -> bool:
        """移除颜色"""
        if color in self.colors:
            self.colors.remove(color)
            return True
        return False


@dataclass
class VisualElement:
    """视觉元素"""
    element_id: str
    name: str
    category: DesignCategory
    description: str = ""
    tags: List[str] = field(default_factory=list)
    style: StyleType = StyleType.REALISTIC
    color_palette: Optional[ColorPalette] = None
    reference_images: List[str] = field(default_factory=list)
    status: DesignStatus = DesignStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CharacterDesign:
    """角色设计"""
    character_id: str
    name: str
    description: str = ""
    age: Optional[str] = None
    gender: Optional[str] = None
    personality: str = ""
    appearance: str = ""
    costume_notes: str = ""
    color_palette: Optional[ColorPalette] = None
    reference_images: List[str] = field(default_factory=list)
    visual_elements: List[VisualElement] = field(default_factory=list)
    status: DesignStatus = DesignStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DesignSuggestion:
    """设计建议"""
    suggestion_id: str
    category: DesignCategory
    title: str
    description: str
    rationale: str = ""  # 建议理由
    priority: int = 1  # 1-5, 5最高
    related_elements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StyleReference:
    """风格参考"""
    reference_id: str
    name: str
    style_type: StyleType
    description: str = ""
    source: str = ""  # 来源
    image_urls: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""


class ArtAgent(BaseAgent):
    """
    美术Agent - 提供视觉设计支持
    
    主要功能:
    - 角色设计管理
    - 视觉元素管理
    - 设计建议生成
    - 风格参考管理
    - LLM 集成：视觉标签生成、参考资料分类（0-Fix.3）
    """
    
    def __init__(
        self,
        message_bus: MessageBus,
        agent_id: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id or f"art_agent_{uuid4().hex[:8]}",
            agent_type=AgentType.ART,
            message_bus=message_bus,
        )
        self._logger = logging.getLogger(__name__)
        
        # 数据存储
        self._characters: Dict[str, CharacterDesign] = {}
        self._visual_elements: Dict[str, VisualElement] = {}
        self._color_palettes: Dict[str, ColorPalette] = {}
        self._style_references: Dict[str, StyleReference] = {}
        self._suggestions: Dict[str, DesignSuggestion] = {}
        
        # LLM 适配器（延迟加载）
        self._llm_adapter: Optional["AgentLLMAdapter"] = None
    
    async def _on_initialize(self) -> None:
        """初始化美术Agent"""
        self._logger.info("美术Agent初始化完成")
    
    def _get_llm_adapter(self) -> Optional["AgentLLMAdapter"]:
        """
        延迟加载 LLM 适配器
        
        Returns:
            AgentLLMAdapter 实例，如果加载失败返回 None
        """
        if self._llm_adapter is None:
            try:
                # 添加 Pervis PRO 后端路径
                pervis_backend = Path(__file__).parent.parent.parent.parent.parent / "Pervis PRO" / "backend"
                if str(pervis_backend) not in sys.path:
                    sys.path.insert(0, str(pervis_backend))
                
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
                self._logger.info("ArtAgent LLM 适配器加载成功")
            except ImportError as e:
                self._logger.warning(f"无法加载 LLM 适配器: {e}")
            except Exception as e:
                self._logger.error(f"LLM 适配器初始化失败: {e}")
        return self._llm_adapter
    
    async def _on_start(self) -> None:
        """启动美术Agent"""
        self._logger.info("美术Agent已启动")
    
    async def _on_stop(self) -> None:
        """停止美术Agent"""
        self._logger.info("美术Agent已停止")
    
    async def handle_message(self, message) -> Optional[Dict[str, Any]]:
        """处理普通消息"""
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = message
        
        if isinstance(content, dict):
            action = content.get("action")
            
            if action == "create_character":
                return await self._handle_create_character(content)
            elif action == "update_character":
                return await self._handle_update_character(content)
            elif action == "get_character":
                return await self._handle_get_character(content)
            elif action == "create_element":
                return await self._handle_create_element(content)
            elif action == "get_suggestions":
                return await self._handle_get_suggestions(content)
            elif action == "create_palette":
                return await self._handle_create_palette(content)
        
        return {"error": "未知操作"}
    
    async def handle_protocol_message(self, message) -> Optional[Any]:
        """处理协议消息"""
        if hasattr(message, 'payload') and hasattr(message.payload, 'data'):
            data = message.payload.data
            return await self.handle_message(data)
        return None
    
    # ========================================================================
    # 角色设计管理
    # ========================================================================
    
    async def create_character(
        self,
        name: str,
        description: str = "",
        age: Optional[str] = None,
        gender: Optional[str] = None,
        personality: str = "",
        appearance: str = "",
    ) -> CharacterDesign:
        """
        创建角色设计
        
        Args:
            name: 角色名称
            description: 角色描述
            age: 年龄
            gender: 性别
            personality: 性格特点
            appearance: 外观描述
            
        Returns:
            创建的角色设计
        """
        character_id = f"char_{uuid4().hex[:8]}"
        character = CharacterDesign(
            character_id=character_id,
            name=name,
            description=description,
            age=age,
            gender=gender,
            personality=personality,
            appearance=appearance,
        )
        
        self._characters[character_id] = character
        self._logger.info(f"创建角色设计: {name} ({character_id})")
        
        return character
    
    async def update_character(
        self,
        character_id: str,
        **updates
    ) -> Optional[CharacterDesign]:
        """
        更新角色设计
        
        Args:
            character_id: 角色ID
            **updates: 要更新的字段
            
        Returns:
            更新后的角色设计，如果不存在返回None
        """
        character = self._characters.get(character_id)
        if not character:
            return None
        
        for key, value in updates.items():
            if hasattr(character, key):
                setattr(character, key, value)
        
        character.updated_at = datetime.now()
        self._logger.info(f"更新角色设计: {character_id}")
        
        return character
    
    def get_character(self, character_id: str) -> Optional[CharacterDesign]:
        """获取角色设计"""
        return self._characters.get(character_id)
    
    def get_all_characters(self) -> List[CharacterDesign]:
        """获取所有角色设计"""
        return list(self._characters.values())
    
    def search_characters(self, query: str) -> List[CharacterDesign]:
        """搜索角色设计"""
        query_lower = query.lower()
        results = []
        for char in self._characters.values():
            if (query_lower in char.name.lower() or
                query_lower in char.description.lower() or
                query_lower in char.personality.lower()):
                results.append(char)
        return results

    
    # ========================================================================
    # 视觉元素管理
    # ========================================================================
    
    async def create_visual_element(
        self,
        name: str,
        category: DesignCategory,
        description: str = "",
        tags: Optional[List[str]] = None,
        style: StyleType = StyleType.REALISTIC,
    ) -> VisualElement:
        """
        创建视觉元素
        
        Args:
            name: 元素名称
            category: 设计类别
            description: 描述
            tags: 标签列表
            style: 风格类型
            
        Returns:
            创建的视觉元素
        """
        element_id = f"elem_{uuid4().hex[:8]}"
        element = VisualElement(
            element_id=element_id,
            name=name,
            category=category,
            description=description,
            tags=tags or [],
            style=style,
        )
        
        self._visual_elements[element_id] = element
        self._logger.info(f"创建视觉元素: {name} ({element_id})")
        
        return element
    
    def get_visual_element(self, element_id: str) -> Optional[VisualElement]:
        """获取视觉元素"""
        return self._visual_elements.get(element_id)
    
    def get_elements_by_category(self, category: DesignCategory) -> List[VisualElement]:
        """按类别获取视觉元素"""
        return [
            elem for elem in self._visual_elements.values()
            if elem.category == category
        ]
    
    def search_elements(self, query: str) -> List[VisualElement]:
        """搜索视觉元素"""
        query_lower = query.lower()
        results = []
        for elem in self._visual_elements.values():
            if (query_lower in elem.name.lower() or
                query_lower in elem.description.lower() or
                any(query_lower in tag.lower() for tag in elem.tags)):
                results.append(elem)
        return results
    
    # ========================================================================
    # 色彩调色板管理
    # ========================================================================
    
    async def create_color_palette(
        self,
        name: str,
        colors: Optional[List[str]] = None,
        description: str = "",
        mood: str = "",
    ) -> ColorPalette:
        """
        创建色彩调色板
        
        Args:
            name: 调色板名称
            colors: 颜色列表 (十六进制)
            description: 描述
            mood: 情绪/氛围
            
        Returns:
            创建的调色板
        """
        palette_id = f"palette_{uuid4().hex[:8]}"
        palette = ColorPalette(
            palette_id=palette_id,
            name=name,
            colors=colors or [],
            description=description,
            mood=mood,
        )
        
        self._color_palettes[palette_id] = palette
        self._logger.info(f"创建调色板: {name} ({palette_id})")
        
        return palette
    
    def get_color_palette(self, palette_id: str) -> Optional[ColorPalette]:
        """获取调色板"""
        return self._color_palettes.get(palette_id)
    
    def get_all_palettes(self) -> List[ColorPalette]:
        """获取所有调色板"""
        return list(self._color_palettes.values())
    
    # ========================================================================
    # 设计建议生成
    # ========================================================================
    
    async def generate_suggestions(
        self,
        category: DesignCategory,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DesignSuggestion]:
        """
        生成设计建议
        
        Args:
            category: 设计类别
            context: 上下文信息
            
        Returns:
            设计建议列表
        """
        suggestions = []
        context = context or {}
        
        # 基于类别生成建议
        if category == DesignCategory.CHARACTER:
            suggestions.extend(self._generate_character_suggestions(context))
        elif category == DesignCategory.ENVIRONMENT:
            suggestions.extend(self._generate_environment_suggestions(context))
        elif category == DesignCategory.COLOR:
            suggestions.extend(self._generate_color_suggestions(context))
        elif category == DesignCategory.LIGHTING:
            suggestions.extend(self._generate_lighting_suggestions(context))
        
        # 存储建议
        for suggestion in suggestions:
            self._suggestions[suggestion.suggestion_id] = suggestion
        
        return suggestions
    
    def _generate_character_suggestions(self, context: Dict[str, Any]) -> List[DesignSuggestion]:
        """生成角色设计建议"""
        suggestions = []
        
        # 检查是否有角色缺少调色板
        for char in self._characters.values():
            if not char.color_palette:
                suggestions.append(DesignSuggestion(
                    suggestion_id=f"sug_{uuid4().hex[:8]}",
                    category=DesignCategory.CHARACTER,
                    title=f"为角色 {char.name} 创建调色板",
                    description="建议为该角色创建专属的色彩调色板，以保持视觉一致性",
                    rationale="统一的色彩方案有助于角色识别和品牌一致性",
                    priority=3,
                    related_elements=[char.character_id],
                ))
        
        # 检查角色数量
        if len(self._characters) > 5:
            suggestions.append(DesignSuggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                category=DesignCategory.CHARACTER,
                title="创建角色关系图",
                description="角色数量较多，建议创建角色关系图以便管理",
                rationale="清晰的角色关系有助于保持设计一致性",
                priority=2,
            ))
        
        return suggestions
    
    def _generate_environment_suggestions(self, context: Dict[str, Any]) -> List[DesignSuggestion]:
        """生成环境设计建议"""
        suggestions = []
        
        env_elements = self.get_elements_by_category(DesignCategory.ENVIRONMENT)
        if len(env_elements) == 0:
            suggestions.append(DesignSuggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                category=DesignCategory.ENVIRONMENT,
                title="创建主要场景设计",
                description="建议创建项目的主要场景环境设计",
                rationale="环境设计是视觉叙事的重要组成部分",
                priority=4,
            ))
        
        return suggestions
    
    def _generate_color_suggestions(self, context: Dict[str, Any]) -> List[DesignSuggestion]:
        """生成色彩设计建议"""
        suggestions = []
        
        if len(self._color_palettes) == 0:
            suggestions.append(DesignSuggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                category=DesignCategory.COLOR,
                title="创建主色调调色板",
                description="建议创建项目的主色调调色板",
                rationale="统一的色彩方案有助于视觉一致性",
                priority=5,
            ))
        
        return suggestions
    
    def _generate_lighting_suggestions(self, context: Dict[str, Any]) -> List[DesignSuggestion]:
        """生成灯光设计建议"""
        suggestions = []
        
        lighting_elements = self.get_elements_by_category(DesignCategory.LIGHTING)
        if len(lighting_elements) == 0:
            suggestions.append(DesignSuggestion(
                suggestion_id=f"sug_{uuid4().hex[:8]}",
                category=DesignCategory.LIGHTING,
                title="定义灯光风格指南",
                description="建议创建项目的灯光风格指南",
                rationale="一致的灯光风格有助于营造氛围",
                priority=3,
            ))
        
        return suggestions
    
    def get_suggestions(self, category: Optional[DesignCategory] = None) -> List[DesignSuggestion]:
        """获取设计建议"""
        if category:
            return [s for s in self._suggestions.values() if s.category == category]
        return list(self._suggestions.values())
    
    # ========================================================================
    # 风格参考管理
    # ========================================================================
    
    async def add_style_reference(
        self,
        name: str,
        style_type: StyleType,
        description: str = "",
        source: str = "",
        tags: Optional[List[str]] = None,
    ) -> StyleReference:
        """
        添加风格参考
        
        Args:
            name: 参考名称
            style_type: 风格类型
            description: 描述
            source: 来源
            tags: 标签
            
        Returns:
            创建的风格参考
        """
        reference_id = f"ref_{uuid4().hex[:8]}"
        reference = StyleReference(
            reference_id=reference_id,
            name=name,
            style_type=style_type,
            description=description,
            source=source,
            tags=tags or [],
        )
        
        self._style_references[reference_id] = reference
        self._logger.info(f"添加风格参考: {name} ({reference_id})")
        
        return reference
    
    def get_style_reference(self, reference_id: str) -> Optional[StyleReference]:
        """获取风格参考"""
        return self._style_references.get(reference_id)
    
    def get_references_by_style(self, style_type: StyleType) -> List[StyleReference]:
        """按风格类型获取参考"""
        return [
            ref for ref in self._style_references.values()
            if ref.style_type == style_type
        ]
    
    # ========================================================================
    # LLM 集成方法（0-Fix.3）
    # ========================================================================
    
    async def generate_visual_tags(
        self,
        description: str,
        file_type: str = "image"
    ) -> Dict[str, Any]:
        """
        使用 LLM 生成视觉标签
        
        Args:
            description: 内容描述或文件名
            file_type: 文件类型（image, video, document）
        
        Returns:
            包含视觉标签的字典：
            {
                "scene_type": "室内/室外/城市/自然",
                "time": "白天/夜晚/黄昏/黎明",
                "shot_type": "全景/中景/特写/过肩",
                "mood": "紧张/浪漫/悲伤/欢乐/悬疑",
                "action": "对话/追逐/打斗/静态",
                "characters": "单人/双人/群戏/无人",
                "free_tags": ["自由标签1", "自由标签2"],
                "summary": "一句话描述",
                "source": "llm/rule"
            }
        """
        adapter = self._get_llm_adapter()
        
        if adapter:
            try:
                response = await adapter.generate_visual_tags(description, file_type)
                if response.success and response.parsed_data:
                    result = response.parsed_data
                    result["source"] = "llm"
                    self._logger.info(f"LLM 生成视觉标签成功: {description[:30]}...")
                    return result
                else:
                    self._logger.warning(f"LLM 生成视觉标签失败: {response.error_message}")
            except Exception as e:
                self._logger.error(f"LLM 调用异常: {e}")
        
        # 回退：基于规则生成标签
        return self._generate_visual_tags_by_rule(description, file_type)
    
    def _generate_visual_tags_by_rule(
        self,
        description: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        基于规则生成视觉标签（回退方案）
        
        Args:
            description: 内容描述
            file_type: 文件类型
        
        Returns:
            基于规则生成的标签
        """
        desc_lower = description.lower()
        
        # 场景类型检测
        scene_type = "未知"
        if any(kw in desc_lower for kw in ["室内", "房间", "办公室", "indoor", "room"]):
            scene_type = "室内"
        elif any(kw in desc_lower for kw in ["室外", "街道", "公园", "outdoor", "street"]):
            scene_type = "室外"
        elif any(kw in desc_lower for kw in ["城市", "都市", "city", "urban"]):
            scene_type = "城市"
        elif any(kw in desc_lower for kw in ["自然", "森林", "山", "nature", "forest"]):
            scene_type = "自然"
        
        # 时间检测
        time = "未知"
        if any(kw in desc_lower for kw in ["白天", "日间", "day", "morning"]):
            time = "白天"
        elif any(kw in desc_lower for kw in ["夜晚", "夜间", "night", "evening"]):
            time = "夜晚"
        elif any(kw in desc_lower for kw in ["黄昏", "日落", "sunset", "dusk"]):
            time = "黄昏"
        elif any(kw in desc_lower for kw in ["黎明", "日出", "dawn", "sunrise"]):
            time = "黎明"
        
        # 镜头类型检测
        shot_type = "中景"
        if any(kw in desc_lower for kw in ["全景", "远景", "wide", "establishing"]):
            shot_type = "全景"
        elif any(kw in desc_lower for kw in ["特写", "close", "closeup"]):
            shot_type = "特写"
        elif any(kw in desc_lower for kw in ["过肩", "over shoulder"]):
            shot_type = "过肩"
        
        # 情绪检测
        mood = "中性"
        if any(kw in desc_lower for kw in ["紧张", "悬疑", "tense", "suspense"]):
            mood = "紧张"
        elif any(kw in desc_lower for kw in ["浪漫", "温馨", "romantic", "warm"]):
            mood = "浪漫"
        elif any(kw in desc_lower for kw in ["悲伤", "忧郁", "sad", "melancholy"]):
            mood = "悲伤"
        elif any(kw in desc_lower for kw in ["欢乐", "喜悦", "happy", "joyful"]):
            mood = "欢乐"
        
        return {
            "scene_type": scene_type,
            "time": time,
            "shot_type": shot_type,
            "mood": mood,
            "action": "静态",
            "characters": "未知",
            "free_tags": [],
            "summary": description[:50] if len(description) > 50 else description,
            "source": "rule"
        }
    
    async def classify_reference(
        self,
        filename: str,
        file_type: str = "image",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用 LLM 分类参考资料
        
        Args:
            filename: 文件名
            file_type: 文件类型（image, video, document）
            metadata: 文件元数据
        
        Returns:
            分类结果：
            {
                "category": "character/scene/reference",
                "confidence": 0.9,
                "reason": "分类理由",
                "suggested_tags": ["标签1", "标签2"],
                "source": "llm/rule"
            }
        """
        adapter = self._get_llm_adapter()
        
        if adapter:
            try:
                response = await adapter.classify_file(filename, file_type, metadata)
                if response.success and response.parsed_data:
                    result = response.parsed_data
                    result["source"] = "llm"
                    self._logger.info(f"LLM 分类成功: {filename} -> {result.get('category')}")
                    return result
                else:
                    self._logger.warning(f"LLM 分类失败: {response.error_message}")
            except Exception as e:
                self._logger.error(f"LLM 调用异常: {e}")
        
        # 回退：基于规则分类
        return self._classify_reference_by_rule(filename, file_type, metadata)
    
    def _classify_reference_by_rule(
        self,
        filename: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        基于规则分类参考资料（回退方案）
        
        Args:
            filename: 文件名
            file_type: 文件类型
            metadata: 文件元数据
        
        Returns:
            基于规则的分类结果
        """
        filename_lower = filename.lower()
        
        # 角色相关关键词
        character_keywords = [
            "角色", "人物", "character", "char", "人设",
            "portrait", "头像", "avatar", "actor", "演员",
            "costume", "服装", "造型"
        ]
        
        # 场景相关关键词
        scene_keywords = [
            "场景", "scene", "环境", "environment", "背景",
            "background", "location", "地点", "布景", "set",
            "landscape", "风景", "建筑", "building"
        ]
        
        # 检测分类
        category = "reference"  # 默认放入参考界面
        confidence = 0.5
        reason = "无法确定分类，放入参考界面等待用户手动分类"
        suggested_tags = []
        
        if any(kw in filename_lower for kw in character_keywords):
            category = "character"
            confidence = 0.7
            reason = "文件名包含角色相关关键词"
            suggested_tags = ["角色参考"]
        elif any(kw in filename_lower for kw in scene_keywords):
            category = "scene"
            confidence = 0.7
            reason = "文件名包含场景相关关键词"
            suggested_tags = ["场景参考"]
        
        # 如果有元数据，尝试进一步分析
        if metadata:
            if metadata.get("has_face", False):
                category = "character"
                confidence = 0.8
                reason = "检测到人脸"
                suggested_tags.append("人物")
        
        return {
            "category": category,
            "confidence": confidence,
            "reason": reason,
            "suggested_tags": suggested_tags,
            "source": "rule"
        }
    
    # ========================================================================
    # 消息处理器
    # ========================================================================
    
    async def _handle_create_character(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建角色请求"""
        character = await self.create_character(
            name=message.get("name", "Unnamed"),
            description=message.get("description", ""),
            age=message.get("age"),
            gender=message.get("gender"),
            personality=message.get("personality", ""),
            appearance=message.get("appearance", ""),
        )
        return {
            "success": True,
            "character_id": character.character_id,
            "name": character.name,
        }
    
    async def _handle_update_character(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新角色请求"""
        character_id = message.get("character_id")
        if not character_id:
            return {"error": "缺少character_id"}
        
        updates = {k: v for k, v in message.items() if k not in ["action", "character_id"]}
        character = await self.update_character(character_id, **updates)
        
        if character:
            return {"success": True, "character_id": character_id}
        return {"error": "角色不存在"}
    
    async def _handle_get_character(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取角色请求"""
        character_id = message.get("character_id")
        character = self.get_character(character_id)
        
        if character:
            return {
                "success": True,
                "character": {
                    "character_id": character.character_id,
                    "name": character.name,
                    "description": character.description,
                    "status": character.status.value,
                }
            }
        return {"error": "角色不存在"}
    
    async def _handle_create_element(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建视觉元素请求"""
        category_str = message.get("category", "character")
        try:
            category = DesignCategory(category_str)
        except ValueError:
            category = DesignCategory.CHARACTER
        
        element = await self.create_visual_element(
            name=message.get("name", "Unnamed"),
            category=category,
            description=message.get("description", ""),
            tags=message.get("tags", []),
        )
        return {
            "success": True,
            "element_id": element.element_id,
            "name": element.name,
        }
    
    async def _handle_get_suggestions(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取建议请求"""
        category_str = message.get("category")
        category = None
        if category_str:
            try:
                category = DesignCategory(category_str)
            except ValueError:
                pass
        
        # 先生成建议
        if category:
            await self.generate_suggestions(category)
        
        suggestions = self.get_suggestions(category)
        return {
            "success": True,
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "title": s.title,
                    "description": s.description,
                    "priority": s.priority,
                }
                for s in suggestions
            ]
        }
    
    async def _handle_create_palette(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建调色板请求"""
        palette = await self.create_color_palette(
            name=message.get("name", "Unnamed"),
            colors=message.get("colors", []),
            description=message.get("description", ""),
            mood=message.get("mood", ""),
        )
        return {
            "success": True,
            "palette_id": palette.palette_id,
            "name": palette.name,
        }
