# -*- coding: utf-8 -*-
"""
Wizard 完整流程验证测试

验证 Phase 0-4 的后端逻辑是否与 spec 一致
"""

import asyncio
import sys
import io

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'backend')

from datetime import datetime


class FlowValidator:
    """流程验证器"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def log(self, phase: str, task: str, status: str, detail: str = ""):
        """记录验证结果"""
        icon = "[PASS]" if status == "pass" else "[FAIL]" if status == "fail" else "[WARN]"
        self.results.append({
            "phase": phase,
            "task": task,
            "status": status,
            "detail": detail
        })
        print(f"  {icon} [{phase}] {task}: {detail}")
        if status == "fail":
            self.errors.append(f"{phase}/{task}: {detail}")
    
    def summary(self):
        """输出汇总"""
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        warned = sum(1 for r in self.results if r["status"] == "warn")
        
        print("\n" + "=" * 70)
        print(f"验证结果: {passed} 通过, {failed} 失败, {warned} 警告")
        print("=" * 70)
        
        if self.errors:
            print("\n失败项:")
            for e in self.errors:
                print(f"  - {e}")
        
        return failed == 0


async def validate_phase_0_fix(v: FlowValidator):
    """验证 Phase 0-Fix: 框架修复"""
    print("\n" + "=" * 70)
    print("Phase 0-Fix: 框架修复验证")
    print("=" * 70)
    
    # 0-Fix.1 LLM 服务适配层
    try:
        from services.agent_llm_adapter import get_agent_llm_adapter, AgentType
        adapter = get_agent_llm_adapter()
        v.log("0-Fix.1", "LLM适配层", "pass", "AgentLLMAdapter 加载成功")
        
        # 检查支持的 Agent 类型
        expected_types = ["SCRIPT", "ART", "DIRECTOR", "PM", "MARKET", "STORYBOARD", "SYSTEM"]
        for t in expected_types:
            if hasattr(AgentType, t):
                v.log("0-Fix.1", f"AgentType.{t}", "pass", "已定义")
            else:
                v.log("0-Fix.1", f"AgentType.{t}", "fail", "未定义")
    except Exception as e:
        v.log("0-Fix.1", "LLM适配层", "fail", str(e))
    
    # 0-Fix.2 Script_Agent 集成 LLM
    try:
        from services.agents.script_agent import get_script_agent_service
        script_agent = get_script_agent_service()
        
        # 检查方法
        methods = ["parse_script", "generate_logline", "generate_synopsis", 
                   "generate_character_bio", "generate_character_tags", "estimate_scene_duration"]
        for m in methods:
            if hasattr(script_agent, m):
                v.log("0-Fix.2", f"Script_Agent.{m}", "pass", "方法存在")
            else:
                v.log("0-Fix.2", f"Script_Agent.{m}", "fail", "方法不存在")
    except Exception as e:
        v.log("0-Fix.2", "Script_Agent", "fail", str(e))
    
    # 0-Fix.3 Art_Agent 集成 LLM
    try:
        from services.agents.art_agent import get_art_agent_service
        art_agent = get_art_agent_service()
        
        methods = ["classify_file", "extract_metadata", "generate_tags"]
        for m in methods:
            if hasattr(art_agent, m):
                v.log("0-Fix.3", f"Art_Agent.{m}", "pass", "方法存在")
            else:
                v.log("0-Fix.3", f"Art_Agent.{m}", "fail", "方法不存在")
    except Exception as e:
        v.log("0-Fix.3", "Art_Agent", "fail", str(e))
    
    # 0-Fix.4 Director_Agent 项目记忆
    try:
        from services.agents.director_agent import get_director_agent_service
        director_agent = get_director_agent_service()
        
        methods = ["review", "_check_rules", "_check_style_consistency"]
        for m in methods:
            if hasattr(director_agent, m):
                v.log("0-Fix.4", f"Director_Agent.{m}", "pass", "方法存在")
            else:
                v.log("0-Fix.4", f"Director_Agent.{m}", "fail", "方法不存在")
        
        # 测试审核功能
        result = await director_agent.review(
            result={"logline": "测试内容"},
            task_type="logline",
            project_id="test_project"
        )
        if result.status in ["approved", "suggestions", "rejected"]:
            v.log("0-Fix.4", "Director_Agent.review()", "pass", f"审核结果: {result.status}")
        else:
            v.log("0-Fix.4", "Director_Agent.review()", "fail", f"无效状态: {result.status}")
    except Exception as e:
        v.log("0-Fix.4", "Director_Agent", "fail", str(e))
    
    # 0-Fix.5 PM_Agent 版本管理
    try:
        from services.agents.pm_agent import get_pm_agent_service
        pm_agent = get_pm_agent_service()
        
        methods = ["record_version", "generate_version_name", "record_decision", 
                   "get_version_display_info", "restore_version"]
        for m in methods:
            if hasattr(pm_agent, m):
                v.log("0-Fix.5", f"PM_Agent.{m}", "pass", "方法存在")
            else:
                v.log("0-Fix.5", f"PM_Agent.{m}", "fail", "方法不存在")
        
        # 测试版本命名
        name = pm_agent.generate_version_name("角色", "张三", 1)
        if name == "角色_张三_v1":
            v.log("0-Fix.5", "版本命名格式", "pass", name)
        else:
            v.log("0-Fix.5", "版本命名格式", "fail", f"期望 '角色_张三_v1', 得到 '{name}'")
    except Exception as e:
        v.log("0-Fix.5", "PM_Agent", "fail", str(e))
    
    # 0-Fix.6 Storyboard_Agent
    try:
        from services.agents.storyboard_agent import get_storyboard_agent_service
        storyboard_agent = get_storyboard_agent_service()
        
        methods = ["recall_assets", "get_cached_candidates", "switch_candidate", "rough_cut"]
        for m in methods:
            if hasattr(storyboard_agent, m):
                v.log("0-Fix.6", f"Storyboard_Agent.{m}", "pass", "方法存在")
            else:
                v.log("0-Fix.6", f"Storyboard_Agent.{m}", "fail", "方法不存在")
    except Exception as e:
        v.log("0-Fix.6", "Storyboard_Agent", "fail", str(e))
    
    # 0-Fix.7 REST API 路由层
    try:
        from routers.wizard import router
        
        # 检查路由
        routes = [r.path for r in router.routes]
        expected_routes = [
            "/parse-script", "/generate-content", "/process-assets",
            "/task-status/{task_id}", "/recall-assets", "/review-content",
            "/switch-candidate", "/cached-candidates/{scene_id}", "/health",
            "/create-project", "/validate-project", "/record-version",
            "/version-history/{project_id}", "/market-analysis",
            "/validate-export", "/check-tag-consistency", "/api-health"
        ]
        
        for route in expected_routes:
            if route in routes:
                v.log("0-Fix.7", f"API {route}", "pass", "路由存在")
            else:
                v.log("0-Fix.7", f"API {route}", "warn", "路由不存在")
    except Exception as e:
        v.log("0-Fix.7", "REST API", "fail", str(e))


async def validate_phase_0(v: FlowValidator):
    """验证 Phase 0: 基础设施安装"""
    print("\n" + "=" * 70)
    print("Phase 0: 基础设施安装验证")
    print("=" * 70)
    
    # 0.1 PySceneDetect
    try:
        import scenedetect
        v.log("0.1", "PySceneDetect", "pass", f"版本 {scenedetect.__version__}")
    except ImportError:
        v.log("0.1", "PySceneDetect", "warn", "未安装 (可选)")
    
    # 0.2 Gemini SDK
    try:
        import google.generativeai
        v.log("0.2", "Gemini SDK", "pass", "已安装")
    except ImportError:
        v.log("0.2", "Gemini SDK", "fail", "未安装")
    
    # 0.3 Milvus (可选)
    try:
        from pymilvus import connections
        v.log("0.3", "pymilvus", "pass", "已安装")
    except ImportError:
        v.log("0.3", "pymilvus", "warn", "未安装 (可选，使用内存存储)")
    
    # 0.4 sentence-transformers
    try:
        import sentence_transformers
        v.log("0.4", "sentence-transformers", "pass", "已安装")
    except ImportError:
        v.log("0.4", "sentence-transformers", "warn", "未安装 (向量搜索不可用)")


async def validate_phase_1(v: FlowValidator):
    """验证 Phase 1: 素材预处理管道"""
    print("\n" + "=" * 70)
    print("Phase 1: 素材预处理管道验证")
    print("=" * 70)
    
    # 1.1 MilvusVideoStore / MemoryVideoStore
    try:
        from services.milvus_store import MemoryVideoStore
        store = MemoryVideoStore()
        v.log("1.1", "MemoryVideoStore", "pass", "加载成功")
        
        methods = ["insert", "search", "search_by_tags"]
        for m in methods:
            if hasattr(store, m):
                v.log("1.1", f"VideoStore.{m}", "pass", "方法存在")
            else:
                v.log("1.1", f"VideoStore.{m}", "fail", "方法不存在")
    except Exception as e:
        v.log("1.1", "VideoStore", "fail", str(e))
    
    # 1.2 VideoPreprocessor
    try:
        from services.video_preprocessor import VideoPreprocessor
        preprocessor = VideoPreprocessor()
        v.log("1.2", "VideoPreprocessor", "pass", "加载成功")
        
        methods = ["preprocess", "_split_video", "_generate_tags"]
        for m in methods:
            if hasattr(preprocessor, m):
                v.log("1.2", f"VideoPreprocessor.{m}", "pass", "方法存在")
            else:
                v.log("1.2", f"VideoPreprocessor.{m}", "warn", "方法不存在")
    except Exception as e:
        v.log("1.2", "VideoPreprocessor", "fail", str(e))
    
    # 1.3 素材上传集成
    try:
        from routers.assets import router as assets_router
        routes = [r.path for r in assets_router.routes]
        
        if "/preprocess" in routes or any("preprocess" in r for r in routes):
            v.log("1.3", "素材预处理端点", "pass", "已集成")
        else:
            v.log("1.3", "素材预处理端点", "warn", "未找到专用端点")
    except Exception as e:
        v.log("1.3", "素材上传集成", "fail", str(e))


async def validate_phase_2(v: FlowValidator):
    """验证 Phase 2: AgentService 层"""
    print("\n" + "=" * 70)
    print("Phase 2: AgentService 层验证")
    print("=" * 70)
    
    # 2.1 AgentService 基础架构
    try:
        from services.agent_service import get_agent_service, AgentTaskStatus, ContentSource
        service = get_agent_service()
        v.log("2.1", "AgentService", "pass", "加载成功")
        
        methods = ["create_task", "get_task", "update_task", "execute_task", "list_tasks"]
        for m in methods:
            if hasattr(service, m):
                v.log("2.1", f"AgentService.{m}", "pass", "方法存在")
            else:
                v.log("2.1", f"AgentService.{m}", "fail", "方法不存在")
        
        # 检查状态枚举
        expected_statuses = ["PENDING", "WORKING", "REVIEWING", "COMPLETED", "FAILED"]
        for s in expected_statuses:
            if hasattr(AgentTaskStatus, s):
                v.log("2.1", f"AgentTaskStatus.{s}", "pass", "已定义")
            else:
                v.log("2.1", f"AgentTaskStatus.{s}", "fail", "未定义")
        
        # 检查内容来源枚举
        expected_sources = ["USER", "SCRIPT_AGENT", "ART_AGENT", "DIRECTOR_AGENT"]
        for s in expected_sources:
            if hasattr(ContentSource, s):
                v.log("2.1", f"ContentSource.{s}", "pass", "已定义")
            else:
                v.log("2.1", f"ContentSource.{s}", "fail", "未定义")
    except Exception as e:
        v.log("2.1", "AgentService", "fail", str(e))
    
    # 2.2-2.8 各 Agent 服务
    agents = [
        ("2.2", "Script_Agent", "services.agents.script_agent", "get_script_agent_service"),
        ("2.3", "Art_Agent", "services.agents.art_agent", "get_art_agent_service"),
        ("2.4", "Director_Agent", "services.agents.director_agent", "get_director_agent_service"),
        ("2.5", "PM_Agent", "services.agents.pm_agent", "get_pm_agent_service"),
        ("2.6", "Storyboard_Agent", "services.agents.storyboard_agent", "get_storyboard_agent_service"),
        ("2.7", "Market_Agent", "services.agents.market_agent", "get_market_agent_service"),
        ("2.8", "System_Agent", "services.agents.system_agent", "get_system_agent_service"),
    ]
    
    for task_id, name, module, func in agents:
        try:
            mod = __import__(module, fromlist=[func])
            getter = getattr(mod, func)
            agent = getter()
            v.log(task_id, name, "pass", "服务加载成功")
        except Exception as e:
            v.log(task_id, name, "fail", str(e))


async def validate_phase_4(v: FlowValidator):
    """验证 Phase 4: API 端点"""
    print("\n" + "=" * 70)
    print("Phase 4: API 端点验证")
    print("=" * 70)
    
    try:
        from routers.wizard import router
        
        # 获取所有路由
        routes = {}
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    routes[f"{method} {route.path}"] = True
        
        # 期望的端点
        expected_endpoints = [
            ("4.1", "POST /parse-script", "剧本解析"),
            ("4.1", "POST /generate-content", "内容生成"),
            ("4.2", "POST /process-assets", "素材处理"),
            ("4.3", "POST /create-project", "项目创建"),
            ("4.3", "GET /projects", "项目列表"),
            ("4.4", "GET /task-status/{task_id}", "任务状态"),
            ("4.5", "POST /record-version", "记录版本"),
            ("4.5", "GET /version-history/{project_id}", "版本历史"),
            ("4.6", "POST /recall-assets", "素材召回"),
            ("4.6", "POST /switch-candidate", "候选切换"),
            ("4.7", "POST /market-analysis", "市场分析"),
            ("4.8", "POST /validate-export", "导出校验"),
            ("4.8", "POST /check-tag-consistency", "标签一致性"),
            ("4.9", "POST /validate-project", "项目验证"),
            ("4.10", "POST /review-content", "内容审核"),
            ("4.11", "GET /health", "健康检查"),
        ]
        
        for task_id, endpoint, desc in expected_endpoints:
            if endpoint in routes:
                v.log(task_id, endpoint, "pass", desc)
            else:
                v.log(task_id, endpoint, "warn", f"{desc} - 未找到")
        
    except Exception as e:
        v.log("4.x", "API端点", "fail", str(e))


async def validate_workflow(v: FlowValidator):
    """验证完整工作流程"""
    print("\n" + "=" * 70)
    print("完整工作流程验证")
    print("=" * 70)
    
    # 模拟完整流程
    try:
        from services.agents.script_agent import get_script_agent_service
        from services.agents.director_agent import get_director_agent_service
        from services.agents.pm_agent import get_pm_agent_service
        
        script_agent = get_script_agent_service()
        director_agent = get_director_agent_service()
        pm_agent = get_pm_agent_service()
        
        # 1. 剧本解析
        test_script = """
