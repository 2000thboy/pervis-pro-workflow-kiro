"""
项目立项向导系统 - Final Checkpoint 验证脚本
验证完整建档流程、素材预处理管道、Storyboard_Agent 素材召回
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 测试结果收集
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}

def log_test(name: str, status: str, message: str = "", details: dict = None):
    """记录测试结果"""
    result = {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {}
    }
    test_results["tests"].append(result)
    test_results["summary"]["total"] += 1
    if status == "PASS":
        test_results["summary"]["passed"] += 1
        print(f"  ✅ {name}")
    elif status == "FAIL":
        test_results["summary"]["failed"] += 1
        print(f"  ❌ {name}: {message}")
    else:
        test_results["summary"]["skipped"] += 1
        print(f"  ⏭️ {name}: {message}")


async def test_backend_api_health():
    """测试后端 API 健康状态"""
    print("\n📡 测试后端 API 健康状态...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试基础健康检查
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                log_test("基础健康检查", "PASS")
            else:
                log_test("基础健康检查", "FAIL", f"状态码: {response.status_code}")
            
            # 测试 Wizard 健康检查
            response = await client.get("http://localhost:8000/api/wizard/health")
            if response.status_code == 200:
                data = response.json()
                log_test("Wizard 健康检查", "PASS", details=data)
            else:
                log_test("Wizard 健康检查", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("后端 API 连接", "FAIL", str(e))
        return False
    
    return True


async def test_script_parsing():
    """测试剧本解析功能"""
    print("\n📜 测试剧本解析功能...")
    
    test_script = """
INT. 咖啡馆 - 日

张三坐在窗边，看着窗外的雨。

张三
（自言自语）
今天的雨下得真大。

李四走进咖啡馆，看到张三。

李四
张三！好久不见！

张三
（惊讶）
李四？你怎么在这里？

EXT. 街道 - 夜

张三和李四走在雨中。

张三
谢谢你今天陪我。

