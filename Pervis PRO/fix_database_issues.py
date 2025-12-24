#!/usr/bin/env python3
"""
修复数据库问题
解决 "database or disk is full" 错误
"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path

def check_disk_space():
    """检查磁盘空间"""
    print("🔍 检查磁盘空间...")
    
    current_dir = Path.cwd()
    total, used, free = shutil.disk_usage(current_dir)
    
    print(f"当前目录: {current_dir}")
    print(f"总空间: {total / (1024**3):.1f} GB")
    print(f"已用空间: {used / (1024**3):.1f} GB")
    print(f"可用空间: {free / (1024**3):.1f} GB")
    
    if free < 1024**3:  # 小于1GB
        print("⚠️ 磁盘空间不足！")
        return False
    else:
        print("✅ 磁盘空间充足")
        return True

def check_database_file():
    """检查数据库文件"""
    print("\n🔍 检查数据库文件...")
    
    db_path = Path("pervis_director.db")
    
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"数据库文件: {db_path}")
        print(f"文件大小: {size / 1024:.1f} KB")
        
        # 检查文件权限
        if os.access(db_path, os.R_OK | os.W_OK):
            print("✅ 文件权限正常")
        else:
            print("❌ 文件权限异常")
            return False
        
        return True
    else:
        print("❌ 数据库文件不存在")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        conn = sqlite3.connect("pervis_director.db")
        cursor = conn.cursor()
        
        # 测试基本操作
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ 数据库连接成功")
        print(f"表数量: {len(tables)}")
        
        # 检查数据库完整性
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("✅ 数据库完整性检查通过")
        else:
            print(f"❌ 数据库完整性问题: {result[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def vacuum_database():
    """清理数据库"""
    print("\n🔧 清理数据库...")
    
    try:
        conn = sqlite3.connect("pervis_director.db")
        
        # 执行VACUUM命令清理数据库
        conn.execute("VACUUM;")
        
        # 重建索引
        conn.execute("REINDEX;")
        
        conn.close()
        print("✅ 数据库清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")
        return False

def backup_and_recreate_database():
    """备份并重新创建数据库"""
    print("\n🔄 备份并重新创建数据库...")
    
    db_path = Path("pervis_director.db")
    backup_path = Path(f"pervis_director_backup_{int(time.time())}.db")
    
    try:
        # 备份现有数据库
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
            print(f"✅ 数据库已备份到: {backup_path}")
        
        # 删除现有数据库
        if db_path.exists():
            db_path.unlink()
            print("✅ 删除旧数据库")
        
        # 重新初始化数据库
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from database import init_database
        
        init_database()
        print("✅ 数据库重新创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库重建失败: {e}")
        
        # 恢复备份
        if backup_path.exists():
            shutil.copy2(backup_path, db_path)
            print("✅ 已恢复备份数据库")
        
        return False

def fix_temp_directory():
    """修复临时目录问题"""
    print("\n🔧 检查临时目录...")
    
    temp_dirs = [
        Path(os.environ.get('TEMP', '/tmp')),
        Path(os.environ.get('TMP', '/tmp')),
        Path('./temp'),
        Path('./storage/temp')
    ]
    
    for temp_dir in temp_dirs:
        try:
            if temp_dir.exists():
                # 检查临时目录空间
                total, used, free = shutil.disk_usage(temp_dir)
                print(f"临时目录 {temp_dir}: {free / (1024**3):.1f} GB 可用")
                
                # 清理临时文件
                temp_files = list(temp_dir.glob("*.tmp"))
                if temp_files:
                    for temp_file in temp_files:
                        try:
                            temp_file.unlink()
                        except:
                            pass
                    print(f"✅ 清理了 {len(temp_files)} 个临时文件")
            else:
                temp_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建临时目录: {temp_dir}")
                
        except Exception as e:
            print(f"⚠️ 临时目录 {temp_dir} 处理失败: {e}")

def run_simple_test():
    """运行简单测试"""
    print("\n🧪 运行简单数据库测试...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from database import SessionLocal, init_database, Project
        
        # 确保数据库初始化
        init_database()
        
        # 创建会话
        db = SessionLocal()
        
        try:
            # 简单的插入测试
            test_project = Project(
                id="test_project_123",
                title="测试项目",
                logline="数据库修复测试",
                current_stage="testing"
            )
            
            db.add(test_project)
            db.commit()
            
            # 查询测试
            project = db.query(Project).filter(Project.id == "test_project_123").first()
            
            if project:
                print("✅ 数据库读写测试成功")
                
                # 清理测试数据
                db.delete(project)
                db.commit()
                
                return True
            else:
                print("❌ 数据库读取失败")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def main():
    """主修复流程"""
    print("=" * 60)
    print("PreVis PRO 数据库问题修复工具")
    print("=" * 60)
    
    # 1. 检查磁盘空间
    if not check_disk_space():
        print("\n❌ 磁盘空间不足，请清理磁盘后重试")
        return False
    
    # 2. 检查数据库文件
    db_exists = check_database_file()
    
    # 3. 修复临时目录
    fix_temp_directory()
    
    # 4. 测试数据库连接
    if db_exists and test_database_connection():
        # 5. 清理数据库
        if vacuum_database():
            # 6. 运行简单测试
            if run_simple_test():
                print("\n🎉 数据库修复成功！")
                return True
    
    # 如果上述步骤失败，重建数据库
    print("\n🔄 尝试重建数据库...")
    if backup_and_recreate_database():
        if run_simple_test():
            print("\n🎉 数据库重建成功！")
            return True
    
    print("\n❌ 数据库修复失败")
    return False

if __name__ == "__main__":
    import time
    success = main()
    
    if success:
        print("\n✅ 可以重新运行测试:")
        print("   python test_video_editing_complete.py")
    else:
        print("\n❌ 修复失败，请检查:")
        print("   1. 磁盘空间是否充足")
        print("   2. 文件权限是否正确")
        print("   3. 是否有其他程序占用数据库")
    
    input("\n按回车键退出...")