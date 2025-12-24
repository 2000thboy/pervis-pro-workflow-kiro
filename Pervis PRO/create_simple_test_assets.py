#!/usr/bin/env python3
"""
创建简单的测试素材
直接在数据库中创建虚拟素材记录，用于测试渲染流程
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

def create_mock_assets():
    """在数据库中创建模拟素材记录"""
    
    # 连接数据库
    db_path = "backend/pervis_director.db"
    if not Path(db_path).exists():
        print("❌ 数据库文件不存在，请先启动后端服务")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查assets表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'")
    if not cursor.fetchone():
        print("❌ assets表不存在")
        conn.close()
        return False
    
    # 创建测试素材数据
    test_assets = [
        {
            "filename": "city_street_busy.mp4",
            "duration": 8.5,
            "description": "繁忙的城市街道，人来人往，车辆川流不息",
            "tags": ["城市", "街道", "繁忙", "白天", "户外"]
        },
        {
            "filename": "office_modern_interior.mp4", 
            "duration": 6.2,
            "description": "现代化开放式办公室，阳光透过落地窗",
            "tags": ["办公室", "室内", "现代", "白天", "工作"]
        },
        {
            "filename": "person_walking_hurried.mp4",
            "duration": 4.8,
            "description": "年轻人匆忙走过，手拿咖啡，表情焦虑",
            "tags": ["人物", "行走", "匆忙", "焦虑", "咖啡"]
        },
        {
            "filename": "conversation_office_serious.mp4",
            "duration": 12.3,
            "description": "办公室对话场景，老板严肃表情",
            "tags": ["对话", "办公室", "严肃", "老板", "员工"]
        },
        {
            "filename": "close_up_face_guilty.mp4",
            "duration": 3.7,
            "description": "年轻人特写，低头愧疚表情",
            "tags": ["特写", "脸部", "愧疚", "情绪", "年轻人"]
        }
    ]
    
    created_count = 0
    
    for asset_data in test_assets:
        asset_id = str(uuid.uuid4())
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM assets WHERE filename = ?", (asset_data["filename"],))
        if cursor.fetchone():
            print(f"⏭️  跳过已存在的素材: {asset_data['filename']}")
            continue
        
        # 插入素材记录
        try:
            cursor.execute("""
                INSERT INTO assets (
                    id, project_id, filename, mime_type, source, file_path, 
                    thumbnail_path, processing_status, tags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                "test-project",
                asset_data["filename"],
                "video/mp4",
                "mock",
                f"assets/originals/{asset_data['filename']}",
                f"assets/thumbnails/{asset_id}.jpg",
                "completed",
                str(asset_data["tags"]),  # JSON字符串
                datetime.now().isoformat()
            ))
            
            # 插入标签（使用正确的表结构）
            for i, tag in enumerate(asset_data["tags"]):
                tag_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR IGNORE INTO asset_tags (id, asset_id, tag_id, weight, order_index, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), asset_id, tag_id, 0.9, i, "mock", datetime.now().isoformat()))
            
            print(f"✅ 创建素材: {asset_data['filename']} ({asset_data['duration']}秒)")
            created_count += 1
            
        except Exception as e:
            print(f"❌ 创建素材失败 {asset_data['filename']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 成功创建 {created_count} 个测试素材")
    return created_count > 0

def verify_assets():
    """验证素材是否创建成功"""
    try:
        import requests
        response = requests.get('http://localhost:8000/api/assets/search?limit=10')
        if response.status_code == 200:
            assets = response.json()
            print(f"\n📊 素材库验证:")
            print(f"   总数量: {len(assets)} 个素材")
            for asset in assets:
                print(f"   - {asset.get('filename')} ({asset.get('duration', 0):.1f}秒)")
            return len(assets) > 0
        else:
            print(f"❌ API验证失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 验证素材库失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("创建简单测试素材")
    print("=" * 50)
    
    # 创建素材目录
    assets_dir = Path("assets/originals")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    thumbnails_dir = Path("assets/thumbnails")
    thumbnails_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建模拟素材
    if create_mock_assets():
        print("\n" + "=" * 50)
        print("✅ 测试素材创建完成")
        
        # 验证
        if verify_assets():
            print("✅ 素材库验证通过")
        else:
            print("⚠️  素材库验证失败，但数据库记录已创建")
    else:
        print("\n❌ 测试素材创建失败")
    
    print("=" * 50)

if __name__ == "__main__":
    main()