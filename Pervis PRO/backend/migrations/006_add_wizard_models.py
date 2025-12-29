# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加项目立项向导相关表

Phase 3: 后端数据模型
Task 3.5: 数据库迁移脚本

添加以下表：
- project_wizard_drafts: 项目立项向导草稿
- project_templates: 项目模板
- agent_tasks: Agent 任务
- agent_task_logs: Agent 任务日志
- project_specs: 项目规格
- style_contexts: 艺术风格上下文
- content_versions: 内容版本
- user_decisions: 用户决策
"""

import logging
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, Float, Integer, JSON, String, Text,
    create_engine, inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================================
# 表定义
# ============================================================================

class ProjectWizardDraft(Base):
    """项目立项向导草稿表"""
    __tablename__ = "project_wizard_drafts"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    current_step = Column(String(50), default="basic_info")
    completion_percentage = Column(Float, default=0.0)
    status = Column(String(50), default="draft")
    field_status = Column(JSON, default=dict)
    draft_data = Column(JSON, default=dict)
    agent_tasks = Column(JSON, default=list)
    review_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_saved_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)  # 改名避免与 SQLAlchemy 冲突


class ProjectTemplate(Base):
    """项目模板表"""
    __tablename__ = "project_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), default="user")
    category = Column(String(50), default="custom")
    default_values = Column(JSON, default=dict)
    preset_fields = Column(JSON, default=dict)
    wizard_config = Column(JSON, default=dict)
    usage_count = Column(Integer, default=0)
    owner_id = Column(String, nullable=True)
    is_public = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)


class AgentTask(Base):
    """Agent 任务表"""
    __tablename__ = "agent_tasks"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    draft_id = Column(String, nullable=True)
    parent_task_id = Column(String, nullable=True)
    agent_type = Column(String(50), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    priority = Column(String(20), default="normal")
    progress = Column(Float, default=0.0)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text)
    error_details = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    review_status = Column(String(50))
    review_result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)


class AgentTaskLog(Base):
    """Agent 任务日志表"""
    __tablename__ = "agent_task_logs"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False)
    log_level = Column(String(20), default="info")
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ProjectSpecs(Base):
    """项目规格表"""
    __tablename__ = "project_specs"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, unique=True)
    duration_minutes = Column(Float)
    aspect_ratio = Column(String(20), default="16:9")
    frame_rate = Column(Float, default=24.0)
    resolution = Column(String(20), default="1920x1080")
    audio_sample_rate = Column(Integer, default=48000)
    audio_channels = Column(Integer, default=2)
    audio_bitrate = Column(Integer, default=320)
    video_codec = Column(String(50), default="H.264")
    video_bitrate = Column(Integer)
    color_space = Column(String(50), default="Rec.709")
    output_format = Column(String(20), default="mp4")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)


class StyleContext(Base):
    """艺术风格上下文表"""
    __tablename__ = "style_contexts"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    visual_style = Column(String(100))
    color_palette = Column(JSON, default=list)
    lighting_style = Column(String(100))
    reference_projects = Column(JSON, default=list)
    style_tags = Column(JSON, default=list)
    cinematography_style = Column(String(100))
    camera_movement = Column(JSON, default=list)
    editing_style = Column(String(100))
    transition_preferences = Column(JSON, default=list)
    is_confirmed = Column(Integer, default=0)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ContentVersion(Base):
    """内容版本表"""
    __tablename__ = "content_versions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    version_name = Column(String(255), nullable=False)
    version_number = Column(Integer, nullable=False)
    content_type = Column(String(50), nullable=False)
    entity_id = Column(String)
    entity_name = Column(String(255))
    content = Column(JSON, nullable=False)
    content_hash = Column(String(64))
    source = Column(String(50), default="user")
    source_task_id = Column(String)
    status = Column(String(50), default="draft")
    reviewed_by = Column(String)
    review_result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)


class UserDecision(Base):
    """用户决策表"""
    __tablename__ = "user_decisions"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    decision_type = Column(String(50), nullable=False)
    content_type = Column(String(50))
    content_id = Column(String)
    version_id = Column(String)
    decision_data = Column(JSON, default=dict)
    context = Column(JSON, default=dict)
    user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)


# ============================================================================
# 迁移函数
# ============================================================================

def upgrade(engine):
    """执行迁移 - 创建新表"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = [
        "project_wizard_drafts",
        "project_templates",
        "agent_tasks",
        "agent_task_logs",
        "project_specs",
        "style_contexts",
        "content_versions",
        "user_decisions"
    ]
    
    created_tables = []
    skipped_tables = []
    
    for table_name in tables_to_create:
        if table_name not in existing_tables:
            created_tables.append(table_name)
        else:
            skipped_tables.append(table_name)
    
    # 创建所有新表
    Base.metadata.create_all(bind=engine)
    
    logger.info(f"迁移完成: 创建 {len(created_tables)} 个表, 跳过 {len(skipped_tables)} 个已存在的表")
    
    if created_tables:
        logger.info(f"新创建的表: {', '.join(created_tables)}")
    if skipped_tables:
        logger.info(f"已存在的表: {', '.join(skipped_tables)}")
    
    return {
        "created": created_tables,
        "skipped": skipped_tables
    }


