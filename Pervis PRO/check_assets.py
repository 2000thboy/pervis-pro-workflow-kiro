#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())
result = db.execute(text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4' LIMIT 5")).fetchall()

print("数据库中的视频素材:")
for r in result:
    print(f"{r[0]}: {r[1]} -> {r[2]}")
    # 检查文件是否存在
    file_path = Path(r[2])
    exists = file_path.exists()
    print(f"  文件存在: {exists}")
    if not exists:
        print(f"  实际路径应该是: {file_path.resolve()}")

db.close()