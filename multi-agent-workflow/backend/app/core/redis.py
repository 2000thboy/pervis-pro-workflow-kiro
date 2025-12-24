"""
Redis连接和管理
"""
import aioredis
import logging
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await self.redis.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已关闭")
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self.redis:
            raise RuntimeError("Redis未连接")
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """设置值"""
        if not self.redis:
            raise RuntimeError("Redis未连接")
        await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """删除键"""
        if not self.redis:
            raise RuntimeError("Redis未连接")
        await self.redis.delete(key)
    
    async def publish(self, channel: str, message: str):
        """发布消息"""
        if not self.redis:
            raise RuntimeError("Redis未连接")
        await self.redis.publish(channel, message)
    
    async def subscribe(self, channel: str):
        """订阅频道"""
        if not self.redis:
            raise RuntimeError("Redis未连接")
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# 全局Redis管理器实例
redis_manager = RedisManager()