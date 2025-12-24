"""
配置测试
"""
import pytest
from app.core.config import settings


def test_settings_loaded():
    """测试配置是否正确加载"""
    assert settings.PROJECT_NAME == "Multi-Agent Workflow Core"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"


def test_required_settings():
    """测试必需的配置项"""
    # 这些配置项应该有默认值或在环境变量中设置
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'REDIS_URL')
    assert hasattr(settings, 'SECRET_KEY')


def test_directory_creation():
    """测试目录创建功能"""
    import os
    
    # 测试目录是否被创建
    directories = [
        settings.UPLOAD_DIR,
        settings.ASSET_DIR,
        settings.TEMP_DIR,
        settings.CHROMA_DB_PATH,
        "./data/logs"
    ]
    
    for directory in directories:
        assert os.path.exists(directory), f"目录 {directory} 未被创建"