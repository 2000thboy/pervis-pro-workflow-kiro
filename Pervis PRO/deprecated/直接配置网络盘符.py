#!/usr/bin/env python3
"""
直接配置网络盘符 - 无需用户输入
"""

import os
import sys
from pathlib import Path

def direct_network_drive_setup():
    """直接设置网络盘符配置"""
    print("🔧 开始配置网络盘符...")
    
    # 检查L盘是否存在
    l_drive = Path("L:\\")
    if not l_drive.exists():
        print("❌ L盘不存在或无法访问")
        return False
    
    print(f"✅ L盘存在: {l_drive}")
    
    try:
        # 创建PreVis_Assets目录结构
        print("📁 创建 PreVis_Assets 目录结构...")
        assets_dirs = [
            Path("L:\\PreVis_Assets\\originals"),
            Path("L:\\PreVis_Assets\\proxies"),
            Path("L:\\PreVis_Assets\\thumbnails"),
            Path("L:\\PreVis_Assets\\audio")
        ]
        
        for directory in assets_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 创建: {directory}")
        
        # 创建PreVis_Storage目录结构
        print("📁 创建 PreVis_Storage 目录结构...")
        storage_dirs = [
            Path("L:\\PreVis_Storage\\renders"),
            Path("L:\\PreVis_Storage\\exports"),
            Path("L:\\PreVis_Storage\\temp")
        ]
        
        for directory in storage_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 创建: {directory}")
        
        # 创建配置文件
        print("📄 创建配置文件...")
        config_content = """ASSET_ROOT=L:\\PreVis_Assets
STORAGE_ROOT=L:\\PreVis_Storage
DATABASE_URL=sqlite:///./pervis_director.db
NETWORK_DRIVE=L
NETWORK_DRIVE_NAME=影片参考"""
        
        with open(".env", "w", encoding='utf-8') as f:
            f.write(config_content)
        print(f"  ✅ 创建配置文件: .env")
        
        # 测试写入权限
        print("🔍 测试写入权限...")
        test_file = Path("L:\\PreVis_Assets\\test_write.tmp")
        
        try:
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink()  # 删除测试文件
            print("  ✅ L盘写入权限正常")
        except Exception as e:
            print(f"  ❌ L盘写入权限测试失败: {e}")
            return False
        
        print("\n🎉 网络盘符配置完成！")
        print("\n📋 配置摘要:")
        print(f"素材库: L:\\PreVis_Assets")
        print(f"存储库: L:\\PreVis_Storage")
        print(f"配置文件: .env")
        
        print("\n📁 目录结构:")
        print("L:\\PreVis_Assets\\")
        print("├── originals\\          # 原始视频文件")
        print("├── proxies\\            # 代理文件")
        print("├── thumbnails\\         # 缩略图")
        print("└── audio\\              # 音频文件")
        print("")
        print("L:\\PreVis_Storage\\")
        print("├── renders\\            # 渲染输出")
        print("├── exports\\            # 导出文件")
        print("└── temp\\               # 临时文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PreVis PRO 网络盘符配置")
    print("=" * 60)
    
    success = direct_network_drive_setup()
    
    if success:
        print("\n🔍 验证配置...")
        
        # 验证配置
        required_dirs = [
            "L:\\PreVis_Assets\\originals",
            "L:\\PreVis_Assets\\proxies", 
            "L:\\PreVis_Assets\\thumbnails",
            "L:\\PreVis_Assets\\audio",
            "L:\\PreVis_Storage\\renders",
            "L:\\PreVis_Storage\\exports",
            "L:\\PreVis_Storage\\temp"
        ]
        
        all_good = True
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                print(f"  ✅ {dir_path}")
            else:
                print(f"  ❌ {dir_path}")
                all_good = False
        
        if Path(".env").exists():
            print(f"  ✅ .env 配置文件")
        else:
            print(f"  ❌ .env 配置文件")
            all_good = False
        
        if all_good:
            print("\n🎉 配置验证通过！现在可以:")
            print("• 将视频文件放入 L:\\PreVis_Assets\\originals\\")
            print("• 重启 PreVis PRO 以应用新配置")
        else:
            print("\n⚠️  配置验证失败")
    else:
        print("\n❌ 配置失败")