#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

# 检查所有表
tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
print("数据库表:")
for t in tables:
    print(f"  {t[0]}")

# 检查timelines表是否存在
if any(t[0] == 'timelines' for t in tables):
    count = db.execute(text("SELECT COUNT(*) FROM timelines")).fetchone()[0]
    print(f"\ntimelines表记录数: {count}")
else:
    print("\n❌ timelines表不存在")

# 检查clips表是否存在  
if any(t[0] == 'clips' for t in tables):
    count = db.execute(text("SELECT COUNT(*) FROM clips")).fetchone()[0]
    print(f"clips表记录数: {count}")
else:
    print("❌ clips表不存在")

db.close()