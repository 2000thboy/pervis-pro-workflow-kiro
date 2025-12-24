from dotenv import load_dotenv

load_dotenv()

import logging
import os

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_database
from routers import analysis, autocut, batch, config, export, feedback, multimodal, projects, render, script, timeline, transcription
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
app.include_router(render.router, tags=["视频渲染"])
app.include_router(analysis.router, tags=["分析日志"])
app.include_router(autocut.router, tags=["自动剪辑"])
app.include_router(config.router, prefix="/api/config", tags=["模型配置"])


@app.get("/")
async def root():
    return {"message": "Pervis Director Workbench API", "status": "running"}


@app.get("/api/health")
async def health_check():
    dam_base_url = os.getenv("DAM_BASE_URL", "http://localhost:8001")
    dam_ok = False
    try:
        timeout = aiohttp.ClientTimeout(total=2)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{dam_base_url}/api/health") as resp:
                dam_ok = resp.status == 200
    except Exception:
        dam_ok = False

    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        return {
            "status": "healthy",
            "service": "director-workbench",
            "version": "0.3.0",
            "dependencies": {"dam": "running" if dam_ok else "stopped"},
            "config": {"gemini_configured": bool(gemini_key)},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


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
