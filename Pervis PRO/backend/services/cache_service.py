"""
Redis缓存服务
用于缓存频繁查询的数据，提升API响应性能
"""

import json
import logging
from typing import Optional, Any, Dict, List
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Mock Redis实现 - 用于开发环境
class MockRedis:
    """Mock Redis实现，用于没有Redis服务器的环境"""
    
    def __init__(self):
        self._data: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            if key in self._data:
                item = self._data[key]
                # 检查过期时间
                if item.get('expires_at') and datetime.now() > item['expires_at']:
                    del self._data[key]
                    return None
                return item['value'].encode() if isinstance(item['value'], str) else item['value']
            return None
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        async with self._lock:
            expires_at = None
            if ex:
                expires_at = datetime.now() + timedelta(seconds=ex)
            
            self._data[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            return True
    
    async def delete(self, key: str) -> int:
        async with self._lock:
            if key in self._data:
                del self._data[key]
                return 1
            return 0
    
    async def exists(self, key: str) -> int:
        async with self._lock:
            return 1 if key in self._data else 0
    
    async def flushall(self) -> bool:
        async with self._lock:
            self._data.clear()
            return True
    
    async def keys(self, pattern: str = "*") -> List[str]:
        async with self._lock:
            if pattern == "*":
                return list(self._data.keys())
            # 简单的模式匹配
            import fnmatch
            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]

class CacheService:
    """缓存服务类"""
    
    def __init__(self, redis_url: str = None, use_mock: bool = False):
        self.redis_url = redis_url
        self.use_mock = use_mock
        self.redis = None
        self._initialized = False
        
        # 缓存统计
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """初始化Redis连接"""
        if self._initialized:
            return
        
        try:
            if self.use_mock or not self.redis_url:
                logger.info("使用Mock Redis缓存")
                self.redis = MockRedis()
            else:
                try:
                    import aioredis
                    self.redis = aioredis.from_url(self.redis_url, decode_responses=False)
                    # 测试连接
                    await self.redis.ping()
                    logger.info(f"Redis缓存已连接: {self.redis_url}")
                except ImportError:
                    logger.warning("aioredis未安装，使用Mock Redis")
                    self.redis = MockRedis()
                except Exception as e:
                    logger.warning(f"Redis连接失败，使用Mock Redis: {e}")
                    self.redis = MockRedis()
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"缓存服务初始化失败: {e}")
            self.redis = MockRedis()
            self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._initialized:
            await self.initialize()
        
        try:
            value = await self.redis.get(key)
            if value:
                self.stats['hits'] += 1
                # 尝试JSON解码
                try:
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    return json.loads(value)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return value
            else:
                self.stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """设置缓存值"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # JSON序列化
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            
            result = await self.redis.set(key, value, ex=expire)
            if result:
                self.stats['sets'] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.redis.delete(key)
            if result:
                self.stats['deletes'] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.redis.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"缓存检查失败 {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self._initialized:
            await self.initialize()
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = 0
                for key in keys:
                    if await self.delete(key):
                        deleted += 1
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"缓存模式清除失败 {pattern}: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'initialized': self._initialized,
            'redis_type': 'mock' if isinstance(self.redis, MockRedis) else 'real'
        }
    
    # 便捷方法
    async def cache_project(self, project_id: str, project_data: Dict, expire: int = 600):
        """缓存项目数据"""
        return await self.set(f"project:{project_id}", project_data, expire)
    
    async def get_project(self, project_id: str) -> Optional[Dict]:
        """获取项目缓存"""
        return await self.get(f"project:{project_id}")
    
    async def cache_search_result(self, query_hash: str, results: List, expire: int = 300):
        """缓存搜索结果"""
        return await self.set(f"search:{query_hash}", results, expire)
    
    async def get_search_result(self, query_hash: str) -> Optional[List]:
        """获取搜索结果缓存"""
        return await self.get(f"search:{query_hash}")
    
    async def cache_asset_analysis(self, asset_id: str, analysis_data: Dict, expire: int = 3600):
        """缓存资产分析结果"""
        return await self.set(f"analysis:{asset_id}", analysis_data, expire)
    
    async def get_asset_analysis(self, asset_id: str) -> Optional[Dict]:
        """获取资产分析缓存"""
        return await self.get(f"analysis:{asset_id}")
    
    async def invalidate_project_cache(self, project_id: str):
        """清除项目相关缓存"""
        await self.clear_pattern(f"project:{project_id}*")
        await self.clear_pattern(f"search:*{project_id}*")

# 全局缓存服务实例
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """获取全局缓存服务实例"""
    global _cache_service
    
    if _cache_service is None:
        try:
            from app.config import settings
            redis_url = settings.redis_url
        except ImportError:
            redis_url = None
        
        # 在开发环境中使用Mock Redis
        use_mock = redis_url is None or "localhost" in str(redis_url)
        _cache_service = CacheService(redis_url, use_mock=use_mock)
    
    return _cache_service

async def init_cache_service():
    """初始化缓存服务"""
    cache = get_cache_service()
    await cache.initialize()
    logger.info("缓存服务已初始化")

# 缓存装饰器
def cache_result(key_template: str, expire: int = 300):
    """缓存结果装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # 生成缓存键
            try:
                cache_key = key_template.format(*args, **kwargs)
            except (IndexError, KeyError):
                # 如果格式化失败，直接执行函数
                return await func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator