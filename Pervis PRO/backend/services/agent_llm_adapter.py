# -*- coding: utf-8 -*-
"""
Agent LLM 适配层

统一 Pervis PRO 和 multi-agent-workflow 的 LLM 调用接口。
为 Agent 提供简化的 LLM 调用方法，支持 Gemini 和 Ollama 双 Provider。

解决问题: P0-1, P0-2
Requirements: 5.1, 5.3, 5.5
"""
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 类型枚举"""
    SCRIPT = "script_agent"      # 编剧 Agent
    ART = "art_agent"            # 美术 Agent
    DIRECTOR = "director_agent"  # 导演 Agent
    PM = "pm_agent"              # 项目管理 Agent
    MARKET = "market_agent"      # 市场分析 Agent
    STORYBOARD = "storyboard_agent"  # 故事板 Agent
    SYSTEM = "system_agent"      # 系统校验 Agent


@dataclass
class AgentLLMRequest:
    """Agent LLM 请求"""
    agent_type: AgentType
    task_type: str  # generate_logline, generate_synopsis, classify_file, etc.
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    json_mode: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class AgentLLMResponse:
    """Agent LLM 响应"""
    id: str
    agent_type: AgentType
    task_type: str
    content: str
    parsed_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def data(self) -> Dict[str, Any]:
        """获取解析后的数据"""
        return self.parsed_data or {}


class AgentLLMAdapter:
    """
    Agent LLM 适配器
    
    统一封装 Pervis PRO 的 LLMProvider，为 Agent 提供简化的调用接口。
    支持 Gemini 和 Ollama 双 Provider，自动回退。
    """
    
    def __init__(self):
        self._provider = None
        self._initialized = False
    
    def _get_provider(self):
        """延迟加载 LLM Provider"""
        if self._provider is None:
            from services.llm_provider import get_llm_provider
            self._provider = get_llm_provider()
            self._initialized = True
            logger.info(f"AgentLLMAdapter 初始化完成: {type(self._provider).__name__}")
        return self._provider
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    async def generate(self, request: AgentLLMRequest) -> AgentLLMResponse:
        """
        通用生成方法
        
        Args:
            request: Agent LLM 请求
        
        Returns:
            Agent LLM 响应
        """
        response_id = str(uuid4())
        
        try:
            provider = self._get_provider()
            
            # 构建系统提示
            system_prompt = self._build_system_prompt(request.agent_type, request.task_type)
            
            # 调用 LLM
            if hasattr(provider, '_chat_completion'):
                # OllamaProvider
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.prompt}
                ]
                result = await provider._chat_completion(messages, json_mode=request.json_mode)
            else:
                # GeminiProvider - 使用 generate_json 或 generate_text
                if request.json_mode:
                    full_prompt = f"{system_prompt}\n\n{request.prompt}"
                    result = await provider.client.generate_json(full_prompt)
                else:
                    full_prompt = f"{system_prompt}\n\n{request.prompt}"
                    text_result = await provider.client.generate_text(full_prompt)
                    result = {"content": text_result.get("data", {}).get("text", "")}
            
            # 解析响应
            if isinstance(result, dict):
                if result.get("status") == "error":
                    return AgentLLMResponse(
                        id=response_id,
                        agent_type=request.agent_type,
                        task_type=request.task_type,
                        content="",
                        success=False,
                        error_message=result.get("message", "Unknown error")
                    )
                
                # 提取内容
                content = result.get("content", "")
                parsed_data = result if request.json_mode else None
                
                # 如果是 JSON 模式但 content 为空，整个 result 就是解析后的数据
                if request.json_mode and not content and "status" not in result:
                    parsed_data = result
                    content = json.dumps(result, ensure_ascii=False)
                
                return AgentLLMResponse(
                    id=response_id,
                    agent_type=request.agent_type,
                    task_type=request.task_type,
                    content=content,
                    parsed_data=parsed_data,
                    success=True
                )
            else:
                return AgentLLMResponse(
                    id=response_id,
                    agent_type=request.agent_type,
                    task_type=request.task_type,
                    content=str(result),
                    success=True
                )
                
        except Exception as e:
            logger.error(f"AgentLLMAdapter.generate 失败: {e}")
            return AgentLLMResponse(
                id=response_id,
                agent_type=request.agent_type,
                task_type=request.task_type,
                content="",
                success=False,
                error_message=str(e)
            )
    
    def _build_system_prompt(self, agent_type: AgentType, task_type: str) -> str:
        """构建系统提示"""
        prompts = {
            AgentType.SCRIPT: """你是 Pervis PRO 的编剧 Agent (Script_Agent)。
