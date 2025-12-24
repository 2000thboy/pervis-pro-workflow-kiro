"""
BackendAgent - 后端监控Agent

需求: 5.1 - WHEN 任何Agent出现异常时 THEN 后端Agent SHALL 检测并记录错误信息
需求: 5.2 - WHEN 系统检测到API接口问题时 THEN 后端Agent SHALL 生成报错日志

本模块实现后端Agent，负责:
- API监控
- 错误检测和记录
- 系统状态监控
- 健康检查
"""
import asyncio
import logging
from datetime import datetime, timedelta
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


class ErrorSeverity(Enum):
    """错误严重程度"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""
    AGENT_ERROR = "agent_error"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MonitoringTarget(Enum):
    """监控目标"""
    API_ENDPOINT = "api_endpoint"
    AGENT = "agent"
    DATABASE = "database"
    MESSAGE_BUS = "message_bus"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class ErrorRecord:
    """错误记录"""
    id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    source: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "stack_trace": self.stack_trace,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolution_notes": self.resolution_notes
        }


@dataclass
class APIEndpoint:
    """API端点信息"""
    id: str
    path: str
    method: str
    description: str
    is_monitored: bool = True
    last_check: Optional[str] = None
    last_status: Optional[int] = None
    last_response_time_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "method": self.method,
            "description": self.description,
            "is_monitored": self.is_monitored,
            "last_check": self.last_check,
            "last_status": self.last_status,
            "last_response_time_ms": self.last_response_time_ms,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at
        }
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.error_count + self.success_count
        if total == 0:
            return 1.0
        return self.success_count / total


@dataclass
class HealthCheck:
    """健康检查结果"""
    target: str
    target_type: MonitoringTarget
    status: HealthStatus
    timestamp: str
    response_time_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "target_type": self.target_type.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "error": self.error
        }


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: str
    active_agents: int
    total_messages: int
    error_count_1h: int
    avg_response_time_ms: float
    api_success_rate: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "active_agents": self.active_agents,
            "total_messages": self.total_messages,
            "error_count_1h": self.error_count_1h,
            "avg_response_time_ms": self.avg_response_time_ms,
            "api_success_rate": self.api_success_rate,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent
        }



class BackendAgent(BaseAgent):
    """
    后端Agent - 系统监控和错误处理
    
    需求: 5.1 - WHEN 任何Agent出现异常时 THEN 后端Agent SHALL 检测并记录错误信息
    需求: 5.2 - WHEN 系统检测到API接口问题时 THEN 后端Agent SHALL 生成报错日志
    
    功能:
    - 错误检测: 检测和记录系统中的各类错误
    - API监控: 监控API端点的健康状态和性能
    - 系统监控: 监控整体系统状态
    - 健康检查: 执行定期健康检查
    """
    
    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化后端Agent
        
        Args:
            agent_id: Agent唯一标识符
            message_bus: 消息总线实例
            config: Agent配置
        """
        capabilities = [
            "error_detection",
            "api_monitoring",
            "system_monitoring",
            "health_check",
            "log_management"
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.BACKEND,
            message_bus=message_bus,
            capabilities=capabilities,
            config=config
        )
        
        # 错误记录
        self._errors: Dict[str, ErrorRecord] = {}
        # API端点
        self._endpoints: Dict[str, APIEndpoint] = {}
        # 健康检查结果
        self._health_checks: Dict[str, HealthCheck] = {}
        # 系统指标历史
        self._metrics_history: List[SystemMetrics] = []
        
        # 错误计数器
        self._error_counter = 0
        # 消息计数器
        self._message_counter = 0
        # 响应时间累计
        self._total_response_time = 0.0
        self._response_count = 0
        
        # 配置
        self._max_errors = config.get("max_errors", 1000) if config else 1000
        self._max_metrics_history = config.get("max_metrics_history", 100) if config else 100
        self._error_retention_hours = config.get("error_retention_hours", 24) if config else 24
        
        # 错误处理回调
        self._error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        
        logger.info(f"BackendAgent初始化: {agent_id}")
    
    # ========================================================================
    # 错误检测和记录
    # ========================================================================
    
    async def record_error(
        self,
        error_id: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> ErrorRecord:
        """
        记录错误
        
        需求: 5.1 - WHEN 任何Agent出现异常时 THEN 后端Agent SHALL 检测并记录错误信息
        
        Args:
            error_id: 错误ID
            severity: 严重程度
            category: 错误类别
            source: 错误来源
            message: 错误消息
            details: 详细信息
            stack_trace: 堆栈跟踪
            
        Returns:
            创建的错误记录
        """
        error = ErrorRecord(
            id=error_id,
            timestamp=datetime.utcnow().isoformat(),
            severity=severity,
            category=category,
            source=source,
            message=message,
            details=details or {},
            stack_trace=stack_trace
        )
        
        self._errors[error_id] = error
        self._error_counter += 1
        
        # 限制错误记录数量
        if len(self._errors) > self._max_errors:
            self._cleanup_old_errors()
        
        # 触发错误处理回调
        await self._trigger_error_handlers(error)
        
        self._log_operation(
            "error_recorded",
            details={
                "error_id": error_id,
                "severity": severity.value,
                "category": category.value,
                "source": source
            }
        )
        
        # 根据严重程度记录日志
        log_message = f"[{source}] {message}"
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return error
    
    async def record_agent_error(
        self,
        agent_id: str,
        error_message: str,
        error_type: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> ErrorRecord:
        """
        记录Agent错误
        
        需求: 5.1 - WHEN 任何Agent出现异常时 THEN 后端Agent SHALL 检测并记录错误信息
        
        Args:
            agent_id: Agent ID
            error_message: 错误消息
            error_type: 错误类型
            details: 详细信息
            stack_trace: 堆栈跟踪
            
        Returns:
            创建的错误记录
        """
        error_id = f"agent_error_{agent_id}_{self._error_counter}"
        
        return await self.record_error(
            error_id=error_id,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AGENT_ERROR,
            source=f"agent:{agent_id}",
            message=error_message,
            details={
                "agent_id": agent_id,
                "error_type": error_type,
                **(details or {})
            },
            stack_trace=stack_trace
        )
    
    async def record_api_error(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        error_message: str,
        request_details: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """
        记录API错误
        
        需求: 5.2 - WHEN 系统检测到API接口问题时 THEN 后端Agent SHALL 生成报错日志
        
        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 状态码
            error_message: 错误消息
            request_details: 请求详情
            
        Returns:
            创建的错误记录
        """
        error_id = f"api_error_{self._error_counter}"
        
        # 确定严重程度
        if status_code >= 500:
            severity = ErrorSeverity.ERROR
        elif status_code >= 400:
            severity = ErrorSeverity.WARNING
        else:
            severity = ErrorSeverity.INFO
        
        # 更新端点错误计数
        endpoint_id = f"{method}:{endpoint}"
        if endpoint_id in self._endpoints:
            self._endpoints[endpoint_id].error_count += 1
        
        return await self.record_error(
            error_id=error_id,
            severity=severity,
            category=ErrorCategory.API_ERROR,
            source=f"api:{endpoint}",
            message=error_message,
            details={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "request": request_details or {}
            }
        )
    
    async def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        """获取错误记录"""
        return self._errors.get(error_id)
    
    async def list_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        source_filter: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 50
    ) -> List[ErrorRecord]:
        """
        列出错误记录
        
        Args:
            severity: 按严重程度过滤
            category: 按类别过滤
            source_filter: 按来源过滤
            unresolved_only: 只显示未解决的
            limit: 返回数量限制
            
        Returns:
            错误记录列表
        """
        errors = list(self._errors.values())
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        if source_filter:
            errors = [e for e in errors if source_filter in e.source]
        
        if unresolved_only:
            errors = [e for e in errors if not e.resolved]
        
        # 按时间排序（最新的在前）
        errors.sort(key=lambda e: e.timestamp, reverse=True)
        
        return errors[:limit]
    
    async def resolve_error(
        self,
        error_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """
        标记错误为已解决
        
        Args:
            error_id: 错误ID
            resolution_notes: 解决说明
            
        Returns:
            是否成功
        """
        error = self._errors.get(error_id)
        if not error:
            return False
        
        error.resolved = True
        error.resolved_at = datetime.utcnow().isoformat()
        error.resolution_notes = resolution_notes
        
        self._log_operation(
            "error_resolved",
            details={"error_id": error_id}
        )
        
        return True
    
    def _cleanup_old_errors(self):
        """清理旧错误记录"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self._error_retention_hours)
        cutoff_str = cutoff_time.isoformat()
        
        old_errors = [
            eid for eid, e in self._errors.items()
            if e.timestamp < cutoff_str and e.resolved
        ]
        
        for eid in old_errors:
            del self._errors[eid]
    
    def register_error_handler(
        self,
        category: ErrorCategory,
        handler: Callable[[ErrorRecord], None]
    ):
        """
        注册错误处理回调
        
        Args:
            category: 错误类别
            handler: 处理函数
        """
        if category not in self._error_handlers:
            self._error_handlers[category] = []
        self._error_handlers[category].append(handler)
    
    async def _trigger_error_handlers(self, error: ErrorRecord):
        """触发错误处理回调"""
        handlers = self._error_handlers.get(error.category, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                logger.error(f"错误处理回调执行失败: {e}")
    
    # ========================================================================
    # API监控
    # ========================================================================
    
    async def register_endpoint(
        self,
        endpoint_id: str,
        path: str,
        method: str,
        description: str = ""
    ) -> APIEndpoint:
        """
        注册API端点
        
        Args:
            endpoint_id: 端点ID
            path: 路径
            method: HTTP方法
            description: 描述
            
        Returns:
            创建的端点对象
        """
        endpoint = APIEndpoint(
            id=endpoint_id,
            path=path,
            method=method,
            description=description
        )
        
        self._endpoints[endpoint_id] = endpoint
        
        self._log_operation(
            "endpoint_registered",
            details={"endpoint_id": endpoint_id, "path": path, "method": method}
        )
        
        logger.info(f"注册API端点: {method} {path}")
        return endpoint
    
    async def record_api_call(
        self,
        endpoint_id: str,
        status_code: int,
        response_time_ms: float,
        success: bool = True
    ) -> bool:
        """
        记录API调用
        
        Args:
            endpoint_id: 端点ID
            status_code: 状态码
            response_time_ms: 响应时间(毫秒)
            success: 是否成功
            
        Returns:
            是否记录成功
        """
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return False
        
        endpoint.last_check = datetime.utcnow().isoformat()
        endpoint.last_status = status_code
        endpoint.last_response_time_ms = response_time_ms
        
        if success:
            endpoint.success_count += 1
        else:
            endpoint.error_count += 1
        
        # 更新全局响应时间统计
        self._total_response_time += response_time_ms
        self._response_count += 1
        self._message_counter += 1
        
        return True
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[APIEndpoint]:
        """获取端点信息"""
        return self._endpoints.get(endpoint_id)
    
    async def list_endpoints(
        self,
        monitored_only: bool = False,
        limit: int = 50
    ) -> List[APIEndpoint]:
        """
        列出端点
        
        Args:
            monitored_only: 只显示监控中的
            limit: 返回数量限制
            
        Returns:
            端点列表
        """
        endpoints = list(self._endpoints.values())
        
        if monitored_only:
            endpoints = [e for e in endpoints if e.is_monitored]
        
        return endpoints[:limit]
    
    async def get_endpoint_statistics(self, endpoint_id: str) -> Dict[str, Any]:
        """
        获取端点统计信息
        
        Args:
            endpoint_id: 端点ID
            
        Returns:
            统计信息
        """
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return {"error": f"端点不存在: {endpoint_id}"}
        
        return {
            "endpoint_id": endpoint_id,
            "path": endpoint.path,
            "method": endpoint.method,
            "total_calls": endpoint.success_count + endpoint.error_count,
            "success_count": endpoint.success_count,
            "error_count": endpoint.error_count,
            "success_rate": endpoint.success_rate,
            "last_response_time_ms": endpoint.last_response_time_ms,
            "last_status": endpoint.last_status,
            "last_check": endpoint.last_check
        }
    
    # ========================================================================
    # 健康检查
    # ========================================================================
    
    async def perform_health_check(
        self,
        target: str,
        target_type: MonitoringTarget,
        check_function: Optional[Callable] = None
    ) -> HealthCheck:
        """
        执行健康检查
        
        Args:
            target: 检查目标
            target_type: 目标类型
            check_function: 自定义检查函数
            
        Returns:
            健康检查结果
        """
        start_time = datetime.utcnow()
        status = HealthStatus.UNKNOWN
        error = None
        details = {}
        
        try:
            if check_function:
                if asyncio.iscoroutinefunction(check_function):
                    result = await check_function()
                else:
                    result = check_function()
                
                if isinstance(result, dict):
                    details = result
                    status = HealthStatus.HEALTHY if result.get("healthy", True) else HealthStatus.UNHEALTHY
                elif isinstance(result, bool):
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                else:
                    status = HealthStatus.HEALTHY
            else:
                # 默认检查逻辑
                status = HealthStatus.HEALTHY
                details = {"message": "默认检查通过"}
                
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error = str(e)
            logger.error(f"健康检查失败 [{target}]: {e}")
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        health_check = HealthCheck(
            target=target,
            target_type=target_type,
            status=status,
            timestamp=end_time.isoformat(),
            response_time_ms=response_time_ms,
            details=details,
            error=error
        )
        
        self._health_checks[target] = health_check
        
        self._log_operation(
            "health_check_performed",
            details={
                "target": target,
                "status": status.value,
                "response_time_ms": response_time_ms
            }
        )
        
        return health_check
    
    async def get_health_check(self, target: str) -> Optional[HealthCheck]:
        """获取健康检查结果"""
        return self._health_checks.get(target)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统整体健康状态
        
        Returns:
            系统健康状态
        """
        checks = list(self._health_checks.values())
        
        if not checks:
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "message": "没有健康检查数据",
                "checks": []
            }
        
        # 计算整体状态
        unhealthy_count = len([c for c in checks if c.status == HealthStatus.UNHEALTHY])
        degraded_count = len([c for c in checks if c.status == HealthStatus.DEGRADED])
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "overall_status": overall_status.value,
            "total_checks": len(checks),
            "healthy_count": len([c for c in checks if c.status == HealthStatus.HEALTHY]),
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "checks": [c.to_dict() for c in checks]
        }
    
    # ========================================================================
    # 系统指标
    # ========================================================================
    
    async def collect_metrics(
        self,
        active_agents: int = 0,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None
    ) -> SystemMetrics:
        """
        收集系统指标
        
        Args:
            active_agents: 活跃Agent数量
            memory_usage_mb: 内存使用(MB)
            cpu_usage_percent: CPU使用率
            
        Returns:
            系统指标
        """
        # 计算1小时内的错误数
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        error_count_1h = len([
            e for e in self._errors.values()
            if e.timestamp >= one_hour_ago
        ])
        
        # 计算平均响应时间
        avg_response_time = (
            self._total_response_time / self._response_count
            if self._response_count > 0 else 0.0
        )
        
        # 计算API成功率
        total_success = sum(e.success_count for e in self._endpoints.values())
        total_error = sum(e.error_count for e in self._endpoints.values())
        total_calls = total_success + total_error
        api_success_rate = total_success / total_calls if total_calls > 0 else 1.0
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            active_agents=active_agents,
            total_messages=self._message_counter,
            error_count_1h=error_count_1h,
            avg_response_time_ms=round(avg_response_time, 2),
            api_success_rate=round(api_success_rate, 4),
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent
        )
        
        self._metrics_history.append(metrics)
        
        # 限制历史记录数量
        if len(self._metrics_history) > self._max_metrics_history:
            self._metrics_history = self._metrics_history[-self._max_metrics_history:]
        
        return metrics
    
    async def get_metrics_history(
        self,
        limit: int = 50
    ) -> List[SystemMetrics]:
        """
        获取指标历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            指标历史列表
        """
        return self._metrics_history[-limit:]
    
    async def get_current_metrics(self) -> Optional[SystemMetrics]:
        """获取当前指标"""
        if self._metrics_history:
            return self._metrics_history[-1]
        return None
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        content = message.content
        action = content.get("action")
        
        if action == "record_error":
            error = await self.record_error(
                error_id=content.get("error_id", f"error_{self._error_counter}"),
                severity=ErrorSeverity(content.get("severity", "error")),
                category=ErrorCategory(content.get("category", "unknown_error")),
                source=content.get("source", "unknown"),
                message=content.get("message", ""),
                details=content.get("details"),
                stack_trace=content.get("stack_trace")
            )
            return Response(
                success=True,
                message_id=message.id,
                data=error.to_dict()
            )
        
        elif action == "get_errors":
            errors = await self.list_errors(
                severity=ErrorSeverity(content["severity"]) if content.get("severity") else None,
                category=ErrorCategory(content["category"]) if content.get("category") else None,
                unresolved_only=content.get("unresolved_only", False),
                limit=content.get("limit", 50)
            )
            return Response(
                success=True,
                message_id=message.id,
                data={"errors": [e.to_dict() for e in errors]}
            )
        
        elif action == "get_system_health":
            health = await self.get_system_health()
            return Response(
                success=True,
                message_id=message.id,
                data=health
            )
        
        elif action == "collect_metrics":
            metrics = await self.collect_metrics(
                active_agents=content.get("active_agents", 0),
                memory_usage_mb=content.get("memory_usage_mb"),
                cpu_usage_percent=content.get("cpu_usage_percent")
            )
            return Response(
                success=True,
                message_id=message.id,
                data=metrics.to_dict()
            )
        
        return None
    
    async def handle_protocol_message(
        self,
        message: ProtocolMessage
    ) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        data = message.payload.data
        
        if msg_type == ProtocolMessageType.ERROR:
            # 记录来自其他Agent的错误
            error = await self.record_agent_error(
                agent_id=message.header.source_agent,
                error_message=data.get("message", "Unknown error"),
                error_type=data.get("error_type", "unknown"),
                details=data.get("details"),
                stack_trace=data.get("stack_trace")
            )
            return message.create_response(
                ProtocolStatus.SUCCESS,
                data={"error_id": error.id}
            )
        
        elif msg_type == ProtocolMessageType.AGENT_STATUS:
            # 处理Agent状态更新
            agent_id = data.get("agent_id")
            new_state = data.get("new_state")
            
            if new_state == "error":
                await self.record_agent_error(
                    agent_id=agent_id,
                    error_message=f"Agent进入错误状态",
                    error_type="state_error",
                    details=data
                )
            
            return message.create_response(
                ProtocolStatus.SUCCESS,
                data={"acknowledged": True}
            )
        
        return None
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_errors": len(self._errors),
            "unresolved_errors": len([e for e in self._errors.values() if not e.resolved]),
            "errors_by_severity": {
                sev.value: len([e for e in self._errors.values() if e.severity == sev])
                for sev in ErrorSeverity
            },
            "errors_by_category": {
                cat.value: len([e for e in self._errors.values() if e.category == cat])
                for cat in ErrorCategory
            },
            "total_endpoints": len(self._endpoints),
            "monitored_endpoints": len([e for e in self._endpoints.values() if e.is_monitored]),
            "total_api_calls": sum(
                e.success_count + e.error_count for e in self._endpoints.values()
            ),
            "health_checks_count": len(self._health_checks),
            "metrics_history_count": len(self._metrics_history)
        }
