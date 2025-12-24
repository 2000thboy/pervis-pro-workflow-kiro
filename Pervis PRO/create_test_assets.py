#!/usr/bin/env python3
"""
创建测试素材目录和管理脚本
帮助用户设置视频编辑系统的测试环境
"""

import os
import shutil
from pathlib import Path
import sys

class TestAssetManager:
    """测试素材管理器"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_assets_dir = self.project_root / "test_assets"
        self.assets_dir = self.project_root / "assets"
        
    def create_directories(self):
        """创建必要的目录结构"""
        directories = [
            self.test_assets_dir,
            self.assets_dir / "originals",
            self.assets_dir / "proxies", 
            self.assets_dir / "thumbnails",
            self.assets_dir / "audio",
            self.project_root / "storage" / "renders",
            self.project_root / "storage" / "temp",
            self.project_root / "storage" / "proxies"
        ]
        
        print("🔧 创建目录结构...")
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory}")
        
        print("\n📁 目录结构创建完成！")
    
    def show_directory_info(self):
        """显示目录信息和使用说明"""
        print("\n" + "="*60)
        print("📹 PreVis PRO 视频测试文件存放指南")
        print("="*60)
        
        print("\n🎯 主要存放目录：")
        print(f"   📂 测试文件目录: {self.test_assets_dir}")
        print(f"   📂 正式素材目录: {self.assets_dir / 'originals'}")
        
        print("\n📋 支持的视频格式：")
        formats = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
        for fmt in formats:
            print(f"   ✅ {fmt}")
        
        print("\n🔄 文件处理流程：")
        print("   1️⃣ 将视频文件放入 test_assets/ 目录")
        print("   2️⃣ 系统自动处理并移动到 assets/originals/")
        print("   3️⃣ 自动生成代理文件到 assets/proxies/")
        print("   4️⃣ 自动生成缩略图到 assets/thumbnails/")
        
        print("\n📝 测试建议：")
        print("   • 使用较小的视频文件（<100MB）进行测试")
        print("   • 建议分辨率：1920x1080 或 1280x720")
        print("   • 建议时长：10-60秒")
        print("   • 建议格式：MP4 (H.264编码)")
    
    def copy_sample_files(self):
        """复制示例文件（如果存在）"""
        sample_sources = [
            self.project_root / "demo_projects",
            self.project_root / "MVP_DEMO_PACKAGE"
        ]
        
        copied_files = []
        
        for source_dir in sample_sources:
            if source_dir.exists():
                for file_path in source_dir.rglob("*.mp4"):
                    if file_path.stat().st_size < 50 * 1024 * 1024:  # 小于50MB
                        dest_path = self.test_assets_dir / file_path.name
                        if not dest_path.exists():
                            shutil.copy2(file_path, dest_path)
                            copied_files.append(dest_path.name)
        
        if copied_files:
            print(f"\n📋 已复制示例文件到测试目录：")
            for filename in copied_files:
                print(f"   ✅ {filename}")
        else:
            print(f"\n📋 未找到示例文件，请手动添加视频文件到：")
            print(f"   📂 {self.test_assets_dir}")
    
    def create_sample_test_files(self):
        """创建示例测试文件名列表"""
        sample_files = [
            "opening_scene.mp4",
            "chase_sequence.mp4", 
            "final_battle.mp4",
            "dialogue_scene.mp4",
            "action_montage.mp4"
        ]
        
        readme_content = f"""# 测试视频文件说明

## 📁 目录用途
此目录用于存放测试视频文件，系统会自动处理这些文件。

## 🎬 建议的测试文件
请将以下类型的视频文件放入此目录：

### 推荐文件名（可参考）：
{chr(10).join(f'- {filename}' for filename in sample_files)}

## 📋 文件要求
- **格式**: MP4, AVI, MOV, MKV 等
- **大小**: 建议 < 100MB（测试用）
- **分辨率**: 1920x1080 或 1280x720
- **时长**: 10-60秒（测试用）
- **编码**: H.264 (推荐)

## 🔄 处理流程
1. 将视频文件放入此目录
2. 运行测试脚本或启动系统
3. 系统自动处理文件：
   - 移动到 assets/originals/
   - 生成代理文件到 assets/proxies/
   - 生成缩略图到 assets/thumbnails/

## 🧪 测试命令
```bash
# 运行完整测试
python test_video_editing_complete.py

# 运行性能测试  
python test_sync_performance.py

# 检查文件处理
python create_test_assets.py --check
```

## 📞 注意事项
- 确保有足够的磁盘空间
- 首次处理可能需要较长时间
- 建议使用较小的文件进行初始测试
"""
        
        readme_path = self.test_assets_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"\n📝 已创建说明文件: {readme_path}")
    
    def check_existing_files(self):
        """检查现有文件"""
        print("\n🔍 检查现有文件...")
        
        # 检查测试目录
        test_files = list(self.test_assets_dir.glob("*.*")) if self.test_assets_dir.exists() else []
        if test_files:
            print(f"\n📂 测试目录 ({self.test_assets_dir}) 中的文件:")
            for file_path in test_files:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"   📹 {file_path.name} ({size_mb:.1f} MB)")
        else:
            print(f"\n📂 测试目录为空: {self.test_assets_dir}")
        
        # 检查正式素材目录
        original_files = list((self.assets_dir / "originals").glob("*.*")) if (self.assets_dir / "originals").exists() else []
        if original_files:
            print(f"\n📂 正式素材目录中的文件:")
            for file_path in original_files:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"   📹 {file_path.name} ({size_mb:.1f} MB)")
        else:
            print(f"\n📂 正式素材目录为空")
    
    def setup_complete_environment(self):
        """设置完整的测试环境"""
        print("🚀 设置 PreVis PRO 视频编辑测试环境")
        print("="*50)
        
        # 1. 创建目录
        self.create_directories()
        
        # 2. 复制示例文件
        self.copy_sample_files()
        
        # 3. 创建说明文件
        self.create_sample_test_files()
        
        # 4. 检查现有文件
        self.check_existing_files()
        
        # 5. 显示使用说明
        self.show_directory_info()
        
        print("\n🎉 测试环境设置完成！")
        print("\n📋 下一步操作：")
        print("   1. 将测试视频文件放入 test_assets/ 目录")
        print("   2. 运行: python test_video_editing_complete.py")
        print("   3. 或启动系统: python start_pervis.py")


def main():
    """主函数"""
    manager = TestAssetManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            manager.check_existing_files()
        elif sys.argv[1] == "--info":
            manager.show_directory_info()
        elif sys.argv[1] == "--dirs":
            manager.create_directories()
        else:
            print("用法: python create_test_assets.py [--check|--info|--dirs]")
    else:
        manager.setup_complete_environment()


if __name__ == "__main__":
    main()