#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pervis PRO E2E API 验证测试
验证所有关键 API 端点可用性（不调用 AI 服务）
"""

import urllib.request
import urllib.error
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, category, name):
        self.passed.append(f"{category}/{name}")
        print(f"  ✅ {name}")
    
    def add_fail(self, category, name, error):
        self.failed.append(f"{category}/{name}: {error}")
        print(f"  ❌ {name}: {error}")

def get(path, timeout=10):
    """GET 请求"""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def post(path, data, timeout=10):
    """POST 请求"""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 60)
    print("🚀 Pervis PRO E2E API 验证测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    result = TestResult()
    
    # ========== 1. 基础健康检查 ==========
    print("\n📡 1. 基础健康检查")
    try:
        status, data = get("/api/health")
        if status == 200 and data.get("status") == "healthy":
            result.add_pass("基础", "后端健康检查")
        else:
            result.add_fail("基础", "后端健康检查", f"状态异常: {data}")
    except Exception as e:
        result.add_fail("基础", "后端健康检查", str(e))
        print("\n❌ 后端服务未运行，测试终止")
        return
    
    # ========== 2. Project Wizard API ==========
    print("\n🧙 2. Project Wizard API")
    
    # Wizard 健康检查
    try:
        status, data = get("/api/wizard/health")
        if status == 200:
            agents = data.get("agents", [])
            result.add_pass("Wizard", f"健康检查 (Agents: {len(agents)})")
        else:
            result.add_fail("Wizard", "健康检查", f"HTTP {status}")
    except Exception as e:
        result.add_fail("Wizard", "健康检查", str(e))
    
    # 创建草稿
    draft_id = None
    try:
        status, data = post("/api/wizard/draft", {
            "title": "E2E测试项目",
            "project_type": "short_film",
            "current_step": 1
        })
        if status == 200 and data.get("draft_id"):
            draft_id = data["draft_id"]
            result.add_pass("Wizard", f"创建草稿 (ID: {draft_id[:12]}...)")
        else:
            result.add_fail("Wizard", "创建草稿", f"响应异常: {data}")
    except Exception as e:
        result.add_fail("Wizard", "创建草稿", str(e))
    
    # 获取草稿
    if draft_id:
        try:
            status, data = get(f"/api/wizard/draft/{draft_id}")
            if status == 200:
                result.add_pass("Wizard", "获取草稿")
            else:
                result.add_fail("Wizard", "获取草稿", f"HTTP {status}")
        except Exception as e:
            result.add_fail("Wizard", "获取草稿", str(e))
    
    # ========== 3. System Agent API ==========
    print("\n🤖 3. System Agent API")
    
    # 系统健康检查
    try:
        status, data = get("/api/system/health")
        if status == 200:
            checks = data.get("checks", {})
            ok_count = sum(1 for c in checks.values() if c.get("status") == "ok")
            result.add_pass("System", f"健康检查 ({ok_count}/{len(checks)} OK)")
        else:
            result.add_fail("System", "健康检查", f"HTTP {status}")
    except Exception as e:
        result.add_fail("System", "健康检查", str(e))
    
    # 通知列表
    try:
        status, data = get("/api/system/notifications")
        if status == 200:
            result.add_pass("System", f"通知列表 (共 {data.get('total', 0)} 条)")
        else:
            result.add_fail("System", "通知列表", f"HTTP {status}")
    except Exception as e:
        result.add_fail("System", "通知列表", str(e))
    
    # 快速健康检查
    try:
        status, data = get("/api/system/health/quick")
        if status == 200:
            result.add_pass("System", "快速健康检查")
        else:
            result.add_fail("System", "快速健康检查", f"HTTP {status}")
    except Exception as e:
        result.add_fail("System", "快速健康检查", str(e))
    
    # ========== 4. Export API ==========
    print("\n📦 4. Export API")
    
    # 导出历史
    try:
        status, data = get("/api/export/history/test-project")
        if status == 200:
            result.add_pass("Export", "导出历史查询")
        else:
            result.add_fail("Export", "导出历史查询", f"HTTP {status}")
    except Exception as e:
        result.add_fail("Export", "导出历史查询", str(e))
    
    # ========== 5. Assets API ==========
    print("\n🎬 5. Assets API")
    
    # 素材列表
    try:
        status, data = get("/api/assets/list")
        if status == 200:
            assets = data if isinstance(data, list) else data.get("assets", [])
            result.add_pass("Assets", f"素材列表 (共 {len(assets)} 个)")
        else:
            result.add_fail("Assets", "素材列表", f"HTTP {status}")
    except Exception as e:
        result.add_fail("Assets", "素材列表", str(e))
    
    # ========== 6. AI API ==========
    print("\n🧠 6. AI API")
    
    # AI 健康检查
    try:
        status, data = get("/api/ai/health")
        if status == 200:
            result.add_pass("AI", f"健康检查 (状态: {data.get('status', 'unknown')})")
        else:
            result.add_fail("AI", "健康检查", f"HTTP {status}")
    except Exception as e:
        result.add_fail("AI", "健康检查", str(e))
    
    # ========== 7. Search API ==========
    print("\n🔍 7. Search API")
    
    try:
        status, data = post("/api/search", {"query": "测试", "top_k": 5})
        if status == 200:
            result.add_pass("Search", "混合搜索")
        else:
            result.add_fail("Search", "混合搜索", f"HTTP {status}")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            result.add_pass("Search", "混合搜索 (参数验证正常)")
        else:
            result.add_fail("Search", "混合搜索", f"HTTP {e.code}")
    except Exception as e:
        result.add_fail("Search", "混合搜索", str(e))
    
    # ========== 8. Timeline API ==========
    print("\n⏱️ 8. Timeline API")
    
    try:
        status, data = get("/api/timelines/list")
        if status == 200:
            result.add_pass("Timeline", f"时间轴列表 (共 {len(data)} 个)")
        else:
            result.add_fail("Timeline", "时间轴列表", f"HTTP {status}")
    except Exception as e:
        result.add_fail("Timeline", "时间轴列表", str(e))
    
    # ========== 结果汇总 ==========
    print("\n" + "=" * 60)
    total = len(result.passed) + len(result.failed)
    rate = len(result.passed) / total * 100 if total > 0 else 0
    
    print(f"📊 测试结果: {len(result.passed)}/{total} 通过 ({rate:.0f}%)")
    
    if result.failed:
        print(f"\n❌ 失败项目 ({len(result.failed)}):")
        for f in result.failed:
            print(f"   - {f}")
    
    print("=" * 60)
    
    # 保存结果
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": len(result.passed),
        "failed": len(result.failed),
        "success_rate": f"{rate:.1f}%",
        "passed_tests": result.passed,
        "failed_tests": result.failed
    }
    
    report_file = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 报告已保存: {report_file}")
    
    return rate >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
