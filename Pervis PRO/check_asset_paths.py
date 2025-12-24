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

# 检查所有素材的文件路径
result = db.execute(text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4' ORDER BY id")).fetchall()

print("素材文件路径检查:")
for r in result:
    asset_id, filename, file_path = r
    print(f"\n{asset_id}: {filename}")
    print(f"  数据库路径: {file_path}")
    
    if file_path:
        # 检查文件是否存在
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✅ 文件存在")
        else:
            print(f"  ❌ 文件不存在")
            
            # 尝试找到正确的路径
            possible_paths = [
                Path(f"../assets/originals/{filename}"),
                Path(f"assets/originals/{filename}"),
                Path(f"../assets/originals/{asset_id}.mp4"),
                Path(f"assets/originals/{asset_id}.mp4")
            ]
            
            for possible_path in possible_paths:
                if possible_path.exists():
                    print(f"  💡 正确路径应该是: {possible_path}")
                    break

db.close()