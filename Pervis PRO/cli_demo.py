#!/usr/bin/env python3
"""
命令行工具演示脚本
"""

from pervis_cli import PervisCLI
import time

def demo_cli():
    """演示命令行工具功能"""
    print("🎬 Pervis PRO 命令行工具演示")
    print("=" * 50)
    
    cli = PervisCLI()
    
    # 1. 检查服务器
    print("1️⃣ 检查服务器状态...")
    if not cli.check_server():
        return
    
    # 2. 分析剧本
    print("\n2️⃣ 分析剧本...")
    if cli.analyze_script("青春校园物语", "sample_script.txt"):
        print("✅ 剧本分析完成")
    
    # 3. 上传素材
    print("\n3️⃣ 上传素材...")
    if cli.upload_assets("backend/assets", max_files=3):
        print("✅ 素材上传完成")
    
    # 等待处理
    print("\n⏳ 等待素材处理...")
    time.sleep(2)
    
    # 4. 多模态搜索
    print("\n4️⃣ 多模态搜索演示...")
    
    test_queries = [
        "樱花飞舞的校园场景",
        "紧张的考试氛围", 
        "夕阳下的浪漫告白",
        "青春活力的运动场面"
    ]
    
    for query in test_queries:
        print(f"\n🔍 搜索: {query}")
        cli.search_assets(query, ["semantic", "visual"])
        time.sleep(1)
    
    # 5. Beat匹配搜索
    print("\n5️⃣ Beat匹配搜索...")
    cli.list_beats()
    
    if cli.current_beats:
        for i in range(min(2, len(cli.current_beats))):
            print(f"\n🎯 为Beat {i+1} 搜索素材...")
            cli.search_for_beat(i+1)
            time.sleep(1)
    
    print("\n🎉 命令行工具演示完成!")
    print("\n💡 使用方式:")
    print("   python pervis_cli.py -i  # 进入交互模式")
    print("   python pervis_cli.py --help  # 查看完整帮助")

if __name__ == "__main__":
    demo_cli()