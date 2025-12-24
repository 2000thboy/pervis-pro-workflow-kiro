"""
基础数据模型
Phase 2: 完整的 Pydantic 模型，对应数据库结构
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class Beat(BaseModel):
    id: str
    content: str
    emotion_tags: List[str] = []
    scene_tags: List[str] = []
    action_tags: List[str] = []
    cinematography_tags: List[str] = []
    duration: Optional[float] = None

class Character(BaseModel):
    id: str
    name: str
    role: str
    description: str

class ScriptAnalysisRequest(BaseModel):
    content: str = Field(..., alias="script_text")
    mode: str = "parse"  # parse, smart_build, ai_build
    project_id: Optional[str] = None
    title: Optional[str] = "Untitled"
    logline: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

class ScriptAnalysisResponse(BaseModel):
    status: str
    beats: List[Beat]
    characters: List[Character]
    processing_time: float
    project_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class AssetUploadResponse(BaseModel):
    asset_id: str
    status: ProcessingStatus
    estimated_processing_time: int

class AssetSegment(BaseModel):
    id: str
    start_time: float
    end_time: float
    description: str
    tags: Dict[str, List[str]]

class AssetStatusResponse(BaseModel):
    status: ProcessingStatus
    progress: int
    proxy_url: Optional[str] = None
    segments: List[AssetSegment] = []

class SearchQuery(BaseModel):
    beat_id: Optional[str] = None
    query_text: Optional[str] = None
    query_tags: Dict[str, List[str]] = {}
    fuzziness: float = 0.7
    limit: int = 5

class SearchResult(BaseModel):
    asset_id: str
    segment_id: str
    match_score: float
    match_reason: str
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags_matched: List[str] = []

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_matches: int
    search_time: float
    query_info: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    beat_id: str
    asset_id: str
    segment_id: str
    action: str  # accept, reject
    context: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str

# 数据库模型对应的Pydantic模型
class ProjectCreate(BaseModel):
    title: str
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    script_raw: str

class ProjectResponse(BaseModel):
    id: str
    title: str
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    script_raw: str
    characters: List[Character] = []
    created_at: datetime
    current_stage: Optional[str] = None

class BeatCreate(BaseModel):
    project_id: str
    content: str
    emotion_tags: List[str] = []
    scene_tags: List[str] = []
    action_tags: List[str] = []
    cinematography_tags: List[str] = []
    duration: float = 2.0
    user_notes: Optional[str] = None

class BeatResponse(BaseModel):
    id: str
    project_id: str
    order_index: Optional[int] = None
    content: str
    emotion_tags: List[str] = []
    scene_tags: List[str] = []
    action_tags: List[str] = []
    cinematography_tags: List[str] = []
    duration: float
    user_notes: Optional[str] = None
    main_asset_id: Optional[str] = None

class AssetCreate(BaseModel):
    project_id: str
    filename: str
    mime_type: str
    source: str = "upload"

class AssetResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    mime_type: str
    source: str
    processing_status: ProcessingStatus
    processing_progress: int
    proxy_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime
