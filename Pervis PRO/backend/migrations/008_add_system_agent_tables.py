# -*- coding: utf-8 -*-
"""
数据库迁移: 添加系统 Agent 相关表

创建表:
- system_notifications: 系统通知表
- background_tasks: 后台任务表
"""

from sqlalchemy import create_engine, inspect, text
import os

# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")


def run_migration():
    """执行迁移"""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("=" * 60)
    print("数据库迁移: 添加系统 Agent 相关表")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 创建 system_notifications 表
        if "system_notifications" in existing_tables:
            print("✅ system_notifications 表已存在，跳过创建")
        else:
            print("📦 创建 system_notifications 表...")
            conn.execute(text("""
                CREATE TABLE system_notifications (
                    id VARCHAR(36) PRIMARY KEY,
                    type VARCHAR(20) NOT NULL,
                    level VARCHAR(20) NOT NULL DEFAULT 'info',
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    action JSON,
                    is_read BOOLEAN DEFAULT 0,
                    task_id VARCHAR(36),
                    agent_type VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME
                )
            """))
            
            # 创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sn_type ON system_notifications(type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sn_level ON system_notifications(level)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sn_is_read ON system_notifications(is_read)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sn_task_id ON system_notifications(task_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sn_created_at ON system_notifications(created_at)
            """))
            conn.commit()
            print("✅ system_notifications 表创建成功")
        
        # 创建 background_tasks 表
        if "background_tasks" in existing_tables:
            print("✅ background_tasks 表已存在，跳过创建")
        else:
            print("📦 创建 background_tasks 表...")
            conn.execute(text("""
                CREATE TABLE background_tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    type VARCHAR(30) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    progress INTEGER DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    details JSON,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    estimated_duration INTEGER,
                    project_id VARCHAR(36)
                )
            """))
            
            # 创建索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bt_type ON background_tasks(type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bt_status ON background_tasks(status)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bt_project_id ON background_tasks(project_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bt_created_at ON background_tasks(created_at)
            """))
            conn.commit()
            print("✅ background_tasks 表创建成功")
    
    print("\n" + "=" * 60)
    print("✅ 迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
