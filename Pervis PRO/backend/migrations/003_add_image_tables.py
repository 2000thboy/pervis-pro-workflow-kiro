#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加图片处理相关表
版本: 003
创建时间: 2024-12-18
描述: 为PreVis PRO添加图片识别和RAG功能的数据库表
"""

import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text, Column, String, Integer, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import Base, engine, SessionLocal
    print("✅ 成功导入现有数据库配置")
except ImportError as e:
    print(f"❌ 导入数据库配置失败: {e}")
    print("请确保在backend目录下运行此脚本")
    sys.exit(1)

# 定义新的表结构
class ImageAsset(Base):
    """图片资产表"""
    __tablename__ = "image_assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False)  # 外键关联到projects表
    
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ImageVector(Base):
    """图片向量表"""
    __tablename__ = "image_vectors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String(36), nullable=False)  # 外键关联到image_assets表
    
    # 向量信息
    vector_type = Column(String(50), nullable=False)  # 'clip', 'description'
    vector_data = Column(Text, nullable=False)  # JSON格式存储向量数据
    content_text = Column(Text)  # 对应的文本内容
    
    # 元数据
    model_version = Column(String(100))  # 使用的模型版本
    confidence_score = Column(Float)  # 置信度评分
    vector_dimension = Column(Integer, default=512)  # 向量维度
    
    created_at = Column(DateTime, default=datetime.utcnow)

def upgrade():
    """升级数据库 - 创建新表"""
    print("🚀 开始升级数据库...")
    
    try:
        # 创建所有新表
        print("📝 创建image_assets表...")
        ImageAsset.__table__.create(engine, checkfirst=True)
        print("✅ image_assets表创建成功")
        
        print("📝 创建image_vectors表...")
        ImageVector.__table__.create(engine, checkfirst=True)
        print("✅ image_vectors表创建成功")
        
        # 创建索引
        print("📝 创建数据库索引...")
        with engine.connect() as conn:
            # 为image_assets创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_image_assets_project_id 
                ON image_assets(project_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_image_assets_status 
                ON image_assets(processing_status)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_image_assets_created 
                ON image_assets(created_at)
            """))
            
            # 为image_vectors创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_image_vectors_image_id 
                ON image_vectors(image_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_image_vectors_type 
                ON image_vectors(vector_type)
            """))
            
            conn.commit()
        
        print("✅ 数据库索引创建成功")
        print("🎉 数据库升级完成!")
        
    except Exception as e:
        print(f"❌ 数据库升级失败: {e}")
        raise

def downgrade():
    """降级数据库 - 删除表"""
    print("⬇️ 开始降级数据库...")
    
    try:
        # 删除索引
        print("📝 删除数据库索引...")
        with engine.connect() as conn:
            conn.execute(text("DROP INDEX IF EXISTS idx_image_vectors_type"))
            conn.execute(text("DROP INDEX IF EXISTS idx_image_vectors_image_id"))
            conn.execute(text("DROP INDEX IF EXISTS idx_image_assets_created"))
            conn.execute(text("DROP INDEX IF EXISTS idx_image_assets_status"))
            conn.execute(text("DROP INDEX IF EXISTS idx_image_assets_project_id"))
            conn.commit()
        
        print("✅ 数据库索引删除成功")
        
        # 删除表（注意顺序，先删除依赖表）
        print("📝 删除image_vectors表...")
        ImageVector.__table__.drop(engine, checkfirst=True)
        print("✅ image_vectors表删除成功")
        
        print("📝 删除image_assets表...")
        ImageAsset.__table__.drop(engine, checkfirst=True)
        print("✅ image_assets表删除成功")
        
        print("🎉 数据库降级完成!")
        
    except Exception as e:
        print(f"❌ 数据库降级失败: {e}")
        raise

def test_tables():
    """测试表创建和基本操作"""
    print("🧪 开始测试数据库表...")
    
    db = SessionLocal()
    
    try:
        # 测试ImageAsset表
        print("📝 测试ImageAsset表...")
        test_image = ImageAsset(
            project_id="test_project_123",
            filename="test_image.jpg",
            original_path="/storage/images/originals/test_image.jpg",
            thumbnail_path="/storage/images/thumbnails/test_image_thumb.jpg",
            mime_type="image/jpeg",
            file_size=1024000,
            width=1920,
            height=1080,
            description="测试图片描述",
            tags={
                "objects": ["建筑", "天空"],
                "scenes": ["城市", "白天"],
                "emotions": ["平静", "现代"],
                "styles": ["摄影", "现实主义"]
            },
            color_palette={
                "dominant": "#4A90E2",
                "palette": ["#4A90E2", "#F5A623", "#7ED321"]
            },
            processing_status="completed"
        )
        
        db.add(test_image)
        db.commit()
        print(f"✅ ImageAsset记录创建成功: {test_image.id}")
        
        # 测试ImageVector表
        print("📝 测试ImageVector表...")
        test_vector = ImageVector(
            image_id=test_image.id,
            vector_type="clip",
            vector_data="[0.1, 0.2, 0.3, 0.4, 0.5]",  # 简化的向量数据
            content_text="城市建筑天空现代摄影",
            model_version="ViT-B/32",
            confidence_score=0.95,
            vector_dimension=512
        )
        
        db.add(test_vector)
        db.commit()
        print(f"✅ ImageVector记录创建成功: {test_vector.id}")
        
        # 测试查询
        print("📝 测试数据查询...")
        
        # 查询图片资产
        images = db.query(ImageAsset).filter(ImageAsset.project_id == "test_project_123").all()
        print(f"✅ 查询到 {len(images)} 个图片资产")
        
        # 查询向量数据
        vectors = db.query(ImageVector).filter(ImageVector.image_id == test_image.id).all()
        print(f"✅ 查询到 {len(vectors)} 个向量记录")
        
        # 测试JSON字段
        if test_image.tags:
            print(f"✅ JSON标签字段正常: {len(test_image.tags)} 个标签类型")
        
        if test_image.color_palette:
            print(f"✅ JSON色彩字段正常: 主色调 {test_image.color_palette.get('dominant')}")
        
        # 清理测试数据
        print("📝 清理测试数据...")
        db.delete(test_vector)
        db.delete(test_image)
        db.commit()
        print("✅ 测试数据清理完成")
        
        print("🎉 所有测试通过!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def show_table_info():
    """显示表结构信息"""
    print("📊 数据库表结构信息:")
    print()
    
    print("🖼️ ImageAsset表字段:")
    print("   - id: 主键 (UUID)")
    print("   - project_id: 项目ID")
    print("   - filename: 文件名")
    print("   - original_path: 原始文件路径")
    print("   - thumbnail_path: 缩略图路径")
    print("   - mime_type: MIME类型")
    print("   - file_size: 文件大小(字节)")
    print("   - width, height: 图片尺寸")
    print("   - description: AI生成描述")
    print("   - tags: JSON标签数据")
    print("   - color_palette: JSON色彩数据")
    print("   - processing_status: 处理状态")
    print("   - processing_progress: 处理进度")
    print("   - error_message: 错误信息")
    print("   - created_at, updated_at: 时间戳")
    print()
    
    print("🔢 ImageVector表字段:")
    print("   - id: 主键 (UUID)")
    print("   - image_id: 关联图片ID")
    print("   - vector_type: 向量类型 (clip/description)")
    print("   - vector_data: 向量数据 (JSON)")
    print("   - content_text: 对应文本内容")
    print("   - model_version: 模型版本")
    print("   - confidence_score: 置信度")
    print("   - vector_dimension: 向量维度")
    print("   - created_at: 创建时间")
    print()
    
    print("📈 数据库索引:")
    print("   - idx_image_assets_project_id: 项目ID索引")
    print("   - idx_image_assets_status: 处理状态索引")
    print("   - idx_image_assets_created: 创建时间索引")
    print("   - idx_image_vectors_image_id: 图片ID索引")
    print("   - idx_image_vectors_type: 向量类型索引")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python 003_add_image_tables.py [upgrade|downgrade|test|info]")
        print()
        print("命令说明:")
        print("  upgrade   - 升级数据库，创建新表")
        print("  downgrade - 降级数据库，删除表")
        print("  test      - 测试表创建和基本操作")
        print("  info      - 显示表结构信息")
        return
    
    command = sys.argv[1].lower()
    
    print("=" * 60)
    print("🎬 PreVis PRO - 图片处理数据库迁移")
    print("=" * 60)
    
    try:
        if command == "upgrade":
            upgrade()
        elif command == "downgrade":
            downgrade()
        elif command == "test":
            test_tables()
        elif command == "info":
            show_table_info()
        else:
            print(f"❌ 未知命令: {command}")
            print("支持的命令: upgrade, downgrade, test, info")
            return
            
    except Exception as e:
        print(f"💥 操作失败: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ 操作完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
