# -*- coding: utf-8 -*-
"""
性能优化模块

提供系统性能优化功能：
- 缓存策略
- 响应时间优化
- 资源使用监控
- 数据库查询优化

Feature: multi-agent-workflow-core
Requirements: 1.5, 7.2
"""
import asyncio
import functools
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    TTL = "ttl"           # 基于时间过期
    LRU_TTL = "lru_ttl"   # 组合策略


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    key: str
    value: T
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def touch(self):
        """更新访问时间"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


class LRUCache(Generic[T]):
    """
    LRU缓存实现
    
    支持：
    - 最大容量限制
    - TTL过期
    - 访问统计
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None
    ):
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            
            # 更新访问信息并移到末尾（最近使用）
            entry.touch()
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            
            return entry.value
    
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None
    ):
        """设置缓存值"""
        async with self._lock:
            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 检查容量，必要时淘汰
            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl or self._default_ttl
            )
            self._cache[key] = entry
    
    async def delete(self, key: str) -> bool:
        """删除缓存条目"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """清理过期条目"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": hit_rate
        }
    
    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self._cache)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)


class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    - 响应时间追踪
    - 资源使用监控
    - 性能指标收集
    """
    
    def __init__(self, max_metrics: int = 10000):
        self._metrics: List[PerformanceMetric] = []
        self._max_metrics = max_metrics
        self._timers: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    def start_timer(self, name: str) -> str:
        """开始计时"""
        timer_id = f"{name}_{time.time()}"
        self._timers[timer_id] = time.perf_counter()
        return timer_id
    
    async def stop_timer(self, timer_id: str, tags: Optional[Dict[str, str]] = None) -> float:
        """停止计时并记录"""
        if timer_id not in self._timers:
            return 0.0
        
        start_time = self._timers.pop(timer_id)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # 提取名称
        name = timer_id.rsplit('_', 1)[0]
        
        await self.record_metric(
            name=f"{name}_duration",
            value=elapsed_ms,
            unit="ms",
            tags=tags or {}
        )
        
        return elapsed_ms
    
    async def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        tags: Optional[Dict[str, str]] = None
    ):
        """记录性能指标"""
        async with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                tags=tags or {}
            )
            self._metrics.append(metric)
            
            # 限制指标数量
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PerformanceMetric]:
        """获取性能指标"""
        metrics = self._metrics
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics[-limit:]
    
    def get_statistics(self, name: str) -> Dict[str, float]:
        """获取指定指标的统计信息"""
        metrics = [m for m in self._metrics if m.name == name]
        
        if not metrics:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }
        
        values = sorted([m.value for m in metrics])
        count = len(values)
        
        return {
            "count": count,
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / count,
            "p50": values[int(count * 0.5)],
            "p95": values[int(count * 0.95)] if count >= 20 else values[-1],
            "p99": values[int(count * 0.99)] if count >= 100 else values[-1]
        }
    
    async def clear(self):
        """清空指标"""
        async with self._lock:
            self._metrics.clear()
            self._timers.clear()


def cached(
    cache: LRUCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[float] = None
):
    """
    缓存装饰器
    
    Args:
        cache: 缓存实例
        key_func: 生成缓存键的函数
        ttl: 缓存过期时间
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def timed(monitor: PerformanceMonitor, name: Optional[str] = None):
    """
    计时装饰器
    
    Args:
        monitor: 性能监控器实例
        name: 指标名称（默认使用函数名）
    """
    def decorator(func: Callable):
        metric_name = name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            timer_id = monitor.start_timer(metric_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                await monitor.stop_timer(timer_id)
        
        return wrapper
    return decorator


class QueryOptimizer:
    """
    查询优化器
    
    提供数据库查询优化建议和批量查询支持
    """
    
    def __init__(self):
        self._query_stats: Dict[str, List[float]] = {}
        self._batch_queue: Dict[str, List[Tuple[Any, asyncio.Future]]] = {}
        self._batch_size = 50
        self._batch_delay = 0.01  # 10ms
    
    async def record_query(self, query_name: str, duration_ms: float):
        """记录查询执行时间"""
        if query_name not in self._query_stats:
            self._query_stats[query_name] = []
        
        self._query_stats[query_name].append(duration_ms)
        
        # 限制记录数量
        if len(self._query_stats[query_name]) > 1000:
            self._query_stats[query_name] = self._query_stats[query_name][-1000:]
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """获取慢查询"""
        slow_queries = []
        
        for query_name, durations in self._query_stats.items():
            avg_duration = sum(durations) / len(durations)
            if avg_duration > threshold_ms:
                slow_queries.append({
                    "query": query_name,
                    "avg_duration_ms": avg_duration,
                    "max_duration_ms": max(durations),
                    "count": len(durations)
                })
        
        return sorted(slow_queries, key=lambda x: x["avg_duration_ms"], reverse=True)
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        slow_queries = self.get_slow_queries()
        for sq in slow_queries[:5]:  # 前5个最慢的查询
            suggestions.append(
                f"查询 '{sq['query']}' 平均耗时 {sq['avg_duration_ms']:.2f}ms，"
                f"建议添加索引或优化查询逻辑"
            )
        
        return suggestions


class ResourceMonitor:
    """
    资源监控器
    
    监控系统资源使用情况
    """
    
    def __init__(self):
        self._samples: List[Dict[str, Any]] = []
        self._max_samples = 1000
    
    async def sample(self) -> Dict[str, Any]:
        """采样当前资源使用"""
        import sys
        
        sample = {
            "timestamp": datetime.utcnow().isoformat(),
            "memory_mb": sys.getsizeof(self._samples) / (1024 * 1024),
            "active_tasks": len(asyncio.all_tasks())
        }
        
        self._samples.append(sample)
        
        # 限制样本数量
        if len(self._samples) > self._max_samples:
            self._samples = self._samples[-self._max_samples:]
        
        return sample
    
    def get_samples(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取资源样本"""
        return self._samples[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取资源使用摘要"""
        if not self._samples:
            return {"error": "无采样数据"}
        
        memory_values = [s.get("memory_mb", 0) for s in self._samples]
        task_values = [s.get("active_tasks", 0) for s in self._samples]
        
        return {
            "sample_count": len(self._samples),
            "memory_mb": {
                "current": memory_values[-1] if memory_values else 0,
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0
            },
            "active_tasks": {
                "current": task_values[-1] if task_values else 0,
                "avg": sum(task_values) / len(task_values) if task_values else 0,
                "max": max(task_values) if task_values else 0
            }
        }


# 全局实例
_performance_monitor: Optional[PerformanceMonitor] = None
_agent_cache: Optional[LRUCache] = None
_project_cache: Optional[LRUCache] = None
_query_optimizer: Optional[QueryOptimizer] = None
_resource_monitor: Optional[ResourceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_agent_cache() -> LRUCache:
    """获取Agent缓存"""
    global _agent_cache
    if _agent_cache is None:
        _agent_cache = LRUCache(max_size=100, default_ttl=300)  # 5分钟TTL
    return _agent_cache


def get_project_cache() -> LRUCache:
    """获取项目缓存"""
    global _project_cache
    if _project_cache is None:
        _project_cache = LRUCache(max_size=500, default_ttl=600)  # 10分钟TTL
    return _project_cache


def get_query_optimizer() -> QueryOptimizer:
    """获取查询优化器"""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


def get_resource_monitor() -> ResourceMonitor:
    """获取资源监控器"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor
