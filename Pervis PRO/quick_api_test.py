#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速 API 测试脚本
验证关键端点是否可用
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, url, data=None):
    """测试单个端点"""
    try:
        if method == "GET":
            resp = requests.get(url, timeout=15)
        else:
            resp = requests.post(url, json=data, timeout=15)
        
        status = "✅" if resp.status_code in [200, 201] else "⚠️" if resp.status_code == 404 else "❌"
        print(f"{status} {name}: HTTP {resp.status_code}")
        return resp.status_code in [200, 201]
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: 连接失败")
        return False
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 Pervis PRO API 快速测试")
    print("=" * 50)
    
    results = []
    
    # 基础健康检查
    results.append(test_endpoint("健康检查", "GET", f"{BASE_URL}/api/health"))
    
    # Wizard API
    results.append(test_endpoint("Wizard 健康", "GET", f"{BASE_URL}/api/wizard/health"))
    results.append(test_endpoint("剧本解析", "POST", f"{BASE_URL}/api/wizard/parse-script", 
                                 {"script_content": "场景一：测试", "format": "txt"}))
    results.append(test_endpoint("创建草稿", "POST", f"{BASE_URL}/api/wizard/draft",
                                 {"title": "测试项目", "project_type": "short_film"}))
    
    # System Agent API
    results.append(test_endpoint("系统健康", "GET", f"{BASE_URL}/api/system/health"))
    results.append(test_endpoint("通知列表", "GET", f"{BASE_URL}/api/system/notifications"))
    
    # Export API
    results.append(test_endpoint("导出历史", "GET", f"{BASE_URL}/api/export/history/test-id"))
    
    # Assets API
    results.append(test_endpoint("素材列表", "GET", f"{BASE_URL}/api/assets/list"))
    
    # AI API
    results.append(test_endpoint("AI 健康", "GET", f"{BASE_URL}/api/ai/health"))
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📊 结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    
    if passed < total:
        print("\n⚠️ 提示: 如果有端点返回 404，请重启后端服务使路由生效")
        print("   cd backend && python -m uvicorn main:app --reload")

if __name__ == "__main__":
    main()
