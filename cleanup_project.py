#!/usr/bin/env python3
"""
项目清理脚本 - 保留核心部分，删除冗余文件
"""
import os
import shutil
import glob
from pathlib import Path


def should_keep_file(file_path: Path, keep_patterns: list, remove_patterns: list) -> bool:
    """判断文件是否应该保留"""
    file_str = str(file_path)
    
    # 检查是否匹配保留模式
    for pattern in keep_patterns:
        if pattern in file_str:
            return True
    
    # 检查是否匹配删除模式
    for pattern in remove_patterns:
        if pattern in file_str:
            return False
    
    return True


def cleanup_project():
    """清理项目"""
    base_dir = Path("Pervis PRO")
    
    if not base_dir.exists():
        print("错误: Pervis PRO 目录不存在")
        return
    
    # 需要保留的核心文件和目录模式
    keep_patterns = [
        # 核心目录
        "backend/app/",
        "backend/models/",
        "backend/routers/",
        "backend/services/",
        "backend/main.py",
        "backend/database.py",
        "backend/requirements.txt",
        "backend/.env.example",
        "backend/alembic/",
        "backend/alembic.ini",
        
        # 前端核心
        "frontend/src/",
        "frontend/public/",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/vite.config.ts",
        "frontend/.env.example",
        
        # 启动器核心
        "launcher/main.py",
        "launcher/requirements.txt",
        "launcher/services/",
        "launcher/ui/",
        
        # 配置和文档
        ".kiro/specs/",
        "README",
        ".env.example",
        ".gitignore",
        
        # 必要的数据目录
        "assets/",
        "storage/",
        "data/",
        
        # 保留一些重要文档
        "AGENTS.md",
        "API_AND_LAUNCHER_PLAN.md",
        "TECHNICAL_SPEC_V2_DETAILS.md",
    ]
    
    # 需要删除的文件和目录模式
    remove_patterns = [
        # 测试和验证文件
        "test_",
        "check_",
        "verify_",
        "debug_",
        "validate_",
        "validation_",
        
        # 报告文件
        "_REPORT",
        "_report",
        "COMPLETION_REPORT",
        "STATUS_REPORT",
        "FINAL_",
        "MVP_",
        "PHASE",
        
        # 安装脚本（保留一个主要的）
        "auto_install",
        "quick_install",
        "setup_environment.ps1",
        "全自动安装",
        "完整环境检查安装",
        "修复安装脚本",
        "超级自动安装",
        
        # 临时和缓存文件
        "__pycache__",
        ".pytest_cache",
        ".hypothesis",
        "*.pyc",
        "*.log",
        "*.db",
        "migration_test.db",
        
        # 重复的配置文件
        "launcher_config.json",
        
        # 废弃目录
        "deprecated/",
        "pool/",
        "MVP_DEMO_PACKAGE/",
        "demo_projects/",
        "narrative-assembly-system/",
        
        # 各种JSON报告
        ".json",
        
        # 中文文档（保留英文版本）
        "使用指南",
        "安装",
        "环境",
        "启动",
        "检查",
        "修复",
        "完成",
        "缺失",
        "视频编辑",
    ]
    
    # 统计信息
    deleted_files = []
    deleted_dirs = []
    kept_files = []
    
    print("开始清理项目...")
    print("=" * 50)
    
    # 遍历所有文件和目录
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        
        # 检查目录是否应该删除
        dirs_to_remove = []
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if not should_keep_file(dir_path, keep_patterns, remove_patterns):
                dirs_to_remove.append(dir_name)
                deleted_dirs.append(str(dir_path))
        
        # 删除目录
        for dir_name in dirs_to_remove:
            dir_path = root_path / dir_name
            try:
                shutil.rmtree(dir_path)
                print(f"删除目录: {dir_path}")
            except Exception as e:
                print(f"删除目录失败 {dir_path}: {e}")
            dirs.remove(dir_name)
        
        # 检查文件是否应该删除
        for file_name in files:
            file_path = root_path / file_name
            if not should_keep_file(file_path, keep_patterns, remove_patterns):
                try:
                    file_path.unlink()
                    deleted_files.append(str(file_path))
                    print(f"删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
            else:
                kept_files.append(str(file_path))
    
    # 清理空目录
    print("\n清理空目录...")
    for root, dirs, files in os.walk(base_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # 目录为空
                    dir_path.rmdir()
                    print(f"删除空目录: {dir_path}")
                    deleted_dirs.append(str(dir_path))
            except:
                pass  # 目录不为空或其他错误，忽略
    
    # 输出统计信息
    print("\n" + "=" * 50)
    print("清理完成!")
    print(f"删除文件数量: {len(deleted_files)}")
    print(f"删除目录数量: {len(deleted_dirs)}")
    print(f"保留文件数量: {len(kept_files)}")
    
    # 创建清理后的项目结构说明
    create_clean_structure_doc()


def create_clean_structure_doc():
    """创建清理后的项目结构说明"""
    structure_doc = """# 清理后的项目结构

## 保留的核心组件

### 后端 (backend/)
- app/ - 应用核心代码
- models/ - 数据模型
- routers/ - API路由
- services/ - 业务服务
- main.py - 应用入口
- database.py - 数据库配置
- requirements.txt - Python依赖

### 前端 (frontend/)
- src/ - 前端源码
- public/ - 静态资源
- package.json - 前端依赖
- 配置文件

### 启动器 (launcher/)
- main.py - 启动器主程序
- services/ - 启动器服务
- ui/ - 用户界面
- requirements.txt - 启动器依赖

### 配置和文档
- .kiro/specs/ - 规格文档
- 核心技术文档
- 配置文件模板

### 数据目录
- assets/ - 素材存储
- storage/ - 文件存储
- data/ - 数据存储

## 已删除的内容

- 大量重复的测试文件
- 各种验证和检查脚本
- 多个版本的安装脚本
- 临时文件和缓存
- 重复的报告文档
- 废弃的目录和文件

## 下一步

1. 检查保留的文件是否完整
2. 更新依赖和配置
3. 重新组织项目结构
4. 实施新的多Agent架构
"""
    
    with open("Pervis PRO/CLEAN_STRUCTURE.md", "w", encoding="utf-8") as f:
        f.write(structure_doc)
    
    print(f"\n已创建项目结构说明: Pervis PRO/CLEAN_STRUCTURE.md")


if __name__ == "__main__":
    print("项目清理脚本")
    print("这将删除大量冗余文件，保留核心组件")
    
    response = input("确定要继续吗? (y/N): ")
    if response.lower() in ['y', 'yes']:
        cleanup_project()
    else:
        print("取消清理操作")