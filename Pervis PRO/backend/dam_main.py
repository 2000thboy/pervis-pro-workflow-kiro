from dotenv import load_dotenv

load_dotenv()

import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_database
from routers import assets, images, search, storage, tags, vector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pervis DAM",
    description="数字资产管理后端API",
    version="0.1.0",
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

app.include_router(assets.router, prefix="/api/assets", tags=["素材管理"])
app.include_router(storage.router, prefix="/api/storage", tags=["存储管理"])
app.include_router(tags.router, prefix="/api/tags", tags=["标签管理"])
app.include_router(search.router, prefix="/api/search", tags=["检索"])
app.include_router(images.router, tags=["图片管理"])
app.include_router(vector.router, prefix="/api/vector", tags=["向量分析"])


@app.get("/")
async def root():
    return {"message": "Pervis DAM API", "status": "running"}


@app.get("/api/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "service": "dam",
            "version": "0.1.0",
            "config": {
                "asset_root": asset_root,
                "asset_dirs_exist": all(
                    os.path.exists(os.path.join(asset_root, d))
                    for d in ["originals", "proxies", "thumbnails", "audio"]
                ),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("dam_main:app", host="0.0.0.0", port=8001, reload=True)

