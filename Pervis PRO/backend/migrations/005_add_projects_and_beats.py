"""
添加项目和Beats表
支持MVP完整工作流
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def upgrade(db_path: str = "pervis_director.db"):
    """升级数据库：添加项目和Beats表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                script_raw TEXT,
                logline TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建Beats表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beats (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                content TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                emotion_tags TEXT,
                scene_tags TEXT,
                duration REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_beats_project_id 
            ON beats(project_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_beats_order 
            ON beats(project_id, order_index)
        """)
        
        conn.commit()
        logger.info("✅ 项目和Beats表创建成功")
        
    except Exception as e:
        logger.error(f"❌ 数据库升级失败: {e}")
        raise
    finally:
        conn.close()

def downgrade(db_path: str = "pervis_director.db"):
    """降级数据库：删除项目和Beats表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS beats")
        cursor.execute("DROP TABLE IF EXISTS projects")
        
        conn.commit()
        logger.info("✅ 项目和Beats表删除成功")
        
    except Exception as e:
        logger.error(f"❌ 数据库降级失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # 运行升级
    upgrade()