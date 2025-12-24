"""
时间轴服务
管理时间轴和视频片段的CRUD操作
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import Timeline, Clip, Asset

logger = logging.getLogger(__name__)


class ClipData:
    """Clip数据传输对象"""
    def __init__(self, data: dict):
        self.asset_id = data['asset_id']
        self.start_time = data['start_time']
        self.end_time = data['end_time']
        self.trim_start = data.get('trim_start', 0.0)
        self.trim_end = data.get('trim_end')
        self.volume = data.get('volume', 1.0)
        self.is_muted = data.get('is_muted', 0)
        self.audio_fade_in = data.get('audio_fade_in', 0.0)
        self.audio_fade_out = data.get('audio_fade_out', 0.0)
        self.transition_type = data.get('transition_type')
        self.transition_duration = data.get('transition_duration', 0.0)
        self.order_index = data.get('order_index', 0)
        self.clip_metadata = data.get('clip_metadata', {})


class TimelineService:
    """时间轴管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_timeline(
        self,
        project_id: str,
        name: str = "主时间轴"
    ) -> Timeline:
        """
        创建新的时间轴
        
        Args:
            project_id: 项目ID
            name: 时间轴名称
            
        Returns:
            Timeline对象
        """
        try:
            timeline = Timeline(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=name,
                duration=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(timeline)
            self.db.commit()
            self.db.refresh(timeline)
            
            logger.info(f"Timeline created: {timeline.id}")
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to create timeline: {e}")
            self.db.rollback()
            raise
    
    def get_timeline(self, timeline_id: str) -> Optional[Timeline]:
        """
        获取时间轴
        
        Args:
            timeline_id: 时间轴ID
            
        Returns:
            Timeline对象，不存在返回None
        """
        return self.db.query(Timeline).filter(
            Timeline.id == timeline_id
        ).first()
    
    def get_timeline_with_clips(self, timeline_id: str) -> Optional[Dict]:
        """
        获取时间轴及其所有片段
        
        Args:
            timeline_id: 时间轴ID
            
        Returns:
            包含时间轴和片段的字典
        """
        timeline = self.get_timeline(timeline_id)
        if not timeline:
            return None
        
        clips = self.db.query(Clip).filter(
            Clip.timeline_id == timeline_id
        ).order_by(Clip.order_index).all()
        
        return {
            'id': timeline.id,
            'project_id': timeline.project_id,
            'name': timeline.name,
            'duration': timeline.duration,
            'created_at': timeline.created_at.isoformat() if timeline.created_at else None,
            'updated_at': timeline.updated_at.isoformat() if timeline.updated_at else None,
            'clips': [self._clip_to_dict(clip) for clip in clips]
        }
    
    async def get_timeline_async(self, timeline_id: str) -> Optional[Dict]:
        """
        异步获取时间轴（用于渲染服务）
        
        Args:
            timeline_id: 时间轴ID
            
        Returns:
            时间轴字典
        """
        return self.get_timeline_with_clips(timeline_id)
    
    def add_clip(
        self,
        timeline_id: str,
        clip_data: ClipData
    ) -> Clip:
        """
        添加视频片段到时间轴
        
        Args:
            timeline_id: 时间轴ID
            clip_data: 片段数据
            
        Returns:
            Clip对象
        """
        try:
            # 验证素材存在
            asset = self.db.query(Asset).filter(
                Asset.id == clip_data.asset_id
            ).first()
            
            if not asset:
                raise ValueError(f"Asset not found: {clip_data.asset_id}")
            
            # 创建Clip
            clip = Clip(
                id=str(uuid.uuid4()),
                timeline_id=timeline_id,
                asset_id=clip_data.asset_id,
                start_time=clip_data.start_time,
                end_time=clip_data.end_time,
                trim_start=clip_data.trim_start,
                trim_end=clip_data.trim_end,
                volume=clip_data.volume,
                is_muted=clip_data.is_muted,
                audio_fade_in=clip_data.audio_fade_in,
                audio_fade_out=clip_data.audio_fade_out,
                transition_type=clip_data.transition_type,
                transition_duration=clip_data.transition_duration,
                order_index=clip_data.order_index,
                clip_metadata=clip_data.clip_metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(clip)
            
            # 更新时间轴时长
            self._update_timeline_duration(timeline_id)
            
            self.db.commit()
            self.db.refresh(clip)
            
            logger.info(f"Clip added: {clip.id}")
            return clip
            
        except Exception as e:
            logger.error(f"Failed to add clip: {e}")
            self.db.rollback()
            raise
    
    async def create_timeline_from_autocut(
        self,
        project_id: str,
        autocut_timeline: Dict[str, Any],
        name: str = "AutoCut时间轴"
    ) -> Timeline:
        """
        从AutoCut Orchestrator的决策结果创建时间轴
        
        这是MVP的核心方法：强制使用智能决策结果
        """
        try:
            # 创建时间轴
            timeline = Timeline(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=name,
                duration=autocut_timeline.get("total_duration", 0.0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(timeline)
            self.db.flush()  # 获取timeline.id
            
            # 添加所有智能决策的片段
            clips_data = autocut_timeline.get("clips", [])
            logger.info(f"🎬 从AutoCut决策创建 {len(clips_data)} 个片段")
            
            for clip_data in clips_data:
                if not clip_data.get("asset_id"):
                    logger.warning(f"跳过无素材的片段: {clip_data}")
                    continue
                
                clip = Clip(
                    id=str(uuid.uuid4()),
                    timeline_id=timeline.id,
                    asset_id=clip_data["asset_id"],
                    start_time=clip_data["start_time"],
                    end_time=clip_data["end_time"],
                    trim_start=0.0,
                    trim_end=clip_data["duration"],
                    volume=1.0,
                    is_muted=0,
                    audio_fade_in=0.0,
                    audio_fade_out=0.0,
                    transition_type=None,
                    transition_duration=0.0,
                    order_index=clip_data["order_index"],
                    clip_metadata={
                        "beat_id": clip_data.get("beat_id"),
                        "confidence": clip_data.get("confidence", 0.0),
                        "reasoning": clip_data.get("reasoning", ""),
                        "generated_by": "AutoCut Orchestrator"
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(clip)
                logger.debug(f"✅ 添加智能片段: {clip_data['asset_id']} ({clip_data['duration']}秒)")
            
            self.db.commit()
            self.db.refresh(timeline)
            
            logger.info(f"🎬 AutoCut时间轴创建完成: {timeline.id}")
            return timeline
            
        except Exception as e:
            logger.error(f"❌ AutoCut时间轴创建失败: {e}")
            self.db.rollback()
            raise
    
    def update_clip(
        self,
        clip_id: str,
        updates: dict
    ) -> Optional[Clip]:
        """
        更新片段属性
        
        Args:
            clip_id: 片段ID
            updates: 更新的字段字典
            
        Returns:
            更新后的Clip对象
        """
        try:
            clip = self.db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                return None
            
            # 更新允许的字段
            allowed_fields = [
                'start_time', 'end_time', 'trim_start', 'trim_end',
                'volume', 'is_muted', 'audio_fade_in', 'audio_fade_out',
                'transition_type', 'transition_duration', 'order_index',
                'clip_metadata'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(clip, field, value)
            
            clip.updated_at = datetime.utcnow()
            
            # 更新时间轴时长
            self._update_timeline_duration(clip.timeline_id)
            
            self.db.commit()
            self.db.refresh(clip)
            
            logger.info(f"Clip updated: {clip_id}")
            return clip
            
        except Exception as e:
            logger.error(f"Failed to update clip: {e}")
            self.db.rollback()
            raise
    
    def delete_clip(self, clip_id: str) -> bool:
        """
        删除片段
        
        Args:
            clip_id: 片段ID
            
        Returns:
            是否成功删除
        """
        try:
            clip = self.db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                return False
            
            timeline_id = clip.timeline_id
            
            self.db.delete(clip)
            
            # 更新时间轴时长
            self._update_timeline_duration(timeline_id)
            
            self.db.commit()
            
            logger.info(f"Clip deleted: {clip_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete clip: {e}")
            self.db.rollback()
            return False
    
    def reorder_clips(
        self,
        timeline_id: str,
        clip_order: List[str]
    ) -> bool:
        """
        重新排序片段
        
        Args:
            timeline_id: 时间轴ID
            clip_order: 片段ID列表（按新顺序）
            
        Returns:
            是否成功
        """
        try:
            for index, clip_id in enumerate(clip_order):
                clip = self.db.query(Clip).filter(
                    and_(
                        Clip.id == clip_id,
                        Clip.timeline_id == timeline_id
                    )
                ).first()
                
                if clip:
                    clip.order_index = index
                    clip.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Clips reordered in timeline: {timeline_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reorder clips: {e}")
            self.db.rollback()
            return False
    
    def validate_timeline(self, timeline_id: str) -> Dict[str, any]:
        """
        验证时间轴完整性
        
        Args:
            timeline_id: 时间轴ID
            
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        clips = self.db.query(Clip).filter(
            Clip.timeline_id == timeline_id
        ).order_by(Clip.order_index).all()
        
        # 检查素材文件存在
        for clip in clips:
            asset = self.db.query(Asset).filter(
                Asset.id == clip.asset_id
            ).first()
            
            if not asset:
                errors.append(f"Clip {clip.id}: Asset not found")
            elif not asset.file_path:
                errors.append(f"Clip {clip.id}: Asset has no file path")
        
        # 检查时间重叠
        for i in range(len(clips) - 1):
            if clips[i].end_time > clips[i + 1].start_time:
                warnings.append(
                    f"Clips {clips[i].id} and {clips[i + 1].id} overlap"
                )
        
        # 检查时间有效性
        for clip in clips:
            if clip.start_time >= clip.end_time:
                errors.append(f"Clip {clip.id}: Invalid time range")
            
            if clip.trim_start < 0:
                errors.append(f"Clip {clip.id}: Negative trim_start")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _update_timeline_duration(self, timeline_id: str):
        """更新时间轴总时长"""
        clips = self.db.query(Clip).filter(
            Clip.timeline_id == timeline_id
        ).all()
        
        if clips:
            max_end_time = max(clip.end_time for clip in clips)
        else:
            max_end_time = 0.0
        
        timeline = self.get_timeline(timeline_id)
        if timeline:
            timeline.duration = max_end_time
            timeline.updated_at = datetime.utcnow()
    
    def _clip_to_dict(self, clip: Clip) -> dict:
        """将Clip对象转换为字典"""
        return {
            'id': clip.id,
            'timeline_id': clip.timeline_id,
            'asset_id': clip.asset_id,
            'start_time': clip.start_time,
            'end_time': clip.end_time,
            'trim_start': clip.trim_start,
            'trim_end': clip.trim_end,
            'volume': clip.volume,
            'is_muted': clip.is_muted,
            'audio_fade_in': clip.audio_fade_in,
            'audio_fade_out': clip.audio_fade_out,
            'transition_type': clip.transition_type,
            'transition_duration': clip.transition_duration,
            'order_index': clip.order_index,
            'clip_metadata': clip.clip_metadata,
            'created_at': clip.created_at.isoformat() if clip.created_at else None,
            'updated_at': clip.updated_at.isoformat() if clip.updated_at else None
        }
