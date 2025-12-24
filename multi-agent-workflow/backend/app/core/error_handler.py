"""
错误处理框架
实现错误分类、处理策略和恢复机制

验证需求: Requirements 5.1, 5.2, 5.5
"""
import asyncio
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json

from .logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """错误分类"""
    AGENT_ERROR = "agent_error"           # Agent级错误
    COMMUNICATION_ERROR = "communication_error"  # 通信错误
    WORKFLOW_ERROR = "workflow_error"     # 工作流错误
    DATA_ERROR = "data_error"             # 数据错误
    EXTERNAL_SERVICE_ERROR = "external_service_error"  # 外部服务错误
    VALIDATION_ERROR = "validation_error"  # 验证错误
    PATH_ERROR = "path_error"             # 路径错误
    API_ERROR = "api_error"               # API错误
    SYSTEM_ERROR = "system_error"         # 系统错误


class RecoveryAction(str, Enum):
    """恢复动作"""
    RETRY = "retry"                       # 重试
    RESTART_AGENT = "restart_agent"       # 重启Agent
    FALLBACK = "fallback"                 # 降级处理
    NOTIFY_USER = "notify_user"           # 通知用户
    LOG_ONLY = "log_only"                 # 仅记录日志
    ABORT = "abort"                       # 中止操作
    SKIP = "skip"                         # 跳过当前步骤


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    source: str  # 错误来源 (agent_id, workflow_id, api_endpoint等)
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_action: Optional[RecoveryAction] = None
    recovery_result: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class ErrorRecord:
    """错误记录"""
    context: ErrorContext
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: Optional[datetime] = None