李四
不客气，朋友就是要互相帮助。
"""
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/wizard/parse-script",
                json={"script_content": test_script}
            )
            
            if response.status_code == 200:
                data = response.json()
                scenes = data.get("scenes", [])
                characters = data.get("characters", [])
                
                if len(scenes) >= 2:
                    log_test("场次解析", "PASS", details={"scene_count": len(scenes)})
                else:
                    log_test("场次解析", "FAIL", f"只解析出 {len(scenes)} 个场次")
                
                if len(characters) >= 2:
                    log_test("角色提取", "PASS", details={"character_count": len(characters)})
                else:
                    log_test("角色提取", "FAIL", f"只提取出 {len(characters)} 个角色")
                
                if data.get("source") == "script_agent":
                    log_test("来源标记", "PASS")
                else:
                    log_test("来源标记", "FAIL", f"来源: {data.get('source')}")
                    
            else:
                log_test("剧本解析 API", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("剧本解析", "FAIL", str(e))


async def test_content_generation():
    """测试内容生成功能"""
    print("\n✨ 测试内容生成功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 测试 Logline 生成
            response = await client.post(
                "http://localhost:8000/api/wizard/generate-content",
                json={
                    "project_id": "test-project-001",
                    "content_type": "logline",
                    "context": {
                        "title": "雨中重逢",
                        "synopsis": "两个老朋友在咖啡馆偶遇，回忆起过去的时光"
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("content"):
                    log_test("Logline 生成", "PASS")
                else:
                    log_test("Logline 生成", "FAIL", "内容为空")
            else:
                log_test("Logline 生成", "FAIL", f"状态码: {response.status_code}")
            
            # 测试人物小传生成
            response = await client.post(
                "http://localhost:8000/api/wizard/generate-content",
                json={
                    "project_id": "test-project-001",
                    "content_type": "character_bio",
                    "context": {
                        "character_name": "张三",
                        "dialogue_count": 5,
                        "scenes": ["咖啡馆", "街道"]
                    },
                    "entity_name": "张三"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("content"):
                    log_test("人物小传生成", "PASS")
                else:
                    log_test("人物小传生成", "FAIL", "内容为空")
            else:
                log_test("人物小传生成", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("内容生成", "FAIL", str(e))


async def test_content_review():
    """测试内容审核功能"""
    print("\n🔍 测试内容审核功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/wizard/review-content",
                json={
                    "project_id": "test-project-001",
                    "content_type": "logline",
                    "content": "两个老朋友在雨天的咖啡馆重逢，回忆起青春岁月，重新找回友谊的温暖。"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test("Director_Agent 审核", "PASS", details={
                    "status": data.get("status"),
                    "suggestions_count": len(data.get("suggestions", []))
                })
            else:
                log_test("Director_Agent 审核", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("内容审核", "FAIL", str(e))


async def test_project_crud():
    """测试项目 CRUD 操作"""
    print("\n📁 测试项目 CRUD 操作...")
    
    project_id = None
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 创建项目
            response = await client.post(
                "http://localhost:8000/api/wizard/create-project",
                json={
                    "title": "测试项目 - Final Checkpoint",
                    "project_type": "short_film",
                    "duration_minutes": 15,
                    "aspect_ratio": "16:9",
                    "frame_rate": 24,
                    "synopsis": "这是一个测试项目"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("project_id"):
                    project_id = data["project_id"]
                    log_test("创建项目", "PASS", details={"project_id": project_id})
                else:
                    log_test("创建项目", "FAIL", data.get("message", "未知错误"))
            else:
                log_test("创建项目", "FAIL", f"状态码: {response.status_code}")
                return
            
            # 获取项目
            if project_id:
                response = await client.get(f"http://localhost:8000/api/wizard/project/{project_id}")
                if response.status_code == 200:
                    log_test("获取项目", "PASS")
                else:
                    log_test("获取项目", "FAIL", f"状态码: {response.status_code}")
            
            # 更新项目
            if project_id:
                response = await client.put(
                    f"http://localhost:8000/api/wizard/project/{project_id}",
                    json={"title": "测试项目 - 已更新"}
                )
                if response.status_code == 200:
                    log_test("更新项目", "PASS")
                else:
                    log_test("更新项目", "FAIL", f"状态码: {response.status_code}")
            
            # 列出项目
            response = await client.get("http://localhost:8000/api/wizard/projects")
            if response.status_code == 200:
                data = response.json()
                log_test("列出项目", "PASS", details={"total": data.get("total", 0)})
            else:
                log_test("列出项目", "FAIL", f"状态码: {response.status_code}")
            
            # 删除项目
            if project_id:
                response = await client.delete(f"http://localhost:8000/api/wizard/project/{project_id}")
                if response.status_code == 200:
                    log_test("删除项目", "PASS")
                else:
                    log_test("删除项目", "FAIL", f"状态码: {response.status_code}")
                    
    except Exception as e:
        log_test("项目 CRUD", "FAIL", str(e))


async def test_version_management():
    """测试版本管理功能"""
    print("\n📚 测试版本管理功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 记录版本
            response = await client.post(
                "http://localhost:8000/api/wizard/record-version",
                json={
                    "project_id": "test-version-project",
                    "content_type": "logline",
                    "content": "测试版本内容",
                    "source": "user"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log_test("记录版本", "PASS")
                else:
                    log_test("记录版本", "FAIL", data.get("error", "未知错误"))
            else:
                log_test("记录版本", "FAIL", f"状态码: {response.status_code}")
            
            # 获取版本历史
            response = await client.get("http://localhost:8000/api/wizard/version-history/test-version-project")
            if response.status_code == 200:
                data = response.json()
                log_test("获取版本历史", "PASS", details={"version_count": len(data.get("versions", []))})
            else:
                log_test("获取版本历史", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("版本管理", "FAIL", str(e))


async def test_asset_recall():
    """测试素材召回功能"""
    print("\n🎬 测试素材召回功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/wizard/recall-assets",
                json={
                    "scene_id": "test-scene-001",
                    "query": "咖啡馆 室内 日景",
                    "strategy": "hybrid"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                has_match = data.get("has_match", False)
                
                if has_match and len(candidates) > 0:
                    log_test("素材召回 (有匹配)", "PASS", details={
                        "candidate_count": len(candidates),
                        "total_searched": data.get("total_searched", 0)
                    })
                else:
                    # 没有匹配也是正常的，只要 API 正常工作
                    log_test("素材召回 (无匹配)", "PASS", details={
                        "placeholder": data.get("placeholder_message", "")
                    })
            else:
                log_test("素材召回", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("素材召回", "FAIL", str(e))


async def test_market_analysis():
    """测试市场分析功能"""
    print("\n📊 测试市场分析功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/wizard/market-analysis",
                json={
                    "project_id": "test-market-project",
                    "project_type": "short_film",
                    "genre": "drama"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test("市场分析生成", "PASS", details={
                    "is_dynamic": data.get("is_dynamic", False),
                    "has_audience": bool(data.get("target_audience")),
                    "has_positioning": bool(data.get("market_positioning"))
                })
            else:
                log_test("市场分析生成", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("市场分析", "FAIL", str(e))


async def test_project_validation():
    """测试项目验证功能"""
    print("\n✅ 测试项目验证功能...")
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 测试有效项目
            response = await client.post(
                "http://localhost:8000/api/wizard/validate-project",
                json={
                    "title": "有效测试项目",
                    "project_type": "short_film",
                    "synopsis": "这是一个有效的测试项目"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_valid"):
                    log_test("有效项目验证", "PASS", details={
                        "completion": data.get("completion_percentage", 0)
                    })
                else:
                    log_test("有效项目验证", "FAIL", f"验证失败: {data.get('errors', [])}")
            else:
                log_test("有效项目验证", "FAIL", f"状态码: {response.status_code}")
            
            # 测试无效项目（缺少必填字段）
            response = await client.post(
                "http://localhost:8000/api/wizard/validate-project",
                json={"title": ""}
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("is_valid") and len(data.get("errors", [])) > 0:
                    log_test("无效项目验证", "PASS", details={
                        "error_count": len(data.get("errors", []))
                    })
                else:
                    log_test("无效项目验证", "FAIL", "应该返回验证错误")
            else:
                log_test("无效项目验证", "FAIL", f"状态码: {response.status_code}")
                
    except Exception as e:
        log_test("项目验证", "FAIL", str(e))


async def test_draft_management():
    """测试草稿管理功能"""
    print("\n💾 测试草稿管理功能...")
    
    draft_id = None
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 创建草稿
            response = await client.post(
                "http://localhost:8000/api/wizard/draft",
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                draft_id = data.get("draft_id")
                if draft_id:
                    log_test("创建草稿", "PASS", details={"draft_id": draft_id})
                else:
                    log_test("创建草稿", "FAIL", "未返回 draft_id")
            else:
                log_test("创建草稿", "FAIL", f"状态码: {response.status_code}")
                return
            
            # 保存草稿
            if draft_id:
                response = await client.put(
                    f"http://localhost:8000/api/wizard/draft/{draft_id}",
                    json={
                        "current_step": 2,
                        "form_data": {
                            "title": "草稿测试项目",
                            "project_type": "short_film"
                        }
                    }
                )
                
                if response.status_code == 200:
                    log_test("保存草稿", "PASS")
                else:
                    log_test("保存草稿", "FAIL", f"状态码: {response.status_code}")
            
            # 加载草稿
            if draft_id:
                response = await client.get(f"http://localhost:8000/api/wizard/draft/{draft_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("current_step") == 2:
                        log_test("加载草稿", "PASS")
                    else:
                        log_test("加载草稿", "FAIL", "数据不匹配")
                else:
                    log_test("加载草稿", "FAIL", f"状态码: {response.status_code}")
                    
    except Exception as e:
        log_test("草稿管理", "FAIL", str(e))


async def test_frontend_components():
    """验证前端组件文件存在"""
    print("\n🎨 验证前端组件文件...")
    
    components = [
        "frontend/components/ProjectWizard/index.tsx",
        "frontend/components/ProjectWizard/types.ts",
        "frontend/components/ProjectWizard/api.ts",
        "frontend/components/ProjectWizard/WizardContext.tsx",
        "frontend/components/ProjectWizard/WizardStep1_BasicInfo.tsx",
        "frontend/components/ProjectWizard/WizardStep2_Script.tsx",
        "frontend/components/ProjectWizard/WizardStep3_Characters.tsx",
        "frontend/components/ProjectWizard/WizardStep4_Scenes.tsx",
        "frontend/components/ProjectWizard/WizardStep5_References.tsx",
        "frontend/components/ProjectWizard/WizardStep6_Confirm.tsx",
        "frontend/components/ProjectWizard/AgentStatusPanel.tsx",
        "frontend/components/ProjectWizard/VersionHistoryPanel.tsx",
        "frontend/components/ProjectWizard/CandidateSwitcher.tsx",
        "frontend/components/ProjectWizard/MissingContentDialog.tsx",
        "frontend/components/ProjectWizard/MarketAnalysisPanel.tsx",
        "frontend/components/ProjectWizard/DataTypeIndicator.tsx",
        "frontend/components/ProjectWizard/exports.ts",
    ]
    
    missing = []
    for component in components:
        if Path(component).exists():
            pass
        else:
            missing.append(component)
    
    if not missing:
        log_test("前端组件文件完整性", "PASS", details={"component_count": len(components)})
    else:
        log_test("前端组件文件完整性", "FAIL", f"缺失: {missing}")


async def test_backend_services():
    """验证后端服务文件存在"""
    print("\n⚙️ 验证后端服务文件...")
    
    services = [
        "backend/services/agent_service.py",
        "backend/services/agents/script_agent.py",
        "backend/services/agents/art_agent.py",
        "backend/services/agents/director_agent.py",
        "backend/services/agents/pm_agent.py",
        "backend/services/agents/storyboard_agent.py",
        "backend/services/agents/market_agent.py",
        "backend/services/agents/system_agent.py",
        "backend/services/milvus_store.py",
        "backend/services/video_preprocessor.py",
        "backend/routers/wizard.py",
    ]
    
    missing = []
    for service in services:
        if Path(service).exists():
            pass
        else:
            missing.append(service)
    
    if not missing:
        log_test("后端服务文件完整性", "PASS", details={"service_count": len(services)})
    else:
        log_test("后端服务文件完整性", "FAIL", f"缺失: {missing}")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 Pervis PRO 项目立项向导 - Final Checkpoint 验证")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 文件完整性检查
    await test_frontend_components()
    await test_backend_services()
    
    # API 测试（需要后端运行）
    api_available = await test_backend_api_health()
    
    if api_available:
        await test_script_parsing()
        await test_content_generation()
        await test_content_review()
        await test_project_crud()
        await test_version_management()
        await test_asset_recall()
        await test_market_analysis()
        await test_project_validation()
        await test_draft_management()
    else:
        print("\n⚠️ 后端 API 不可用，跳过 API 测试")
        print("   请确保后端服务运行在 http://localhost:8000")
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"总计: {test_results['summary']['total']}")
    print(f"通过: {test_results['summary']['passed']} ✅")
    print(f"失败: {test_results['summary']['failed']} ❌")
    print(f"跳过: {test_results['summary']['skipped']} ⏭️")
    
    # 计算通过率
    if test_results['summary']['total'] > 0:
        pass_rate = test_results['summary']['passed'] / test_results['summary']['total'] * 100
        print(f"通过率: {pass_rate:.1f}%")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"wizard_final_checkpoint_{timestamp}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 详细结果已保存到: {result_file}")
    
    # 返回状态码
    if test_results['summary']['failed'] == 0:
        print("\n🎉 Final Checkpoint 验证通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查详细结果")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
