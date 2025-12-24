#!/usr/bin/env python3
"""
创建PreVis PRO桌面快捷方式
"""

import os
import sys
from pathlib import Path

def create_desktop_shortcut():
    """创建桌面快捷方式"""
    try:
        # 获取当前目录
        current_dir = Path.cwd()
        
        # 获取桌面路径
        if sys.platform == "win32":
            import winshell
            desktop = winshell.desktop()
            
            # 创建快捷方式
            shortcut_path = Path(desktop) / "PreVis PRO.lnk"
            
            with winshell.shortcut(str(shortcut_path)) as link:
                link.path = sys.executable
                link.arguments = f'"{current_dir / "启动_Pervis_PRO.py"}"'
                link.description = "PreVis PRO - 导演的智能创意助手"
                link.working_directory = str(current_dir)
                
            print("✅ 桌面快捷方式创建成功！")
            print(f"📍 位置: {shortcut_path}")
            
        else:
            # Linux/Mac 创建 .desktop 文件
            desktop_dir = Path.home() / "Desktop"
            if not desktop_dir.exists():
                desktop_dir = Path.home()
            
            desktop_file = desktop_dir / "PreVis PRO.desktop"
            
            content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=PreVis PRO
Comment=导演的智能创意助手
Exec=python3 "{current_dir}/中文启动器.py"
Icon={current_dir}/icon.png
Path={current_dir}
Terminal=false
Categories=AudioVideo;Video;
"""
            
            with open(desktop_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 设置可执行权限
            os.chmod(desktop_file, 0o755)
            
            print("✅ 桌面快捷方式创建成功！")
            print(f"📍 位置: {desktop_file}")
            
    except ImportError:
        print("❌ 需要安装 winshell 库")
        print("请运行: pip install winshell")
    except Exception as e:
        print(f"❌ 创建快捷方式失败: {e}")

def main():
    """主函数"""
    print("🎬 PreVis PRO 桌面快捷方式创建工具")
    print("=" * 40)
    
    create_desktop_shortcut()
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()