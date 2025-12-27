# -*- coding: utf-8 -*-
"""
框架修复验证测试 (0-Fix.Checkpoint)

验证内容：
1. Script_Agent 可以调用 LLM 生成 Logline
2. Director_Agent 可以带上下文审核
3. REST API 可以正常调用

Feature: pervis-project-wizard
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

pervis_backend = backend_path.parent.parent / "Pervis PRO" / "backend"
sys.path.insert(0, str(pervis_backend))


async def test_script_agent_llm():
    """测试 Script_Agent LLM 集成"""
    print("\n" + "=" * 60)
    print("测试 1: Script_Agent LLM 集成")
    print("=" * 60)
    
    from app.core.message_bus import MessageBus
    from app.agents.script_agent import ScriptAgent
    
    # 创建消息总线和 Agent
    message_bus = MessageBus()
    await message_bus.start()
    
    agent = ScriptAgent(message_bus=message_bus)
    await agent.initialize()
    await agent.start()
    
    # 测试剧本内容
    test_script = """
    INT. 咖啡馆 - 日
    
    张三坐在窗边，看着窗外的雨。
    
    张三
    （叹气）
    又是一个人的下午。
    
    李四走进咖啡馆，看到张三。
    
    李四
    好久不见！
    
    EXT. 街道 - 夜
    
    张三和李四并肩走在雨中。
    """
    
    # 测试 Logline 生成
    print("\n[测试] generate_logline()...")
    try:
        result = await agent.generate_logline(test_script)
        print(f"  ✓ Logline: {result.logline[:50]}..." if len(result.logline) > 50 else f"  ✓ Logline: {result.logline}")
        print(f"  ✓ Confidence: {result.confidence}")
        logline_ok = bool(result.logline)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        logline_ok = False
    
    # 测试 Synopsis 生成
    print("\n[测试] generate_synopsis()...")
    try:
        result = await agent.generate_synopsis(test_script)
        print(f"  ✓ Synopsis: {result.synopsis[:80]}..." if len(result.synopsis) > 80 else f"  ✓ Synopsis: {result.synopsis}")
        print(f"  ✓ Word count: {result.word_count}")
        synopsis_ok = bool(result.synopsis)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        synopsis_ok = False
    
    # 测试人物小传生成
    print("\n[测试] generate_character_bio()...")
    try:
        result = await agent.generate_character_bio("张三", test_script)
        print(f"  ✓ Name: {result.name}")
        print(f"  ✓ Bio: {result.bio[:80]}..." if len(result.bio) > 80 else f"  ✓ Bio: {result.bio}")
        bio_ok = bool(result.bio)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        bio_ok = False
    
    await agent.stop()
    await message_bus.stop()
    
    return logline_ok and synopsis_ok and bio_ok


async def test_director_agent_context():
    """测试 Director_Agent 带上下文审核"""
    print("\n" + "=" * 60)
    print("测试 2: Director_Agent 带上下文审核")
    print("=" * 60)
    
    from app.core.message_bus import MessageBus
    from app.agents.director_agent import DirectorAgent
    
    # 创建消息总线和 Agent
    message_bus = MessageBus()
    await message_bus.start()
    
    agent = DirectorAgent(message_bus=message_bus)
    await agent.initialize()
    await agent.start()
    
    project_id = "test_project_001"
    
    # 测试设置项目规格
    print("\n[测试] set_project_specs()...")
    try:
        context = agent.set_project_specs(project_id, {
            "duration": 90,
            "aspect_ratio": "16:9",
            "frame_rate": 24,
            "resolution": "4K"
        })
        print(f"  ✓ 项目规格已设置: {context.specs}")
        specs_ok = bool(context.specs)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        specs_ok = False
    
    # 测试设置艺术风格
    print("\n[测试] set_style_context()...")
    try:
        context = agent.set_style_context(project_id, {
            "style_type": "realistic",
            "reference_projects": ["肖申克的救赎", "阿甘正传"],
            "color_palette": "warm"
        })
        print(f"  ✓ 艺术风格已设置: {context.style_context}")
        style_ok = bool(context.style_context)
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        style_ok = False
    
    # 测试带上下文审核
    print("\n[测试] review_with_context()...")
    try:
        test_content = "一个关于友情和救赎的故事，两个老朋友在咖啡馆重逢，回忆往事。"
        result = await agent.review_with_context(project_id, test_content, "logline")
        print(f"  ✓ 审核状态: {result.get('status')}")
        print(f"  ✓ 通过检查: {result.get('passed_checks')}")
        print(f"  ✓ 来源: {result.get('source')}")
        review_ok = result.get("status") in ["approved", "suggestions"]
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        review_ok = False
    
    # 测试风格一致性检查
    print("\n[测试] check_style_consistency()...")
    try:
        test_content = "真实写实的画面风格，参考肖申克的救赎的叙事方式。"
        result = await agent.check_style_consistency(project_id, test_content)
        print(f"  ✓ 一致性: {result.get('is_consistent')}")
        print(f"  ✓ 分数: {result.get('consistency_score')}")
        print(f"  ✓ 匹配元素: {result.get('matching_elements')}")
        consistency_ok = True
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        consistency_ok = False
    
    # 测试历史版本对比
    print("\n[测试] compare_with_history()...")
    try:
        # 先记录一个被拒绝的版本
        agent.record_user_decision(
            project_id, "logline", False, 
            "一个无聊的故事", "内容太简单"
        )
        
        # 测试对比
        result = await agent.compare_with_history(project_id, "一个无聊的故事", "logline")
        print(f"  ✓ 与被拒版本相似: {result.get('is_similar_to_rejected')}")
        print(f"  ✓ 相似度: {result.get('similarity_score'):.2%}")
        print(f"  ✓ 版本数: {result.get('version_count')}")
        history_ok = True
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        history_ok = False
    
    await agent.stop()
    await message_bus.stop()
    
    return specs_ok and style_ok and review_ok and consistency_ok and history_ok


def test_rest_api_routes():
    """测试 REST API 路由定义"""
    print("\n" + "=" * 60)
    print("测试 3: REST API 路由定义")
    print("=" * 60)
    
    try:
        from routers.wizard import router
        
        # 获取所有路由
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else []
                })
        
        print(f"\n[测试] 已定义的路由:")
        expected_routes = [
            "/parse-script",
            "/generate-content",
            "/process-assets",
            "/task-status/{task_id}",
            "/recall-assets",
            "/health"
        ]
        
        found_routes = [r["path"] for r in routes]
        
        all_found = True
        for expected in expected_routes:
            if expected in found_routes:
                print(f"  ✓ {expected}")
            else:
                print(f"  ✗ {expected} (未找到)")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ✗ 导入错误: {e}")
        return False


def test_llm_adapter():
    """测试 LLM 适配器"""
    print("\n" + "=" * 60)
    print("测试 4: LLM 适配器")
    print("=" * 60)
    
    try:
        from services.agent_llm_adapter import get_agent_llm_adapter, AgentType
        
        adapter = get_agent_llm_adapter()
        print(f"  ✓ 适配器创建成功")
        
        # 检查 Agent 类型
        print(f"\n[测试] Agent 类型定义:")
        for agent_type in AgentType:
            print(f"  ✓ {agent_type.name}: {agent_type.value}")
        
        # 检查方法
        print(f"\n[测试] 适配器方法:")
        methods = [
            "generate_logline",
            "generate_synopsis",
            "generate_character_bio",
            "classify_file",
            "generate_visual_tags",
            "review_content",
            "check_style_consistency",
            "analyze_market",
            "check_tag_consistency"
        ]
        
        all_methods_ok = True
        for method in methods:
            if hasattr(adapter, method):
                print(f"  ✓ {method}()")
            else:
                print(f"  ✗ {method}() (未找到)")
                all_methods_ok = False
        
        return all_methods_ok
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


async def main():
    """运行所有验证测试"""
    print("\n" + "=" * 60)
    print("框架修复验证 (0-Fix.Checkpoint)")
    print("=" * 60)
    
    results = {}
    
    # 测试 1: Script_Agent LLM 集成
    results["script_agent_llm"] = await test_script_agent_llm()
    
    # 测试 2: Director_Agent 带上下文审核
    results["director_agent_context"] = await test_director_agent_context()
    
    # 测试 3: REST API 路由
    results["rest_api_routes"] = test_rest_api_routes()
    
    # 测试 4: LLM 适配器
    results["llm_adapter"] = test_llm_adapter()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "-" * 60)
    if all_passed:
        print("✓ 所有验证通过！框架修复完成。")
        print("  可以继续执行 Phase 0: 基础设施安装配置")
    else:
        print("✗ 部分验证失败，请检查上述错误。")
    print("-" * 60)
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
