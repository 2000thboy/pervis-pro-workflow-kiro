#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

db = next(get_db())

# 获取最新的时间轴
timeline_result = db.execute(text("SELECT id, name FROM timelines ORDER BY created_at DESC LIMIT 1")).fetchone()

if timeline_result:
    timeline_id = timeline_result[0]
    print(f"最新时间轴: {timeline_id} - {timeline_result[1]}")
    
    # 获取时间轴的片段
    clips_result = db.execute(
        text("SELECT id, asset_id, start_time, end_time FROM clips WHERE timeline_id = :timeline_id"),
        {"timeline_id": timeline_id}
    ).fetchall()
    
    print(f"包含 {len(clips_result)} 个片段:")
    for clip in clips_result:
        clip_id, asset_id, start_time, end_time = clip
        
        # 检查asset是否存在
        asset_result = db.execute(
            text("SELECT filename, file_path FROM assets WHERE id = :asset_id"),
            {"asset_id": asset_id}
        ).fetchone()
        
        if asset_result:
            print(f"  片段 {clip_id}: {start_time}s-{end_time}s")
            print(f"    素材: {asset_id} -> {asset_result[0]} ({asset_result[1]})")
        else:
            print(f"  片段 {clip_id}: {start_time}s-{end_time}s")
            print(f"    ❌ 素材不存在: {asset_id}")
else:
    print("没有找到时间轴")

db.close()