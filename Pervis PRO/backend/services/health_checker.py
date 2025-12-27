"""
HealthChecker - 系统健康检查器

定期检查系统各组件状态，发现问题时通过 EventService 发送警告。
"""

import os
import shutil
import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """检查状态"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """单项检查结果"""
    name: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details or {}
        }


@dataclass
class HealthCheckResult:
    """完整健康检查结果"""
    status: str  # healthy, degraded, unhealthy
    checks: Dict[str, CheckResult]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "checks": {k: v.to_dict() for k, v in self.checks.items()},
            "timestamp": self.timestamp
        }


class HealthChecker:
    """
    健康检查器
    
    检查项目:
    - API 服务状态
    - 数据库连接
    - FFmpeg 可用性
    - AI 服务 (Ollama)
    - 存储空间
    - 缓存状态
    """
    
    def __init__(self):
        self._event_service = None
    
    @property
    def event_service(self):
        """延迟加载 EventService，避免循环导入"""
        if self._event_service is None:
            from services.event_service import event_service
            self._event_service = event_service
        return self._event_service
    
    async def check_all(self) -> HealthCheckResult:
        """
        执行完整健康检查
        
        Returns:
            HealthCheckResult: 检查结果
        """
        checks = {}
        
        # 并行执行所有检查
        results = await asyncio.gather(
            self._check_api(),
            self._check_database(),
            self._check_ffmpeg(),
            self._check_ai_service(),
            self._check_storage(),
            self._check_cache(),
            return_exceptions=True
        )
        
        check_names = ["api", "database", "ffmpeg", "ai_service", "storage", "cache"]
        
        for name, result in zip(check_names, results):
            if isinstance(result, Exception):
                checks[name] = CheckResult(
                    name=name,
                    status=CheckStatus.ERROR,
                    message=f"检查失败: {str(result)}"
                )
            else:
                checks[name] = result
        
        # 计算整体状态
        statuses = [c.status for c in checks.values()]
        if all(s == CheckStatus.OK for s in statuses):
            overall_status = "healthy"
        elif any(s == CheckStatus.ERROR for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return HealthCheckResult(
            status=overall_status,
            checks=checks,
            timestamp=datetime.now().isoformat()
        )
    
    async def _check_api(self) -> CheckResult:
        """检查 API 服务状态"""
        try:
            # API 正在运行（因为这个检查本身就是通过 API 调用的）
            return CheckResult(
                name="api",
                status=CheckStatus.OK,
                message="API 服务正常运行"
            )
        except Exception as e:
            return CheckResult(
                name="api",
                status=CheckStatus.ERROR,
                message=f"API 服务异常: {str(e)}"
            )
    
    async def _check_database(self) -> CheckResult:
        """检查数据库连接"""
        try:
            from database import get_db_session
            
            with get_db_session() as session:
                # 执行简单查询测试连接
                session.execute("SELECT 1")
            
            return CheckResult(
                name="database",
                status=CheckStatus.OK,
                message="数据库连接正常"
            )
        except ImportError:
            return CheckResult(
                name="database",
                status=CheckStatus.WARNING,
                message="数据库模块未配置"
            )
        except Exception as e:
            return CheckResult(
                name="database",
                status=CheckStatus.ERROR,
                message=f"数据库连接失败: {str(e)}"
            )
    
    async def _check_ffmpeg(self) -> CheckResult:
        """检查 FFmpeg 可用性"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # 提取版本信息
                version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
                return CheckResult(
                    name="ffmpeg",
                    status=CheckStatus.OK,
                    message="FFmpeg 可用",
                    details={"version": version_line}
                )
            else:
                return CheckResult(
                    name="ffmpeg",
                    status=CheckStatus.ERROR,
                    message="FFmpeg 执行失败"
                )
        except FileNotFoundError:
            return CheckResult(
                name="ffmpeg",
                status=CheckStatus.ERROR,
                message="FFmpeg 未安装或不在 PATH 中"
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="ffmpeg",
                status=CheckStatus.WARNING,
                message="FFmpeg 响应超时"
            )
        except Exception as e:
            return CheckResult(
                name="ffmpeg",
                status=CheckStatus.ERROR,
                message=f"FFmpeg 检查失败: {str(e)}"
            )
    
    async def _check_ai_service(self) -> CheckResult:
        """检查 AI 服务 (Ollama)"""
        try:
            import aiohttp
            
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get("models", [])
                        model_names = [m.get("name", "") for m in models]
                        return CheckResult(
                            name="ai_service",
                            status=CheckStatus.OK,
                            message=f"Ollama 服务正常，已加载 {len(models)} 个模型",
                            details={"models": model_names[:5]}  # 只显示前5个
                        )
                    else:
                        return CheckResult(
                            name="ai_service",
                            status=CheckStatus.WARNING,
                            message=f"Ollama 响应异常: {resp.status}"
                        )
        except ImportError:
            return CheckResult(
                name="ai_service",
                status=CheckStatus.WARNING,
                message="aiohttp 未安装"
            )
        except Exception as e:
            error_msg = str(e)
            if "Cannot connect" in error_msg or "Connection refused" in error_msg:
                return CheckResult(
                    name="ai_service",
                    status=CheckStatus.WARNING,
                    message="Ollama 服务未运行（可选服务）"
                )
            return CheckResult(
                name="ai_service",
                status=CheckStatus.WARNING,
                message=f"AI 服务检查失败: {error_msg}"
            )
    
    async def _check_storage(self) -> CheckResult:
        """检查存储空间"""
        try:
            asset_root = os.getenv("ASSET_ROOT", "./assets")
            
            # 确保目录存在
            if not os.path.exists(asset_root):
                os.makedirs(asset_root, exist_ok=True)
            
            # 获取磁盘使用情况
            usage = shutil.disk_usage(asset_root)
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            used_percent = (usage.used / usage.total) * 100
            
            details = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 1),
                "path": asset_root
            }
            
            if free_gb < 1:
                # 空间不足，发送警告
                await self.event_service.emit_system_warning(
                    "storage.low",
                    f"存储空间不足，剩余 {free_gb:.1f} GB",
                    {"action": "clean_cache", "label": "清理缓存"}
                )
                return CheckResult(
                    name="storage",
                    status=CheckStatus.ERROR,
                    message=f"存储空间严重不足: {free_gb:.1f} GB",
                    details=details
                )
            elif free_gb < 5:
                return CheckResult(
                    name="storage",
                    status=CheckStatus.WARNING,
                    message=f"存储空间较低: {free_gb:.1f} GB",
                    details=details
                )
            else:
                return CheckResult(
                    name="storage",
                    status=CheckStatus.OK,
                    message=f"存储空间充足: {free_gb:.1f} GB 可用",
                    details=details
                )
        except Exception as e:
            return CheckResult(
                name="storage",
                status=CheckStatus.ERROR,
                message=f"存储检查失败: {str(e)}"
            )
    
    async def _check_cache(self) -> CheckResult:
        """检查缓存状态"""
        try:
            cache_dir = os.getenv("CACHE_DIR", "./data/cache")
            
            if not os.path.exists(cache_dir):
                return CheckResult(
                    name="cache",
                    status=CheckStatus.OK,
                    message="缓存目录未创建（正常）"
                )
            
            # 计算缓存大小
            total_size = 0
            file_count = 0
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
                        file_count += 1
            
            size_mb = total_size / (1024 ** 2)
            details = {
                "size_mb": round(size_mb, 2),
                "file_count": file_count,
                "path": cache_dir
            }
            
            if size_mb > 1000:  # 超过 1GB
                return CheckResult(
                    name="cache",
                    status=CheckStatus.WARNING,
                    message=f"缓存较大: {size_mb:.0f} MB，建议清理",
                    details=details
                )
            else:
                return CheckResult(
                    name="cache",
                    status=CheckStatus.OK,
                    message=f"缓存正常: {size_mb:.0f} MB",
                    details=details
                )
        except Exception as e:
            return CheckResult(
                name="cache",
                status=CheckStatus.WARNING,
                message=f"缓存检查失败: {str(e)}"
            )


# 全局实例
health_checker = HealthChecker()
