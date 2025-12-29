# -*- coding: utf-8 -*-
"""
Ollama 视觉模型适配器

支持使用本地 Ollama 视觉模型（如 llava-llama3）进行图像分析，
替代 Gemini API 进行视频帧标签生成。

Requirements: 16.6 (视频标签生成)
"""
import os
import json
import base64
import logging
import asyncio
import aiohttp
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VisionConfig:
    """视觉模型配置"""
    # Ollama 服务地址
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # 视觉模型名称 (支持 llava, llava-llama3, bakllava, moondream 等)
    VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "llava-llama3")
    # 请求超时（秒）- 视觉模型处理较慢
    TIMEOUT: int = int(os.getenv("OLLAMA_VISION_TIMEOUT", "120"))
    # 是否启用本地视觉模型
    ENABLED: bool = os.getenv("OLLAMA_VISION_ENABLED", "true").lower() == "true"


class OllamaVisionProvider:
    """
    Ollama 视觉模型 Provider
    
    用于分析图像/视频帧，生成结构化标签。
    支持的模型: llava-llama3, llava, bakllava, moondream
    """
    
    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        # 修正 URL
        base = self.config.OLLAMA_BASE_URL
        if base.endswith('/v1'):
            base = base[:-3]
        self.base_url = base
        self.model = self.config.VISION_MODEL
        self._available: Optional[bool] = None
        logger.info(f"OllamaVisionProvider 初始化: {self.base_url}, 模型: {self.model}")
    
    async def check_availability(self) -> bool:
        """检查视觉模型是否可用"""
        if self._available is not None:
            return self._available
        
        try:
            async with aiohttp.ClientSession() as session:
                # 检查 Ollama 服务
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        self._available = False
                        return False
                    
                    data = await resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    
                    # 检查视觉模型是否已安装
                    model_base = self.model.split(":")[0]
                    for m in models:
                        if model_base in m:
                            self._available = True
                            logger.info(f"视觉模型 {self.model} 可用")
                            return True
                    
                    logger.warning(f"视觉模型 {self.model} 未安装，已安装模型: {models}")
                    self._available = False
                    return False
                    
        except Exception as e:
            logger.error(f"检查视觉模型可用性失败: {e}")
            self._available = False
            return False
    
    def _encode_image(self, image_path: str) -> str:
        """将图像编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析图像，生成结构化标签
        
        Args:
            image_path: 图像文件路径
            prompt: 自定义提示词（可选）
        
        Returns:
            包含标签的字典
        """
        if not self.config.ENABLED:
            logger.info("本地视觉模型已禁用")
            return self._get_fallback_tags()
        
        if not Path(image_path).exists():
            logger.error(f"图像文件不存在: {image_path}")
            return self._get_fallback_tags()
        
        # 默认提示词
        if prompt is None:
            prompt = self._get_default_prompt()
        
        try:
            # 编码图像
            image_base64 = self._encode_image(image_path)
            
            # 构建请求
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "format": "json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"Ollama Vision 错误: {resp.status} - {err_text}")
                        return self._get_fallback_tags()
                    
                    data = await resp.json()
                    response_text = data.get("response", "")
                    
                    # 解析 JSON 响应
                    return self._parse_response(response_text)
                    
        except asyncio.TimeoutError:
            logger.error(f"Ollama Vision 请求超时 ({self.config.TIMEOUT}s)")
            return self._get_fallback_tags()
        except Exception as e:
            logger.error(f"Ollama Vision 分析失败: {e}")
            return self._get_fallback_tags()
    
    async def batch_analyze(
        self,
        image_paths: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析图像
        
        Args:
            image_paths: 图像路径列表
            progress_callback: 进度回调函数 (current, total)
        
        Returns:
            标签列表
        """
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            result = await self.analyze_image(path)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
            
            # 避免过快请求
            if i < total - 1:
                await asyncio.sleep(0.5)
        
        return results
    
    def _get_default_prompt(self) -> str:
        """获取默认的图像分析提示词"""
        return """仔细分析这张图片的视觉内容，返回 JSON 格式的详细标签。

请深入分析图片中的：
1. 场景环境（室内/室外、城市/自然、具体地点类型）
2. 时间氛围（白天/夜晚/黄昏/黎明、天气）
3. 画面构图（全景/中景/特写/过肩）
4. 情绪基调（紧张/浪漫/悲伤/欢乐/悬疑/平静/史诗/神秘）
5. 动作状态（对话/追逐/打斗/静态/行走/战斗）
6. 人物情况（单人/双人/群戏/无人、人物特征）
7. 视觉风格（写实/动漫/概念艺术/电影感）
8. 色调（暖色/冷色/高对比/低饱和）
9. 具体内容元素（武器、服装、建筑、自然元素等）

请严格按照以下格式返回：
{
  "scene_type": "室内/室外/城市/自然/废墟/森林/山脉/海边/战场 等具体描述",
  "time": "白天/夜晚/黄昏/黎明/阴天 之一",
  "shot_type": "全景/中景/特写/过肩/俯视/仰视 之一",
  "mood": "紧张/浪漫/悲伤/欢乐/悬疑/平静/史诗/神秘/孤独/壮观 之一",
  "action": "对话/追逐/打斗/静态/行走/战斗/潜行/观望 之一",
  "characters": "单人/双人/群戏/无人 之一",
  "free_tags": ["具体内容标签1", "具体内容标签2", "风格标签", "色调标签", "元素标签"],
  "summary": "详细描述画面内容，包括人物、动作、环境、氛围"
}

free_tags 要求：
- 至少包含 5-8 个具体标签
- 包含人物特征（如：武士、剑客、少女、盔甲）
- 包含环境元素（如：樱花、废墟、城堡、草原）
- 包含风格标签（如：日式、中世纪、赛博朋克、水墨风）
- 包含色调标签（如：暖色调、冷色调、高对比、剪影）
- 包含情绪标签（如：孤独、壮观、神秘、紧张）

只返回 JSON，不要其他内容。"""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析模型响应"""
        try:
            # 清理 markdown 代码块
            text = response_text.strip()
            if "```" in text:
                text = text.replace("```json", "").replace("```", "")
            text = text.strip()
            
            # 尝试找到 JSON 对象
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
                
                # 验证并补充缺失字段
                return self._validate_tags(result)
            
            logger.warning(f"无法从响应中提取 JSON: {text[:100]}")
            return self._get_fallback_tags()
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 响应: {response_text[:100]}")
            return self._get_fallback_tags()
    
    def _validate_tags(self, tags: Dict[str, Any]) -> Dict[str, Any]:
        """验证并补充标签字段"""
        defaults = self._get_fallback_tags()
        
        # 确保所有必要字段存在
        for key in defaults:
            if key not in tags:
                tags[key] = defaults[key]
        
        # 验证枚举值（扩展支持更多选项）
        valid_values = {
            "scene_type": ["室内", "室外", "城市", "自然", "废墟", "森林", "山脉", "海边", "战场", "街道", "宫殿", "洞穴", "未知"],
            "time": ["白天", "夜晚", "黄昏", "黎明", "阴天", "未知"],
            "shot_type": ["全景", "中景", "特写", "过肩", "俯视", "仰视", "未知"],
            "mood": ["紧张", "浪漫", "悲伤", "欢乐", "悬疑", "平静", "史诗", "神秘", "孤独", "壮观", "未知"],
            "action": ["对话", "追逐", "打斗", "静态", "行走", "战斗", "潜行", "观望", "未知"],
            "characters": ["单人", "双人", "群戏", "无人", "未知"]
        }
        
        for key, valid in valid_values.items():
            if tags.get(key) not in valid:
                # 如果值不在预定义列表中，但不为空，保留原值（允许更灵活的描述）
                if not tags.get(key):
                    tags[key] = "未知"
        
        # 确保 free_tags 是列表且不为空
        if not isinstance(tags.get("free_tags"), list):
            tags["free_tags"] = []
        
        # 过滤空标签
        tags["free_tags"] = [t for t in tags["free_tags"] if t and str(t).strip()]
        
        return tags
    
    def _get_fallback_tags(self) -> Dict[str, Any]:
        """获取回退标签（当分析失败时使用）"""
        return {
            "scene_type": "未知",
            "time": "未知",
            "shot_type": "未知",
            "mood": "未知",
            "action": "未知",
            "characters": "未知",
            "free_tags": [],
            "summary": "无法分析图像内容"
        }


# 全局实例
_vision_provider: Optional[OllamaVisionProvider] = None


def get_vision_provider() -> OllamaVisionProvider:
    """获取视觉模型 Provider 实例"""
    global _vision_provider
    if _vision_provider is None:
        _vision_provider = OllamaVisionProvider()
    return _vision_provider


async def analyze_video_frame(image_path: str) -> Dict[str, Any]:
    """
    便捷函数：分析视频帧
    
    Args:
        image_path: 图像文件路径
    
    Returns:
        标签字典
    """
    provider = get_vision_provider()
    return await provider.analyze_image(image_path)
