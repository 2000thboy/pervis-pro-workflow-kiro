#!/usr/bin/env python3
"""
修复测试素材数据
确保数据库记录与实际文件匹配
"""

import os
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

def fix_test_assets():
    """修复测试素材数据"""
    print("🔧 修复测试素材数据...")
    
    db = next(get_db())
    
    try:
        # 1. 清理无效的素材记录
        print("🗑️ 清理无效素材记录...")
        db.execute(text("DELETE FROM assets WHERE file_path IS NULL OR file_path = ''"))
        db.execute(text("DELETE FROM assets WHERE filename LIKE '%.txt'"))
        db.execute(text("DELETE FROM assets WHERE file_path LIKE '%.jpg'"))
        
        # 2. 检查实际存在的MP4文件
        assets_dir = Path("assets/originals")
        if not assets_dir.exists():
            print("❌ assets/originals 目录不存在")
            return False
        
        mp4_files = list(assets_dir.glob("*.mp4"))
        print(f"📁 找到 {len(mp4_files)} 个MP4文件")
        
        # 3. 为每个MP4文件创建正确的数据库记录
        for mp4_file in mp4_files:
            file_path = str(mp4_file).replace("\\", "/")
            filename = mp4_file.name
            asset_id = f"asset_{mp4_file.stem}"
            
            # 检查是否已存在
            existing = db.execute(
                text("SELECT id FROM assets WHERE file_path = :file_path"),
                {"file_path": file_path}
            ).fetchone()
            
            if not existing:
                # 插入新记录
                db.execute(
                    text("""
                        INSERT INTO assets (id, project_id, filename, mime_type, file_path, processing_status)
                        VALUES (:id, 'test-project', :filename, 'video/mp4', :file_path, 'completed')
                    """),
                    {
                        "id": asset_id,
                        "filename": filename,
                        "file_path": file_path
                    }
                )
                print(f"✅ 添加素材: {filename}")
            else:
                print(f"⏭️ 跳过已存在: {filename}")
        
        db.commit()
        
        # 4. 验证修复结果
        result = db.execute(
            text("SELECT COUNT(*) FROM assets WHERE mime_type = 'video/mp4' AND file_path IS NOT NULL")
        ).fetchone()
        
        print(f"✅ 修复完成，共有 {result[0]} 个有效视频素材")
        
        # 显示素材列表
        assets = db.execute(
            text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4' LIMIT 10")
        ).fetchall()
        
        print("\n📋 当前素材列表:")
        for asset in assets:
            print(f"  {asset[0]}: {asset[1]} -> {asset[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_test_assets()
    exit(0 if success else 1)