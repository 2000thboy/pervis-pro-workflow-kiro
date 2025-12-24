# -*- coding: utf-8 -*-
"""
LLM服务模块

提供统一的LLM接口，支持多种LLM提供商：
- Ollama (本地模型)
- OpenAI
- Gemini

Feature: multi-agent-workflow-core
Requirements: 6.1, 6.2, 6.4
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    MOCK = "mock"  # 用于测试


class LLMRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """LLM消息"""
    role: LLMRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class LLMResponse:
    """LLM响应"""
    id: str
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    raw_response: Optional[Dict[str, Any]] = None
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 30.0
    
    @classmethod
    def ollama(cls, model: str = "llama2", base_url: str = "http://localhost:11434") -> "LLMConfig":
        """创建Ollama配置"""
        return cls(
            provider=LLMProvider.OLLAMA,
            model=model,
            base_url=base_url
        )
    
    @classmethod
    def openai(cls, model: str = "gpt-3.5-turbo", api_key: str = "") -> "LLMConfig":
        """创建OpenAI配置"""
        return cls(
            provider=LLMProvider.OPENAI,
            model=model,
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
    
    @classmethod
    def gemini(cls, model: str = "gemini-pro", api_key: str = "") -> "LLMConfig":
        """创建Gemini配置"""
        return cls(
            provider=LLMProvider.GEMINI,
            model=model,
            api_key=api_key
        )
    
    @classmethod
    def mock(cls) -> "LLMConfig":
        """创建Mock配置（用于测试）"""
        return cls(
            provider=LLMProvider.MOCK,
            model="mock-model"
        )


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """发送补全请求"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class MockLLMClient(BaseLLMClient):
    """Mock LLM客户端（用于测试）"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._responses: Dict[str, str] = {}
        self._available = True
    
    def set_response(self, prompt_contains: str, response: str):
        """设置模拟响应"""
        self._responses[prompt_contains] = response
    
    def set_available(self, available: bool):
        """设置可用状态"""
        self._available = available
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """模拟聊天请求"""
        if not self._available:
            raise ConnectionError("LLM service unavailable")
        
        # 获取最后一条用户消息
        user_content = ""
        for msg in reversed(messages):
            if msg.role == LLMRole.USER:
                user_content = msg.content
                break
        
        # 查找匹配的响应
        response_content = "这是一个模拟响应。"
        for key, value in self._responses.items():
            if key in user_content:
                response_content = value
                break
        
        return LLMResponse(
            id=str(uuid4()),
            content=response_content,
            model=self.config.model,
            provider=self.config.provider,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """模拟补全请求"""
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._available


class OllamaClient(BaseLLMClient):
    """Ollama客户端"""
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送聊天请求到Ollama"""
        import aiohttp
        
        url = f"{self.config.base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                data = await response.json()
                
                return LLMResponse(
                    id=str(uuid4()),
                    content=data.get("message", {}).get("content", ""),
                    model=self.config.model,
                    provider=self.config.provider,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    },
                    raw_response=data
                )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """发送补全请求"""
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        import aiohttp
        
        try:
            url = f"{self.config.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception:
            return False


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送聊天请求到OpenAI"""
        import aiohttp
        
        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                data = await response.json()
                
                return LLMResponse(
                    id=data.get("id", str(uuid4())),
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self.config.model),
                    provider=self.config.provider,
                    usage=data.get("usage", {}),
                    raw_response=data
                )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """发送补全请求"""
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def is_available(self) -> bool:
        """检查OpenAI服务是否可用"""
        import aiohttp
        
        try:
            url = f"{self.config.base_url}/models"
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception:
            return False


class GeminiClient(BaseLLMClient):
    """Gemini客户端"""
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送聊天请求到Gemini"""
        import aiohttp
        
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.config.model}:generateContent"
        params = {"key": self.config.api_key}
        
        # 转换消息格式
        contents = []
        for msg in messages:
            role = "user" if msg.role in [LLMRole.USER, LLMRole.SYSTEM] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params=params,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error: {response.status} - {error_text}")
                
                data = await response.json()
                
                content = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    parts = data["candidates"][0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "")
                
                return LLMResponse(
                    id=str(uuid4()),
                    content=content,
                    model=self.config.model,
                    provider=self.config.provider,
                    usage=data.get("usageMetadata", {}),
                    raw_response=data
                )
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """发送补全请求"""
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(messages, **kwargs)
    
    async def is_available(self) -> bool:
        """检查Gemini服务是否可用"""
        import aiohttp
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models"
            params = {"key": self.config.api_key}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception:
            return False


