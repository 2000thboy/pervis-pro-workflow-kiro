#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pervis PRO 完整系统 E2E 验证测试
测试所有 Spec 功能：Project Wizard、System Agent、Export System
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, name, detail=""):
        self.passed.append({"name": name, "detail": detail})
        print(f"  ✅ {name}")
    
    def add_fail(self, name, error):
        self.failed.append({"name": name, "error": str(error)})
        print(f"  ❌ {name}: {error}")
    
    def add_warning(self, name, msg):
        self.warnings.append({"name": name, "msg": msg})
        print(f"  ⚠️ {name}: {msg}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        return {
            "total": total,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "warnings": len(self.warnings),
            "success_rate": f"{len(self.passed)/total*100:.1f}%" if total > 0 else "N/A"
        }


async def test_backend_health(session, result):
    """测试后端健康状态"""
    print("\n📡 测试后端健康状态...")
    
    try:
        async with session.get(f"{BASE_URL}/api/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("后端健康检查", f"状态: {data.get('status', 'ok')}")
            else:
                result.add_fail("后端健康检查", f"HTTP {resp.status}")
    except aiohttp.ClientError as e:
        result.add_fail("后端健康检查", f"连接失败: {e}")
        return False
    
    return True


async def test_wizard_api(session, result):
    """测试 Project Wizard API"""
    print("\n🧙 测试 Project Wizard API...")
    
    # 1. 测试健康检查
    try:
        async with session.get(f"{BASE_URL}/api/wizard/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("Wizard 健康检查", f"Agents: {len(data.get('agents', []))}")
            else:
                result.add_fail("Wizard 健康检查", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("Wizard 健康检查", str(e))
    
    # 2. 测试剧本解析
    try:
        test_script = """
        场景一：咖啡馆 - 日
        
        张三坐在窗边，看着窗外的雨。
        
        张三：今天的雨真大啊。
        
        李四走进来，抖落身上的雨水。
        
        李四：是啊，我都淋湿了。
        """
        
        async with session.post(
            f"{BASE_URL}/api/wizard/parse-script",
            json={"script_content": test_script, "format": "txt"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                scenes = data.get("scenes", [])
                characters = data.get("characters", [])
                result.add_pass("剧本解析 API", f"场景: {len(scenes)}, 角色: {len(characters)}")
            else:
                text = await resp.text()
                result.add_fail("剧本解析 API", f"HTTP {resp.status}: {text[:100]}")
    except Exception as e:
        result.add_fail("剧本解析 API", str(e))
    
    # 3. 测试内容生成
    try:
        async with session.post(
            f"{BASE_URL}/api/wizard/generate-content",
            json={
                "content_type": "logline",
                "context": {"title": "测试项目", "synopsis": "一个关于友情的故事"}
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("内容生成 API", f"任务ID: {data.get('task_id', 'N/A')}")
            else:
                result.add_warning("内容生成 API", f"HTTP {resp.status} (可能需要 LLM 服务)")
    except Exception as e:
        result.add_warning("内容生成 API", str(e))
    
    # 4. 测试草稿创建
    try:
        async with session.post(
            f"{BASE_URL}/api/wizard/draft",
            json={
                "title": "E2E 测试项目",
                "project_type": "short_film",
                "current_step": 1
            }
        ) as resp:
            if resp.status in [200, 201]:
                data = await resp.json()
                draft_id = data.get("id") or data.get("draft_id")
                result.add_pass("草稿创建 API", f"草稿ID: {draft_id}")
                return draft_id
            else:
                text = await resp.text()
                result.add_fail("草稿创建 API", f"HTTP {resp.status}: {text[:100]}")
    except Exception as e:
        result.add_fail("草稿创建 API", str(e))
    
    return None


async def test_system_agent_api(session, result):
    """测试 System Agent API"""
    print("\n🤖 测试 System Agent API...")
    
    # 1. 测试系统健康检查
    try:
        async with session.get(f"{BASE_URL}/api/system/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                checks = data.get("checks", {})
                passed_checks = sum(1 for v in checks.values() if v.get("status") == "ok")
                result.add_pass("系统健康检查 API", f"通过: {passed_checks}/{len(checks)}")
            else:
                result.add_fail("系统健康检查 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("系统健康检查 API", str(e))
    
    # 2. 测试通知列表
    try:
        async with session.get(f"{BASE_URL}/api/system/notifications") as resp:
            if resp.status == 200:
                data = await resp.json()
                notifications = data if isinstance(data, list) else data.get("notifications", [])
                result.add_pass("通知列表 API", f"通知数: {len(notifications)}")
            else:
                result.add_fail("通知列表 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("通知列表 API", str(e))
    
    # 3. 测试缓存清理
    try:
        async with session.post(f"{BASE_URL}/api/system/actions/clean-cache") as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("缓存清理 API", f"结果: {data.get('message', 'ok')}")
            else:
                result.add_warning("缓存清理 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_warning("缓存清理 API", str(e))


async def test_export_api(session, result):
    """测试 Export System API"""
    print("\n📦 测试 Export System API...")
    
    # 1. 测试剧本导出（需要项目ID）
    try:
        async with session.post(
            f"{BASE_URL}/api/export/script",
            json={
                "project_id": "test-project-id",
                "format": "markdown",
                "include_characters": True,
                "include_scenes": True
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("剧本导出 API", f"导出ID: {data.get('export_id', 'N/A')}")
            elif resp.status == 404:
                result.add_warning("剧本导出 API", "项目不存在（预期行为）")
            else:
                result.add_fail("剧本导出 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("剧本导出 API", str(e))
    
    # 2. 测试导出历史
    try:
        async with session.get(f"{BASE_URL}/api/export/history/test-project-id") as resp:
            if resp.status == 200:
                data = await resp.json()
                history = data if isinstance(data, list) else data.get("history", [])
                result.add_pass("导出历史 API", f"记录数: {len(history)}")
            elif resp.status == 404:
                result.add_warning("导出历史 API", "项目不存在（预期行为）")
            else:
                result.add_fail("导出历史 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("导出历史 API", str(e))
    
    # 3. 测试视频导出状态
    try:
        async with session.get(f"{BASE_URL}/api/export/timeline/video/status/test-task-id") as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("视频导出状态 API", f"状态: {data.get('status', 'N/A')}")
            elif resp.status == 404:
                result.add_warning("视频导出状态 API", "任务不存在（预期行为）")
            else:
                result.add_fail("视频导出状态 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("视频导出状态 API", str(e))


async def test_asset_api(session, result):
    """测试素材管理 API"""
    print("\n🎬 测试素材管理 API...")
    
    # 1. 测试素材列表
    try:
        async with session.get(f"{BASE_URL}/api/assets/list") as resp:
            if resp.status == 200:
                data = await resp.json()
                assets = data if isinstance(data, list) else data.get("assets", [])
                result.add_pass("素材列表 API", f"素材数: {len(assets)}")
            else:
                result.add_fail("素材列表 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_fail("素材列表 API", str(e))
    
    # 2. 测试搜索 API
    try:
        async with session.get(f"{BASE_URL}/api/assets/search?query=test") as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get("results", []) if isinstance(data, dict) else data
                result.add_pass("搜索 API", f"结果数: {len(results)}")
            else:
                result.add_warning("搜索 API", f"HTTP {resp.status}")
    except Exception as e:
        result.add_warning("搜索 API", str(e))


async def test_ai_api(session, result):
    """测试 AI 服务 API"""
    print("\n🧠 测试 AI 服务 API...")
    
    # 1. 测试 AI 健康检查
    try:
        async with session.get(f"{BASE_URL}/api/ai/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                result.add_pass("AI 健康检查", f"状态: {data.get('status', 'ok')}")
            else:
                result.add_warning("AI 健康检查", f"HTTP {resp.status}")
    except Exception as e:
        result.add_warning("AI 健康检查", str(e))
    
    # 2. 测试 LLM 提供者列表
    try:
        async with session.get(f"{BASE_URL}/api/ai/providers") as resp:
            if resp.status == 200:
                data = await resp.json()
                providers = data if isinstance(data, list) else data.get("providers", [])
                result.add_pass("LLM 提供者列表", f"提供者数: {len(providers)}")
            else:
                result.add_warning("LLM 提供者列表", f"HTTP {resp.status}")
    except Exception as e:
        result.add_warning("LLM 提供者列表", str(e))


async def test_frontend_availability(session, result):
    """测试前端可用性"""
    print("\n🖥️ 测试前端可用性...")
    
    try:
        async with session.get(FRONTEND_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                result.add_pass("前端服务", f"HTTP {resp.status}")
            else:
                result.add_warning("前端服务", f"HTTP {resp.status}")
    except aiohttp.ClientError as e:
        result.add_warning("前端服务", f"未运行或无法连接: {e}")


async def test_websocket(result):
    """测试 WebSocket 连接"""
    print("\n🔌 测试 WebSocket 连接...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"ws://localhost:8000/ws/events", timeout=5) as ws:
                result.add_pass("WebSocket 连接", "连接成功")
                await ws.close()
    except Exception as e:
        result.add_warning("WebSocket 连接", f"无法连接: {e}")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 Pervis PRO 完整系统 E2E 验证测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    result = TestResult()
    
    async with aiohttp.ClientSession() as session:
        # 1. 后端健康检查
        backend_ok = await test_backend_health(session, result)
        
        if not backend_ok:
            print("\n❌ 后端服务未运行，请先启动后端服务：")
            print("   cd 'Pervis PRO/backend' && py -m uvicorn main:app --reload")
            return result
        
        # 2. Project Wizard API
        await test_wizard_api(session, result)
        
        # 3. System Agent API
        await test_system_agent_api(session, result)
        
        # 4. Export System API
        await test_export_api(session, result)
        
        # 5. 素材管理 API
        await test_asset_api(session, result)
        
        # 6. AI 服务 API
        await test_ai_api(session, result)
        
        # 7. 前端可用性
        await test_frontend_availability(session, result)
    
    # 8. WebSocket 测试
    await test_websocket(result)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    summary = result.summary()
    print(f"  总测试数: {summary['total']}")
    print(f"  ✅ 通过: {summary['passed']}")
    print(f"  ❌ 失败: {summary['failed']}")
    print(f"  ⚠️ 警告: {summary['warnings']}")
    print(f"  成功率: {summary['success_rate']}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "passed": result.passed,
        "failed": result.failed,
        "warnings": result.warnings
    }
    
    report_path = Path(__file__).parent / f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 报告已保存: {report_path}")
    
    return result


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    
    # 返回退出码
    if result.failed:
        sys.exit(1)
    sys.exit(0)
