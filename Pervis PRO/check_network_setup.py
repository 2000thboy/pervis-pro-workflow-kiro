#!/usr/bin/env python3
"""
检查网络盘符设置
"""

import os
from pathlib import Path

def check_network_setup():
    """检查网络盘符设置"""
    print("🔍 检查网络盘符设置...")
    
    # 1. 检查配置文件
    env_file = Path(".env")
    if env_file.exists():
        print("✅ 配置文件存在")
        with open(env_file, 'r', encoding='utf-8') as f:
            config = f.read()
            print("📄 配置内容:")
            for line in config.strip().split('\n'):
                print(f"   {line}")
    else:
        print("❌ 配置文件不存在")
        return False
    
    # 2. 检查L盘目录结构
    print("\n📁 检查目录结构:")
    
    required_dirs = [
        "L:\\PreVis_Assets",
        "L:\\PreVis_Assets\\originals",
        "L:\\PreVis_Assets\\proxies",
        "L:\\PreVis_Assets\\thumbnails", 
        "L:\\PreVis_Assets\\audio",
        "L:\\PreVis_Storage",
        "L:\\PreVis_Storage\\renders",
        "L:\\PreVis_Storage\\exports",
        "L:\\PreVis_Storage\\temp"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path}")
            all_good = False
    
    # 3. 检查素材文件
    print("\n🎬 检查素材文件:")
    originals_path = Path("L:\\PreVis_Assets\\originals")
    
    if originals_path.exists():
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        video_files = []
        
        for file_path in originals_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                video_files.append(file_path)
        
        print(f"   📹 找到 {len(video_files)} 个视频文件")
        
        # 显示前5个文件
        for i, file_path in enumerate(video_files[:5]):
            size_mb = file_path.stat().st_size / (1024 * 1024)
            rel_path = file_path.relative_to(originals_path)
            print(f"      {i+1}. {rel_path} ({size_mb:.1f} MB)")
        
        if len(video_files) > 5:
            print(f"      ... 还有 {len(video_files) - 5} 个文件")
    else:
        print("   ❌ 素材目录不存在")
        all_good = False
    
    # 4. 检查处理后的文件
    print("\n🔄 检查处理后的文件:")
    
    proxies_path = Path("L:\\PreVis_Assets\\proxies")
    thumbnails_path = Path("L:\\PreVis_Assets\\thumbnails")
    audio_path = Path("L:\\PreVis_Assets\\audio")
    
    proxy_count = len(list(proxies_path.glob('*.mp4'))) if proxies_path.exists() else 0
    thumb_count = len(list(thumbnails_path.glob('*.jpg'))) if thumbnails_path.exists() else 0
    audio_count = len(list(audio_path.glob('*.wav'))) if audio_path.exists() else 0
    
    print(f"   📹 代理文件: {proxy_count} 个")
    print(f"   🖼️  缩略图: {thumb_count} 个")
    print(f"   🎵 音频文件: {audio_count} 个")
    
    # 5. 总结
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 网络盘符配置完整！")
        print("\n📋 下一步:")
        print("   1. 启动PreVis PRO: python 快速启动PreVis_PRO.py")
        print("   2. 打开Web界面上传素材")
        print("   3. 系统会自动处理并生成代理文件")
        
        if len(video_files) > 0:
            print(f"\n💡 你已经有 {len(video_files)} 个视频文件在素材库中")
            print("   可以通过PreVis PRO Web界面进行批量处理")
    else:
        print("⚠️  配置不完整，请检查上述问题")
    
    return all_good

if __name__ == "__main__":
    print("=" * 50)
    print("PreVis PRO 网络盘符设置检查")
    print("=" * 50)
    check_network_setup()