@dataclass
class AIUsageRecord:
    """AI使用记录（用于MVP验证）"""
    id: str
    provider: LLMProvider
    model: str
    operation: str  # chat, complete, validate, etc.
    prompt_summary: str
    response_summary: str
    tokens_used: int
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMService:
    """
    LLM服务
    
    提供统一的LLM接口，支持：
    - 多提供商切换（Ollama、OpenAI、Gemini）
    - AI辅助生成
    - 内容验证
    - 使用记录追踪
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.mock()
        self._client: Optional[BaseLLMClient] = None
        self._usage_records: List[AIUsageRecord] = []
        self._validators: Dict[str, Callable] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化LLM服务"""
        self._client = self._create_client()
        self._initialized = True
        logger.info(f"LLM服务初始化完成: provider={self.config.provider.value}, model={self.config.model}")
        return True
    
    def _create_client(self) -> BaseLLMClient:
        """创建LLM客户端"""
        if self.config.provider == LLMProvider.OLLAMA:
            return OllamaClient(self.config)
        elif self.config.provider == LLMProvider.OPENAI:
            return OpenAIClient(self.config)
        elif self.config.provider == LLMProvider.GEMINI:
            return GeminiClient(self.config)
        else:
            return MockLLMClient(self.config)
    
    @property
    def client(self) -> BaseLLMClient:
        """获取LLM客户端"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    async def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return await self.client.is_available()
    
    async def chat(
        self,
        messages: List[LLMMessage],
        operation: str = "chat",
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            operation: 操作类型（用于记录）
            **kwargs: 额外参数
        
        Returns:
            LLM响应
        """
        import time
        start_time = time.time()
        
        try:
            response = await self.client.chat(messages, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录使用情况
            self._record_usage(
                operation=operation,
                prompt_summary=messages[-1].content[:100] if messages else "",
                response_summary=response.content[:100],
                tokens_used=response.total_tokens,
                duration_ms=duration_ms,
                success=True
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_usage(
                operation=operation,
                prompt_summary=messages[-1].content[:100] if messages else "",
                response_summary="",
                tokens_used=0,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def complete(
        self,
        prompt: str,
        operation: str = "complete",
        **kwargs
    ) -> LLMResponse:
        """
        发送补全请求
        
        Args:
            prompt: 提示文本
            operation: 操作类型
            **kwargs: 额外参数
        
        Returns:
            LLM响应
        """
        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]
        return await self.chat(messages, operation=operation, **kwargs)
    
    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        operation: str = "generate",
        **kwargs
    ) -> LLMResponse:
        """
        使用系统提示生成内容
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            operation: 操作类型
            **kwargs: 额外参数
        
        Returns:
            LLM响应
        """
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
            LLMMessage(role=LLMRole.USER, content=user_prompt)
        ]
        return await self.chat(messages, operation=operation, **kwargs)
    
    # === AI辅助功能 (Requirements 6.1) ===
    
    async def assist_content_creation(
        self,
        content_type: str,
        context: str,
        requirements: Optional[str] = None
    ) -> LLMResponse:
        """
        AI辅助内容创作
        
        Args:
            content_type: 内容类型（剧本、对话、描述等）
            context: 上下文信息
            requirements: 具体要求
        
        Returns:
            生成的内容
        """
        system_prompt = f"""你是一个专业的{content_type}创作助手。
请根据提供的上下文和要求，生成高质量的内容。
保持专业性和创意性的平衡。"""
        
        user_prompt = f"上下文：{context}"
        if requirements:
            user_prompt += f"\n\n具体要求：{requirements}"
        user_prompt += f"\n\n请生成{content_type}内容："
        
        return await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            operation=f"assist_{content_type}"
        )
    
    async def complete_project_info(
        self,
        partial_info: Dict[str, Any],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """
        补全项目信息（Requirements 2.2）
        
        Args:
            partial_info: 部分项目信息
            required_fields: 需要补全的字段
        
        Returns:
            补全后的项目信息
        """
        system_prompt = """你是一个专业的影视项目信息分析助手。
根据已有的项目信息，推断并补全缺失的字段。
返回JSON格式的补全结果。"""
        
        user_prompt = f"""已有项目信息：
{json.dumps(partial_info, ensure_ascii=False, indent=2)}

需要补全的字段：{', '.join(required_fields)}

请根据已有信息推断缺失字段的合理值，返回JSON格式："""
        
        response = await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            operation="complete_project_info"
        )
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            content = response.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                completed_info = json.loads(json_str)
                # 合并原有信息和补全信息
                result = {**partial_info, **completed_info}
                return result
        except json.JSONDecodeError:
            pass
        
        return partial_info
    
    # === 内容验证功能 (Requirements 6.2) ===
    
    def register_validator(self, name: str, validator: Callable[[str], bool]):
        """注册内容验证器"""
        self._validators[name] = validator
    
    async def validate_content(
        self,
        content: str,
        validation_type: str,
        criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证AI生成的内容
        
        Args:
            content: 待验证内容
            validation_type: 验证类型
            criteria: 验证标准
        
        Returns:
            验证结果
        """
        # 首先检查是否有注册的验证器
        if validation_type in self._validators:
            is_valid = self._validators[validation_type](content)
            return {
                "valid": is_valid,
                "validation_type": validation_type,
                "method": "registered_validator"
            }
        
        # 使用LLM进行验证
        system_prompt = """你是一个内容质量验证专家。
请评估提供的内容是否符合要求。
返回JSON格式的验证结果，包含：
- valid: 是否通过验证 (true/false)
- score: 质量评分 (0-100)
- issues: 发现的问题列表
- suggestions: 改进建议"""
        
        user_prompt = f"""验证类型：{validation_type}
验证标准：{criteria or '通用质量标准'}

待验证内容：
{content}

请进行验证并返回JSON结果："""
        
        response = await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            operation=f"validate_{validation_type}"
        )
        
        # 解析验证结果
        try:
            content_str = response.content
            start = content_str.find('{')
            end = content_str.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(content_str[start:end])
        except json.JSONDecodeError:
            pass
        
        return {
            "valid": True,
            "validation_type": validation_type,
            "method": "llm_validation",
            "raw_response": response.content
        }
    
    # === 智能分析功能 (Requirements 6.4) ===
    
    async def analyze_script(self, script_content: str) -> Dict[str, Any]:
        """
        分析剧本内容
        
        Args:
            script_content: 剧本内容
        
        Returns:
            分析结果
        """
        system_prompt = """你是一个专业的剧本分析师。
请分析提供的剧本内容，返回JSON格式的分析结果，包含：
- scenes: 场景列表，每个场景包含 name, duration_estimate, description
- characters: 角色列表
- themes: 主题列表
- mood: 整体情绪基调
- estimated_duration: 预估总时长（秒）"""
        
        response = await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=f"请分析以下剧本：\n\n{script_content}",
            operation="analyze_script"
        )
        
        try:
            content = response.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {
            "raw_analysis": response.content,
            "parse_error": True
        }
    
    async def generate_search_keywords(
        self,
        scene_description: str,
        asset_type: str = "video"
    ) -> List[str]:
        """
        生成素材搜索关键词（Requirements 3.4）
        
        Args:
            scene_description: 场景描述
            asset_type: 素材类型
        
        Returns:
            搜索关键词列表
        """
        system_prompt = f"""你是一个专业的{asset_type}素材搜索专家。
根据场景描述，生成用于搜索相关素材的关键词。
返回JSON数组格式的关键词列表。"""
        
        response = await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=f"场景描述：{scene_description}\n\n请生成搜索关键词：",
            operation="generate_keywords"
        )
        
        try:
            content = response.content
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass
        
        # 简单分词作为后备
        return scene_description.split()[:5]
    
    async def provide_professional_advice(
        self,
        domain: str,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        提供专业建议（Requirements 6.3）
        
        Args:
            domain: 专业领域（编剧、美术、市场等）
            question: 问题
            context: 上下文
        
        Returns:
            专业建议
        """
        domain_prompts = {
            "script": "你是一个资深编剧，擅长剧本创作和故事结构设计。",
            "art": "你是一个专业美术指导，擅长视觉设计和画面构图。",
            "market": "你是一个影视市场分析专家，了解观众喜好和市场趋势。",
            "director": "你是一个经验丰富的导演，擅长整体把控和创意指导。"
        }
        
        system_prompt = domain_prompts.get(domain, f"你是一个{domain}领域的专家。")
        system_prompt += "\n请提供专业、实用的建议。"
        
        user_prompt = question
        if context:
            user_prompt = f"背景信息：{context}\n\n问题：{question}"
        
        response = await self.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            operation=f"advice_{domain}"
        )
        
        return response.content
    
    # === 使用记录管理 (Requirements 6.5) ===
    
    def _record_usage(
        self,
        operation: str,
        prompt_summary: str,
        response_summary: str,
        tokens_used: int,
        duration_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """记录AI使用情况"""
        record = AIUsageRecord(
            id=str(uuid4()),
            provider=self.config.provider,
            model=self.config.model,
            operation=operation,
            prompt_summary=prompt_summary,
            response_summary=response_summary,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        self._usage_records.append(record)
        logger.debug(f"AI使用记录: operation={operation}, tokens={tokens_used}, success={success}")
    
    def get_usage_records(
        self,
        operation: Optional[str] = None,
        limit: int = 100
    ) -> List[AIUsageRecord]:
        """获取使用记录"""
        records = self._usage_records
        if operation:
            records = [r for r in records if r.operation == operation]
        return records[-limit:]
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        if not self._usage_records:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "average_duration_ms": 0,
                "operations": {}
            }
        
        successful = [r for r in self._usage_records if r.success]
        failed = [r for r in self._usage_records if not r.success]
        
        # 按操作类型统计
        operations: Dict[str, int] = {}
        for record in self._usage_records:
            operations[record.operation] = operations.get(record.operation, 0) + 1
        
        return {
            "total_requests": len(self._usage_records),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "total_tokens": sum(r.tokens_used for r in self._usage_records),
            "average_duration_ms": sum(r.duration_ms for r in self._usage_records) / len(self._usage_records),
            "operations": operations
        }
    
    def clear_usage_records(self):
        """清空使用记录"""
        self._usage_records.clear()


# 全局LLM服务实例
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取全局LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def set_llm_service(service: LLMService):
    """设置全局LLM服务实例"""
    global _llm_service
    _llm_service = service