@dataclass
class PathValidationResult:
    """路径验证结果"""
    path: str
    is_valid: bool
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class APIMonitoringResult:
    """API监控结果"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    is_success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ErrorHandler:
    """
    错误处理器
    
    实现错误分类、处理策略和恢复机制
    验证需求: Requirements 5.1, 5.2, 5.5
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        self._error_records: Dict[str, ErrorRecord] = {}
        self._error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self._recovery_strategies: Dict[ErrorCategory, RecoveryAction] = {}
        self._api_monitoring_results: List[APIMonitoringResult] = []
        self._path_validation_results: List[PathValidationResult] = []
        self._error_counter: int = 0
        self._log_dir = Path(log_dir) if log_dir else Path("./data/logs/errors")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置默认恢复策略
        self._setup_default_strategies()
    
    def _setup_default_strategies(self) -> None:
        """设置默认恢复策略"""
        self._recovery_strategies = {
            ErrorCategory.AGENT_ERROR: RecoveryAction.RESTART_AGENT,
            ErrorCategory.COMMUNICATION_ERROR: RecoveryAction.RETRY,
            ErrorCategory.WORKFLOW_ERROR: RecoveryAction.NOTIFY_USER,
            ErrorCategory.DATA_ERROR: RecoveryAction.ABORT,
            ErrorCategory.EXTERNAL_SERVICE_ERROR: RecoveryAction.FALLBACK,
            ErrorCategory.VALIDATION_ERROR: RecoveryAction.NOTIFY_USER,
            ErrorCategory.PATH_ERROR: RecoveryAction.LOG_ONLY,
            ErrorCategory.API_ERROR: RecoveryAction.RETRY,
            ErrorCategory.SYSTEM_ERROR: RecoveryAction.ABORT,
        }
    
    def _generate_error_id(self) -> str:
        """生成错误ID"""
        self._error_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ERR-{timestamp}-{self._error_counter:04d}"
    
    def register_handler(
        self, 
        category: ErrorCategory, 
        handler: Callable[[ErrorContext], None]
    ) -> None:
        """注册错误处理器"""
        if category not in self._error_handlers:
            self._error_handlers[category] = []
        self._error_handlers[category].append(handler)
    
    def set_recovery_strategy(
        self, 
        category: ErrorCategory, 
        action: RecoveryAction
    ) -> None:
        """设置恢复策略"""
        self._recovery_strategies[category] = action
    
    def get_recovery_strategy(self, category: ErrorCategory) -> RecoveryAction:
        """获取恢复策略"""
        return self._recovery_strategies.get(category, RecoveryAction.LOG_ONLY)

    async def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        source: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        处理错误
        
        Args:
            error: 异常对象
            category: 错误分类
            source: 错误来源
            severity: 严重程度
            metadata: 额外元数据
            
        Returns:
            ErrorContext: 错误上下文
        """
        error_id = self._generate_error_id()
        
        context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            message=str(error),
            source=source,
            exception_type=type(error).__name__,
            exception_message=str(error),
            stack_trace=traceback.format_exc(),
            metadata=metadata or {},
            recovery_action=self.get_recovery_strategy(category)
        )
        
        # 创建错误记录
        record = ErrorRecord(context=context)
        self._error_records[error_id] = record
        
        # 记录日志
        await self._log_error(context)
        
        # 调用注册的处理器
        await self._invoke_handlers(context)
        
        # 执行恢复策略
        await self._execute_recovery(record)
        
        return context
    
    async def handle_agent_error(
        self,
        agent_id: str,
        error: Exception,
        task_id: Optional[str] = None
    ) -> ErrorContext:
        """
        处理Agent级错误
        
        验证需求: Requirements 5.1
        """
        metadata = {
            "agent_id": agent_id,
            "task_id": task_id
        }
        
        return await self.handle_error(
            error=error,
            category=ErrorCategory.AGENT_ERROR,
            source=agent_id,
            severity=ErrorSeverity.ERROR,
            metadata=metadata
        )
    
    async def handle_communication_error(
        self,
        source: str,
        target: str,
        error: Exception
    ) -> ErrorContext:
        """处理通信错误"""
        metadata = {
            "source_agent": source,
            "target_agent": target
        }
        
        return await self.handle_error(
            error=error,
            category=ErrorCategory.COMMUNICATION_ERROR,
            source=f"{source}->{target}",
            severity=ErrorSeverity.WARNING,
            metadata=metadata
        )
    
    async def handle_workflow_error(
        self,
        workflow_id: str,
        step_id: str,
        error: Exception
    ) -> ErrorContext:
        """处理工作流错误"""
        metadata = {
            "workflow_id": workflow_id,
            "step_id": step_id
        }
        
        return await self.handle_error(
            error=error,
            category=ErrorCategory.WORKFLOW_ERROR,
            source=workflow_id,
            severity=ErrorSeverity.ERROR,
            metadata=metadata
        )
    
    async def handle_api_error(
        self,
        endpoint: str,
        method: str,
        error: Exception,
        status_code: Optional[int] = None
    ) -> ErrorContext:
        """
        处理API错误
        
        验证需求: Requirements 5.2
        """
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        }
        
        return await self.handle_error(
            error=error,
            category=ErrorCategory.API_ERROR,
            source=f"{method} {endpoint}",
            severity=ErrorSeverity.ERROR,
            metadata=metadata
        )
    
    async def handle_path_error(
        self,
        path: str,
        error: Exception,
        suggested_fix: Optional[str] = None
    ) -> ErrorContext:
        """
        处理路径错误
        
        验证需求: Requirements 5.5
        """
        metadata = {
            "path": path,
            "suggested_fix": suggested_fix
        }
        
        # 记录路径验证结果
        validation_result = PathValidationResult(
            path=path,
            is_valid=False,
            error_message=str(error),
            suggested_fix=suggested_fix
        )
        self._path_validation_results.append(validation_result)
        
        return await self.handle_error(
            error=error,
            category=ErrorCategory.PATH_ERROR,
            source=path,
            severity=ErrorSeverity.WARNING,
            metadata=metadata
        )
    
    async def _log_error(self, context: ErrorContext) -> None:
        """记录错误日志"""
        log_data = {
            "error_id": context.error_id,
            "timestamp": context.timestamp.isoformat(),
            "category": context.category.value,
            "severity": context.severity.value,
            "message": context.message,
            "source": context.source,
            "exception_type": context.exception_type,
            "exception_message": context.exception_message,
            "metadata": context.metadata
        }
        
        # 根据严重程度选择日志级别
        if context.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", **log_data)
        elif context.severity == ErrorSeverity.ERROR:
            logger.error("Error occurred", **log_data)
        elif context.severity == ErrorSeverity.WARNING:
            logger.warning("Warning occurred", **log_data)
        else:
            logger.info("Info logged", **log_data)
        
        # 写入错误日志文件
        await self._write_error_log(context)
    
    async def _write_error_log(self, context: ErrorContext) -> None:
        """写入错误日志文件"""
        log_file = self._log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        log_entry = {
            "error_id": context.error_id,
            "timestamp": context.timestamp.isoformat(),
            "category": context.category.value,
            "severity": context.severity.value,
            "message": context.message,
            "source": context.source,
            "exception_type": context.exception_type,
            "stack_trace": context.stack_trace,
            "metadata": context.metadata,
            "recovery_action": context.recovery_action.value if context.recovery_action else None
        }
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")
    
    async def _invoke_handlers(self, context: ErrorContext) -> None:
        """调用注册的错误处理器"""
        handlers = self._error_handlers.get(context.category, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context)
                else:
                    handler(context)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")
    
    async def _execute_recovery(self, record: ErrorRecord) -> None:
        """执行恢复策略"""
        context = record.context
        action = context.recovery_action
        
        if action == RecoveryAction.RETRY:
            await self._handle_retry(record)
        elif action == RecoveryAction.RESTART_AGENT:
            context.recovery_result = "Agent restart requested"
        elif action == RecoveryAction.FALLBACK:
            context.recovery_result = "Fallback mode activated"
        elif action == RecoveryAction.NOTIFY_USER:
            context.recovery_result = "User notification sent"
        elif action == RecoveryAction.ABORT:
            context.recovery_result = "Operation aborted"
        elif action == RecoveryAction.SKIP:
            context.recovery_result = "Step skipped"
        else:
            context.recovery_result = "Logged only"
    
    async def _handle_retry(self, record: ErrorRecord) -> None:
        """处理重试逻辑"""
        if record.retry_count < record.max_retries:
            record.retry_count += 1
            record.last_retry_at = datetime.now()
            record.context.recovery_result = f"Retry {record.retry_count}/{record.max_retries}"
        else:
            record.context.recovery_result = "Max retries exceeded"
            record.context.recovery_action = RecoveryAction.ABORT

    # API监控方法
    def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        error_message: Optional[str] = None
    ) -> APIMonitoringResult:
        """
        记录API调用结果
        
        验证需求: Requirements 5.2
        """
        result = APIMonitoringResult(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            is_success=100 <= status_code < 400,  # 1xx, 2xx, 3xx 都视为成功
            error_message=error_message,
            timestamp=datetime.now()
        )
        
        self._api_monitoring_results.append(result)
        
        # 如果是错误状态码，记录日志
        if not result.is_success:
            logger.warning(
                "API call failed",
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                error=error_message
            )
        
        return result
    
    def get_api_monitoring_results(
        self,
        endpoint: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[APIMonitoringResult]:
        """获取API监控结果"""
        results = self._api_monitoring_results
        
        if endpoint:
            results = [r for r in results if r.endpoint == endpoint]
        
        if since:
            results = [r for r in results if r.timestamp >= since]
        
        return results
    
    def get_api_error_rate(
        self,
        endpoint: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> float:
        """计算API错误率"""
        results = self.get_api_monitoring_results(endpoint, since)
        
        if not results:
            return 0.0
        
        error_count = sum(1 for r in results if not r.is_success)
        return error_count / len(results)
    
    # 路径验证方法
    def validate_path(
        self,
        path: str,
        must_exist: bool = True,
        allowed_extensions: Optional[List[str]] = None
    ) -> PathValidationResult:
        """
        验证文件路径
        
        验证需求: Requirements 5.5
        """
        path_obj = Path(path)
        
        # 检查路径是否存在
        if must_exist and not path_obj.exists():
            suggested_fix = f"Create the file or directory at: {path}"
            result = PathValidationResult(
                path=path,
                is_valid=False,
                error_message=f"Path does not exist: {path}",
                suggested_fix=suggested_fix
            )
            self._path_validation_results.append(result)
            logger.warning(
                "Path validation failed",
                path=path,
                error="Path does not exist",
                suggested_fix=suggested_fix
            )
            return result
        
        # 检查文件扩展名
        if allowed_extensions and path_obj.suffix:
            if path_obj.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                suggested_fix = f"Use one of the allowed extensions: {', '.join(allowed_extensions)}"
                result = PathValidationResult(
                    path=path,
                    is_valid=False,
                    error_message=f"Invalid file extension: {path_obj.suffix}",
                    suggested_fix=suggested_fix
                )
                self._path_validation_results.append(result)
                logger.warning(
                    "Path validation failed",
                    path=path,
                    error="Invalid extension",
                    suggested_fix=suggested_fix
                )
                return result
        
        # 检查路径是否包含非法字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in str(path_obj.name):
                suggested_fix = f"Remove invalid character '{char}' from the path"
                result = PathValidationResult(
                    path=path,
                    is_valid=False,
                    error_message=f"Path contains invalid character: {char}",
                    suggested_fix=suggested_fix
                )
                self._path_validation_results.append(result)
                logger.warning(
                    "Path validation failed",
                    path=path,
                    error=f"Invalid character: {char}",
                    suggested_fix=suggested_fix
                )
                return result
        
        result = PathValidationResult(path=path, is_valid=True)
        self._path_validation_results.append(result)
        return result
    
    def get_path_validation_results(
        self,
        valid_only: bool = False,
        invalid_only: bool = False
    ) -> List[PathValidationResult]:
        """获取路径验证结果"""
        results = self._path_validation_results
        
        if valid_only:
            results = [r for r in results if r.is_valid]
        elif invalid_only:
            results = [r for r in results if not r.is_valid]
        
        return results
    
    # 错误查询方法
    def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        """获取错误记录"""
        return self._error_records.get(error_id)
    
    def get_errors(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        source: Optional[str] = None,
        resolved: Optional[bool] = None,
        since: Optional[datetime] = None
    ) -> List[ErrorRecord]:
        """查询错误记录"""
        records = list(self._error_records.values())
        
        if category:
            records = [r for r in records if r.context.category == category]
        
        if severity:
            records = [r for r in records if r.context.severity == severity]
        
        if source:
            records = [r for r in records if r.context.source == source]
        
        if resolved is not None:
            records = [r for r in records if r.context.resolved == resolved]
        
        if since:
            records = [r for r in records if r.context.timestamp >= since]
        
        return records
    
    def resolve_error(self, error_id: str, resolution_note: Optional[str] = None) -> bool:
        """标记错误为已解决"""
        record = self._error_records.get(error_id)
        if record:
            record.context.resolved = True
            record.context.resolved_at = datetime.now()
            if resolution_note:
                record.context.metadata["resolution_note"] = resolution_note
            return True
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        records = list(self._error_records.values())
        
        # 按分类统计
        by_category = {}
        for cat in ErrorCategory:
            count = sum(1 for r in records if r.context.category == cat)
            if count > 0:
                by_category[cat.value] = count
        
        # 按严重程度统计
        by_severity = {}
        for sev in ErrorSeverity:
            count = sum(1 for r in records if r.context.severity == sev)
            if count > 0:
                by_severity[sev.value] = count
        
        # 解决状态统计
        resolved_count = sum(1 for r in records if r.context.resolved)
        unresolved_count = len(records) - resolved_count
        
        return {
            "total_errors": len(records),
            "resolved": resolved_count,
            "unresolved": unresolved_count,
            "by_category": by_category,
            "by_severity": by_severity,
            "api_error_rate": self.get_api_error_rate(),
            "path_validation_failures": len([r for r in self._path_validation_results if not r.is_valid])
        }
    
    def clear_errors(self) -> int:
        """清除所有错误记录"""
        count = len(self._error_records)
        self._error_records.clear()
        self._api_monitoring_results.clear()
        self._path_validation_results.clear()
        return count


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def set_error_handler(handler: ErrorHandler) -> None:
    """设置全局错误处理器"""
    global _error_handler
    _error_handler = handler
