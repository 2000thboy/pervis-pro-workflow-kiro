"""
EventService - WebSocket 事件服务

管理 WebSocket 连接和实时事件推送。
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    # 任务事件
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Agent 事件
    AGENT_WORKING = "agent.working"
    AGENT_REVIEWING = "agent.reviewing"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # 系统事件
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"
    SYSTEM_INFO = "system.info"
    
    # 健康检查事件
    HEALTH_CHECK = "health.check"


@dataclass
class SystemEvent:
    """系统事件数据结构"""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventService:
    """
    事件服务 - 管理 WebSocket 连接和事件推送
    
    功能:
    - 管理多个 WebSocket 连接
    - 广播事件到所有连接的客户端
    - 提供便捷的事件发送方法
    """
    
    _instance: Optional['EventService'] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        logger.info("EventService 初始化完成")
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        建立 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        async with self._lock:
            self.connections.append(websocket)
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
        """
        async with self._lock:
            if websocket in self.connections:
                self.connections.remove(websocket)
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.connections)}")
    
    async def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        发送事件到所有连接的客户端
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = SystemEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        
        # 复制连接列表，避免迭代时修改
        async with self._lock:
            connections = self.connections.copy()
        
        # 发送到所有连接
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(event.to_dict())
            except Exception as e:
                logger.warning(f"发送事件失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.connections:
                        self.connections.remove(conn)
    
    async def emit_task_progress(
        self, 
        task_id: str, 
        progress: int, 
        message: str,
        task_type: str = "unknown",
        task_name: str = ""
    ) -> None:
        """
        发送任务进度事件
        
        Args:
            task_id: 任务 ID
            progress: 进度百分比 (0-100)
            message: 进度消息
            task_type: 任务类型
            task_name: 任务名称
        """
        await self.emit(EventType.TASK_PROGRESS.value, {
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "task_type": task_type,
            "task_name": task_name
        })
    
    async def emit_task_started(
        self,
        task_id: str,
        task_type: str,
        task_name: str,
        estimated_duration: Optional[int] = None
    ) -> None:
        """
        发送任务开始事件
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型 (export, render, ai_generate, asset_process)
            task_name: 任务名称
            estimated_duration: 预计耗时（秒）
        """
        await self.emit(EventType.TASK_STARTED.value, {
            "task_id": task_id,
            "task_type": task_type,
            "task_name": task_name,
            "estimated_duration": estimated_duration
        })
    
    async def emit_task_completed(
        self,
        task_id: str,
        task_type: str,
        task_name: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送任务完成事件
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型
            task_name: 任务名称
            result: 任务结果
        """
        await self.emit(EventType.TASK_COMPLETED.value, {
            "task_id": task_id,
            "task_type": task_type,
            "task_name": task_name,
            "result": result or {}
        })
    
    async def emit_task_failed(
        self,
        task_id: str,
        task_type: str,
        task_name: str,
        error: str,
        can_retry: bool = True
    ) -> None:
        """
        发送任务失败事件
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型
            task_name: 任务名称
            error: 错误信息
            can_retry: 是否可重试
        """
        await self.emit(EventType.TASK_FAILED.value, {
            "task_id": task_id,
            "task_type": task_type,
            "task_name": task_name,
            "error": error,
            "can_retry": can_retry
        })
    
    async def emit_agent_status(
        self, 
        agent_type: str, 
        status: str, 
        message: str,
        task_id: Optional[str] = None
    ) -> None:
        """
        发送 Agent 状态事件
        
        Args:
            agent_type: Agent 类型 (script_agent, art_agent, director_agent 等)
            status: 状态 (working, reviewing, completed, failed)
            message: 状态消息
            task_id: 关联的任务 ID
        """
        event_type = f"agent.{status}"
        await self.emit(event_type, {
            "agent_type": agent_type,
            "status": status,
            "message": message,
            "task_id": task_id
        })
    
    async def emit_system_warning(
        self, 
        warning_type: str, 
        message: str, 
        suggestion: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送系统警告事件
        
        Args:
            warning_type: 警告类型 (storage.low, asset.missing 等)
            message: 警告消息
            suggestion: 操作建议 {action, label, url, instructions}
        """
        await self.emit(EventType.SYSTEM_WARNING.value, {
            "warning_type": warning_type,
            "message": message,
            "suggestion": suggestion or {}
        })
    
    async def emit_system_error(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送系统错误事件
        
        Args:
            error_type: 错误类型
            message: 错误消息
            details: 错误详情
        """
        await self.emit(EventType.SYSTEM_ERROR.value, {
            "error_type": error_type,
            "message": message,
            "details": details or {}
        })
    
    async def emit_system_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        发送系统信息事件
        
        Args:
            message: 信息消息
            data: 附加数据
        """
        await self.emit(EventType.SYSTEM_INFO.value, {
            "message": message,
            "data": data or {}
        })
    
    @property
    def connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connections)
    
    @property
    def is_connected(self) -> bool:
        """是否有活跃连接"""
        return len(self.connections) > 0


# 全局单例实例
event_service = EventService()
