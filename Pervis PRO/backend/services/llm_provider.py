import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from enum import Enum

# Configuration
class LLMConfig:
    PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # auto, gemini, ollama, local
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")  # 默认使用 7b 模型
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    # 自动回退: 当主服务不可用时尝试备用服务
    AUTO_FALLBACK = os.getenv("LLM_AUTO_FALLBACK", "true").lower() == "true"


class AIServiceStatus(Enum):
    """AI 服务状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers"""
    
    @abstractmethod
    async def analyze_script(self, script_text: str, mode: str = "analytical") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_visual_tags(self, visual_keywords: List[str]) -> Dict[str, List[str]]:
        pass

    @abstractmethod
    async def generate_demo_script(self, topic: str = "random") -> Dict[str, Any]:
        """Generate a short demo script (Logline, Synopsis, Script)"""
        pass

    @abstractmethod
    async def generate_beat_tags(self, content: str) -> Dict[str, Any]:
        """Generate tags for a beat/scene based on its content"""
        pass

    @abstractmethod
    async def generate_asset_description(self, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Generate AI description for a video asset"""
        pass

    @abstractmethod
    async def analyze_rough_cut(self, script_content: str, video_tags: Dict[str, Any]) -> Dict[str, Any]:
        """AI rough cut analysis - find best in/out points"""
        pass

class GeminiProvider(LLMProvider):
    """Adapter for existing GeminiClient"""
    def __init__(self):
        from services.gemini_client import GeminiClient
        self.client = GeminiClient()

    async def analyze_script(self, script_text: str, mode: str = "analytical") -> Dict[str, Any]:
        return await self.client.analyze_script(script_text, mode)

    async def generate_visual_tags(self, visual_keywords: List[str]) -> Dict[str, List[str]]:
        # Gemini Vision logic usually handles this, but for hybrid parity:
        prompt = f"Given these visual elements: {', '.join(visual_keywords)}, generate tags."
        return {"error": "Not implemented in legacy client"} 

    async def generate_demo_script(self, topic: str = "random") -> Dict[str, Any]:
        prompt = f"""Generate a creative micro-short film script demo (approx 120s).
Topic/Genre: {topic if topic != "random" else "Sci-Fi or Thriller"}.
Output JSON format:
{{
  "title": "...",
  "logline": "...",
  "synopsis": "...",
  "script_content": "..."  (Standard screenplay format, in Chinese)
}}
"""
        return await self.client.generate_json(prompt)

    async def generate_beat_tags(self, content: str) -> Dict[str, Any]:
        """Generate tags for a beat/scene based on its content using Gemini"""
        prompt = f"""分析以下剧本片段，生成结构化的标签信息。

剧本内容：
{content}

请返回JSON格式：
{{
  "scene_slug": "场景标识 (如 INT. OFFICE - DAY)",
  "location_type": "INT 或 EXT",
  "time_of_day": "DAY/NIGHT/DAWN/DUSK",
  "primary_emotion": "主要情绪 (如 tense, happy, sad, mysterious)",
  "key_action": "关键动作 (如 dialogue, chase, fight, discovery)",
  "visual_notes": "视觉备注",
  "shot_type": "建议镜头类型 (WIDE/MEDIUM/CLOSE/EXTREME_CLOSE)"
}}

只返回JSON，不要其他内容。
"""
        try:
            result = await self.client.generate_json(prompt)
            if "error" in result:
                return {"status": "error", "message": result.get("error")}
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Gemini generate_beat_tags failed: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_asset_description(self, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Generate AI description for a video asset using Gemini"""
        metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else "无额外元数据"
        prompt = f"""为以下视频素材生成一段专业的描述文字。

文件名：{filename}
元数据：{metadata_str}

要求：
1. 描述应该简洁但信息丰富
2. 包含可能的内容类型、情绪、适用场景
3. 使用中文
4. 不超过100字

只返回描述文字，不要其他内容。
"""
        try:
            result = await self.client.generate_text(prompt)
            if result.get("status") == "success":
                return result["data"]["text"].strip()
            return f"视频素材：{filename}"
        except Exception as e:
            logger.error(f"Gemini generate_asset_description failed: {e}")
            return f"视频素材：{filename}"

    async def analyze_rough_cut(self, script_content: str, video_tags: Dict[str, Any]) -> Dict[str, Any]:
        """AI rough cut analysis using Gemini"""
        tags_str = json.dumps(video_tags, ensure_ascii=False)
        prompt = f"""作为专业的视频剪辑师，分析以下剧本内容和视频标签，推荐最佳的入出点。

剧本内容：
{script_content}

视频标签：
{tags_str}

请返回JSON格式：
{{
  "inPoint": 入点时间（秒，数字）,
  "outPoint": 出点时间（秒，数字）,
  "confidence": 置信度（0-1之间的数字）,
  "reason": "推荐理由（中文，简洁说明为什么选择这个片段）"
}}

只返回JSON，不要其他内容。
"""
        try:
            result = await self.client.generate_json(prompt)
            if "error" in result:
                return {"status": "error", "message": result.get("error")}
            # 验证必要字段
            required_fields = ["inPoint", "outPoint", "confidence", "reason"]
            for field in required_fields:
                if field not in result:
                    return {"status": "error", "message": f"Missing field: {field}"}
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Gemini analyze_rough_cut failed: {e}")
            return {"status": "error", "message": str(e)} 

class OllamaProvider(LLMProvider):
    """Adapter for Local Ollama (Qwen)"""
    def __init__(self):
        # 修正 URL: Ollama 原生 API 不需要 /v1 后缀
        base = LLMConfig.OLLAMA_BASE_URL
        if base.endswith('/v1'):
            base = base[:-3]
        self.base_url = base
        self.model = LLMConfig.LOCAL_MODEL_NAME
        logger.info(f"Initialized OllamaProvider with {self.base_url} using {self.model}")
    
    async def check_availability(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False

    async def _chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = True) -> Dict[str, Any]:
        # Ollama 原生 API 使用 /api/chat 端点
        url = f"{self.base_url}/api/chat"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if json_mode:
            payload["format"] = "json"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"Ollama Error: {resp.status} - {err_text}")
                        return {"status": "error", "message": f"Ollama Error: {resp.status}"}
                    
                    data = await resp.json()
                    # Ollama 原生 API 返回格式不同
                    content = data.get("message", {}).get("content", "")
                    
                    if json_mode:
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            logger.warning("Ollama returned invalid JSON, attempting cleanup")
                            return self._repair_json(content)
                    return {"content": content}
            except aiohttp.ClientError as e:
                logger.error(f"Ollama Connection Failed: {e}")
                return {
                    "status": "error", 
                    "error_code": "CONNECTION_FAILED",
                    "message": f"无法连接到AI服务 (Ollama)。请检查 {self.base_url} 是否可访问。"
                }
            except asyncio.TimeoutError:
                logger.error("Ollama request timeout")
                return {"status": "error", "message": "AI服务请求超时，请稍后重试"}
            except Exception as e:
                logger.error(f"Unexpected Error: {e}")
                return {"status": "error", "message": f"AI服务异常: {str(e)}"}

    def _repair_json(self, content: str) -> Dict[str, Any]:
        # Strip markdown code blocks if present
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
        
        content = content.strip()
        
        # Simple heuristic to find first { and last }
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"JSON Repair Failed: {e}")
            
        return {"status": "error", "message": "Failed to parse JSON: " + content[:50]}

    async def analyze_script(self, script_text: str, mode: str = "analytical") -> Dict[str, Any]:
        system_prompt = """You are a professional Script Breakdown Assistant for Pervis PRO.
Your job is to analyze screenplays and output structured JSON data.
Strictly follow the output schema.
Identify: Logline, Synopsis, Characters, and Beats (Scenes).
For each Beat, analyze: Content, Emotion Tags (mood), Scene Tags (location type), Action Tags.
"""
        user_prompt = f"""Analyze the following script segment.
Return JSON format:
{{
  "logline": "...",
  "synopsis": "...",
  "characters": [ {{"id": "...", "name": "...", "role": "...", "description": "..."}} ],
  "beats": [ {{"content": "...", "emotion_tags": [...], "scene_tags": [...], "action_tags": [...], "duration_estimate": 2.0}} ]
}}

Script:
{script_text}
"""
        logger.info(f"Ollama Request: Analyze Script ({len(script_text)} chars)")
        result = await self._chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        if result.get("status") == "error":
            return result

        # Normalize result structure to match GeminiClient output
        if "beats" in result:
             return {"status": "success", "data": result}
        return {"status": "error", "message": "Invalid AI Response: " + str(result)[:100]}

    async def generate_visual_tags(self, visual_keywords: List[str]) -> Dict[str, List[str]]:
        prompt = f"""Analyze these visual keywords from a video frame: {', '.join(visual_keywords)}.
Generate structured tags in JSON:
{{
  "scene_type": ["Indoor/Outdoor", ...],
  "lighting": ["Day", "Night", "Neon", ...],
  "mood": ["Tense", "Happy", ...],
  "objects": [...]
}}
"""
        return await self._chat_completion([{"role": "user", "content": prompt}])

    async def generate_demo_script(self, topic: str = "random") -> Dict[str, Any]:
        prompt = f"""Generate a creative short film script demo (Trailer or Teaser style).
Genre: {topic if topic != "random" else "Action, Sci-Fi, or Noir"}.
Language: Chinese (Simplified).

IMPORTANT: Return valid JSON only. Do not wrap in markdown blocks.
Use EXACTLY these keys: "title", "logline", "synopsis", "script_content".

Example Output:
{{
  "title": "Neon Rain",
  "logline": "A detective hunts a ghost.",
  "synopsis": "Full story summary...",
  "script_content": "SCENE 1\\nINT. ROOM..."
}}

Output JSON:
"""
        logger.info(f"Ollama Request: Generate Demo ({topic})")
        result = await self._chat_completion([{"role": "user", "content": prompt}])
        logger.info(f"Ollama Response: {str(result)[:200]}...") # Log first 200 chars
        return result

    async def generate_beat_tags(self, content: str) -> Dict[str, Any]:
        """Generate tags for a beat/scene based on its content using Ollama"""
        prompt = f"""分析以下剧本片段，生成结构化的标签信息。

剧本内容：
{content}

请返回JSON格式：
{{
  "scene_slug": "场景标识 (如 INT. OFFICE - DAY)",
  "location_type": "INT 或 EXT",
  "time_of_day": "DAY/NIGHT/DAWN/DUSK",
  "primary_emotion": "主要情绪 (如 tense, happy, sad, mysterious)",
  "key_action": "关键动作 (如 dialogue, chase, fight, discovery)",
  "visual_notes": "视觉备注",
  "shot_type": "建议镜头类型 (WIDE/MEDIUM/CLOSE/EXTREME_CLOSE)"
}}

只返回JSON，不要其他内容。
"""
        logger.info(f"Ollama Request: Generate Beat Tags ({len(content)} chars)")
        result = await self._chat_completion([{"role": "user", "content": prompt}])
        
        if result.get("status") == "error":
            return result
        
        # 验证必要字段
        required_fields = ["scene_slug", "location_type", "time_of_day", "primary_emotion", "key_action"]
        for field in required_fields:
            if field not in result:
                result[field] = "unknown"
        
        return {"status": "success", "data": result}

    async def generate_asset_description(self, filename: str, metadata: Dict[str, Any] = None) -> str:
        """Generate AI description for a video asset using Ollama"""
        metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else "无额外元数据"
        prompt = f"""为以下视频素材生成一段专业的描述文字。

文件名：{filename}
元数据：{metadata_str}

要求：
1. 描述应该简洁但信息丰富
2. 包含可能的内容类型、情绪、适用场景
3. 使用中文
4. 不超过100字

只返回描述文字，不要JSON格式，不要其他内容。
"""
        logger.info(f"Ollama Request: Generate Asset Description ({filename})")
        result = await self._chat_completion([{"role": "user", "content": prompt}], json_mode=False)
        
        if result.get("status") == "error":
            return f"视频素材：{filename}"
        
        return result.get("content", f"视频素材：{filename}").strip()

    async def analyze_rough_cut(self, script_content: str, video_tags: Dict[str, Any]) -> Dict[str, Any]:
        """AI rough cut analysis using Ollama"""
        tags_str = json.dumps(video_tags, ensure_ascii=False)
        prompt = f"""作为专业的视频剪辑师，分析以下剧本内容和视频标签，推荐最佳的入出点。

剧本内容：
{script_content}

视频标签：
{tags_str}

请返回JSON格式：
{{
  "inPoint": 入点时间（秒，数字）,
  "outPoint": 出点时间（秒，数字）,
  "confidence": 置信度（0-1之间的数字）,
  "reason": "推荐理由（中文，简洁说明为什么选择这个片段）"
}}

只返回JSON，不要其他内容。
"""
        logger.info(f"Ollama Request: Analyze Rough Cut")
        result = await self._chat_completion([{"role": "user", "content": prompt}])
        
        if result.get("status") == "error":
            return result
        
        # 验证必要字段
        required_fields = ["inPoint", "outPoint", "confidence", "reason"]
        for field in required_fields:
            if field not in result:
                return {"status": "error", "message": f"Missing field: {field}"}
        
        # 确保数值类型正确
        try:
            result["inPoint"] = float(result["inPoint"])
            result["outPoint"] = float(result["outPoint"])
            result["confidence"] = float(result["confidence"])
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid numeric value: {e}"}
        
        return {"status": "success", "data": result}

