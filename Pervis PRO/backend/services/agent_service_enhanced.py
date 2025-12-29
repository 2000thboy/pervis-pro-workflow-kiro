# -*- coding: utf-8 -*-
"""
增强版 Agent 服务

Phase 2 Task 2.3: Agent 协作优化
- LLM 调用重试机制
- 任务超时处理
- Agent 状态持久化
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from uuid import uuid4

from .agent_service import (
    AgentService,
    AgentTask,
    AgentTaskStatus,
    ContentSource,
    get_agent_service as get_base_agent_service,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================
# 重试配置
# ============================================================

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3                    # 最大重试次数
    base_delay: float = 1.0                 # 基础延迟（秒）
    max_delay: float = 30.0                 # 最大延迟（秒）
    exponential_base: float = 2.0           # 指数退避基数
    jitter: bool = True                     # 是否添加抖动
    retry_on_exceptions: tuple = (Exception,)  # 重试的异常类型


@dataclass
class TimeoutConfig:
    """超时配置"""
    default_timeout: float = 60.0           # 默认超时（秒）
    llm_call_timeout: float = 30.0          # LLM 调用超时
    review_timeout: float = 20.0            # 审核超时
    task_timeout: float = 120.0             # 任务总超时


# ============================================================
# 重试装饰器
# ============================================================

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retry_on: tuple = (Exception,)
):
    """
    重试装饰器
    
    支持指数退避和抖动
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # 计算延迟
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        # 添加抖动 (±25%)
                        import random
                        jitter = delay * 0.25 * (random.random() * 2 - 1)
                        delay += jitter
                        
                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}. "
                            f"将在 {delay:.2f}s 后重试"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 最终失败 (已重试 {max_retries} 次): {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def with_timeout(timeout: float):
    """超时装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"{func.__name__} 超时 ({timeout}s)")
                raise TimeoutError(f"操作超时 ({timeout}s)")
        
        return wrapper
    return decorator


# ============================================================
# 任务持久化
# ============================================================

class TaskPersistence:
    """任务持久化管理"""
    
    def __init__(self, db_session=None):
        self._db = db_session
        self._cache: Dict[str, AgentTask] = {}
    
    async def save_task(self, task: AgentTask) -> bool:
        """保存任务到数据库"""
        try:
            if self._db is None:
                # 无数据库，仅缓存
                self._cache[task.task_id] = task
                return True
            
            from models.agent_task import AgentTaskModel
            
            # 查找或创建
            db_task = self._db.query(AgentTaskModel).filter(
                AgentTaskModel.task_id == task.task_id
            ).first()
            
            if db_task:
                # 更新
                db_task.status = task.status.value
                db_task.progress = task.progress
                db_task.message = task.message
                db_task.result = json.dumps(task.result) if task.result else None
                db_task.error = task.error
                db_task.updated_at = datetime.now()
                if task.completed_at:
                    db_task.completed_at = task.completed_at
            else:
                # 创建
                db_task = AgentTaskModel(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    agent_type=task.agent_type,
                    status=task.status.value,
                    progress=task.progress,
                    message=task.message,
                    input_data=json.dumps(task.input_data),
                    result=json.dumps(task.result) if task.result else None,
                    source=task.source.value,
                    error=task.error,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                self._db.add(db_task)
            
            self._db.commit()
            self._cache[task.task_id] = task
            return True
            
        except Exception as e:
            logger.error(f"保存任务失败: {e}")
            self._cache[task.task_id] = task
            return False
    
    async def load_task(self, task_id: str) -> Optional[AgentTask]:
        """从数据库加载任务"""
        # 先查缓存
        if task_id in self._cache:
            return self._cache[task_id]
        
        if self._db is None:
            return None
        
        try:
            from models.agent_task import AgentTaskModel
            
            db_task = self._db.query(AgentTaskModel).filter(
                AgentTaskModel.task_id == task_id
            ).first()
            
            if not db_task:
                return None
            
            task = AgentTask(
                task_id=db_task.task_id,
                task_type=db_task.task_type,
                agent_type=db_task.agent_type,
                status=AgentTaskStatus(db_task.status),
                progress=db_task.progress,
                message=db_task.message or "",
                input_data=json.loads(db_task.input_data) if db_task.input_data else {},
                result=json.loads(db_task.result) if db_task.result else None,
                source=ContentSource(db_task.source) if db_task.source else ContentSource.USER,
                error=db_task.error,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at,
                completed_at=db_task.completed_at
            )
            
            self._cache[task_id] = task
            return task
            
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            return None
    
    async def list_tasks(
        self,
        status: AgentTaskStatus = None,
        agent_type: str = None,
        limit: int = 100
    ) -> List[AgentTask]:
        """列出任务"""
        if self._db is None:
            # 从缓存返回
            tasks = list(self._cache.values())
            if status:
                tasks = [t for t in tasks if t.status == status]
            if agent_type:
                tasks = [t for t in tasks if t.agent_type == agent_type]
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return tasks[:limit]
        
        try:
            from models.agent_task import AgentTaskModel
            
            query = self._db.query(AgentTaskModel)
            
            if status:
                query = query.filter(AgentTaskModel.status == status.value)
            if agent_type:
                query = query.filter(AgentTaskModel.agent_type == agent_type)
            
            query = query.order_by(AgentTaskModel.created_at.desc()).limit(limit)
            
            tasks = []
            for db_task in query.all():
                task = AgentTask(
                    task_id=db_task.task_id,
                    task_type=db_task.task_type,
                    agent_type=db_task.agent_type,
                    status=AgentTaskStatus(db_task.status),
                    progress=db_task.progress,
                    message=db_task.message or "",
                    input_data=json.loads(db_task.input_data) if db_task.input_data else {},
                    result=json.loads(db_task.result) if db_task.result else None,
                    source=ContentSource(db_task.source) if db_task.source else ContentSource.USER,
                    error=db_task.error,
                    created_at=db_task.created_at,
                    updated_at=db_task.updated_at,
                    completed_at=db_task.completed_at
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return list(self._cache.values())[:limit]


# ============================================================
# 增强版 Agent 服务
# ============================================================

class EnhancedAgentService(AgentService):
    """
    增强版 Agent 服务
    
    新增功能：
    1. LLM 调用重试机制
    2. 任务超时处理
    3. Agent 状态持久化
    4. 任务恢复
    """
    
    def __init__(
        self,
        db_session=None,
        retry_config: RetryConfig = None,
        timeout_config: TimeoutConfig = None
    ):
        super().__init__()
        self._persistence = TaskPersistence(db_session)
        self._retry_config = retry_config or RetryConfig()
        self._timeout_config = timeout_config or TimeoutConfig()
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(
        self,
        task_type: str,
        agent_type: str,
        input_data: Dict[str, Any] = None
    ) -> AgentTask:
        """创建任务并持久化"""
        task = super().create_task(task_type, agent_type, input_data)
        
        # 异步保存
        asyncio.create_task(self._persistence.save_task(task))
        
        return task
    
    def update_task(
        self,
        task_id: str,
        status: AgentTaskStatus = None,
        progress: float = None,
        message: str = None,
        result: Any = None,
        error: str = None
    ):
        """更新任务状态并持久化"""
        super().update_task(task_id, status, progress, message, result, error)
        
        task = self._tasks.get(task_id)
        if task:
            asyncio.create_task(self._persistence.save_task(task))
    
    async def execute_task(
        self,
        task_type: str,
        agent_type: str,
        input_data: Dict[str, Any],
        skip_review: bool = False,
        timeout: float = None
    ) -> AgentTask:
        """
        执行 Agent 任务（带超时和重试）
        """
        # 创建任务
        task = self.create_task(task_type, agent_type, input_data)
        
        # 设置超时
        task_timeout = timeout or self._timeout_config.task_timeout
        
        try:
            # 使用超时包装
            async_task = asyncio.create_task(
                self._execute_with_retry(task, skip_review)
            )
            self._running_tasks[task.task_id] = async_task
            
            try:
                await asyncio.wait_for(async_task, timeout=task_timeout)
            except asyncio.TimeoutError:
                logger.error(f"任务 {task.task_id} 超时 ({task_timeout}s)")
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.FAILED,
                    error=f"任务超时 ({task_timeout}s)"
                )
            finally:
                self._running_tasks.pop(task.task_id, None)
                
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.FAILED,
                error=str(e)
            )
        
        return task
    
    async def _execute_with_retry(
        self,
        task: AgentTask,
        skip_review: bool
    ):
        """带重试的任务执行"""
        try:
            # 更新状态：工作中
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.WORKING,
                progress=0.1,
                message=f"{task.agent_type} 正在工作..."
            )
            
            # 执行任务（带重试）
            result = await self._execute_agent_task_with_retry(task)
            
            if result is None:
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.FAILED,
                    error="Agent 执行返回空结果"
                )
                return
            
            task.result = result
            task.source = self._get_content_source(task.agent_type)
            
            # Director_Agent 审核（带超时）
            if not skip_review:
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.REVIEWING,
                    progress=0.7,
                    message="Director_Agent 审核中..."
                )
                
                try:
                    review_result = await asyncio.wait_for(
                        self._review_result_with_retry(task),
                        timeout=self._timeout_config.review_timeout
                    )
                    task.review_result = review_result
                except asyncio.TimeoutError:
                    logger.warning(f"审核超时，自动通过")
                    task.review_result = {"status": "approved", "reason": "审核超时，自动通过"}
            
            # 完成
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.COMPLETED,
                progress=1.0,
                message="任务完成",
                result=result
            )
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self.update_task(
                task.task_id,
                status=AgentTaskStatus.FAILED,
                error=str(e)
            )
    
    async def _execute_agent_task_with_retry(self, task: AgentTask) -> Optional[Any]:
        """带重试的 Agent 任务执行"""
        config = self._retry_config
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                # 使用超时包装 LLM 调用
                result = await asyncio.wait_for(
                    self._execute_agent_task(task),
                    timeout=self._timeout_config.llm_call_timeout
                )
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"LLM 调用超时 (尝试 {attempt + 1}/{config.max_retries + 1})")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}")
            
            if attempt < config.max_retries:
                # 计算延迟
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                
                # 添加抖动
                if config.jitter:
                    import random
                    jitter = delay * 0.25 * (random.random() * 2 - 1)
                    delay += jitter
                
                # 更新进度消息
                self.update_task(
                    task.task_id,
                    message=f"重试中 ({attempt + 1}/{config.max_retries})..."
                )
                
                await asyncio.sleep(delay)
        
        logger.error(f"LLM 调用最终失败: {last_exception}")
        return None
    
    async def _review_result_with_retry(self, task: AgentTask) -> Dict[str, Any]:
        """带重试的审核"""
        config = self._retry_config
        
        for attempt in range(config.max_retries + 1):
            try:
                return await self._review_result(task)
            except Exception as e:
                logger.warning(f"审核失败 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}")
                
                if attempt < config.max_retries:
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    await asyncio.sleep(delay)
        
        return {"status": "approved", "reason": "审核重试失败，自动通过"}
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 取消运行中的异步任务
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            self._running_tasks.pop(task_id, None)
        
        return super().cancel_task(task_id)
    
    async def recover_tasks(self):
        """恢复未完成的任务"""
        try:
            # 加载未完成的任务
            pending_tasks = await self._persistence.list_tasks(
                status=AgentTaskStatus.WORKING
            )
            
            for task in pending_tasks:
                logger.info(f"恢复任务: {task.task_id}")
                
                # 标记为失败（需要重新执行）
                self.update_task(
                    task.task_id,
                    status=AgentTaskStatus.FAILED,
                    error="服务重启，任务中断"
                )
            
            logger.info(f"恢复了 {len(pending_tasks)} 个任务")
            
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
    
    async def get_task_from_db(self, task_id: str) -> Optional[AgentTask]:
        """从数据库获取任务"""
        return await self._persistence.load_task(task_id)
    
    async def list_tasks_from_db(
        self,
        status: AgentTaskStatus = None,
        agent_type: str = None,
        limit: int = 100
    ) -> List[AgentTask]:
        """从数据库列出任务"""
        return await self._persistence.list_tasks(status, agent_type, limit)


# ============================================================
# 全局实例
# ============================================================

_enhanced_agent_service: Optional[EnhancedAgentService] = None


def get_enhanced_agent_service(db_session=None) -> EnhancedAgentService:
    """获取增强版 Agent 服务实例"""
    global _enhanced_agent_service
    
    if _enhanced_agent_service is None:
        _enhanced_agent_service = EnhancedAgentService(db_session)
    
    return _enhanced_agent_service


def create_agent_service_with_config(
    db_session=None,
    max_retries: int = 3,
    llm_timeout: float = 30.0,
    task_timeout: float = 120.0
) -> EnhancedAgentService:
    """创建带配置的 Agent 服务"""
    return EnhancedAgentService(
        db_session=db_session,
        retry_config=RetryConfig(max_retries=max_retries),
        timeout_config=TimeoutConfig(
            llm_call_timeout=llm_timeout,
            task_timeout=task_timeout
        )
    )
