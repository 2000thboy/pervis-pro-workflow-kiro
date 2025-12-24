"""
消息总线实现 - 支持发布/订阅模式的Agent间通信框架

需求: 1.2 - WHEN Agent间需要数据交换时 THEN 系统 SHALL 通过统一的消息总线进行通信
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    BROADCAST = "broadcast"      # 广播消息
    DIRECT = "direct"            # 点对点消息
    REQUEST = "request"          # 请求消息
    RESPONSE = "response"        # 响应消息
    EVENT = "event"              # 事件通知
    COMMAND = "command"          # 命令消息


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """消息数据类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.EVENT
    source: str = ""
    target: Optional[str] = None
    topic: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "target": self.target,
            "topic": self.topic,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MessageType(data.get("type", "event")),
            source=data.get("source", ""),
            target=data.get("target"),
            topic=data.get("topic", ""),
            content=data.get("content", {}),
            priority=MessagePriority(data.get("priority", 2)),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to")
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """从JSON字符串创建消息"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Response:
    """响应数据类"""
    success: bool
    message_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message_id": self.message_id,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp
        }


class Subscription:
    """订阅信息类"""
    
    def __init__(
        self,
        subscriber_id: str,
        topic: str,
        handler: Callable,
        filter_func: Optional[Callable[[Message], bool]] = None
    ):
        self.id = str(uuid.uuid4())
        self.subscriber_id = subscriber_id
        self.topic = topic
        self.handler = handler
        self.filter_func = filter_func
        self.created_at = datetime.utcnow()
        self.message_count = 0
    
    async def handle(self, message: Message) -> bool:
        """处理消息"""
        # 应用过滤器
        if self.filter_func and not self.filter_func(message):
            return False
        
        try:
            # 调用处理函数
            if asyncio.iscoroutinefunction(self.handler):
                await self.handler(message)
            else:
                self.handler(message)
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"订阅处理错误 [{self.subscriber_id}]: {e}")
            return False


class MessageBus:
    """
    消息总线类 - 实现Agent间的发布/订阅通信模式
    
    功能:
    - 发布/订阅模式消息传递
    - 消息路由和分发
    - 请求-响应模式通信
    - 消息优先级处理
    - 消息历史记录
    """
    
    def __init__(self, max_history: int = 1000):
        # 主题订阅映射: topic -> List[Subscription]
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        # Agent订阅映射: agent_id -> Set[subscription_id]
        self._agent_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        # 待处理的请求-响应: correlation_id -> Future
        self._pending_requests: Dict[str, asyncio.Future] = {}
        # 消息历史
        self._message_history: List[Message] = []
        self._max_history = max_history
        # 统计信息
        self._stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "active_subscriptions": 0
        }
        # 锁
        self._lock = asyncio.Lock()
        # 运行状态
        self._running = False
        
        logger.info("消息总线初始化完成")
    
    async def start(self):
        """启动消息总线"""
        self._running = True
        logger.info("消息总线已启动")
    
    async def stop(self):
        """停止消息总线"""
        self._running = False
        # 取消所有待处理的请求
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        logger.info("消息总线已停止")
    
    async def subscribe(
        self,
        subscriber_id: str,
        topic: str,
        handler: Callable,
        filter_func: Optional[Callable[[Message], bool]] = None
    ) -> str:
        """
        订阅主题
        
        Args:
            subscriber_id: 订阅者ID (通常是Agent ID)
            topic: 主题名称
            handler: 消息处理函数
            filter_func: 可选的消息过滤函数
            
        Returns:
            订阅ID
        """
        async with self._lock:
            subscription = Subscription(subscriber_id, topic, handler, filter_func)
            self._subscriptions[topic].append(subscription)
            self._agent_subscriptions[subscriber_id].add(subscription.id)
            self._stats["active_subscriptions"] += 1
            
            logger.debug(f"新订阅: {subscriber_id} -> {topic} (ID: {subscription.id})")
            return subscription.id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            是否成功取消
        """
        async with self._lock:
            for topic, subs in self._subscriptions.items():
                for sub in subs:
                    if sub.id == subscription_id:
                        subs.remove(sub)
                        self._agent_subscriptions[sub.subscriber_id].discard(subscription_id)
                        self._stats["active_subscriptions"] -= 1
                        logger.debug(f"取消订阅: {subscription_id}")
                        return True
            return False
    
    async def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        取消指定订阅者的所有订阅
        
        Args:
            subscriber_id: 订阅者ID
            
        Returns:
            取消的订阅数量
        """
        async with self._lock:
            subscription_ids = self._agent_subscriptions.get(subscriber_id, set()).copy()
            count = 0
            
            for topic, subs in self._subscriptions.items():
                original_len = len(subs)
                self._subscriptions[topic] = [
                    s for s in subs if s.subscriber_id != subscriber_id
                ]
                count += original_len - len(self._subscriptions[topic])
            
            self._agent_subscriptions.pop(subscriber_id, None)
            self._stats["active_subscriptions"] -= count
            
            logger.debug(f"取消所有订阅: {subscriber_id}, 数量: {count}")
            return count

    
    async def publish(self, topic: str, message: Message) -> int:
        """
        发布消息到指定主题
        
        Args:
            topic: 主题名称
            message: 消息对象
            
        Returns:
            成功投递的订阅者数量
        """
        if not self._running:
            logger.warning("消息总线未运行，无法发布消息")
            return 0
        
        message.topic = topic
        delivered_count = 0
        
        # 记录消息历史
        await self._add_to_history(message)
        self._stats["messages_published"] += 1
        
        # 获取该主题的所有订阅
        subscriptions = self._subscriptions.get(topic, [])
        
        # 按优先级排序处理
        sorted_subs = sorted(
            subscriptions,
            key=lambda s: s.message_count  # 负载均衡
        )
        
        # 分发消息
        for subscription in sorted_subs:
            try:
                success = await subscription.handle(message)
                if success:
                    delivered_count += 1
                    self._stats["messages_delivered"] += 1
                else:
                    self._stats["messages_failed"] += 1
            except Exception as e:
                logger.error(f"消息分发错误: {e}")
                self._stats["messages_failed"] += 1
        
        logger.debug(f"消息发布: {topic}, 投递: {delivered_count}/{len(subscriptions)}")
        return delivered_count
    
    async def broadcast(self, message: Message) -> int:
        """
        广播消息到所有订阅者
        
        Args:
            message: 消息对象
            
        Returns:
            成功投递的订阅者数量
        """
        message.type = MessageType.BROADCAST
        total_delivered = 0
        
        # 向所有主题发布
        for topic in self._subscriptions.keys():
            delivered = await self.publish(topic, message)
            total_delivered += delivered
        
        return total_delivered
    
    async def send_direct(self, target_id: str, message: Message) -> bool:
        """
        发送点对点消息
        
        Args:
            target_id: 目标Agent ID
            message: 消息对象
            
        Returns:
            是否成功发送
        """
        message.type = MessageType.DIRECT
        message.target = target_id
        
        # 查找目标Agent的订阅
        target_subs = self._agent_subscriptions.get(target_id, set())
        if not target_subs:
            logger.warning(f"目标Agent未找到: {target_id}")
            return False
        
        # 发送到目标Agent订阅的所有主题
        delivered = False
        for topic, subs in self._subscriptions.items():
            for sub in subs:
                if sub.subscriber_id == target_id:
                    try:
                        success = await sub.handle(message)
                        if success:
                            delivered = True
                            self._stats["messages_delivered"] += 1
                    except Exception as e:
                        logger.error(f"点对点消息发送错误: {e}")
        
        return delivered
    
    async def request_response(
        self,
        target_id: str,
        message: Message,
        timeout: float = 30.0
    ) -> Response:
        """
        请求-响应模式通信
        
        Args:
            target_id: 目标Agent ID
            message: 请求消息
            timeout: 超时时间(秒)
            
        Returns:
            响应对象
        """
        # 设置消息类型和关联ID
        message.type = MessageType.REQUEST
        message.target = target_id
        correlation_id = message.id
        message.correlation_id = correlation_id
        
        # 创建Future等待响应
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_requests[correlation_id] = future
        
        try:
            # 发送请求
            success = await self.send_direct(target_id, message)
            if not success:
                return Response(
                    success=False,
                    message_id=message.id,
                    error=f"无法发送请求到 {target_id}"
                )
            
            # 等待响应
            response_data = await asyncio.wait_for(future, timeout=timeout)
            return Response(
                success=True,
                message_id=message.id,
                data=response_data
            )
        except asyncio.TimeoutError:
            return Response(
                success=False,
                message_id=message.id,
                error=f"请求超时 ({timeout}秒)"
            )
        except Exception as e:
            return Response(
                success=False,
                message_id=message.id,
                error=str(e)
            )
        finally:
            self._pending_requests.pop(correlation_id, None)
    
    async def send_response(self, correlation_id: str, data: Dict[str, Any]) -> bool:
        """
        发送响应消息
        
        Args:
            correlation_id: 关联ID
            data: 响应数据
            
        Returns:
            是否成功发送
        """
        future = self._pending_requests.get(correlation_id)
        if future and not future.done():
            future.set_result(data)
            return True
        return False
    
    async def _add_to_history(self, message: Message):
        """添加消息到历史记录"""
        self._message_history.append(message)
        # 限制历史记录大小
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
    
    def get_history(
        self,
        topic: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        获取消息历史
        
        Args:
            topic: 过滤主题
            source: 过滤来源
            limit: 返回数量限制
            
        Returns:
            消息列表
        """
        messages = self._message_history
        
        if topic:
            messages = [m for m in messages if m.topic == topic]
        if source:
            messages = [m for m in messages if m.source == source]
        
        return messages[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "topics": list(self._subscriptions.keys()),
            "history_size": len(self._message_history)
        }
    
    def get_subscribers(self, topic: str) -> List[str]:
        """获取主题的所有订阅者"""
        return [sub.subscriber_id for sub in self._subscriptions.get(topic, [])]
    
    def get_topics(self) -> List[str]:
        """获取所有主题"""
        return list(self._subscriptions.keys())
    
    @property
    def is_running(self) -> bool:
        """检查消息总线是否运行中"""
        return self._running


# 全局消息总线实例
message_bus = MessageBus()
