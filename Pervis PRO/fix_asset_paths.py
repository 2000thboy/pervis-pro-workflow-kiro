#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 切换到backend目录
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

print("修复素材文件路径...")

# 获取所有素材
assets = db.execute(text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4'")).fetchall()

fixed_count = 0
for asset_id, filename, file_path in assets:
    if not file_path:
        continue
    
    # 检查当前路径是否存在
    current_path = Path(file_path)
    if current_path.exists():
        continue  # 路径正确，跳过
    
    # 尝试找到正确的路径
    correct_path = None
    possible_paths = [
        Path(f"../assets/originals/{filename}"),
        Path(f"assets/originals/{filename}"),
        Path(f"../assets/originals/{asset_id}.mp4"),
        Path(f"assets/originals/{asset_id}.mp4")
    ]
    
    for possible_path in possible_paths:
        if possible_path.exists():
            correct_path = str(possible_path).replace("\\", "/")
            break
    
    if correct_path:
        # 更新数据库
        db.execute(
            text("UPDATE assets SET file_path = :new_path WHERE id = :asset_id"),
            {"new_path": correct_path, "asset_id": asset_id}
        )
        print(f"修复 {asset_id}: {file_path} -> {correct_path}")
        fixed_count += 1
    else:
        print(f"❌ 找不到文件: {asset_id} ({filename})")

db.commit()
print(f"\n修复了 {fixed_count} 个文件路径")

# 验证修复结果
print("\n验证修复结果:")
assets = db.execute(text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4' LIMIT 5")).fetchall()
for asset_id, filename, file_path in assets:
    if file_path and Path(file_path).exists():
        print(f"✅ {asset_id}: {file_path}")
    else:
        print(f"❌ {asset_id}: {file_path}")

db.close()
print("路径修复完成")