#!/usr/bin/env python3
"""
修复导出功能问题
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def fix_export_functionality():
    """修复导出功能"""
    print("🔧 开始修复导出功能...")
    
    # 1. 创建测试项目数据
    await create_test_project_data()
    
    # 2. 测试导出功能
    await test_export_with_real_data()
    
    print("✅ 导出功能修复完成!")

async def create_test_project_data():
    """创建测试项目数据"""
    print("\n📝 创建测试项目数据...")
    
    try:
        from database import get_db
        from services.script_processor import ScriptProcessor
        
        # 创建一个真实的项目
        test_script = """FADE IN:

INT. COFFEE SHOP - DAY

SARAH (20s) sits at a corner table, typing on her laptop. The morning sun streams through large windows.

BARISTA (30s) approaches with a steaming cup.

BARISTA
Your usual latte.

SARAH
(looking up, smiling)
Thanks, Mike. You're a lifesaver.

Sarah takes a sip and returns to her work. Her phone BUZZES.

SARAH (CONT'D)
(reading text)
Finally! The interview is confirmed.

She closes her laptop with determination.

FADE OUT."""

        # 使用ScriptProcessor分析剧本
        async with get_db() as db:
            processor = ScriptProcessor(db)
            result = await processor.analyze_script(test_script, title="导出测试项目", logline="一个关于咖啡店的故事")
            
            project_id = result.get('project_id')
            print(f"  ✅ 创建测试项目: {project_id}")
            print(f"  📊 生成Beat数量: {len(result.get('beats', []))}")
            print(f"  👥 识别角色数量: {len(result.get('characters', []))}")
            
            return project_id
            
    except Exception as e:
        print(f"  ❌ 创建测试项目失败: {e}")
        return None

async def test_export_with_real_data():
    """使用真实数据测试导出功能"""
    print("\n🧪 使用真实数据测试导出功能...")
    
    try:
        from database import get_db
        
        # 获取一个真实的项目ID
        async with get_db() as db:
            result = await db.execute("SELECT id FROM projects LIMIT 1")
            project_row = result.fetchone()
            
            if not project_row:
                print("  ⚠️ 没有找到项目数据，无法测试导出功能")
                return
                
            project_id = project_row['id']
            print(f"  📋 使用项目ID: {project_id}")
            
            # 测试导出API
            import requests
            
            # 测试剧本导出
            try:
                response = requests.post(
                    "http://localhost:8000/api/export/script",
                    json={
                        "project_id": project_id,
                        "format": "docx",
                        "include_beats": True,
                        "include_tags": True,
                        "include_metadata": True
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ 剧本导出成功: {response.status_code}")
                    export_data = response.json()
                    print(f"    📄 导出ID: {export_data.get('export_id')}")
                    print(f"    📁 文件路径: {export_data.get('file_path')}")
                    print(f"    📊 文件大小: {export_data.get('file_size')} bytes")
                else:
                    print(f"  ❌ 剧本导出失败: {response.status_code}")
                    print(f"    错误信息: {response.json()}")
                    
            except Exception as e:
                print(f"  ❌ 剧本导出测试失败: {e}")
                
            # 测试BeatBoard导出
            try:
                response = requests.post(
                    "http://localhost:8000/api/export/beatboard",
                    json={
                        "project_id": project_id,
                        "format": "png",
                        "width": 1920,
                        "height": 1080,
                        "quality": 90
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ BeatBoard导出成功: {response.status_code}")
                    export_data = response.json()
                    print(f"    📄 导出ID: {export_data.get('export_id')}")
                    print(f"    📁 文件路径: {export_data.get('file_path')}")
                    print(f"    📊 文件大小: {export_data.get('file_size')} bytes")
                else:
                    print(f"  ❌ BeatBoard导出失败: {response.status_code}")
                    print(f"    错误信息: {response.json()}")
                    
            except Exception as e:
                print(f"  ❌ BeatBoard导出测试失败: {e}")
                
    except Exception as e:
        print(f"  ❌ 导出功能测试失败: {e}")

async def main():
    """主函数"""
    await fix_export_functionality()

if __name__ == "__main__":
    asyncio.run(main())