# -*- coding: utf-8 -*-
"""
编剧Agent (ScriptAgent) - 处理剧本相关任务

Feature: multi-agent-workflow-core, pervis-project-wizard
验证需求: Requirements 3.2 - 剧本时长评估和分析功能
         Requirements 5.1 - Agent 协作内容生成

主要功能:
- 剧本时长评估
- 剧本结构分析
- 场景分解
- 对话分析
- [NEW] Logline 生成（LLM）
- [NEW] Synopsis 生成（LLM）
- [NEW] 人物小传生成（LLM）
"""
import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.core.agent_types import AgentType
from app.core.message_bus import MessageBus

# 添加 Pervis PRO 路径以导入 AgentLLMAdapter
_pervis_pro_path = Path(__file__).parent.parent.parent.parent.parent / "Pervis PRO" / "backend"
if str(_pervis_pro_path) not in sys.path:
    sys.path.insert(0, str(_pervis_pro_path))

logger = logging.getLogger(__name__)


class SceneType(str, Enum):
    """场景类型"""
    INTERIOR = "interior"  # 内景
    EXTERIOR = "exterior"  # 外景
    INT_EXT = "int_ext"    # 内外景


class TimeOfDay(str, Enum):
    """时间段"""
    DAY = "day"
    NIGHT = "night"
    DAWN = "dawn"
    DUSK = "dusk"
    CONTINUOUS = "continuous"


@dataclass
class DialogueLine:
    """对话行"""
    character: str
    text: str
    parenthetical: Optional[str] = None  # 括号内说明
    word_count: int = 0
    estimated_duration_seconds: float = 0.0
    
    def __post_init__(self):
        self.word_count = len(self.text.split())
        # 平均语速: 每分钟150词 = 每秒2.5词
        self.estimated_duration_seconds = self.word_count / 2.5


@dataclass
class ActionLine:
    """动作描述行"""
    text: str
    word_count: int = 0
    estimated_duration_seconds: float = 0.0
    
    def __post_init__(self):
        self.word_count = len(self.text.split())
        # 动作描述: 每行约3-5秒
        self.estimated_duration_seconds = max(3.0, self.word_count / 3.0)


@dataclass
class Scene:
    """场景"""
    scene_id: str
    scene_number: int
    heading: str
    scene_type: SceneType
    location: str
    time_of_day: TimeOfDay
    dialogues: List[DialogueLine] = field(default_factory=list)
    actions: List[ActionLine] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    
    def calculate_duration(self) -> float:
        """计算场景预估时长"""
        dialogue_duration = sum(d.estimated_duration_seconds for d in self.dialogues)
        action_duration = sum(a.estimated_duration_seconds for a in self.actions)
        # 场景转换时间
        transition_time = 2.0
        self.estimated_duration_seconds = dialogue_duration + action_duration + transition_time
        return self.estimated_duration_seconds


@dataclass
class Script:
    """剧本"""
    script_id: str
    title: str
    author: str = ""
    genre: str = ""
    scenes: List[Scene] = field(default_factory=list)
    total_pages: int = 0
    estimated_duration_minutes: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    def calculate_total_duration(self) -> float:
        """计算总时长"""
        total_seconds = sum(scene.calculate_duration() for scene in self.scenes)
        self.estimated_duration_minutes = total_seconds / 60.0
        return self.estimated_duration_minutes


@dataclass
class DurationEstimate:
    """时长评估结果"""
    script_id: str
    total_minutes: float
    total_seconds: float
    scene_count: int
    dialogue_count: int
    action_count: int
    character_count: int
    average_scene_duration: float
    breakdown_by_scene: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.8  # 评估置信度


@dataclass
class ScriptAnalysisResult:
    """剧本分析结果"""
    script_id: str
    title: str
    scene_count: int
    character_list: List[str]
    dialogue_ratio: float  # 对话占比
    action_ratio: float    # 动作占比
    pacing_score: float    # 节奏评分 (0-1)
    complexity_score: float  # 复杂度评分 (0-1)
    duration_estimate: DurationEstimate
    recommendations: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)


