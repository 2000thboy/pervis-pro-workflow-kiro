# -*- coding: utf-8 -*-
"""
视频预处理服务

Feature: pervis-project-wizard Phase 1
Task: 1.2 创建 VideoPreprocessor

提供视频素材的预处理功能：
- 镜头分割（PySceneDetect）
- 确保片段 ≤10秒
- 批量 Gemini 标签生成
- FFmpeg 切割视频

Requirements: 16.1, 16.2, 16.5, 16.6
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class PreprocessStatus(str, Enum):
    """预处理状态"""
    PENDING = "pending"
    SPLITTING = "splitting"
    TAGGING = "tagging"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PreprocessProgress:
    """预处理进度"""
    video_path: str
    status: PreprocessStatus = PreprocessStatus.PENDING
    progress: float = 0.0
    message: str = ""
    total_segments: int = 0
    processed_segments: int = 0
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class VideoSegmentInfo:
    """视频片段信息"""
    segment_id: str
    video_id: str
    video_path: str
    segment_path: str
    start_time: float
    end_time: float
    duration: float
    thumbnail_path: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


class VideoPreprocessor:
    """
    视频预处理器
    
    处理流程：
    1. 使用 PySceneDetect 进行镜头分割
    2. 确保每个片段 ≤10秒（超长片段再切割）
    3. 使用 Gemini 生成标签
    4. 生成向量嵌入
    """
    
    MAX_SEGMENT_DURATION = 10.0  # 最大片段时长（秒）
    
    def __init__(
        self,
        output_dir: str = None,
        gemini_api_key: str = None,
        use_gpu: bool = False
    ):
        self.output_dir = output_dir or tempfile.gettempdir()
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.use_gpu = use_gpu
        self._progress: Dict[str, PreprocessProgress] = {}
        self._embedding_model = None
    
    def _get_embedding_model(self):
        """延迟加载嵌入模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("嵌入模型加载完成")
            except Exception as e:
                logger.error(f"嵌入模型加载失败: {e}")
        return self._embedding_model
    
    async def preprocess(
        self,
        video_path: str,
        video_id: str = None,
        generate_tags: bool = True,
        generate_embeddings: bool = True
    ) -> List[VideoSegmentInfo]:
        """
        完整预处理流程
        
        Args:
            video_path: 视频文件路径
            video_id: 视频ID（可选）
            generate_tags: 是否生成标签
            generate_embeddings: 是否生成嵌入
        
        Returns:
            处理后的视频片段列表
        """
        video_id = video_id or str(uuid4())
        
        # 初始化进度
        self._progress[video_id] = PreprocessProgress(
            video_path=video_path,
            status=PreprocessStatus.SPLITTING
        )
        
        try:
            # 1. 镜头分割
            self._update_progress(video_id, PreprocessStatus.SPLITTING, 0.1, "正在分割镜头...")
            scene_list = await self._detect_scenes(video_path)
            
            # 2. 确保片段 ≤10秒
            segments = await self._ensure_max_duration(video_path, video_id, scene_list)
            self._progress[video_id].total_segments = len(segments)
            
            # 3. 切割视频
            self._update_progress(video_id, PreprocessStatus.SPLITTING, 0.3, "正在切割视频...")
            segments = await self._split_video(video_path, video_id, segments)
            
            # 4. 生成标签
            if generate_tags:
                self._update_progress(video_id, PreprocessStatus.TAGGING, 0.5, "正在生成标签...")
                segments = await self._batch_generate_tags(segments)
            
            # 5. 生成嵌入
            if generate_embeddings:
                self._update_progress(video_id, PreprocessStatus.EMBEDDING, 0.8, "正在生成向量...")
                segments = await self._generate_embeddings(segments)
            
            # 完成
            self._update_progress(video_id, PreprocessStatus.COMPLETED, 1.0, "预处理完成")
            self._progress[video_id].completed_at = datetime.now()
            
            return segments
            
        except Exception as e:
            logger.error(f"预处理失败: {e}")
            self._progress[video_id].status = PreprocessStatus.FAILED
            self._progress[video_id].error = str(e)
            raise
    
    async def _detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """
        使用 PySceneDetect 检测场景
        
        Returns:
            场景列表 [(start_time, end_time), ...]
        """
        try:
            from scenedetect import detect, ContentDetector, AdaptiveDetector
            
            # 使用内容检测器
            scene_list = detect(video_path, ContentDetector(threshold=27.0))
            
            # 转换为时间列表
            scenes = []
            for scene in scene_list:
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                scenes.append((start_time, end_time))
            
            logger.info(f"检测到 {len(scenes)} 个场景")
            return scenes
            
        except Exception as e:
            logger.error(f"场景检测失败: {e}")
            # 回退：获取视频时长，作为单个场景
            duration = await self._get_video_duration(video_path)
            return [(0.0, duration)]
    
    async def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
            return 60.0  # 默认60秒
    
    async def _ensure_max_duration(
        self,
        video_path: str,
        video_id: str,
        scenes: List[Tuple[float, float]]
    ) -> List[VideoSegmentInfo]:
        """
        确保每个片段 ≤10秒
        
        超长片段会被进一步切割
        """
        segments = []
        segment_index = 0
        
        for start_time, end_time in scenes:
            duration = end_time - start_time
            
            if duration <= self.MAX_SEGMENT_DURATION:
                # 片段时长合适
                segments.append(VideoSegmentInfo(
                    segment_id=f"{video_id}_seg_{segment_index:04d}",
                    video_id=video_id,
                    video_path=video_path,
                    segment_path="",  # 稍后填充
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration
                ))
                segment_index += 1
            else:
                # 片段过长，需要切割
                current_start = start_time
                while current_start < end_time:
                    current_end = min(current_start + self.MAX_SEGMENT_DURATION, end_time)
                    segments.append(VideoSegmentInfo(
                        segment_id=f"{video_id}_seg_{segment_index:04d}",
                        video_id=video_id,
                        video_path=video_path,
                        segment_path="",
                        start_time=current_start,
                        end_time=current_end,
                        duration=current_end - current_start
                    ))
                    segment_index += 1
                    current_start = current_end
        
        logger.info(f"处理后共 {len(segments)} 个片段")
        return segments
    
    async def _split_video(
        self,
        video_path: str,
        video_id: str,
        segments: List[VideoSegmentInfo]
    ) -> List[VideoSegmentInfo]:
        """
        使用 FFmpeg 切割视频
        """
        output_dir = Path(self.output_dir) / video_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, segment in enumerate(segments):
            try:
                # 输出路径
                segment_filename = f"{segment.segment_id}.mp4"
                segment_path = output_dir / segment_filename
                thumbnail_path = output_dir / f"{segment.segment_id}_thumb.jpg"
                
                # FFmpeg 切割命令
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(segment.start_time),
                    "-i", video_path,
                    "-t", str(segment.duration),
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    str(segment_path)
                ]
                
                subprocess.run(cmd, capture_output=True, check=True)
                segment.segment_path = str(segment_path)
                
                # 生成缩略图
                thumb_cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(segment.start_time + segment.duration / 2),
                    "-i", video_path,
                    "-vframes", "1",
                    "-q:v", "2",
                    str(thumbnail_path)
                ]
                subprocess.run(thumb_cmd, capture_output=True)
                if thumbnail_path.exists():
                    segment.thumbnail_path = str(thumbnail_path)
                
                # 更新进度
                self._progress[video_id].processed_segments = i + 1
                
            except subprocess.CalledProcessError as e:
                logger.error(f"切割片段失败 {segment.segment_id}: {e}")
                segment.segment_path = video_path  # 回退使用原视频
        
        return segments
    
    async def _batch_generate_tags(
        self,
        segments: List[VideoSegmentInfo]
    ) -> List[VideoSegmentInfo]:
        """
        批量生成标签（优先使用本地 Ollama 视觉模型，回退到 Gemini）
        
        标签类型（Requirements 16.6）：
        - scene_type: 室内/室外/城市/自然
        - time: 白天/夜晚/黄昏/黎明
        - shot_type: 全景/中景/特写/过肩
        - mood: 紧张/浪漫/悲伤/欢乐/悬疑
        - action: 对话/追逐/打斗/静态
        - characters: 单人/双人/群戏/无人
        - free_tags: 自由标签列表
        """
        # 优先尝试本地 Ollama 视觉模型
        use_local_vision = await self._try_local_vision(segments)
        if use_local_vision:
            return segments
        
        # 回退到 Gemini
        if not self.gemini_api_key:
            logger.warning("未配置 Gemini API Key 且本地视觉模型不可用，使用基础标签")
            for segment in segments:
                segment.tags = self._generate_basic_tags(segment)
                segment.description = segment.tags.get("summary", "")
            return segments
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            for segment in segments:
                try:
                    # 如果有缩略图，使用图片分析
                    if segment.thumbnail_path and Path(segment.thumbnail_path).exists():
                        tags = await self._generate_tags_from_image(
                            model, segment.thumbnail_path
                        )
                    else:
                        # 使用文件名和时间信息生成基础标签
                        tags = self._generate_basic_tags(segment)
                    
                    segment.tags = tags
                    segment.description = tags.get("summary", "")
                    
                except Exception as e:
                    logger.error(f"生成标签失败 {segment.segment_id}: {e}")
                    segment.tags = self._generate_basic_tags(segment)
            
        except Exception as e:
            logger.error(f"Gemini 初始化失败: {e}")
        
        return segments
    
    async def _try_local_vision(self, segments: List[VideoSegmentInfo]) -> bool:
        """
        尝试使用本地 Ollama 视觉模型生成标签
        
        Returns:
            True 如果成功使用本地模型，False 需要回退到 Gemini
        """
        try:
            from services.ollama_vision import get_vision_provider
            
            vision = get_vision_provider()
            
            # 检查视觉模型是否可用
            if not await vision.check_availability():
                logger.info("本地视觉模型不可用，将使用 Gemini")
                return False
            
            logger.info(f"使用本地视觉模型 ({vision.model}) 生成标签...")
            
            total = len(segments)
            for i, segment in enumerate(segments):
                try:
                    if segment.thumbnail_path and Path(segment.thumbnail_path).exists():
                        tags = await vision.analyze_image(segment.thumbnail_path)
                        segment.tags = tags
                        segment.description = tags.get("summary", "")
                        logger.debug(f"片段 {i+1}/{total} 标签生成完成")
                    else:
                        segment.tags = self._generate_basic_tags(segment)
                        segment.description = segment.tags.get("summary", "")
                except Exception as e:
                    logger.warning(f"本地视觉分析失败 {segment.segment_id}: {e}")
                    segment.tags = self._generate_basic_tags(segment)
                    segment.description = segment.tags.get("summary", "")
            
            logger.info(f"本地视觉模型标签生成完成，共 {total} 个片段")
            return True
            
        except ImportError:
            logger.debug("ollama_vision 模块未安装")
            return False
        except Exception as e:
            logger.warning(f"本地视觉模型初始化失败: {e}")
            return False
    
    async def _generate_tags_from_image(
        self,
        model,
        image_path: str
    ) -> Dict[str, Any]:
        """使用 Gemini 分析图片生成标签"""
        import PIL.Image
        
        image = PIL.Image.open(image_path)
        
        prompt = """分析这张视频截图，返回 JSON 格式的标签：
{
  "scene_type": "室内/室外/城市/自然 之一",
  "time": "白天/夜晚/黄昏/黎明 之一",
  "shot_type": "全景/中景/特写/过肩 之一",
  "mood": "紧张/浪漫/悲伤/欢乐/悬疑/平静 之一",
  "action": "对话/追逐/打斗/静态 之一",
  "characters": "单人/双人/群戏/无人 之一",
  "free_tags": ["标签1", "标签2", "标签3"],
  "summary": "一句话描述画面内容"
}
只返回 JSON，不要其他内容。"""
        
        response = model.generate_content([prompt, image])
        
        # 解析 JSON
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return json.loads(text)
    
    def _generate_basic_tags(self, segment: VideoSegmentInfo) -> Dict[str, Any]:
        """生成基础标签（无 AI 时的回退）"""
        return {
            "scene_type": "未知",
            "time": "未知",
            "shot_type": "未知",
            "mood": "未知",
            "action": "未知",
            "characters": "未知",
            "free_tags": [],
            "summary": f"视频片段 {segment.start_time:.1f}s - {segment.end_time:.1f}s"
        }
    
    async def _generate_embeddings(
        self,
        segments: List[VideoSegmentInfo]
    ) -> List[VideoSegmentInfo]:
        """生成向量嵌入"""
        model = self._get_embedding_model()
        if model is None:
            return segments
        
        for segment in segments:
            try:
                # 使用描述和标签生成文本
                text_parts = []
                if segment.description:
                    text_parts.append(segment.description)
                if segment.tags:
                    for key, value in segment.tags.items():
                        if key == "free_tags" and isinstance(value, list):
                            text_parts.extend(value)
                        elif isinstance(value, str) and value != "未知":
                            text_parts.append(value)
                
                text = " ".join(text_parts) if text_parts else "video segment"
                
                # 生成嵌入
                embedding = model.encode(text).tolist()
                segment.tags["embedding"] = embedding
                
            except Exception as e:
                logger.error(f"生成嵌入失败 {segment.segment_id}: {e}")
        
        return segments
    
    def get_progress(self, video_id: str) -> Optional[PreprocessProgress]:
        """获取预处理进度"""
        return self._progress.get(video_id)
    
    def _update_progress(
        self,
        video_id: str,
        status: PreprocessStatus,
        progress: float,
        message: str
    ):
        """更新进度"""
        if video_id in self._progress:
            self._progress[video_id].status = status
            self._progress[video_id].progress = progress
            self._progress[video_id].message = message


# 全局预处理器实例
_preprocessor: Optional[VideoPreprocessor] = None


def get_video_preprocessor() -> VideoPreprocessor:
    """获取视频预处理器实例"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = VideoPreprocessor()
    return _preprocessor
