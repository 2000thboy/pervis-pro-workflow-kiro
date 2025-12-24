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

print("清理后端数据库中的无效素材...")

# 删除所有非MP4文件的记录
result1 = db.execute(text("DELETE FROM assets WHERE file_path LIKE '%.txt'"))
result2 = db.execute(text("DELETE FROM assets WHERE file_path LIKE '%.jpg'"))
result3 = db.execute(text("DELETE FROM assets WHERE filename LIKE '%.txt'"))
result4 = db.execute(text("DELETE FROM assets WHERE mime_type != 'video/mp4'"))

print(f"删除了 {result1.rowcount + result2.rowcount + result3.rowcount + result4.rowcount} 个无效素材")

# 添加正确的MP4素材
assets_dir = Path("../assets/originals")
mp4_files = list(assets_dir.glob("*.mp4"))

for mp4_file in mp4_files:
    file_path = f"assets/originals/{mp4_file.name}"
    asset_id = f"asset_{mp4_file.stem}"
    
    # 检查是否已存在
    existing = db.execute(
        text("SELECT id FROM assets WHERE id = :asset_id"),
        {"asset_id": asset_id}
    ).fetchone()
    
    if not existing:
        db.execute(
            text("""
                INSERT INTO assets (id, project_id, filename, mime_type, file_path, processing_status)
                VALUES (:id, 'test-project', :filename, 'video/mp4', :file_path, 'completed')
            """),
            {
                "id": asset_id,
                "filename": mp4_file.name,
                "file_path": file_path
            }
        )
        print(f"添加素材: {mp4_file.name}")

db.commit()

# 检查结果
result = db.execute(text("SELECT id, filename, file_path FROM assets WHERE mime_type = 'video/mp4'")).fetchall()
print(f"\n后端数据库中的有效素材 ({len(result)} 个):")
for r in result:
    print(f"  {r[0]}: {r[1]} -> {r[2]}")

db.close()
print("后端数据库清理完成")