# 场景标题正则表达式
# 匹配格式: INT. LOCATION - TIME 或 EXT. LOCATION - TIME
SCENE_HEADING_PATTERN = re.compile(
    r'^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s*(.+?)\s*[-–—]\s*(DAY|NIGHT|DAWN|DUSK|CONTINUOUS|LATER|MOMENTS LATER)?\s*$',
    re.IGNORECASE
)

# 角色名正则表达式 (全大写)
CHARACTER_PATTERN = re.compile(r'^([A-Z][A-Z\s\.\-\']+)(\s*\(.*\))?$')


# ========== LLM 生成结果数据类 ==========

@dataclass
class LoglineResult:
    """Logline 生成结果"""
    logline: str
    confidence: float = 0.8
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SynopsisResult:
    """Synopsis 生成结果"""
    synopsis: str
    word_count: int = 0
    key_plot_points: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CharacterBioResult:
    """人物小传生成结果"""
    name: str
    bio: str
    appearance: str = ""
    personality: List[str] = field(default_factory=list)
    motivation: str = ""
    relationships: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


class ScriptAgent(BaseAgent):
    """
    编剧Agent - 处理剧本相关任务
    
    主要功能:
    - 剧本时长评估
    - 剧本结构分析
    - 场景分解
    - 对话分析
    - LLM 内容生成（Logline, Synopsis, 人物小传）
    """
    
    def __init__(
        self,
        message_bus: MessageBus,
        agent_id: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id or f"script_agent_{uuid4().hex[:8]}",
            agent_type=AgentType.SCRIPT,
            message_bus=message_bus,
        )
        self._scripts: Dict[str, Script] = {}
        self._analysis_cache: Dict[str, ScriptAnalysisResult] = {}
        self._llm_adapter = None  # 延迟加载
        self._logger = logging.getLogger(__name__)
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
                self._logger.info("Script_Agent: LLM 适配器加载成功")
            except ImportError as e:
                self._logger.warning(f"Script_Agent: LLM 适配器加载失败: {e}")
                self._llm_adapter = None
        return self._llm_adapter
    
    async def _on_initialize(self) -> None:
        """初始化编剧Agent"""
        self._logger.info("编剧Agent初始化完成")
    
    async def _on_start(self) -> None:
        """启动编剧Agent"""
        self._logger.info("编剧Agent已启动")
    
    async def _on_stop(self) -> None:
        """停止编剧Agent"""
        self._logger.info("编剧Agent已停止")
    
    async def handle_message(self, message) -> Optional[Dict[str, Any]]:
        """处理普通消息 - 实现抽象方法"""
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = message
        
        if isinstance(content, dict):
            action = content.get("action")
            
            if action == "parse_script":
                return await self._handle_parse_script(content)
            elif action == "estimate_duration":
                return await self._handle_estimate_duration(content)
            elif action == "analyze_script":
                return await self._handle_analyze_script(content)
            elif action == "get_scene":
                return await self._handle_get_scene(content)
        
        return {"error": "未知操作"}
    
    async def handle_protocol_message(self, message) -> Optional[Any]:
        """处理协议消息 - 实现抽象方法"""
        if hasattr(message, 'payload') and hasattr(message.payload, 'data'):
            data = message.payload.data
            return await self.handle_message(data)
        return None

    
    async def _handle_parse_script(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理剧本解析请求"""
        content = message.get("content", "")
        title = message.get("title", "Untitled")
        author = message.get("author", "")
        
        script = await self.parse_script(content, title, author)
        return {
            "success": True,
            "script_id": script.script_id,
            "scene_count": len(script.scenes),
        }
    
    async def _handle_estimate_duration(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理时长评估请求"""
        script_id = message.get("script_id")
        if not script_id or script_id not in self._scripts:
            return {"error": "剧本不存在"}
        
        estimate = await self.estimate_duration(script_id)
        return {
            "success": True,
            "total_minutes": estimate.total_minutes,
            "scene_count": estimate.scene_count,
        }
    
    async def _handle_analyze_script(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理剧本分析请求"""
        script_id = message.get("script_id")
        if not script_id or script_id not in self._scripts:
            return {"error": "剧本不存在"}
        
        result = await self.analyze_script(script_id)
        return {
            "success": True,
            "analysis": {
                "scene_count": result.scene_count,
                "character_count": len(result.character_list),
                "pacing_score": result.pacing_score,
                "complexity_score": result.complexity_score,
            }
        }
    
    async def _handle_get_scene(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取场景请求"""
        script_id = message.get("script_id")
        scene_number = message.get("scene_number")
        
        scene = self.get_scene(script_id, scene_number)
        if not scene:
            return {"error": "场景不存在"}
        
        return {
            "success": True,
            "scene": {
                "scene_id": scene.scene_id,
                "heading": scene.heading,
                "location": scene.location,
                "duration_seconds": scene.estimated_duration_seconds,
            }
        }

    async def parse_script(
        self,
        content: str,
        title: str = "Untitled",
        author: str = "",
        genre: str = "",
    ) -> Script:
        """
        解析剧本内容
        
        Args:
            content: 剧本文本内容
            title: 剧本标题
            author: 作者
            genre: 类型
            
        Returns:
            解析后的Script对象
        """
        script_id = f"script_{uuid4().hex[:8]}"
        script = Script(
            script_id=script_id,
            title=title,
            author=author,
            genre=genre,
        )
        
        lines = content.strip().split('\n')
        current_scene: Optional[Scene] = None
        scene_number = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # 检查是否是场景标题
            scene_match = SCENE_HEADING_PATTERN.match(line)
            if scene_match:
                # 保存之前的场景
                if current_scene:
                    current_scene.calculate_duration()
                    script.scenes.append(current_scene)
                
                scene_number += 1
                scene_type = self._parse_scene_type(scene_match.group(1))
                location = scene_match.group(2).strip()
                time_of_day = self._parse_time_of_day(scene_match.group(3))
                
                current_scene = Scene(
                    scene_id=f"scene_{uuid4().hex[:8]}",
                    scene_number=scene_number,
                    heading=line,
                    scene_type=scene_type,
                    location=location,
                    time_of_day=time_of_day,
                )
                i += 1
                continue
            
            # 如果还没有场景，跳过
            if not current_scene:
                i += 1
                continue
            
            # 检查是否是角色名 (对话开始)
            char_match = CHARACTER_PATTERN.match(line)
            if char_match and i + 1 < len(lines):
                character = char_match.group(1).strip()
                parenthetical = None
                
                # 检查下一行是否是括号说明
                next_line = lines[i + 1].strip()
                if next_line.startswith('(') and next_line.endswith(')'):
                    parenthetical = next_line[1:-1]
                    i += 1
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                    else:
                        next_line = ""
                
                # 收集对话文本
                dialogue_text = []
                i += 1
                while i < len(lines):
                    dl = lines[i].strip()
                    if not dl or SCENE_HEADING_PATTERN.match(dl) or CHARACTER_PATTERN.match(dl):
                        break
                    dialogue_text.append(dl)
                    i += 1
                
                if dialogue_text:
                    dialogue = DialogueLine(
                        character=character,
                        text=' '.join(dialogue_text),
                        parenthetical=parenthetical,
                    )
                    current_scene.dialogues.append(dialogue)
                    if character not in current_scene.characters:
                        current_scene.characters.append(character)
                continue
            
            # 否则是动作描述
            action = ActionLine(text=line)
            current_scene.actions.append(action)
            i += 1
        
        # 保存最后一个场景
        if current_scene:
            current_scene.calculate_duration()
            script.scenes.append(current_scene)
        
        # 计算总时长
        script.calculate_total_duration()
        script.analyzed_at = datetime.now()
        
        # 存储剧本
        self._scripts[script_id] = script
        
        return script

    
    def _parse_scene_type(self, prefix: str) -> SceneType:
        """解析场景类型"""
        prefix = prefix.upper().strip('.')
        if prefix in ('INT', 'I'):
            return SceneType.INTERIOR
        elif prefix in ('EXT', 'E'):
            return SceneType.EXTERIOR
        else:
            return SceneType.INT_EXT
    
    def _parse_time_of_day(self, time_str: Optional[str]) -> TimeOfDay:
        """解析时间段"""
        if not time_str:
            return TimeOfDay.DAY
        
        time_str = time_str.upper()
        if 'NIGHT' in time_str:
            return TimeOfDay.NIGHT
        elif 'DAWN' in time_str:
            return TimeOfDay.DAWN
        elif 'DUSK' in time_str:
            return TimeOfDay.DUSK
        elif 'CONTINUOUS' in time_str or 'LATER' in time_str:
            return TimeOfDay.CONTINUOUS
        else:
            return TimeOfDay.DAY
    
    async def estimate_duration(self, script_id: str) -> DurationEstimate:
        """
        评估剧本时长
        
        Args:
            script_id: 剧本ID
            
        Returns:
            时长评估结果
        """
        script = self._scripts.get(script_id)
        if not script:
            raise ValueError(f"剧本不存在: {script_id}")
        
        # 重新计算时长
        script.calculate_total_duration()
        
        # 统计数据
        total_dialogues = sum(len(s.dialogues) for s in script.scenes)
        total_actions = sum(len(s.actions) for s in script.scenes)
        all_characters = set()
        for scene in script.scenes:
            all_characters.update(scene.characters)
        
        # 场景时长分解
        breakdown = {
            scene.scene_id: scene.estimated_duration_seconds
            for scene in script.scenes
        }
        
        avg_scene_duration = (
            script.estimated_duration_minutes * 60 / len(script.scenes)
            if script.scenes else 0
        )
        
        return DurationEstimate(
            script_id=script_id,
            total_minutes=script.estimated_duration_minutes,
            total_seconds=script.estimated_duration_minutes * 60,
            scene_count=len(script.scenes),
            dialogue_count=total_dialogues,
            action_count=total_actions,
            character_count=len(all_characters),
            average_scene_duration=avg_scene_duration,
            breakdown_by_scene=breakdown,
        )
    
    async def analyze_script(self, script_id: str) -> ScriptAnalysisResult:
        """
        分析剧本结构
        
        Args:
            script_id: 剧本ID
            
        Returns:
            剧本分析结果
        """
        script = self._scripts.get(script_id)
        if not script:
            raise ValueError(f"剧本不存在: {script_id}")
        
        # 获取时长评估
        duration_estimate = await self.estimate_duration(script_id)
        
        # 收集所有角色
        all_characters = set()
        for scene in script.scenes:
            all_characters.update(scene.characters)
        
        # 计算对话和动作占比
        total_dialogue_duration = sum(
            sum(d.estimated_duration_seconds for d in s.dialogues)
            for s in script.scenes
        )
        total_action_duration = sum(
            sum(a.estimated_duration_seconds for a in s.actions)
            for s in script.scenes
        )
        total_duration = total_dialogue_duration + total_action_duration
        
        dialogue_ratio = total_dialogue_duration / total_duration if total_duration > 0 else 0
        action_ratio = total_action_duration / total_duration if total_duration > 0 else 0
        
        # 计算节奏评分 (基于场景长度变化)
        pacing_score = self._calculate_pacing_score(script)
        
        # 计算复杂度评分 (基于角色数量、场景数量等)
        complexity_score = self._calculate_complexity_score(script, len(all_characters))
        
        # 生成建议
        recommendations = self._generate_recommendations(
            script, dialogue_ratio, pacing_score, complexity_score
        )
        
        result = ScriptAnalysisResult(
            script_id=script_id,
            title=script.title,
            scene_count=len(script.scenes),
            character_list=list(all_characters),
            dialogue_ratio=dialogue_ratio,
            action_ratio=action_ratio,
            pacing_score=pacing_score,
            complexity_score=complexity_score,
            duration_estimate=duration_estimate,
            recommendations=recommendations,
        )
        
        # 缓存分析结果
        self._analysis_cache[script_id] = result
        
        return result

    
    def _calculate_pacing_score(self, script: Script) -> float:
        """计算节奏评分"""
        if len(script.scenes) < 2:
            return 0.5
        
        durations = [s.estimated_duration_seconds for s in script.scenes]
        avg_duration = sum(durations) / len(durations)
        
        # 计算变异系数 (标准差/平均值)
        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        cv = std_dev / avg_duration if avg_duration > 0 else 0
        
        # 适度的变化是好的 (cv在0.3-0.5之间最佳)
        if cv < 0.1:
            return 0.4  # 太单调
        elif cv < 0.3:
            return 0.6 + (cv - 0.1) * 2  # 逐渐变好
        elif cv < 0.5:
            return 1.0 - (cv - 0.3) * 0.5  # 最佳范围
        else:
            return max(0.3, 0.9 - (cv - 0.5) * 0.6)  # 变化太大
    
    def _calculate_complexity_score(self, script: Script, character_count: int) -> float:
        """计算复杂度评分"""
        # 基于多个因素
        scene_factor = min(1.0, len(script.scenes) / 50)  # 50场景为满分
        character_factor = min(1.0, character_count / 20)  # 20角色为满分
        
        # 场景类型多样性
        scene_types = set(s.scene_type for s in script.scenes)
        type_factor = len(scene_types) / 3  # 3种类型为满分
        
        # 时间段多样性
        time_periods = set(s.time_of_day for s in script.scenes)
        time_factor = len(time_periods) / 5  # 5种时间段为满分
        
        return (scene_factor + character_factor + type_factor + time_factor) / 4
    
    def _generate_recommendations(
        self,
        script: Script,
        dialogue_ratio: float,
        pacing_score: float,
        complexity_score: float,
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if dialogue_ratio > 0.7:
            recommendations.append("对话占比较高，考虑增加更多视觉动作描述")
        elif dialogue_ratio < 0.3:
            recommendations.append("动作描述较多，考虑增加角色对话以增强情感表达")
        
        if pacing_score < 0.5:
            recommendations.append("场景节奏较为单一，考虑调整场景长度以增加变化")
        
        if complexity_score < 0.3:
            recommendations.append("剧本结构相对简单，可以考虑增加场景或角色丰富度")
        elif complexity_score > 0.8:
            recommendations.append("剧本结构较为复杂，确保观众能够跟上故事发展")
        
        if len(script.scenes) < 5:
            recommendations.append("场景数量较少，考虑是否需要扩展故事")
        
        return recommendations
    
    def get_script(self, script_id: str) -> Optional[Script]:
        """获取剧本"""
        return self._scripts.get(script_id)
    
    def get_scene(self, script_id: str, scene_number: int) -> Optional[Scene]:
        """获取指定场景"""
        script = self._scripts.get(script_id)
        if not script:
            return None
        
        for scene in script.scenes:
            if scene.scene_number == scene_number:
                return scene
        return None
    
    def get_all_scripts(self) -> List[Script]:
        """获取所有剧本"""
        return list(self._scripts.values())
    
    def get_analysis(self, script_id: str) -> Optional[ScriptAnalysisResult]:
        """获取缓存的分析结果"""
        return self._analysis_cache.get(script_id)


    # ========== LLM 生成方法 (0-Fix.2) ==========
    
    async def generate_logline(self, script_content: str) -> LoglineResult:
        """
        使用 LLM 生成 Logline（一句话概括）
        
        Args:
            script_content: 剧本内容
        
        Returns:
            LoglineResult 对象
        
        Requirements: 5.1 - Logline 生成
        """
        adapter = self._get_llm_adapter()
        
        if adapter is None:
            # 回退到简单的规则生成
            self._logger.warning("LLM 适配器不可用，使用规则生成 Logline")
            return self._generate_logline_fallback(script_content)
        
        try:
            response = await adapter.generate_logline(script_content)
            
            if response.success and response.parsed_data:
                data = response.parsed_data
                return LoglineResult(
                    logline=data.get("logline", ""),
                    confidence=data.get("confidence", 0.8)
                )
            else:
                self._logger.warning(f"LLM 生成 Logline 失败: {response.error_message}")
                return self._generate_logline_fallback(script_content)
                
        except Exception as e:
            self._logger.error(f"generate_logline 异常: {e}")
            return self._generate_logline_fallback(script_content)
    
    def _generate_logline_fallback(self, script_content: str) -> LoglineResult:
        """Logline 回退生成（无 LLM 时使用）"""
        # 提取第一个场景的描述作为简单 Logline
        lines = script_content.strip().split('\n')[:20]
        first_action = ""
        for line in lines:
            line = line.strip()
            if line and not SCENE_HEADING_PATTERN.match(line) and not CHARACTER_PATTERN.match(line):
                first_action = line[:100]
                break
        
        return LoglineResult(
            logline=first_action or "一个关于冒险与发现的故事。",
            confidence=0.3
        )
    
    async def generate_synopsis(self, script_content: str) -> SynopsisResult:
        """
        使用 LLM 生成 Synopsis（故事概要）
        
        Args:
            script_content: 剧本内容
        
        Returns:
            SynopsisResult 对象
        
        Requirements: 5.1 - Synopsis 生成
        """
        adapter = self._get_llm_adapter()
        
        if adapter is None:
            self._logger.warning("LLM 适配器不可用，使用规则生成 Synopsis")
            return self._generate_synopsis_fallback(script_content)
        
        try:
            response = await adapter.generate_synopsis(script_content)
            
            if response.success and response.parsed_data:
                data = response.parsed_data
                return SynopsisResult(
                    synopsis=data.get("synopsis", ""),
                    word_count=data.get("word_count", 0),
                    key_plot_points=data.get("key_plot_points", [])
                )
            else:
                self._logger.warning(f"LLM 生成 Synopsis 失败: {response.error_message}")
                return self._generate_synopsis_fallback(script_content)
                
        except Exception as e:
            self._logger.error(f"generate_synopsis 异常: {e}")
            return self._generate_synopsis_fallback(script_content)
    
    def _generate_synopsis_fallback(self, script_content: str) -> SynopsisResult:
        """Synopsis 回退生成（无 LLM 时使用）"""
        # 提取所有场景标题作为简单概要
        lines = script_content.strip().split('\n')
        scene_headings = []
        for line in lines:
            line = line.strip()
            if SCENE_HEADING_PATTERN.match(line):
                scene_headings.append(line)
        
        synopsis = "故事发生在以下场景中：\n" + "\n".join(scene_headings[:10])
        
        return SynopsisResult(
            synopsis=synopsis,
            word_count=len(synopsis),
            key_plot_points=scene_headings[:5]
        )
    
    async def generate_character_bio(
        self,
        character_name: str,
        script_content: str,
        existing_info: Optional[Dict[str, Any]] = None
    ) -> CharacterBioResult:
        """
        使用 LLM 生成人物小传
        
        Args:
            character_name: 角色名称
            script_content: 剧本内容
            existing_info: 已有的角色信息
        
        Returns:
            CharacterBioResult 对象
        
        Requirements: 5.1 - 人物小传生成
        """
        adapter = self._get_llm_adapter()
        
        if adapter is None:
            self._logger.warning("LLM 适配器不可用，使用规则生成人物小传")
            return self._generate_character_bio_fallback(character_name, script_content)
        
        try:
            response = await adapter.generate_character_bio(
                character_name, 
                script_content,
                existing_info
            )
            
            if response.success and response.parsed_data:
                data = response.parsed_data
                return CharacterBioResult(
                    name=data.get("name", character_name),
                    bio=data.get("bio", ""),
                    appearance=data.get("appearance", ""),
                    personality=data.get("personality", []),
                    motivation=data.get("motivation", ""),
                    relationships=data.get("relationships", []),
                    tags=data.get("tags", {})
                )
            else:
                self._logger.warning(f"LLM 生成人物小传失败: {response.error_message}")
                return self._generate_character_bio_fallback(character_name, script_content)
                
        except Exception as e:
            self._logger.error(f"generate_character_bio 异常: {e}")
            return self._generate_character_bio_fallback(character_name, script_content)
    
    def _generate_character_bio_fallback(
        self,
        character_name: str,
        script_content: str
    ) -> CharacterBioResult:
        """人物小传回退生成（无 LLM 时使用）"""
        # 统计角色出现次数和对话
        lines = script_content.strip().split('\n')
        dialogue_count = 0
        sample_dialogues = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if CHARACTER_PATTERN.match(line) and character_name.upper() in line.upper():
                dialogue_count += 1
                # 获取下一行作为对话样本
                if i + 1 < len(lines) and len(sample_dialogues) < 3:
                    next_line = lines[i + 1].strip()
                    if next_line and not SCENE_HEADING_PATTERN.match(next_line):
                        sample_dialogues.append(next_line[:50])
        
        role_type = "主角" if dialogue_count > 10 else ("配角" if dialogue_count > 3 else "龙套")
        
        return CharacterBioResult(
            name=character_name,
            bio=f"{character_name} 是故事中的{role_type}，共有 {dialogue_count} 段对话。",
            appearance="待补充",
            personality=["待分析"],
            motivation="待分析",
            relationships=[],
            tags={"role_type": role_type, "dialogue_count": str(dialogue_count)}
        )
