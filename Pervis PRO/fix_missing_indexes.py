#!/usr/bin/env python3
"""
修复缺失的数据库索引
为视频编辑系统表创建性能索引
"""

import sys
import os
import sqlite3
from datetime import datetime

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DATABASE_URL
    print("✅ 成功导入数据库配置")
except ImportError as e:
    print(f"❌ 导入数据库配置失败: {e}")
    DATABASE_URL = "sqlite:///./pervis_director.db"

def get_db_path():
    """获取数据库路径"""
    if "sqlite:///" in DATABASE_URL:
        return DATABASE_URL.replace("sqlite:///", "")
    else:
        return "pervis_director.db"

def create_missing_indexes():
    """创建缺失的索引"""
    db_path = get_db_path()
    
    print("=" * 60)
    print("🔧 修复缺失的数据库索引")
    print("=" * 60)
    print(f"📍 数据库路径: {db_path}")
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 需要创建的索引
        missing_indexes = [
            {
                "name": "idx_timelines_project_id",
                "table": "timelines",
                "columns": ["project_id"],
                "description": "时间轴项目ID索引"
            },
            {
                "name": "idx_clips_timeline_id", 
                "table": "clips",
                "columns": ["timeline_id"],
                "description": "片段时间轴ID索引"
            },
            {
                "name": "idx_clips_order_index",
                "table": "clips", 
                "columns": ["order_index"],
                "description": "片段顺序索引"
            },
            {
                "name": "idx_render_tasks_timeline_id",
                "table": "render_tasks",
                "columns": ["timeline_id"],
                "description": "渲染任务时间轴ID索引"
            },
            {
                "name": "idx_render_tasks_status",
                "table": "render_tasks",
                "columns": ["status"],
                "description": "渲染任务状态索引"
            }
        ]
        
        created_count = 0
        failed_count = 0
        
        for index_info in missing_indexes:
            index_name = index_info["name"]
            table_name = index_info["table"]
            columns = index_info["columns"]
            description = index_info["description"]
            
            print(f"🔧 创建索引: {index_name}")
            print(f"   表: {table_name}")
            print(f"   列: {', '.join(columns)}")
            print(f"   描述: {description}")
            
            try:
                # 检查表是否存在
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor.fetchone():
                    print(f"   ⚠️  表 {table_name} 不存在，跳过索引创建")
                    continue
                
                # 检查索引是否已存在
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                if cursor.fetchone():
                    print(f"   ℹ️  索引 {index_name} 已存在，跳过")
                    continue
                
                # 创建索引
                columns_str = ', '.join(columns)
                sql = f"CREATE INDEX {index_name} ON {table_name}({columns_str})"
                cursor.execute(sql)
                
                print(f"   ✅ 索引创建成功")
                created_count += 1
                
            except Exception as e:
                print(f"   ❌ 索引创建失败: {e}")
                failed_count += 1
            
            print()
        
        # 提交更改
        conn.commit()
        
        print("=" * 60)
        print("📊 索引创建结果")
        print("=" * 60)
        print(f"✅ 成功创建: {created_count} 个索引")
        print(f"❌ 创建失败: {failed_count} 个索引")
        print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if created_count > 0:
            print("\n🎉 数据库索引优化完成！")
            print("💡 这将提升以下操作的性能:")
            print("   - 按项目查询时间轴")
            print("   - 按时间轴查询片段")
            print("   - 按顺序排序片段")
            print("   - 查询渲染任务状态")
        
        return failed_count == 0
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    finally:
        conn.close()

def verify_indexes():
    """验证索引是否创建成功"""
    db_path = get_db_path()
    
    print("\n🔍 验证索引创建结果...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查所有索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        existing_indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            "idx_timelines_project_id",
            "idx_clips_timeline_id", 
            "idx_clips_order_index",
            "idx_render_tasks_timeline_id",
            "idx_render_tasks_status"
        ]
        
        print(f"📊 现有索引总数: {len(existing_indexes)}")
        
        missing_indexes = []
        for expected in expected_indexes:
            if expected in existing_indexes:
                print(f"✅ {expected}")
            else:
                print(f"❌ {expected}")
                missing_indexes.append(expected)
        
        if not missing_indexes:
            print("\n🎉 所有预期索引都已创建！")
            return True
        else:
            print(f"\n⚠️  仍有 {len(missing_indexes)} 个索引缺失")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("🚀 开始修复数据库索引...")
    
    # 创建缺失的索引
    success = create_missing_indexes()
    
    if success:
        # 验证索引创建结果
        verify_indexes()
        print("\n✅ 数据库索引修复完成！")
        return 0
    else:
        print("\n❌ 数据库索引修复失败！")
        return 1

if __name__ == "__main__":
    exit(main())