#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""简单 API 测试 - 使用 urllib"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"

def test_get(name, path):
    """测试 GET 端点"""
    try:
        url = f"{BASE_URL}{path}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            print(f"✅ {name}: HTTP {status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"⚠️ {name}: HTTP {e.code}")
        return e.code in [200, 201]
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}")
        return False

def test_post(name, path, data):
    """测试 POST 端点"""
    try:
        url = f"{BASE_URL}{path}"
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            print(f"✅ {name}: HTTP {status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"⚠️ {name}: HTTP {e.code}")
        return e.code in [200, 201]
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}")
        return False

def main():
    print("=" * 50)
    print("🔍 Pervis PRO API 简单测试")
    print("=" * 50)
    
    results = []
    
    # 基础端点
    results.append(test_get("健康检查", "/api/health"))
    results.append(test_get("Wizard 健康", "/api/wizard/health"))
    results.append(test_get("系统健康", "/api/system/health"))
    results.append(test_get("通知列表", "/api/system/notifications"))
    results.append(test_get("素材列表", "/api/assets/list"))
    results.append(test_get("AI 健康", "/api/ai/health"))
    results.append(test_get("导出历史", "/api/export/history/test-id"))
    
    # POST 端点
    results.append(test_post("创建草稿", "/api/wizard/draft", 
                             {"title": "测试", "project_type": "short_film"}))
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📊 结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

if __name__ == "__main__":
    main()
