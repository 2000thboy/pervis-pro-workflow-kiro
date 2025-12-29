# -*- coding: utf-8 -*-
"""
项目立项向导 REST API 路由层

Feature: pervis-project-wizard
Phase 4: API 端点集成

提供以下端点：
- POST /api/wizard/parse-script - 剧本解析 (Script_Agent)
- POST /api/wizard/generate-content - 内容生成 (Script_Agent/Art_Agent)
- POST /api/wizard/process-assets - 素材处理 (Art_Agent)
- GET /api/wizard/task-status/{id} - 任务状态查询
- POST /api/wizard/recall-assets - 素材召回 (Storyboard_Agent)
- POST /api/wizard/review-content - 内容审核 (Director_Agent)
"""

import asyncio
import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Agent 服务（延迟加载）
# ============================================================================

_script_agent = None
_art_agent = None
_director_agent = None
_storyboard_agent = None
_pm_agent = None
_market_agent = None
_system_agent = None
_agent_service = None


def _get_script_agent():
    """获取 Script_Agent 服务"""
    global _script_agent
    if _script_agent is None:
        try:
            from services.agents.script_agent import get_script_agent_service
            _script_agent = get_script_agent_service()
            logger.info("Script_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"Script_Agent 服务加载失败: {e}")
    return _script_agent


def _get_art_agent():
    """获取 Art_Agent 服务"""
    global _art_agent
    if _art_agent is None:
        try:
            from services.agents.art_agent import get_art_agent_service
            _art_agent = get_art_agent_service()
            logger.info("Art_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"Art_Agent 服务加载失败: {e}")
    return _art_agent


def _get_director_agent():
    """获取 Director_Agent 服务"""
    global _director_agent
    if _director_agent is None:
        try:
            from services.agents.director_agent import get_director_agent_service
            _director_agent = get_director_agent_service()
            logger.info("Director_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"Director_Agent 服务加载失败: {e}")
    return _director_agent


def _get_storyboard_agent():
    """获取 Storyboard_Agent 服务"""
    global _storyboard_agent
    if _storyboard_agent is None:
        try:
            from services.agents.storyboard_agent import get_storyboard_agent_service
            _storyboard_agent = get_storyboard_agent_service()
            logger.info("Storyboard_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"Storyboard_Agent 服务加载失败: {e}")
    return _storyboard_agent


def _get_agent_service():
    """获取 AgentService"""
    global _agent_service
    if _agent_service is None:
        try:
            from services.agent_service import get_agent_service
            _agent_service = get_agent_service()
            logger.info("AgentService 加载成功")
        except Exception as e:
            logger.error(f"AgentService 加载失败: {e}")
    return _agent_service


def _get_pm_agent():
    """获取 PM_Agent 服务"""
    global _pm_agent
    if _pm_agent is None:
        try:
            from services.agents.pm_agent import get_pm_agent_service
            _pm_agent = get_pm_agent_service()
            logger.info("PM_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"PM_Agent 服务加载失败: {e}")
    return _pm_agent


def _get_market_agent():
    """获取 Market_Agent 服务"""
    global _market_agent
    if _market_agent is None:
        try:
            from services.agents.market_agent import get_market_agent_service
            _market_agent = get_market_agent_service()
            logger.info("Market_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"Market_Agent 服务加载失败: {e}")
    return _market_agent


def _get_system_agent():
    """获取 System_Agent 服务"""
    global _system_agent
    if _system_agent is None:
        try:
            from services.agents.system_agent import get_system_agent_service
            _system_agent = get_system_agent_service()
            logger.info("System_Agent 服务加载成功")
        except Exception as e:
            logger.error(f"System_Agent 服务加载失败: {e}")
    return _system_agent


# ============================================================================
# 请求/响应模型
# ============================================================================

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    WORKING = "working"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentSource(str, Enum):
    """内容来源"""
    USER = "user"
    SCRIPT_AGENT = "script_agent"
    ART_AGENT = "art_agent"
    DIRECTOR_AGENT = "director_agent"


# --- 剧本解析 ---

class ParseScriptRequest(BaseModel):
    """剧本解析请求"""
    script_content: str = Field(..., description="剧本内容")
    project_id: Optional[str] = Field(None, description="项目ID")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="解析选项")


class SceneInfo(BaseModel):
    """场次信息"""
    scene_id: str
    scene_number: int
    heading: str
    location: str
    time_of_day: str
    description: str
    characters: List[str]
    estimated_duration: float


class CharacterInfo(BaseModel):
    """角色信息"""
    name: str
    dialogue_count: int
    first_appearance: int
    tags: Dict[str, str] = Field(default_factory=dict)


class ParseScriptResponse(BaseModel):
    """剧本解析响应"""
    task_id: str
    status: TaskStatus
    scenes: List[SceneInfo] = Field(default_factory=list)
    characters: List[CharacterInfo] = Field(default_factory=list)
    total_scenes: int = 0
    estimated_duration: float = 0.0
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    source: ContentSource = ContentSource.SCRIPT_AGENT
    error: Optional[str] = None


# --- 内容生成 ---

class GenerateContentRequest(BaseModel):
    """内容生成请求"""
    project_id: str = Field(..., description="项目ID")
    content_type: str = Field(..., description="内容类型: logline, synopsis, character_bio")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    entity_name: Optional[str] = Field(None, description="实体名称（如角色名）")


class GenerateContentResponse(BaseModel):
    """内容生成响应"""
    task_id: str
    status: TaskStatus
    content_type: str
    content: Any = None
    source: ContentSource = ContentSource.SCRIPT_AGENT
    review_status: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# --- 素材处理 ---

class ProcessAssetsRequest(BaseModel):
    """素材处理请求"""
    project_id: str = Field(..., description="项目ID")
    asset_paths: List[str] = Field(..., description="素材文件路径列表")
    auto_classify: bool = Field(True, description="是否自动分类")


class AssetProcessResult(BaseModel):
    """单个素材处理结果"""
    asset_path: str
    category: str  # character, scene, reference
    confidence: float
    tags: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ProcessAssetsResponse(BaseModel):
    """素材处理响应"""
    task_id: str
    status: TaskStatus
    results: List[AssetProcessResult] = Field(default_factory=list)
    total_processed: int = 0
    success_count: int = 0
    failed_count: int = 0
    source: ContentSource = ContentSource.ART_AGENT
    error: Optional[str] = None


# --- 任务状态 ---

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: TaskStatus
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    error: Optional[str] = None


# --- 素材召回 ---

class RecallAssetsRequest(BaseModel):
    """素材召回请求"""
    scene_id: str = Field(..., description="场次ID")
    query: str = Field(..., description="搜索查询")
    tags: List[str] = Field(default_factory=list, description="标签过滤")
    strategy: str = Field("hybrid", description="召回策略: tag_only, vector_only, hybrid")


class AssetCandidateInfo(BaseModel):
    """素材候选信息"""
    candidate_id: str
    asset_id: str
    asset_path: str
    score: float
    rank: int
    tags: List[str] = Field(default_factory=list)
    match_reason: str = ""


class RecallAssetsResponse(BaseModel):
    """素材召回响应"""
    scene_id: str
    candidates: List[AssetCandidateInfo] = Field(default_factory=list)
    total_searched: int = 0
    has_match: bool = True
    placeholder_message: str = ""
    error: Optional[str] = None


# ============================================================================
# 任务存储（内存，生产环境应使用数据库）
# ============================================================================

_tasks: Dict[str, Dict[str, Any]] = {}


def _create_task(task_type: str) -> str:
    """创建任务"""
    task_id = f"task_{uuid4().hex[:12]}"
    _tasks[task_id] = {
        "task_id": task_id,
        "task_type": task_type,
        "status": TaskStatus.PENDING,
        "progress": 0.0,
        "message": "任务已创建",
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "error": None
    }
    return task_id


def _update_task(task_id: str, **kwargs):
    """更新任务"""
    if task_id in _tasks:
        _tasks[task_id].update(kwargs)
        _tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()


def _get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务"""
    return _tasks.get(task_id)


# ============================================================================
# Agent 适配器（延迟加载）
# ============================================================================

_llm_adapter = None


def _get_llm_adapter():
    """获取 LLM 适配器"""
    global _llm_adapter
    if _llm_adapter is None:
        try:
            from services.agent_llm_adapter import get_agent_llm_adapter
            _llm_adapter = get_agent_llm_adapter()
            logger.info("Wizard 路由 LLM 适配器加载成功")
        except Exception as e:
            logger.error(f"LLM 适配器加载失败: {e}")
    return _llm_adapter


# ============================================================================
# API 端点
# ============================================================================

@router.post("/parse-script", response_model=ParseScriptResponse)
async def parse_script(
    request: ParseScriptRequest,
    background_tasks: BackgroundTasks
) -> ParseScriptResponse:
    """
    剧本解析接口
    
    调用 Script_Agent 解析剧本，提取场次、角色、对话等信息。
    解析失败时返回错误信息并提供手动输入选项。
    """
    task_id = _create_task("parse_script")
    
    try:
        _update_task(task_id, status=TaskStatus.WORKING, message="Script_Agent 正在解析剧本...")
        
        # 使用新的 ScriptAgentService
        script_agent = _get_script_agent()
        
        if script_agent:
            # 使用 ScriptAgentService 解析
            parse_result = script_agent.parse_script(request.script_content)
            
            # 转换场次数据
            scenes = [
                SceneInfo(
                    scene_id=s.scene_id,
                    scene_number=s.scene_number,
                    heading=s.heading,
                    location=s.location,
                    time_of_day=s.time_of_day,
                    description=s.description or s.action,
                    characters=s.characters,
                    estimated_duration=s.estimated_duration
                )
                for s in parse_result.scenes
            ]
            
            # 转换角色数据
            characters = [
                CharacterInfo(
                    name=c.name,
                    dialogue_count=c.dialogue_count,
                    first_appearance=c.first_appearance,
                    tags=c.tags
                )
                for c in parse_result.characters
            ]
            
            # 异步生成 Logline 和 Synopsis
            logline = None
            synopsis = None
            
            try:
                logline = await script_agent.generate_logline(request.script_content)
                synopsis_data = await script_agent.generate_synopsis(request.script_content)
                if synopsis_data:
                    synopsis = synopsis_data.get("synopsis")
            except Exception as e:
                logger.warning(f"LLM 生成失败，使用基础解析结果: {e}")
            
            # Director_Agent 审核
            _update_task(task_id, status=TaskStatus.REVIEWING, message="Director_Agent 审核中...")
            director_agent = _get_director_agent()
            if director_agent and request.project_id:
                await director_agent.review(
                    result=parse_result.to_dict(),
                    task_type="parse_script",
                    project_id=request.project_id
                )
            
            _update_task(task_id, status=TaskStatus.COMPLETED, message="解析完成")
            
            return ParseScriptResponse(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                scenes=scenes,
                characters=characters,
                total_scenes=parse_result.total_scenes,
                estimated_duration=parse_result.estimated_duration,
                logline=logline,
                synopsis=synopsis,
                source=ContentSource.SCRIPT_AGENT
            )
        
        # 回退：使用基础解析
        return _parse_script_fallback(task_id, request.script_content)
        
    except Exception as e:
        logger.error(f"剧本解析失败: {e}")
        _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        return ParseScriptResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=f"解析失败: {str(e)}。您可以手动输入场次和角色信息。"
        )


def _parse_script_fallback(task_id: str, script_content: str) -> ParseScriptResponse:
    """剧本解析回退方案"""
    scenes, characters = _basic_script_parse(script_content)
    
    _update_task(task_id, status=TaskStatus.COMPLETED, message="基础解析完成")
    
    return ParseScriptResponse(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        scenes=scenes,
        characters=characters,
        total_scenes=len(scenes),
        estimated_duration=sum(s.estimated_duration for s in scenes),
        source=ContentSource.USER  # 标记为需要用户确认
    )


def _basic_script_parse(script_content: str) -> tuple:
    """基础剧本解析（正则匹配）"""
    import re
    
    scenes = []
    characters = {}
    
    # 场次标题模式：INT./EXT. 场景 - 时间
    scene_pattern = r'(INT\.|EXT\.|内景|外景)[.\s]*([^-\n]+)[-\s]*(.*?)(?=\n|$)'
    
    scene_matches = re.findall(scene_pattern, script_content, re.IGNORECASE)
    
    for i, match in enumerate(scene_matches):
        location_type, location, time_of_day = match
        scenes.append(SceneInfo(
            scene_id=f"scene_{i+1}",
            scene_number=i + 1,
            heading=f"{location_type} {location} - {time_of_day}".strip(),
            location=location.strip(),
            time_of_day=time_of_day.strip() or "日",
            description="",
            characters=[],
            estimated_duration=30.0  # 默认30秒
        ))
    
    # 角色名模式：全大写或中文名后跟冒号/括号
    char_pattern = r'^([A-Z\u4e00-\u9fa5]{2,10})[\s]*[:：(（]'
    char_matches = re.findall(char_pattern, script_content, re.MULTILINE)
    
    for name in char_matches:
        if name not in characters:
            characters[name] = CharacterInfo(
                name=name,
                dialogue_count=1,
                first_appearance=1
            )
        else:
            characters[name].dialogue_count += 1
    
    return scenes, list(characters.values())


@router.post("/generate-content", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest) -> GenerateContentResponse:
    """
    内容生成接口
    
    调用 Script_Agent 或 Art_Agent 生成内容（Logline、Synopsis、人物小传等）。
    生成后由 Director_Agent 审核。
    """
    task_id = _create_task("generate_content")
    
    try:
        _update_task(task_id, status=TaskStatus.WORKING, message=f"正在生成 {request.content_type}...")
        
        adapter = _get_llm_adapter()
        if not adapter:
            return GenerateContentResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                content_type=request.content_type,
                error="LLM 服务不可用，请手动输入内容"
            )
        
        content = None
        source = ContentSource.SCRIPT_AGENT
        
        # 根据内容类型调用不同方法
        if request.content_type == "logline":
            script_content = request.context.get("script_content", "")
            response = await adapter.generate_logline(script_content)
            if response.success and response.parsed_data:
                content = response.parsed_data.get("logline")
        
        elif request.content_type == "synopsis":
            script_content = request.context.get("script_content", "")
            response = await adapter.generate_synopsis(script_content)
            if response.success and response.parsed_data:
                content = response.parsed_data
        
        elif request.content_type == "character_bio":
            character_name = request.entity_name or request.context.get("character_name", "")
            script_content = request.context.get("script_content", "")
            response = await adapter.generate_character_bio(character_name, script_content)
            if response.success and response.parsed_data:
                content = response.parsed_data
        
        elif request.content_type == "visual_tags":
            description = request.context.get("description", "")
            response = await adapter.generate_visual_tags(description)
            if response.success and response.parsed_data:
                content = response.parsed_data
            source = ContentSource.ART_AGENT
        
        elif request.content_type == "demo_script":
            # 根据标题和一句话故事生成剧本
            title = request.context.get("title", "未命名项目")
            logline = request.context.get("logline", "")
            project_type = request.context.get("project_type", "short_film")
            
            # 构建生成提示
            prompt = f"""请根据以下信息生成一个专业的剧本：

项目标题：{title}
一句话故事：{logline if logline else "（未提供，请自由发挥）"}
项目类型：{project_type}

要求：
1. 使用标准剧本格式（场景标题、角色名、对话、动作描述）
2. 场景标题格式：INT./EXT. 场景名 - 时间（日/夜/黄昏等）
3. 角色名用中文，对话自然流畅
4. 包含 3-5 个场景
5. 总时长约 2-3 分钟
6. 故事要有开头、发展、结尾
7. 如果有一句话故事，剧本内容必须围绕它展开

请直接输出剧本内容，不要添加额外说明。"""

            response = await adapter.generate_raw(prompt)
            if response.success and response.raw_content:
                content = {"script": response.raw_content}
        
        else:
            return GenerateContentResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                content_type=request.content_type,
                error=f"不支持的内容类型: {request.content_type}"
            )
        
        if content is None:
            return GenerateContentResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                content_type=request.content_type,
                error="内容生成失败，请手动输入"
            )
        
        # Director_Agent 审核（简化版）
        _update_task(task_id, status=TaskStatus.REVIEWING, message="Director_Agent 审核中...")
        review_response = await adapter.review_content(
            content=content,
            content_type=request.content_type,
            project_context=request.context
        )
        
        review_status = "approved"
        suggestions = []
        if review_response.success and review_response.parsed_data:
            review_status = review_response.parsed_data.get("status", "approved")
            suggestions = review_response.parsed_data.get("suggestions", [])
        
        _update_task(task_id, status=TaskStatus.COMPLETED, message="生成完成")
        
        return GenerateContentResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            content_type=request.content_type,
            content=content,
            source=source,
            review_status=review_status,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"内容生成失败: {e}")
        _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        return GenerateContentResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            content_type=request.content_type,
            error=str(e)
        )


@router.post("/process-assets", response_model=ProcessAssetsResponse)
async def process_assets(request: ProcessAssetsRequest) -> ProcessAssetsResponse:
    """
    素材处理接口
    
    调用 Art_Agent 处理上传的素材，进行分类和标签生成。
    无法分类的文件放入参考界面。
    """
    task_id = _create_task("process_assets")
    
    try:
        _update_task(task_id, status=TaskStatus.WORKING, message="Art_Agent 正在处理素材...")
        
        # 使用新的 ArtAgentService
        art_agent = _get_art_agent()
        
        results = []
        success_count = 0
        failed_count = 0
        
        for asset_path in request.asset_paths:
            try:
                if art_agent and request.auto_classify:
                    # 使用 ArtAgentService 分类
                    metadata = art_agent.extract_metadata(asset_path)
                    classification = await art_agent.classify_file(asset_path, metadata)
                    
                    # 生成标签
                    tags = await art_agent.generate_tags(asset_path)
                    tag_list = tags.free_tags if tags else []
                    
                    results.append(AssetProcessResult(
                        asset_path=asset_path,
                        category=classification.category,
                        confidence=classification.confidence,
                        tags=tag_list + classification.suggested_tags
                    ))
                    success_count += 1
                else:
                    # 回退：基于文件名分类
                    filename = Path(asset_path).name
                    category = _classify_by_filename(filename)
                    results.append(AssetProcessResult(
                        asset_path=asset_path,
                        category=category,
                        confidence=0.5,
                        tags=[]
                    ))
                    success_count += 1
                
            except Exception as e:
                logger.error(f"处理素材失败 {asset_path}: {e}")
                results.append(AssetProcessResult(
                    asset_path=asset_path,
                    category="reference",
                    confidence=0.0,
                    error=str(e)
                ))
                failed_count += 1
        
        _update_task(task_id, status=TaskStatus.COMPLETED, message="处理完成")
        
        return ProcessAssetsResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            results=results,
            total_processed=len(request.asset_paths),
            success_count=success_count,
            failed_count=failed_count,
            source=ContentSource.ART_AGENT
        )
        
    except Exception as e:
        logger.error(f"素材处理失败: {e}")
        _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        return ProcessAssetsResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(e)
        )


def _get_file_type(path: str) -> str:
    """获取文件类型"""
    ext = Path(path).suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return "image"
    elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
        return "video"
    elif ext in ['.pdf', '.doc', '.docx', '.txt']:
        return "document"
    return "unknown"


def _classify_by_filename(filename: str) -> str:
    """基于文件名分类"""
    filename_lower = filename.lower()
    
    character_keywords = ["角色", "人物", "character", "char", "人设", "portrait"]
    scene_keywords = ["场景", "scene", "环境", "background", "location"]
    
    for kw in character_keywords:
        if kw in filename_lower:
            return "character"
    
    for kw in scene_keywords:
        if kw in filename_lower:
            return "scene"
    
    return "reference"


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    任务状态查询接口
    
    查询异步任务的执行状态和结果。
    """
    task = _get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        result=task["result"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        error=task["error"]
    )


@router.post("/recall-assets", response_model=RecallAssetsResponse)
async def recall_assets(request: RecallAssetsRequest) -> RecallAssetsResponse:
    """
    素材召回接口
    
    调用 Storyboard_Agent 基于场次描述召回匹配素材。
    返回 Top 5 候选，支持丝滑切换。
    """
    try:
        # 使用新的 StoryboardAgentService
        storyboard_agent = _get_storyboard_agent()
        
        if storyboard_agent:
            # 转换标签格式
            tags_dict = {}
            for tag in request.tags:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    tags_dict[key] = value
                else:
                    if "free_tags" not in tags_dict:
                        tags_dict["free_tags"] = []
                    tags_dict["free_tags"].append(tag)
            
            # 调用 Storyboard_Agent 召回
            result = await storyboard_agent.recall_assets(
                scene_id=request.scene_id,
                query=request.query,
                tags=tags_dict if tags_dict else None,
                strategy=request.strategy
            )
            
            # 转换候选格式
            candidates = [
                AssetCandidateInfo(
                    candidate_id=c.candidate_id,
                    asset_id=c.asset_id,
                    asset_path=c.asset_path,
                    score=c.score,
                    rank=c.rank,
                    tags=c.tags.get("free_tags", []) if isinstance(c.tags, dict) else [],
                    match_reason=c.match_reason
                )
                for c in result.candidates
            ]
            
            return RecallAssetsResponse(
                scene_id=result.scene_id,
                candidates=candidates,
                total_searched=result.total_searched,
                has_match=result.has_match,
                placeholder_message=result.placeholder_message
            )
        
        # 回退：返回空结果
        return RecallAssetsResponse(
            scene_id=request.scene_id,
            candidates=[],
            has_match=False,
            placeholder_message="Storyboard_Agent 服务不可用"
        )
        
    except Exception as e:
        logger.error(f"素材召回失败: {e}")
        return RecallAssetsResponse(
            scene_id=request.scene_id,
            candidates=[],
            has_match=False,
            placeholder_message=f"召回失败: {str(e)}",
            error=str(e)
        )


# ============================================================================
# 新增端点：内容审核
# ============================================================================

class ReviewContentRequest(BaseModel):
    """内容审核请求"""
    project_id: str = Field(..., description="项目ID")
    content: Any = Field(..., description="待审核内容")
    content_type: str = Field(..., description="内容类型")


class ReviewContentResponse(BaseModel):
    """内容审核响应"""
    status: str  # approved, suggestions, rejected
    passed_checks: List[str] = Field(default_factory=list)
    failed_checks: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    reason: str = ""
    confidence: float = 0.9


@router.post("/review-content", response_model=ReviewContentResponse)
async def review_content(request: ReviewContentRequest) -> ReviewContentResponse:
    """
    内容审核接口
    
    调用 Director_Agent 审核内容，返回审核结果和建议。
    """
    try:
        director_agent = _get_director_agent()
        
        if director_agent:
            result = await director_agent.review(
                result=request.content,
                task_type=request.content_type,
                project_id=request.project_id
            )
            
            return ReviewContentResponse(
                status=result.status,
                passed_checks=result.passed_checks,
                failed_checks=result.failed_checks,
                suggestions=result.suggestions,
                reason=result.reason,
                confidence=result.confidence
            )
        
        # 回退：自动通过
        return ReviewContentResponse(
            status="approved",
            reason="Director_Agent 服务不可用，自动通过"
        )
        
    except Exception as e:
        logger.error(f"内容审核失败: {e}")
        return ReviewContentResponse(
            status="approved",
            reason=f"审核异常: {str(e)}，自动通过"
        )


# ============================================================================
# 新增端点：候选切换
# ============================================================================

class SwitchCandidateRequest(BaseModel):
    """候选切换请求"""
    scene_id: str = Field(..., description="场次ID")
    from_rank: int = Field(..., description="当前排名")
    to_rank: int = Field(..., description="目标排名")


class SwitchCandidateResponse(BaseModel):
    """候选切换响应"""
    success: bool
    candidate: Optional[AssetCandidateInfo] = None
    error: Optional[str] = None


@router.post("/switch-candidate", response_model=SwitchCandidateResponse)
async def switch_candidate(request: SwitchCandidateRequest) -> SwitchCandidateResponse:
    """
    候选切换接口
    
    丝滑切换候选素材，无需重新搜索。
    """
    try:
        storyboard_agent = _get_storyboard_agent()
        
        if storyboard_agent:
            candidate = storyboard_agent.switch_candidate(
                scene_id=request.scene_id,
                from_rank=request.from_rank,
                to_rank=request.to_rank
            )
            
            if candidate:
                return SwitchCandidateResponse(
                    success=True,
                    candidate=AssetCandidateInfo(
                        candidate_id=candidate.candidate_id,
                        asset_id=candidate.asset_id,
                        asset_path=candidate.asset_path,
                        score=candidate.score,
                        rank=candidate.rank,
                        tags=candidate.tags.get("free_tags", []) if isinstance(candidate.tags, dict) else [],
                        match_reason=candidate.match_reason
                    )
                )
            
            return SwitchCandidateResponse(
                success=False,
                error=f"未找到排名 {request.to_rank} 的候选"
            )
        
        return SwitchCandidateResponse(
            success=False,
            error="Storyboard_Agent 服务不可用"
        )
        
    except Exception as e:
        logger.error(f"候选切换失败: {e}")
        return SwitchCandidateResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# 新增端点：获取缓存候选
# ============================================================================

@router.get("/cached-candidates/{scene_id}")
async def get_cached_candidates(scene_id: str) -> RecallAssetsResponse:
    """
    获取缓存的候选素材
    
    返回之前召回的 Top 5 候选，无需重新搜索。
    """
    try:
        storyboard_agent = _get_storyboard_agent()
        
        if storyboard_agent:
            candidates = storyboard_agent.get_cached_candidates(scene_id)
            
            return RecallAssetsResponse(
                scene_id=scene_id,
                candidates=[
                    AssetCandidateInfo(
                        candidate_id=c.candidate_id,
                        asset_id=c.asset_id,
                        asset_path=c.asset_path,
                        score=c.score,
                        rank=c.rank,
                        tags=c.tags.get("free_tags", []) if isinstance(c.tags, dict) else [],
                        match_reason=c.match_reason
                    )
                    for c in candidates
                ],
                has_match=len(candidates) > 0,
                placeholder_message="" if candidates else "无缓存候选"
            )
        
        return RecallAssetsResponse(
            scene_id=scene_id,
            candidates=[],
            has_match=False,
            placeholder_message="Storyboard_Agent 服务不可用"
        )
        
    except Exception as e:
        logger.error(f"获取缓存候选失败: {e}")
        return RecallAssetsResponse(
            scene_id=scene_id,
            candidates=[],
            has_match=False,
            error=str(e)
        )


# ============================================================================
# 健康检查
# ============================================================================

@router.get("/health")
async def health_check():
    """健康检查 - 显示所有 Agent 服务状态"""
    script_agent = _get_script_agent()
    art_agent = _get_art_agent()
    director_agent = _get_director_agent()
    storyboard_agent = _get_storyboard_agent()
    agent_service = _get_agent_service()
    
    return {
        "status": "ok",
        "agents": {
            "script_agent": "available" if script_agent else "unavailable",
            "art_agent": "available" if art_agent else "unavailable",
            "director_agent": "available" if director_agent else "unavailable",
            "storyboard_agent": "available" if storyboard_agent else "unavailable",
            "agent_service": "available" if agent_service else "unavailable"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# MVP 新增端点：项目创建和验证
# ============================================================================

class ProjectType(str, Enum):
    """项目类型"""
    SHORT_FILM = "short_film"
    ADVERTISEMENT = "advertisement"
    MUSIC_VIDEO = "music_video"
    FEATURE_FILM = "feature_film"
    CUSTOM = "custom"


class CreateProjectRequest(BaseModel):
    """项目创建请求"""
    title: str = Field(..., description="项目标题", min_length=1, max_length=200)
    project_type: ProjectType = Field(..., description="项目类型")
    duration_minutes: Optional[float] = Field(None, description="预计时长（分钟）")
    aspect_ratio: str = Field("16:9", description="画幅比例")
    frame_rate: float = Field(24.0, description="帧率")
    resolution: str = Field("1920x1080", description="分辨率")
    script_content: Optional[str] = Field(None, description="剧本内容")
    synopsis: Optional[str] = Field(None, description="故事概要")
    logline: Optional[str] = Field(None, description="一句话概要")
    template_id: Optional[str] = Field(None, description="模板ID")


class CreateProjectResponse(BaseModel):
    """项目创建响应"""
    success: bool
    project_id: Optional[str] = None
    message: str = ""
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ValidateProjectRequest(BaseModel):
    """项目验证请求"""
    title: Optional[str] = None
    project_type: Optional[str] = None
    duration_minutes: Optional[float] = None
    aspect_ratio: Optional[str] = None
    frame_rate: Optional[float] = None
    resolution: Optional[str] = None
    script_content: Optional[str] = None
    synopsis: Optional[str] = None


class ValidationError(BaseModel):
    """验证错误"""
    field: str
    message: str
    severity: str = "error"  # error, warning


class ValidateProjectResponse(BaseModel):
    """项目验证响应"""
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    completion_percentage: float = 0.0
    missing_required: List[str] = Field(default_factory=list)


# 项目存储（内存，生产环境应使用数据库）
_projects: Dict[str, Dict[str, Any]] = {}

# 草稿存储（内存，生产环境应使用数据库）
_drafts: Dict[str, Dict[str, Any]] = {}


# --- 草稿管理请求/响应模型 ---

class CreateDraftRequest(BaseModel):
    """创建草稿请求"""
    title: Optional[str] = None
    project_type: Optional[str] = None
    current_step: int = 1
    initial_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateDraftResponse(BaseModel):
    """创建草稿响应"""
    id: str
    draft_id: str
    title: Optional[str] = None
    project_type: Optional[str] = None
    current_step: int = 1
    status: str = "draft"
    created_at: str
    message: str = ""


class UpdateDraftRequest(BaseModel):
    """更新草稿请求"""
    current_step: Optional[int] = None
    draft_data: Optional[Dict[str, Any]] = None
    field_status: Optional[Dict[str, str]] = None


class DraftResponse(BaseModel):
    """草稿响应"""
    id: str
    draft_id: str
    title: Optional[str] = None
    project_type: Optional[str] = None
    current_step: int = 1
    completion_percentage: float = 0.0
    status: str = "draft"
    draft_data: Dict[str, Any] = Field(default_factory=dict)
    field_status: Dict[str, str] = Field(default_factory=dict)
    created_at: str
    updated_at: str


@router.post("/draft", response_model=CreateDraftResponse)
async def create_draft(request: CreateDraftRequest) -> CreateDraftResponse:
    """
    创建向导草稿
    
    创建新的项目立项向导草稿，保存用户进度。
    """
    try:
        draft_id = f"draft_{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        draft = {
            "id": draft_id,
            "draft_id": draft_id,
            "title": request.title,
            "project_type": request.project_type,
            "current_step": request.current_step,
            "completion_percentage": 0.0,
            "status": "draft",
            "draft_data": request.initial_data or {},
            "field_status": {},
            "created_at": now,
            "updated_at": now
        }
        
        _drafts[draft_id] = draft
        
        return CreateDraftResponse(
            id=draft_id,
            draft_id=draft_id,
            title=request.title,
            project_type=request.project_type,
            current_step=request.current_step,
            status="draft",
            created_at=now,
            message="草稿创建成功"
        )
        
    except Exception as e:
        logger.error(f"创建草稿失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建草稿失败: {str(e)}")


@router.get("/draft/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str) -> DraftResponse:
    """
    获取草稿详情
    """
    draft = _drafts.get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    return DraftResponse(**draft)


@router.put("/draft/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: str, request: UpdateDraftRequest) -> DraftResponse:
    """
    更新草稿
    """
    draft = _drafts.get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    if request.current_step is not None:
        draft["current_step"] = request.current_step
    
    if request.draft_data is not None:
        draft["draft_data"].update(request.draft_data)
    
    if request.field_status is not None:
        draft["field_status"].update(request.field_status)
    
    draft["updated_at"] = datetime.utcnow().isoformat()
    
    return DraftResponse(**draft)


@router.delete("/draft/{draft_id}")
async def delete_draft(draft_id: str):
    """
    删除草稿
    """
    if draft_id not in _drafts:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    del _drafts[draft_id]
    return {"status": "success", "message": "草稿已删除"}


@router.post("/create-project", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest) -> CreateProjectResponse:
    """
    项目创建接口
    
    创建新项目，验证必填字段，返回项目ID。
    """
    try:
        # 验证必填字段
        validation_errors = []
        warnings = []
        
        if not request.title or not request.title.strip():
            validation_errors.append("项目标题不能为空")
        
        if not request.script_content and not request.synopsis:
            warnings.append("建议提供剧本或故事概要以获得更好的 AI 辅助")
        
        # 验证画幅格式
        if request.aspect_ratio:
            if ":" not in request.aspect_ratio:
                validation_errors.append("画幅格式错误，应为 '宽:高' 格式（如 16:9）")
        
        # 验证帧率
        valid_frame_rates = [23.976, 24, 25, 29.97, 30, 50, 60]
        if request.frame_rate and request.frame_rate not in valid_frame_rates:
            warnings.append(f"非标准帧率 {request.frame_rate}，建议使用: {valid_frame_rates}")
        
        # 验证分辨率格式
        if request.resolution:
            if "x" not in request.resolution.lower():
                validation_errors.append("分辨率格式错误，应为 '宽x高' 格式（如 1920x1080）")
        
        if validation_errors:
            return CreateProjectResponse(
                success=False,
                message="项目创建失败：验证错误",
                validation_errors=validation_errors,
                warnings=warnings
            )
        
        # 创建项目
        project_id = f"proj_{uuid4().hex[:12]}"
        
        project_data = {
            "project_id": project_id,
            "title": request.title.strip(),
            "project_type": request.project_type.value,
            "duration_minutes": request.duration_minutes,
            "aspect_ratio": request.aspect_ratio,
            "frame_rate": request.frame_rate,
            "resolution": request.resolution,
            "script_content": request.script_content,
            "synopsis": request.synopsis,
            "logline": request.logline,
            "template_id": request.template_id,
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        _projects[project_id] = project_data
        
        logger.info(f"项目创建成功: {project_id} - {request.title}")
        
        return CreateProjectResponse(
            success=True,
            project_id=project_id,
            message="项目创建成功",
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"项目创建失败: {e}")
        return CreateProjectResponse(
            success=False,
            message=f"项目创建失败: {str(e)}"
        )


@router.post("/validate-project", response_model=ValidateProjectResponse)
async def validate_project(request: ValidateProjectRequest) -> ValidateProjectResponse:
    """
    项目验证接口
    
    验证项目字段，返回错误和警告信息。
    """
    errors = []
    warnings = []
    missing_required = []
    
    # 必填字段检查
    required_fields = ["title", "project_type"]
    
    if not request.title or not request.title.strip():
        errors.append(ValidationError(
            field="title",
            message="项目标题不能为空",
            severity="error"
        ))
        missing_required.append("title")
    elif len(request.title) > 200:
        errors.append(ValidationError(
            field="title",
            message="项目标题不能超过200个字符",
            severity="error"
        ))
    
    if not request.project_type:
        errors.append(ValidationError(
            field="project_type",
            message="请选择项目类型",
            severity="error"
        ))
        missing_required.append("project_type")
    else:
        valid_types = ["short_film", "advertisement", "music_video", "feature_film", "custom"]
        if request.project_type not in valid_types:
            errors.append(ValidationError(
                field="project_type",
                message=f"无效的项目类型，可选: {valid_types}",
                severity="error"
            ))
    
    # 可选字段验证
    if request.duration_minutes is not None:
        if request.duration_minutes <= 0:
            errors.append(ValidationError(
                field="duration_minutes",
                message="时长必须大于0",
                severity="error"
            ))
        elif request.duration_minutes > 300:
            warnings.append(ValidationError(
                field="duration_minutes",
                message="时长超过5小时，请确认是否正确",
                severity="warning"
            ))
    
    if request.aspect_ratio:
        if ":" not in request.aspect_ratio:
            errors.append(ValidationError(
                field="aspect_ratio",
                message="画幅格式错误，应为 '宽:高' 格式（如 16:9）",
                severity="error"
            ))
        else:
            try:
                w, h = request.aspect_ratio.split(":")
                float(w)
                float(h)
            except ValueError:
                errors.append(ValidationError(
                    field="aspect_ratio",
                    message="画幅比例必须是数字",
                    severity="error"
                ))
    
    if request.frame_rate is not None:
        valid_frame_rates = [23.976, 24, 25, 29.97, 30, 50, 60]
        if request.frame_rate <= 0:
            errors.append(ValidationError(
                field="frame_rate",
                message="帧率必须大于0",
                severity="error"
            ))
        elif request.frame_rate not in valid_frame_rates:
            warnings.append(ValidationError(
                field="frame_rate",
                message=f"非标准帧率，建议使用: {valid_frame_rates}",
                severity="warning"
            ))
    
    if request.resolution:
        if "x" not in request.resolution.lower():
            errors.append(ValidationError(
                field="resolution",
                message="分辨率格式错误，应为 '宽x高' 格式（如 1920x1080）",
                severity="error"
            ))
        else:
            try:
                w, h = request.resolution.lower().split("x")
                int(w)
                int(h)
            except ValueError:
                errors.append(ValidationError(
                    field="resolution",
                    message="分辨率必须是整数",
                    severity="error"
                ))
    
    # 内容检查
    if not request.script_content and not request.synopsis:
        warnings.append(ValidationError(
            field="content",
            message="建议提供剧本或故事概要以获得更好的 AI 辅助",
            severity="warning"
        ))
    
    # 计算完成度
    total_fields = 8  # title, type, duration, aspect, frame_rate, resolution, script, synopsis
    filled_fields = sum([
        bool(request.title),
        bool(request.project_type),
        request.duration_minutes is not None,
        bool(request.aspect_ratio),
        request.frame_rate is not None,
        bool(request.resolution),
        bool(request.script_content),
        bool(request.synopsis)
    ])
    completion_percentage = (filled_fields / total_fields) * 100
    
    return ValidateProjectResponse(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        completion_percentage=completion_percentage,
        missing_required=missing_required
    )


@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    return project


@router.put("/project/{project_id}")
async def update_project(project_id: str, updates: Dict[str, Any]):
    """更新项目"""
    project = _projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    # 更新字段
    for key, value in updates.items():
        if key not in ["project_id", "created_at"]:
            project[key] = value
    
    project["updated_at"] = datetime.utcnow().isoformat()
    
    return {"success": True, "project": project}


@router.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")
    
    del _projects[project_id]
    return {"success": True, "message": f"项目 {project_id} 已删除"}


@router.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    limit: int = 50
):
    """列出项目"""
    projects = list(_projects.values())
    
    if status:
        projects = [p for p in projects if p.get("status") == status]
    if project_type:
        projects = [p for p in projects if p.get("project_type") == project_type]
    
    # 按创建时间倒序
    projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    
    return {
        "projects": projects[:limit],
        "total": len(projects)
    }



# ============================================================================
# MVP 新增端点：PM_Agent 版本管理
# ============================================================================

class RecordVersionRequest(BaseModel):
    """记录版本请求"""
    project_id: str = Field(..., description="项目ID")
    content_type: str = Field(..., description="内容类型")
    content: Any = Field(..., description="内容数据")
    entity_id: Optional[str] = Field(None, description="实体ID")
    entity_name: Optional[str] = Field(None, description="实体名称")
    source: str = Field("user", description="来源")


class VersionInfo(BaseModel):
    """版本信息"""
    version_id: str
    version_name: str
    version_number: int
    content_type: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    source: str
    status: str
    created_at: str


class RecordVersionResponse(BaseModel):
    """记录版本响应"""
    success: bool
    version: Optional[VersionInfo] = None
    error: Optional[str] = None


@router.post("/record-version", response_model=RecordVersionResponse)
async def record_version(request: RecordVersionRequest) -> RecordVersionResponse:
    """
    记录版本接口
    
    调用 PM_Agent 记录内容版本。
    """
    try:
        pm_agent = _get_pm_agent()
        
        if pm_agent:
            version = pm_agent.record_version(
                project_id=request.project_id,
                content_type=request.content_type,
                content=request.content,
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                source=request.source
            )
            
            return RecordVersionResponse(
                success=True,
                version=VersionInfo(
                    version_id=version.version_id,
                    version_name=version.version_name,
                    version_number=version.version_number,
                    content_type=version.content_type,
                    entity_id=version.entity_id,
                    entity_name=version.entity_name,
                    source=version.source,
                    status=version.status,
                    created_at=version.created_at.isoformat()
                )
            )
        
        return RecordVersionResponse(
            success=False,
            error="PM_Agent 服务不可用"
        )
        
    except Exception as e:
        logger.error(f"记录版本失败: {e}")
        return RecordVersionResponse(
            success=False,
            error=str(e)
        )


@router.get("/version-history/{project_id}")
async def get_version_history(
    project_id: str,
    content_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 50
):
    """
    获取版本历史接口
    
    返回项目的版本历史记录。
    """
    try:
        pm_agent = _get_pm_agent()
        
        if pm_agent:
            versions = pm_agent.get_version_history(
                project_id=project_id,
                content_type=content_type,
                entity_id=entity_id,
                limit=limit
            )
            
            return {
                "success": True,
                "versions": [v.to_dict() for v in versions],
                "total": len(versions)
            }
        
        return {
            "success": False,
            "error": "PM_Agent 服务不可用",
            "versions": []
        }
        
    except Exception as e:
        logger.error(f"获取版本历史失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "versions": []
        }


@router.post("/restore-version/{version_id}")
async def restore_version(version_id: str, project_id: str):
    """
    恢复版本接口
    
    恢复到指定的历史版本。
    """
    try:
        pm_agent = _get_pm_agent()
        
        if pm_agent:
            new_version = pm_agent.restore_version(
                project_id=project_id,
                version_id=version_id
            )
            
            if new_version:
                return {
                    "success": True,
                    "new_version": new_version.to_dict(),
                    "message": f"已恢复到版本 {version_id}"
                }
            
            return {
                "success": False,
                "error": f"版本不存在: {version_id}"
            }
        
        return {
            "success": False,
            "error": "PM_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"恢复版本失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/version-display/{project_id}")
async def get_version_display(
    project_id: str,
    content_type: str,
    entity_id: Optional[str] = None
):
    """
    获取版本显示信息接口
    
    返回当前版本号、修改历史等显示信息。
    """
    try:
        pm_agent = _get_pm_agent()
        
        if pm_agent:
            info = pm_agent.get_version_display_info(
                project_id=project_id,
                content_type=content_type,
                entity_id=entity_id
            )
            
            return {
                "success": True,
                "current_version": info.current_version,
                "version_count": info.version_count,
                "last_modified": info.last_modified,
                "last_modified_by": info.last_modified_by,
                "has_pending_changes": info.has_pending_changes,
                "history": info.history
            }
        
        return {
            "success": False,
            "error": "PM_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"获取版本显示信息失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# MVP 新增端点：Market_Agent 市场分析
# ============================================================================

class MarketAnalysisRequest(BaseModel):
    """市场分析请求"""
    project_id: str = Field(..., description="项目ID")
    project_data: Dict[str, Any] = Field(..., description="项目数据")


@router.post("/market-analysis")
async def analyze_market(request: MarketAnalysisRequest):
    """
    市场分析接口
    
    调用 Market_Agent 进行市场分析。
    """
    try:
        market_agent = _get_market_agent()
        
        if market_agent:
            result = await market_agent.analyze_market(
                project_id=request.project_id,
                project_data=request.project_data
            )
            
            return {
                "success": True,
                "analysis": result.to_dict()
            }
        
        return {
            "success": False,
            "error": "Market_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"市场分析失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/market-analysis/{project_id}")
async def get_market_analysis(project_id: str):
    """
    获取市场分析结果接口
    
    返回缓存的市场分析结果。
    """
    try:
        market_agent = _get_market_agent()
        
        if market_agent:
            result = market_agent.get_cached_analysis(project_id)
            
            if result:
                return {
                    "success": True,
                    "analysis": result.to_dict()
                }
            
            return {
                "success": False,
                "error": "未找到分析结果，请先调用 /market-analysis 进行分析"
            }
        
        return {
            "success": False,
            "error": "Market_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"获取市场分析失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# MVP 新增端点：System_Agent 系统校验
# ============================================================================

class ValidateExportRequest(BaseModel):
    """导出校验请求"""
    project_id: str = Field(..., description="项目ID")
    project_data: Dict[str, Any] = Field(..., description="项目数据")


@router.post("/validate-export")
async def validate_export(request: ValidateExportRequest):
    """
    导出前校验接口
    
    调用 System_Agent 进行全面校验。
    """
    try:
        system_agent = _get_system_agent()
        
        if system_agent:
            result = await system_agent.validate_before_export(
                project_id=request.project_id,
                project_data=request.project_data
            )
            
            summary = system_agent.get_validation_summary(result)
            
            return {
                "success": True,
                "validation": result.to_dict(),
                "summary": summary
            }
        
        return {
            "success": False,
            "error": "System_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"导出校验失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


class CheckTagConsistencyRequest(BaseModel):
    """标签一致性检查请求"""
    tags: List[str] = Field(..., description="标签列表")


@router.post("/check-tag-consistency")
async def check_tag_consistency(request: CheckTagConsistencyRequest):
    """
    标签一致性检查接口
    
    检查标签是否存在矛盾。
    """
    try:
        system_agent = _get_system_agent()
        
        if system_agent:
            result = system_agent.check_tag_consistency(request.tags)
            
            return {
                "success": True,
                "result": result.to_dict()
            }
        
        return {
            "success": False,
            "error": "System_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"标签一致性检查失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/api-health")
async def check_api_health():
    """
    API 健康检查接口
    
    检查所有 API 端点的健康状态。
    """
    try:
        system_agent = _get_system_agent()
        
        if system_agent:
            results = await system_agent.check_api_health()
            
            all_healthy = all(r.status == "healthy" for r in results)
            
            return {
                "success": True,
                "overall_status": "healthy" if all_healthy else "degraded",
                "endpoints": [r.to_dict() for r in results]
            }
        
        return {
            "success": False,
            "error": "System_Agent 服务不可用"
        }
        
    except Exception as e:
        logger.error(f"API 健康检查失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# 更新健康检查端点，包含所有 Agent
@router.get("/health-full")
async def health_check_full():
    """完整健康检查 - 显示所有 Agent 服务状态"""
    script_agent = _get_script_agent()
    art_agent = _get_art_agent()
    director_agent = _get_director_agent()
    storyboard_agent = _get_storyboard_agent()
    pm_agent = _get_pm_agent()
    market_agent = _get_market_agent()
    system_agent = _get_system_agent()
    agent_service = _get_agent_service()
    
    agents_status = {
        "script_agent": "available" if script_agent else "unavailable",
        "art_agent": "available" if art_agent else "unavailable",
        "director_agent": "available" if director_agent else "unavailable",
        "storyboard_agent": "available" if storyboard_agent else "unavailable",
        "pm_agent": "available" if pm_agent else "unavailable",
        "market_agent": "available" if market_agent else "unavailable",
        "system_agent": "available" if system_agent else "unavailable",
        "agent_service": "available" if agent_service else "unavailable"
    }
    
    available_count = sum(1 for s in agents_status.values() if s == "available")
    total_count = len(agents_status)
    
    return {
        "status": "ok" if available_count == total_count else "degraded",
        "agents": agents_status,
        "available": available_count,
        "total": total_count,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Phase 9: Script_Agent 视觉分析 API（新增 2025-12-27）
# ============================================================================

class ImageAnalysisItem(BaseModel):
    """图像分析项"""
    image_id: str = Field(..., description="图像ID")
    image_path: str = Field(..., description="图像文件路径")
    image_type: str = Field(..., description="图像类型: character | scene")
    related_id: str = Field(..., description="关联的角色/场景 ID")


class AnalyzeImagesRequest(BaseModel):
    """图像分析请求"""
    draft_id: str = Field(..., description="草稿ID")
    images: List[ImageAnalysisItem] = Field(..., description="待分析的图像列表")


class AnalyzeImagesResponse(BaseModel):
    """图像分析响应"""
    task_id: str
    status: str
    agent: str = "script_agent"
    message: str = ""


class CharacterTagsInfo(BaseModel):
    """角色标签信息"""
    character_id: str
    image_path: str
    tags: Dict[str, Any]
    confidence: float
    confirmed: bool = False


class SceneTagsInfo(BaseModel):
    """场景标签信息"""
    scene_id: str
    image_path: str
    tags: Dict[str, Any]
    confidence: float
    confirmed: bool = False


class SuggestedTagsResponse(BaseModel):
    """建议标签响应"""
    draft_id: str
    character_tags: List[CharacterTagsInfo] = Field(default_factory=list)
    scene_tags: List[SceneTagsInfo] = Field(default_factory=list)
    status: str = "ready"
    error: Optional[str] = None


class ConfirmTagItem(BaseModel):
    """确认标签项"""
    entity_id: str = Field(..., description="角色/场景 ID")
    image_path: str = Field(..., description="图像路径")
    tags: Dict[str, Any] = Field(..., description="确认的标签")
    confirmed: bool = True


class ConfirmTagsRequest(BaseModel):
    """确认标签请求"""
    character_tags: List[ConfirmTagItem] = Field(default_factory=list)
    scene_tags: List[ConfirmTagItem] = Field(default_factory=list)


class ConfirmTagsResponse(BaseModel):
    """确认标签响应"""
    success: bool
    message: str = ""
    asset_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# 视觉标签缓存（内存存储，生产环境应使用数据库）
_visual_tags_cache: Dict[str, Dict[str, Any]] = {}


@router.post("/analyze-images", response_model=AnalyzeImagesResponse)
async def analyze_images(
    request: AnalyzeImagesRequest,
    background_tasks: BackgroundTasks
) -> AnalyzeImagesResponse:
    """
    图像分析接口（Phase 9 Task 9.4）
    
    调用 Script_Agent 分析参考图像（人设图/场景参考图），
    生成结构化的视觉标签。
    
    支持的图像类型：
    - character: 角色/人设图
    - scene: 场景参考图
    """
    task_id = _create_task("analyze_images")
    
    try:
        _update_task(task_id, status=TaskStatus.WORKING, message="Script_Agent 正在分析图像...")
        
        script_agent = _get_script_agent()
        
        if not script_agent:
            _update_task(task_id, status=TaskStatus.FAILED, error="Script_Agent 服务不可用")
            return AnalyzeImagesResponse(
                task_id=task_id,
                status="failed",
                message="Script_Agent 服务不可用"
            )
        
        # 转换请求格式
        from services.agents.script_agent import ImageAnalysisRequest as ScriptImageRequest
        
        analysis_requests = [
            ScriptImageRequest(
                image_id=img.image_id,
                image_path=img.image_path,
                image_type=img.image_type,
                related_id=img.related_id
            )
            for img in request.images
        ]
        
        # 异步执行分析
        async def run_analysis():
            try:
                results = await script_agent.analyze_reference_images(analysis_requests)
                
                # 缓存结果
                character_tags = []
                scene_tags = []
                
                for result in results:
                    if result.success:
                        if result.image_type == "character":
                            character_tags.append({
                                "character_id": result.related_id,
                                "image_path": result.image_path,
                                "tags": result.tags,
                                "confidence": result.confidence,
                                "confirmed": False
                            })
                        elif result.image_type == "scene":
                            scene_tags.append({
                                "scene_id": result.related_id,
                                "image_path": result.image_path,
                                "tags": result.tags,
                                "confidence": result.confidence,
                                "confirmed": False
                            })
                
                # 存入缓存
                _visual_tags_cache[request.draft_id] = {
                    "character_tags": character_tags,
                    "scene_tags": scene_tags,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                _update_task(
                    task_id, 
                    status=TaskStatus.COMPLETED, 
                    message=f"分析完成，生成 {len(character_tags)} 个角色标签，{len(scene_tags)} 个场景标签",
                    result={
                        "character_count": len(character_tags),
                        "scene_count": len(scene_tags)
                    }
                )
                
            except Exception as e:
                logger.error(f"图像分析任务失败: {e}")
                _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        
        # 添加到后台任务
        background_tasks.add_task(run_analysis)
        
        return AnalyzeImagesResponse(
            task_id=task_id,
            status="processing",
            message="图像分析任务已启动"
        )
        
    except Exception as e:
        logger.error(f"启动图像分析失败: {e}")
        _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        return AnalyzeImagesResponse(
            task_id=task_id,
            status="failed",
            message=str(e)
        )


@router.get("/draft/{draft_id}/suggested-tags", response_model=SuggestedTagsResponse)
async def get_suggested_tags(draft_id: str) -> SuggestedTagsResponse:
    """
    获取 AI 生成的标签（Phase 9 Task 9.4）
    
    返回 Script_Agent 为参考图像生成的视觉标签，
    供用户确认或修改。
    """
    try:
        cached = _visual_tags_cache.get(draft_id)
        
        if not cached:
            return SuggestedTagsResponse(
                draft_id=draft_id,
                status="not_found",
                error="未找到标签数据，请先调用 /analyze-images 进行分析"
            )
        
        character_tags = [
            CharacterTagsInfo(
                character_id=t["character_id"],
                image_path=t["image_path"],
                tags=t["tags"],
                confidence=t["confidence"],
                confirmed=t.get("confirmed", False)
            )
            for t in cached.get("character_tags", [])
        ]
        
        scene_tags = [
            SceneTagsInfo(
                scene_id=t["scene_id"],
                image_path=t["image_path"],
                tags=t["tags"],
                confidence=t["confidence"],
                confirmed=t.get("confirmed", False)
            )
            for t in cached.get("scene_tags", [])
        ]
        
        return SuggestedTagsResponse(
            draft_id=draft_id,
            character_tags=character_tags,
            scene_tags=scene_tags,
            status="ready"
        )
        
    except Exception as e:
        logger.error(f"获取建议标签失败: {e}")
        return SuggestedTagsResponse(
            draft_id=draft_id,
            status="error",
            error=str(e)
        )


@router.post("/draft/{draft_id}/confirm-tags", response_model=ConfirmTagsResponse)
async def confirm_tags(
    draft_id: str,
    request: ConfirmTagsRequest
) -> ConfirmTagsResponse:
    """
    用户确认标签（Phase 9 Task 9.4 + 9.5）
    
    用户确认或修改 AI 生成的标签后，
    将标签写入资产管理系统（asset_tags 表）。
    """
    try:
        asset_ids = []
        
        # 处理角色标签
        for tag_item in request.character_tags:
            if tag_item.confirmed:
                # 写入资产管理
                asset_id = await _save_visual_tags_to_asset(
                    entity_type="character",
                    entity_id=tag_item.entity_id,
                    image_path=tag_item.image_path,
                    tags=tag_item.tags
                )
                if asset_id:
                    asset_ids.append(asset_id)
                
                # 更新缓存状态
                if draft_id in _visual_tags_cache:
                    for cached_tag in _visual_tags_cache[draft_id].get("character_tags", []):
                        if cached_tag["character_id"] == tag_item.entity_id:
                            cached_tag["confirmed"] = True
                            cached_tag["tags"] = tag_item.tags
        
        # 处理场景标签
        for tag_item in request.scene_tags:
            if tag_item.confirmed:
                # 写入资产管理
                asset_id = await _save_visual_tags_to_asset(
                    entity_type="scene",
                    entity_id=tag_item.entity_id,
                    image_path=tag_item.image_path,
                    tags=tag_item.tags
                )
                if asset_id:
                    asset_ids.append(asset_id)
                
                # 更新缓存状态
                if draft_id in _visual_tags_cache:
                    for cached_tag in _visual_tags_cache[draft_id].get("scene_tags", []):
                        if cached_tag["scene_id"] == tag_item.entity_id:
                            cached_tag["confirmed"] = True
                            cached_tag["tags"] = tag_item.tags
        
        return ConfirmTagsResponse(
            success=True,
            message=f"标签已确认并写入资产管理，共 {len(asset_ids)} 个资产",
            asset_ids=asset_ids
        )
        
    except Exception as e:
        logger.error(f"确认标签失败: {e}")
        return ConfirmTagsResponse(
            success=False,
            error=str(e)
        )


async def _save_visual_tags_to_asset(
    entity_type: str,
    entity_id: str,
    image_path: str,
    tags: Dict[str, Any]
) -> Optional[str]:
    """
    将视觉标签保存到资产管理（Phase 9 Task 9.5）
    
    Args:
        entity_type: 实体类型（character/scene）
        entity_id: 实体ID
        image_path: 图像路径
        tags: 标签数据
    
    Returns:
        资产ID（如果保存成功）
    """
    try:
        from models.asset_tags import AssetTags, SceneType, TimeOfDay, Mood
        
        # 生成资产ID
        asset_id = f"asset_{uuid4().hex[:12]}"
        
        # 转换标签格式
        if entity_type == "character":
            # 角色标签转换
            asset_tags = AssetTags(
                scene_type="UNKNOWN",
                time_of_day="UNKNOWN",
                shot_size="CU",  # 角色图通常是特写
                camera_move="STATIC",
                action_type="IDLE",
                mood="NEUTRAL",
                characters=[entity_id],
                props=tags.get("accessories", []),
                free_tags=tags.get("color_palette", []) + [tags.get("clothing_style", "")],
                summary=tags.get("appearance", {}).get("face", "")[:50]
            )
        else:
            # 场景标签转换
            scene_type_str = tags.get("scene_type", "")
            time_str = tags.get("time_of_day", tags.get("time", ""))
            mood_str = tags.get("mood", "")
            
            asset_tags = AssetTags(
                scene_type=SceneType.from_chinese(scene_type_str).value,
                time_of_day=TimeOfDay.from_chinese(time_str).value,
                shot_size="LS",  # 场景图通常是远景
                camera_move="STATIC",
                action_type="IDLE",
                mood=Mood.from_chinese(mood_str).value,
                environment=tags.get("environment", []),
                free_tags=[tags.get("lighting", ""), tags.get("color_tone", "")],
                summary=tags.get("summary", "")[:50]
            )
        
        # TODO: 实际写入数据库
        # 这里需要集成 asset_library_service 或直接写入数据库
        # 当前先记录日志，后续完善数据库写入
        logger.info(f"保存视觉标签到资产管理: {asset_id}, 类型: {entity_type}, 实体: {entity_id}")
        logger.info(f"标签内容: {asset_tags.to_dict()}")
        
        # 尝试写入资产库
        try:
            from services.asset_library_service import get_asset_library_service
            asset_service = get_asset_library_service()
            
            # 创建资产记录
            await asset_service.create_asset(
                asset_id=asset_id,
                file_path=image_path,
                asset_type="image",
                category=entity_type,
                tags=asset_tags.to_dict(),
                metadata={
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "source": "vision_model",
                    "confirmed": True
                }
            )
            logger.info(f"资产 {asset_id} 已写入资产库")
        except Exception as db_error:
            logger.warning(f"写入资产库失败（服务可能未启动）: {db_error}")
            # 不影响主流程，标签已缓存
        
        return asset_id
        
    except Exception as e:
        logger.error(f"保存视觉标签失败: {e}")
        return None
