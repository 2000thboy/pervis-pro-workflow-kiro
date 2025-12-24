#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

# 检查特定的时间轴
# 获取最新的时间轴ID
latest_result = db.execute(text("SELECT id FROM timelines ORDER BY created_at DESC LIMIT 1")).fetchone()
if not latest_result:
    print("没有时间轴")
    db.close()
    exit()

timeline_id = latest_result[0]

timeline_result = db.execute(
    text("SELECT id, name, duration FROM timelines WHERE id = :timeline_id"),
    {"timeline_id": timeline_id}
).fetchone()

if timeline_result:
    print(f"时间轴: {timeline_result[0]} - {timeline_result[1]} ({timeline_result[2]}秒)")
    
    # 获取clips
    clips_result = db.execute(
        text("SELECT id, asset_id, start_time, end_time FROM clips WHERE timeline_id = :timeline_id ORDER BY order_index"),
        {"timeline_id": timeline_id}
    ).fetchall()
    
    print(f"包含 {len(clips_result)} 个片段:")
    for clip in clips_result:
        clip_id, asset_id, start_time, end_time = clip
        
        # 检查asset
        asset_result = db.execute(
            text("SELECT filename, file_path FROM assets WHERE id = :asset_id"),
            {"asset_id": asset_id}
        ).fetchone()
        
        if asset_result:
            print(f"  ✅ {clip_id}: {start_time}s-{end_time}s")
            print(f"     素材: {asset_id} -> {asset_result[0]} ({asset_result[1]})")
        else:
            print(f"  ❌ {clip_id}: {start_time}s-{end_time}s")
            print(f"     素材不存在: {asset_id}")
else:
    print("时间轴不存在")

db.close()