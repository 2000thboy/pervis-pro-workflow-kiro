"""
MarketAgent - 市场分析Agent

需求: 6.3 - WHEN 用户需要内容建议时 THEN 相关Agent SHALL 调用LLM提供专业建议

本模块实现市场Agent，负责:
- 调用LLM进行内容分析
- 通过MCP联网获取豆瓣电影数据
- 标签匹配和向量对比
- 市场参考数据获取
"""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from ..core.message_bus import MessageBus, Message, Response
from ..core.communication_protocol import (
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
)
from ..core.agent_types import AgentType, AgentState
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商"""
    OLLAMA = "ollama"          # 本地Ollama
    OPENAI = "openai"          # OpenAI API
    GEMINI = "gemini"          # Google Gemini


class DataSource(Enum):
    """数据源类型"""
    DOUBAN = "douban"          # 豆瓣电影
    LOCAL_DB = "local_db"      # 本地数据库
    LLM_GENERATED = "llm"      # LLM生成


class MatchType(Enum):
    """匹配类型"""
    TAG = "tag"                # 标签匹配
    VECTOR = "vector"          # 向量相似度
    SEMANTIC = "semantic"      # 语义匹配


@dataclass
class MovieReference:
    """电影参考数据"""
    id: str
    title: str
    year: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    summary: Optional[str] = None
    director: Optional[str] = None
    source: DataSource = DataSource.DOUBAN
    vector_embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "tags": self.tags,
            "genres": self.genres,
            "rating": self.rating,
            "summary": self.summary,
            "director": self.director,
            "source": self.source.value,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


@dataclass
class TagMatchResult:
    """标签匹配结果"""
    query_tags: List[str]
    matched_movie: MovieReference
    matched_tags: List[str]
    match_score: float  # 0.0 - 1.0
    match_type: MatchType
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_tags": self.query_tags,
            "matched_movie": self.matched_movie.to_dict(),
            "matched_tags": self.matched_tags,
            "match_score": self.match_score,
            "match_type": self.match_type.value
        }


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    query_text: str
    results: List[MovieReference]
    similarity_scores: List[float]
    search_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "results": [r.to_dict() for r in self.results],
            "similarity_scores": self.similarity_scores,
            "search_time_ms": self.search_time_ms
        }


@dataclass
class LLMAnalysisResult:
    """LLM分析结果"""
    id: str
    query: str
    provider: LLMProvider
    response: str
    suggested_tags: List[str] = field(default_factory=list)
    suggested_genres: List[str] = field(default_factory=list)
    confidence: float = 0.0
    tokens_used: int = 0
    latency_ms: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "provider": self.provider.value,
            "response": self.response,
            "suggested_tags": self.suggested_tags,
            "suggested_genres": self.suggested_genres,
            "confidence": self.confidence,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at
        }


@dataclass 
class ContentSuggestion:
    """内容建议"""
    id: str
    title: str
    description: str
    reference_movies: List[MovieReference] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    rationale: str = ""
    priority: int = 3  # 1-5
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "reference_movies": [m.to_dict() for m in self.reference_movies],
            "suggested_tags": self.suggested_tags,
            "rationale": self.rationale,
            "priority": self.priority,
            "created_at": self.created_at
        }



class MarketAgent(BaseAgent):
    """
    市场Agent - 豆瓣电影标签匹配和LLM分析
    
    需求: 6.3 - WHEN 用户需要内容建议时 THEN 相关Agent SHALL 调用LLM提供专业建议
    
    功能:
    - LLM分析: 调用Ollama/OpenAI/Gemini进行内容分析
    - 豆瓣数据: 通过MCP获取豆瓣电影标签和数据
    - 标签匹配: 基于标签进行电影匹配
    - 向量对比: 基于向量相似度进行语义匹配
    """
    
    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化市场Agent
        
        Args:
            agent_id: Agent唯一标识符
            message_bus: 消息总线实例
            config: Agent配置
        """
        capabilities = [
            "llm_analysis",
            "tag_matching",
            "vector_search",
            "douban_data",
            "content_suggestion"
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.MARKET,
            message_bus=message_bus,
            capabilities=capabilities,
            config=config
        )
        
        # 电影参考库
        self._movies: Dict[str, MovieReference] = {}
        # LLM分析结果缓存
        self._llm_cache: Dict[str, LLMAnalysisResult] = {}
        # 内容建议
        self._suggestions: Dict[str, ContentSuggestion] = {}
        
        # LLM配置
        self._default_provider = LLMProvider(
            config.get("llm_provider", "ollama") if config else "ollama"
        )
        self._ollama_model = config.get("ollama_model", "llama3") if config else "llama3"
        self._ollama_url = config.get("ollama_url", "http://localhost:11434") if config else "http://localhost:11434"
        
        # MCP配置
        self._mcp_enabled = config.get("mcp_enabled", False) if config else False
        
        # 限制
        self._max_movies = config.get("max_movies", 500) if config else 500
        self._max_cache = config.get("max_cache", 100) if config else 100
        
        # LLM调用回调 (用于测试和扩展)
        self._llm_handler: Optional[Callable] = None
        # MCP调用回调
        self._mcp_handler: Optional[Callable] = None
        
        logger.info(f"MarketAgent初始化: {agent_id}, LLM: {self._default_provider.value}")
    
    # ========================================================================
    # LLM集成
    # ========================================================================
    
    def set_llm_handler(self, handler: Callable):
        """设置LLM调用处理器 (用于依赖注入)"""
        self._llm_handler = handler
    
    def set_mcp_handler(self, handler: Callable):
        """设置MCP调用处理器 (用于依赖注入)"""
        self._mcp_handler = handler
    
    async def analyze_with_llm(
        self,
        query: str,
        provider: Optional[LLMProvider] = None,
        context: Optional[str] = None
    ) -> LLMAnalysisResult:
        """
        使用LLM分析内容
        
        需求: 6.3 - WHEN 用户需要内容建议时 THEN 相关Agent SHALL 调用LLM提供专业建议
        
        Args:
            query: 查询内容
            provider: LLM提供商
            context: 上下文信息
            
        Returns:
            LLM分析结果
        """
        provider = provider or self._default_provider
        start_time = datetime.utcnow()
        
        # 构建提示词
        prompt = self._build_analysis_prompt(query, context)
        
        # 调用LLM
        response_text = ""
        suggested_tags = []
        suggested_genres = []
        tokens_used = 0
        
        try:
            if self._llm_handler:
                # 使用注入的处理器
                result = await self._llm_handler(prompt, provider)
                response_text = result.get("response", "")
                suggested_tags = result.get("tags", [])
                suggested_genres = result.get("genres", [])
                tokens_used = result.get("tokens", 0)
            else:
                # 默认模拟响应 (实际实现需要调用真实LLM API)
                response_text = f"分析结果: {query}"
                suggested_tags = self._extract_tags_from_query(query)
                suggested_genres = []
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            response_text = f"LLM调用失败: {str(e)}"
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        result = LLMAnalysisResult(
            id=f"llm_{len(self._llm_cache)}",
            query=query,
            provider=provider,
            response=response_text,
            suggested_tags=suggested_tags,
            suggested_genres=suggested_genres,
            confidence=0.8 if response_text else 0.0,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
        
        # 缓存结果
        cache_key = f"{provider.value}:{query[:50]}"
        self._llm_cache[cache_key] = result
        
        if len(self._llm_cache) > self._max_cache:
            oldest_key = next(iter(self._llm_cache))
            del self._llm_cache[oldest_key]
        
        self._log_operation(
            "llm_analysis",
            details={
                "provider": provider.value,
                "query_length": len(query),
                "latency_ms": latency_ms
            }
        )
        
        return result
    
    def _build_analysis_prompt(self, query: str, context: Optional[str]) -> str:
        """构建分析提示词"""
        prompt = f"""请分析以下内容，并提取相关的电影标签和类型：

内容: {query}
"""
        if context:
            prompt += f"\n上下文: {context}"
        
        prompt += """

请返回:
1. 相关的标签 (如: 悬疑, 爱情, 科幻等)
2. 可能的电影类型
3. 风格特点
"""
        return prompt
    
    def _extract_tags_from_query(self, query: str) -> List[str]:
        """从查询中提取标签 (简单实现)"""
        # 常见电影标签
        common_tags = [
            "悬疑", "爱情", "科幻", "动作", "喜剧", "恐怖", "剧情",
            "动画", "纪录片", "战争", "历史", "奇幻", "冒险", "犯罪"
        ]
        
        found_tags = []
        for tag in common_tags:
            if tag in query:
                found_tags.append(tag)
        
        return found_tags if found_tags else ["剧情"]
    
    # ========================================================================
    # 豆瓣数据获取
    # ========================================================================
    
    async def fetch_douban_data(
        self,
        movie_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MovieReference]:
        """
        获取豆瓣电影数据
        
        Args:
            movie_name: 电影名称
            tags: 标签过滤
            limit: 返回数量
            
        Returns:
            电影参考列表
        """
        results = []
        
        try:
            if self._mcp_handler:
                # 使用MCP获取数据
                data = await self._mcp_handler({
                    "action": "search_douban",
                    "movie_name": movie_name,
                    "tags": tags,
                    "limit": limit
                })
                
                for item in data.get("movies", []):
                    movie = MovieReference(
                        id=item.get("id", f"douban_{len(results)}"),
                        title=item.get("title", ""),
                        year=item.get("year"),
                        tags=item.get("tags", []),
                        genres=item.get("genres", []),
                        rating=item.get("rating"),
                        summary=item.get("summary"),
                        director=item.get("director"),
                        source=DataSource.DOUBAN
                    )
                    results.append(movie)
                    self._movies[movie.id] = movie
            else:
                # 从本地缓存返回
                movies = list(self._movies.values())
                
                if movie_name:
                    movies = [m for m in movies if movie_name.lower() in m.title.lower()]
                
                if tags:
                    movies = [m for m in movies if any(t in m.tags for t in tags)]
                
                results = movies[:limit]
                
        except Exception as e:
            logger.error(f"获取豆瓣数据失败: {e}")
        
        self._log_operation(
            "fetch_douban_data",
            details={
                "movie_name": movie_name,
                "tags": tags,
                "results_count": len(results)
            }
        )
        
        return results
    
    async def add_movie_reference(
        self,
        movie_id: str,
        title: str,
        tags: List[str],
        genres: Optional[List[str]] = None,
        year: Optional[int] = None,
        rating: Optional[float] = None,
        summary: Optional[str] = None,
        source: DataSource = DataSource.LOCAL_DB
    ) -> MovieReference:
        """
        添加电影参考数据
        
        Args:
            movie_id: 电影ID
            title: 标题
            tags: 标签
            genres: 类型
            year: 年份
            rating: 评分
            summary: 简介
            source: 数据源
            
        Returns:
            创建的电影参考
        """
        movie = MovieReference(
            id=movie_id,
            title=title,
            tags=tags,
            genres=genres or [],
            year=year,
            rating=rating,
            summary=summary,
            source=source
        )
        
        self._movies[movie_id] = movie
        
        if len(self._movies) > self._max_movies:
            oldest_id = next(iter(self._movies))
            del self._movies[oldest_id]
        
        self._log_operation(
            "movie_added",
            details={"movie_id": movie_id, "title": title}
        )
        
        return movie
    
    async def get_movie(self, movie_id: str) -> Optional[MovieReference]:
        """获取电影参考"""
        return self._movies.get(movie_id)
    
    async def list_movies(
        self,
        tags: Optional[List[str]] = None,
        genres: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        limit: int = 20
    ) -> List[MovieReference]:
        """列出电影参考"""
        movies = list(self._movies.values())
        
        if tags:
            movies = [m for m in movies if any(t in m.tags for t in tags)]
        
        if genres:
            movies = [m for m in movies if any(g in m.genres for g in genres)]
        
        if min_rating is not None:
            movies = [m for m in movies if m.rating and m.rating >= min_rating]
        
        # 按评分排序
        movies.sort(key=lambda m: m.rating or 0, reverse=True)
        
        return movies[:limit]
    
    # ========================================================================
    # 标签匹配
    # ========================================================================
    
    async def match_by_tags(
        self,
        query_tags: List[str],
        min_score: float = 0.3,
        limit: int = 10
    ) -> List[TagMatchResult]:
        """
        基于标签匹配电影
        
        Args:
            query_tags: 查询标签
            min_score: 最小匹配分数
            limit: 返回数量
            
        Returns:
            匹配结果列表
        """
        # 空标签返回空结果
        if not query_tags:
            return []
        
        results = []
        query_set = set(query_tags)
        
        for movie in self._movies.values():
            movie_tags = set(movie.tags)
            
            if not movie_tags:
                continue
            
            # 计算Jaccard相似度
            intersection = query_set & movie_tags
            union = query_set | movie_tags
            
            if union:
                score = len(intersection) / len(union)
            else:
                score = 0.0
            
            if score >= min_score:
                results.append(TagMatchResult(
                    query_tags=query_tags,
                    matched_movie=movie,
                    matched_tags=list(intersection),
                    match_score=score,
                    match_type=MatchType.TAG
                ))
        
        # 按分数排序
        results.sort(key=lambda r: r.match_score, reverse=True)
        
        self._log_operation(
            "tag_matching",
            details={
                "query_tags": query_tags,
                "results_count": len(results[:limit])
            }
        )
        
        return results[:limit]
    
    # ========================================================================
    # 向量搜索
    # ========================================================================
    
    async def vector_search(
        self,
        query_text: str,
        limit: int = 10
    ) -> VectorSearchResult:
        """
        基于向量相似度搜索
        
        Args:
            query_text: 查询文本
            limit: 返回数量
            
        Returns:
            向量搜索结果
        """
        start_time = datetime.utcnow()
        
        results = []
        scores = []
        
        # 简单实现: 基于文本相似度
        # 实际实现需要使用向量数据库 (如ChromaDB)
        query_lower = query_text.lower()
        
        for movie in self._movies.values():
            score = 0.0
            
            # 标题匹配
            if query_lower in movie.title.lower():
                score += 0.5
            
            # 标签匹配
            for tag in movie.tags:
                if tag.lower() in query_lower:
                    score += 0.2
            
            # 简介匹配
            if movie.summary and query_lower in movie.summary.lower():
                score += 0.3
            
            if score > 0:
                results.append(movie)
                scores.append(min(score, 1.0))
        
        # 排序
        paired = list(zip(results, scores))
        paired.sort(key=lambda x: x[1], reverse=True)
        
        results = [p[0] for p in paired[:limit]]
        scores = [p[1] for p in paired[:limit]]
        
        end_time = datetime.utcnow()
        search_time = (end_time - start_time).total_seconds() * 1000
        
        self._log_operation(
            "vector_search",
            details={
                "query": query_text[:50],
                "results_count": len(results),
                "search_time_ms": search_time
            }
        )
        
        return VectorSearchResult(
            query_text=query_text,
            results=results,
            similarity_scores=scores,
            search_time_ms=search_time
        )
    
    # ========================================================================
    # 内容建议
    # ========================================================================
    
    async def generate_suggestion(
        self,
        project_description: str,
        use_llm: bool = True
    ) -> ContentSuggestion:
        """
        生成内容建议
        
        Args:
            project_description: 项目描述
            use_llm: 是否使用LLM
            
        Returns:
            内容建议
        """
        suggested_tags = []
        reference_movies = []
        rationale = ""
        
        # 使用LLM分析
        if use_llm:
            llm_result = await self.analyze_with_llm(project_description)
            suggested_tags = llm_result.suggested_tags
            rationale = llm_result.response
        else:
            suggested_tags = self._extract_tags_from_query(project_description)
            rationale = "基于关键词提取"
        
        # 匹配参考电影
        if suggested_tags:
            matches = await self.match_by_tags(suggested_tags, min_score=0.2, limit=5)
            reference_movies = [m.matched_movie for m in matches]
        
        suggestion = ContentSuggestion(
            id=f"suggestion_{len(self._suggestions)}",
            title=f"内容建议: {project_description[:30]}...",
            description=project_description,
            reference_movies=reference_movies,
            suggested_tags=suggested_tags,
            rationale=rationale,
            priority=3
        )
        
        self._suggestions[suggestion.id] = suggestion
        
        self._log_operation(
            "suggestion_generated",
            details={
                "suggestion_id": suggestion.id,
                "tags_count": len(suggested_tags),
                "references_count": len(reference_movies)
            }
        )
        
        return suggestion
    
    async def get_suggestion(self, suggestion_id: str) -> Optional[ContentSuggestion]:
        """获取建议"""
        return self._suggestions.get(suggestion_id)
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        content = message.content
        action = content.get("action")
        
        if action == "analyze":
            result = await self.analyze_with_llm(
                content.get("query", ""),
                context=content.get("context")
            )
            return Response(
                success=True,
                message_id=message.id,
                data=result.to_dict()
            )
        
        elif action == "match_tags":
            results = await self.match_by_tags(
                content.get("tags", []),
                min_score=content.get("min_score", 0.3),
                limit=content.get("limit", 10)
            )
            return Response(
                success=True,
                message_id=message.id,
                data={"matches": [r.to_dict() for r in results]}
            )
        
        elif action == "vector_search":
            result = await self.vector_search(
                content.get("query", ""),
                limit=content.get("limit", 10)
            )
            return Response(
                success=True,
                message_id=message.id,
                data=result.to_dict()
            )
        
        elif action == "generate_suggestion":
            suggestion = await self.generate_suggestion(
                content.get("description", ""),
                use_llm=content.get("use_llm", True)
            )
            return Response(
                success=True,
                message_id=message.id,
                data=suggestion.to_dict()
            )
        
        return None
    
    async def handle_protocol_message(
        self,
        message: ProtocolMessage
    ) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        data = message.payload.data
        
        if msg_type == ProtocolMessageType.TASK_REQUEST:
            task_type = data.get("task_type")
            
            if task_type == "llm_analysis":
                result = await self.analyze_with_llm(
                    data.get("query", ""),
                    context=data.get("context")
                )
                return message.create_response(
                    ProtocolStatus.SUCCESS,
                    data=result.to_dict()
                )
            
            elif task_type == "tag_matching":
                results = await self.match_by_tags(
                    data.get("tags", []),
                    min_score=data.get("min_score", 0.3)
                )
                return message.create_response(
                    ProtocolStatus.SUCCESS,
                    data={"matches": [r.to_dict() for r in results]}
                )
        
        return None
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "movies_count": len(self._movies),
            "llm_cache_count": len(self._llm_cache),
            "suggestions_count": len(self._suggestions),
            "default_llm_provider": self._default_provider.value,
            "mcp_enabled": self._mcp_enabled,
            "movies_by_source": {
                source.value: len([m for m in self._movies.values() if m.source == source])
                for source in DataSource
            }
        }
