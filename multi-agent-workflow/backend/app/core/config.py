"""
应用配置管理
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "Multi-Agent Workflow Core"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str
    
    # 数据库配置
    DATABASE_URL: str
    DATABASE_TEST_URL: Optional[str] = None
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ChromaDB配置
    CHROMA_DB_PATH: str = "./data/chroma_db"
    
    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LOCAL_LLM_ENDPOINT: Optional[str] = None
    
    # 文件存储配置
    UPLOAD_DIR: str = "./data/uploads"
    ASSET_DIR: str = "./data/assets"
    TEMP_DIR: str = "./data/temp"
    
    # WebSocket配置
    WS_HOST: str = "localhost"
    WS_PORT: int = 8001
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.UPLOAD_DIR,
            self.ASSET_DIR,
            self.TEMP_DIR,
            self.CHROMA_DB_PATH,
            "./data/logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

# 创建必要目录
settings.create_directories()