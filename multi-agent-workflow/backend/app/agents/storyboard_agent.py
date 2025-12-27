# -*- coding: utf-8 -*-
"""
故事板Agent (StoryboardAgent) - 素材召回和粗剪

Feature: pervis-project-wizard
验证需求: Requirements 13, 15 - 素材召回、候选切换、粗剪

主要功能（0-Fix.6）:
- recall_assets() - 素材召回（返回 Top 5 候选）
- _candidate_cache - 候选缓存
- switch_candidate() - 切换候选（丝滑切换）
- rough_cut() - 粗剪（FFmpeg 切割）
"""
import asyncio
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.core.agent_types import AgentType, AgentState
from app.core.message_bus import MessageBus, Message, Response

# 类型检查时导入，运行时延迟加载
if TYPE_CHECKING:
    from services.agent_llm_adapter import AgentLLMAdapter

logger = logging.getLogger(__name__)


class RecallStrategy(str, Enum):
    """召回策略"""
    TAG_ONLY = "tag_only"           # 仅标签匹配
    VECTOR_ONLY = "vector_only"     # 仅向量搜索
    HYBRID = "hybrid"               # 混合（标签+向量）


class CandidateStatus(str, Enum):
    """候选状态"""
    AVAILABLE = "available"         # 可用
    SELECTED = "selected"           # 已选中
    REJECTED = "rejected"           # 已拒绝
    USED = "used"                   # 已使用


@dataclass
class AssetCandidate:
    """素材候选"""
    candidate_id: str
    asset_id: str
    asset_path: str
    score: float                    # 匹配分数 0-1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: CandidateStatus = CandidateStatus.AVAILABLE
    rank: int = 0                   # 排名（1-5）
    match_reason: str = ""          # 匹配原因
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "asset_id": self.asset_id,
            "asset_path": self.asset_path,
            "score": self.score,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status.value,
            "rank": self.rank,
            "match_reason": self.match_reason,
        }


@dataclass
class RecallResult:
    """召回结果"""
    scene_id: str
    query: str
    candidates: List[AssetCandidate] = field(default_factory=list)
    total_searched: int = 0
    strategy: RecallStrategy = RecallStrategy.HYBRID
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    has_match: bool = True
    placeholder_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "query": self.query,
            "candidates": [c.to_dict() for c in self.candidates],
            "total_searched": self.total_searched,
            "strategy": self.strategy.value,
            "created_at": self.created_at,
            "has_match": self.has_match,
            "placeholder_message": self.placeholder_message,
        }


@dataclass
class RoughCutResult:
    """粗剪结果"""
    cut_id: str
    scene_id: str
    output_path: str
    duration_seconds: float
    source_assets: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cut_id": self.cut_id,
            "scene_id": self.scene_id,
            "output_path": self.output_path,
            "duration_seconds": self.duration_seconds,
            "source_assets": self.source_assets,
            "success": self.success,
            "error": self.error,
            "created_at": self.created_at,
        }


