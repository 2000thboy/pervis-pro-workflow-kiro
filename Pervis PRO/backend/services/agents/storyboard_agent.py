# -*- coding: utf-8 -*-
"""
Storyboard_Agent 服务（故事板 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.6 实现 Storyboard_Agent

提供故事板相关的 AI 功能：
- 素材召回（返回 Top 5 候选）
- 候选缓存
- 丝滑切换候选
- 粗剪（FFmpeg）
- 合并排序结果（标签+向量混合）

Requirements: 13.1, 13.2, 13.4, 13.5, 15.1-15.7
"""

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class AssetCandidate:
    """素材候选"""
    candidate_id: str
    asset_id: str
    asset_path: str
    score: float
    rank: int
    tags: Dict[str, Any] = field(default_factory=dict)
    match_reason: str = ""
    thumbnail_path: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "asset_id": self.asset_id,
            "asset_path": self.asset_path,
            "score": self.score,
            "rank": self.rank,
            "tags": self.tags,
            "match_reason": self.match_reason,
            "thumbnail_path": self.thumbnail_path,
            "duration": self.duration
        }


@dataclass
class RecallResult:
    """召回结果"""
    scene_id: str
    candidates: List[AssetCandidate] = field(default_factory=list)
    total_searched: int = 0
    has_match: bool = True
    placeholder_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "candidates": [c.to_dict() for c in self.candidates],
            "total_searched": self.total_searched,
            "has_match": self.has_match,
            "placeholder_message": self.placeholder_message
        }


@dataclass
class RoughCutResult:
    """粗剪结果"""
    output_path: str
    duration: float
    segments: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


