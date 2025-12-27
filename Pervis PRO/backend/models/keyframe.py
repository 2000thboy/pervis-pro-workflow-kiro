# -*- coding: utf-8 -*-
"""
关键帧数据模型

Feature: pervis-asset-tagging
Task: 6.2 关键帧数据模型

定义关键帧的数据结构和配置类。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

# 从 database 模块导入 SQLAlchemy Base
from database import Base


# ============================================================
# 枚举类型
# ============================================================

class ExtractionStrategy(str, Enum):
    """关键帧提取策略"""
    SCENE_CHANGE = "scene_change"   # 场景变化检测
    INTERVAL = "interval"           # 固定间隔
    MOTION = "motion"               # 动作峰值
    HYBRID = "hybrid"               # 混合策略（推荐）


# ============================================================
# 配置数据类
# ============================================================

@dataclass
class KeyFrameConfig:
    """关键帧提取配置"""
    strategy: ExtractionStrategy = ExtractionStrategy.HYBRID
    min_frames: int = 1              # 最小帧数
    max_frames: int = 20             # 最大帧数
    interval_seconds: float = 5.0    # 固定间隔（秒）
    motion_threshold: float = 0.3    # 运动阈值
    scene_threshold: float = 30.0    # 场景变化阈值
    thumbnail_width: int = 320       # 缩略图宽度
    thumbnail_height: int = 180      # 缩略图高度
    thumbnail_format: str = "jpg"    # 缩略图格式
    
    @property
    def thumbnail_size(self) -> Tuple[int, int]:
        return (self.thumbnail_width, self.thumbnail_height)
    
    def get_frame_limits(self, duration: float) -> Tuple[int, int]:
        """根据素材时长获取帧数限制"""
        if duration < 5:
            return (1, 3)
        elif duration < 30:
            return (3, 10)
        elif duration < 120:
            return (5, 20)
        else:
            return (10, 50)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "min_frames": self.min_frames,
            "max_frames": self.max_frames,
            "interval_seconds": self.interval_seconds,
            "motion_threshold": self.motion_threshold,
            "scene_threshold": self.scene_threshold,
            "thumbnail_size": self.thumbnail_size,
            "thumbnail_format": self.thumbnail_format,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyFrameConfig":
        strategy = data.get("strategy", "hybrid")
        if isinstance(strategy, str):
            strategy = ExtractionStrategy(strategy)
        
        return cls(
            strategy=strategy,
            min_frames=data.get("min_frames", 1),
            max_frames=data.get("max_frames", 20),
            interval_seconds=data.get("interval_seconds", 5.0),
            motion_threshold=data.get("motion_threshold", 0.3),
            scene_threshold=data.get("scene_threshold", 30.0),
            thumbnail_width=data.get("thumbnail_width", 320),
            thumbnail_height=data.get("thumbnail_height", 180),
            thumbnail_format=data.get("thumbnail_format", "jpg"),
        )


# ============================================================
# 关键帧数据类
# ============================================================

@dataclass
class KeyFrameData:
    """关键帧数据（内存中使用）"""
    keyframe_id: str                      # 关键帧 ID
    asset_id: str                         # 素材 ID
    frame_index: int                      # 帧序号
    timestamp: float                      # 时间戳（秒）
    timecode: str                         # SMPTE 时间码
    image_path: str                       # 缩略图路径
    scene_id: int = 0                     # 场景 ID
    
    # 元数据
    motion_score: float = 0.0             # 运动强度 (0-1)
    brightness: float = 128.0             # 亮度值 (0-255)
    contrast: float = 0.0                 # 对比度值
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    is_scene_start: bool = False          # 是否场景起始帧
    
    # 视觉嵌入
    visual_embedding: Optional[List[float]] = None
    
    # 图像尺寸
    image_width: int = 320
    image_height: int = 180
    
    @property
    def image_size(self) -> Tuple[int, int]:
        return (self.image_width, self.image_height)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyframe_id": self.keyframe_id,
            "asset_id": self.asset_id,
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "timecode": self.timecode,
            "image_path": self.image_path,
            "scene_id": self.scene_id,
            "motion_score": self.motion_score,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "dominant_colors": self.dominant_colors,
            "is_scene_start": self.is_scene_start,
            "has_embedding": self.visual_embedding is not None,
            "image_size": self.image_size,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyFrameData":
        return cls(
            keyframe_id=data["keyframe_id"],
            asset_id=data["asset_id"],
            frame_index=data["frame_index"],
            timestamp=data["timestamp"],
            timecode=data.get("timecode", "00:00:00:00"),
            image_path=data["image_path"],
            scene_id=data.get("scene_id", 0),
            motion_score=data.get("motion_score", 0.0),
            brightness=data.get("brightness", 128.0),
            contrast=data.get("contrast", 0.0),
            dominant_colors=data.get("dominant_colors", []),
            is_scene_start=data.get("is_scene_start", False),
            visual_embedding=data.get("visual_embedding"),
            image_width=data.get("image_width", 320),
            image_height=data.get("image_height", 180),
        )


# ============================================================
# 数据库模型
# ============================================================

class KeyFrame(Base):
    """关键帧数据库模型"""
    __tablename__ = "keyframes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyframe_id = Column(String(64), unique=True, nullable=False, index=True)
    asset_id = Column(String(64), nullable=False, index=True)
    
    # 帧信息
    frame_index = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)  # 秒
    timecode = Column(String(20), default="00:00:00:00")
    
    # 图像信息
    image_path = Column(String(512), nullable=False)
    image_width = Column(Integer, default=320)
    image_height = Column(Integer, default=180)
    
    # 场景信息
    scene_id = Column(Integer, default=0)
    is_scene_start = Column(Boolean, default=False)
    
    # 元数据
    motion_score = Column(Float, default=0.0)
    brightness = Column(Float, default=128.0)
    contrast = Column(Float, default=0.0)
    dominant_colors = Column(JSON, default=list)
    
    # 视觉嵌入（存储为 JSON）
    visual_embedding = Column(JSON, nullable=True)
    has_embedding = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_data(self) -> KeyFrameData:
        """转换为数据类"""
        return KeyFrameData(
            keyframe_id=self.keyframe_id,
            asset_id=self.asset_id,
            frame_index=self.frame_index,
            timestamp=self.timestamp,
            timecode=self.timecode,
            image_path=self.image_path,
            scene_id=self.scene_id,
            motion_score=self.motion_score,
            brightness=self.brightness,
            contrast=self.contrast,
            dominant_colors=self.dominant_colors or [],
            is_scene_start=self.is_scene_start,
            visual_embedding=self.visual_embedding,
            image_width=self.image_width,
            image_height=self.image_height,
        )
    
    @classmethod
    def from_data(cls, data: KeyFrameData) -> "KeyFrame":
        """从数据类创建"""
        return cls(
            keyframe_id=data.keyframe_id,
            asset_id=data.asset_id,
            frame_index=data.frame_index,
            timestamp=data.timestamp,
            timecode=data.timecode,
            image_path=data.image_path,
            image_width=data.image_width,
            image_height=data.image_height,
            scene_id=data.scene_id,
            is_scene_start=data.is_scene_start,
            motion_score=data.motion_score,
            brightness=data.brightness,
            contrast=data.contrast,
            dominant_colors=data.dominant_colors,
            visual_embedding=data.visual_embedding,
            has_embedding=data.visual_embedding is not None,
        )


class KeyFrameExtractionJob(Base):
    """关键帧提取任务"""
    __tablename__ = "keyframe_extraction_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    asset_id = Column(String(64), nullable=False, index=True)
    
    # 配置
    config = Column(JSON, default=dict)
    
    # 状态
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # 结果
    total_frames = Column(Integer, default=0)
    extracted_frames = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


# ============================================================
# 辅助函数
# ============================================================

def frame_to_timecode(frame_index: int, fps: float = 24.0) -> str:
    """帧序号转 SMPTE 时间码"""
    total_seconds = frame_index / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int((total_seconds % 1) * fps)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def timestamp_to_timecode(timestamp: float, fps: float = 24.0) -> str:
    """时间戳转 SMPTE 时间码"""
    hours = int(timestamp // 3600)
    minutes = int((timestamp % 3600) // 60)
    seconds = int(timestamp % 60)
    frames = int((timestamp % 1) * fps)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def timecode_to_timestamp(timecode: str, fps: float = 24.0) -> float:
    """SMPTE 时间码转时间戳"""
    parts = timecode.split(":")
    if len(parts) != 4:
        return 0.0
    
    hours, minutes, seconds, frames = map(int, parts)
    return hours * 3600 + minutes * 60 + seconds + frames / fps


def generate_keyframe_id(asset_id: str, frame_index: int) -> str:
    """生成关键帧 ID"""
    return f"kf_{asset_id}_{frame_index:06d}"
