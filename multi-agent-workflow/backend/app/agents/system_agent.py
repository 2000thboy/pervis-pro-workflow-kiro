"""
系统Agent - 提供用户交互接口和系统状态查询

需求: 1.5 - WHEN 用户查询系统状态时 THEN 系统Agent SHALL 提供实时的Agent状态信息
需求: 8.1 - WHEN 用户需要与Agent交互时 THEN 系统Agent SHALL 在界面上提供对话框
需求: 8.5 - WHEN 用户需要检索信息时 THEN 系统Agent SHALL 提供智能搜索功能

本模块实现了系统Agent，负责:
- 提供用户交互接口
- 实时查询和返回系统状态
- 提供智能搜索功能
- 管理用户会话
"""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .base_agent import BaseAgent, AgentLifecycleState
from ..core.message_bus import MessageBus, Message, Response
from ..core.agent_types import AgentState, AgentType
from ..core.communication_protocol import (
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
)

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """搜索类型枚举"""
    AGENT = "agent"              # 搜索Agent
    PROJECT = "project"          # 搜索项目
    ASSET = "asset"              # 搜索素材
    WORKFLOW = "workflow"        # 搜索工作流
    LOG = "log"                  # 搜索日志
    ALL = "all"                  # 全局搜索


@dataclass
class SearchResult:
    """搜索结果"""
    result_type: SearchType
    result_id: str
    title: str
    description: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_type": self.result_type.value,
            "result_id": self.result_id,
            "title": self.title,
            "description": self.description,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }



@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "context": self.context
        }


