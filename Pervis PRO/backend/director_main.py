from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件（支持从 backend 目录或根目录启动）
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # 尝试加载当前目录的 .env

import logging
import os

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_database
from routers import analysis, autocut, batch, config, export, feedback, multimodal, projects, render, script, timeline, transcription, websocket, system, wizard, ai, image_generation
from routers.dam_proxy import create_dam_proxy_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pervis Director Workbench",
    description="导演工作台后端API（DAM网关模式）",
    version="0.3.0",
)

try:
    init_database()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    raise

asset_root = os.getenv("ASSET_ROOT", "./assets")
for subdir in ["originals", "proxies", "thumbnails", "audio"]:
    os.makedirs(os.path.join(asset_root, subdir), exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(asset_root):
    app.mount("/assets", StaticFiles(directory=asset_root), name="assets")

# 挂载生成图片目录（确保目录存在）
storage_root = os.getenv("STORAGE_ROOT", "./data")
generated_images_dir = os.path.join(storage_root, "generated_images")
os.makedirs(generated_images_dir, exist_ok=True)  # 确保目录存在
app.mount("/generated-images", StaticFiles(directory=generated_images_dir), name="generated_images")
logger.info(f"已挂载生成图片目录: {generated_images_dir}")

app.include_router(create_dam_proxy_router("/api/assets"), tags=["素材管理"])
app.include_router(create_dam_proxy_router("/api/storage"), tags=["存储管理"])
app.include_router(create_dam_proxy_router("/api/tags"), tags=["标签管理"])
app.include_router(create_dam_proxy_router("/api/search"), tags=["检索"])
app.include_router(create_dam_proxy_router("/api/images"), tags=["图片管理"])
app.include_router(create_dam_proxy_router("/api/vector"), tags=["向量分析"])

app.include_router(projects.router, tags=["项目管理"])
app.include_router(script.router, prefix="/api/script", tags=["剧本处理"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["反馈收集"])
app.include_router(transcription.router, tags=["音频转录"])
app.include_router(multimodal.router, tags=["多模态搜索"])
app.include_router(batch.router, tags=["批量处理"])
app.include_router(export.router, prefix="/api/export", tags=["导出功能"])
app.include_router(timeline.router, tags=["时间轴编辑"])
app.include_router(render.router, prefix="/api/render", tags=["视频渲染"])
app.include_router(analysis.router, tags=["分析日志"])
app.include_router(autocut.router, tags=["自动剪辑"])
app.include_router(config.router, prefix="/api/config", tags=["模型配置"])
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(wizard.router, prefix="/api/wizard", tags=["项目向导"])
app.include_router(ai.router, tags=["AI服务"])
app.include_router(image_generation.router, prefix="/api/image-generation", tags=["图片生成"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {"message": "Pervis Director Workbench API", "status": "running"}


@app.get("/api/health")
async def health_check():
    """
    快速健康检查
    
    注意: DAM 状态检查已移除以提高响应速度
    如需检查 DAM 状态，请使用 /api/system/health
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    replicate_key = os.getenv("REPLICATE_API_TOKEN")
    
    return {
        "status": "healthy",
        "service": "director-workbench",
        "version": "0.3.0",
        "config": {
            "gemini_configured": bool(gemini_key),
            "replicate_configured": bool(replicate_key),
            "llm_provider": os.getenv("LLM_PROVIDER", "auto")
        },
    }


@app.on_event("startup")
async def startup_event():
    try:
        from services.batch_processor import start_batch_processor

        await start_batch_processor()
        logger.info("批量处理器已启动")
    except Exception as e:
        logger.error(f"启动事件失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from services.batch_processor import stop_batch_processor

        await stop_batch_processor()
        logger.info("批量处理器已停止")
    except Exception as e:
        logger.error(f"关闭事件失败: {e}")


if __name__ == "__main__":
    uvicorn.run("director_main:app", host="0.0.0.0", port=8000, reload=True)
