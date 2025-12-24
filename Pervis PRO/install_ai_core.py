import subprocess
import sys
import os

def install_dependencies():
    """
    安装 Pervis PRO 视觉内核所需的核心依赖
    """
    print("="*50)
    print("🤖 Pervis PRO AI内核 依赖安装程序")
    print("="*50)
    print("正在准备安装 PyTorch, CLIP, OpenCV...")
    print("⚠️ 注意: 这可能需要下载约 1-2GB 的数据，请确保网络通畅。")
    
    packages = [
        "torch torchvision torchaudio",  # PyTorch
        "git+https://github.com/openai/CLIP.git",  # CLIP from source
        "opencv-python",
        "pillow",
        "chromadb"  # Vector DB for memory
    ]
    
    for package in packages:
        print(f"\n📦 正在安装: {package} ...")
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if "git+" in package:
                cmd.append(package)
            else:
                cmd.extend(package.split())
                
            subprocess.check_call(cmd)
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")
            print("建议手动运行 pip install 命令尝试解决。")

    print("\n" + "="*50)
    print("🎉 所有任务执行完毕")
    print("="*50)
    # input("按回车键退出...") # Automating, so no input needed

if __name__ == "__main__":
    install_dependencies()
