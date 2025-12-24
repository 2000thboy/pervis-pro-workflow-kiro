"""Configuration management for Pervis PRO backend."""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    
    # Database
    database_url: str = "sqlite:///./pervis_pro.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Database Connection Pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600  # 1 hour
    
    # AI Services
    gemini_api_key: str = ""
    
    # File Storage
    asset_root: Path = Path("./.data/pervis_assets")
    proxy_root: Path = Path("./.data/pervis_proxies")
    temp_root: Path = Path("./.data/pervis_temp")
    
    # FFmpeg
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    
    # Application
    debug: bool = False
    log_level: str = "INFO"
    max_upload_size: int = 5 * 1024 * 1024 * 1024  # 5GB
    concurrent_processing_limit: int = 3
    
    # Security
    secret_key: str = "dev-secret"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.asset_root.mkdir(parents=True, exist_ok=True)
        self.proxy_root.mkdir(parents=True, exist_ok=True)
        self.temp_root.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
