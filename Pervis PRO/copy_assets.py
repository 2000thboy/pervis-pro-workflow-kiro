
# 素材复制脚本
# 将你的动漫素材复制到项目目录

import shutil
import os
from pathlib import Path

# 源目录（你的素材目录）
SOURCE_DIR = r"F:\BaiduNetdiskDownload\动漫素材"

# 目标目录（项目assets目录）
TARGET_DIR = r"backend\assets"

def copy_video_files():
    """复制视频文件到项目目录"""
    
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 源目录不存在: {SOURCE_DIR}")
        return
    
    # 创建目标目录
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 支持的视频格式
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    copied_count = 0
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                source_path = os.path.join(root, file)
                target_path = os.path.join(TARGET_DIR, file)
                
                try:
                    shutil.copy2(source_path, target_path)
                    print(f"✅ 复制: {file}")
                    copied_count += 1
                except Exception as e:
                    print(f"❌ 复制失败 {file}: {e}")
    
    print(f"\n📊 总计复制了 {copied_count} 个视频文件")

if __name__ == "__main__":
    copy_video_files()
