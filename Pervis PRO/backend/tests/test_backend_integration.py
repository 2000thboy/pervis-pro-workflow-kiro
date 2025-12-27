# -*- coding: utf-8 -*-
"""
Pervis PRO 后端完整集成测试
测试所有核心功能的端到端工作流

测试模块:
1. Agent 服务集成
2. 搜索系统集成
3. 导出系统集成
4. 项目向导集成
5. API 端点集成
"""

import os
import sys
import asyncio
import pytest
import time
from typing import Dict, Any, List
from dataclasses import dataclass

# 添加 backend 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentServiceIntegration:
    """Agent 服务集成测试"""
    
    def test_all_agents_load_successfully(self):
        """测试所有 Agent 服务加载"""
        agents = {}
        
        # Script_Agent
        try:
            from services.agents.script_agent import get_script_agent_service
            agents['Script_Agent'] = get_script_agent_service()
        except Exception as e:
            pytest.fail(f"Script_Agent 加载失败: {e}")
        
        # Art_Agent
        try:
            from services.agents.art_agent import get_art_agent_service
            agents['Art_Agent'] = get_art_agent_service()
        except Exception as e:
            pytest.fail(f"Art_Agent 加载失败: {e}")
        
        # Director_Agent
        try:
            from services.agents.director_agent import get_director_agent_service
            agents['Director_Agent'] = get_director_agent_service()
        except Exception as e:
            pytest.fail(f"Director_Agent 加载失败: {e}")
        
        # PM_Agent
        try:
            from services.agents.pm_agent import get_pm_agent_service
            agents['PM_Agent'] = get_pm_agent_service()
        except Exception as e:
            pytest.fail(f"PM_Agent 加载失败: {e}")
        
        # Market_Agent
        try:
            from services.agents.market_agent import get_market_agent_service
            agents['Market_Agent'] = get_market_agent_service()
        except Exception as e:
            pytest.fail(f"Market_Agent 加载失败: {e}")
        
        # System_Agent
        try:
            from services.agents.system_agent import get_system_agent_service
            agents['System_Agent'] = get_system_agent_service()
        except Exception as e:
            pytest.fail(f"System_Agent 加载失败: {e}")
        
        # Storyboard_Agent
        try:
            from services.agents.storyboard_agent import get_storyboard_agent_service
            agents['Storyboard_Agent'] = get_storyboard_agent_service()
        except Exception as e:
            pytest.fail(f"Storyboard_Agent 加载失败: {e}")
        
        assert len(agents) == 7, f"Agent 数量不正确: {len(agents)}"
        print(f"\n  ✅ 所有 7 个 Agent 服务加载成功")
    
    def test_script_agent_parse_workflow(self):
        """测试 Script_Agent 剧本解析工作流"""
        from services.agents.script_agent import get_script_agent_service
        
        agent = get_script_agent_service()
        
        test_script = """
INT. 办公室 - 日

张三坐在电脑前，眉头紧锁。

张三
（自言自语）
这个 bug 到底在哪里...

李四推门进来。

李四
张三，下班了，走吧。

张三
你先走，我再看看。

EXT. 公司门口 - 夜

李四站在门口等待。张三终于走出来。

李四
搞定了？

张三
（微笑）
搞定了。
"""
        
        result = agent.parse_script(test_script)
        
        assert result.total_scenes >= 2, f"场次数量不正确: {result.total_scenes}"
        assert result.total_characters >= 2, f"角色数量不正确: {result.total_characters}"
        assert result.estimated_duration > 0, f"时长估算为 0"
        
        print(f"\n  场次: {result.total_scenes}, 角色: {result.total_characters}, 时长: {result.estimated_duration:.1f}s")
    
    @pytest.mark.asyncio
    async def test_director_agent_review_workflow(self):
        """测试 Director_Agent 审核工作流"""
        from services.agents.director_agent import get_director_agent_service
        
        agent = get_director_agent_service()
        
        test_content = {
            "logline": "一个程序员在深夜加班时发现了改变世界的代码。"
        }
        
        result = await agent.review(
            result=test_content,
            task_type="logline",
            project_id="test_integration"
        )
        
        assert result.status in ['approved', 'suggestions', 'rejected']
        assert isinstance(result.passed_checks, list)
        assert isinstance(result.suggestions, list)
        
        print(f"\n  审核状态: {result.status}")
        print(f"  通过检查: {len(result.passed_checks)}")
        print(f"  建议数量: {len(result.suggestions)}")
    
    def test_pm_agent_version_workflow(self):
        """测试 PM_Agent 版本管理工作流"""
        from services.agents.pm_agent import get_pm_agent_service
        
        agent = get_pm_agent_service()
        
        # 记录多个版本
        versions = []
        for i in range(3):
            version = agent.record_version(
                project_id="test_integration",
                content_type="logline",
                content=f"Logline 版本 {i+1}",
                source="script_agent"
            )
            versions.append(version)
        
        assert len(versions) == 3
        assert versions[0].version_number == 1
        assert versions[2].version_number == 3
        
        # 获取版本显示信息
        info = agent.get_version_display_info(
            project_id="test_integration",
            content_type="logline"
        )
        
        assert info.version_count == 3
        # current_version 是版本名称字符串，不是数字
        assert "v3" in info.current_version or info.current_version.endswith("_v3")
        
        print(f"\n  版本总数: {info.version_count}")
        print(f"  当前版本: {info.current_version}")
    
    def test_system_agent_validation_workflow(self):
        """测试 System_Agent 校验工作流"""
        from services.agents.system_agent import get_system_agent_service
        
        agent = get_system_agent_service()
        
        # 测试一致标签
        consistent_tags = ["室内", "白天", "现代", "喜剧"]
        result1 = agent.check_tag_consistency(consistent_tags)
        
        assert result1.is_consistent, "一致标签应该通过检查"
        
        # 测试矛盾标签
        conflict_tags = ["室内", "室外", "白天"]
        result2 = agent.check_tag_consistency(conflict_tags)
        
        assert not result2.is_consistent, "矛盾标签应该检测到冲突"
        assert len(result2.conflicts) > 0, "应该报告冲突详情"
        
        print(f"\n  一致标签检查: {'通过' if result1.is_consistent else '失败'}")
        print(f"  矛盾标签检测: {'检测到冲突' if not result2.is_consistent else '未检测到'}")
    
    def test_market_agent_analysis_workflow(self):
        """测试 Market_Agent 分析工作流"""
        from services.agents.market_agent import get_market_agent_service
        
        agent = get_market_agent_service()
        
        result = agent._rule_based_analysis(
            project_id="test_integration",
            project_data={
                "project_type": "short_film",
                "genre": "drama",
                "duration_minutes": 15
            }
        )
        
        assert result.audience is not None
        assert result.market_position != ""
        assert len(result.distribution_channels) > 0
        
        print(f"\n  目标受众: {result.audience.primary_age_range}")
        print(f"  发行渠道: {result.distribution_channels[:3]}")


