# -*- coding: utf-8 -*-
"""
关键帧存储服务

Feature: pervis-asset-tagging
Task: 6.3 关键帧存储服务

提供关键帧的存储、查询和管理功能：
- 关键帧缩略图存储
- 关键帧元数据存储
- 按素材 ID 查询关键帧
- 视觉嵌入存储和搜索
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.keyframe import KeyFrame, KeyFrameData, KeyFrameExtractionJob

logger = logging.getLogger(__name__)


class KeyFrameStore:
    """关键帧存储服务"""
    
    def __init__(
        self,
        db: Session,
        storage_dir: str = "data/keyframes",
        cache_dir: str = "data/keyframe_cache",
    ):
        self.db = db
        self.storage_dir = Path(storage_dir)
        self.cache_dir = Path(cache_dir)
        
        # 确保目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._cache: Dict[str, List[KeyFrameData]] = {}
    
    # ============================================================
    # 关键帧 CRUD 操作
    # ============================================================
    
    async def save_keyframe(self, keyframe: KeyFrameData) -> bool:
        """保存单个关键帧"""
        try:
            # 检查是否已存在
            existing = self.db.query(KeyFrame).filter(
                KeyFrame.keyframe_id == keyframe.keyframe_id
            ).first()
            
            if existing:
                # 更新
                existing.timestamp = keyframe.timestamp
                existing.timecode = keyframe.timecode
                existing.image_path = keyframe.image_path
                existing.scene_id = keyframe.scene_id
                existing.motion_score = keyframe.motion_score
                existing.brightness = keyframe.brightness
                existing.contrast = keyframe.contrast
                existing.dominant_colors = keyframe.dominant_colors
                existing.is_scene_start = keyframe.is_scene_start
                existing.visual_embedding = keyframe.visual_embedding
                existing.has_embedding = keyframe.visual_embedding is not None
                existing.updated_at = datetime.utcnow()
            else:
                # 创建新记录
                db_keyframe = KeyFrame.from_data(keyframe)
                self.db.add(db_keyframe)
            
            self.db.commit()
            
            # 更新缓存
            self._update_cache(keyframe)
            
            return True
            
        except Exception as e:
            logger.error(f"保存关键帧失败: {e}")
            self.db.rollback()
            return False
    
    async def save_keyframes_batch(self, keyframes: List[KeyFrameData]) -> int:
        """批量保存关键帧"""
        saved_count = 0
        
        try:
            for keyframe in keyframes:
                existing = self.db.query(KeyFrame).filter(
                    KeyFrame.keyframe_id == keyframe.keyframe_id
                ).first()
                
                if existing:
                    existing.timestamp = keyframe.timestamp
                    existing.timecode = keyframe.timecode
                    existing.image_path = keyframe.image_path
                    existing.scene_id = keyframe.scene_id
                    existing.motion_score = keyframe.motion_score
                    existing.brightness = keyframe.brightness
                    existing.contrast = keyframe.contrast
                    existing.dominant_colors = keyframe.dominant_colors
                    existing.is_scene_start = keyframe.is_scene_start
                    existing.visual_embedding = keyframe.visual_embedding
                    existing.has_embedding = keyframe.visual_embedding is not None
                    existing.updated_at = datetime.utcnow()
                else:
                    db_keyframe = KeyFrame.from_data(keyframe)
                    self.db.add(db_keyframe)
                
                saved_count += 1
                self._update_cache(keyframe)
            
            self.db.commit()
            logger.info(f"批量保存 {saved_count} 个关键帧")
            
        except Exception as e:
            logger.error(f"批量保存关键帧失败: {e}")
            self.db.rollback()
            saved_count = 0
        
        return saved_count
    
    async def get_keyframe(self, keyframe_id: str) -> Optional[KeyFrameData]:
        """获取单个关键帧"""
        try:
            db_keyframe = self.db.query(KeyFrame).filter(
                KeyFrame.keyframe_id == keyframe_id
            ).first()
            
            if db_keyframe:
                return db_keyframe.to_data()
            return None
            
        except Exception as e:
            logger.error(f"获取关键帧失败: {e}")
            return None
    
    async def get_keyframes_by_asset(
        self,
        asset_id: str,
        include_embeddings: bool = False,
    ) -> List[KeyFrameData]:
        """按素材 ID 查询关键帧"""
        # 先检查缓存
        if asset_id in self._cache and not include_embeddings:
            return self._cache[asset_id]
        
        try:
            query = self.db.query(KeyFrame).filter(
                KeyFrame.asset_id == asset_id
            ).order_by(KeyFrame.timestamp)
            
            keyframes = []
            for db_kf in query.all():
                kf_data = db_kf.to_data()
                if not include_embeddings:
                    kf_data.visual_embedding = None
                keyframes.append(kf_data)
            
            # 更新缓存（不含嵌入）
            if not include_embeddings:
                self._cache[asset_id] = keyframes
            
            return keyframes
            
        except Exception as e:
            logger.error(f"查询关键帧失败: {e}")
            return []
    
    async def delete_keyframes_by_asset(self, asset_id: str) -> int:
        """删除素材的所有关键帧"""
        try:
            # 获取要删除的关键帧
            keyframes = self.db.query(KeyFrame).filter(
                KeyFrame.asset_id == asset_id
            ).all()
            
            # 删除缩略图文件
            for kf in keyframes:
                if kf.image_path and os.path.exists(kf.image_path):
                    try:
                        os.remove(kf.image_path)
                    except Exception as e:
                        logger.warning(f"删除缩略图失败: {e}")
            
            # 删除数据库记录
            deleted = self.db.query(KeyFrame).filter(
                KeyFrame.asset_id == asset_id
            ).delete()
            
            self.db.commit()
            
            # 清除缓存
            if asset_id in self._cache:
                del self._cache[asset_id]
            
            logger.info(f"删除素材 {asset_id} 的 {deleted} 个关键帧")
            return deleted
            
        except Exception as e:
            logger.error(f"删除关键帧失败: {e}")
            self.db.rollback()
            return 0
    
    # ============================================================
    # 视觉嵌入操作
    # ============================================================
    
    async def update_embedding(
        self,
        keyframe_id: str,
        embedding: List[float],
    ) -> bool:
        """更新关键帧的视觉嵌入"""
        try:
            db_keyframe = self.db.query(KeyFrame).filter(
                KeyFrame.keyframe_id == keyframe_id
            ).first()
            
            if not db_keyframe:
                return False
            
            db_keyframe.visual_embedding = embedding
            db_keyframe.has_embedding = True
            db_keyframe.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新嵌入失败: {e}")
            self.db.rollback()
            return False
    
    async def search_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        asset_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """通过视觉嵌入搜索关键帧"""
        import numpy as np
        
        try:
            # 构建查询
            query = self.db.query(KeyFrame).filter(
                KeyFrame.has_embedding == True
            )
            
            if asset_ids:
                query = query.filter(KeyFrame.asset_id.in_(asset_ids))
            
            # 获取所有有嵌入的关键帧
            keyframes = query.all()
            
            if not keyframes:
                return []
            
            # 计算相似度
            query_vec = np.array(query_embedding)
            query_norm = np.linalg.norm(query_vec)
            
            if query_norm == 0:
                return []
            
            results = []
            for kf in keyframes:
                if not kf.visual_embedding:
                    continue
                
                kf_vec = np.array(kf.visual_embedding)
                kf_norm = np.linalg.norm(kf_vec)
                
                if kf_norm == 0:
                    continue
                
                # 余弦相似度
                similarity = float(np.dot(query_vec, kf_vec) / (query_norm * kf_norm))
                
                results.append({
                    "keyframe_id": kf.keyframe_id,
                    "asset_id": kf.asset_id,
                    "timestamp": kf.timestamp,
                    "timecode": kf.timecode,
                    "image_path": kf.image_path,
                    "score": similarity,
                })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"嵌入搜索失败: {e}")
            return []
    
    # ============================================================
    # 提取任务管理
    # ============================================================
    
    async def create_extraction_job(
        self,
        asset_id: str,
        config: Dict[str, Any],
    ) -> str:
        """创建提取任务"""
        import uuid
        
        job_id = f"kf_job_{uuid.uuid4().hex[:12]}"
        
        try:
            job = KeyFrameExtractionJob(
                job_id=job_id,
                asset_id=asset_id,
                config=config,
                status="pending",
            )
            self.db.add(job)
            self.db.commit()
            
            return job_id
            
        except Exception as e:
            logger.error(f"创建提取任务失败: {e}")
            self.db.rollback()
            return ""
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float = 0.0,
        error_message: str = "",
        extracted_frames: int = 0,
    ) -> bool:
        """更新任务状态"""
        try:
            job = self.db.query(KeyFrameExtractionJob).filter(
                KeyFrameExtractionJob.job_id == job_id
            ).first()
            
            if not job:
                return False
            
            job.status = status
            job.progress = progress
            job.error_message = error_message
            job.extracted_frames = extracted_frames
            
            if status == "running" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ("completed", "failed"):
                job.completed_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            self.db.rollback()
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            job = self.db.query(KeyFrameExtractionJob).filter(
                KeyFrameExtractionJob.job_id == job_id
            ).first()
            
            if not job:
                return None
            
            return {
                "job_id": job.job_id,
                "asset_id": job.asset_id,
                "status": job.status,
                "progress": job.progress,
                "error_message": job.error_message,
                "total_frames": job.total_frames,
                "extracted_frames": job.extracted_frames,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return None
    
    # ============================================================
    # 统计和缓存
    # ============================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            total_keyframes = self.db.query(KeyFrame).count()
            with_embeddings = self.db.query(KeyFrame).filter(
                KeyFrame.has_embedding == True
            ).count()
            
            # 按素材统计
            from sqlalchemy import func
            asset_stats = self.db.query(
                KeyFrame.asset_id,
                func.count(KeyFrame.id).label("count")
            ).group_by(KeyFrame.asset_id).all()
            
            return {
                "total_keyframes": total_keyframes,
                "with_embeddings": with_embeddings,
                "embedding_coverage": with_embeddings / total_keyframes if total_keyframes > 0 else 0,
                "assets_count": len(asset_stats),
                "avg_keyframes_per_asset": total_keyframes / len(asset_stats) if asset_stats else 0,
            }
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}
    
    def _update_cache(self, keyframe: KeyFrameData):
        """更新内存缓存"""
        asset_id = keyframe.asset_id
        
        if asset_id not in self._cache:
            self._cache[asset_id] = []
        
        # 查找并更新或添加
        found = False
        for i, kf in enumerate(self._cache[asset_id]):
            if kf.keyframe_id == keyframe.keyframe_id:
                # 不存储嵌入到缓存
                cached_kf = KeyFrameData(
                    keyframe_id=keyframe.keyframe_id,
                    asset_id=keyframe.asset_id,
                    frame_index=keyframe.frame_index,
                    timestamp=keyframe.timestamp,
                    timecode=keyframe.timecode,
                    image_path=keyframe.image_path,
                    scene_id=keyframe.scene_id,
                    motion_score=keyframe.motion_score,
                    brightness=keyframe.brightness,
                    contrast=keyframe.contrast,
                    dominant_colors=keyframe.dominant_colors,
                    is_scene_start=keyframe.is_scene_start,
                    image_width=keyframe.image_width,
                    image_height=keyframe.image_height,
                )
                self._cache[asset_id][i] = cached_kf
                found = True
                break
        
        if not found:
            cached_kf = KeyFrameData(
                keyframe_id=keyframe.keyframe_id,
                asset_id=keyframe.asset_id,
                frame_index=keyframe.frame_index,
                timestamp=keyframe.timestamp,
                timecode=keyframe.timecode,
                image_path=keyframe.image_path,
                scene_id=keyframe.scene_id,
                motion_score=keyframe.motion_score,
                brightness=keyframe.brightness,
                contrast=keyframe.contrast,
                dominant_colors=keyframe.dominant_colors,
                is_scene_start=keyframe.is_scene_start,
                image_width=keyframe.image_width,
                image_height=keyframe.image_height,
            )
            self._cache[asset_id].append(cached_kf)
            # 按时间戳排序
            self._cache[asset_id].sort(key=lambda x: x.timestamp)
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


# ============================================================
# 全局实例
# ============================================================

_keyframe_store: Optional[KeyFrameStore] = None


def get_keyframe_store(db: Session) -> KeyFrameStore:
    """获取关键帧存储实例"""
    global _keyframe_store
    
    if _keyframe_store is None:
        _keyframe_store = KeyFrameStore(db)
    
    return _keyframe_store
