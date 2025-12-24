#!/usr/bin/env python3
"""
PreVis PRO 导出和标签管理功能演示脚本
展示新增的导出和标签管理功能
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def demo_export_features():
    """演示导出功能"""
    print_section("📤 导出功能演示")
    
    # 假设有一个项目ID
    project_id = "cyberpunk_trailer"
    
    print("1. 导出剧本为DOCX格式")
    print(f"   POST {BASE_URL}/api/export/script")
    print(f"   项目ID: {project_id}")
    print(f"   格式: DOCX")
    print(f"   包含: Beats, 标签, 元数据")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/export/script",
            json={
                "project_id": project_id,
                "format": "docx",
                "include_beats": True,
                "include_tags": True,
                "include_metadata": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 导出成功!")
            print(f"   导出ID: {result.get('export_id')}")
            print(f"   文件大小: {result.get('file_size', 0) / 1024:.2f} KB")
            print(f"   下载URL: {BASE_URL}/api/export/download/{result.get('export_id')}")
        else:
            print(f"   ❌ 导出失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n2. 导出BeatBoard为PNG格式")
    print(f"   POST {BASE_URL}/api/export/beatboard")
    print(f"   项目ID: {project_id}")
    print(f"   格式: PNG")
    print(f"   尺寸: 1920x1080")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/export/beatboard",
            json={
                "project_id": project_id,
                "format": "png",
                "width": 1920,
                "height": 1080,
                "quality": 95
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 导出成功!")
            print(f"   导出ID: {result.get('export_id')}")
            print(f"   文件大小: {result.get('file_size', 0) / 1024:.2f} KB")
        else:
            print(f"   ❌ 导出失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n3. 查询导出历史")
    print(f"   GET {BASE_URL}/api/export/history/{project_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/export/history/{project_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            history = result.get('history', [])
            print(f"   ✅ 找到 {len(history)} 条导出记录")
            
            for i, record in enumerate(history[:3], 1):
                print(f"\n   记录 {i}:")
                print(f"   - 类型: {record.get('export_type')}")
                print(f"   - 格式: {record.get('file_format')}")
                print(f"   - 大小: {record.get('file_size', 0) / 1024:.2f} KB")
                print(f"   - 状态: {record.get('status')}")
        else:
            print(f"   ❌ 查询失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")

def demo_tag_management():
    """演示标签管理功能"""
    print_section("🏷️ 标签管理功能演示")
    
    # 假设有一个资产ID
    asset_id = "asset_001"
    
    print("1. 获取视频标签")
    print(f"   GET {BASE_URL}/api/tags/{asset_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/tags/{asset_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            tags = result.get('tags', [])
            print(f"   ✅ 找到 {len(tags)} 个标签")
            
            # 显示前5个标签
            for i, tag in enumerate(tags[:5], 1):
                print(f"\n   标签 {i}:")
                print(f"   - 名称: {tag.get('name')}")
                print(f"   - 分类: {tag.get('category')}")
                print(f"   - 权重: {tag.get('weight', 0.5):.2f}")
                print(f"   - 层级: {tag.get('parent_id', '根节点')}")
        else:
            print(f"   ⚠️ 资产不存在或无标签")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n2. 更新标签权重")
    print(f"   PUT {BASE_URL}/api/tags/weight")
    print(f"   资产ID: {asset_id}")
    print(f"   标签ID: tag_001")
    print(f"   新权重: 0.8")
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/tags/weight",
            json={
                "asset_id": asset_id,
                "tag_id": "tag_001",
                "weight": 0.8
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ 权重更新成功!")
        else:
            print(f"   ⚠️ 更新失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n3. 更新标签层级")
    print(f"   PUT {BASE_URL}/api/tags/hierarchy")
    print(f"   资产ID: {asset_id}")
    print(f"   标签ID: tag_002")
    print(f"   新父标签: tag_001")
    print(f"   顺序: 1")
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/tags/hierarchy",
            json={
                "asset_id": asset_id,
                "tag_id": "tag_002",
                "parent_id": "tag_001",
                "order": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ 层级更新成功!")
        else:
            print(f"   ⚠️ 更新失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")

def demo_vector_analysis():
    """演示向量分析功能"""
    print_section("🔍 向量分析功能演示")
    
    print("1. 计算相似度")
    print(f"   POST {BASE_URL}/api/vector/similarity")
    print(f"   查询: '赛博朋克城市夜景'")
    print(f"   Top-K: 5")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/vector/similarity",
            json={
                "query": "赛博朋克城市夜景",
                "top_k": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            print(f"   ✅ 找到 {len(results)} 个匹配结果")
            
            for i, match in enumerate(results, 1):
                print(f"\n   结果 {i}:")
                print(f"   - 文件: {match.get('filename')}")
                print(f"   - 相似度: {match.get('similarity_score', 0) * 100:.1f}%")
                print(f"   - 匹配标签: {', '.join(match.get('matched_tags', [])[:3])}")
        else:
            print(f"   ⚠️ 搜索失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n2. 解释匹配结果")
    print(f"   POST {BASE_URL}/api/vector/explain")
    print(f"   查询: '赛博朋克城市夜景'")
    print(f"   资产ID: asset_001")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/vector/explain",
            json={
                "query": "赛博朋克城市夜景",
                "asset_id": "asset_001"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 解释生成成功!")
            print(f"\n   {result.get('explanation', '无解释')}")
            
            keywords = result.get('matched_keywords', [])
            if keywords:
                print(f"\n   匹配关键词: {', '.join(keywords)}")
        else:
            print(f"   ⚠️ 解释失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n3. 保存测试案例")
    print(f"   POST {BASE_URL}/api/vector/test-case")
    print(f"   名称: '赛博朋克场景测试'")
    print(f"   查询: '赛博朋克城市夜景'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/vector/test-case",
            json={
                "name": "赛博朋克场景测试",
                "query": "赛博朋克城市夜景",
                "expected_results": ["asset_001", "asset_002", "asset_003"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 测试案例保存成功!")
            print(f"   案例ID: {result.get('test_case_id')}")
        else:
            print(f"   ⚠️ 保存失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")
    
    print("\n4. 获取所有测试案例")
    print(f"   GET {BASE_URL}/api/vector/test-cases")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/vector/test-cases",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            test_cases = result.get('test_cases', [])
            print(f"   ✅ 找到 {len(test_cases)} 个测试案例")
            
            for i, case in enumerate(test_cases[:3], 1):
                print(f"\n   案例 {i}:")
                print(f"   - 名称: {case.get('name')}")
                print(f"   - 查询: {case.get('query')}")
                print(f"   - 状态: {case.get('status')}")
                print(f"   - 期望结果数: {case.get('expected_count')}")
        else:
            print(f"   ⚠️ 查询失败: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 无法连接到后端: {e}")

def show_usage_guide():
    """显示使用指南"""
    print_section("📖 使用指南")
    
    print("启动器使用方法:")
    print("1. 启动PreVis PRO启动器")
    print("   python pervis_desktop_launcher.py")
    print()
    print("2. 在项目卡片上找到新增的按钮:")
    print("   - 📤 导出: 导出剧本和BeatBoard")
    print("   - 🏷️ 标签: 打开标签管理界面")
    print()
    print("3. 点击导出按钮:")
    print("   - 选择导出类型（剧本/BeatBoard）")
    print("   - 选择格式（DOCX/PDF 或 PNG/JPG）")
    print("   - 点击导出并选择保存位置")
    print()
    print("4. 点击标签按钮:")
    print("   - 自动在浏览器中打开标签管理页面")
    print("   - 查看和调整标签层级和权重")
    print()
    print("\nWeb界面使用方法:")
    print("1. 标签管理页面:")
    print("   http://localhost:3001/tag-management?project=<project_id>")
    print()
    print("2. 向量可视化页面:")
    print("   http://localhost:3001/vector-visualization")
    print()
    print("\nAPI端点:")
    print("- 导出: /api/export/script, /api/export/beatboard")
    print("- 标签: /api/tags/{asset_id}, /api/tags/weight, /api/tags/hierarchy")
    print("- 向量: /api/vector/similarity, /api/vector/explain, /api/vector/test-case")

def main():
    """主函数"""
    print("\n" + "🎬" * 30)
    print("  PreVis PRO 导出和标签管理功能演示")
    print("🎬" * 30)
    
    print("\n⚠️ 注意: 此演示需要后端服务运行在 http://localhost:8000")
    print("如果后端未启动，部分演示将显示连接错误\n")
    
    input("按Enter键开始演示...")
    
    # 演示各个功能
    demo_export_features()
    demo_tag_management()
    demo_vector_analysis()
    show_usage_guide()
    
    print_section("✅ 演示完成")
    print("所有新功能已展示完毕！")
    print("\n详细文档请查看:")
    print("- FRONTEND_INTEGRATION_COMPLETION_REPORT.md")
    print("- ENHANCED_EXPORT_TAG_COMPLETION_REPORT.md")
    print("- MVP_EXPORT_TAG_VALIDATION_REPORT.md")
    print("\n感谢使用 PreVis PRO! 🎉\n")

if __name__ == "__main__":
    main()
