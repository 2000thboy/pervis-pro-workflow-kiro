"""
数据库迁移脚本 - 添加标签管理和导出功能
Migration 001: Add tag management and export features
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
Base = declarative_base()

# 新增表定义

class TagHierarchy(Base):
    """标签层级表"""
    __tablename__ = "tag_hierarchy"
    
    id = Column(String, primary_key=True)
    tag_name = Column(String(255), nullable=False)
    parent_id = Column(String, ForeignKey('tag_hierarchy.id'), nullable=True)
    level = Column(Integer, default=0)
    category = Column(String(100))  # location, time, action, emotion, visual_style, camera, color
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssetTag(Base):
    """资产标签关联表（扩展）"""
    __tablename__ = "asset_tags"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, nullable=False)
    tag_id = Column(String, ForeignKey('tag_hierarchy.id'), nullable=False)
    weight = Column(Float, default=1.0)  # 关联度权重 0.0-1.0
    order_index = Column(Integer, default=0)  # 显示顺序
    source = Column(String(50), default='auto')  # auto, manual, ai
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def upgrade():
    """执行迁移 - 创建新表"""
    print("Creating new tables for tag management and export features...")
    Base.metadata.create_all(bind=engine)
    print("Migration completed successfully!")

def downgrade():
    """回滚迁移 - 删除新表"""
    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)
    print("Rollback completed!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
