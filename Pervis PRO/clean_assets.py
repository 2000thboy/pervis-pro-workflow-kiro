#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

print("清理无效素材记录...")

# 删除所有非MP4文件的记录
db.execute(text("DELETE FROM assets WHERE file_path LIKE '%.txt'"))
db.execute(text("DELETE FROM assets WHERE file_path LIKE '%.jpg'"))
db.execute(text("DELETE FROM assets WHERE filename LIKE '%.txt'"))
db.execute(text("DELETE FROM assets WHERE mime_type != 'video/mp4'"))

db.commit()

# 检查剩余记录
result = db.execute(text("SELECT id, filename, file_path FROM assets")).fetchall()
print(f"剩余 {len(result)} 个素材记录:")
for r in result:
    print(f"  {r[0]}: {r[1]} -> {r[2]}")

db.close()
print("清理完成")