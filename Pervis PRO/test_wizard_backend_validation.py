# -*- coding: utf-8 -*-
"""
Pervis PRO 项目立项向导后端验证脚本

Task 5: Checkpoint - 后端功能验证
验证所有后端 API 和 Agent 服务是否正常工作
"""

import asyncio
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_agent_services():
    """测试 Agent 服务加载"""
    print("\n" + "="*60)
    print("1. 测试 Agent 服务加载")
    print("="*60)
    
    results = {}
    
    # Script_Agent
    try:
        from services.agents.script_agent import get_script_agent_service
        agent = get_script_agent_service()
        results['Script_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['Script_Agent'] = f'❌ 加载失败: {e}'
    
    # Art_Agent
    try:
        from services.agents.art_agent import get_art_agent_service
        agent = get_art_agent_service()
        results['Art_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['Art_Agent'] = f'❌ 加载失败: {e}'
    
    # Director_Agent
    try:
        from services.agents.director_agent import get_director_agent_service
        agent = get_director_agent_service()
        results['Director_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['Director_Agent'] = f'❌ 加载失败: {e}'
    
    # PM_Agent
    try:
        from services.agents.pm_agent import get_pm_agent_service
        agent = get_pm_agent_service()
        results['PM_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['PM_Agent'] = f'❌ 加载失败: {e}'
    
    # Market_Agent
    try:
        from services.agents.market_agent import get_market_agent_service
        agent = get_market_agent_service()
        results['Market_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['Market_Agent'] = f'❌ 加载失败: {e}'
    
    # System_Agent
    try:
        from services.agents.system_agent import get_system_agent_service
        agent = get_system_agent_service()
        results['System_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['System_Agent'] = f'❌ 加载失败: {e}'
    
    # Storyboard_Agent
    try:
        from services.agents.storyboard_agent import get_storyboard_agent_service
        agent = get_storyboard_agent_service()
        results['Storyboard_Agent'] = '✅ 加载成功'
    except Exception as e:
        results['Storyboard_Agent'] = f'❌ 加载失败: {e}'
    
    # AgentService
    try:
        from services.agent_service import get_agent_service
        service = get_agent_service()
        results['AgentService'] = '✅ 加载成功'
    except Exception as e:
        results['AgentService'] = f'❌ 加载失败: {e}'
    
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    return all('✅' in s for s in results.values())


def test_llm_adapter():
    """测试 LLM 适配器"""
    print("\n" + "="*60)
    print("2. 测试 LLM 适配器")
    print("="*60)
    
    try:
        from services.agent_llm_adapter import get_agent_llm_adapter, AgentType
        adapter = get_agent_llm_adapter()
        print(f"  LLM 适配器: ✅ 加载成功")
        print(f"  支持的 Agent 类型: {[t.value for t in AgentType]}")
        return True
    except Exception as e:
        print(f"  LLM 适配器: ❌ 加载失败: {e}")
        return False


def test_video_store():
    """测试视频存储"""
    print("\n" + "="*60)
    print("3. 测试视频存储")
    print("="*60)
    
    try:
        from services.milvus_store import get_video_store, VectorStoreType
        store = get_video_store(VectorStoreType.MEMORY)
        print(f"  MemoryVideoStore: ✅ 加载成功")
        return True
    except Exception as e:
        print(f"  视频存储: ❌ 加载失败: {e}")
        return False


def test_script_parsing():
    """测试剧本解析"""
    print("\n" + "="*60)
    print("4. 测试剧本解析功能")
    print("="*60)
    
    try:
        from services.agents.script_agent import get_script_agent_service
        agent = get_script_agent_service()
        
        # 测试剧本
        test_script = """
INT. 咖啡馆 - 日

张三坐在窗边，看着窗外的雨。

张三
（叹气）
又是一个人的下午。

李四走进咖啡馆，看到张三。

李四
张三！好久不见！

张三
（惊喜）
李四？你怎么在这？

EXT. 街道 - 夜

张三和李四走在雨中。

张三
谢谢你今天陪我。

李四
朋友嘛，应该的。
"""
        
        result = agent.parse_script(test_script)
        
        print(f"  解析场次数: {result.total_scenes}")
        print(f"  解析角色数: {result.total_characters}")
        print(f"  估算总时长: {result.estimated_duration:.1f} 秒")
        
        if result.scenes:
            print(f"  场次列表:")
            for scene in result.scenes:
                print(f"    - {scene.heading} ({scene.estimated_duration:.1f}秒)")
        
        if result.characters:
            print(f"  角色列表:")
            for char in result.characters:
                print(f"    - {char.name} (对话 {char.dialogue_count} 次)")
        
        return result.total_scenes > 0 and result.total_characters > 0
        
    except Exception as e:
        print(f"  剧本解析: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_director_review():
    """测试导演审核"""
    print("\n" + "="*60)
    print("5. 测试导演审核功能")
    print("="*60)
    
    try:
        from services.agents.director_agent import get_director_agent_service
        agent = get_director_agent_service()
        
        # 测试审核
        test_content = {
            "logline": "一个孤独的程序员在咖啡馆遇到了老朋友，重新找回了生活的意义。"
        }
        
        async def run_review():
            return await agent.review(
                result=test_content,
                task_type="logline",
                project_id="test_project"
            )
        
        result = asyncio.run(run_review())
        
        print(f"  审核状态: {result.status}")
        print(f"  通过检查: {result.passed_checks}")
        print(f"  失败检查: {result.failed_checks}")
        print(f"  建议: {result.suggestions}")
        
        return result.status in ['approved', 'suggestions']
        
    except Exception as e:
        print(f"  导演审核: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pm_version():
    """测试版本管理"""
    print("\n" + "="*60)
    print("6. 测试版本管理功能")
    print("="*60)
    
    try:
        from services.agents.pm_agent import get_pm_agent_service
        agent = get_pm_agent_service()
        
        # 记录版本
        version = agent.record_version(
            project_id="test_project",
            content_type="logline",
            content="测试 Logline 内容",
            source="script_agent"
        )
        
        print(f"  版本ID: {version.version_id}")
        print(f"  版本名称: {version.version_name}")
        print(f"  版本号: {version.version_number}")
        
        # 获取显示信息
        info = agent.get_version_display_info(
            project_id="test_project",
            content_type="logline"
        )
        
        print(f"  当前版本: {info.current_version}")
        print(f"  版本总数: {info.version_count}")
        
        return version.version_number == 1
        
    except Exception as e:
        print(f"  版本管理: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_validation():
    """测试系统校验"""
    print("\n" + "="*60)
    print("7. 测试系统校验功能")
    print("="*60)
    
    try:
        from services.agents.system_agent import get_system_agent_service
        agent = get_system_agent_service()
        
        # 测试标签一致性
        test_tags = ["室内", "白天", "现代", "喜剧"]
        result = agent.check_tag_consistency(test_tags)
        
        print(f"  标签一致性: {'✅ 通过' if result.is_consistent else '⚠️ 有冲突'}")
        if result.conflicts:
            print(f"  冲突: {result.conflicts}")
        
        # 测试矛盾标签
        conflict_tags = ["室内", "室外", "白天"]
        result2 = agent.check_tag_consistency(conflict_tags)
        
        print(f"  矛盾标签检测: {'✅ 检测到冲突' if not result2.is_consistent else '❌ 未检测到冲突'}")
        
        return result.is_consistent and not result2.is_consistent
        
    except Exception as e:
        print(f"  系统校验: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_analysis():
    """测试市场分析"""
    print("\n" + "="*60)
    print("8. 测试市场分析功能")
    print("="*60)
    
    try:
        from services.agents.market_agent import get_market_agent_service
        agent = get_market_agent_service()
        
        # 测试基于规则的分析
        result = agent._rule_based_analysis(
            project_id="test_project",
            project_data={
                "project_type": "short_film",
                "genre": "drama",
                "duration_minutes": 15
            }
        )
        
        print(f"  目标受众: {result.audience.primary_age_range}")
        print(f"  市场定位: {result.market_position[:50]}...")
        print(f"  发行渠道: {result.distribution_channels[:3]}")
        print(f"  是否动态分析: {result.is_dynamic}")
        
        return result.market_position != ""
        
    except Exception as e:
        print(f"  市场分析: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_art_classification():
    """测试美术分类"""
    print("\n" + "="*60)
    print("9. 测试美术分类功能")
    print("="*60)
    
    try:
        from services.agents.art_agent import get_art_agent_service
        agent = get_art_agent_service()
        
        # 测试文件名分类
        test_files = [
            "角色_张三_设计图.png",
            "场景_咖啡馆_参考.jpg",
            "random_image.png"
        ]
        
        for filename in test_files:
            result = agent._classify_by_filename(filename)
            print(f"  {filename}: {result.category} (置信度: {result.confidence})")
        
        return True
        
    except Exception as e:
        print(f"  美术分类: ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Pervis PRO 项目立项向导后端验证")
    print("Task 5: Checkpoint - 后端功能验证")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("Agent 服务加载", test_agent_services()))
    results.append(("LLM 适配器", test_llm_adapter()))
    results.append(("视频存储", test_video_store()))
    results.append(("剧本解析", test_script_parsing()))
    results.append(("导演审核", test_director_review()))
    results.append(("版本管理", test_pm_version()))
    results.append(("系统校验", test_system_validation()))
    results.append(("市场分析", test_market_analysis()))
    results.append(("美术分类", test_art_classification()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("-"*60)
    
    if failed == 0:
        print("\n🎉 所有后端功能验证通过！")
        print("可以继续进行前端开发 (Phase 5-8)")
    else:
        print(f"\n⚠️ 有 {failed} 项验证失败，请检查相关功能")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
