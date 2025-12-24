"""
剧本处理服务
Phase 2: 集成Gemini和数据库的完整剧本分析流程
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from services.database_service import DatabaseService
from models.base import ScriptAnalysisRequest, ScriptAnalysisResponse, Beat, Character
import time
import uuid

class ScriptProcessor:
    
    def __init__(self, db: Session):
        self.db = db
        self.db_service = DatabaseService(db)
        # Use Factory to get provider (Gemini or Local)
        from services.llm_provider import get_llm_provider
        self.ai_client = get_llm_provider()
    
    async def analyze_script(self, request: ScriptAnalysisRequest) -> ScriptAnalysisResponse:
        """
        完整的剧本分析流程
        """
        start_time = time.time()
        
        try:
            # 1. [New] 剧本结构预校验 (Pre-validation)
            # 在发送给AI之前，先进行本地规则检查
            validation_result = self._validate_script_structure(request.content)
            
            # 如果发现过长的场次，直接中断并返回警告
            if validation_result["status"] == "needs_split":
                return ScriptAnalysisResponse(
                    status="needs_split",
                    beats=[],
                    characters=[],
                    processing_time=time.time() - start_time,
                    meta={"logline": request.logline or "", "synopsis": ""},
                    error={
                        "error_code": "SCENE_TOO_LONG",
                        "message": "检测到超长场次，建议人工拆分",
                        "details": validation_result["long_scenes"],
                        "trace_id": str(uuid.uuid4()),
                        "retryable": False,
                        "retry": {"supported": False, "max_attempts": 0},
                    }
                )

            # 2. 调用AI分析剧本 (Provider Agnostic)
            ai_result = await self.ai_client.analyze_script(
                script_text=request.content,
                mode=request.mode
            )
            
            if ai_result["status"] != "success":
                # AI分析失败，返回错误
                return ScriptAnalysisResponse(
                    status="error",
                    beats=[],
                    characters=[],
                    processing_time=time.time() - start_time,
                    meta={"logline": request.logline or "", "synopsis": ""},
                    error=self._normalize_error(
                        ai_result,
                        default_error_code="AI_ANALYSIS_ERROR",
                        default_message="AI分析失败",
                        retryable_default=True,
                    ),
                )
            
            ai_data = ai_result["data"]
            
            # 2. 创建项目记录
            from models.base import ProjectCreate
            project_data = ProjectCreate(
                title=request.title,
                logline=ai_data.get("logline", request.logline),
                synopsis=ai_data.get("synopsis", ""),
                script_raw=request.content
            )
            
            project = await self.db_service.create_project(project_data)
            
            # 3. 处理角色数据
            characters = []
            for char_data in ai_data.get("characters", []):
                character = Character(
                    id=char_data.get("id", f"char_{uuid.uuid4().hex[:8]}"),
                    name=char_data.get("name", "未知角色"),
                    role=char_data.get("role", "Extra"),
                    description=char_data.get("description", "")
                )
                characters.append(character)
            
            # 4. 处理Beat数据并存储到数据库
            beats = []
            for i, beat_data in enumerate(ai_data.get("beats", [])):
                # 创建Beat数据库记录
                from models.base import BeatCreate
                beat_create = BeatCreate(
                    project_id=project.id,
                    content=beat_data.get("content", ""),
                    emotion_tags=beat_data.get("emotion_tags", []),
                    scene_tags=beat_data.get("scene_tags", []),
                    action_tags=beat_data.get("action_tags", []),
                    cinematography_tags=beat_data.get("cinematography_tags", []),
                    duration=beat_data.get("duration_estimate", 2.0)
                )
                
                db_beat = await self.db_service.create_beat(beat_create, order_index=i)
                
                # 转换为响应模型
                beat = Beat(
                    id=db_beat.id,
                    content=db_beat.content,
                    emotion_tags=db_beat.emotion_tags or [],
                    scene_tags=db_beat.scene_tags or [],
                    action_tags=db_beat.action_tags or [],
                    cinematography_tags=db_beat.cinematography_tags or [],
                    duration=db_beat.duration
                )
                beats.append(beat)
            
            processing_time = time.time() - start_time
            
            return ScriptAnalysisResponse(
                status="success",
                beats=beats,
                characters=characters,
                processing_time=processing_time,
                project_id=project.id,
                meta={
                    "logline": ai_data.get("logline", request.logline or ""),
                    "synopsis": ai_data.get("synopsis", ""),
                },
            )
            
        except Exception as e:
            return ScriptAnalysisResponse(
                status="error",
                beats=[],
                characters=[],
                processing_time=time.time() - start_time,
                meta={"logline": request.logline or "", "synopsis": ""},
                error=self._normalize_error(
                    {
                        "error_code": "SCRIPT_PROCESSING_ERROR",
                        "message": "剧本处理过程中发生错误",
                        "details": str(e),
                    },
                    default_error_code="SCRIPT_PROCESSING_ERROR",
                    default_message="剧本处理过程中发生错误",
                    retryable_default=True,
                ),
            )

    def _normalize_error(
        self,
        error: Any,
        default_error_code: str,
        default_message: str,
        retryable_default: bool,
    ) -> Dict[str, Any]:
        if isinstance(error, dict):
            normalized: Dict[str, Any] = dict(error)
        else:
            normalized = {"details": str(error)}

        normalized.setdefault("error_code", default_error_code)
        normalized.setdefault("message", default_message)
        normalized.setdefault("trace_id", str(uuid.uuid4()))
        normalized.setdefault("retryable", retryable_default)

        if "retry" not in normalized:
            if normalized.get("retryable"):
                normalized["retry"] = {
                    "supported": True,
                    "suggested_after_seconds": 1,
                    "max_attempts": 3,
                }
            else:
                normalized["retry"] = {"supported": False, "max_attempts": 0}

        return normalized

    def _validate_script_structure(self, script_text: str) -> Dict[str, Any]:
        """
        本地剧本结构校验器
        规则：检测是否有单场戏超过预估2分钟 (约2400字或特定行数)
        """
        lines = script_text.split('\n')
        scenes = []
        current_scene = None
        current_content = []
        
        # 简单解析场景
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 识别场景标题 (EXT./INT. 或 中文场景词)
            is_scene_header = (
                line.startswith('EXT.') or line.startswith('INT.') or
                line.startswith('内景') or line.startswith('外景') or
                ('场' in line and (line.startswith('第') or line[0].isdigit()))
            )
            
            if is_scene_header:
                # 保存上一个场景
                if current_scene:
                    duration = self._estimate_duration_rough(current_content)
                    scenes.append({
                        "header": current_scene,
                        "duration": duration,
                        "line_count": len(current_content)
                    })
                
                # 开始新场景
                current_scene = line
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一个场景
        if current_scene:
            duration = self._estimate_duration_rough(current_content)
            scenes.append({
                "header": current_scene,
                "duration": duration,
                "line_count": len(current_content)
            })
            
        # 检查是否有超长场景 (> 120秒)
        long_scenes = []
        for scene in scenes:
            if scene["duration"] > 120.0:
                long_scenes.append({
                    "scene_header": scene["header"],
                    "estimated_duration": scene["duration"],
                    "suggestion": "建议拆分为多个分场 (如 A/B 场)"
                })
                
        if long_scenes:
            return {
                "status": "needs_split",
                "long_scenes": long_scenes
            }
            
        return {"status": "ok"}
    
    def _estimate_duration_rough(self, content_lines: List[str]) -> float:
        """
        粗略估算时长 (不依赖AI)
        规则：
        1. 对话行: 1行 ≈ 4秒
        2. 动作行: 1行 ≈ 3秒
        3. 简单字数统估: 15字 ≈ 1秒
        """
        total_seconds = 0.0
        for line in content_lines:
            # 简单启发式
            length = len(line)
            if length == 0: continue
            
            # 粗算
            total_seconds += max(2.0, length / 5.0) # 中文阅读速度
            
        return total_seconds
