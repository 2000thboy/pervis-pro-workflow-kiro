"""
批量处理队列管理器
Phase 4: 并发处理、队列管理、性能优化
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class BatchTask:
    id: str
    task_type: str  # 'video_processing', 'transcription', 'visual_analysis'
    asset_id: str
    file_path: str
    parameters: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class BatchProcessor:
    
    def __init__(self, max_workers: int = None, max_concurrent_tasks: int = 5):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # 任务队列和状态管理
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, BatchTask] = {}
        self.completed_tasks: Dict[str, BatchTask] = {}
        self.task_history: List[BatchTask] = []
        
        # 线程池和进程池
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 1))
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_processing_time": 0.0,
            "queue_size": 0,
            "active_workers": 0
        }
        
        # 控制标志
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        logger.info(f"批量处理器初始化: {self.max_workers}个工作线程, {max_concurrent_tasks}个并发任务")
    
    async def start(self):
        """启动批量处理器"""
        
        if self.is_running:
            logger.warning("批量处理器已在运行")
            return
        
        self.is_running = True
        
        # 启动工作协程
        for i in range(self.max_concurrent_tasks):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        # 启动统计更新协程
        stats_task = asyncio.create_task(self._update_stats())
        self.worker_tasks.append(stats_task)
        
        logger.info(f"批量处理器已启动，{len(self.worker_tasks)}个工作协程")
    
    async def stop(self):
        """停止批量处理器"""
        
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消所有工作协程
        for task in self.worker_tasks:
            task.cancel()
        
        # 等待所有任务完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # 关闭线程池
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        
        logger.info("批量处理器已停止")
    
    async def submit_task(self, 
                         task_type: str,
                         asset_id: str,
                         file_path: str,
                         parameters: Dict[str, Any] = None,
                         priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交批量处理任务"""
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = BatchTask(
            id=task_id,
            task_type=task_type,
            asset_id=asset_id,
            file_path=file_path,
            parameters=parameters or {},
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=time.time()
        )
        
        await self.task_queue.put(task)
        self.stats["total_tasks"] += 1
        self.stats["queue_size"] = self.task_queue.qsize()
        
        logger.info(f"任务已提交: {task_id} ({task_type})")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        
        # 检查运行中的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return self._task_to_dict(task)
        
        # 检查已完成的任务
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return self._task_to_dict(task)
        
        # 检查队列中的任务
        for task in list(self.task_queue._queue):
            if task.id == task_id:
                return self._task_to_dict(task)
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        
        # 如果任务在运行中，标记为取消
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            logger.info(f"任务已标记为取消: {task_id}")
            return True
        
        # 如果任务在队列中，移除
        queue_items = []
        found = False
        
        while not self.task_queue.empty():
            task = await self.task_queue.get()
            if task.id == task_id:
                task.status = TaskStatus.CANCELLED
                self.completed_tasks[task_id] = task
                found = True
                logger.info(f"任务已从队列中取消: {task_id}")
            else:
                queue_items.append(task)
        
        # 重新加入队列
        for item in queue_items:
            await self.task_queue.put(item)
        
        return found
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        
        return {
            "queue_size": self.task_queue.qsize(),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "stats": self.stats.copy(),
            "is_running": self.is_running,
            "active_workers": len([t for t in self.worker_tasks if not t.done()])
        }
    
    async def _worker(self, worker_name: str):
        """工作协程"""
        
        logger.info(f"工作协程启动: {worker_name}")
        
        while self.is_running:
            try:
                # 获取任务 (带超时)
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                if task.status == TaskStatus.CANCELLED:
                    continue
                
                # 开始处理任务
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                self.running_tasks[task.id] = task
                
                logger.info(f"{worker_name} 开始处理任务: {task.id} ({task.task_type})")
                
                # 执行任务
                try:
                    result = await self._execute_task(task)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    self.stats["completed_tasks"] += 1
                    
                except Exception as e:
                    logger.error(f"任务执行失败: {task.id}, 错误: {e}")
                    task.error = str(e)
                    task.retry_count += 1
                    
                    if task.retry_count < task.max_retries:
                        # 重新加入队列
                        task.status = TaskStatus.PENDING
                        await self.task_queue.put(task)
                        logger.info(f"任务重试: {task.id} ({task.retry_count}/{task.max_retries})")
                    else:
                        task.status = TaskStatus.FAILED
                        self.stats["failed_tasks"] += 1
                
                # 完成任务
                task.completed_at = time.time()
                self.completed_tasks[task.id] = task
                
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                # 更新平均处理时间
                if task.started_at and task.completed_at:
                    processing_time = task.completed_at - task.started_at
                    self._update_average_processing_time(processing_time)
                
                logger.info(f"{worker_name} 完成任务: {task.id} ({task.status.value})")
                
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except Exception as e:
                logger.error(f"{worker_name} 工作协程错误: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"工作协程停止: {worker_name}")
    
    async def _execute_task(self, task: BatchTask) -> Dict[str, Any]:
        """执行具体任务"""
        
        if task.task_type == "video_processing":
            return await self._execute_video_processing(task)
        elif task.task_type == "transcription":
            return await self._execute_transcription(task)
        elif task.task_type == "visual_analysis":
            return await self._execute_visual_analysis(task)
        else:
            raise ValueError(f"未知任务类型: {task.task_type}")
    
    async def _execute_video_processing(self, task: BatchTask) -> Dict[str, Any]:
        """执行视频处理任务"""
        
        from services.video_processor import VideoProcessor
        
        processor = VideoProcessor()
        
        # 更新进度
        task.progress = 10.0
        
        # 执行视频处理
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.thread_executor,
            lambda: asyncio.run(processor.process_video(task.asset_id, task.file_path))
        )
        
        task.progress = 100.0
        return result
    
    async def _execute_transcription(self, task: BatchTask) -> Dict[str, Any]:
        """执行转录任务"""
        
        from services.audio_transcriber import AudioTranscriber
        
        transcriber = AudioTranscriber()
        
        # 更新进度
        task.progress = 10.0
        
        # 执行转录
        result = await transcriber.transcribe_audio(task.file_path, task.asset_id)
        
        task.progress = 100.0
        return result
    
    async def _execute_visual_analysis(self, task: BatchTask) -> Dict[str, Any]:
        """执行视觉分析任务"""
        
        from services.visual_processor import VisualProcessor
        
        processor = VisualProcessor()
        
        # 更新进度
        task.progress = 10.0
        
        # 获取参数
        sample_interval = task.parameters.get("sample_interval", 2.0)
        
        # 执行视觉分析
        result = await processor.extract_visual_features(
            task.file_path, task.asset_id, sample_interval
        )
        
        task.progress = 100.0
        return result
    
    async def _update_stats(self):
        """更新统计信息"""
        
        while self.is_running:
            try:
                self.stats["queue_size"] = self.task_queue.qsize()
                self.stats["active_workers"] = len([t for t in self.worker_tasks if not t.done()])
                
                await asyncio.sleep(5)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"统计更新错误: {e}")
                await asyncio.sleep(5)
    
    def _update_average_processing_time(self, processing_time: float):
        """更新平均处理时间"""
        
        current_avg = self.stats["average_processing_time"]
        completed_count = self.stats["completed_tasks"]
        
        if completed_count == 1:
            self.stats["average_processing_time"] = processing_time
        else:
            # 计算移动平均
            self.stats["average_processing_time"] = (
                (current_avg * (completed_count - 1) + processing_time) / completed_count
            )
    
    def _task_to_dict(self, task: BatchTask) -> Dict[str, Any]:
        """将任务转换为字典"""
        
        task_dict = asdict(task)
        task_dict["status"] = task.status.value
        task_dict["priority"] = task.priority.value
        
        # 计算处理时间
        if task.started_at and task.completed_at:
            task_dict["processing_time"] = task.completed_at - task.started_at
        elif task.started_at:
            task_dict["processing_time"] = time.time() - task.started_at
        else:
            task_dict["processing_time"] = 0
        
        return task_dict
    
    async def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务历史"""
        
        all_tasks = []
        
        # 添加已完成的任务
        for task in self.completed_tasks.values():
            all_tasks.append(self._task_to_dict(task))
        
        # 添加运行中的任务
        for task in self.running_tasks.values():
            all_tasks.append(self._task_to_dict(task))
        
        # 按创建时间排序
        all_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return all_tasks[:limit]
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # 清理已完成的任务
        to_remove = []
        for task_id, task in self.completed_tasks.items():
            if current_time - task.created_at > max_age_seconds:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.completed_tasks[task_id]
        
        logger.info(f"清理了 {len(to_remove)} 个旧任务")
        
        return len(to_remove)

# 全局批量处理器实例
_batch_processor: Optional[BatchProcessor] = None

def get_batch_processor() -> BatchProcessor:
    """获取全局批量处理器实例"""
    
    global _batch_processor
    
    if _batch_processor is None:
        max_workers = int(os.getenv("BATCH_MAX_WORKERS", "8"))
        max_concurrent = int(os.getenv("BATCH_MAX_CONCURRENT", "5"))
        
        _batch_processor = BatchProcessor(
            max_workers=max_workers,
            max_concurrent_tasks=max_concurrent
        )
    
    return _batch_processor

async def start_batch_processor():
    """启动全局批量处理器"""
    
    processor = get_batch_processor()
    await processor.start()

async def stop_batch_processor():
    """停止全局批量处理器"""
    
    global _batch_processor
    
    if _batch_processor:
        await _batch_processor.stop()
        _batch_processor = None