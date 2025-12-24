"""
FastAPI应用主入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import redis_manager
from app.core.logging import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动多Agent协作工作流系统...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
        
        # 连接Redis
        await redis_manager.connect()
        logger.info("Redis连接完成")
        
        logger.info("系统启动完成")
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭系统...")
    
    try:
        await redis_manager.disconnect()
        await close_db()
        logger.info("系统关闭完成")
    except Exception as e:
        logger.error(f"系统关闭时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于多Agent协作的智能视频制作系统",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "多Agent协作工作流核心系统",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )