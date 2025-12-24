#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

# 获取最新的clips
clips_result = db.execute(
    text("SELECT id, timeline_id, asset_id, start_time, end_time, created_at FROM clips ORDER BY created_at DESC LIMIT 5")
).fetchall()

print(f"最新的 {len(clips_result)} 个clips:")
for clip in clips_result:
    clip_id, timeline_id, asset_id, start_time, end_time, created_at = clip
    print(f"  {clip_id}: timeline={timeline_id}, asset={asset_id}, {start_time}s-{end_time}s, {created_at}")
    
    # 检查asset是否存在
    asset_result = db.execute(
        text("SELECT filename, file_path FROM assets WHERE id = :asset_id"),
        {"asset_id": asset_id}
    ).fetchone()
    
    if asset_result:
        print(f"    ✅ 素材存在: {asset_result[0]} -> {asset_result[1]}")
    else:
        print(f"    ❌ 素材不存在: {asset_id}")

db.close()