def downgrade(engine):
    """回滚迁移 - 删除新表"""
    tables_to_drop = [
        "user_decisions",
        "content_versions",
        "style_contexts",
        "project_specs",
        "agent_task_logs",
        "agent_tasks",
        "project_templates",
        "project_wizard_drafts"
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    dropped_tables = []
    
    for table_name in tables_to_drop:
        if table_name in existing_tables:
            # 使用原始 SQL 删除表
            with engine.connect() as conn:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
            dropped_tables.append(table_name)
    
    logger.info(f"回滚完成: 删除 {len(dropped_tables)} 个表")
    
    return {
        "dropped": dropped_tables
    }


def insert_system_templates(engine):
    """插入系统预设模板"""
    from uuid import uuid4
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有系统模板
        existing = session.query(ProjectTemplate).filter_by(template_type="system").first()
        if existing:
            logger.info("系统模板已存在，跳过插入")
            return
        
        # 系统预设模板
        system_templates = [
            {
                "id": "tpl_short_film",
                "name": "短片模板",
                "description": "适用于 5-30 分钟的短片项目",
                "template_type": "system",
                "category": "short_film",
                "default_values": {
                    "duration_minutes": 15,
                    "aspect_ratio": "2.39:1",
                    "frame_rate": 24,
                    "resolution": "1920x1080"
                },
                "preset_fields": {
                    "project_type": "short_film",
                    "style_tags": ["电影感", "叙事"]
                },
                "wizard_config": {
                    "skip_steps": [],
                    "required_fields": ["title", "script_content", "logline"],
                    "auto_generate": ["synopsis", "character_bio"]
                }
            },
            {
                "id": "tpl_advertisement",
                "name": "广告模板",
                "description": "适用于 15-60 秒的商业广告",
                "template_type": "system",
                "category": "advertisement",
                "default_values": {
                    "duration_minutes": 0.5,
                    "aspect_ratio": "16:9",
                    "frame_rate": 30,
                    "resolution": "1920x1080"
                },
                "preset_fields": {
                    "project_type": "advertisement",
                    "style_tags": ["商业", "快节奏"]
                },
                "wizard_config": {
                    "skip_steps": ["scene_planning"],
                    "required_fields": ["title", "logline"],
                    "auto_generate": ["visual_tags"]
                }
            },
            {
                "id": "tpl_music_video",
                "name": "MV 模板",
                "description": "适用于音乐视频项目",
                "template_type": "system",
                "category": "music_video",
                "default_values": {
                    "duration_minutes": 4,
                    "aspect_ratio": "16:9",
                    "frame_rate": 24,
                    "resolution": "1920x1080"
                },
                "preset_fields": {
                    "project_type": "music_video",
                    "style_tags": ["视觉", "节奏感"]
                },
                "wizard_config": {
                    "skip_steps": ["script_import"],
                    "required_fields": ["title"],
                    "auto_generate": ["visual_tags", "mood_tags"]
                }
            },
            {
                "id": "tpl_feature_film",
                "name": "长片模板",
                "description": "适用于 60 分钟以上的长片项目",
                "template_type": "system",
                "category": "feature_film",
                "default_values": {
                    "duration_minutes": 90,
                    "aspect_ratio": "2.39:1",
                    "frame_rate": 24,
                    "resolution": "3840x2160"
                },
                "preset_fields": {
                    "project_type": "feature_film",
                    "style_tags": ["电影", "叙事", "专业"]
                },
                "wizard_config": {
                    "skip_steps": [],
                    "required_fields": ["title", "script_content", "logline", "synopsis"],
                    "auto_generate": ["character_bio", "scene_breakdown"]
                }
            }
        ]
        
        for template_data in system_templates:
            template = ProjectTemplate(**template_data)
            session.add(template)
        
        session.commit()
        logger.info(f"成功插入 {len(system_templates)} 个系统模板")
        
    except Exception as e:
        session.rollback()
        logger.error(f"插入系统模板失败: {e}")
        raise
    finally:
        session.close()


# ============================================================================
# 主函数
# ============================================================================

def run_migration(database_url: str = None):
    """运行迁移"""
    import os
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")
    
    engine = create_engine(database_url)
    
    logger.info(f"开始迁移: {database_url}")
    
    # 执行迁移
    result = upgrade(engine)
    
    # 插入系统模板
    insert_system_templates(engine)
    
    logger.info("迁移完成")
    
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
