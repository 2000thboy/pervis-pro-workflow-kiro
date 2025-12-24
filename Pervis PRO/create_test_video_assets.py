#!/usr/bin/env python3
"""
创建测试视频素材
使用FFmpeg生成一些简单的测试视频
"""

import os
import subprocess
import sys
from pathlib import Path

def create_test_video(output_path, duration=5, color="blue", text="Test Video"):
    """创建测试视频"""
    try:
        # 使用FFmpeg创建彩色测试视频
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color={color}:size=1280x720:duration={duration}',
            '-f', 'lavfi', 
            '-i', f'sine=frequency=440:duration={duration}',
            '-vf', f'drawtext=text=\'{text}\':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-shortest',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 创建测试视频: {output_path}")
            return True
        else:
            print(f"❌ 创建视频失败: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg未安装，无法创建测试视频")
        return False
    except Exception as e:
        print(f"❌ 创建视频异常: {e}")
        return False

def add_asset_to_database(file_path):
    """将素材添加到数据库"""
    import requests
    
    try:
        # 模拟文件上传
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
            response = requests.post(
                'http://localhost:8000/api/assets/upload',
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 素材已添加到数据库: {result.get('id')}")
            return True
        else:
            print(f"❌ 添加素材失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 添加素材异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("创建测试视频素材")
    print("=" * 50)
    
    # 创建素材目录
    assets_dir = Path("assets/originals")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试视频配置
    test_videos = [
        {
            "filename": "test_city_street.mp4",
            "duration": 8,
            "color": "blue",
            "text": "City Street Scene"
        },
        {
            "filename": "test_office_interior.mp4", 
            "duration": 6,
            "color": "green",
            "text": "Office Interior"
        },
        {
            "filename": "test_person_walking.mp4",
            "duration": 4,
            "color": "red", 
            "text": "Person Walking"
        },
        {
            "filename": "test_conversation.mp4",
            "duration": 10,
            "color": "yellow",
            "text": "Conversation Scene"
        },
        {
            "filename": "test_close_up.mp4",
            "duration": 3,
            "color": "purple",
            "text": "Close Up Shot"
        }
    ]
    
    created_count = 0
    
    for video_config in test_videos:
        output_path = assets_dir / video_config["filename"]
        
        # 如果文件已存在，跳过
        if output_path.exists():
            print(f"⏭️  跳过已存在的文件: {output_path}")
            continue
        
        # 创建视频
        if create_test_video(
            output_path,
            duration=video_config["duration"],
            color=video_config["color"],
            text=video_config["text"]
        ):
            created_count += 1
            
            # 添加到数据库
            add_asset_to_database(output_path)
    
    print("\n" + "=" * 50)
    print(f"✅ 完成！创建了 {created_count} 个测试视频")
    print(f"📁 素材位置: {assets_dir}")
    print("=" * 50)
    
    # 验证素材
    print("\n验证素材库...")
    try:
        import requests
        response = requests.get('http://localhost:8000/api/assets/search?limit=10')
        if response.status_code == 200:
            assets = response.json()
            print(f"✅ 素材库中共有 {len(assets)} 个素材")
            for asset in assets:
                print(f"   - {asset.get('filename')} ({asset.get('duration', 0):.1f}秒)")
        else:
            print("❌ 无法验证素材库")
    except Exception as e:
        print(f"❌ 验证素材库失败: {e}")

if __name__ == "__main__":
    main()