class SystemAgent(BaseAgent):
    """
    系统Agent - 提供用户交互接口和系统状态查询
    
    作为用户与系统交互的主要接口，系统Agent负责:
    - 提供实时的Agent状态信息
    - 提供智能搜索功能
    - 管理用户会话
    - 处理用户对话请求
    
    需求: 1.5 - 提供实时的Agent状态信息
    需求: 8.1 - 提供用户交互对话框
    需求: 8.5 - 提供智能搜索功能
    """
    
    # 系统Agent的固定ID
    SYSTEM_AGENT_ID = "system"
    
    def __init__(
        self,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化系统Agent
        
        Args:
            message_bus: 消息总线实例
            config: 配置选项
        """
        super().__init__(
            agent_id=self.SYSTEM_AGENT_ID,
            agent_type=AgentType.SYSTEM,
            message_bus=message_bus,
            capabilities=[
                "status_query",
                "smart_search",
                "user_interaction",
                "session_management",
                "system_monitoring"
            ],
            config=config
        )
        
        # Agent状态缓存
        self._agent_status_cache: Dict[str, Dict[str, Any]] = {}
        # 用户会话
        self._sessions: Dict[str, UserSession] = {}
        # 搜索索引（简化实现）
        self._search_index: Dict[str, List[Dict[str, Any]]] = {
            "agents": [],
            "projects": [],
            "assets": [],
            "workflows": [],
            "logs": []
        }
        # 状态更新时间戳
        self._last_status_update: Optional[str] = None
        
        logger.info("系统Agent创建完成")

    
    # ========================================================================
    # 生命周期钩子
    # ========================================================================
    
    async def _on_initialize(self):
        """初始化钩子"""
        # 注册状态查询处理器
        self.register_message_handler(
            ProtocolMessageType.AGENT_STATUS,
            self._handle_status_update
        )
        # 注册数据请求处理器
        self.register_message_handler(
            ProtocolMessageType.DATA_REQUEST,
            self._handle_data_request
        )
        logger.info("系统Agent初始化完成")
    
    async def _on_start(self):
        """启动钩子"""
        # 订阅所有Agent的状态更新
        await self._message_bus.subscribe(
            self._agent_id,
            "agent.status",
            self._handle_status_broadcast
        )
        # 初始化Agent状态缓存
        await self._refresh_agent_status()
        logger.info("系统Agent已启动，开始监听状态更新")
    
    async def _on_stop(self):
        """停止钩子"""
        # 清理会话
        self._sessions.clear()
        logger.info("系统Agent正在停止")
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        self._log_operation(
            "message_received",
            details={"message_id": message.id, "source": message.source}
        )
        return None
    
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        
        if msg_type == ProtocolMessageType.DATA_REQUEST:
            return await self._handle_data_request(message)
        elif msg_type == ProtocolMessageType.AGENT_STATUS:
            return await self._handle_status_update(message)
        
        return None

    
    # ========================================================================
    # 状态查询 - 需求 1.5
    # ========================================================================
    
    async def _handle_status_update(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理Agent状态更新"""
        data = message.payload.data
        agent_id = data.get("agent_id")
        
        if agent_id:
            self._agent_status_cache[agent_id] = {
                "agent_id": agent_id,
                "agent_type": data.get("agent_type"),
                "work_state": data.get("new_state", data.get("work_state")),
                "current_task": data.get("current_task"),
                "last_update": datetime.utcnow().isoformat()
            }
            self._last_status_update = datetime.utcnow().isoformat()
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data={"acknowledged": True}
        )
    
    async def _handle_status_broadcast(self, message: Message):
        """处理状态广播消息"""
        content = message.content
        agent_id = content.get("agent_id")
        
        if agent_id:
            self._agent_status_cache[agent_id] = {
                "agent_id": agent_id,
                "agent_type": content.get("agent_type"),
                "work_state": content.get("new_state", content.get("work_state")),
                "current_task": content.get("current_task"),
                "last_update": datetime.utcnow().isoformat()
            }
            self._last_status_update = datetime.utcnow().isoformat()
    
    async def _refresh_agent_status(self):
        """刷新所有Agent状态"""
        # 向导演Agent请求所有Agent状态
        if self._protocol and self._protocol.is_running:
            response = await self.request(
                "director",
                ProtocolMessageType.DATA_REQUEST,
                {"request_type": "registered_agents"},
                timeout=5.0
            )
            
            if response.success and response.data:
                agents = response.data.get("agents", [])
                for agent_info in agents:
                    agent_id = agent_info.get("agent_id")
                    if agent_id:
                        self._agent_status_cache[agent_id] = agent_info
    
    def get_all_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有Agent的状态
        
        需求: 1.5 - 提供实时的Agent状态信息
        
        Returns:
            所有Agent状态的字典
        """
        return {
            "agents": self._agent_status_cache.copy(),
            "last_update": self._last_status_update,
            "total_agents": len(self._agent_status_cache)
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定Agent的状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent状态信息
        """
        return self._agent_status_cache.get(agent_id)
    
    def update_agent_status(self, agent_id: str, status: Dict[str, Any]):
        """
        更新Agent状态缓存
        
        Args:
            agent_id: Agent ID
            status: 状态信息
        """
        self._agent_status_cache[agent_id] = {
            **status,
            "last_update": datetime.utcnow().isoformat()
        }
        self._last_status_update = datetime.utcnow().isoformat()

    
    # ========================================================================
    # 智能搜索 - 需求 8.5
    # ========================================================================
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.ALL,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        执行智能搜索
        
        需求: 8.5 - 提供智能搜索功能
        
        Args:
            query: 搜索查询
            search_type: 搜索类型
            limit: 结果数量限制
            
        Returns:
            搜索结果列表
        """
        await self.update_work_state(AgentState.WORKING, f"searching_{query}")
        
        results: List[SearchResult] = []
        query_lower = query.lower()
        
        # 根据搜索类型执行搜索
        if search_type in [SearchType.ALL, SearchType.AGENT]:
            results.extend(await self._search_agents(query_lower))
        
        if search_type in [SearchType.ALL, SearchType.PROJECT]:
            results.extend(await self._search_projects(query_lower))
        
        if search_type in [SearchType.ALL, SearchType.ASSET]:
            results.extend(await self._search_assets(query_lower))
        
        if search_type in [SearchType.ALL, SearchType.WORKFLOW]:
            results.extend(await self._search_workflows(query_lower))
        
        if search_type in [SearchType.ALL, SearchType.LOG]:
            results.extend(await self._search_logs(query_lower))
        
        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        await self.update_work_state(AgentState.IDLE)
        
        self._log_operation(
            "search_executed",
            details={
                "query": query,
                "search_type": search_type.value,
                "results_count": len(results[:limit])
            }
        )
        
        return results[:limit]
    
    async def _search_agents(self, query: str) -> List[SearchResult]:
        """搜索Agent"""
        results = []
        
        for agent_id, status in self._agent_status_cache.items():
            score = self._calculate_relevance(query, [
                agent_id,
                status.get("agent_type", ""),
                status.get("work_state", ""),
                status.get("current_task", "") or ""
            ])
            
            if score > 0:
                results.append(SearchResult(
                    result_type=SearchType.AGENT,
                    result_id=agent_id,
                    title=f"Agent: {agent_id}",
                    description=f"Type: {status.get('agent_type')}, State: {status.get('work_state')}",
                    relevance_score=score,
                    metadata=status
                ))
        
        return results
    
    async def _search_projects(self, query: str) -> List[SearchResult]:
        """搜索项目"""
        results = []
        
        for item in self._search_index.get("projects", []):
            score = self._calculate_relevance(query, [
                item.get("name", ""),
                item.get("description", ""),
                item.get("status", "")
            ])
            
            if score > 0:
                results.append(SearchResult(
                    result_type=SearchType.PROJECT,
                    result_id=item.get("id", ""),
                    title=item.get("name", "Unknown Project"),
                    description=item.get("description", ""),
                    relevance_score=score,
                    metadata=item
                ))
        
        return results
    
    async def _search_assets(self, query: str) -> List[SearchResult]:
        """搜索素材"""
        results = []
        
        for item in self._search_index.get("assets", []):
            score = self._calculate_relevance(query, [
                item.get("name", ""),
                item.get("tags", []),
                item.get("type", "")
            ])
            
            if score > 0:
                results.append(SearchResult(
                    result_type=SearchType.ASSET,
                    result_id=item.get("id", ""),
                    title=item.get("name", "Unknown Asset"),
                    description=f"Type: {item.get('type', 'unknown')}",
                    relevance_score=score,
                    metadata=item
                ))
        
        return results
    
    async def _search_workflows(self, query: str) -> List[SearchResult]:
        """搜索工作流"""
        results = []
        
        for item in self._search_index.get("workflows", []):
            score = self._calculate_relevance(query, [
                item.get("name", ""),
                item.get("type", ""),
                item.get("status", "")
            ])
            
            if score > 0:
                results.append(SearchResult(
                    result_type=SearchType.WORKFLOW,
                    result_id=item.get("id", ""),
                    title=item.get("name", "Unknown Workflow"),
                    description=f"Status: {item.get('status', 'unknown')}",
                    relevance_score=score,
                    metadata=item
                ))
        
        return results
    
    async def _search_logs(self, query: str) -> List[SearchResult]:
        """搜索日志"""
        results = []
        
        # 搜索自身的操作日志
        logs = self.get_operation_logs(limit=100)
        for log in logs:
            score = self._calculate_relevance(query, [
                log.get("operation", ""),
                str(log.get("details", {}))
            ])
            
            if score > 0:
                results.append(SearchResult(
                    result_type=SearchType.LOG,
                    result_id=log.get("timestamp", ""),
                    title=f"Log: {log.get('operation', 'unknown')}",
                    description=str(log.get("details", {}))[:100],
                    relevance_score=score,
                    metadata=log
                ))
        
        return results
    
    def _calculate_relevance(self, query: str, fields: List[Any]) -> float:
        """计算相关性分数"""
        score = 0.0
        
        for field in fields:
            if isinstance(field, list):
                for item in field:
                    if query in str(item).lower():
                        score += 0.5
            elif isinstance(field, str):
                if query in field.lower():
                    score += 1.0
                    # 完全匹配加分
                    if query == field.lower():
                        score += 0.5
        
        return min(score, 1.0)  # 归一化到0-1

    
    # ========================================================================
    # 用户交互 - 需求 8.1
    # ========================================================================
    
    async def _handle_data_request(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理数据请求"""
        data = message.payload.data
        request_type = data.get("request_type")
        
        response_data = {}
        
        if request_type == "system_status":
            response_data = self.get_all_agent_status()
        elif request_type == "agent_status":
            agent_id = data.get("agent_id")
            response_data = self.get_agent_status(agent_id) or {"error": "Agent not found"}
        elif request_type == "search":
            query = data.get("query", "")
            search_type = SearchType(data.get("search_type", "all"))
            limit = data.get("limit", 20)
            results = await self.search(query, search_type, limit)
            response_data = {"results": [r.to_dict() for r in results]}
        elif request_type == "session_info":
            session_id = data.get("session_id")
            session = self._sessions.get(session_id)
            response_data = session.to_dict() if session else {"error": "Session not found"}
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data=response_data
        )
    
    def create_session(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> UserSession:
        """
        创建用户会话
        
        需求: 8.1 - 提供用户交互接口
        
        Args:
            user_id: 用户ID
            context: 会话上下文
            
        Returns:
            用户会话对象
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            context=context or {}
        )
        
        self._sessions[session_id] = session
        
        self._log_operation(
            "session_created",
            details={"session_id": session_id, "user_id": user_id}
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """获取用户会话"""
        return self._sessions.get(session_id)
    
    def update_session_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """更新会话上下文"""
        session = self._sessions.get(session_id)
        if session:
            session.context.update(context)
            session.last_activity = datetime.utcnow().isoformat()
            return True
        return False
    
    def close_session(self, session_id: str) -> bool:
        """关闭用户会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._log_operation(
                "session_closed",
                details={"session_id": session_id}
            )
            return True
        return False
    
    # ========================================================================
    # 搜索索引管理
    # ========================================================================
    
    def add_to_search_index(self, index_type: str, item: Dict[str, Any]):
        """添加项目到搜索索引"""
        if index_type in self._search_index:
            self._search_index[index_type].append(item)
    
    def remove_from_search_index(self, index_type: str, item_id: str):
        """从搜索索引移除项目"""
        if index_type in self._search_index:
            self._search_index[index_type] = [
                item for item in self._search_index[index_type]
                if item.get("id") != item_id
            ]
    
    def clear_search_index(self, index_type: Optional[str] = None):
        """清空搜索索引"""
        if index_type:
            if index_type in self._search_index:
                self._search_index[index_type] = []
        else:
            for key in self._search_index:
                self._search_index[key] = []
    
    # ========================================================================
    # 状态查询
    # ========================================================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统Agent状态"""
        return {
            **self.get_status(),
            "cached_agents": len(self._agent_status_cache),
            "active_sessions": len(self._sessions),
            "search_index_sizes": {k: len(v) for k, v in self._search_index.items()},
            "last_status_update": self._last_status_update
        }
