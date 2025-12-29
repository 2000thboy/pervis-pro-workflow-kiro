# -*- coding: utf-8 -*-
"""
渲染进度 SSE (Server-Sent Events) 服务

Phase 2 Task 2.1: 视频渲染完善
- 实时进度推送
- 多客户端支持
- 自动清理断开连接
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, AsyncGenerator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RenderProgressEvent:
    """渲染进度事件"""
    task_id: str
    status: str  # pending, processing, completed, failed, cancelled
    progress: float  # 0-100
    message: str = ""
    current_stage: str = ""
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    output_path: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        data = {
            "task_id": self.task_id,
            "status": self.status,
            "progress": round(self.progress, 2),
            "message": self.message,
            "current_stage": self.current_stage,
            "elapsed_time": round(self.elapsed_time, 2),
            "estimated_remaining": round(self.estimated_remaining, 2),
            "output_path": self.output_path,
            "file_size": self.file_size,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class RenderProgressSSE:
    """渲染进度 SSE 管理器"""
    
    def __init__(self):
        # task_id -> set of queues (每个客户端一个队列)
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        # 全局订阅者 (订阅所有任务)
        self._global_subscribers: Set[asyncio.Queue] = set()
        # 最新进度缓存 (用于新订阅者获取当前状态)
        self._latest_progress: Dict[str, RenderProgressEvent] = {}
        # 清理锁
        self._lock = asyncio.Lock()
    
    async def subscribe(self, task_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        订阅渲染进度
        
        Args:
            task_id: 任务ID，None 表示订阅所有任务
            
        Yields:
            SSE 格式的进度数据
        """
        queue: asyncio.Queue = asyncio.Queue()
        
        async with self._lock:
            if task_id:
                if task_id not in self._subscribers:
                    self._subscribers[task_id] = set()
                self._subscribers[task_id].add(queue)
                
                # 发送当前状态
                if task_id in self._latest_progress:
                    yield self._latest_progress[task_id].to_sse()
            else:
                self._global_subscribers.add(queue)
                
                # 发送所有任务的当前状态
                for event in self._latest_progress.values():
                    yield event.to_sse()
        
        try:
            while True:
                try:
                    # 等待新事件，超时 30 秒发送心跳
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse()
                    
                    # 如果任务完成或失败，结束订阅
                    if event.status in ["completed", "failed", "cancelled"]:
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield ": heartbeat\n\n"
                    
        finally:
            # 清理订阅
            async with self._lock:
                if task_id and task_id in self._subscribers:
                    self._subscribers[task_id].discard(queue)
                    if not self._subscribers[task_id]:
                        del self._subscribers[task_id]
                else:
                    self._global_subscribers.discard(queue)
    
    async def publish(self, event: RenderProgressEvent):
        """
        发布渲染进度事件
        
        Args:
            event: 进度事件
        """
        task_id = event.task_id
        
        # 更新缓存
        self._latest_progress[task_id] = event
        
        # 发送给任务订阅者
        if task_id in self._subscribers:
            for queue in self._subscribers[task_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(f"队列已满，跳过事件: {task_id}")
        
        # 发送给全局订阅者
        for queue in self._global_subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"全局队列已满，跳过事件: {task_id}")
        
        # 如果任务完成，延迟清理缓存
        if event.status in ["completed", "failed", "cancelled"]:
            asyncio.create_task(self._delayed_cleanup(task_id))
    
    async def _delayed_cleanup(self, task_id: str, delay: float = 60.0):
        """延迟清理已完成任务的缓存"""
        await asyncio.sleep(delay)
        async with self._lock:
            if task_id in self._latest_progress:
                if self._latest_progress[task_id].status in ["completed", "failed", "cancelled"]:
                    del self._latest_progress[task_id]
    
    def get_latest_progress(self, task_id: str) -> Optional[RenderProgressEvent]:
        """获取任务的最新进度"""
        return self._latest_progress.get(task_id)
    
    def get_all_active_tasks(self) -> Dict[str, RenderProgressEvent]:
        """获取所有活跃任务的进度"""
        return {
            task_id: event 
            for task_id, event in self._latest_progress.items()
            if event.status not in ["completed", "failed", "cancelled"]
        }


# 全局实例
_render_progress_sse: Optional[RenderProgressSSE] = None


def get_render_progress_sse() -> RenderProgressSSE:
    """获取渲染进度 SSE 实例"""
    global _render_progress_sse
    if _render_progress_sse is None:
        _render_progress_sse = RenderProgressSSE()
    return _render_progress_sse


async def publish_render_progress(
    task_id: str,
    status: str,
    progress: float,
    message: str = "",
    current_stage: str = "",
    elapsed_time: float = 0.0,
    estimated_remaining: float = 0.0,
    output_path: Optional[str] = None,
    file_size: Optional[int] = None,
    error: Optional[str] = None
):
    """便捷函数：发布渲染进度"""
    sse = get_render_progress_sse()
    event = RenderProgressEvent(
        task_id=task_id,
        status=status,
        progress=progress,
        message=message,
        current_stage=current_stage,
        elapsed_time=elapsed_time,
        estimated_remaining=estimated_remaining,
        output_path=output_path,
        file_size=file_size,
        error=error
    )
    await sse.publish(event)
