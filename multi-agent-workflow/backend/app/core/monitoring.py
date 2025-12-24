"""
系统监控和健康检查模块

实现日志记录、系统健康检查和性能监控
验证需求: Requirements 1.4, 5.1
"""
import asyncio
import os
import psutil
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json

from .logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """组件类型"""
    AGENT = "agent"
    MESSAGE_BUS = "message_bus"
    DATABASE = "database"
    LLM_SERVICE = "llm_service"
    VECTOR_STORE = "vector_store"
    WORKFLOW_ENGINE = "workflow_engine"
    API_SERVER = "api_server"
    REDIS = "redis"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    process_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OperationLog:
    """操作日志"""
    log_id: str
    timestamp: datetime
    agent_id: Optional[str]
    operation: str
    status: str
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class SystemMonitor:
    """
    系统监控器
    
    实现系统健康检查、性能监控和操作日志记录
    验证需求: Requirements 1.4, 5.1
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        self._health_checks: Dict[str, Callable] = {}
        self._health_results: Dict[str, HealthCheckResult] = {}
        self._operation_logs: List[OperationLog] = []
        self._metrics_history: List[SystemMetrics] = []
        self._log_counter: int = 0
        self._log_dir = Path(log_dir) if log_dir else Path("./data/logs/monitoring")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._is_running: bool = False
        self._check_interval: int = 30  # 秒
    
    def _generate_log_id(self) -> str:
        """生成日志ID"""
        self._log_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"LOG-{timestamp}-{self._log_counter:06d}"
    
    # ============== 健康检查 ==============
    
    def register_health_check(
        self,
        component: str,
        component_type: ComponentType,
        check_func: Callable[[], bool]
    ) -> None:
        """注册健康检查函数"""
        self._health_checks[component] = {
            "type": component_type,
            "func": check_func
        }
    
    async def check_component_health(
        self,
        component: str
    ) -> Optional[HealthCheckResult]:
        """检查单个组件健康状态"""
        if component not in self._health_checks:
            return None
        
        check_info = self._health_checks[component]
        start_time = time.time()
        
        try:
            check_func = check_info["func"]
            if asyncio.iscoroutinefunction(check_func):
                is_healthy = await check_func()
            else:
                is_healthy = check_func()
            
            response_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                component=component,
                component_type=check_info["type"],
                status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                message="OK" if is_healthy else "Health check failed",
                response_time_ms=response_time
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                component=component,
                component_type=check_info["type"],
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                response_time_ms=response_time,
                details={"error": str(e)}
            )
        
        self._health_results[component] = result
        return result
    
    async def check_all_health(self) -> Dict[str, HealthCheckResult]:
        """检查所有组件健康状态"""
        results = {}
        for component in self._health_checks:
            result = await self.check_component_health(component)
            if result:
                results[component] = result
        return results
    
    def get_health_status(self, component: Optional[str] = None) -> Union[HealthCheckResult, Dict[str, HealthCheckResult], None]:
        """获取健康状态"""
        if component:
            return self._health_results.get(component)
        return self._health_results.copy()
    
    def get_overall_health(self) -> HealthStatus:
        """获取整体健康状态"""
        if not self._health_results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self._health_results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED
    
    # ============== 系统指标 ==============
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
        except Exception:
            # 如果 psutil 不可用，返回默认值
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                process_count=0
            )
        
        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_percent=disk.percent,
            disk_used_gb=disk.used / (1024 * 1024 * 1024),
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            process_count=len(psutil.pids())
        )
        
        self._metrics_history.append(metrics)
        
        # 保留最近1000条记录
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]
        
        return metrics
    
    def get_metrics_history(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """获取指标历史"""
        metrics = self._metrics_history
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics[-limit:]
    
    def get_average_metrics(
        self,
        since: Optional[datetime] = None
    ) -> Optional[Dict[str, float]]:
        """获取平均指标"""
        metrics = self.get_metrics_history(since)
        
        if not metrics:
            return None
        
        return {
            "avg_cpu_percent": sum(m.cpu_percent for m in metrics) / len(metrics),
            "avg_memory_percent": sum(m.memory_percent for m in metrics) / len(metrics),
            "avg_disk_percent": sum(m.disk_percent for m in metrics) / len(metrics),
            "sample_count": len(metrics)
        }

    # ============== 操作日志 ==============
    
    def log_operation(
        self,
        operation: str,
        status: str,
        duration_ms: float,
        agent_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> OperationLog:
        """
        记录操作日志
        
        验证需求: Requirements 1.4
        """
        log_entry = OperationLog(
            log_id=self._generate_log_id(),
            timestamp=datetime.now(),
            agent_id=agent_id,
            operation=operation,
            status=status,
            duration_ms=duration_ms,
            details=details or {},
            error_message=error_message
        )
        
        self._operation_logs.append(log_entry)
        
        # 保留最近10000条记录
        if len(self._operation_logs) > 10000:
            self._operation_logs = self._operation_logs[-10000:]
        
        # 写入日志文件
        self._write_operation_log(log_entry)
        
        # 记录到结构化日志
        log_data = {
            "log_id": log_entry.log_id,
            "agent_id": agent_id,
            "operation": operation,
            "status": status,
            "duration_ms": duration_ms
        }
        
        if status == "success":
            logger.info("Operation completed", **log_data)
        elif status == "error":
            logger.error("Operation failed", **log_data, error=error_message)
        else:
            logger.warning("Operation status", **log_data)
        
        return log_entry
    
    def _write_operation_log(self, log_entry: OperationLog) -> None:
        """写入操作日志文件"""
        log_file = self._log_dir / f"operations_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        entry_dict = {
            "log_id": log_entry.log_id,
            "timestamp": log_entry.timestamp.isoformat(),
            "agent_id": log_entry.agent_id,
            "operation": log_entry.operation,
            "status": log_entry.status,
            "duration_ms": log_entry.duration_ms,
            "details": log_entry.details,
            "error_message": log_entry.error_message
        }
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry_dict, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write operation log: {e}")
    
    def get_operation_logs(
        self,
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[OperationLog]:
        """查询操作日志"""
        logs = self._operation_logs
        
        if agent_id:
            logs = [l for l in logs if l.agent_id == agent_id]
        
        if operation:
            logs = [l for l in logs if l.operation == operation]
        
        if status:
            logs = [l for l in logs if l.status == status]
        
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        return logs[-limit:]
    
    def get_operation_statistics(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取操作统计"""
        logs = self._operation_logs
        
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        if not logs:
            return {
                "total_operations": 0,
                "success_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0
            }
        
        success_count = sum(1 for l in logs if l.status == "success")
        error_count = sum(1 for l in logs if l.status == "error")
        avg_duration = sum(l.duration_ms for l in logs) / len(logs)
        
        # 按Agent统计
        by_agent = {}
        for log in logs:
            if log.agent_id:
                if log.agent_id not in by_agent:
                    by_agent[log.agent_id] = {"total": 0, "success": 0, "error": 0}
                by_agent[log.agent_id]["total"] += 1
                if log.status == "success":
                    by_agent[log.agent_id]["success"] += 1
                elif log.status == "error":
                    by_agent[log.agent_id]["error"] += 1
        
        # 按操作类型统计
        by_operation = {}
        for log in logs:
            if log.operation not in by_operation:
                by_operation[log.operation] = {"total": 0, "avg_duration_ms": 0.0}
            by_operation[log.operation]["total"] += 1
        
        # 计算每种操作的平均时长
        for op in by_operation:
            op_logs = [l for l in logs if l.operation == op]
            by_operation[op]["avg_duration_ms"] = sum(l.duration_ms for l in op_logs) / len(op_logs)
        
        return {
            "total_operations": len(logs),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": success_count / len(logs) if logs else 0.0,
            "avg_duration_ms": avg_duration,
            "by_agent": by_agent,
            "by_operation": by_operation
        }
    
    # ============== 监控任务 ==============
    
    async def start_monitoring(self, interval: int = 30) -> None:
        """启动监控任务"""
        self._is_running = True
        self._check_interval = interval
        
        while self._is_running:
            try:
                # 收集系统指标
                self.collect_system_metrics()
                
                # 执行健康检查
                await self.check_all_health()
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            await asyncio.sleep(self._check_interval)
    
    def stop_monitoring(self) -> None:
        """停止监控任务"""
        self._is_running = False
    
    def is_running(self) -> bool:
        """检查监控是否运行中"""
        return self._is_running
    
    # ============== 报告生成 ==============
    
    def generate_health_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        metrics = self.collect_system_metrics()
        avg_metrics = self.get_average_metrics(
            since=datetime.now() - timedelta(hours=1)
        )
        op_stats = self.get_operation_statistics(
            since=datetime.now() - timedelta(hours=1)
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": self.get_overall_health().value,
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "response_time_ms": result.response_time_ms,
                    "last_check": result.timestamp.isoformat()
                }
                for name, result in self._health_results.items()
            },
            "current_metrics": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_percent": metrics.disk_percent
            },
            "average_metrics_1h": avg_metrics,
            "operation_statistics_1h": op_stats
        }
    
    def clear_history(self) -> None:
        """清除历史数据"""
        self._operation_logs.clear()
        self._metrics_history.clear()
        self._health_results.clear()


# 全局监控器实例
_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """获取全局系统监控器"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def set_system_monitor(monitor: SystemMonitor) -> None:
    """设置全局系统监控器"""
    global _system_monitor
    _system_monitor = monitor
