#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加视频编辑系统表
迁移编号: 002
创建时间: 2024-12-18
描述: 添加Timeline, Clip, RenderTask, ProxyFile表
"""

from sqlalchemy import create_engine, text
import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_URL, Base, Timeline, Clip, RenderTask, ProxyFile

def upgrade():
    """执行迁移 - 创建新表"""
    print("开始迁移: 添加视频编辑系统表...")
    
    engine = create_engine(DATABASE_URL)
    
    # 创建新表
    print("创建Timeline表...")
    Timeline.__table__.create(engine, checkfirst=True)
    
    print("创建Clip表...")
    Clip.__table__.create(engine, checkfirst=True)
    
    print("创建RenderTask表...")
    RenderTask.__table__.create(engine, checkfirst=True)
    
    print("创建ProxyFile表...")
    ProxyFile.__table__.create(engine, checkfirst=True)
    
    print("✅ 迁移完成！")
    
    # 验证表是否创建成功
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('timelines', 'clips', 'render_tasks', 'proxy_files')"
        ))
        tables = [row[0] for row in result]
        
        print(f"\n已创建的表: {', '.join(tables)}")
        
        if len(tables) == 4:
            print("✅ 所有表创建成功！")
        else:
            print(f"⚠️ 警告: 只创建了 {len(tables)}/4 个表")

def downgrade():
    """回滚迁移 - 删除表"""
    print("开始回滚: 删除视频编辑系统表...")
    
    engine = create_engine(DATABASE_URL)
    
    # 删除表（按依赖顺序）
    print("删除Clip表...")
    Clip.__table__.drop(engine, checkfirst=True)
    
    print("删除RenderTask表...")
    RenderTask.__table__.drop(engine, checkfirst=True)
    
    print("删除ProxyFile表...")
    ProxyFile.__table__.drop(engine, checkfirst=True)
    
    print("删除Timeline表...")
    Timeline.__table__.drop(engine, checkfirst=True)
    
    print("✅ 回滚完成！")

def test_migration():
    """测试迁移"""
    print("\n测试迁移...")
    
    from database import SessionLocal
    from datetime import datetime
    import uuid
    
    db = SessionLocal()
    
    try:
        # 测试创建Timeline
        timeline_id = str(uuid.uuid4())
        timeline = Timeline(
            id=timeline_id,
            project_id="test_project",
            name="测试时间轴",
            duration=0.0
        )
        db.add(timeline)
        db.commit()
        print("✅ Timeline表测试通过")
        
        # 测试创建Clip
        clip_id = str(uuid.uuid4())
        clip = Clip(
            id=clip_id,
            timeline_id=timeline_id,
            asset_id="test_asset",
            start_time=0.0,
            end_time=5.0,
            order_index=0
        )
        db.add(clip)
        db.commit()
        print("✅ Clip表测试通过")
        
        # 测试创建RenderTask
        task_id = str(uuid.uuid4())
        task = RenderTask(
            id=task_id,
            timeline_id=timeline_id,
            format='mp4',
            resolution='1080p',
            status='pending'
        )
        db.add(task)
        db.commit()
        print("✅ RenderTask表测试通过")
        
        # 测试创建ProxyFile
        proxy_id = str(uuid.uuid4())
        proxy = ProxyFile(
            id=proxy_id,
            asset_id="test_asset",
            proxy_path="/path/to/proxy.mp4",
            resolution='480p'
        )
        db.add(proxy)
        db.commit()
        print("✅ ProxyFile表测试通过")
        
        # 清理测试数据
        db.delete(proxy)
        db.delete(task)
        db.delete(clip)
        db.delete(timeline)
        db.commit()
        print("✅ 测试数据清理完成")
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='视频编辑系统数据库迁移')
    parser.add_argument('action', choices=['upgrade', 'downgrade', 'test'], 
                       help='迁移操作: upgrade(升级), downgrade(回滚), test(测试)')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        upgrade()
    elif args.action == 'downgrade':
        downgrade()
    elif args.action == 'test':
        upgrade()
        test_migration()

