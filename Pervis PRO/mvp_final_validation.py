#!/usr/bin/env python3
"""
MVP最终验证脚本
验证完整工作流的所有关键功能点
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_mvp_workflow():
    """测试MVP完整工作流"""
    print("🚀 开始MVP最终验证")
    print("=" * 50)
    
    results = {
        "script_analysis": False,
        "beat_generation": False,
        "asset_search": False,
        "timeline_creation": False,
        "render_system": False,
        "frontend_integration": False
    }
    
    try:
        # 1. 测试剧本分析
        print("\n📝 测试剧本分析...")
        response = requests.post(f"{BASE_URL}/api/projects", json={
            "title": "MVP验证项目",
            "script_raw": "EXT. 城市街道 - 白天\n程序员匆忙走过街道。",
            "logline": "验证测试"
        })
        
        if response.status_code == 200:
            project_data = response.json()
            project_id = project_data["id"]
            print(f"✅ 剧本分析成功: {project_id}")
            results["script_analysis"] = True
        else:
            print(f"❌ 剧本分析失败: {response.status_code}")
            return results
        
        # 2. 测试Beat生成
        print("\n🎯 测试Beat生成...")
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/beats")
        
        if response.status_code == 200:
            beats_data = response.json()
            beats = beats_data.get("beats", [])
            print(f"✅ Beat生成成功: {len(beats)} 个Beat")
            results["beat_generation"] = True
        else:
            print(f"❌ Beat生成失败: {response.status_code}")
        
        # 3. 测试素材搜索
        print("\n🔍 测试多模态搜索...")
        response = requests.post(f"{BASE_URL}/api/multimodal/search", json={
            "query": "城市街道",
            "search_modes": ["semantic"],
            "limit": 5
        })
        
        if response.status_code == 200:
            search_results = response.json()
            result_count = len(search_results.get("results", []))
            print(f"✅ 素材搜索成功: {result_count} 个结果")
            results["asset_search"] = True
        else:
            print(f"❌ 素材搜索失败: {response.status_code}")
        
        # 4. 测试时间轴创建
        print("\n✂️  测试时间轴功能...")
        response = requests.post(f"{BASE_URL}/api/timeline/create", json={
            "project_id": project_id,
            "name": "验证时间轴"
        })
        
        if response.status_code == 200:
            timeline_data = response.json()
            timeline_id = timeline_data["id"]
            print(f"✅ 时间轴创建成功: {timeline_id}")
            results["timeline_creation"] = True
        else:
            print(f"❌ 时间轴创建失败: {response.status_code}")
        
        # 5. 测试渲染系统
        print("\n📤 测试渲染系统...")
        response = requests.get(f"{BASE_URL}/api/render/{timeline_id}/check")
        
        if response.status_code == 200:
            check_result = response.json()
            print(f"✅ 渲染系统检查成功")
            results["render_system"] = True
        else:
            print(f"❌ 渲染系统检查失败: {response.status_code}")
        
        # 6. 测试前端集成
        print("\n🌐 测试前端集成...")
        try:
            response = requests.get("http://localhost:3000")
            if response.status_code == 200:
                print("✅ 前端服务可访问")
                results["frontend_integration"] = True
            else:
                print(f"❌ 前端服务异常: {response.status_code}")
        except:
            print("⚠️  前端服务未启动或不可访问")
        
    except Exception as e:
        print(f"❌ 验证过程异常: {e}")
    
    return results

def generate_validation_report(results):
    """生成验证报告"""
    print("\n" + "=" * 50)
    print("📊 MVP验证结果汇总")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        test_display = test_name.replace("_", " ").title()
        print(f"{test_display:.<30} {status}")
    
    print("-" * 50)
    print(f"通过率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 MVP验证通过！系统可以投入使用")
        status = "READY"
    elif success_rate >= 60:
        print("⚠️  MVP基本可用，但需要修复部分问题")
        status = "PARTIAL"
    else:
        print("❌ MVP验证失败，需要重大修复")
        status = "FAILED"
    
    # 保存报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_results": results,
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "status": status
        }
    }
    
    report_path = Path("MVP_FINAL_VALIDATION_REPORT.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 验证报告已保存: {report_path}")
    return status

def main():
    """主函数"""
    try:
        results = test_mvp_workflow()
        status = generate_validation_report(results)
        
        if status == "READY":
            print("\n🚀 MVP已准备就绪，可以开始演示和用户测试！")
        elif status == "PARTIAL":
            print("\n🔧 MVP需要进一步完善，请检查失败的测试项")
        else:
            print("\n🛠️  MVP需要重大修复，请优先解决核心问题")
            
    except KeyboardInterrupt:
        print("\n⏹️  验证被用户中断")
    except Exception as e:
        print(f"\n💥 验证执行异常: {e}")

if __name__ == "__main__":
    main()