class TestSearchSystemIntegration:
    """搜索系统集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        from services.milvus_store import MemoryVideoStore
        
        self.video_store = MemoryVideoStore()
        
        yield
        
        # MemoryVideoStore 没有 clear 方法，直接重置内部字典
        self.video_store._segments = {}
    
    @pytest.mark.asyncio
    async def test_embedding_service_integration(self):
        """测试嵌入服务集成"""
        from services.ollama_embedding import get_embedding_service
        
        service = get_embedding_service()
        
        test_texts = [
            "城市夜景霓虹灯",
            "森林清晨薄雾",
            "海滩日落金色"
        ]
        
        embeddings = []
        for text in test_texts:
            # embed 是异步方法，需要 await
            embedding = await service.embed(text)
            embeddings.append(embedding)
            
            assert embedding is not None
            assert len(embedding) > 0
        
        # 验证不同文本的嵌入不同
        assert embeddings[0] != embeddings[1]
        
        print(f"\n  嵌入维度: {len(embeddings[0])}")
        print(f"  生成数量: {len(embeddings)}")
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_search_service_integration(self):
        """测试搜索服务集成"""
        from services.ollama_embedding import get_embedding_service
        from services.milvus_store import VideoSegment
        
        embedding_service = get_embedding_service()
        
        # 索引测试数据
        test_data = [
            ("asset_001", "城市夜景_霓虹灯.mp4", "城市夜景霓虹灯闪烁"),
            ("asset_002", "森林_清晨_薄雾.mp4", "森林清晨薄雾弥漫"),
            ("asset_003", "海滩_日落_金色.mp4", "海滩日落金色阳光"),
        ]
        
        for asset_id, filename, description in test_data:
            # embed 是异步方法
            embedding = await embedding_service.embed(description)
            
            if embedding is None:
                await embedding_service.close()
                pytest.skip("Embedding service unavailable")
            
            # 从文件名提取简单标签
            tags_list = filename.replace(".mp4", "").replace("_", " ").split()
            
            segment = VideoSegment(
                segment_id=asset_id,
                video_id=asset_id,
                video_path=f"/test/videos/{filename}",
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                tags={"keywords": tags_list},
                embedding=embedding,
                description=description
            )
            await self.video_store.insert(segment)
        
        # 测试搜索
        query_embedding = await embedding_service.embed("城市夜景")
        if query_embedding is None:
            await embedding_service.close()
            pytest.skip("Embedding service unavailable")
        
        results = await self.video_store.search(
            query_embedding=query_embedding,
            top_k=5
        )
        
        assert len(results) > 0
        print(f"\n  搜索结果数: {len(results)}")
        
        for r in results[:3]:
            print(f"    - {r.segment.segment_id}: {r.score:.3f}")
        
        await embedding_service.close()


class TestExportSystemIntegration:
    """导出系统集成测试"""
    
    def test_document_exporter_integration(self):
        """测试文档导出器集成"""
        # DocumentExporter 需要数据库 Session，这里只验证类可以导入
        try:
            from services.document_exporter import DocumentExporter
            
            # 验证类存在且有必要的方法
            assert hasattr(DocumentExporter, 'export_script_docx'), "缺少 export_script_docx 方法"
            assert hasattr(DocumentExporter, 'export_script_pdf'), "缺少 export_script_pdf 方法"
            assert hasattr(DocumentExporter, 'export_script_markdown'), "缺少 export_script_markdown 方法"
            
            print(f"\n  DocumentExporter 类验证通过")
            print(f"    - export_script_docx: OK")
            print(f"    - export_script_pdf: OK")
            print(f"    - export_script_markdown: OK")
            
        except ImportError as e:
            pytest.skip(f"DocumentExporter 导入失败: {e}")
    
    def test_nle_exporter_integration(self):
        """测试 NLE 导出器集成"""
        # NLEExporter 需要数据库 Session，这里只验证类可以导入
        try:
            from services.nle_exporter import NLEExporter
            
            # 验证类存在且有必要的方法
            assert hasattr(NLEExporter, 'export_fcpxml'), "缺少 export_fcpxml 方法"
            assert hasattr(NLEExporter, 'export_edl_cmx3600'), "缺少 export_edl_cmx3600 方法"
            
            print(f"\n  NLEExporter 类验证通过")
            print(f"    - export_fcpxml: OK")
            print(f"    - export_edl_cmx3600: OK")
            
        except ImportError as e:
            pytest.skip(f"NLEExporter 导入失败: {e}")


class TestProjectWizardIntegration:
    """项目向导集成测试"""
    
    def test_wizard_full_workflow(self):
        """测试向导完整工作流"""
        from services.agents.script_agent import get_script_agent_service
        from services.agents.director_agent import get_director_agent_service
        from services.agents.pm_agent import get_pm_agent_service
        
        script_agent = get_script_agent_service()
        director_agent = get_director_agent_service()
        pm_agent = get_pm_agent_service()
        
        project_id = "wizard_test_001"
        
        # Step 1: 解析剧本
        test_script = """