INT. 咖啡厅 - 日

张三坐在窗边。

张三
今天天气真好。

EXT. 街道 - 夜

李四走在街上。
"""
        parse_result = script_agent.parse_script(test_script)
        v.log("流程", "1.剧本解析", "pass", 
              f"{parse_result.total_scenes}场次, {parse_result.total_characters}角色")
        
        # 2. Director_Agent 审核
        review_result = await director_agent.review(
            result=parse_result.to_dict(),
            task_type="parse_script",
            project_id="test_flow"
        )
        v.log("流程", "2.导演审核", "pass", f"状态: {review_result.status}")
        
        # 3. PM_Agent 记录版本
        version = pm_agent.record_version(
            project_id="test_flow",
            content_type="剧本解析",
            content=parse_result.to_dict(),
            source="script_agent"
        )
        v.log("流程", "3.版本记录", "pass", f"版本: {version.version_name}")
        
        # 4. 用户决策记录
        decision = pm_agent.record_decision(
            project_id="test_flow",
            decision_type="approve",
            target_type="version",
            target_id=version.version_id
        )
        v.log("流程", "4.决策记录", "pass", f"决策ID: {decision.decision_id}")
        
    except Exception as e:
        v.log("流程", "工作流程", "fail", str(e))


async def main():
    """主函数"""
    print("=" * 70)
    print("Pervis PRO Project Wizard - Phase 0-4 完整验证")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    v = FlowValidator()
    
    await validate_phase_0_fix(v)
    await validate_phase_0(v)
    await validate_phase_1(v)
    await validate_phase_2(v)
    await validate_phase_4(v)
    await validate_workflow(v)
    
    success = v.summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
