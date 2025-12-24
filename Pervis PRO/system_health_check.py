#!/usr/bin/env python3
"""
系统健康检查
验证所有关键组件是否正常工作
"""

import sys
import os
from pathlib import Path

# 切换到backend目录
backend_dir = Path(__file__).parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import get_db
from sqlalchemy import text

def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("1. 数据库检查")
    print("=" * 60)
    
    db = next(get_db())
    
    # 检查关键表
    tables = ['projects', 'beats', 'assets', 'timelines', 'clips', 'render_tasks']
    for table in tables:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"✅ {table}: {count} 条记录")
        except Exception as e:
            print(f"❌ {table}: 错误 - {e}")
    
    # 检查有效素材
    valid_assets = db.execute(text("""
        SELECT COUNT(*) FROM assets 
        WHERE mime_type = 'video/mp4' 
        AND file_path IS NOT NULL 
        AND processing_status = 'completed'
    """)).fetchone()[0]
    print(f"✅ 有效视频素材: {valid_assets} 个")
    
    # 检查素材文件是否存在
    assets = db.execute(text("""
        SELECT id, filename, file_path FROM assets 
        WHERE mime_type = 'video/mp4' 
        AND file_path IS NOT NULL 
        LIMIT 5
    """)).fetchall()
    
    print("\n素材文件验证:")
    for asset_id, filename, file_path in assets:
        if Path(file_path).exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - 文件不存在: {file_path}")
    
    db.close()

def check_autocut_orchestrator():
    """检查AutoCut Orchestrator"""
    print("\n" + "=" * 60)
    print("2. AutoCut Orchestrator 检查")
    print("=" * 60)
    
    try:
        from services.autocut_orchestrator import AutoCutOrchestrator
        print("✅ AutoCut Orchestrator 模块导入成功")
        
        # 检查关键方法
        methods = ['generate_timeline', '_smart_duration_analyze', '_semantic_asset_match', '_build_authoritative_decisions']
        for method in methods:
            if hasattr(AutoCutOrchestrator, method):
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法缺失: {method}")
    except Exception as e:
        print(f"❌ AutoCut Orchestrator 导入失败: {e}")

def check_api_routes():
    """检查API路由"""
    print("\n" + "=" * 60)
    print("3. API路由检查")
    print("=" * 60)
    
    try:
        from routers import autocut, timeline, render
        print("✅ AutoCut API 路由导入成功")
        print("✅ Timeline API 路由导入成功")
        print("✅ Render API 路由导入成功")
        
        # 检查关键端点
        if hasattr(autocut.router, 'routes'):
            print(f"  AutoCut 路由数: {len(autocut.router.routes)}")
        if hasattr(timeline.router, 'routes'):
            print(f"  Timeline 路由数: {len(timeline.router.routes)}")
        if hasattr(render.router, 'routes'):
            print(f"  Render 路由数: {len(render.router.routes)}")
    except Exception as e:
        print(f"❌ API路由导入失败: {e}")

def check_services():
    """检查核心服务"""
    print("\n" + "=" * 60)
    print("4. 核心服务检查")
    print("=" * 60)
    
    services = [
        'services.autocut_orchestrator',
        'services.timeline_service',
        'services.render_service',
        'services.gemini_client',
        'services.ffmpeg_wrapper'
    ]
    
    for service in services:
        try:
            __import__(service)
            print(f"✅ {service}")
        except Exception as e:
            print(f"❌ {service}: {e}")

def check_output_directory():
    """检查输出目录"""
    print("\n" + "=" * 60)
    print("5. 输出目录检查")
    print("=" * 60)
    
    output_dir = Path("storage/renders")
    if output_dir.exists():
        files = list(output_dir.glob("*.mp4"))
        print(f"✅ 输出目录存在: {output_dir}")
        print(f"  已渲染视频: {len(files)} 个")
        
        if files:
            latest = max(files, key=lambda p: p.stat().st_mtime)
            size_mb = latest.stat().st_size / 1024 / 1024
            print(f"  最新视频: {latest.name} ({size_mb:.2f} MB)")
    else:
        print(f"❌ 输出目录不存在: {output_dir}")

def main():
    """主函数"""
    print("\n🔍 PreVis PRO 系统健康检查")
    print("=" * 60)
    
    try:
        check_database()
        check_autocut_orchestrator()
        check_api_routes()
        check_services()
        check_output_directory()
        
        print("\n" + "=" * 60)
        print("✅ 系统健康检查完成")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ 系统健康检查失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
