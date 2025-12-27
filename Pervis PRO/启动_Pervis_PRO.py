import sys
import os
import subprocess
import time

def main():
    print("🚀 Pervis PRO 启动器初始化...")
    print("--------------------------------")
    
    # 1. 自动检查并安装 UI 依赖
    try:
        import customtkinter
    except ImportError:
        print("📦 检测到缺少组件 (customtkinter)，正在自动安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
            print("✅ 安装成功！")
            import customtkinter # 验证
        except Exception as e:
            print(f"❌ 自动安装失败: {e}")
            print("请尝试手动运行: pip install customtkinter")
            input("按任意键退出...")
            return

    # 2. 设置环境路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    # 3. 启动仪表盘
    try:
        print("✅ 环境检查通过，正在启动控制中心...")
        from launcher.main import main as launcher_main
        launcher_main()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")

if __name__ == "__main__":
    main()
