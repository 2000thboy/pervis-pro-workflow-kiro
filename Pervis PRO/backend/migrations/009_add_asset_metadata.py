# -*- coding: utf-8 -*-
"""
Migration 009: 添加 AssetMetadata 表
管理素材的缓存路径和版本信息
"""

from sqlalchemy import text


def upgrade(engine):
    """执行迁移"""
    with engine.connect() as conn:
        # 创建 asset_metadata 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asset_metadata (
                id VARCHAR(36) PRIMARY KEY,
                asset_id VARCHAR(36) NOT NULL,
                original_path TEXT,
                original_size INTEGER,
                original_hash VARCHAR(64),
                thumbnail_path TEXT,
                thumbnail_size INTEGER,
                thumbnail_generated_at DATETIME,
                proxy_path TEXT,
                proxy_size INTEGER,
                proxy_resolution VARCHAR(20),
                proxy_generated_at DATETIME,
                cache_version INTEGER DEFAULT 1,
                last_verified_at DATETIME,
                is_available BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_asset_metadata_asset_id 
            ON asset_metadata(asset_id)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_asset_metadata_is_available 
            ON asset_metadata(is_available)
        """))
        
        conn.commit()
        print("✅ Migration 009: asset_metadata 表创建成功")


def downgrade(engine):
    """回滚迁移"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS asset_metadata"))
        conn.commit()
        print("✅ Migration 009: asset_metadata 表已删除")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__file__).replace("migrations/009_add_asset_metadata.py", ""))
    from database import engine
    upgrade(engine)
