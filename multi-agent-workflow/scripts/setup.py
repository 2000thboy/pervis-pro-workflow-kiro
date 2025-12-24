#!/usr/bin/env python3
"""
项目环境设置脚本
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, cwd=None):
    """运行命令"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"命令执行成功: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.stderr}")
        return False


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("错误: 需要Python 3.9或更高版本")
        return False
    print(f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True


def check_node_version():
    """检查Node.js版本"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f"Node.js版本: {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到Node.js，请先安装Node.js")
        return False


def setup_backend():
    """设置后端环境"""
    print("\n=== 设置后端环境 ===")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("错误: backend目录不存在")
        return False
    
    # 创建虚拟环境
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        if not run_command("python -m venv venv", cwd=backend_dir):
            return False
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_cmd = str(venv_dir / "Scripts" / "pip")
    else:  # Unix/Linux/macOS
        pip_cmd = str(venv_dir / "bin" / "pip")
    
    if not run_command(f"{pip_cmd} install --upgrade pip", cwd=backend_dir):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=backend_dir):
        return False
    
    print("后端环境设置完成")
    return True


def setup_frontend():
    """设置前端环境"""
    print("\n=== 设置前端环境 ===")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("错误: frontend目录不存在")
        return False
    
    # 安装npm依赖
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    print("前端环境设置完成")
    return True


def setup_launcher():
    """设置启动器环境"""
    print("\n=== 设置启动器环境 ===")
    
    launcher_dir = Path("launcher")
    if not launcher_dir.exists():
        print("错误: launcher目录不存在")
        return False
    
    # 创建虚拟环境
    venv_dir = launcher_dir / "venv"
    if not venv_dir.exists():
        if not run_command("python -m venv venv", cwd=launcher_dir):
            return False
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_cmd = str(venv_dir / "Scripts" / "pip")
    else:  # Unix/Linux/macOS
        pip_cmd = str(venv_dir / "bin" / "pip")
    
    if not run_command(f"{pip_cmd} install --upgrade pip", cwd=launcher_dir):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", cwd=launcher_dir):
        return False
    
    print("启动器环境设置完成")
    return True


def create_env_file():
    """创建环境配置文件"""
    print("\n=== 创建环境配置文件 ===")
    
    backend_dir = Path("backend")
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print(f"已创建环境配置文件: {env_file}")
        print("请根据实际情况修改 .env 文件中的配置")
    else:
        print("环境配置文件已存在或模板文件不存在")


def main():
    """主函数"""
    print("多Agent协作工作流系统环境设置")
    print("=" * 50)
    
    # 检查系统要求
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    # 设置各个组件
    success = True
    
    success &= setup_backend()
    success &= setup_frontend()
    success &= setup_launcher()
    
    create_env_file()
    
    if success:
        print("\n" + "=" * 50)
        print("环境设置完成！")
        print("\n下一步:")
        print("1. 修改 backend/.env 文件中的数据库配置")
        print("2. 启动PostgreSQL和Redis服务")
        print("3. 运行 python scripts/init_db.py 初始化数据库")
        print("4. 启动各个服务:")
        print("   - 后端: cd backend && python main.py")
        print("   - 前端: cd frontend && npm start")
        print("   - 启动器: cd launcher && python src/main.py")
    else:
        print("\n环境设置过程中出现错误，请检查上述输出")
        sys.exit(1)


if __name__ == "__main__":
    main()