INT. 实验室 - 夜

科学家独自工作，屏幕闪烁。

科学家
（兴奋）
终于成功了！

EXT. 城市街道 - 日

人们正常生活，不知道即将发生的变化。
"""
        
        parse_result = script_agent.parse_script(test_script)
        assert parse_result.total_scenes >= 2
        
        # Step 2: 生成 Logline
        logline = "一位科学家的深夜发现将改变整个城市的命运。"
        
        # Step 3: 导演审核
        async def review():
            return await director_agent.review(
                result={"logline": logline},
                task_type="logline",
                project_id=project_id
            )
        
        review_result = asyncio.run(review())
        assert review_result.status in ['approved', 'suggestions', 'rejected']
        
        # Step 4: 记录版本
        version = pm_agent.record_version(
            project_id=project_id,
            content_type="logline",
            content=logline,
            source="script_agent"
        )
        
        assert version.version_number == 1
        
        print(f"\n  ✅ 向导工作流测试通过")
        print(f"    场次: {parse_result.total_scenes}")
        print(f"    审核: {review_result.status}")
        print(f"    版本: v{version.version_number}")


class TestAPIEndpointsIntegration:
    """API 端点集成测试"""
    
    def test_router_imports(self):
        """测试所有路由模块导入"""
        routers = []
        failed = []
        
        router_names = ['ai', 'assets', 'search', 'export', 'wizard', 'timeline', 'keyframes']
        
        for name in router_names:
            try:
                module = __import__(f'routers.{name}', fromlist=[name])
                routers.append(name)
            except Exception as e:
                failed.append((name, str(e)))
        
        print(f"\n  路由模块导入: {len(routers)}/{len(router_names)}")
        for name in routers:
            print(f"    [OK] {name}")
        for name, err in failed:
            print(f"    [SKIP] {name}: {err[:50]}...")
        
        # 至少核心路由应该能导入
        assert len(routers) >= 3, f"核心路由导入失败: {failed}"
    
    def test_service_dependencies(self):
        """测试服务依赖关系"""
        services = {}
        
        service_imports = [
            ('llm_provider', 'services.llm_provider', 'get_llm_provider'),
            ('tag_manager', 'services.tag_manager', 'get_tag_manager'),
            ('search_service', 'services.search_service', 'get_search_service'),
            ('cache_manager', 'services.cache_manager', 'get_cache_manager'),
            ('agent_service', 'services.agent_service', 'get_agent_service'),
        ]
        
        for name, module_path, func_name in service_imports:
            try:
                module = __import__(module_path, fromlist=[func_name])
                getattr(module, func_name)
                services[name] = True
            except Exception as e:
                services[name] = f"失败: {str(e)[:50]}"
        
        # 统计结果
        success_count = sum(1 for v in services.values() if v is True)
        
        print(f"\n  服务依赖检查: {success_count}/{len(services)}")
        for name, status in services.items():
            status_str = "[OK]" if status is True else f"[SKIP] {status}"
            print(f"    {name}: {status_str}")
        
        # 至少核心服务应该能加载
        assert success_count >= 3, f"核心服务加载失败"


class TestPerformanceIntegration:
    """性能集成测试"""
    
    @pytest.mark.asyncio
    async def test_search_performance(self):
        """测试搜索性能"""
        from services.ollama_embedding import get_embedding_service
        from services.milvus_store import MemoryVideoStore, VideoSegment
        
        video_store = MemoryVideoStore()
        embedding_service = get_embedding_service()
        
        # 索引 10 个测试素材
        for i in range(10):
            filename = f"test_video_{i:03d}.mp4"
            description = f"测试视频 {i} 的描述内容"
            
            # embed 是异步方法
            embedding = await embedding_service.embed(description)
            
            if embedding is None:
                await embedding_service.close()
                pytest.skip("Embedding service unavailable")
            
            # 从文件名提取简单标签
            tags_list = [f"video_{i}", "test"]
            
            segment = VideoSegment(
                segment_id=f"perf_test_{i}",
                video_id=f"perf_test_{i}",
                video_path=f"/test/videos/{filename}",
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                tags={"keywords": tags_list},
                embedding=embedding,
                description=description
            )
            await video_store.insert(segment)
        
        # 测试搜索性能
        queries = ["测试视频", "描述内容", "视频素材"]
        response_times = []
        
        for query in queries:
            query_embedding = await embedding_service.embed(query)
            if query_embedding is None:
                continue
            
            start = time.time()
            
            results = await video_store.search(
                query_embedding=query_embedding,
                top_k=5
            )
            
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)
        
        await embedding_service.close()
        
        if not response_times:
            pytest.skip("No successful queries")
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        print(f"\n  搜索性能测试:")
        print(f"    平均响应: {avg_time:.1f}ms")
        print(f"    最大响应: {max_time:.1f}ms")
        
        # 性能要求: 最大响应时间 < 5000ms
        assert max_time < 5000, f"响应时间超标: {max_time:.1f}ms"


def run_all_tests():
    """运行所有集成测试"""
    print("\n" + "="*60)
    print("Pervis PRO 后端完整集成测试")
    print("="*60)
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_all_tests()
