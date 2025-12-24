"""
数据库迁移脚本 - 添加分析日志表
创建AnalysisLog和AutoTagTask表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base, AnalysisLog, AutoTagTask
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """升级：创建分析日志表"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # 创建表
        AnalysisLog.__table__.create(engine, checkfirst=True)
        AutoTagTask.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ 分析日志表创建成功")
        logger.info("  - analysis_logs")
        logger.info("  - auto_tag_tasks")
        
    except Exception as e:
        logger.error(f"❌ 创建分析日志表失败: {e}")
        raise


def downgrade():
    """降级：删除分析日志表"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # 删除表
        AnalysisLog.__table__.drop(engine, checkfirst=True)
        AutoTagTask.__table__.drop(engine, checkfirst=True)
        
        logger.info("✅ 分析日志表删除成功")
        
    except Exception as e:
        logger.error(f"❌ 删除分析日志表失败: {e}")
        raise


def test():
    """测试：验证表创建和基本操作"""
    try:
        from database import SessionLocal
        import uuid
        from datetime import datetime
        
        db = SessionLocal()
        
        # 测试创建分析日志
        log = AnalysisLog(
            id=str(uuid.uuid4()),
            asset_id="test-asset",
            analysis_type="video_processing",
            status="started",
            steps=["step1", "step2"],
            current_step="step1"
        )
        db.add(log)
        
        # 测试创建自动打标任务
        task = AutoTagTask(
            id=str(uuid.uuid4()),
            name="测试任务",
            target_assets=["asset1", "asset2"],
            tag_types=["emotion", "scene"],
            total_count=2
        )
        db.add(task)
        
        db.commit()
        
        # 验证数据
        log_count = db.query(AnalysisLog).count()
        task_count = db.query(AutoTagTask).count()
        
        logger.info(f"✅ 测试通过")
        logger.info(f"  - 分析日志数量: {log_count}")
        logger.info(f"  - 自动打标任务数量: {task_count}")
        
        # 清理测试数据
        db.delete(log)
        db.delete(task)
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 003_add_analysis_log_tables.py [upgrade|downgrade|test]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upgrade":
        upgrade()
    elif command == "downgrade":
        downgrade()
    elif command == "test":
        upgrade()  # 先创建表
        test()     # 然后测试
    else:
        print("无效命令。使用: upgrade, downgrade, 或 test")
        sys.exit(1)