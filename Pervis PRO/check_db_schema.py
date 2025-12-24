#!/usr/bin/env python3
"""
检查数据库表结构
"""

import sqlite3
from pathlib import Path

def check_table_schema(table_name):
    """检查表结构"""
    db_path = "backend/pervis_director.db"
    if not Path(db_path).exists():
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    if columns:
        print(f"\n📋 {table_name} 表结构:")
        for col in columns:
            print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    else:
        print(f"❌ 表 {table_name} 不存在")
    
    conn.close()

def main():
    """主函数"""
    print("=" * 50)
    print("数据库表结构检查")
    print("=" * 50)
    
    tables = ['assets', 'asset_tags', 'timelines', 'clips', 'render_tasks']
    
    for table in tables:
        check_table_schema(table)
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()