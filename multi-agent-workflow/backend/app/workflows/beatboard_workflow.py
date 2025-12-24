# -*- coding: utf-8 -*-
"""
Beatboard Workflow - 故事板工作流

实现场次分析、素材装配和故事板生成
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowStatus,
    StepType,
)


class SceneType(Enum):
    """场景类型"""
    INTERIOR = "interior"  # 内景
    EXTERIOR = "exterior"  # 外景
    MIXED = "mixed"        # 混合


class ShotType(Enum):
    """镜头类型"""
    WIDE = "wide"           # 全景
    MEDIUM = "medium"       # 中景
    CLOSE_UP = "close_up"   # 特写
    EXTREME_CLOSE_UP = "extreme_close_up"  # 大特写
    OVER_SHOULDER = "over_shoulder"  # 过肩
    POV = "pov"             # 主观镜头


@dataclass
class SceneAnalysis:
    """场次分析结果"""
    scene_id: str
    scene_number: int
    scene_type: SceneType
    location: str
    time_of_day: str
    characters: List[str]
    description: str
    estimated_duration: float  # 秒
    mood: str
    key_actions: List[str]
    dialogue_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "scene_type": self.scene_type.value,
            "location": self.location,
            "time_of_day": self.time_of_day,
            "characters": self.characters,
            "description": self.description,
            "estimated_duration": self.estimated_duration,
            "mood": self.mood,
            "key_actions": self.key_actions,
            "dialogue_count": self.dialogue_count,
            "metadata": self.metadata,
        }


@dataclass
class BeatboardItem:
    """故事板项目"""
    id: str
    scene_id: str
    shot_number: int
    shot_type: ShotType
    description: str
    duration: float  # 秒
    camera_movement: str
    audio_notes: str
    visual_notes: str
    asset_ids: List[str] = field(default_factory=list)
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scene_id": self.scene_id,
            "shot_number": self.shot_number,
            "shot_type": self.shot_type.value,
            "description": self.description,
            "duration": self.duration,
            "camera_movement": self.camera_movement,
            "audio_notes": self.audio_notes,
            "visual_notes": self.visual_notes,
            "asset_ids": self.asset_ids,
            "thumbnail_url": self.thumbnail_url,
            "metadata": self.metadata,
        }


@dataclass
class AssetMatch:
    """素材匹配结果"""
    asset_id: str
    asset_name: str
    asset_type: str
    match_score: float
    tags: List[str]
    preview_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "match_score": self.match_score,
            "tags": self.tags,
            "preview_url": self.preview_url,
        }


@dataclass
class Beatboard:
    """完整故事板"""
    id: str
    project_id: str
    name: str
    scenes: List[SceneAnalysis] = field(default_factory=list)
    items: List[BeatboardItem] = field(default_factory=list)
    total_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "scenes": [s.to_dict() for s in self.scenes],
            "items": [i.to_dict() for i in self.items],
            "total_duration": self.total_duration,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class BeatboardWorkflow:
    """故事板工作流"""
    
    WORKFLOW_ID = "beatboard"
    WORKFLOW_NAME = "故事板工作流"
    
    def __init__(
        self,
        engine: WorkflowEngine,
        scene_analyzer: Optional[Callable] = None,
        asset_matcher: Optional[Callable] = None
    ):
        self.engine = engine
        self.scene_analyzer = scene_analyzer or self._default_scene_analyzer
        self.asset_matcher = asset_matcher or self._default_asset_matcher
        self._beatboards: Dict[str, Beatboard] = {}
        self._scenes: Dict[str, SceneAnalysis] = {}
        
        # 注册工作流
        self._register_workflow()
    
    def _register_workflow(self) -> None:
        """注册故事板工作流"""
        workflow = WorkflowDefinition(
            id=self.WORKFLOW_ID,
            name=self.WORKFLOW_NAME,
            description="故事板生成流程，包括场次分析、素材匹配、故事板装配"
        )
        
        # Step 1: 解析剧本场次
        step1 = WorkflowStep(
            id="parse_scenes",
            name="解析剧本场次",
            step_type=StepType.TASK,
            handler=self._parse_scenes_handler,
            next_steps=["analyze_scenes"]
        )
        
        # Step 2: 分析场次
        step2 = WorkflowStep(
            id="analyze_scenes",
            name="分析场次",
            step_type=StepType.TASK,
            handler=self._analyze_scenes_handler,
            next_steps=["match_assets"]
        )
        
        # Step 3: 匹配素材
        step3 = WorkflowStep(
            id="match_assets",
            name="匹配素材",
            step_type=StepType.TASK,
            handler=self._match_assets_handler,
            next_steps=["user_review"]
        )
        
        # Step 4: 用户审核
        step4 = WorkflowStep(
            id="user_review",
            name="用户审核",
            step_type=StepType.WAIT,
            next_steps=["assemble_beatboard"]
        )
        
        # Step 5: 装配故事板
        step5 = WorkflowStep(
            id="assemble_beatboard",
            name="装配故事板",
            step_type=StepType.TASK,
            handler=self._assemble_beatboard_handler
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        workflow.add_step(step5)
        
        self.engine.register_workflow(workflow)
    
    # 步骤处理器
    async def _parse_scenes_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """解析剧本场次"""
        script_content = context.get("script_content", "")
        project_id = context.get("project_id", str(uuid.uuid4()))
        
        # 简单的场次解析（实际应该更复杂）
        scenes_data = []
        lines = script_content.strip().split("\n") if script_content else []
        
        current_scene = None
        scene_number = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测场景标题（简化版）
            if line.startswith("场景") or line.startswith("SCENE") or line.startswith("INT.") or line.startswith("EXT."):
                if current_scene:
                    scenes_data.append(current_scene)
                
                scene_number += 1
                scene_type = SceneType.INTERIOR if "INT" in line.upper() or "内" in line else SceneType.EXTERIOR
                
                current_scene = {
                    "scene_number": scene_number,
                    "scene_type": scene_type.value,
                    "location": line,
                    "content": [],
                }
            elif current_scene:
                current_scene["content"].append(line)
        
        if current_scene:
            scenes_data.append(current_scene)
        
        # 如果没有解析到场景，创建一个默认场景
        if not scenes_data:
            scenes_data.append({
                "scene_number": 1,
                "scene_type": SceneType.INTERIOR.value,
                "location": "默认场景",
                "content": lines,
            })
        
        return {
            "project_id": project_id,
            "parsed_scenes": scenes_data,
            "total_scenes": len(scenes_data),
            "parse_status": "completed"
        }

    
    async def _analyze_scenes_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """分析场次"""
        parsed_scenes = context.get("parsed_scenes", [])
        
        analyzed_scenes = []
        for scene_data in parsed_scenes:
            analysis = await self.scene_analyzer(scene_data)
            analyzed_scenes.append(analysis)
            self._scenes[analysis["scene_id"]] = SceneAnalysis(
                scene_id=analysis["scene_id"],
                scene_number=analysis["scene_number"],
                scene_type=SceneType(analysis["scene_type"]),
                location=analysis["location"],
                time_of_day=analysis.get("time_of_day", "day"),
                characters=analysis.get("characters", []),
                description=analysis.get("description", ""),
                estimated_duration=analysis.get("estimated_duration", 30.0),
                mood=analysis.get("mood", "neutral"),
                key_actions=analysis.get("key_actions", []),
                dialogue_count=analysis.get("dialogue_count", 0),
            )
        
        return {
            "analyzed_scenes": analyzed_scenes,
            "analysis_status": "completed"
        }
    
    async def _match_assets_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """匹配素材"""
        analyzed_scenes = context.get("analyzed_scenes", [])
        
        asset_matches = {}
        for scene in analyzed_scenes:
            scene_id = scene["scene_id"]
            matches = await self.asset_matcher(scene)
            asset_matches[scene_id] = matches
        
        return {
            "asset_matches": asset_matches,
            "match_status": "completed"
        }
    
    async def _assemble_beatboard_handler(self, context: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """装配故事板"""
        project_id = context.get("project_id")
        analyzed_scenes = context.get("analyzed_scenes", [])
        asset_matches = context.get("asset_matches", {})
        user_approved = context.get("user_approved", True)
        
        if not user_approved:
            return {"assemble_status": "rejected"}
        
        # 创建故事板
        beatboard_id = str(uuid.uuid4())
        beatboard = Beatboard(
            id=beatboard_id,
            project_id=project_id,
            name=f"故事板_{project_id[:8]}",
        )
        
        # 添加场景和故事板项目
        total_duration = 0.0
        for scene_data in analyzed_scenes:
            scene_id = scene_data["scene_id"]
            scene = self._scenes.get(scene_id)
            if scene:
                beatboard.scenes.append(scene)
                total_duration += scene.estimated_duration
                
                # 为每个场景创建故事板项目
                matches = asset_matches.get(scene_id, [])
                item = BeatboardItem(
                    id=str(uuid.uuid4()),
                    scene_id=scene_id,
                    shot_number=scene.scene_number,
                    shot_type=ShotType.WIDE,
                    description=scene.description,
                    duration=scene.estimated_duration,
                    camera_movement="static",
                    audio_notes="",
                    visual_notes=scene.mood,
                    asset_ids=[m.get("asset_id", "") for m in matches[:3]],
                )
                beatboard.items.append(item)
        
        beatboard.total_duration = total_duration
        self._beatboards[beatboard_id] = beatboard
        
        return {
            "beatboard_id": beatboard_id,
            "beatboard": beatboard.to_dict(),
            "assemble_status": "completed"
        }

    
    # 默认处理器
    async def _default_scene_analyzer(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认场次分析器"""
        content = scene_data.get("content", [])
        content_text = " ".join(content)
        
        # 简单分析
        characters = []
        dialogue_count = 0
        for line in content:
            # 检测角色名（简化：大写开头的词）
            if "：" in line or ":" in line:
                dialogue_count += 1
                parts = line.split("：") if "：" in line else line.split(":")
                if parts:
                    char_name = parts[0].strip()
                    if char_name and char_name not in characters:
                        characters.append(char_name)
        
        return {
            "scene_id": str(uuid.uuid4()),
            "scene_number": scene_data.get("scene_number", 1),
            "scene_type": scene_data.get("scene_type", "interior"),
            "location": scene_data.get("location", "未知地点"),
            "time_of_day": "day",
            "characters": characters,
            "description": content_text[:200] if content_text else "场景描述",
            "estimated_duration": max(30.0, len(content) * 5.0),
            "mood": "neutral",
            "key_actions": [],
            "dialogue_count": dialogue_count,
        }
    
    async def _default_asset_matcher(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """默认素材匹配器"""
        # 模拟素材匹配
        return [
            {
                "asset_id": str(uuid.uuid4()),
                "asset_name": f"素材_{scene.get('scene_number', 1)}_1",
                "asset_type": "image",
                "match_score": 0.85,
                "tags": ["场景", scene.get("location", "")],
            },
            {
                "asset_id": str(uuid.uuid4()),
                "asset_name": f"素材_{scene.get('scene_number', 1)}_2",
                "asset_type": "video",
                "match_score": 0.75,
                "tags": ["参考", scene.get("mood", "neutral")],
            },
        ]
    
    # 公共API
    async def start_beatboard_creation(
        self,
        project_id: str,
        script_content: str
    ) -> Optional[WorkflowInstance]:
        """启动故事板创建流程"""
        instance = await self.engine.create_instance(
            self.WORKFLOW_ID,
            context={
                "project_id": project_id,
                "script_content": script_content,
            }
        )
        
        if instance:
            await self.engine.start_instance(instance.id)
        
        return instance
    
    async def approve_beatboard(self, instance_id: str) -> bool:
        """审核通过故事板"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": True}
        )
    
    async def reject_beatboard(self, instance_id: str) -> bool:
        """拒绝故事板"""
        return await self.engine.resume_instance(
            instance_id,
            user_input={"user_approved": False}
        )
    
    def get_beatboard(self, beatboard_id: str) -> Optional[Beatboard]:
        """获取故事板"""
        return self._beatboards.get(beatboard_id)
    
    def get_scene(self, scene_id: str) -> Optional[SceneAnalysis]:
        """获取场次分析"""
        return self._scenes.get(scene_id)
    
    def list_beatboards(self, project_id: Optional[str] = None) -> List[Beatboard]:
        """列出故事板"""
        beatboards = list(self._beatboards.values())
        if project_id:
            beatboards = [b for b in beatboards if b.project_id == project_id]
        return beatboards
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_beatboards": len(self._beatboards),
            "total_scenes": len(self._scenes),
        }