你的职责是：
- 解析剧本，提取场次、角色、对话
- 生成 Logline（一句话概括）
- 生成 Synopsis（故事概要）
- 生成人物小传
- 估算场次时长
请以专业编剧的视角提供高质量的内容。""",
            
            AgentType.ART: """你是 Pervis PRO 的美术 Agent (Art_Agent)。
你的职责是：
- 分析视觉风格
- 生成素材标签（内容、风格、技术）
- 分类参考资料（角色/场景/参考）
- 生成角色和场景的视觉描述
请以专业美术指导的视角提供高质量的内容。""",
            
            AgentType.DIRECTOR: """你是 Pervis PRO 的导演 Agent (Director_Agent)。
你的职责是：
- 审核其他 Agent 的输出
- 检查内容与项目规格的一致性
- 检查艺术风格的一致性
- 对比历史版本，避免重复错误
请以专业导演的视角提供审核建议。""",
            
            AgentType.PM: """你是 Pervis PRO 的项目管理 Agent (PM_Agent)。
你的职责是：
- 管理项目上下文
- 记录版本历史
- 生成版本命名
请以专业项目经理的视角管理项目信息。""",
            
            AgentType.MARKET: """你是 Pervis PRO 的市场分析 Agent (Market_Agent)。
你的职责是：
- 分析目标受众
- 提供市场定位建议
- 进行竞品分析
- 推荐发行渠道
请以专业市场分析师的视角提供动态分析。""",
            
            AgentType.STORYBOARD: """你是 Pervis PRO 的故事板 Agent (Storyboard_Agent)。
你的职责是：
- 基于场次描述召回匹配素材
- 生成搜索关键词
- 分析素材与场景的匹配度
请以专业故事板设计师的视角提供建议。""",
            
            AgentType.SYSTEM: """你是 Pervis PRO 的系统校验 Agent (System_Agent)。
你的职责是：
- 检查标签一致性
- 检测矛盾标签
- 验证数据完整性
请以严格的质量检查员视角进行校验。"""
        }
        
        return prompts.get(agent_type, "你是一个专业的 AI 助手。")


    # ========== Script_Agent 专用方法 ==========
    
    async def generate_logline(self, script_content: str) -> AgentLLMResponse:
        """
        生成 Logline（一句话概括）
        
        Args:
            script_content: 剧本内容
        
        Returns:
            包含 logline 的响应
        """
        prompt = f"""请根据以下剧本内容，生成一句话概括（Logline）。

剧本内容：
{script_content[:3000]}  # 限制长度

要求：
1. 一句话概括整个故事
2. 包含主角、冲突、目标
3. 简洁有力，吸引观众
4. 使用中文

请返回 JSON 格式：
{{
  "logline": "一句话概括",
  "confidence": 0.9
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.SCRIPT,
            task_type="generate_logline",
            prompt=prompt
        ))
    
    async def generate_synopsis(self, script_content: str) -> AgentLLMResponse:
        """
        生成 Synopsis（故事概要）
        
        Args:
            script_content: 剧本内容
        
        Returns:
            包含 synopsis 的响应
        """
        prompt = f"""请根据以下剧本内容，生成故事概要（Synopsis）。

剧本内容：
{script_content[:5000]}  # 限制长度

要求：
1. 概述完整故事线
2. 包含开端、发展、高潮、结局
3. 突出主要角色和冲突
4. 200-500字
5. 使用中文

请返回 JSON 格式：
{{
  "synopsis": "故事概要内容",
  "word_count": 300,
  "key_plot_points": ["情节点1", "情节点2", "情节点3"]
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.SCRIPT,
            task_type="generate_synopsis",
            prompt=prompt
        ))
    
    async def generate_character_bio(
        self, 
        character_name: str, 
        script_content: str,
        existing_info: Optional[Dict[str, Any]] = None
    ) -> AgentLLMResponse:
        """
        生成人物小传
        
        Args:
            character_name: 角色名称
            script_content: 剧本内容
            existing_info: 已有的角色信息
        
        Returns:
            包含人物小传的响应
        """
        existing_str = json.dumps(existing_info, ensure_ascii=False) if existing_info else "无"
        
        prompt = f"""请根据以下剧本内容，为角色 "{character_name}" 生成人物小传。

剧本内容：
{script_content[:4000]}

已有角色信息：
{existing_str}

要求：
1. 分析角色在剧本中的行为和对话
2. 推断角色的背景、性格、动机
3. 包含外貌描述、性格特点、人物关系
4. 100-300字
5. 使用中文

请返回 JSON 格式：
{{
  "name": "{character_name}",
  "bio": "人物小传内容",
  "appearance": "外貌描述",
  "personality": ["性格特点1", "性格特点2"],
  "motivation": "角色动机",
  "relationships": ["与其他角色的关系"],
  "tags": {{
    "gender": "男/女/未知",
    "age_range": "年龄范围",
    "role_type": "主角/配角/龙套"
  }}
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.SCRIPT,
            task_type="generate_character_bio",
            prompt=prompt,
            context={"character_name": character_name}
        ))
    
    async def estimate_scene_duration(self, scene_content: str) -> AgentLLMResponse:
        """
        估算场次时长
        
        Args:
            scene_content: 场次内容
        
        Returns:
            包含时长估算的响应
        """
        prompt = f"""请根据以下场次内容，估算该场次的时长。

场次内容：
{scene_content}

估算规则：
1. 对话：每行约 2-3 秒
2. 动作描述：根据复杂度 3-10 秒
3. 场景转换：约 2 秒
4. 情绪渲染：根据需要 3-5 秒

请返回 JSON 格式：
{{
  "duration_seconds": 30,
  "breakdown": {{
    "dialogue": 15,
    "action": 10,
    "transition": 2,
    "atmosphere": 3
  }},
  "confidence": 0.8,
  "notes": "估算说明"
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.SCRIPT,
            task_type="estimate_scene_duration",
            prompt=prompt
        ))
    
    # ========== Art_Agent 专用方法 ==========
    
    async def classify_file(
        self, 
        filename: str, 
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentLLMResponse:
        """
        分类文件（角色/场景/参考）
        
        Args:
            filename: 文件名
            file_type: 文件类型（image, video, document）
            metadata: 文件元数据
        
        Returns:
            包含分类结果的响应
        """
        metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else "无"
        
        prompt = f"""请根据以下文件信息，判断该文件应该分类到哪个界面。

文件名：{filename}
文件类型：{file_type}
元数据：{metadata_str}

分类规则：
1. 角色相关（人物照片、人设图、角色参考）→ "character"
2. 场景相关（场景图、环境参考、布景图）→ "scene"
3. 无法确定 → "reference"（等待用户手动分类）

请返回 JSON 格式：
{{
  "category": "character/scene/reference",
  "confidence": 0.9,
  "reason": "分类理由",
  "suggested_tags": ["标签1", "标签2"]
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.ART,
            task_type="classify_file",
            prompt=prompt,
            context={"filename": filename, "file_type": file_type}
        ))
    
    async def generate_visual_tags(
        self, 
        description: str,
        file_type: str = "image"
    ) -> AgentLLMResponse:
        """
        生成视觉标签
        
        Args:
            description: 内容描述或文件名
            file_type: 文件类型
        
        Returns:
            包含标签的响应
        """
        prompt = f"""请根据以下描述，生成结构化的视觉标签。

描述：{description}
文件类型：{file_type}

请返回 JSON 格式：
{{
  "scene_type": "室内/室外/城市/自然",
  "time": "白天/夜晚/黄昏/黎明",
  "shot_type": "全景/中景/特写/过肩",
  "mood": "紧张/浪漫/悲伤/欢乐/悬疑",
  "action": "对话/追逐/打斗/静态",
  "characters": "单人/双人/群戏/无人",
  "free_tags": ["自由标签1", "自由标签2"],
  "summary": "一句话描述"
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.ART,
            task_type="generate_visual_tags",
            prompt=prompt
        ))
    
    # ========== Director_Agent 专用方法 ==========
    
    async def review_content(
        self,
        content: Any,
        content_type: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> AgentLLMResponse:
        """
        审核内容
        
        Args:
            content: 待审核内容
            content_type: 内容类型（logline, synopsis, character_bio, etc.）
            project_context: 项目上下文
        
        Returns:
            包含审核结果的响应
        """
        content_str = json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)
        context_str = json.dumps(project_context, ensure_ascii=False) if project_context else "无"
        
        prompt = f"""请审核以下内容，检查是否符合项目要求。

内容类型：{content_type}
待审核内容：
{content_str}

项目上下文：
{context_str}

审核要点：
1. 内容是否完整、不为空
2. 字数是否在合理范围内
3. 格式是否正确
4. 是否与项目规格一致（时长、画幅、帧率）
5. 是否与已确定的艺术风格一致

