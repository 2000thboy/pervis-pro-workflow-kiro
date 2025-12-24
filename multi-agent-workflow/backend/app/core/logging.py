"""
日志配置
"""
import logging
from pathlib import Path
from typing import Any

# 尝试导入structlog，如果不可用则使用标准logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

try:
    from .config import settings
    LOG_LEVEL = settings.LOG_LEVEL
except Exception:
    LOG_LEVEL = "INFO"


class SimpleLogger:
    """简单日志器，当structlog不可用时使用"""
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        if kwargs:
            extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
            msg = f"{msg} | {extra_info}"
        self._logger.log(level, msg)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)


def setup_logging():
    """配置日志系统"""
    
    # 创建日志目录
    log_dir = Path("./data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if HAS_STRUCTLOG:
        # 配置structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # 配置标准logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # 尝试添加文件处理器
    try:
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)
    except Exception:
        pass
    
    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)


def get_logger(name: str):
    """获取日志器"""
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return SimpleLogger(name)