"""
数据库配置和连接管理
Phase 2: 使用SQLite进行快速开发，后续可切换PostgreSQL
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import os

# 导入配置
try:
    from app.config import settings
    DATABASE_URL = settings.database_url
    # 连接池配置
    DB_POOL_SIZE = settings.db_pool_size
    DB_MAX_OVERFLOW = settings.db_max_overflow
    DB_POOL_TIMEOUT = settings.db_pool_timeout
    DB_POOL_RECYCLE = settings.db_pool_recycle
except ImportError:
    # 兼容旧配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# 数据库引擎配置
if "sqlite" in DATABASE_URL:
    # SQLite配置 - 使用StaticPool以支持多线程
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False  # 生产环境关闭SQL日志
    )
else:
    # PostgreSQL配置 - 使用连接池
    engine = create_engine(
        DATABASE_URL,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=DB_POOL_RECYCLE,
        pool_pre_ping=True,  # 连接前检查连接有效性
        echo=False  # 生产环境关闭SQL日志
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据库表模型
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    title = Column(String(255), nullable=False)
    logline = Column(Text)
    synopsis = Column(Text)
    script_raw = Column(Text)
    characters = Column(JSON)  # 存储角色列表
    specs = Column(JSON)       # 存储项目规格
    created_at = Column(DateTime, default=datetime.utcnow)
    current_stage = Column(String(50))

class Beat(Base):
    __tablename__ = "beats"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    order_index = Column(Integer)
    content = Column(Text)
    emotion_tags = Column(JSON)      # ["紧张", "恐惧"]
    scene_tags = Column(JSON)        # ["夜晚", "街道"]
    action_tags = Column(JSON)       # ["奔跑", "追逐"]
    cinematography_tags = Column(JSON) # ["手持", "特写"]
    duration = Column(Float)
    user_notes = Column(Text)
    main_asset_id = Column(String)

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    filename = Column(String(255))
    mime_type = Column(String(100))
    source = Column(String(50))      # upload, external, generated, local
    file_path = Column(String(500))  # 原始文件路径
    proxy_path = Column(String(500)) # 代理文件路径
    thumbnail_path = Column(String(500)) # 缩略图路径
    processing_status = Column(String(50)) # uploaded, processing, completed, error
    processing_progress = Column(Integer, default=0)
    tags = Column(JSON)              # 自由标签
    processing_metadata = Column(JSON)          # 处理元数据
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetSegment(Base):
    __tablename__ = "asset_segments"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    description = Column(Text)
    emotion_tags = Column(JSON)
    scene_tags = Column(JSON)
    action_tags = Column(JSON)
    cinematography_tags = Column(JSON)

class AssetVector(Base):
    __tablename__ = "asset_vectors"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    segment_id = Column(String)      # 可选，关联到具体segment
    vector_data = Column(Text)       # JSON存储向量数据
    content_type = Column(String(50)) # transcript, description, tags
    text_content = Column(Text)      # 原始文本内容
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedbackLog(Base):
    __tablename__ = "feedback_logs"
    
    id = Column(String, primary_key=True)
    beat_id = Column(String)
    asset_id = Column(String, nullable=False)
    segment_id = Column(String)
    action = Column(String(50))      # accept, reject
    context = Column(Text)           # 用户反馈上下文
    query_context = Column(Text)     # 搜索上下文
    timestamp = Column(DateTime, default=datetime.utcnow)

# 新增模型 - 标签管理和导出功能

class TagHierarchy(Base):
    """标签层级表"""
    __tablename__ = "tag_hierarchy"
    
    id = Column(String, primary_key=True)
    tag_name = Column(String(255), nullable=False)
    parent_id = Column(String)
    level = Column(Integer, default=0)
    category = Column(String(100))  # location, time, action, emotion, visual_style, camera, color
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AssetTag(Base):
    """资产标签关联表"""
    __tablename__ = "asset_tags"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    tag_id = Column(String, nullable=False)
    weight = Column(Float, default=1.0)  # 关联度权重 0.0-1.0
    order_index = Column(Integer, default=0)  # 显示顺序
    source = Column(String(50), default='auto')  # auto, manual, ai
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ExportHistory(Base):
    """导出历史表"""
    __tablename__ = "export_history"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    export_type = Column(String(50), nullable=False)  # script_docx, script_pdf, beatboard_image
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_format = Column(String(20))  # docx, pdf, png, jpg
    options = Column(JSON)  # 导出选项
    status = Column(String(50), default='completed')  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

class SearchTestCase(Base):
    """搜索测试案例表"""
    __tablename__ = "search_test_cases"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    expected_results = Column(JSON)  # 期望的结果列表
    actual_results = Column(JSON)  # 实际的结果列表
    similarity_scores = Column(JSON)  # 相似度分数
    tag_contributions = Column(JSON)  # 标签贡献度
    status = Column(String(50))  # passed, failed, pending
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# 视频编辑系统模型

class Timeline(Base):
    """时间轴表"""
    __tablename__ = "timelines"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    name = Column(String(255), default="主时间轴")
    duration = Column(Float, default=0.0)  # 总时长（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Clip(Base):
    """视频片段表"""
    __tablename__ = "clips"
    
    id = Column(String, primary_key=True)
    timeline_id = Column(String, nullable=False)
    asset_id = Column(String, nullable=False)
    
    # 时间属性
    start_time = Column(Float, nullable=False)  # 在时间轴上的开始时间
    end_time = Column(Float, nullable=False)    # 在时间轴上的结束时间
    trim_start = Column(Float, default=0.0)     # 素材的入点
    trim_end = Column(Float)                    # 素材的出点（null表示到结尾）
    
    # 音频属性
    volume = Column(Float, default=1.0)         # 音量（0-2）
    is_muted = Column(Integer, default=0)       # 是否静音（0/1）
    audio_fade_in = Column(Float, default=0.0)  # 音频淡入时长
    audio_fade_out = Column(Float, default=0.0) # 音频淡出时长
    
    # 转场属性
    transition_type = Column(String(50))        # fade, cut, wipe, dissolve
    transition_duration = Column(Float, default=0.0)
    
    # 顺序和元数据
    order_index = Column(Integer, nullable=False)
    clip_metadata = Column(JSON)                # 额外的元数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class RenderTask(Base):
    """渲染任务表"""
    __tablename__ = "render_tasks"
    
    id = Column(String, primary_key=True)
    timeline_id = Column(String, nullable=False)
    
    # 渲染选项
    format = Column(String(20), default='mp4')  # mp4, mov
    resolution = Column(String(20), default='1080p')  # 720p, 1080p, 4k
    framerate = Column(Integer, default=30)     # 24, 30, 60
    quality = Column(String(20), default='high') # low, medium, high, custom
    bitrate = Column(Integer)                   # 自定义比特率（kbps）
    audio_bitrate = Column(Integer, default=192) # 音频比特率（kbps）
    
    # 状态
    status = Column(String(50), default='pending')  # pending, processing, completed, failed, cancelled
    progress = Column(Float, default=0.0)       # 0.0-100.0
    error_message = Column(Text)
    
    # 结果
    output_path = Column(String(500))
    file_size = Column(Integer)                 # 字节
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Celery任务ID
    celery_task_id = Column(String(255))

class ProxyFile(Base):
    """代理文件表"""
    __tablename__ = "proxy_files"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    proxy_path = Column(String(500), nullable=False)
    resolution = Column(String(20), default='480p')  # 代理文件分辨率
    file_size = Column(Integer)                      # 字节
    status = Column(String(50), default='completed') # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 视频分析日志系统模型

class AnalysisLog(Base):
    """分析日志表"""
    __tablename__ = "analysis_logs"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    analysis_type = Column(String(50), nullable=False)  # video_processing, audio_transcription, tag_generation, vector_embedding
    status = Column(String(50), default='started')      # started, processing, completed, failed
    progress = Column(Float, default=0.0)               # 0.0-100.0
    
    # 分析步骤和结果
    steps = Column(JSON)                                 # 分析步骤列表
    current_step = Column(String(100))                   # 当前步骤
    results = Column(JSON)                               # 分析结果
    error_message = Column(Text)                         # 错误信息
    
    # 性能指标
    duration = Column(Float)                             # 总耗时（秒）
    file_size = Column(Integer)                          # 文件大小（字节）
    processing_speed = Column(Float)                     # 处理速度（MB/s）
    
    # 时间戳
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutoTagTask(Base):
    """自动打标任务表"""
    __tablename__ = "auto_tag_tasks"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)           # 任务名称
    description = Column(Text)                           # 任务描述
    
    # 任务配置
    target_assets = Column(JSON)                         # 目标素材ID列表
    tag_types = Column(JSON)                             # 要生成的标签类型
    force_reprocess = Column(Integer, default=0)         # 是否强制重新处理
    
    # 任务状态
    status = Column(String(50), default='pending')       # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)                # 0.0-100.0
    processed_count = Column(Integer, default=0)         # 已处理数量
    total_count = Column(Integer, default=0)             # 总数量
    failed_count = Column(Integer, default=0)            # 失败数量
    
    # 结果统计
    results_summary = Column(JSON)                       # 结果摘要
    error_message = Column(Text)                         # 错误信息
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(String(100))                     # 创建者

# 图片处理系统模型

class ImageAsset(Base):
    """图片资产表"""
    __tablename__ = "image_assets"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)  # 外键关联到projects表
    
    # 文件信息
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    mime_type = Column(String(100))
    file_size = Column(Integer)  # 字节
    width = Column(Integer)
    height = Column(Integer)
    
    # AI分析结果
    description = Column(Text)  # AI生成的图片描述
    tags = Column(JSON)  # {"objects": [], "scenes": [], "emotions": [], "styles": []}
    color_palette = Column(JSON)  # {"dominant": "#FF0000", "palette": ["#FF0000", ...]}
    
    # 处理状态
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Float, default=0.0)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ImageVector(Base):
    """图片向量表"""
    __tablename__ = "image_vectors"
    
    id = Column(String, primary_key=True)
    image_id = Column(String, nullable=False)  # 外键关联到image_assets表
    
    # 向量信息
    vector_type = Column(String(50), nullable=False)  # 'clip', 'description'
    vector_data = Column(Text, nullable=False)  # JSON格式存储向量数据
    content_text = Column(Text)  # 对应的文本内容
    
    # 元数据
    model_version = Column(String(100))  # 使用的模型版本
    confidence_score = Column(Float)  # 置信度评分
    vector_dimension = Column(Integer, default=512)  # 向量维度
    
    created_at = Column(DateTime, default=datetime.utcnow)

# 数据库初始化
def init_database():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

# 数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()