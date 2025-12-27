# -*- coding: utf-8 -*-
"""
关键帧提取服务

Feature: pervis-asset-tagging
Task: 6.1 关键帧提取服务

支持的提取策略：
- scene_change: 场景变化检测（PySceneDetect）
- interval: 固定间隔提取
- motion: 动作峰值提取
- hybrid: 混合策略（推荐）
"""

import asyncio
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models.keyframe import (
    ExtractionStrategy,
    KeyFrameConfig,
    KeyFrameData,
    generate_keyframe_id,
    timestamp_to_timecode,
)

logger = logging.getLogger(__name__)


# ============================================================
# 提取结果
# ============================================================

@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    keyframes: List[KeyFrameData]
    total_frames: int
    duration: float
    fps: float
    error_message: str = ""
    extraction_time_ms: float = 0.0


# ============================================================
# 关键帧提取器
# ============================================================

class KeyFrameExtractor:
    """关键帧提取器"""
    
    def __init__(
        self,
        output_dir: str = "data/keyframes",
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
    ):
        self.output_dir = Path(output_dir)
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def extract(
        self,
        video_path: str,
        asset_id: str,
        config: Optional[KeyFrameConfig] = None,
    ) -> ExtractionResult:
        """提取关键帧"""
        start_time = datetime.now()
        
        if config is None:
            config = KeyFrameConfig()
        
        # 检查视频文件
        if not os.path.exists(video_path):
            return ExtractionResult(
                success=False,
                keyframes=[],
                total_frames=0,
                duration=0.0,
                fps=24.0,
                error_message=f"视频文件不存在: {video_path}",
            )
        
        try:
            # 获取视频信息
            video_info = await self._get_video_info(video_path)
            if not video_info:
                return ExtractionResult(
                    success=False,
                    keyframes=[],
                    total_frames=0,
                    duration=0.0,
                    fps=24.0,
                    error_message="无法获取视频信息",
                )
            
            duration = video_info["duration"]
            fps = video_info["fps"]
            total_frames = video_info["total_frames"]
            
            # 根据时长调整帧数限制
            min_frames, max_frames = config.get_frame_limits(duration)
            config.min_frames = max(config.min_frames, min_frames)
            config.max_frames = min(config.max_frames, max_frames)
            
            # 根据策略提取关键帧时间点
            if config.strategy == ExtractionStrategy.SCENE_CHANGE:
                timestamps = await self._extract_scene_change(video_path, config)
            elif config.strategy == ExtractionStrategy.INTERVAL:
                timestamps = self._extract_interval(duration, config)
            elif config.strategy == ExtractionStrategy.MOTION:
                timestamps = await self._extract_motion(video_path, config)
            else:  # HYBRID
                timestamps = await self._extract_hybrid(video_path, duration, config)
            
            # 限制帧数
            if len(timestamps) > config.max_frames:
                # 均匀采样
                step = len(timestamps) / config.max_frames
                timestamps = [timestamps[int(i * step)] for i in range(config.max_frames)]
            
            # 确保至少有最小帧数
            if len(timestamps) < config.min_frames and duration > 0:
                # 补充固定间隔帧
                interval = duration / (config.min_frames + 1)
                for i in range(config.min_frames):
                    t = interval * (i + 1)
                    if t not in timestamps:
                        timestamps.append(t)
                timestamps.sort()
            
            # 创建素材输出目录
            asset_output_dir = self.output_dir / asset_id
            asset_output_dir.mkdir(parents=True, exist_ok=True)
            
            # 提取帧图像
            keyframes = []
            for i, timestamp in enumerate(timestamps):
                frame_index = int(timestamp * fps)
                keyframe_id = generate_keyframe_id(asset_id, frame_index)
                
                # 生成缩略图文件名
                image_filename = f"frame_{frame_index:06d}_{timestamp:.2f}.{config.thumbnail_format}"
                image_path = asset_output_dir / image_filename
                
                # 提取帧
                success = await self._extract_frame(
                    video_path,
                    str(image_path),
                    timestamp,
                    config.thumbnail_size,
                )
                
                if success:
                    # 获取帧元数据
                    metadata = await self._get_frame_metadata(str(image_path))
                    
                    keyframe = KeyFrameData(
                        keyframe_id=keyframe_id,
                        asset_id=asset_id,
                        frame_index=frame_index,
                        timestamp=timestamp,
                        timecode=timestamp_to_timecode(timestamp, fps),
                        image_path=str(image_path),
                        scene_id=i,  # 简单使用序号作为场景 ID
                        motion_score=metadata.get("motion_score", 0.0),
                        brightness=metadata.get("brightness", 128.0),
                        contrast=metadata.get("contrast", 0.0),
                        dominant_colors=metadata.get("dominant_colors", []),
                        is_scene_start=(i == 0 or timestamp in timestamps[:1]),
                        image_width=config.thumbnail_width,
                        image_height=config.thumbnail_height,
                    )
                    keyframes.append(keyframe)
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExtractionResult(
                success=True,
                keyframes=keyframes,
                total_frames=total_frames,
                duration=duration,
                fps=fps,
                extraction_time_ms=elapsed_ms,
            )
            
        except Exception as e:
            logger.error(f"关键帧提取失败: {e}")
            return ExtractionResult(
                success=False,
                keyframes=[],
                total_frames=0,
                duration=0.0,
                fps=24.0,
                error_message=str(e),
            )
    
    async def _get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            
            import json
            data = json.loads(stdout.decode())
            
            # 查找视频流
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            # 解析帧率
            fps_str = video_stream.get("r_frame_rate", "24/1")
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den if den > 0 else 24.0
            else:
                fps = float(fps_str)
            
            # 获取时长
            duration = float(data.get("format", {}).get("duration", 0))
            
            # 计算总帧数
            total_frames = int(duration * fps)
            
            return {
                "duration": duration,
                "fps": fps,
                "total_frames": total_frames,
                "width": video_stream.get("width", 0),
                "height": video_stream.get("height", 0),
            }
            
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return None
    
    async def _extract_scene_change(
        self,
        video_path: str,
        config: KeyFrameConfig,
    ) -> List[float]:
        """场景变化检测提取"""
        timestamps = []
        
        try:
            # 尝试使用 PySceneDetect
            from scenedetect import detect, ContentDetector
            
            scene_list = detect(video_path, ContentDetector(threshold=config.scene_threshold))
            
            for scene in scene_list:
                # 获取场景开始时间
                start_time = scene[0].get_seconds()
                timestamps.append(start_time)
            
            # 如果没有检测到场景，添加开始帧
            if not timestamps:
                timestamps.append(0.0)
                
        except ImportError:
            logger.warning("PySceneDetect 未安装，使用 FFmpeg 场景检测")
            timestamps = await self._extract_scene_change_ffmpeg(video_path, config)
        except Exception as e:
            logger.error(f"场景检测失败: {e}")
            timestamps = [0.0]
        
        return timestamps
    
    async def _extract_scene_change_ffmpeg(
        self,
        video_path: str,
        config: KeyFrameConfig,
    ) -> List[float]:
        """使用 FFmpeg 进行场景检测"""
        timestamps = [0.0]  # 始终包含开始帧
        
        try:
            # 使用 FFmpeg 的 scene 滤镜
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", f"select='gt(scene,{config.scene_threshold/100})',showinfo",
                "-f", "null",
                "-",
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await result.communicate()
            
            # 解析输出获取时间戳
            import re
            for line in stderr.decode().split("\n"):
                match = re.search(r"pts_time:(\d+\.?\d*)", line)
                if match:
                    timestamp = float(match.group(1))
                    if timestamp not in timestamps:
                        timestamps.append(timestamp)
            
        except Exception as e:
            logger.error(f"FFmpeg 场景检测失败: {e}")
        
        return sorted(timestamps)
    
    def _extract_interval(
        self,
        duration: float,
        config: KeyFrameConfig,
    ) -> List[float]:
        """固定间隔提取"""
        timestamps = []
        
        interval = config.interval_seconds
        current = 0.0
        
        while current < duration:
            timestamps.append(current)
            current += interval
        
        # 确保包含最后一帧附近
        if timestamps and timestamps[-1] < duration - 1:
            timestamps.append(duration - 0.1)
        
        return timestamps
    
    async def _extract_motion(
        self,
        video_path: str,
        config: KeyFrameConfig,
    ) -> List[float]:
        """动作峰值提取"""
        # 简化实现：使用场景检测 + 间隔采样
        scene_timestamps = await self._extract_scene_change(video_path, config)
        
        # 在场景之间添加中间点
        timestamps = []
        for i, t in enumerate(scene_timestamps):
            timestamps.append(t)
            if i < len(scene_timestamps) - 1:
                mid = (t + scene_timestamps[i + 1]) / 2
                timestamps.append(mid)
        
        return sorted(set(timestamps))
    
    async def _extract_hybrid(
        self,
        video_path: str,
        duration: float,
        config: KeyFrameConfig,
    ) -> List[float]:
        """混合策略提取"""
        # 1. 场景变化检测
        scene_timestamps = await self._extract_scene_change(video_path, config)
        
        # 2. 固定间隔补充
        interval_timestamps = self._extract_interval(duration, config)
        
        # 3. 合并去重
        all_timestamps = set(scene_timestamps + interval_timestamps)
        
        # 4. 过滤太近的帧（至少间隔 0.5 秒）
        sorted_timestamps = sorted(all_timestamps)
        filtered = []
        last_t = -1.0
        
        for t in sorted_timestamps:
            if t - last_t >= 0.5:
                filtered.append(t)
                last_t = t
        
        return filtered
    
    async def _extract_frame(
        self,
        video_path: str,
        output_path: str,
        timestamp: float,
        size: Tuple[int, int],
    ) -> bool:
        """提取单帧"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-vf", f"scale={size[0]}:{size[1]}",
                "-y",
                output_path,
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()
            
            return os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"提取帧失败: {e}")
            return False
    
    async def _get_frame_metadata(self, image_path: str) -> Dict[str, Any]:
        """获取帧元数据"""
        metadata = {
            "motion_score": 0.0,
            "brightness": 128.0,
            "contrast": 0.0,
            "dominant_colors": [],
        }
        
        try:
            from PIL import Image
            import colorsys
            
            with Image.open(image_path) as img:
                # 转换为 RGB
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # 缩小图像以加速计算
                img_small = img.resize((50, 50))
                pixels = list(img_small.getdata())
                
                # 计算亮度
                brightness_values = [
                    0.299 * r + 0.587 * g + 0.114 * b
                    for r, g, b in pixels
                ]
                metadata["brightness"] = sum(brightness_values) / len(brightness_values)
                
                # 计算对比度（标准差）
                mean_brightness = metadata["brightness"]
                variance = sum((b - mean_brightness) ** 2 for b in brightness_values) / len(brightness_values)
                metadata["contrast"] = variance ** 0.5
                
                # 提取主色调（简单 K-means）
                from collections import Counter
                
                # 量化颜色
                quantized = [
                    (r // 32 * 32, g // 32 * 32, b // 32 * 32)
                    for r, g, b in pixels
                ]
                color_counts = Counter(quantized)
                dominant = color_counts.most_common(3)
                metadata["dominant_colors"] = [list(c[0]) for c in dominant]
                
        except Exception as e:
            logger.warning(f"获取帧元数据失败: {e}")
        
        return metadata


# ============================================================
# 全局实例
# ============================================================

_extractor: Optional[KeyFrameExtractor] = None


def get_keyframe_extractor() -> KeyFrameExtractor:
    """获取关键帧提取器实例"""
    global _extractor
    
    if _extractor is None:
        _extractor = KeyFrameExtractor()
    
    return _extractor


async def extract_keyframes(
    video_path: str,
    asset_id: str,
    config: Optional[KeyFrameConfig] = None,
) -> ExtractionResult:
    """便捷提取函数"""
    extractor = get_keyframe_extractor()
    return await extractor.extract(video_path, asset_id, config)
