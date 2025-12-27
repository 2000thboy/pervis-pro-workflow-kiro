"""
Pervis PRO 导演工作台 - FastAPI 主应用
Phase 2: 集成数据库和核心服务
"""

# 必须在其他导入之前加载 .env 文件
from dotenv import load_dotenv
load_dotenv() # Config Reload Triggered

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os
import logging

from routers import script, assets, search, feedback, transcription, multimodal, batch, export, tags, vector, timeline, render, analysis, images, projects, autocut, storage, config, ai, asset_libraries, wizard, image_generation, system, websocket, keyframes
from database import init_database, get_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pervis PRO Director Workbench",
    description="导演工作台后端API",
    version="0.2.0"
)

# 初始化数据库
try:
    init_database()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    raise

# 创建资产目录结构
asset_root = os.getenv("ASSET_ROOT", "./assets")
for subdir in ["originals", "proxies", "thumbnails", "audio"]:
    os.makedirs(os.path.join(asset_root, subdir), exist_ok=True)

# CORS 中间件 - 允许前端调用 (MUST be before static files)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务 - 用于提供代理视频和缩略图
if os.path.exists(asset_root):
    app.mount("/assets", StaticFiles(directory=asset_root), name="assets")

# 注册路由
app.include_router(projects.router, tags=["项目管理"])
app.include_router(script.router, prefix="/api/script", tags=["剧本处理"])
app.include_router(assets.router, prefix="/api/assets", tags=["素材管理"])
app.include_router(search.router, prefix="/api/search", tags=["语义搜索"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["反馈收集"])
app.include_router(transcription.router, tags=["音频转录"])
app.include_router(multimodal.router, tags=["多模态搜索"])
app.include_router(batch.router, tags=["批量处理"])
app.include_router(export.router, prefix="/api/export", tags=["导出功能"])
app.include_router(tags.router, prefix="/api/tags", tags=["标签管理"])
app.include_router(vector.router, prefix="/api/vector", tags=["向量分析"])
app.include_router(timeline.router, tags=["时间轴编辑"])
app.include_router(render.router, tags=["视频渲染"])
app.include_router(analysis.router, tags=["分析日志"])
app.include_router(images.router, tags=["图片管理"])
app.include_router(autocut.router, tags=["自动剪辑"])
app.include_router(storage.router, prefix="/api/storage", tags=["存储管理"])
app.include_router(config.router, prefix="/api/config", tags=["模型配置"])
app.include_router(ai.router, tags=["AI服务"])
app.include_router(asset_libraries.router, tags=["素材库管理"])
app.include_router(asset_libraries.project_router, tags=["项目素材库"])
app.include_router(wizard.router, prefix="/api/wizard", tags=["项目立项向导"])
app.include_router(image_generation.router, prefix="/api/image-generation", tags=["AI图片生成"])
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(keyframes.router, prefix="/api/keyframes", tags=["关键帧管理"])

@app.get("/")
async def root():
    return {"message": "Pervis PRO Director Workbench API", "status": "running"}

@app.get("/api/timelines/list")
async def list_timelines_redirect(
    project_id: str = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    时间轴列表端点 - 前端集成修复
    重定向到时间轴服务
    """
    try:
        from sqlalchemy import text
        
        sql = text("""
            SELECT id, project_id, name, duration, created_at, updated_at
            FROM timelines 
            ORDER BY created_at DESC 
            LIMIT :limit
        """)
        result = db.execute(sql, {"limit": limit})
        
        timelines = []
        for row in result:
            timelines.append({
                "id": row[0],
                "project_id": row[1],
                "name": row[2],
                "duration": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            })
        
        return timelines
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间轴列表失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    
    try:
        # 检查环境变量
        gemini_key = os.getenv("GEMINI_API_KEY")
        asset_root = os.getenv("ASSET_ROOT", "./assets")
        
        return {
            "status": "healthy",
            "service": "director-workbench",
            "version": "0.2.0",
            "config": {
                "gemini_configured": bool(gemini_key),
                "asset_root": asset_root,
                "asset_dirs_exist": all(
                    os.path.exists(os.path.join(asset_root, d)) 
                    for d in ["originals", "proxies", "thumbnails", "audio"]
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

# 应用启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    try:
        # 启动批量处理器
        from services.batch_processor import start_batch_processor
        await start_batch_processor()
        logger.info("批量处理器已启动")
    except Exception as e:
        logger.error(f"启动事件失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    try:
        # 停止批量处理器
        from services.batch_processor import stop_batch_processor
        await stop_batch_processor()
        logger.info("批量处理器已停止")
    except Exception as e:
        logger.error(f"关闭事件失败: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)