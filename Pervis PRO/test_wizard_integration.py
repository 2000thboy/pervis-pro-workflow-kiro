# -*- coding: utf-8 -*-
"""
Wizard API 集成测试

验证 Agent 服务是否正确集成到 API 端点
"""

import asyncio
import sys
sys.path.insert(0, 'backend')


async def test_script_agent():
    """测试 Script_Agent 服务"""
    print("\n=== 测试 Script_Agent ===")
    try:
        from services.agents.script_agent import get_script_agent_service
        
        agent = get_script_agent_service()
        print(f"✓ Script_Agent 服务加载成功")
        
        # 测试剧本解析
        test_script = """
INT. 咖啡厅 - 日

张三坐在窗边，看着窗外的雨。

张三
（自言自语）
今天的雨下得真大。

李四走进咖啡厅，看到张三。

李四
张三！好久不见！

EXT. 街道 - 夜

张三和李四走在街上。
"""
        result = agent.parse_script(test_script)
        print(f"✓ 剧本解析成功: {result.total_scenes} 个场次, {result.total_characters} 个角色")
        
        for scene in result.scenes:
            print(f"  - 场次 {scene.scene_number}: {scene.heading}")
        
        for char in result.characters:
            print(f"  - 角色: {char.name} (对话 {char.dialogue_count} 次)")
        
        return True
    except Exception as e:
        print(f"✗ Script_Agent 测试失败: {e}")
        return False


async def test_art_agent():
    """测试 Art_Agent 服务"""
    print("\n=== 测试 Art_Agent ===")
    try:
        from services.agents.art_agent import get_art_agent_service
        
        agent = get_art_agent_service()
        print(f"✓ Art_Agent 服务加载成功")
        
        # 测试文件分类（基于文件名）
        test_files = [
            "角色_张三.jpg",
            "场景_咖啡厅.png",
            "参考资料.pdf"
        ]
        
        for filename in test_files:
            classification = agent._classify_by_filename(filename)
            print(f"  - {filename} -> {classification.category} (置信度: {classification.confidence})")
        
        return True
    except Exception as e:
        print(f"✗ Art_Agent 测试失败: {e}")
        return False


async def test_director_agent():
    """测试 Director_Agent 服务"""
    print("\n=== 测试 Director_Agent ===")
    try:
        from services.agents.director_agent import get_director_agent_service
        
        agent = get_director_agent_service()
        print(f"✓ Director_Agent 服务加载成功")
        
        # 测试规则校验
        test_content = {"logline": "一个关于友情的故事"}
        result = await agent.review(test_content, "logline", "test_project")
        print(f"✓ 审核结果: {result.status}")
        print(f"  - 通过检查: {result.passed_checks}")
        print(f"  - 建议: {result.suggestions}")
        
        return True
    except Exception as e:
        print(f"✗ Director_Agent 测试失败: {e}")
        return False


async def test_storyboard_agent():
    """测试 Storyboard_Agent 服务"""
    print("\n=== 测试 Storyboard_Agent ===")
    try:
        from services.agents.storyboard_agent import get_storyboard_agent_service
        
        agent = get_storyboard_agent_service()
        print(f"✓ Storyboard_Agent 服务加载成功")
        
        # 测试素材召回（使用内存存储，应返回空结果）
        result = await agent.recall_assets(
            scene_id="test_scene_1",
            query="咖啡厅 白天 对话",
            strategy="hybrid"
        )
        print(f"✓ 素材召回完成: {len(result.candidates)} 个候选")
        print(f"  - 是否有匹配: {result.has_match}")
        print(f"  - 占位符消息: {result.placeholder_message}")
        
        return True
    except Exception as e:
        print(f"✗ Storyboard_Agent 测试失败: {e}")
        return False


async def test_agent_service():
    """测试 AgentService"""
    print("\n=== 测试 AgentService ===")
    try:
        from services.agent_service import get_agent_service
        
        service = get_agent_service()
        print(f"✓ AgentService 加载成功")
        
        # 测试任务创建
        task = service.create_task("test_task", "script_agent", {"test": True})
        print(f"✓ 任务创建成功: {task.task_id}")
        
        # 测试任务列表
        tasks = service.list_tasks()
        print(f"✓ 任务列表: {len(tasks)} 个任务")
        
        return True
    except Exception as e:
        print(f"✗ AgentService 测试失败: {e}")
        return False


async def test_pm_agent():
    """测试 PM_Agent 服务"""
    print("\n=== 测试 PM_Agent ===")
    try:
        from services.agents.pm_agent import get_pm_agent_service
        
        agent = get_pm_agent_service()
        print(f"✓ PM_Agent 服务加载成功")
        
        # 测试版本记录
        version = agent.record_version(
            project_id="test_project",
            content_type="logline",
            content="一个关于友情的故事",
            source="script_agent"
        )
        print(f"✓ 版本记录成功: {version.version_name}")
        
        # 测试版本显示信息
        info = agent.get_version_display_info("test_project", "logline")
        print(f"✓ 版本显示: {info.current_version} (共 {info.version_count} 个版本)")
        
        # 测试决策记录
        decision = agent.record_decision(
            project_id="test_project",
            decision_type="approve",
            target_type="version",
            target_id=version.version_id
        )
        print(f"✓ 决策记录成功: {decision.decision_id}")
        
        return True
    except Exception as e:
        print(f"✗ PM_Agent 测试失败: {e}")
        return False


async def test_market_agent():
    """测试 Market_Agent 服务"""
    print("\n=== 测试 Market_Agent ===")
    try:
        from services.agents.market_agent import get_market_agent_service
        
        agent = get_market_agent_service()
        print(f"✓ Market_Agent 服务加载成功")
        
        # 测试基于规则的市场分析
        result = agent._rule_based_analysis(
            project_id="test_project",
            project_data={
                "project_type": "short_film",
                "title": "测试短片",
                "duration_minutes": 15
            }
        )
        print(f"✓ 市场分析成功:")
        print(f"  - 市场定位: {result.market_position[:40]}...")
        print(f"  - 目标受众: {result.audience.primary_age_range}")
        print(f"  - 发行渠道: {result.distribution_channels[:2]}")
        
        return True
    except Exception as e:
        print(f"✗ Market_Agent 测试失败: {e}")
        return False


async def test_system_agent():
    """测试 System_Agent 服务"""
    print("\n=== 测试 System_Agent ===")
    try:
        from services.agents.system_agent import get_system_agent_service
        
        agent = get_system_agent_service()
        print(f"✓ System_Agent 服务加载成功")
        
        # 测试标签一致性检查
        result = agent.check_tag_consistency(["室内", "室外", "白天", "现代"])
        print(f"✓ 标签一致性检查:")
        print(f"  - 一致: {result.is_consistent}")
        print(f"  - 冲突数: {len(result.conflicts)}")
        for conflict in result.conflicts:
            print(f"    - {conflict['tag1']} vs {conflict['tag2']}")
        
        return True
    except Exception as e:
        print(f"✗ System_Agent 测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Wizard API 集成测试")
    print("=" * 60)
    
    results = []
    
    results.append(await test_script_agent())
    results.append(await test_art_agent())
    results.append(await test_director_agent())
    results.append(await test_storyboard_agent())
    results.append(await test_agent_service())
    results.append(await test_pm_agent())
    results.append(await test_market_agent())
    results.append(await test_system_agent())
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！Agent 服务已正确集成。")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