def get_llm_provider() -> LLMProvider:
    """
    获取 LLM Provider 实例
    
    支持的配置值:
    - "auto": 自动检测可用服务 (优先本地 Ollama，回退到 Gemini)
    - "ollama" / "local": 使用本地 Ollama
    - "gemini": 使用 Google Gemini API
    
    当 AUTO_FALLBACK=true 时，如果主服务不可用会自动尝试备用服务
    """
    provider_type = LLMConfig.PROVIDER.lower()
    
    # 自动模式: 检测可用服务
    if provider_type == "auto":
        return _get_auto_provider()
    
    # 支持 "local" 和 "ollama" 两种配置值
    if provider_type in ["local", "ollama"]:
        return OllamaProvider()
    
    # Gemini 模式
    if provider_type == "gemini":
        if not LLMConfig.GEMINI_API_KEY:
            if LLMConfig.AUTO_FALLBACK:
                logger.warning("Gemini API Key 未配置，尝试回退到 Ollama...")
                return OllamaProvider()
            raise ValueError(
                "AI 配置错误: LLM_PROVIDER='gemini' 但 GEMINI_API_KEY 未设置。"
                "请在 .env 中设置 GEMINI_API_KEY，或使用 LLM_PROVIDER=ollama 切换到本地 AI。"
            )
        return GeminiProvider()
    
    # 未知配置，使用自动模式
    logger.warning(f"未知的 LLM_PROVIDER 配置: {provider_type}，使用自动模式")
    return _get_auto_provider()