class StoryboardAgentService:
    """
    Storyboard_Agent 服务
    
    故事板 Agent，负责素材召回和粗剪
    """
    
    TOP_K = 5  # 返回 Top 5 候选
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "data/rough_cuts"
        self._llm_adapter = None
        self._video_store = None
        self._candidate_cache: Dict[str, List[AssetCandidate]] = {}
        self._embedding_model = None
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    def _get_video_store(self):
        """延迟加载视频存储"""
        if self._video_store is None:
            try:
                from services.milvus_store import get_video_store
                self._video_store = get_video_store()
                logger.info(f"视频存储已加载，当前素材数: {len(self._video_store._segments) if hasattr(self._video_store, '_segments') else 'N/A'}")
            except Exception as e:
                logger.error(f"视频存储加载失败: {e}")
        return self._video_store
    
    def _get_embedding_model(self):
        """延迟加载嵌入模型"""
        if self._embedding_model is None:
            try:
                # 尝试导入 sentence_transformers
                # 注意：可能因为 NumPy 版本不兼容而失败
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("嵌入模型加载成功")
            except ImportError as e:
                logger.warning(f"sentence_transformers 未安装: {e}")
                self._embedding_model = False  # 标记为不可用
            except Exception as e:
                # NumPy 版本冲突等问题
                logger.warning(f"嵌入模型加载失败（可能是 NumPy 版本问题）: {e}")
                logger.info("提示: 可以尝试运行 'pip install numpy<2' 来解决此问题")
                self._embedding_model = False  # 标记为不可用
        
        # 返回 None 如果模型不可用
        if self._embedding_model is False:
            return None
        return self._embedding_model
    
    async def recall_assets(
        self,
        scene_id: str,
        query: str,
        tags: Dict[str, Any] = None,
        strategy: str = "hybrid"
    ) -> RecallResult:
        """
        素材召回
        
        Args:
            scene_id: 场次ID
            query: 搜索查询（场次描述）
            tags: 标签过滤
            strategy: 召回策略 (tag_only, vector_only, hybrid)
        
        Returns:
            召回结果，包含 Top 5 候选
        """
        result = RecallResult(scene_id=scene_id)
        
        video_store = self._get_video_store()
        if not video_store:
            return self._return_empty_with_placeholder(
                scene_id, "视频存储服务不可用"
            )
        
        try:
            # 初始化存储
            await video_store.initialize()
            
            candidates = []
            
            # 标签搜索
            if strategy in ["tag_only", "hybrid"] and tags:
                tag_results = await video_store.search_by_tags(tags, top_k=self.TOP_K * 2)
                for r in tag_results:
                    candidates.append(AssetCandidate(
                        candidate_id=f"cand_{uuid4().hex[:8]}",
                        asset_id=r.segment.segment_id,
                        asset_path=r.segment.video_path,
                        score=r.score,
                        rank=0,
                        tags=r.segment.tags,
                        match_reason=r.match_reason,
                        thumbnail_path=r.segment.thumbnail_path,
                        duration=r.segment.duration
                    ))
            
            # 向量搜索
            if strategy in ["vector_only", "hybrid"]:
                embedding = self._generate_query_embedding(query)
                if embedding:
                    vector_results = await video_store.search(
                        embedding, top_k=self.TOP_K * 2
                    )
                    for r in vector_results:
                        candidates.append(AssetCandidate(
                            candidate_id=f"cand_{uuid4().hex[:8]}",
                            asset_id=r.segment.segment_id,
                            asset_path=r.segment.video_path,
                            score=r.score,
                            rank=0,
                            tags=r.segment.tags,
                            match_reason="向量相似度匹配",
                            thumbnail_path=r.segment.thumbnail_path,
                            duration=r.segment.duration
                        ))
            
            # 合并排序
            candidates = self._merge_and_rank(candidates)
            
            # 取 Top K
            candidates = candidates[:self.TOP_K]
            
            # 更新排名
            for i, c in enumerate(candidates):
                c.rank = i + 1
            
            # 缓存候选
            self._candidate_cache[scene_id] = candidates
            
            result.candidates = candidates
            result.total_searched = await video_store.count()
            result.has_match = len(candidates) > 0
            
            if not result.has_match:
                result.placeholder_message = "未找到匹配的素材，请上传更多素材或调整搜索条件"
            
        except Exception as e:
            logger.error(f"素材召回失败: {e}")
            return self._return_empty_with_placeholder(scene_id, str(e))
        
        return result
    
    def _generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """生成查询向量"""
        model = self._get_embedding_model()
        if model:
            try:
                return model.encode(query).tolist()
            except Exception as e:
                logger.error(f"生成查询向量失败: {e}")
        return None
    
    def _merge_and_rank(
        self,
        candidates: List[AssetCandidate]
    ) -> List[AssetCandidate]:
        """合并排序结果"""
        # 按 asset_id 去重，保留最高分
        unique_candidates: Dict[str, AssetCandidate] = {}
        for c in candidates:
            if c.asset_id not in unique_candidates:
                unique_candidates[c.asset_id] = c
            elif c.score > unique_candidates[c.asset_id].score:
                unique_candidates[c.asset_id] = c
        
        # 按分数排序
        sorted_candidates = sorted(
            unique_candidates.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_candidates
    
    def _return_empty_with_placeholder(
        self,
        scene_id: str,
        message: str
    ) -> RecallResult:
        """返回空结果和占位符"""
        return RecallResult(
            scene_id=scene_id,
            candidates=[],
            has_match=False,
            placeholder_message=message
        )
    
    def get_cached_candidates(self, scene_id: str) -> List[AssetCandidate]:
        """获取缓存的候选"""
        return self._candidate_cache.get(scene_id, [])
    
    def switch_candidate(
        self,
        scene_id: str,
        from_rank: int,
        to_rank: int
    ) -> Optional[AssetCandidate]:
        """
        切换候选（丝滑切换，无需重新搜索）
        
        Args:
            scene_id: 场次ID
            from_rank: 当前排名
            to_rank: 目标排名
        
        Returns:
            切换后的候选
        """
        candidates = self._candidate_cache.get(scene_id, [])
        
        if not candidates:
            return None
        
        # 查找目标候选
        for c in candidates:
            if c.rank == to_rank:
                return c
        
        return None
    
    async def rough_cut(
        self,
        segments: List[Dict[str, Any]],
        output_filename: str = None
    ) -> RoughCutResult:
        """
        粗剪（FFmpeg 切割和拼接）
        
        Args:
            segments: 片段列表 [{"path": "...", "start": 0, "end": 5}, ...]
            output_filename: 输出文件名
        
        Returns:
            粗剪结果
        """
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if output_filename is None:
            output_filename = f"rough_cut_{uuid4().hex[:8]}.mp4"
        
        output_path = str(output_dir / output_filename)
        
        try:
            # 创建临时文件列表
            temp_files = []
            concat_list_path = output_dir / f"concat_{uuid4().hex[:8]}.txt"
            
            # 切割每个片段
            for i, seg in enumerate(segments):
                temp_path = output_dir / f"temp_{i}_{uuid4().hex[:8]}.mp4"
                
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(seg.get("start", 0)),
                    "-i", seg["path"],
                    "-t", str(seg.get("end", 5) - seg.get("start", 0)),
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-preset", "fast",
                    str(temp_path)
                ]
                
                subprocess.run(cmd, capture_output=True, check=True)
                temp_files.append(str(temp_path))
            
            # 创建 concat 文件
            with open(concat_list_path, 'w') as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # 拼接
            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-c", "copy",
                output_path
            ]
            
            subprocess.run(concat_cmd, capture_output=True, check=True)
            
            # 计算总时长
            total_duration = sum(
                seg.get("end", 5) - seg.get("start", 0)
                for seg in segments
            )
            
            # 清理临时文件
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)
            concat_list_path.unlink(missing_ok=True)
            
            return RoughCutResult(
                output_path=output_path,
                duration=total_duration,
                segments=segments,
                success=True
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"粗剪失败: {e}")
            return RoughCutResult(
                output_path="",
                duration=0,
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"粗剪异常: {e}")
            return RoughCutResult(
                output_path="",
                duration=0,
                success=False,
                error=str(e)
            )
    
    async def generate_search_terms(
        self,
        scene_description: str,
        existing_tags: List[str] = None
    ) -> List[str]:
        """
        生成搜索词条
        
        基于场次描述生成用于素材召回的搜索词条
        """
        adapter = self._get_llm_adapter()
        if not adapter:
            # 回退：简单分词
            return self._simple_tokenize(scene_description)
        
        try:
            from services.agent_llm_adapter import AgentLLMRequest, AgentType
            
            existing_str = ", ".join(existing_tags) if existing_tags else "无"
            
            prompt = f"""根据以下场次描述，生成用于素材搜索的关键词。

场次描述：{scene_description}
已有标签：{existing_str}

请返回 JSON 格式：
{{
  "search_terms": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "scene_type": "室内/室外",
  "mood": "情绪",
  "action": "动作类型"
}}
"""
            response = await adapter.generate(AgentLLMRequest(
                agent_type=AgentType.STORYBOARD,
                task_type="generate_search_terms",
                prompt=prompt
            ))
            
            if response.success and response.parsed_data:
                return response.parsed_data.get("search_terms", [])
                
        except Exception as e:
            logger.error(f"生成搜索词条失败: {e}")
        
        return self._simple_tokenize(scene_description)
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """简单分词"""
        import re
        # 移除标点，按空格分词
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        return list(set(words))[:10]


# 全局服务实例
_storyboard_agent_service: Optional[StoryboardAgentService] = None


def get_storyboard_agent_service() -> StoryboardAgentService:
    """获取 Storyboard_Agent 服务实例"""
    global _storyboard_agent_service
    if _storyboard_agent_service is None:
        _storyboard_agent_service = StoryboardAgentService()
    return _storyboard_agent_service
