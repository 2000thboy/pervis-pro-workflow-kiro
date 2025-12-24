"""
数据库服务层
Phase 2: 基础CRUD操作
P0 Fix: 异步化数据库操作
"""

from sqlalchemy.orm import Session
from database import Project, Beat, Asset, AssetSegment, AssetVector, FeedbackLog
from models.base import ProjectCreate, BeatCreate, AssetCreate
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

class DatabaseService:
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    # Project 操作
    async def create_project(self, project_data: ProjectCreate) -> Project:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._create_project_sync, 
            project_data
        )
    
    def _create_project_sync(self, project_data: ProjectCreate) -> Project:
        project = Project(
            id=f"proj_{uuid.uuid4().hex[:8]}",
            title=project_data.title,
            logline=project_data.logline,
            synopsis=project_data.synopsis,
            script_raw=project_data.script_raw,
            characters=[],
            current_stage="ANALYSIS"
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_project_sync,
            project_id
        )
    
    def _get_project_sync(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()
    
    async def list_projects(self) -> List[Project]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._list_projects_sync
        )
    
    def _list_projects_sync(self) -> List[Project]:
        return self.db.query(Project).order_by(Project.created_at.desc()).all()
    
    # Beat 操作
    async def create_beat(self, beat_data: BeatCreate, order_index: int = 0) -> Beat:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_beat_sync,
            beat_data,
            order_index
        )
    
    def _create_beat_sync(self, beat_data: BeatCreate, order_index: int = 0) -> Beat:
        beat = Beat(
            id=f"beat_{uuid.uuid4().hex[:8]}",
            project_id=beat_data.project_id,
            order_index=order_index,
            content=beat_data.content,
            emotion_tags=beat_data.emotion_tags,
            scene_tags=beat_data.scene_tags,
            action_tags=beat_data.action_tags,
            cinematography_tags=beat_data.cinematography_tags,
            duration=beat_data.duration,
            user_notes=beat_data.user_notes
        )
        self.db.add(beat)
        self.db.commit()
        self.db.refresh(beat)
        return beat
    
    async def get_beats_by_project(self, project_id: str) -> List[Beat]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_beats_by_project_sync,
            project_id
        )
    
    def _get_beats_by_project_sync(self, project_id: str) -> List[Beat]:
        return self.db.query(Beat).filter(
            Beat.project_id == project_id
        ).order_by(Beat.order_index).all()
    
    async def get_beat(self, beat_id: str) -> Optional[Beat]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_beat_sync,
            beat_id
        )
    
    def _get_beat_sync(self, beat_id: str) -> Optional[Beat]:
        return self.db.query(Beat).filter(Beat.id == beat_id).first()
    
    # Asset 操作
    async def create_asset(self, asset_data: AssetCreate) -> Asset:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_asset_sync,
            asset_data
        )
    
    def _create_asset_sync(self, asset_data: AssetCreate) -> Asset:
        asset = Asset(
            id=f"asset_{uuid.uuid4().hex[:8]}",
            project_id=asset_data.project_id,
            filename=asset_data.filename,
            mime_type=asset_data.mime_type,
            source=asset_data.source,
            processing_status="uploaded",
            processing_progress=0
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset
    
    async def get_asset(self, asset_id: str) -> Optional[Asset]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_asset_sync,
            asset_id
        )
    
    def _get_asset_sync(self, asset_id: str) -> Optional[Asset]:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()
    
    async def update_asset_status(self, asset_id: str, status: str, progress: int = None):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._update_asset_status_sync,
            asset_id,
            status,
            progress
        )
    
    def _update_asset_status_sync(self, asset_id: str, status: str, progress: int = None):
        asset = self._get_asset_sync(asset_id)
        if asset:
            asset.processing_status = status
            if progress is not None:
                asset.processing_progress = progress
            self.db.commit()
    
    async def update_asset_paths(self, asset_id: str, file_path: str = None, 
                          proxy_path: str = None, thumbnail_path: str = None):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._update_asset_paths_sync,
            asset_id,
            file_path,
            proxy_path,
            thumbnail_path
        )
    
    def _update_asset_paths_sync(self, asset_id: str, file_path: str = None, 
                          proxy_path: str = None, thumbnail_path: str = None):
        asset = self._get_asset_sync(asset_id)
        if asset:
            if file_path:
                asset.file_path = file_path
            if proxy_path:
                asset.proxy_path = proxy_path
            if thumbnail_path:
                asset.thumbnail_path = thumbnail_path
            self.db.commit()
    
    # AssetSegment 操作
    async def create_asset_segment(self, asset_id: str, start_time: float, end_time: float,
                           description: str, tags: dict) -> AssetSegment:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_asset_segment_sync,
            asset_id,
            start_time,
            end_time,
            description,
            tags
        )
    
    def _create_asset_segment_sync(self, asset_id: str, start_time: float, end_time: float,
                           description: str, tags: dict) -> AssetSegment:
        segment = AssetSegment(
            id=f"seg_{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            start_time=start_time,
            end_time=end_time,
            description=description,
            emotion_tags=tags.get("emotions", []),
            scene_tags=tags.get("scenes", []),
            action_tags=tags.get("actions", []),
            cinematography_tags=tags.get("cinematography", [])
        )
        self.db.add(segment)
        self.db.commit()
        self.db.refresh(segment)
        return segment
    
    async def get_asset_segments(self, asset_id: str) -> List[AssetSegment]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._get_asset_segments_sync,
            asset_id
        )
    
    def _get_asset_segments_sync(self, asset_id: str) -> List[AssetSegment]:
        return self.db.query(AssetSegment).filter(
            AssetSegment.asset_id == asset_id
        ).all()
    
    # AssetVector 操作
    async def create_asset_vector(self, asset_id: str, vector_data: str, 
                          content_type: str, text_content: str,
                          segment_id: str = None) -> AssetVector:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_asset_vector_sync,
            asset_id,
            vector_data,
            content_type,
            text_content,
            segment_id
        )
    
    def _create_asset_vector_sync(self, asset_id: str, vector_data: str, 
                          content_type: str, text_content: str,
                          segment_id: str = None) -> AssetVector:
        vector = AssetVector(
            id=f"vec_{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            segment_id=segment_id,
            vector_data=vector_data,
            content_type=content_type,
            text_content=text_content
        )
        self.db.add(vector)
        self.db.commit()
        self.db.refresh(vector)
        return vector
    
    def update_asset_paths(self, asset_id: str, file_path: str = None, 
                          proxy_path: str = None, thumbnail_path: str = None):
        asset = self.get_asset(asset_id)
        if asset:
            if file_path:
                asset.file_path = file_path
            if proxy_path:
                asset.proxy_path = proxy_path
            if thumbnail_path:
                asset.thumbnail_path = thumbnail_path
            self.db.commit()
    
    # AssetSegment 操作
    def create_asset_segment(self, asset_id: str, start_time: float, end_time: float,
                           description: str, tags: dict) -> AssetSegment:
        segment = AssetSegment(
            id=f"seg_{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            start_time=start_time,
            end_time=end_time,
            description=description,
            emotion_tags=tags.get("emotions", []),
            scene_tags=tags.get("scenes", []),
            action_tags=tags.get("actions", []),
            cinematography_tags=tags.get("cinematography", [])
        )
        self.db.add(segment)
        self.db.commit()
        self.db.refresh(segment)
        return segment
    
    def get_asset_segments(self, asset_id: str) -> List[AssetSegment]:
        return self.db.query(AssetSegment).filter(
            AssetSegment.asset_id == asset_id
        ).all()
    
    # AssetVector 操作
    def create_asset_vector(self, asset_id: str, vector_data: str, 
                          content_type: str, text_content: str,
                          segment_id: str = None) -> AssetVector:
        vector = AssetVector(
            id=f"vec_{uuid.uuid4().hex[:8]}",
            asset_id=asset_id,
            segment_id=segment_id,
            vector_data=vector_data,
            content_type=content_type,
            text_content=text_content
        )
        self.db.add(vector)
        self.db.commit()
        self.db.refresh(vector)
        return vector
    
    def search_vectors_by_similarity(self, query_vector: str, limit: int = 10) -> List[AssetVector]:
        # Phase 2: 简单实现，返回所有向量
        # 后续Phase会实现真正的向量相似度搜索
        return self.db.query(AssetVector).limit(limit).all()
    
    # FeedbackLog 操作
    def create_feedback(self, beat_id: str, asset_id: str, segment_id: str,
                       action: str, context: str = None, query_context: str = None) -> FeedbackLog:
        feedback = FeedbackLog(
            id=f"fb_{uuid.uuid4().hex[:8]}",
            beat_id=beat_id,
            asset_id=asset_id,
            segment_id=segment_id,
            action=action,
            context=context,
            query_context=query_context
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    # 转录数据操作
    def store_transcription_data(self, asset_id: str, transcription_data: dict):
        """存储转录数据到资产的元数据中"""
        asset = self.get_asset(asset_id)
        if asset:
            # 将转录数据存储在metadata字段中
            if not asset.metadata:
                asset.metadata = {}
            
            asset.metadata["transcription"] = transcription_data
            self.db.commit()
    
    def get_transcription_data(self, asset_id: str) -> Optional[dict]:
        """获取资产的转录数据"""
        asset = self.get_asset(asset_id)
        if asset and asset.metadata:
            return asset.metadata.get("transcription")
        return None
    
    def search_transcription_text(self, query: str, limit: int = 10) -> List[dict]:
        """在转录文本中搜索关键词"""
        results = []
        
        # 查询所有有转录数据的资产
        assets = self.db.query(Asset).filter(
            Asset.metadata.isnot(None)
        ).all()
        
        for asset in assets:
            if asset.metadata and "transcription" in asset.metadata:
                transcription = asset.metadata["transcription"]
                full_text = transcription.get("full_text", "").lower()
                
                # 简单的关键词匹配
                if query.lower() in full_text:
                    # 查找匹配的片段
                    matching_segments = []
                    for segment in transcription.get("segments", []):
                        if query.lower() in segment.get("text", "").lower():
                            matching_segments.append({
                                "segment_id": segment["id"],
                                "start_time": segment["start_time"],
                                "end_time": segment["end_time"],
                                "text": segment["text"],
                                "confidence": segment["confidence"]
                            })
                    
                    if matching_segments:
                        results.append({
                            "asset_id": asset.id,
                            "filename": asset.filename,
                            "language": transcription.get("language", "unknown"),
                            "matching_segments": matching_segments
                        })
                
                if len(results) >= limit:
                    break
        
        return results
    
    # 视觉数据操作
    def store_visual_data(self, asset_id: str, visual_data: dict):
        """存储视觉分析数据到资产的元数据中"""
        asset = self.get_asset(asset_id)
        if asset:
            # 将视觉数据存储在metadata字段中
            if not asset.metadata:
                asset.metadata = {}
            
            asset.metadata["visual_analysis"] = visual_data
            self.db.commit()
    
    def get_visual_data(self, asset_id: str) -> Optional[dict]:
        """获取资产的视觉分析数据"""
        asset = self.get_asset(asset_id)
        if asset and asset.metadata:
            return asset.metadata.get("visual_analysis")
        return None
    
    def search_visual_features(self, query_tags: dict, limit: int = 10) -> List[dict]:
        """基于视觉特征搜索资产"""
        results = []
        
        # 查询所有有视觉数据的资产
        assets = self.db.query(Asset).filter(
            Asset.metadata.isnot(None)
        ).all()
        
        for asset in assets:
            if asset.metadata and "visual_analysis" in asset.metadata:
                visual_data = asset.metadata["visual_analysis"]
                
                # 检查视觉特征匹配
                if self._match_visual_features(visual_data, query_tags):
                    keyframes = visual_data.get("keyframes", [])
                    visual_summary = visual_data.get("visual_description", {}).get("visual_summary", {})
                    
                    results.append({
                        "asset_id": asset.id,
                        "filename": asset.filename,
                        "visual_summary": visual_summary,
                        "keyframes_count": len(keyframes),
                        "duration": visual_data.get("duration", 0)
                    })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _match_visual_features(self, visual_data: dict, query_tags: dict) -> bool:
        """检查视觉特征是否匹配查询标签"""
        
        visual_summary = visual_data.get("visual_description", {}).get("visual_summary", {})
        
        # 检查亮度匹配
        brightness_query = query_tags.get("brightness_level")
        if brightness_query:
            brightness_level = visual_summary.get("brightness_level", "normal")
            if brightness_query.lower() not in brightness_level.lower():
                return False
        
        # 检查色调匹配
        color_query = query_tags.get("color_tone")
        if color_query:
            color_tone = visual_summary.get("color_tone", "neutral")
            if color_query.lower() not in color_tone.lower():
                return False
        
        # 检查复杂度匹配
        complexity_query = query_tags.get("visual_complexity")
        if complexity_query:
            complexity = visual_summary.get("visual_complexity", "medium")
            if complexity_query.lower() not in complexity.lower():
                return False
        
        # 检查光线匹配
        lighting_query = query_tags.get("lighting_quality")
        if lighting_query:
            lighting = visual_summary.get("lighting_quality", "normal")
            if lighting_query.lower() not in lighting.lower():
                return False
        
        return True