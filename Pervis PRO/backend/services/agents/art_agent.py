# -*- coding: utf-8 -*-
"""
Art_Agent 服务（美术 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.3 实现 Art_Agent

提供美术相关的 AI 功能：
- 文件分类（角色/场景/参考）
- 元数据提取
- 标签生成（内容、风格、技术）
- 缩略图生成
- 视觉风格分析
- 角色/场景视觉描述

Requirements: 3.2, 3.5, 3.6, 5.3, 5.4
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class FileClassification:
    """文件分类结果"""
    category: str  # character, scene, reference
    confidence: float
    reason: str
    suggested_tags: List[str] = field(default_factory=list)


@dataclass
class FileMetadata:
    """文件元数据"""
    filename: str
    file_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    color_space: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "format": self.format,
            "color_space": self.color_space
        }


@dataclass
class VisualTags:
    """视觉标签"""
    scene_type: str = "未知"
    time: str = "未知"
    shot_type: str = "未知"
    mood: str = "未知"
    action: str = "未知"
    characters: str = "未知"
    free_tags: List[str] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_type": self.scene_type,
            "time": self.time,
            "shot_type": self.shot_type,
            "mood": self.mood,
            "action": self.action,
            "characters": self.characters,
            "free_tags": self.free_tags,
            "summary": self.summary
        }


class ArtAgentService:
    """
    Art_Agent 服务
    
    美术 Agent，负责视觉相关的 AI 功能
    """
    
    # 文件类型映射
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv'}
    DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.psd', '.ai'}
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "data/thumbnails"
        self._llm_adapter = None
        self._image_service = None
    
    def _get_image_service(self):
        """延迟加载图片生成服务"""
        if self._image_service is None:
            try:
                from services.image_generation import get_image_generation_service
                self._image_service = get_image_generation_service()
            except Exception as e:
                logger.error(f"图片生成服务加载失败: {e}")
        return self._image_service
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    def get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        ext = Path(file_path).suffix.lower()
        if ext in self.IMAGE_EXTENSIONS:
            return "image"
        elif ext in self.VIDEO_EXTENSIONS:
            return "video"
        elif ext in self.DOCUMENT_EXTENSIONS:
            return "document"
        return "unknown"
    
    def extract_metadata(self, file_path: str) -> FileMetadata:
        """
        提取文件元数据
        """
        path = Path(file_path)
        file_type = self.get_file_type(file_path)
        
        metadata = FileMetadata(
            filename=path.name,
            file_type=file_type,
            file_size=path.stat().st_size if path.exists() else 0
        )
        
        if file_type == "image":
            metadata = self._extract_image_metadata(file_path, metadata)
        elif file_type == "video":
            metadata = self._extract_video_metadata(file_path, metadata)
        
        return metadata
    
    def _extract_image_metadata(self, file_path: str, metadata: FileMetadata) -> FileMetadata:
        """提取图片元数据"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                metadata.width, metadata.height = img.size
                metadata.format = img.format
                metadata.color_space = img.mode
        except Exception as e:
            logger.warning(f"提取图片元数据失败: {e}")
        return metadata
    
    def _extract_video_metadata(self, file_path: str, metadata: FileMetadata) -> FileMetadata:
        """提取视频元数据"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "csv=p=0",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    metadata.width = int(parts[0])
                    metadata.height = int(parts[1])
                if len(parts) >= 3:
                    metadata.duration = float(parts[2])
        except Exception as e:
            logger.warning(f"提取视频元数据失败: {e}")
        return metadata
    
    async def classify_file(
        self,
        file_path: str,
        metadata: FileMetadata = None
    ) -> FileClassification:
        """
        分类文件（角色/场景/参考）
        """
        if metadata is None:
            metadata = self.extract_metadata(file_path)
        
        adapter = self._get_llm_adapter()
        if adapter:
            try:
                response = await adapter.classify_file(
                    metadata.filename,
                    metadata.file_type,
                    metadata.to_dict()
                )
                if response.success and response.parsed_data:
                    return FileClassification(
                        category=response.parsed_data.get("category", "reference"),
                        confidence=response.parsed_data.get("confidence", 0.5),
                        reason=response.parsed_data.get("reason", ""),
                        suggested_tags=response.parsed_data.get("suggested_tags", [])
                    )
            except Exception as e:
                logger.error(f"LLM 分类失败: {e}")
        
        # 回退：基于文件名分类
        return self._classify_by_filename(metadata.filename)
    
    def _classify_by_filename(self, filename: str) -> FileClassification:
        """基于文件名分类"""
        filename_lower = filename.lower()
        
        character_keywords = ["角色", "人物", "character", "char", "人设", "portrait", "face"]
        scene_keywords = ["场景", "scene", "环境", "background", "location", "bg"]
        
        for kw in character_keywords:
            if kw in filename_lower:
                return FileClassification(
                    category="character",
                    confidence=0.7,
                    reason=f"文件名包含关键词: {kw}"
                )
        
        for kw in scene_keywords:
            if kw in filename_lower:
                return FileClassification(
                    category="scene",
                    confidence=0.7,
                    reason=f"文件名包含关键词: {kw}"
                )
        
        return FileClassification(
            category="reference",
            confidence=0.5,
            reason="无法确定分类，放入参考"
        )
    
    async def generate_tags(
        self,
        file_path: str,
        description: str = None
    ) -> VisualTags:
        """
        生成视觉标签
        
        必须使用视觉模型分析图片内容，不支持 LLM 回退（因为 LLM 无法看到图片）
        """
        file_type = self.get_file_type(file_path)
        
        # 非图片文件：返回错误
        if file_type != "image":
            logger.warning(f"不支持的文件类型: {file_type}, 文件: {file_path}")
            return VisualTags(
                summary=f"[错误] 不支持的文件类型: {file_type}，仅支持图片分析"
            )
        
        # 文件不存在
        if not Path(file_path).exists():
            logger.error(f"文件不存在: {file_path}")
            return VisualTags(
                summary=f"[错误] 文件不存在: {Path(file_path).name}"
            )
        
        # 使用视觉模型分析图片内容
        try:
            from services.ollama_vision import get_vision_provider
            vision = get_vision_provider()
            
            if not vision:
                logger.error("视觉模型服务未初始化")
                return VisualTags(
                    summary="[错误] 视觉模型服务未初始化，请检查 Ollama 是否已启动"
                )
            
            if not vision.config.ENABLED:
                logger.error("视觉模型已被禁用")
                return VisualTags(
                    summary="[错误] 视觉模型已禁用，请在配置中启用 OLLAMA_VISION_ENABLED"
                )
            
            # 检查视觉模型是否可用
            is_available = await vision.check_availability()
            if not is_available:
                logger.error(f"视觉模型不可用，模型: {vision.model}")
                return VisualTags(
                    summary=f"[错误] 视觉模型 {vision.model} 不可用，请确保 Ollama 已启动并安装了视觉模型"
                )
            
            logger.info(f"使用视觉模型分析图片: {file_path}")
            vision_result = await vision.analyze_image(file_path)
            
            # 检查分析结果
            if not vision_result or vision_result.get("summary") == "无法分析图像内容":
                logger.error(f"视觉模型分析失败: {file_path}")
                return VisualTags(
                    summary="[错误] 视觉模型分析失败，请重试或检查图片格式"
                )
            
            # 成功：返回分析结果
            return VisualTags(
                scene_type=vision_result.get("scene_type", "未知"),
                time=vision_result.get("time", "未知"),
                shot_type=vision_result.get("shot_type", "未知"),
                mood=vision_result.get("mood", "未知"),
                action=vision_result.get("action", "未知"),
                characters=vision_result.get("characters", "未知"),
                free_tags=vision_result.get("free_tags", []),
                summary=vision_result.get("summary", "")
            )
            
        except ImportError as e:
            logger.error(f"ollama_vision 模块导入失败: {e}")
            return VisualTags(
                summary="[错误] 视觉模型模块未安装，请检查依赖"
            )
        except Exception as e:
            logger.error(f"视觉模型分析异常: {e}")
            return VisualTags(
                summary=f"[错误] 分析异常: {str(e)}"
            )
    
    def create_thumbnail(
        self,
        file_path: str,
        output_path: str = None,
        size: tuple = (320, 180)
    ) -> Optional[str]:
        """
        生成缩略图
        """
        path = Path(file_path)
        file_type = self.get_file_type(file_path)
        
        if output_path is None:
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{path.stem}_thumb.jpg")
        
        try:
            if file_type == "image":
                return self._create_image_thumbnail(file_path, output_path, size)
            elif file_type == "video":
                return self._create_video_thumbnail(file_path, output_path, size)
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
        
        return None
    
    def _create_image_thumbnail(
        self,
        file_path: str,
        output_path: str,
        size: tuple
    ) -> str:
        """生成图片缩略图"""
        from PIL import Image
        with Image.open(file_path) as img:
            img.thumbnail(size)
            img.save(output_path, "JPEG", quality=85)
        return output_path
    
    def _create_video_thumbnail(
        self,
        file_path: str,
        output_path: str,
        size: tuple
    ) -> str:
        """生成视频缩略图"""
        cmd = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-ss", "00:00:01",
            "-vframes", "1",
            "-vf", f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease",
            "-q:v", "2",
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    
    async def analyze_visual_style(
        self,
        file_paths: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        分析视觉风格
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            from services.agent_llm_adapter import AgentLLMRequest, AgentType
            
            # 收集文件信息
            files_info = []
            for fp in file_paths[:10]:  # 最多分析10个文件
                metadata = self.extract_metadata(fp)
                files_info.append(metadata.to_dict())
            
            prompt = f"""分析以下参考素材的视觉风格。