def _get_auto_provider() -> LLMProvider:
    """
    自动检测并返回可用的 LLM Provider
    优先级: Ollama (本地) > Gemini (云端)
    """
    import asyncio
    
    # 1. 尝试 Ollama (本地优先)
    try:
        ollama = OllamaProvider()
        # 同步检查可用性
        loop = asyncio.new_event_loop()
        try:
            is_available = loop.run_until_complete(ollama.check_availability())
        finally:
            loop.close()
        
        if is_available:
            logger.info("自动检测: 使用本地 Ollama 服务")
            return ollama
        else:
            logger.info("自动检测: Ollama 服务不可用")
    except Exception as e:
        logger.debug(f"Ollama 初始化失败: {e}")
    
    # 2. 尝试 Gemini (云端备用)
    if LLMConfig.GEMINI_API_KEY:
        try:
            gemini = GeminiProvider()
            logger.info("自动检测: 使用 Gemini API 服务")
            return gemini
        except Exception as e:
            logger.warning(f"Gemini 初始化失败: {e}")
    
    # 3. 都不可用，返回 Ollama 并让调用时报错
    logger.warning(
        "自动检测: 没有可用的 AI 服务。"
        "请确保 Ollama 正在运行 (http://localhost:11434) 或配置 GEMINI_API_KEY。"
    )
    return OllamaProvider()


