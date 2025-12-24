#!/usr/bin/env python3
"""
CLIP模型安装和修复脚本
解决Windows环境下的PyTorch DLL问题
"""

import os
import sys
import subprocess
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    logger.info(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 8:
        logger.error("需要Python 3.8或更高版本")
        return False
    
    return True

def check_system_info():
    """检查系统信息"""
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"架构: {platform.machine()}")
    logger.info(f"处理器: {platform.processor()}")
    
    return platform.system() == "Windows"

def uninstall_pytorch():
    """卸载现有的PyTorch"""
    logger.info("卸载现有的PyTorch...")
    
    packages_to_remove = [
        "torch",
        "torchvision", 
        "torchaudio",
        "clip-by-openai"
    ]
    
    for package in packages_to_remove:
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"], 
                         check=False, capture_output=True)
            logger.info(f"已卸载: {package}")
        except Exception as e:
            logger.warning(f"卸载{package}失败: {e}")

def install_pytorch_cpu():
    """安装CPU版本的PyTorch"""
    logger.info("安装CPU版本的PyTorch...")
    
    try:
        # 安装CPU版本的PyTorch
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("PyTorch CPU版本安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"PyTorch安装失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False

def install_clip():
    """安装CLIP模型"""
    logger.info("安装CLIP模型...")
    
    try:
        # 安装CLIP
        subprocess.run([sys.executable, "-m", "pip", "install", "clip-by-openai"], 
                      check=True, capture_output=True)
        logger.info("CLIP模型安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"CLIP安装失败: {e}")
        return False

def install_additional_deps():
    """安装其他依赖"""
    logger.info("安装其他依赖...")
    
    deps = [
        "pillow",
        "numpy", 
        "opencv-python",
        "sentence-transformers"
    ]
    
    for dep in deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                          check=True, capture_output=True)
            logger.info(f"已安装: {dep}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"安装{dep}失败: {e}")

def test_clip_import():
    """测试CLIP导入"""
    logger.info("测试CLIP导入...")
    
    try:
        import torch
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"CUDA可用: {torch.cuda.is_available()}")
        
        import clip
        logger.info("CLIP导入成功")
        
        # 测试加载模型
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, preprocess = clip.load("ViT-B/32", device=device)
        logger.info(f"CLIP模型加载成功，使用设备: {device}")
        
        return True
        
    except Exception as e:
        logger.error(f"CLIP测试失败: {e}")
        return False

def create_requirements_file():
    """创建requirements文件"""
    logger.info("创建requirements文件...")
    
    requirements = """# 图片处理系统依赖
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
clip-by-openai>=1.0.1
pillow>=9.0.0
numpy>=1.21.0
opencv-python>=4.5.0
sentence-transformers>=2.2.0
"""
    
    with open("requirements_image.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    logger.info("requirements_image.txt 已创建")

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🖼️ CLIP模型安装和修复工具")
    logger.info("=" * 60)
    
    # 检查环境
    if not check_python_version():
        return False
    
    is_windows = check_system_info()
    
    # 卸载现有版本
    uninstall_pytorch()
    
    # 安装CPU版本的PyTorch（避免DLL问题）
    if not install_pytorch_cpu():
        logger.error("PyTorch安装失败，请手动安装")
        return False
    
    # 安装CLIP
    if not install_clip():
        logger.error("CLIP安装失败")
        return False
    
    # 安装其他依赖
    install_additional_deps()
    
    # 创建requirements文件
    create_requirements_file()
    
    # 测试导入
    if test_clip_import():
        logger.info("🎉 CLIP模型安装和测试成功！")
        return True
    else:
        logger.error("❌ CLIP模型测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)