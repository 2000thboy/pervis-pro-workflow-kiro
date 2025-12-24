#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

print("清理无效的clips和timelines...")

# 删除引用不存在素材的clips
result = db.execute(text("""
    DELETE FROM clips 
    WHERE asset_id NOT IN (SELECT id FROM assets)
"""))
print(f"删除了 {result.rowcount} 个无效clips")

# 删除没有clips的timelines
result = db.execute(text("""
    DELETE FROM timelines 
    WHERE id NOT IN (SELECT DISTINCT timeline_id FROM clips)
"""))
print(f"删除了 {result.rowcount} 个空timelines")

# 删除所有render_tasks（重新开始）
result = db.execute(text("DELETE FROM render_tasks"))
print(f"删除了 {result.rowcount} 个render_tasks")

db.commit()

# 检查清理结果
clips_count = db.execute(text("SELECT COUNT(*) FROM clips")).fetchone()[0]
timelines_count = db.execute(text("SELECT COUNT(*) FROM timelines")).fetchone()[0]
render_tasks_count = db.execute(text("SELECT COUNT(*) FROM render_tasks")).fetchone()[0]

print(f"\n清理后:")
print(f"  clips: {clips_count}")
print(f"  timelines: {timelines_count}")
print(f"  render_tasks: {render_tasks_count}")

db.close()
print("清理完成")