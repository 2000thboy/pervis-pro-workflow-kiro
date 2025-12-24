#!/usr/bin/env python3
"""
创建 Pervis PRO 安装指导快捷方式
"""

import os
import sys
from pathlib import Path

def create_installation_shortcut():
    """创建安装指导快捷方式"""
    try:
        current_dir = Path(__file__).parent.absolute()
        
        if sys.platform == "win32":
            # Windows 创建批处理文件
            batch_content = f'''@echo off
echo ===============================================
echo     Pervis PRO 安装指导
echo ===============================================
echo.
echo 请按照以下步骤安装环境：
echo.
echo 1. 安装 Python 3.10+
echo    下载地址: https://www.python.org/downloads/
echo    重要：勾选 "Add Python to PATH"
echo.
echo 2. 安装 Node.js 18+
echo    下载地址: https://nodejs.org/
echo.
echo 3. 安装 Git
echo    下载地址: https://git-scm.com/
echo.
echo 4. 重启命令行后运行:
echo    python setup_environment.py
echo.
echo 详细说明请查看: README_安装说明.md
echo.
start "" "{current_dir}\\README_安装说明.md"
pause
'''
            
            batch_file = current_dir / "安装指导.bat"
            with open(batch_file, 'w', encoding='gbk') as f:
                f.write(batch_content)
            
            print("✅ 安装指导快捷方式创建成功！")
            print(f"📍 位置: {batch_file}")
            print("💡 双击 '安装指导.bat' 查看安装步骤")
            
        else:
            # Linux/Mac 创建 shell 脚本
            shell_content = f'''#!/bin/bash
echo "==============================================="
echo "     Pervis PRO 安装指导"
echo "==============================================="
echo ""
echo "请按照以下步骤安装环境："
echo ""
echo "1. 安装 Python 3.10+"
echo "   下载地址: https://www.python.org/downloads/"
echo ""
echo "2. 安装 Node.js 18+"
echo "   下载地址: https://nodejs.org/"
echo ""
echo "3. 安装 Git"
echo "   下载地址: https://git-scm.com/"
echo ""
echo "4. 运行安装脚本:"
echo "   python3 setup_environment.py"
echo ""
echo "详细说明请查看: README_安装说明.md"
echo ""

# 尝试打开 README 文件
if command -v xdg-open > /dev/null; then
    xdg-open "{current_dir}/README_安装说明.md"
elif command -v open > /dev/null; then
    open "{current_dir}/README_安装说明.md"
else
    echo "请手动打开 README_安装说明.md 文件"
fi

read -p "按 Enter 键退出..."
'''
            
            shell_file = current_dir / "安装指导.sh"
            with open(shell_file, 'w', encoding='utf-8') as f:
                f.write(shell_content)
            
            # 设置可执行权限
            os.chmod(shell_file, 0o755)
            
            print("✅ 安装指导快捷方式创建成功！")
            print(f"📍 位置: {shell_file}")
            print("💡 运行 './安装指导.sh' 查看安装步骤")
            
    except Exception as e:
        print(f"❌ 创建快捷方式失败: {e}")

def main():
    """主函数"""
    print("🚀 Pervis PRO 安装指导快捷方式创建工具")
    print("=" * 50)
    
    create_installation_shortcut()
    
    # 同时显示当前状态
    print("\n" + "=" * 50)
    print("📋 当前环境状态:")
    print("=" * 50)
    
    # 检查基础环境
    components = [
        ("Python", "python --version"),
        ("Node.js", "node --version"), 
        ("Git", "git --version"),
        ("FFmpeg", "ffmpeg -version")
    ]
    
    for name, cmd in components:
        try:
            result = os.system(f"{cmd} >nul 2>&1" if sys.platform == "win32" else f"{cmd} >/dev/null 2>&1")
            if result == 0:
                print(f"✅ {name} - 已安装")
            else:
                print(f"❌ {name} - 未安装")
        except:
            print(f"❌ {name} - 未安装")
    
    print("\n" + "=" * 50)
    print("📚 可用文档:")
    print("- README_安装说明.md (详细安装指南)")
    print("- 一键安装环境.md (快速安装)")
    print("- 环境安装指南.md (完整文档)")
    print("- 开始安装.txt (简要说明)")
    
    if sys.platform == "win32":
        input("\n按 Enter 键退出...")

if __name__ == "__main__":
    main()