async def check_ai_services() -> Dict[str, Any]:
    """
    检查所有 AI 服务的可用性
    返回各服务的状态信息，供前端显示选择
    """
    results = {
        "ollama": {
            "status": AIServiceStatus.UNKNOWN.value,
            "url": LLMConfig.OLLAMA_BASE_URL,
            "model": LLMConfig.LOCAL_MODEL_NAME,
            "message": ""
        },
        "gemini": {
            "status": AIServiceStatus.UNKNOWN.value,
            "configured": bool(LLMConfig.GEMINI_API_KEY),
            "message": ""
        },
        "current_provider": LLMConfig.PROVIDER,
        "auto_fallback": LLMConfig.AUTO_FALLBACK
    }
    
    # 检查 Ollama
    try:
        ollama = OllamaProvider()
        is_available = await ollama.check_availability()
        if is_available:
            results["ollama"]["status"] = AIServiceStatus.AVAILABLE.value
            results["ollama"]["message"] = "Ollama 服务正常运行"
        else:
            results["ollama"]["status"] = AIServiceStatus.UNAVAILABLE.value
            results["ollama"]["message"] = "Ollama 服务未响应"
    except Exception as e:
        results["ollama"]["status"] = AIServiceStatus.UNAVAILABLE.value
        results["ollama"]["message"] = f"连接失败: {str(e)}"
    
    # 检查 Gemini
    if LLMConfig.GEMINI_API_KEY:
        results["gemini"]["status"] = AIServiceStatus.AVAILABLE.value
        results["gemini"]["message"] = "Gemini API Key 已配置"
    else:
        results["gemini"]["status"] = AIServiceStatus.UNAVAILABLE.value
        results["gemini"]["message"] = "未配置 GEMINI_API_KEY"
    
    return results
