#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# 切换到backend目录，确保使用正确的数据库
import os
os.chdir(backend_dir)

from database import get_db
from sqlalchemy import text

db = next(get_db())

# 检查所有时间轴
print("所有时间轴:")
timelines = db.execute(text("SELECT id, name, created_at FROM timelines")).fetchall()
for t in timelines:
    print(f"  {t[0]}: {t[1]} ({t[2]})")

if timelines:
    # 检查最新时间轴的clips（按时间排序，最新的在最后）
    latest_timeline_id = timelines[-1][0]
    print(f"\n检查时间轴 {latest_timeline_id} 的clips:")
    
    clips = db.execute(
        text("SELECT id, asset_id, start_time, end_time FROM clips WHERE timeline_id = :timeline_id"),
        {"timeline_id": latest_timeline_id}
    ).fetchall()
    
    print(f"找到 {len(clips)} 个clips:")
    for clip in clips:
        print(f"  {clip[0]}: asset={clip[1]}, {clip[2]}s-{clip[3]}s")
        
        # 检查asset是否存在
        asset = db.execute(
            text("SELECT filename, file_path FROM assets WHERE id = :asset_id"),
            {"asset_id": clip[1]}
        ).fetchone()
        
        if asset:
            print(f"    ✅ 素材: {asset[0]} -> {asset[1]}")
        else:
            print(f"    ❌ 素材不存在: {clip[1]}")

db.close()