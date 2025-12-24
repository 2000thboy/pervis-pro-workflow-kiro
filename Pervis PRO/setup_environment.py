#!/usr/bin/env python3
"""
Pervis PRO 环境安装脚本 (跨平台版本)
支持 Windows, macOS, Linux
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(cmd, shell=False, check=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, "命令未找到"

def check_python():
    """检查 Python 版本"""
    print("[1/7] 检查 Python 环境...")
    success, output = run_command([sys.executable, "--version"])
    if success:
        print(f"✓ 已安装: {output}")
        # 检查版本
        version_parts = output.split()[1].split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        if major < 3 or (major == 3 and minor < 10):
            print(f"⚠ 警告: Python 版本过低，建议 3.10+，当前: {output}")
        return True
    else:
        print("✗ Python 检查失败")
        return False

def check_node():
    """检查 Node.js"""
    print("\n[2/7] 检查 Node.js 环境...")
    success, output = run_command(["node", "--version"])
    if success:
        print(f"✓ 已安装: {output}")
        # 检查版本
        version = int(output[1:].split('.')[0])
        if version < 18:
            print(f"⚠ 警告: Node.js 版本过低，建议 18+，当前: {output}")
        return True
    else:
        print("✗ 未检测到 Node.js！")
        print("  请从 https://nodejs.org/ 下载并安装 Node.js 18+")
        return False

def check_ffmpeg():
    """检查 FFmpeg"""
    print("\n[3/7] 检查 FFmpeg...")
    success, output = run_command(["ffmpeg", "-version"])
    if success:
        first_line = output.split('\n')[0]
        print(f"✓ 已安装: {first_line}")
        return True
    else:
        print("⚠ 未检测到 FFmpeg（视频处理需要）")
        print("  建议安装: https://www.ffmpeg.org/download.html")
        if platform.system() == "Windows":
            print("  或使用 Chocolatey: choco install ffmpeg")
        elif platform.system() == "Darwin":
            print("  或使用 Homebrew: brew install ffmpeg")
        elif platform.system() == "Linux":
            print("  或使用包管理器: sudo apt install ffmpeg")
        return False

def setup_backend():
    """安装后端依赖"""
    print("\n[4/7] 安装后端 Python 依赖...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("✗ 未找到 backend 目录")
        return False
    
    os.chdir(backend_dir)
    
    # 创建虚拟环境
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("  检测到现有虚拟环境")
    else:
        print("  创建 Python 虚拟环境...")
        success, _ = run_command([sys.executable, "-m", "venv", "venv"])
        if not success:
            print("✗ 虚拟环境创建失败")
            return False
    
    # 激活虚拟环境并安装依赖
    print("  激活虚拟环境并安装依赖...")
    
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # 升级 pip
    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安装依赖
    success, output = run_command([str(pip_exe), "install", "-r", "requirements.txt"])
    
    os.chdir("..")
    
    if success:
        print("✓ 后端依赖安装完成")
        return True
    else:
        print("✗ 后端依赖安装失败")
        print(f"  错误: {output}")
        return False

def setup_frontend():
    """安装前端依赖"""
    print("\n[5/7] 安装前端 Node.js 依赖...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("✗ 未找到 frontend 目录")
        return False
    
    os.chdir(frontend_dir)
    
    success, output = run_command(["npm", "install"])
    
    os.chdir("..")
    
    if success:
        print("✓ 前端依赖安装完成")
        return True
    else:
        print("✗ 前端依赖安装失败")
        print(f"  错误: {output}")
        return False

def setup_launcher():
    """安装启动器依赖"""
    print("\n[6/7] 安装启动器依赖...")
    
    success, output = run_command([sys.executable, "-m", "pip", "install", 
                                  "customtkinter", "pillow"])
    
    if success:
        print("✓ 启动器依赖安装完成")
        return True
    else:
        print("✗ 启动器依赖安装失败")
        print(f"  错误: {output}")
        return False

def check_config():
    """检查配置文件"""
    print("\n[7/7] 检查配置文件...")
    
    env_file = Path("backend") / ".env"
    if env_file.exists():
        print("✓ 检测到 backend/.env 配置文件")
        return True
    else:
        print("⚠ 未找到 backend/.env 配置文件")
        print("  请配置以下环境变量:")
        print("  - GEMINI_API_KEY (Google Gemini API 密钥)")
        print("  - LLM_PROVIDER (gemini 或 local)")
        return False

def main():
    """主函数"""
    print("=" * 40)
    print("  Pervis PRO 环境安装向导")
    print("=" * 40)
    print()
    
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 检查基础环境
    python_ok = check_python()
    node_ok = check_node()
    ffmpeg_ok = check_ffmpeg()
    
    if not python_ok or not node_ok:
        print("\n✗ 基础环境检查失败，请先安装必要组件")
        return False
    
    # 安装依赖
    backend_ok = setup_backend()
    frontend_ok = setup_frontend()
    launcher_ok = setup_launcher()
    config_ok = check_config()
    
    # 总结
    print("\n" + "=" * 40)
    if backend_ok and frontend_ok and launcher_ok:
        print("  环境安装完成！")
        print("=" * 40)
        print()
        print("下一步操作:")
        print("1. 配置 backend/.env 文件（设置 API 密钥）")
        print("2. 运行启动脚本: python 启动_Pervis_PRO.py")
        print()
        print("可选安装:")
        print("- Ollama (本地 AI): https://ollama.com")
        print("- Redis (任务队列): https://redis.io/download")
        return True
    else:
        print("  环境安装遇到问题")
        print("=" * 40)
        print("请检查上述错误信息并重试")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
    except Exception as e:
        print(f"\n安装过程中出现错误: {e}")
        import traceback
        traceback.print_exc()