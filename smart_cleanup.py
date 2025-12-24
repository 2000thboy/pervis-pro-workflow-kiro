#!/usr/bin/env python3
"""
智能项目清理脚本 - 保留核心组件，为多Agent架构做准备
"""
import os
import shutil
import json
from pathlib import Path


def backup_important_files():
    """备份重要文件"""
    backup_dir = Path("backup_before_cleanup")
    backup_dir.mkdir(exist_ok=True)
    
    important_files = [
        "Pervis PRO/backend/main.py",
        "Pervis PRO/backend/database.py", 
        "Pervis PRO/backend/requirements.txt",
        "Pervis PRO/backend/.env",
        "Pervis PRO/frontend/package.json",
        "Pervis PRO/launcher/main.py",
        "Pervis PRO/.env",
    ]
    
    for file_path in important_files:
        if Path(file_path).exists():
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"备份: {file_path} -> {backup_path}")


def clean_test_and_validation_files():
    """清理测试和验证文件"""
    base_dir = Path("Pervis PRO")
    
    patterns_to_remove = [
        "test_*.py",
        "check_*.py", 
        "verify_*.py",
        "debug_*.py",
        "*_test_*.py",
        "*_validation*.py",
        "*_report*.json",
        "*_REPORT*.md",
        "MVP_*.md",
        "PHASE*.md",
        "FINAL_*.md",
        "COMPLETION_*.md",
        "STATUS_*.md",
    ]
    
    removed_count = 0
    for pattern in patterns_to_remove:
        for file_path in base_dir.rglob(pattern):
            try:
                file_path.unlink()
                print(f"删除测试文件: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"删除失败 {file_path}: {e}")
    
    print(f"删除了 {removed_count} 个测试/验证文件")


def clean_installation_scripts():
    """清理多余的安装脚本，只保留一个主要的"""
    base_dir = Path("Pervis PRO")
    
    # 保留的安装脚本
    keep_scripts = [
        "setup_environment.py",  # 保留这个作为主要安装脚本
    ]
    
    # 删除其他安装脚本
    install_patterns = [
        "*install*.ps1",
        "*install*.bat", 
        "*安装*.ps1",
        "*环境*.ps1",
        "*修复*.ps1",
        "*自动*.ps1",
        "quick_*.ps1",
        "auto_*.ps1",
    ]
    
    removed_count = 0
    for pattern in install_patterns:
        for file_path in base_dir.rglob(pattern):
            if file_path.name not in keep_scripts:
                try:
                    file_path.unlink()
                    print(f"删除安装脚本: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"删除失败 {file_path}: {e}")
    
    print(f"删除了 {removed_count} 个安装脚本")


def clean_cache_and_temp():
    """清理缓存和临时文件"""
    base_dir = Path("Pervis PRO")
    
    cache_dirs = [
        "__pycache__",
        ".pytest_cache", 
        ".hypothesis",
        "node_modules",  # 前端会重新安装
    ]
    
    temp_files = [
        "*.pyc",
        "*.log",
        "*.db",
        "*.tmp",
        "migration_test.db",
        "pervis_director.db",
    ]
    
    # 删除缓存目录
    removed_dirs = 0
    for cache_dir in cache_dirs:
        for dir_path in base_dir.rglob(cache_dir):
            if dir_path.is_dir():
                try:
                    shutil.rmtree(dir_path)
                    print(f"删除缓存目录: {dir_path}")
                    removed_dirs += 1
                except Exception as e:
                    print(f"删除失败 {dir_path}: {e}")
    
    # 删除临时文件
    removed_files = 0
    for pattern in temp_files:
        for file_path in base_dir.rglob(pattern):
            try:
                file_path.unlink()
                print(f"删除临时文件: {file_path}")
                removed_files += 1
            except Exception as e:
                print(f"删除失败 {file_path}: {e}")
    
    print(f"删除了 {removed_dirs} 个缓存目录和 {removed_files} 个临时文件")


def clean_deprecated_dirs():
    """删除废弃的目录"""
    base_dir = Path("Pervis PRO")
    
    deprecated_dirs = [
        "deprecated",
        "pool", 
        "MVP_DEMO_PACKAGE",
        "demo_projects",
        "narrative-assembly-system",
        "temp",
        "tools",  # 空目录
    ]
    
    removed_count = 0
    for dir_name in deprecated_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                print(f"删除废弃目录: {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"删除失败 {dir_path}: {e}")
    
    print(f"删除了 {removed_count} 个废弃目录")


def reorganize_core_structure():
    """重新组织核心结构"""
    base_dir = Path("Pervis PRO")
    
    # 创建新的多Agent架构目录
    new_dirs = [
        "multi-agent-core",
        "multi-agent-core/agents",
        "multi-agent-core/workflows", 
        "multi-agent-core/core",
        "multi-agent-core/tests",
    ]
    
    for new_dir in new_dirs:
        dir_path = base_dir / new_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {dir_path}")
    
    # 移动现有的有用文件到新结构
    moves = [
        # 保留现有后端的核心部分
        ("backend/app", "multi-agent-core/legacy-app"),
        ("backend/models", "multi-agent-core/legacy-models"), 
        ("backend/routers", "multi-agent-core/legacy-routers"),
        ("backend/services", "multi-agent-core/legacy-services"),
    ]
    
    for src, dst in moves:
        src_path = base_dir / src
        dst_path = base_dir / dst
        if src_path.exists():
            try:
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.move(str(src_path), str(dst_path))
                print(f"移动: {src_path} -> {dst_path}")
            except Exception as e:
                print(f"移动失败 {src_path}: {e}")


def create_migration_guide():
    """创建迁移指南"""
    guide_content = """# 项目清理和迁移指南

## 清理完成的内容

### 已删除
- 大量重复的测试文件 (test_*.py, check_*.py, verify_*.py)
- 多个版本的安装脚本 (保留了 setup_environment.py)
- 各种报告文档 (*_REPORT*.md, MVP_*.md, PHASE*.md)
- 缓存和临时文件 (__pycache__, *.pyc, *.log)
- 废弃目录 (deprecated/, pool/, MVP_DEMO_PACKAGE/)

### 保留的核心组件
- backend/ - 现有后端代码 (需要重构为多Agent架构)
- frontend/ - 现有前端代码 (需要适配新架构)
- launcher/ - 桌面启动器
- .kiro/specs/ - 规格文档
- assets/, storage/, data/ - 数据目录

### 新增的目录结构
- multi-agent-core/ - 新的多Agent架构
  - agents/ - Agent实现
  - workflows/ - 工作流引擎
  - core/ - 核心服务
  - tests/ - 测试代码

## 下一步行动

1. **备份检查**: 检查 backup_before_cleanup/ 目录中的重要文件
2. **依赖清理**: 重新安装前端依赖 (cd frontend && npm install)
3. **架构迁移**: 
   - 将现有功能逐步迁移到新的多Agent架构
   - 保留有用的业务逻辑和数据模型
   - 重构为基于消息总线的Agent协作模式
4. **测试重建**: 基于新架构重新编写测试

## 重要文件位置

- 主配置: backend/.env, frontend/package.json
- 数据库: backend/database.py
- 启动器: launcher/main.py
- 规格文档: .kiro/specs/multi-agent-workflow-core/

## 迁移策略

1. 保持现有系统可运行
2. 逐步实现新的Agent架构
3. 分阶段迁移功能模块
4. 最终替换为完整的多Agent系统
"""
    
    with open("Pervis PRO/MIGRATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("已创建迁移指南: Pervis PRO/MIGRATION_GUIDE.md")


def main():
    """主清理流程"""
    print("智能项目清理脚本")
    print("=" * 50)
    
    # 确认操作
    print("这将执行以下操作:")
    print("1. 备份重要文件")
    print("2. 删除测试和验证文件")
    print("3. 清理多余的安装脚本")
    print("4. 删除缓存和临时文件")
    print("5. 删除废弃目录")
    print("6. 重新组织目录结构")
    print("7. 创建迁移指南")
    
    response = input("\n确定要继续吗? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("取消清理操作")
        return
    
    try:
        # 执行清理步骤
        print("\n1. 备份重要文件...")
        backup_important_files()
        
        print("\n2. 清理测试和验证文件...")
        clean_test_and_validation_files()
        
        print("\n3. 清理安装脚本...")
        clean_installation_scripts()
        
        print("\n4. 清理缓存和临时文件...")
        clean_cache_and_temp()
        
        print("\n5. 删除废弃目录...")
        clean_deprecated_dirs()
        
        print("\n6. 重新组织目录结构...")
        reorganize_core_structure()
        
        print("\n7. 创建迁移指南...")
        create_migration_guide()
        
        print("\n" + "=" * 50)
        print("清理完成!")
        print("请查看 MIGRATION_GUIDE.md 了解下一步操作")
        print("重要文件已备份到 backup_before_cleanup/ 目录")
        
    except Exception as e:
        print(f"清理过程中出现错误: {e}")
        print("请检查错误信息并手动处理")


if __name__ == "__main__":
    main()