#!/usr/bin/env python3
"""
Pervis PRO 完整依赖检查
检查所有必需和可选组件的安装状态
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def check_command(cmd, name):
    """检查命令行工具是否可用"""
    try:
        result = subprocess.run([cmd, "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"✓ {name}: {version}")
            return True
        else:
            print(f"❌ {name}: 命令执行失败")
            return False
    except FileNotFoundError:
        print(f"❌ {name}: 未安装")
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠ {name}: 响应超时")
        return False
    except Exception as e:
        print(f"❌ {name}: 检查失败 - {e}")
        return False

def check_python_package(package_name, display_name=None):
    """检查Python包是否已安装"""
    if display_name is None:
        display_name = package_name
    
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {display_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {display_name}: 未安装")
        return False
    except Exception as e:
        print(f"⚠ {display_name}: 检查异常 - {e}")
        return False

def check_ollama_models():
    """检查Ollama模型"""
    try:
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = result.stdout.strip()
            if "qwen2.5:14b" in models:
                print("✓ Qwen2.5:14b 模型已安装")
                return True
            elif "qwen2.5:7b" in models:
                print("✓ Qwen2.5:7b 模型已安装")
                return True
            else:
                print("⚠ 未找到推荐的Qwen模型")
                print("  可用模型:")
                for line in models.split('\n')[1:]:  # 跳过标题行
                    if line.strip():
                        print(f"    {line}")
                return False
        else:
            print("❌ Ollama 模型列表获取失败")
            return False
    except Exception as e:
        print(f"❌ Ollama 模型检查失败: {e}")
        return False

def check_project_structure():
    """检查项目结构"""
    required_dirs = [
        "backend",
        "frontend", 
        "launcher"
    ]
    
    required_files = [
        "backend/requirements.txt",
        "backend/.env",
        "frontend/package.json",
        "启动_Pervis_PRO.py"
    ]
    
    print("\n📁 项目结构检查:")
    all_good = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ {dir_name}/ 目录存在")
        else:
            print(f"❌ {dir_name}/ 目录缺失")
            all_good = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} 文件存在")
        else:
            print(f"❌ {file_path} 文件缺失")
            all_good = False
    
    return all_good

def check_backend_dependencies():
    """检查后端Python依赖"""
    print("\n🐍 后端Python依赖:")
    
    # 核心依赖
    core_deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("python_dotenv", "Python-dotenv")
    ]
    
    # AI/ML依赖
    ai_deps = [
        ("google.generativeai", "Google Generative AI"),
        ("sentence_transformers", "Sentence Transformers"),
        ("chromadb", "ChromaDB")
    ]
    
    # 视觉处理依赖
    vision_deps = [
        ("torch", "PyTorch"),
        ("clip", "OpenAI CLIP"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow")
    ]
    
    # 其他依赖
    other_deps = [
        ("ffmpeg", "FFmpeg-Python"),
        ("celery", "Celery"),
        ("redis", "Redis-py"),
        ("aiohttp", "aiohttp"),
        ("aioredis", "aioredis")
    ]
    
    results = {}
    
    print("  核心框架:")
    results['core'] = all(check_python_package(pkg, name) for pkg, name in core_deps)
    
    print("\n  AI/ML组件:")
    results['ai'] = all(check_python_package(pkg, name) for pkg, name in ai_deps)
    
    print("\n  视觉处理:")
    results['vision'] = all(check_python_package(pkg, name) for pkg, name in vision_deps)
    
    print("\n  其他组件:")
    results['other'] = all(check_python_package(pkg, name) for pkg, name in other_deps)
    
    return results

def check_frontend_dependencies():
    """检查前端依赖"""
    print("\n🌐 前端依赖:")
    
    if not os.path.exists("frontend/node_modules"):
        print("❌ node_modules 目录不存在，请运行 npm install")
        return False
    
    # 检查关键包
    key_packages = [
        "react",
        "react-dom", 
        "vite",
        "typescript"
    ]
    
    try:
        with open("frontend/package.json", "r", encoding="utf-8") as f:
            import json
            package_data = json.load(f)
            dependencies = {**package_data.get("dependencies", {}), 
                          **package_data.get("devDependencies", {})}
            
            all_good = True
            for pkg in key_packages:
                if pkg in dependencies:
                    print(f"✓ {pkg}: {dependencies[pkg]}")
                else:
                    print(f"❌ {pkg}: 未找到")
                    all_good = False
            
            return all_good
            
    except Exception as e:
        print(f"❌ package.json 读取失败: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 60)
    print("🔍 Pervis PRO 完整依赖检查")
    print("=" * 60)
    
    # 1. 基础环境检查
    print("\n🛠️ 基础环境:")
    basic_tools = [
        ("python", "Python"),
        ("node", "Node.js"),
        ("npm", "NPM"),
        ("git", "Git"),
        ("ffmpeg", "FFmpeg")
    ]
    
    basic_results = {}
    for cmd, name in basic_tools:
        basic_results[cmd] = check_command(cmd, name)
    
    # 2. 本地AI环境检查
    print("\n🤖 本地AI环境:")
    ollama_available = check_command("ollama", "Ollama")
    if ollama_available:
        models_ok = check_ollama_models()
    else:
        models_ok = False
        print("⚠ Ollama 未安装，无法使用本地AI")
    
    # 3. Redis检查
    print("\n📦 缓存服务:")
    redis_available = check_command("redis-server", "Redis Server")
    if not redis_available:
        print("⚠ Redis 未安装，将使用内存缓存")
    
    # 4. 项目结构检查
    structure_ok = check_project_structure()
    
    # 5. 后端依赖检查
    backend_results = check_backend_dependencies()
    
    # 6. 前端依赖检查
    frontend_ok = check_frontend_dependencies()
    
    # 7. 配置文件检查
    print("\n⚙️ 配置文件:")
    env_file = "backend/.env"
    if os.path.exists(env_file):
        print(f"✓ {env_file} 存在")
        
        # 检查关键配置
        with open(env_file, "r", encoding="utf-8") as f:
            env_content = f.read()
            
            if "GEMINI_API_KEY" in env_content:
                if "your_gemini_api_key_here" in env_content:
                    print("⚠ 需要设置真实的 Gemini API 密钥")
                else:
                    print("✓ Gemini API 密钥已配置")
            
            if "LLM_PROVIDER" in env_content:
                print("✓ AI 提供商配置存在")
            
            if "OLLAMA_BASE_URL" in env_content:
                print("✓ 本地AI配置存在")
    else:
        print(f"❌ {env_file} 不存在")
    
    # 8. 总结报告
    print("\n" + "=" * 60)
    print("📊 检查总结")
    print("=" * 60)
    
    # 基础环境
    basic_score = sum(basic_results.values())
    print(f"基础环境: {basic_score}/{len(basic_tools)} ({'✓' if basic_score >= 4 else '❌'})")
    
    # AI环境
    ai_score = (ollama_available + models_ok + backend_results.get('ai', False))
    print(f"AI环境: {ai_score}/3 ({'✓' if ai_score >= 2 else '⚠'})")
    
    # 视觉处理
    vision_score = backend_results.get('vision', False)
    print(f"视觉处理: {'✓' if vision_score else '❌'}")
    
    # 项目完整性
    project_score = (structure_ok + backend_results.get('core', False) + frontend_ok)
    print(f"项目完整性: {project_score}/3 ({'✓' if project_score == 3 else '❌'})")
    
    print("\n" + "=" * 60)
    
    # 给出建议
    if basic_score < 4:
        print("🔧 建议: 先运行基础安装脚本安装Python/Node.js等")
    elif not backend_results.get('vision', False):
        print("🔧 建议: 运行补充安装脚本安装AI/视觉处理组件")
    elif ai_score < 2:
        print("🔧 建议: 安装Ollama和本地模型以获得完整AI功能")
    elif project_score == 3 and basic_score >= 4:
        print("🎉 恭喜! 所有核心组件已就绪，可以启动项目了!")
    
    print("\n可用的安装脚本:")
    print("- 完全自动安装.ps1 (基础环境)")
    print("- 补充安装_本地AI和缺失组件.ps1 (高级组件)")
    print("- simple_install.bat (简单安装)")

if __name__ == "__main__":
    main()