素材列表：
{files_info}

请返回 JSON 格式：
{{
  "overall_style": "整体风格描述",
  "color_palette": ["主色1", "主色2", "主色3"],
  "mood": "情绪基调",
  "lighting": "光线风格",
  "composition": "构图特点",
  "reference_projects": ["可能的对标项目1", "对标项目2"],
  "suggestions": ["风格建议1", "风格建议2"]
}}
"""
            response = await adapter.generate(AgentLLMRequest(
                agent_type=AgentType.ART,
                task_type="analyze_visual_style",
                prompt=prompt
            ))
            
            if response.success and response.parsed_data:
                return response.parsed_data
                
        except Exception as e:
            logger.error(f"分析视觉风格失败: {e}")
        
        return None
    
    async def generate_visual_description(
        self,
        entity_type: str,  # character, scene
        entity_name: str,
        context: str = ""
    ) -> Optional[str]:
        """
        生成角色/场景视觉描述
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            return None
        
        try:
            from services.agent_llm_adapter import AgentLLMRequest, AgentType
            
            if entity_type == "character":
                prompt = f"""为角色 "{entity_name}" 生成视觉描述。

上下文：{context}

请描述角色的外貌特征，包括：
- 年龄、性别
- 身高、体型
- 发型、发色
- 服装风格
- 标志性特征

返回 JSON 格式：
{{
  "description": "详细视觉描述",
  "key_features": ["特征1", "特征2"],
  "costume_notes": "服装说明",
  "reference_style": "参考风格"
}}
"""
            else:
                prompt = f"""为场景 "{entity_name}" 生成视觉描述。

上下文：{context}

请描述场景的视觉特征，包括：
- 环境类型（室内/室外）
- 时间氛围
- 空间布局
- 光线特点
- 关键道具

返回 JSON 格式：
{{
  "description": "详细视觉描述",
  "environment": "环境类型",
  "lighting": "光线描述",
  "key_props": ["道具1", "道具2"],
  "mood": "氛围"
}}
"""
            
            response = await adapter.generate(AgentLLMRequest(
                agent_type=AgentType.ART,
                task_type="generate_visual_description",
                prompt=prompt
            ))
            
            if response.success and response.parsed_data:
                return response.parsed_data.get("description")
                
        except Exception as e:
            logger.error(f"生成视觉描述失败: {e}")
        
        return None
    
    # ========== 图片生成功能 ==========
    
    async def generate_character_image(
        self,
        character_name: str,
        character_bio: str = "",
        tags: Dict[str, Any] = None,
        style: str = "cinematic"
    ) -> Optional[Dict[str, Any]]:
        """
        生成角色人设图
        
        Args:
            character_name: 角色名称
            character_bio: 人物小传
            tags: 角色标签 (gender, age, role 等)
            style: 图片风格
        
        Returns:
            生成结果，包含 image_url, local_path 等
        """
        image_service = self._get_image_service()
        if not image_service:
            logger.warning("图片生成服务不可用")
            return None
        
        if not image_service.is_configured:
            logger.warning("图片生成服务未配置 API Token")
            return None
        
        try:
            from services.image_generation import ImageStyle
            
            style_map = {
                "realistic": ImageStyle.REALISTIC,
                "anime": ImageStyle.ANIME,
                "concept_art": ImageStyle.CONCEPT_ART,
                "cinematic": ImageStyle.CINEMATIC,
                "illustration": ImageStyle.ILLUSTRATION
            }
            
            result = await image_service.generate_character_image(
                character_name=character_name,
                character_bio=character_bio,
                tags=tags or {},
                style=style_map.get(style, ImageStyle.CINEMATIC)
            )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"生成角色图片失败: {e}")
            return None
    
    async def generate_scene_image(
        self,
        scene_name: str,
        scene_description: str = "",
        time_of_day: str = "",
        style: str = "cinematic"
    ) -> Optional[Dict[str, Any]]:
        """
        生成场景概念图
        
        Args:
            scene_name: 场景名称
            scene_description: 场景描述
            time_of_day: 时间（白天/夜晚等）
            style: 图片风格
        
        Returns:
            生成结果
        """
        image_service = self._get_image_service()
        if not image_service:
            logger.warning("图片生成服务不可用")
            return None
        
        if not image_service.is_configured:
            logger.warning("图片生成服务未配置 API Token")
            return None
        
        try:
            from services.image_generation import ImageStyle
            
            style_map = {
                "realistic": ImageStyle.REALISTIC,
                "anime": ImageStyle.ANIME,
                "concept_art": ImageStyle.CONCEPT_ART,
                "cinematic": ImageStyle.CINEMATIC,
                "illustration": ImageStyle.ILLUSTRATION
            }
            
            result = await image_service.generate_scene_image(
                scene_name=scene_name,
                scene_description=scene_description,
                time_of_day=time_of_day,
                style=style_map.get(style, ImageStyle.CINEMATIC)
            )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"生成场景图片失败: {e}")
            return None
    
    def is_image_generation_available(self) -> bool:
        """检查图片生成服务是否可用"""
        image_service = self._get_image_service()
        return image_service is not None and image_service.is_configured


# 全局服务实例
_art_agent_service: Optional[ArtAgentService] = None


def get_art_agent_service() -> ArtAgentService:
    """获取 Art_Agent 服务实例"""
    global _art_agent_service
    if _art_agent_service is None:
        _art_agent_service = ArtAgentService()
    return _art_agent_service
