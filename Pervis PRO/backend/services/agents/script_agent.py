# -*- coding: utf-8 -*-
"""
Script_Agent 服务（编剧 Agent）

Feature: pervis-project-wizard Phase 2 + Phase 9
Task: 2.2 实现 Script_Agent, 9.1 视觉能力集成

提供剧本相关的 AI 功能：
- 剧本解析（提取场次、角色、动作、对话）
- Logline 生成
- Synopsis 生成
- 人物小传生成
- 角色基础标签生成
- 时长估算
- 剧本结构分析报告
- [新增] 视觉分析（人设图/参考图标签生成）

Requirements: 2.2, 2.4, 2.6, 5.1, 5.2, 5.1.8
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# 视觉标签数据结构（Phase 9 新增）
# ============================================================================

@dataclass
class CharacterVisualTags:
    """角色视觉标签"""
    character_id: str           # 关联的角色 ID
    image_path: str             # 原图路径
    
    # 外观特征
    appearance: Dict[str, str] = field(default_factory=dict)  # 发型、肤色、体型等
    clothing_style: str = ""    # 服装风格
    color_palette: List[str] = field(default_factory=list)    # 配色（RGB 或颜色名）
    accessories: List[str] = field(default_factory=list)      # 配饰/道具
    
    # 元数据
    confidence: float = 0.0     # 识别置信度
    source: str = "vision_model"  # 来源
    confirmed: bool = False     # 是否已确认
    confirmed_at: Optional[datetime] = None  # 确认时间
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "image_path": self.image_path,
            "appearance": self.appearance,
            "clothing_style": self.clothing_style,
            "color_palette": self.color_palette,
            "accessories": self.accessories,
            "confidence": self.confidence,
            "source": self.source,
            "confirmed": self.confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None
        }


@dataclass
class SceneVisualTags:
    """场景视觉标签"""
    scene_id: str               # 关联的场景 ID
    image_path: str             # 原图路径
    
    # 场景特征
    scene_type: str = ""        # 室内/室外
    time_of_day: str = ""       # 日/夜/黄昏/黎明
    lighting: str = ""          # 光线类型
    mood: str = ""              # 氛围
    environment: List[str] = field(default_factory=list)  # 环境元素
    
    # 元数据
    confidence: float = 0.0     # 识别置信度
    source: str = "vision_model"  # 来源
    confirmed: bool = False     # 是否已确认
    confirmed_at: Optional[datetime] = None  # 确认时间
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "image_path": self.image_path,
            "scene_type": self.scene_type,
            "time_of_day": self.time_of_day,
            "lighting": self.lighting,
            "mood": self.mood,
            "environment": self.environment,
            "confidence": self.confidence,
            "source": self.source,
            "confirmed": self.confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None
        }


@dataclass
class ImageAnalysisRequest:
    """图像分析请求"""
    image_id: str
    image_path: str
    image_type: str  # character | scene
    related_id: str  # 关联的角色/场景 ID


@dataclass
class ImageAnalysisResult:
    """图像分析结果"""
    image_id: str
    image_path: str
    image_type: str
    related_id: str
    tags: Dict[str, Any]  # 生成的标签
    confidence: float
    success: bool
    error: Optional[str] = None


@dataclass
class SceneData:
    """场次数据"""
    scene_id: str
    scene_number: int
    heading: str
    location: str
    time_of_day: str
    int_ext: str  # INT/EXT
    description: str = ""
    action: str = ""
    dialogue: List[Dict[str, str]] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    estimated_duration: float = 30.0  # 秒
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "heading": self.heading,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "int_ext": self.int_ext,
            "description": self.description,
            "action": self.action,
            "dialogue": self.dialogue,
            "characters": self.characters,
            "estimated_duration": self.estimated_duration
        }


@dataclass
class CharacterData:
    """角色数据"""
    character_id: str
    name: str
    dialogue_count: int = 0
    first_appearance: int = 1
    scenes: List[int] = field(default_factory=list)
    bio: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "dialogue_count": self.dialogue_count,
            "first_appearance": self.first_appearance,
            "scenes": self.scenes,
            "bio": self.bio,
            "tags": self.tags
        }


@dataclass
class ScriptParseResult:
    """剧本解析结果"""
    scenes: List[SceneData] = field(default_factory=list)
    characters: List[CharacterData] = field(default_factory=list)
    total_scenes: int = 0
    total_characters: int = 0
    estimated_duration: float = 0.0
    logline: str = ""
    synopsis: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenes": [s.to_dict() for s in self.scenes],
            "characters": [c.to_dict() for c in self.characters],
            "total_scenes": self.total_scenes,
            "total_characters": self.total_characters,
            "estimated_duration": self.estimated_duration,
            "logline": self.logline,
            "synopsis": self.synopsis
        }


class ScriptAgentService:
    """
    Script_Agent 服务
    
    编剧 Agent，负责剧本相关的 AI 功能
    """
    
    # 场次标题正则模式
    SCENE_HEADING_PATTERNS = [
        # 英文格式: INT./EXT. LOCATION - TIME
        r'^(INT\.|EXT\.|INT/EXT\.?)\s*[-.]?\s*(.+?)\s*[-–—]\s*(.+?)$',
        # 中文格式: 内景/外景 场景 - 时间
        r'^(内景|外景|内/外景)\s*[-.]?\s*(.+?)\s*[-–—]\s*(.+?)$',
        # 简化格式: 场景编号. 场景名
        r'^(\d+)\.\s*(.+?)$',
        # 中文场次格式: === 第X场 ===
        r'^[=\-]+\s*第([一二三四五六七八九十\d]+)场\s*[=\-]+$',
        # 场景：格式
        r'^场景[：:]\s*(.+?)\s*[-–—]\s*(.+?)$',
    ]
    
    # 角色名正则模式
    CHARACTER_PATTERNS = [
        # 全大写英文名
        r'^([A-Z][A-Z\s]{1,20})$',
        # 中文名后跟括号或冒号（对话格式）
        r'^([\u4e00-\u9fa5]{2,4})\s*[：:]',
        # 中文名后跟括号（表情/动作）
        r'^([\u4e00-\u9fa5]{2,4})\s*[（(]',
        # 中文名独立一行
        r'^([\u4e00-\u9fa5]{2,4})$',
    ]
    
    def __init__(self):
        self._llm_adapter = None
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    def parse_script(self, script_content: str) -> ScriptParseResult:
        """
        解析剧本
        
        提取场次、角色、动作、对话
        
        支持的格式：
        1. === 第X场 === + 场景：xxx - 时间 组合格式
        2. INT./EXT. LOCATION - TIME 英文格式
        3. 内景/外景 场景 - 时间 中文格式
        """
        result = ScriptParseResult()
        
        # 按行分割
        lines = script_content.split('\n')
        
        current_scene = None
        current_character = None
        characters_dict: Dict[str, CharacterData] = {}
        scene_number = 0
        pending_scene_marker = False  # 标记是否刚遇到 === 第X场 ===
        
        for line in lines:
            line = line.strip()
            if not line:
                current_character = None  # 空行重置当前角色
                continue
            
            # 检测场次分隔符 (=== 第X场 ===)
            if self._is_scene_separator(line):
                pending_scene_marker = True
                continue
            
            # 检测场景信息行 (场景：xxx - 时间)
            scene_info = self._match_scene_info(line)
            if scene_info:
                # 保存上一个场次
                if current_scene:
                    result.scenes.append(current_scene)
                
                scene_number += 1
                int_ext, location, time_of_day = scene_info
                
                current_scene = SceneData(
                    scene_id=f"scene_{uuid4().hex[:8]}",
                    scene_number=scene_number,
                    heading=line,
                    location=location.strip(),
                    time_of_day=time_of_day.strip() if time_of_day else "日",
                    int_ext=int_ext.strip() if int_ext else ""
                )
                current_character = None
                pending_scene_marker = False
                continue
            
            # 如果有待处理的场次标记但没有场景信息，跳过
            if pending_scene_marker:
                pending_scene_marker = False
            
            # 检测角色对话行 (角色名：对话内容)
            dialogue_match = self._match_dialogue_line(line)
            if dialogue_match and current_scene:
                char_name, dialogue_text = dialogue_match
                
                # 记录角色
                if char_name not in characters_dict:
                    characters_dict[char_name] = CharacterData(
                        character_id=f"char_{uuid4().hex[:8]}",
                        name=char_name,
                        first_appearance=scene_number
                    )
                
                characters_dict[char_name].dialogue_count += 1
                if scene_number not in characters_dict[char_name].scenes:
                    characters_dict[char_name].scenes.append(scene_number)
                
                if char_name not in current_scene.characters:
                    current_scene.characters.append(char_name)
                
                # 记录对话
                if dialogue_text:
                    current_scene.dialogue.append({
                        "character": char_name,
                        "text": dialogue_text
                    })
                
                current_character = char_name
                continue
            
            # 检测动作描述 (括号开头)
            if line.startswith('（') or line.startswith('('):
                if current_scene:
                    action_text = line.strip('（）()')
                    if current_scene.action:
                        current_scene.action += " " + action_text
                    else:
                        current_scene.action = action_text
                continue
            
            # 其他内容作为动作描述
            if current_scene and not current_character:
                if current_scene.action:
                    current_scene.action += " " + line
                else:
                    current_scene.action = line
        
        # 保存最后一个场次
        if current_scene:
            result.scenes.append(current_scene)
        
        # 整理结果
        result.characters = list(characters_dict.values())
        result.total_scenes = len(result.scenes)
        result.total_characters = len(result.characters)
        
        # 估算总时长
        for scene in result.scenes:
            scene.estimated_duration = self._estimate_scene_duration_basic(scene)
            result.estimated_duration += scene.estimated_duration
        
        return result
    
    def _is_scene_separator(self, line: str) -> bool:
        """检测场次分隔符 (=== 第X场 ===)"""
        return bool(re.match(r'^[=\-]+\s*第[一二三四五六七八九十\d]+场\s*[=\-]+$', line))
    
    def _match_scene_info(self, line: str) -> Optional[Tuple[str, str, str]]:
        """匹配场景信息行"""
        # 场景：格式 (如 "场景：咖啡馆内 - 日")
        match = re.match(r'^场景[：:]\s*(.+?)\s*[-–—]\s*(.+?)$', line)
        if match:
            return "", match.group(1).strip(), match.group(2).strip()
        
        # 英文格式: INT./EXT. LOCATION - TIME
        match = re.match(r'^(INT\.|EXT\.|INT/EXT\.?)\s*[-.]?\s*(.+?)\s*[-–—]\s*(.+?)$', line, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2), match.group(3)
        
        # 中文格式: 内景/外景 场景 - 时间
        match = re.match(r'^(内景|外景|内/外景)\s*[-.]?\s*(.+?)\s*[-–—]\s*(.+?)$', line)
        if match:
            return match.group(1), match.group(2), match.group(3)
        
        return None
    
    def _match_dialogue_line(self, line: str) -> Optional[Tuple[str, str]]:
        """
        匹配对话行
        
        格式: 角色名：对话内容 或 角色名：（动作）对话内容
        
        排除：
        - 时间：xxx (时间信息)
        - 场景：xxx (场景信息)
        """
        # 排除特殊标签
        excluded_prefixes = ['时间', '场景', '地点', '日期', '备注', '说明', '类型', '时长', '导演']
        
        # 匹配 角色名：内容 格式
        match = re.match(r'^([\u4e00-\u9fa5]{2,4})[：:]\s*(.*)$', line)
        if match:
            char_name = match.group(1)
            content = match.group(2).strip()
            
            # 排除特殊标签
            if char_name in excluded_prefixes:
                return None
            
            # 处理括号内的动作描述
            if content.startswith('（') or content.startswith('('):
                # 提取括号后的对话
                bracket_match = re.match(r'^[（(][^）)]*[）)]\s*(.*)$', content)
                if bracket_match:
                    content = bracket_match.group(1)
            
            return char_name, content
        
        return None
    
    def _match_scene_heading(self, line: str) -> Optional[Tuple[str, str, str]]:
        """匹配场次标题 (保留兼容性)"""
        return self._match_scene_info(line)
    
    def _estimate_scene_duration_basic(self, scene: SceneData) -> float:
        """基础时长估算"""
        duration = 0.0
        
        # 对话：每行约 2-3 秒
        duration += len(scene.dialogue) * 2.5
        
        # 动作描述：每 50 字约 5 秒
        if scene.action:
            duration += (len(scene.action) / 50) * 5
        
        # 最小 5 秒，最大 120 秒
        return max(5.0, min(120.0, duration))
    
    async def generate_logline(self, script_content: str) -> Optional[str]:
        """
        生成 Logline（一句话概括）
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            response = await adapter.generate_logline(script_content)
            if response.success and response.parsed_data:
                return response.parsed_data.get("logline")
        except Exception as e:
            logger.error(f"生成 Logline 失败: {e}")
        
        return None
    
    async def generate_synopsis(self, script_content: str) -> Optional[Dict[str, Any]]:
        """
        生成 Synopsis（故事概要）
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            response = await adapter.generate_synopsis(script_content)
            if response.success and response.parsed_data:
                return response.parsed_data
        except Exception as e:
            logger.error(f"生成 Synopsis 失败: {e}")
        
        return None
    
    async def generate_character_bio(
        self,
        character_name: str,
        script_content: str,
        existing_info: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成人物小传
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            response = await adapter.generate_character_bio(
                character_name, script_content, existing_info
            )
            if response.success and response.parsed_data:
                return response.parsed_data
        except Exception as e:
            logger.error(f"生成人物小传失败: {e}")
        
        return None
    
    async def generate_character_tags(
        self,
        character_name: str,
        character_bio: str
    ) -> Optional[Dict[str, str]]:
        """
        生成角色基础标签
        
        标签包括：性别、年龄范围、角色类型等
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            from services.agent_llm_adapter import AgentLLMRequest, AgentType
            
            prompt = f"""根据以下角色信息，生成基础标签。

角色名：{character_name}
人物小传：{character_bio}

请返回 JSON 格式：
{{
  "gender": "男/女/未知",
  "age_range": "儿童/青年/中年/老年",
  "role_type": "主角/配角/龙套",
  "personality": "性格关键词",
  "occupation": "职业"
}}
"""
            response = await adapter.generate(AgentLLMRequest(
                agent_type=AgentType.SCRIPT,
                task_type="generate_character_tags",
                prompt=prompt
            ))
            
            if response.success and response.parsed_data:
                return response.parsed_data
                
        except Exception as e:
            logger.error(f"生成角色标签失败: {e}")
        
        return None
    
    async def estimate_scene_duration(self, scene_content: str) -> Optional[Dict[str, Any]]:
        """
        估算场次时长（使用 LLM）
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            response = await adapter.estimate_scene_duration(scene_content)
            if response.success and response.parsed_data:
                return response.parsed_data
        except Exception as e:
            logger.error(f"估算时长失败: {e}")
        
        return None
    
    async def generate_script_report(self, script_content: str) -> Optional[Dict[str, Any]]:
        """
        生成剧本结构分析报告
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            from services.agent_llm_adapter import AgentLLMRequest, AgentType
            
            prompt = f"""分析以下剧本的结构，生成分析报告。

剧本内容：
{script_content[:5000]}

请返回 JSON 格式：
{{
  "structure": {{
    "act_count": 3,
    "scene_count": 10,
    "estimated_duration_minutes": 15
  }},
  "story_elements": {{
    "protagonist": "主角名",
    "antagonist": "对手名",
    "central_conflict": "核心冲突",
    "theme": "主题"
  }},
  "pacing": {{
    "opening": "开场评价",
    "rising_action": "发展评价",
    "climax": "高潮评价",
    "resolution": "结局评价"
  }},
  "suggestions": ["改进建议1", "改进建议2"],
  "overall_score": 8.0
}}
"""
            response = await adapter.generate(AgentLLMRequest(
                agent_type=AgentType.SCRIPT,
                task_type="generate_script_report",
                prompt=prompt
            ))
            
            if response.success and response.parsed_data:
                return response.parsed_data
                
        except Exception as e:
            logger.error(f"生成剧本报告失败: {e}")
        
        return None

    # ========================================================================
    # Phase 9: 视觉分析能力（新增 2025-12-27）
    # ========================================================================
    
    def _get_vision_provider(self):
        """延迟加载视觉模型 Provider"""
        try:
            from services.ollama_vision import get_vision_provider
            return get_vision_provider()
        except Exception as e:
            logger.error(f"视觉模型 Provider 加载失败: {e}")
            return None
    
    async def analyze_reference_images(
        self,
        images: List[ImageAnalysisRequest]
    ) -> List[ImageAnalysisResult]:
        """
        分析参考图像（人设图/场景参考图）
        
        Phase 9 Task 9.1: Script_Agent 视觉能力集成
        
        Args:
            images: 图像分析请求列表
        
        Returns:
            图像分析结果列表
        """
        results = []
        vision_provider = self._get_vision_provider()
        
        if not vision_provider:
            logger.warning("视觉模型不可用，返回空结果")
            for img in images:
                results.append(ImageAnalysisResult(
                    image_id=img.image_id,
                    image_path=img.image_path,
                    image_type=img.image_type,
                    related_id=img.related_id,
                    tags={},
                    confidence=0.0,
                    success=False,
                    error="视觉模型服务不可用"
                ))
            return results
        
        for img in images:
            try:
                if img.image_type == "character":
                    tags = await self.generate_character_visual_tags(
                        img.image_path, img.related_id
                    )
                elif img.image_type == "scene":
                    tags = await self.generate_scene_visual_tags(
                        img.image_path, img.related_id
                    )
                else:
                    tags = None
                
                if tags:
                    results.append(ImageAnalysisResult(
                        image_id=img.image_id,
                        image_path=img.image_path,
                        image_type=img.image_type,
                        related_id=img.related_id,
                        tags=tags.to_dict() if hasattr(tags, 'to_dict') else tags,
                        confidence=tags.confidence if hasattr(tags, 'confidence') else 0.8,
                        success=True
                    ))
                else:
                    results.append(ImageAnalysisResult(
                        image_id=img.image_id,
                        image_path=img.image_path,
                        image_type=img.image_type,
                        related_id=img.related_id,
                        tags={},
                        confidence=0.0,
                        success=False,
                        error="标签生成失败"
                    ))
                    
            except Exception as e:
                logger.error(f"分析图像失败 {img.image_path}: {e}")
                results.append(ImageAnalysisResult(
                    image_id=img.image_id,
                    image_path=img.image_path,
                    image_type=img.image_type,
                    related_id=img.related_id,
                    tags={},
                    confidence=0.0,
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    async def generate_character_visual_tags(
        self,
        image_path: str,
        character_id: str
    ) -> Optional[CharacterVisualTags]:
        """
        生成角色视觉标签
        
        Phase 9 Task 9.2: 人设/角色视觉标签生成
        
        Args:
            image_path: 图像文件路径
            character_id: 关联的角色 ID
        
        Returns:
            角色视觉标签
        """
        vision_provider = self._get_vision_provider()
        if not vision_provider:
            return None
        
        # 检查视觉模型可用性
        is_available = await vision_provider.check_availability()
        if not is_available:
            logger.warning("视觉模型不可用")
            return None
        
        try:
            # 使用专门的角色分析提示词
            prompt = self._get_character_analysis_prompt()
            result = await vision_provider.analyze_image(image_path, prompt)
            
            if not result or result.get("summary") == "无法分析图像内容":
                return None
            
            # 解析结果并构建 CharacterVisualTags
            tags = CharacterVisualTags(
                character_id=character_id,
                image_path=image_path,
                appearance=self._extract_appearance(result),
                clothing_style=result.get("clothing_style", result.get("服装风格", "")),
                color_palette=self._extract_colors(result),
                accessories=result.get("accessories", result.get("配饰", [])),
                confidence=0.85,
                source="vision_model"
            )
            
            logger.info(f"角色视觉标签生成成功: {character_id}")
            return tags
            
        except Exception as e:
            logger.error(f"生成角色视觉标签失败: {e}")
            return None
    
    async def generate_scene_visual_tags(
        self,
        image_path: str,
        scene_id: str
    ) -> Optional[SceneVisualTags]:
        """
        生成场景视觉标签
        
        Phase 9 Task 9.3: 场景视觉标签生成
        
        Args:
            image_path: 图像文件路径
            scene_id: 关联的场景 ID
        
        Returns:
            场景视觉标签
        """
        vision_provider = self._get_vision_provider()
        if not vision_provider:
            return None
        
        # 检查视觉模型可用性
        is_available = await vision_provider.check_availability()
        if not is_available:
            logger.warning("视觉模型不可用")
            return None
        
        try:
            # 使用专门的场景分析提示词
            prompt = self._get_scene_analysis_prompt()
            result = await vision_provider.analyze_image(image_path, prompt)
            
            if not result or result.get("summary") == "无法分析图像内容":
                return None
            
            # 解析结果并构建 SceneVisualTags
            tags = SceneVisualTags(
                scene_id=scene_id,
                image_path=image_path,
                scene_type=result.get("scene_type", result.get("场景类型", "")),
                time_of_day=result.get("time", result.get("时间", "")),
                lighting=result.get("lighting", result.get("光线", "")),
                mood=result.get("mood", result.get("氛围", "")),
                environment=result.get("environment", result.get("环境元素", [])),
                confidence=0.85,
                source="vision_model"
            )
            
            logger.info(f"场景视觉标签生成成功: {scene_id}")
            return tags
            
        except Exception as e:
            logger.error(f"生成场景视觉标签失败: {e}")
            return None
    
    def _get_character_analysis_prompt(self) -> str:
        """获取角色分析提示词"""
        return """分析这张角色/人设图，提取角色的视觉特征。

请严格按照以下 JSON 格式返回：
{
  "appearance": {
    "hair": "发型和发色描述",
    "skin": "肤色描述",
    "build": "体型描述（如纤细、健壮、普通）",
    "face": "面部特征描述",
    "age_appearance": "外观年龄（如青年、中年）"
  },
  "clothing_style": "服装风格（如现代休闲、古装、制服、运动装）",
  "color_palette": ["主色调1", "主色调2", "主色调3"],
  "accessories": ["配饰1", "配饰2"],
  "distinctive_features": "显著特征描述",
  "summary": "一句话描述这个角色的整体形象"
}

只返回 JSON，不要其他内容。"""
    
    def _get_scene_analysis_prompt(self) -> str:
        """获取场景分析提示词"""
        return """分析这张场景/环境图，提取场景的视觉特征。

请严格按照以下 JSON 格式返回：
{
  "scene_type": "室内/室外/混合",
  "time": "白天/夜晚/黄昏/黎明/未知",
  "lighting": "自然光/人工光/混合光/昏暗/明亮",
  "mood": "温馨/紧张/神秘/欢乐/悲伤/平静/热血",
  "environment": ["环境元素1", "环境元素2", "环境元素3"],
  "architecture_style": "建筑风格（如现代、古典、工业、自然）",
  "color_tone": "整体色调（如暖色调、冷色调、中性）",
  "summary": "一句话描述这个场景"
}

只返回 JSON，不要其他内容。"""
    
    def _extract_appearance(self, result: Dict[str, Any]) -> Dict[str, str]:
        """从分析结果中提取外观信息"""
        appearance = result.get("appearance", {})
        if isinstance(appearance, dict):
            return appearance
        
        # 尝试从其他字段提取
        return {
            "hair": result.get("hair", result.get("发型", "")),
            "skin": result.get("skin", result.get("肤色", "")),
            "build": result.get("build", result.get("体型", "")),
            "face": result.get("face", result.get("面部特征", "")),
            "age_appearance": result.get("age_appearance", result.get("外观年龄", ""))
        }
    
    def _extract_colors(self, result: Dict[str, Any]) -> List[str]:
        """从分析结果中提取配色信息"""
        colors = result.get("color_palette", result.get("配色", []))
        if isinstance(colors, list):
            return colors
        if isinstance(colors, str):
            return [c.strip() for c in colors.split(",")]
        return []


# 全局服务实例
_script_agent_service: Optional[ScriptAgentService] = None


def get_script_agent_service() -> ScriptAgentService:
    """获取 Script_Agent 服务实例"""
    global _script_agent_service
    if _script_agent_service is None:
        _script_agent_service = ScriptAgentService()
    return _script_agent_service
