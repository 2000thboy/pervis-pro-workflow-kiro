"""
修复 workflow.db 数据库表结构
添加缺失的 created_at 列到 conversation_context 表
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'workflow.db')

def fix_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查 conversation_context 表结构
    cursor.execute("PRAGMA table_info(conversation_context)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前 conversation_context 表列: {columns}")
    
    # 如果缺少 created_at 列，添加它
    if 'created_at' not in columns:
        print("添加 created_at 列...")
        # SQLite 不支持带函数的默认值，使用 NULL 默认值
        cursor.execute("""
            ALTER TABLE conversation_context 
            ADD COLUMN created_at TEXT
        """)
        # 更新现有记录，使用 timestamp 列的值
        cursor.execute("""
            UPDATE conversation_context 
            SET created_at = timestamp 
            WHERE created_at IS NULL
        """)
        conn.commit()
        print("✅ created_at 列已添加")
    else:
        print("✅ created_at 列已存在")
    
    # 验证修复
    cursor.execute("PRAGMA table_info(conversation_context)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"修复后 conversation_context 表列: {columns}")
    
    conn.close()
    print("数据库修复完成！")

if __name__ == "__main__":
    fix_schema()
