# -*- coding: utf-8 -*-
"""
数据库迁移: 添加素材库管理表

创建表:
- asset_libraries: 素材库配置表
- project_library_mappings: 项目-素材库关联表

同时为现有 Asset 表添加 library_id 字段
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
import os

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")


def run_migration():
    """执行迁移"""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("=" * 60)
    print("数据库迁移: 添加素材库管理表")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 检查表是否已存在
        if "asset_libraries" in existing_tables:
            print("✅ asset_libraries 表已存在，跳过创建")
        else:
            print("📦 创建 asset_libraries 表...")
            conn.execute(text("""
                CREATE TABLE asset_libraries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    path VARCHAR(500) NOT NULL,
                    path_type VARCHAR(20) DEFAULT 'local',
                    network_host VARCHAR(200),
                    network_share VARCHAR(200),
                    network_username VARCHAR(100),
                    network_password VARCHAR(200),
                    is_active BOOLEAN DEFAULT 1,
                    is_default BOOLEAN DEFAULT 0,
                    is_indexed BOOLEAN DEFAULT 0,
                    total_assets INTEGER DEFAULT 0,
                    indexed_assets INTEGER DEFAULT 0,
                    total_size_bytes INTEGER DEFAULT 0,
                    last_scan_at DATETIME,
                    last_index_at DATETIME,
                    scan_subdirs BOOLEAN DEFAULT 1,
                    file_extensions JSON,
                    exclude_patterns JSON,
                    metadata JSON,
                    tags JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ asset_libraries 表创建成功")
        
        if "project_library_mappings" in existing_tables:
            print("✅ project_library_mappings 表已存在，跳过创建")
        else:
            print("📦 创建 project_library_mappings 表...")
            conn.execute(text("""
                CREATE TABLE project_library_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id VARCHAR(50) NOT NULL,
                    library_id INTEGER NOT NULL,
                    is_primary BOOLEAN DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plm_project_id ON project_library_mappings(project_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plm_library_id ON project_library_mappings(library_id)
            """))
            conn.commit()
            print("✅ project_library_mappings 表创建成功")
        
        # 检查 assets 表是否有 library_id 字段
        if "assets" in existing_tables:
            columns = [col["name"] for col in inspector.get_columns("assets")]
            if "library_id" not in columns:
                print("📦 为 assets 表添加 library_id 字段...")
                try:
                    conn.execute(text("""
                        ALTER TABLE assets ADD COLUMN library_id INTEGER
                    """))
                    conn.commit()
                    print("✅ library_id 字段添加成功")
                except Exception as e:
                    print(f"⚠️ 添加 library_id 字段失败（可能已存在）: {e}")
            else:
                print("✅ assets.library_id 字段已存在")
        
        # 从环境变量导入默认素材库
        asset_root = os.getenv("ASSET_ROOT")
        if asset_root:
            print(f"\n📁 检测到 ASSET_ROOT: {asset_root}")
            
            # 检查是否已存在
            result = conn.execute(
                text("SELECT id FROM asset_libraries WHERE path = :path"),
                {"path": asset_root}
            ).fetchone()
            
            if result:
                print("✅ 默认素材库已存在")
            else:
                print("📦 创建默认素材库...")
                path_type = "network" if "\\\\" in asset_root or ":" in asset_root else "local"
                conn.execute(text("""
                    INSERT INTO asset_libraries (name, path, path_type, is_default, is_active, tags)
                    VALUES (:name, :path, :path_type, 1, 1, :tags)
                """), {
                    "name": "主素材库",
                    "path": asset_root,
                    "path_type": path_type,
                    "tags": '["imported", "main"]'
                })
                conn.commit()
                print("✅ 默认素材库创建成功")
    
    print("\n" + "=" * 60)
    print("✅ 迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