class StoryboardAgent(BaseAgent):
    """
    故事板Agent - 素材召回和粗剪
    
    主要功能:
    - 基于场次描述召回匹配素材（Top 5）
    - 缓存候选素材，支持丝滑切换
    - 使用 FFmpeg 进行粗剪
    
    需求: 13.1, 13.2, 13.4, 13.5, 15.1-15.7
    """
    
    def __init__(
        self,
        message_bus: MessageBus,
        agent_id: Optional[str] = None,
        output_dir: str = "./rough_cuts",
        max_candidates: int = 5,
    ):
        super().__init__(
            agent_id=agent_id or f"storyboard_agent_{uuid4().hex[:8]}",
            agent_type=AgentType.STORYBOARD,
            message_bus=message_bus,
            capabilities=[
                "asset_recall",
                "candidate_caching",
                "candidate_switching",
                "rough_cut",
            ]
        )
        
        self._output_dir = Path(output_dir)
        self._max_candidates = max_candidates
        
        # 候选缓存：scene_id -> List[AssetCandidate]
        self._candidate_cache: Dict[str, List[AssetCandidate]] = {}
        # 当前选中：scene_id -> candidate_id
        self._current_selection: Dict[str, str] = {}
        # 粗剪结果缓存
        self._rough_cuts: Dict[str, RoughCutResult] = {}
        
        # LLM 适配器（延迟加载）
        self._llm_adapter: Optional["AgentLLMAdapter"] = None
        # Milvus 客户端（延迟加载）
        self._milvus_client = None
        
        logger.info(f"StoryboardAgent 初始化: output_dir={output_dir}")
    
    async def _on_initialize(self) -> None:
        """初始化钩子"""
        # 确保输出目录存在
        self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("StoryboardAgent 初始化完成")
    
    async def _on_start(self) -> None:
        """启动钩子"""
        logger.info("StoryboardAgent 已启动")
    
    async def _on_stop(self) -> None:
        """停止钩子"""
        logger.info("StoryboardAgent 已停止")
    
    def _get_llm_adapter(self) -> Optional["AgentLLMAdapter"]:
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                pervis_backend = Path(__file__).parent.parent.parent.parent.parent / "Pervis PRO" / "backend"
                if str(pervis_backend) not in sys.path:
                    sys.path.insert(0, str(pervis_backend))
                
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
                logger.info("StoryboardAgent LLM 适配器加载成功")
            except ImportError as e:
                logger.warning(f"无法加载 LLM 适配器: {e}")
            except Exception as e:
                logger.error(f"LLM 适配器初始化失败: {e}")
        return self._llm_adapter

    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        content = message.content
        action = content.get("action", "")
        
        if action == "recall_assets":
            result = await self.recall_assets(
                scene_id=content.get("scene_id", ""),
                query=content.get("query", ""),
                tags=content.get("tags", []),
                strategy=RecallStrategy(content.get("strategy", "hybrid"))
            )
            return Response(
                success=True,
                message_id=message.id,
                data=result.to_dict()
            )
        
        elif action == "switch_candidate":
            result = self.switch_candidate(
                scene_id=content.get("scene_id", ""),
                candidate_id=content.get("candidate_id", "")
            )
            return Response(
                success=result is not None,
                message_id=message.id,
                data=result.to_dict() if result else None
            )
        
        elif action == "rough_cut":
            result = await self.rough_cut(
                scene_id=content.get("scene_id", ""),
                duration=content.get("duration", 5.0)
            )
            return Response(
                success=result.success,
                message_id=message.id,
                data=result.to_dict(),
                error=result.error
            )
        
        elif action == "get_candidates":
            candidates = self.get_cached_candidates(content.get("scene_id", ""))
            return Response(
                success=True,
                message_id=message.id,
                data={"candidates": [c.to_dict() for c in candidates]}
            )
        
        return None
    
    async def handle_protocol_message(self, message) -> Optional[Any]:
        """处理协议消息"""
        if hasattr(message, 'payload') and hasattr(message.payload, 'data'):
            data = message.payload.data
            return await self.handle_message(Message(
                id=message.header.message_id,
                source=message.header.source_agent,
                content=data
            ))
        return None
    
    # ========================================================================
    # 素材召回功能
    # ========================================================================
    
    async def recall_assets(
        self,
        scene_id: str,
        query: str,
        tags: Optional[List[str]] = None,
        strategy: RecallStrategy = RecallStrategy.HYBRID
    ) -> RecallResult:
        """
        素材召回（返回 Top 5 候选）
        
        需求: 13.1, 13.2, 15.1, 15.2
        
        Args:
            scene_id: 场次ID
            query: 搜索查询（场次描述）
            tags: 标签过滤
            strategy: 召回策略
        
        Returns:
            RecallResult 包含 Top 5 候选
        """
        await self.update_work_state(AgentState.WORKING, f"召回素材: {scene_id}")
        
        self._log_operation(
            "recall_started",
            details={
                "scene_id": scene_id,
                "query": query[:50],
                "strategy": strategy.value
            }
        )
        
        try:
            candidates = []
            total_searched = 0
            
            # 根据策略执行召回
            if strategy == RecallStrategy.TAG_ONLY:
                candidates, total_searched = await self._recall_by_tags(query, tags or [])
            elif strategy == RecallStrategy.VECTOR_ONLY:
                candidates, total_searched = await self._recall_by_vector(query)
            else:  # HYBRID
                candidates, total_searched = await self._recall_hybrid(query, tags or [])
            
            # 限制为 Top 5
            candidates = candidates[:self._max_candidates]
            
            # 设置排名
            for i, c in enumerate(candidates):
                c.rank = i + 1
            
            # 缓存候选
            self._candidate_cache[scene_id] = candidates
            
            # 自动选中第一个
            if candidates:
                self._current_selection[scene_id] = candidates[0].candidate_id
                candidates[0].status = CandidateStatus.SELECTED
            
            # 构建结果
            has_match = len(candidates) > 0
            result = RecallResult(
                scene_id=scene_id,
                query=query,
                candidates=candidates,
                total_searched=total_searched,
                strategy=strategy,
                has_match=has_match,
                placeholder_message="" if has_match else "未找到匹配素材，请手动上传或调整搜索条件"
            )
            
            self._log_operation(
                "recall_completed",
                details={
                    "scene_id": scene_id,
                    "candidates_count": len(candidates),
                    "total_searched": total_searched,
                    "has_match": has_match
                }
            )
            
            logger.info(f"素材召回完成: {scene_id}, 找到 {len(candidates)} 个候选")
            
            return result
            
        except Exception as e:
            logger.error(f"素材召回失败: {e}")
            return self._return_empty_with_placeholder(scene_id, query, str(e))
        
        finally:
            await self.update_work_state(AgentState.IDLE)
    
    async def _recall_by_tags(
        self,
        query: str,
        tags: List[str]
    ) -> Tuple[List[AssetCandidate], int]:
        """基于标签召回"""
        # TODO: 集成实际的标签搜索（Milvus 或数据库）
        # 当前返回模拟数据
        candidates = self._generate_mock_candidates(query, "tag")
        return candidates, 100
    
    async def _recall_by_vector(
        self,
        query: str
    ) -> Tuple[List[AssetCandidate], int]:
        """基于向量召回"""
        # TODO: 集成 Milvus 向量搜索
        # 当前返回模拟数据
        candidates = self._generate_mock_candidates(query, "vector")
        return candidates, 100
    
    async def _recall_hybrid(
        self,
        query: str,
        tags: List[str]
    ) -> Tuple[List[AssetCandidate], int]:
        """
        混合召回（标签+向量）
        
        需求: 15.5 - 合并排序结果
        """
        # 分别执行标签和向量召回
        tag_candidates, tag_total = await self._recall_by_tags(query, tags)
        vector_candidates, vector_total = await self._recall_by_vector(query)
        
        # 合并和排序
        merged = self._merge_and_rank(tag_candidates, vector_candidates)
        
        return merged, tag_total + vector_total
    
    def _merge_and_rank(
        self,
        tag_candidates: List[AssetCandidate],
        vector_candidates: List[AssetCandidate]
    ) -> List[AssetCandidate]:
        """
        合并排序结果
        
        需求: 15.5 - 标签+向量混合排序
        """
        # 使用字典去重（按 asset_id）
        merged_dict: Dict[str, AssetCandidate] = {}
        
        # 标签结果权重 0.4
        for c in tag_candidates:
            if c.asset_id not in merged_dict:
                c.score = c.score * 0.4
                merged_dict[c.asset_id] = c
            else:
                merged_dict[c.asset_id].score += c.score * 0.4
        
        # 向量结果权重 0.6
        for c in vector_candidates:
            if c.asset_id not in merged_dict:
                c.score = c.score * 0.6
                merged_dict[c.asset_id] = c
            else:
                merged_dict[c.asset_id].score += c.score * 0.6
        
        # 按分数排序
        merged = list(merged_dict.values())
        merged.sort(key=lambda x: x.score, reverse=True)
        
        return merged
    
    def _generate_mock_candidates(
        self,
        query: str,
        source: str
    ) -> List[AssetCandidate]:
        """生成模拟候选（开发测试用）"""
        candidates = []
        for i in range(5):
            candidates.append(AssetCandidate(
                candidate_id=f"cand_{uuid4().hex[:8]}",
                asset_id=f"asset_{uuid4().hex[:8]}",
                asset_path=f"/mock/assets/video_{i+1}.mp4",
                score=0.9 - i * 0.1,
                tags=["mock", source, f"tag_{i}"],
                metadata={"duration": 5.0 + i, "resolution": "1920x1080"},
                match_reason=f"基于{source}匹配: {query[:20]}..."
            ))
        return candidates
    
    def _return_empty_with_placeholder(
        self,
        scene_id: str,
        query: str,
        error: str = ""
    ) -> RecallResult:
        """
        无匹配时返回空列表和占位符
        
        需求: 15.7
        """
        return RecallResult(
            scene_id=scene_id,
            query=query,
            candidates=[],
            total_searched=0,
            has_match=False,
            placeholder_message=f"未找到匹配素材。{error}" if error else "未找到匹配素材，请手动上传或调整搜索条件"
        )
    
    # ========================================================================
    # 候选切换功能
    # ========================================================================
    
    def get_cached_candidates(self, scene_id: str) -> List[AssetCandidate]:
        """
        获取缓存的候选
        
        需求: 15.3
        """
        return self._candidate_cache.get(scene_id, [])
    
    def switch_candidate(
        self,
        scene_id: str,
        candidate_id: str
    ) -> Optional[AssetCandidate]:
        """
        切换候选（丝滑切换，无需重新搜索）
        
        需求: 15.3, 15.4
        
        Args:
            scene_id: 场次ID
            candidate_id: 要切换到的候选ID
        
        Returns:
            切换后的候选，如果失败返回 None
        """
        candidates = self._candidate_cache.get(scene_id, [])
        if not candidates:
            logger.warning(f"场次 {scene_id} 没有缓存的候选")
            return None
        
        # 查找目标候选
        target = None
        for c in candidates:
            if c.candidate_id == candidate_id:
                target = c
                break
        
        if not target:
            logger.warning(f"候选 {candidate_id} 不存在")
            return None
        
        # 更新状态
        old_selection = self._current_selection.get(scene_id)
        for c in candidates:
            if c.candidate_id == old_selection:
                c.status = CandidateStatus.AVAILABLE
            elif c.candidate_id == candidate_id:
                c.status = CandidateStatus.SELECTED
        
        self._current_selection[scene_id] = candidate_id
        
        self._log_operation(
            "candidate_switched",
            details={
                "scene_id": scene_id,
                "from": old_selection,
                "to": candidate_id
            }
        )
        
        logger.info(f"切换候选: {scene_id} -> {candidate_id}")
        
        return target
    
    def get_current_selection(self, scene_id: str) -> Optional[AssetCandidate]:
        """获取当前选中的候选"""
        candidate_id = self._current_selection.get(scene_id)
        if not candidate_id:
            return None
        
        candidates = self._candidate_cache.get(scene_id, [])
        for c in candidates:
            if c.candidate_id == candidate_id:
                return c
        return None
    
    # ========================================================================
    # 粗剪功能
    # ========================================================================
    
    async def rough_cut(
        self,
        scene_id: str,
        duration: float = 5.0,
        start_time: float = 0.0
    ) -> RoughCutResult:
        """
        粗剪（FFmpeg 切割）
        
        需求: 13.4, 13.5
        
        Args:
            scene_id: 场次ID
            duration: 切割时长（秒）
            start_time: 开始时间（秒）
        
        Returns:
            RoughCutResult 粗剪结果
        """
        await self.update_work_state(AgentState.WORKING, f"粗剪: {scene_id}")
        
        cut_id = f"cut_{uuid4().hex[:8]}"
        
        try:
            # 获取当前选中的素材
            selection = self.get_current_selection(scene_id)
            if not selection:
                return RoughCutResult(
                    cut_id=cut_id,
                    scene_id=scene_id,
                    output_path="",
                    duration_seconds=0,
                    success=False,
                    error="没有选中的素材"
                )
            
            # 构建输出路径
            output_filename = f"{scene_id}_{cut_id}.mp4"
            output_path = self._output_dir / output_filename
            
            # 执行 FFmpeg 切割
            success, error = await self._ffmpeg_cut(
                input_path=selection.asset_path,
                output_path=str(output_path),
                start_time=start_time,
                duration=duration
            )
            
            result = RoughCutResult(
                cut_id=cut_id,
                scene_id=scene_id,
                output_path=str(output_path) if success else "",
                duration_seconds=duration if success else 0,
                source_assets=[selection.asset_id],
                success=success,
                error=error
            )
            
            if success:
                self._rough_cuts[cut_id] = result
                selection.status = CandidateStatus.USED
            
            self._log_operation(
                "rough_cut_completed",
                success=success,
                error=error,
                details={
                    "cut_id": cut_id,
                    "scene_id": scene_id,
                    "duration": duration
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"粗剪失败: {e}")
            return RoughCutResult(
                cut_id=cut_id,
                scene_id=scene_id,
                output_path="",
                duration_seconds=0,
                success=False,
                error=str(e)
            )
        
        finally:
            await self.update_work_state(AgentState.IDLE)
    
    async def _ffmpeg_cut(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ) -> Tuple[bool, Optional[str]]:
        """
        执行 FFmpeg 切割
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            start_time: 开始时间
            duration: 时长
        
        Returns:
            (success, error_message)
        """
        # 检查输入文件是否存在
        if not Path(input_path).exists():
            # 开发模式：如果是模拟路径，创建空文件
            if input_path.startswith("/mock/"):
                logger.warning(f"模拟路径，跳过实际切割: {input_path}")
                # 创建空的输出文件作为占位
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).touch()
                return True, None
            return False, f"输入文件不存在: {input_path}"
        
        # 构建 FFmpeg 命令
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖输出文件
            "-ss", str(start_time),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",  # 直接复制，不重新编码
            output_path
        ]
        
        try:
            # 异步执行 FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"FFmpeg 切割成功: {output_path}")
                return True, None
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"FFmpeg 切割失败: {error_msg}")
                return False, error_msg
                
        except FileNotFoundError:
            return False, "FFmpeg 未安装或不在 PATH 中"
        except Exception as e:
            return False, str(e)
    
    def get_rough_cut(self, cut_id: str) -> Optional[RoughCutResult]:
        """获取粗剪结果"""
        return self._rough_cuts.get(cut_id)
    
    def list_rough_cuts(self, scene_id: Optional[str] = None) -> List[RoughCutResult]:
        """列出粗剪结果"""
        cuts = list(self._rough_cuts.values())
        if scene_id:
            cuts = [c for c in cuts if c.scene_id == scene_id]
        return cuts
    
    # ========================================================================
    # 状态查询
    # ========================================================================
    
    def get_storyboard_status(self) -> Dict[str, Any]:
        """获取故事板Agent状态"""
        return {
            **self.get_status(),
            "cached_scenes": len(self._candidate_cache),
            "total_candidates": sum(len(c) for c in self._candidate_cache.values()),
            "rough_cuts_count": len(self._rough_cuts),
            "current_selections": len(self._current_selection)
        }