请返回 JSON 格式：
{{
  "status": "approved/suggestions/rejected",
  "passed_checks": ["通过的检查项"],
  "failed_checks": ["未通过的检查项"],
  "suggestions": ["改进建议"],
  "reason": "审核理由",
  "confidence": 0.9
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.DIRECTOR,
            task_type="review_content",
            prompt=prompt,
            context={"content_type": content_type}
        ))
    
    async def check_style_consistency(
        self,
        content: Any,
        style_context: Dict[str, Any]
    ) -> AgentLLMResponse:
        """
        检查艺术风格一致性
        
        Args:
            content: 待检查内容
            style_context: 艺术风格上下文
        
        Returns:
            包含检查结果的响应
        """
        content_str = json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)
        style_str = json.dumps(style_context, ensure_ascii=False)
        
        prompt = f"""请检查以下内容是否符合项目的艺术风格。

待检查内容：
{content_str}

项目艺术风格：
{style_str}

请返回 JSON 格式：
{{
  "is_consistent": true/false,
  "consistency_score": 0.9,
  "matching_elements": ["匹配的元素"],
  "conflicting_elements": ["冲突的元素"],
  "suggestions": ["调整建议"]
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.DIRECTOR,
            task_type="check_style_consistency",
            prompt=prompt
        ))
    
    # ========== Market_Agent 专用方法 ==========
    
    async def analyze_market(
        self,
        project_data: Dict[str, Any]
    ) -> AgentLLMResponse:
        """
        市场分析
        
        Args:
            project_data: 项目数据
        
        Returns:
            包含市场分析的响应
        """
        project_str = json.dumps(project_data, ensure_ascii=False)
        
        prompt = f"""请根据以下项目信息，进行专业的市场分析。

项目信息：
{project_str}

请提供动态分析（非静态案例），返回 JSON 格式：
{{
  "audience": {{
    "primary": {{
      "age_range": "18-35",
      "gender": "男性为主",
      "interests": ["兴趣1", "兴趣2"]
    }},
    "secondary": {{
      "age_range": "35-50",
      "gender": "不限",
      "interests": ["兴趣1"]
    }},
    "viewing_habits": ["观看习惯1", "观看习惯2"]
  }},
  "positioning": {{
    "market_position": "市场定位描述",
    "differentiation": ["差异化优势1", "差异化优势2"],
    "value_proposition": "价值主张"
  }},
  "competitors": {{
    "similar_projects": ["竞品1", "竞品2"],
    "strengths": ["本项目优势"],
    "weaknesses": ["本项目劣势"]
  }},
  "distribution": {{
    "primary_channels": ["主要渠道1", "主要渠道2"],
    "secondary_channels": ["次要渠道"],
    "timing_suggestion": "发行时机建议",
    "pricing_strategy": "定价策略"
  }},
  "is_dynamic": true
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.MARKET,
            task_type="analyze_market",
            prompt=prompt
        ))
    
    # ========== System_Agent 专用方法 ==========
    
    async def check_tag_consistency(
        self,
        tags: List[Dict[str, Any]]
    ) -> AgentLLMResponse:
        """
        检查标签一致性
        
        Args:
            tags: 标签列表
        
        Returns:
            包含检查结果的响应
        """
        tags_str = json.dumps(tags, ensure_ascii=False)
        
        prompt = f"""请检查以下标签是否存在矛盾。

标签列表：
{tags_str}

矛盾标签规则：
1. 性别：男/女 不能同时存在
2. 位置：室内/室外 不能同时存在
3. 时间：白天/夜晚 不能同时存在
4. 身高：高/矮 不能同时存在
5. 体型：胖/瘦 不能同时存在

请返回 JSON 格式：
{{
  "has_conflicts": true/false,
  "conflicts": [
    {{
      "entity": "实体名称",
      "conflicting_tags": ["标签1", "标签2"],
      "category": "冲突类别",
      "suggestion": "修复建议"
    }}
  ],
  "warnings": ["警告信息"],
  "passed": true/false
}}
"""
        return await self.generate(AgentLLMRequest(
            agent_type=AgentType.SYSTEM,
            task_type="check_tag_consistency",
            prompt=prompt
        ))


# 全局适配器实例
_agent_llm_adapter: Optional[AgentLLMAdapter] = None


def get_agent_llm_adapter() -> AgentLLMAdapter:
    """获取全局 Agent LLM 适配器实例"""
    global _agent_llm_adapter
    if _agent_llm_adapter is None:
        _agent_llm_adapter = AgentLLMAdapter()
    return _agent_llm_adapter


def set_agent_llm_adapter(adapter: AgentLLMAdapter):
    """设置全局 Agent LLM 适配器实例"""
    global _agent_llm_adapter
    _agent_llm_adapter = adapter
