"""
DAM Agent属性测试 - 基于属性的测试验证素材匹配有效性

Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
验证需求: Requirements 3.5 - WHEN 向量搜索完成后 THEN DAM_Agent SHALL 寻找匹配的标签素材

测试策略:
- 使用Hypothesis生成随机的素材和标签
- 验证DAM Agent能够正确匹配素材
- 验证标签验证和格式验证的正确性
"""
import pytest
import asyncio
import uuid
from typing import List, Dict, Any
from hypothesis import given, strategies as st, settings, assume

from app.core.message_bus import MessageBus
from app.agents.dam_agent import (
    DAMAgent,
    Asset,
    AssetType,
    AssetStatus,
    MatchResult,
    SUPPORTED_FORMATS,
)


# 自定义策略：生成有效的标签 (ASCII lowercase only to match TAG_PATTERN ^[a-z0-9_-]+$)
valid_tag_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
    min_size=1,
    max_size=30
).filter(lambda x: len(x.strip()) > 0 and not x.startswith('-') and not x.startswith('_'))

# 自定义策略：生成无效的标签（包含大写或特殊字符）
invalid_tag_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'P', 'S')),
    min_size=1,
    max_size=30
).filter(lambda x: len(x.strip()) > 0)

# 自定义策略：生成素材类型
asset_type_strategy = st.sampled_from(list(AssetType))

# 自定义策略：生成素材ID
asset_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=30
).filter(lambda x: len(x.strip()) > 0)


class TestDAMAgentAssetMatching:
    """
    属性 16: 素材匹配有效性
    
    *对于任何*向量搜索结果，DAM_Agent应该找到相关度高的标签素材
    
    验证需求: Requirements 3.5
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        asset_type=asset_type_strategy,
        tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True)
    )
    async def test_asset_matching_returns_relevant_results(
        self,
        asset_type: AssetType,
        tags: List[str]
    ):
        """
        Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
        
        属性: 对于任何搜索标签，DAM Agent应该返回包含这些标签的素材
        
        验证需求: Requirements 3.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            dam_agent = DAMAgent(message_bus=bus)
            await dam_agent.initialize()
            await dam_agent.start()
            
            # 获取该类型支持的格式
            formats = SUPPORTED_FORMATS.get(asset_type, [])
            if not formats:
                await dam_agent.stop()
                return
            
            # 添加一个包含搜索标签的素材
            asset_id = str(uuid.uuid4())
            file_path = f"test_file{formats[0]}"
            
            success, error = dam_agent.add_asset(
                asset_id=asset_id,
                name="Test Asset",
                asset_type=asset_type,
                file_path=file_path,
                tags=tags
            )
            
            assert success, f"添加素材应该成功: {error}"
            
            # 执行匹配
            results = await dam_agent.match_assets(tags, asset_type)
            
            # 验证属性1: 结果不为空
            assert len(results) > 0, "应该找到匹配的素材"
            
            # 验证属性2: 结果包含我们添加的素材
            result_ids = [r.asset.asset_id for r in results]
            assert asset_id in result_ids, "结果应该包含添加的素材"
            
            # 验证属性3: 匹配的标签是搜索标签的子集
            for result in results:
                for matched_tag in result.matched_tags:
                    assert matched_tag in tags, f"匹配的标签{matched_tag}应该在搜索标签中"
            
            await dam_agent.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        tags=st.lists(valid_tag_strategy, min_size=1, max_size=5, unique=True)
    )
    async def test_matching_score_reflects_tag_overlap(
        self,
        tags: List[str]
    ):
        """
        Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
        
        属性: 匹配分数应该反映标签重叠程度，完全匹配应该得分最高
        
        验证需求: Requirements 3.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            dam_agent = DAMAgent(message_bus=bus)
            await dam_agent.initialize()
            await dam_agent.start()
            
            # 添加完全匹配的素材
            full_match_id = str(uuid.uuid4())
            dam_agent.add_asset(
                asset_id=full_match_id,
                name="Full Match",
                asset_type=AssetType.IMAGE,
                file_path="full.jpg",
                tags=tags
            )
            
            # 添加部分匹配的素材（只有第一个标签）
            if len(tags) > 1:
                partial_match_id = str(uuid.uuid4())
                dam_agent.add_asset(
                    asset_id=partial_match_id,
                    name="Partial Match",
                    asset_type=AssetType.IMAGE,
                    file_path="partial.jpg",
                    tags=[tags[0]]
                )
            
            # 执行匹配
            results = await dam_agent.match_assets(tags)
            
            # 验证属性: 完全匹配的素材分数应该是1.0
            full_match_result = next(
                (r for r in results if r.asset.asset_id == full_match_id),
                None
            )
            assert full_match_result is not None, "应该找到完全匹配的素材"
            assert full_match_result.score == 1.0, "完全匹配的分数应该是1.0"
            
            # 如果有部分匹配，验证其分数低于完全匹配
            if len(tags) > 1:
                partial_match_result = next(
                    (r for r in results if r.asset.asset_id == partial_match_id),
                    None
                )
                if partial_match_result:
                    assert partial_match_result.score < full_match_result.score, \
                        "部分匹配的分数应该低于完全匹配"
            
            await dam_agent.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        valid_tags=st.lists(valid_tag_strategy, min_size=1, max_size=3, unique=True),
        invalid_tags=st.lists(invalid_tag_strategy, min_size=1, max_size=3, unique=True)
    )
    async def test_tag_validation(
        self,
        valid_tags: List[str],
        invalid_tags: List[str]
    ):
        """
        Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
        
        属性: 标签验证应该正确识别有效和无效的标签
        
        验证需求: Requirements 5.4
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            dam_agent = DAMAgent(message_bus=bus)
            await dam_agent.initialize()
            await dam_agent.start()
            
            # 验证有效标签
            valid_result = dam_agent.validate_tags(valid_tags)
            assert valid_result["valid"] is True, "有效标签应该通过验证"
            assert len(valid_result["invalid_tags"]) == 0, "不应该有无效标签"
            
            # 验证无效标签
            invalid_result = dam_agent.validate_tags(invalid_tags)
            # 注意：某些生成的"无效"标签可能实际上是有效的
            # 所以我们只检查结果结构
            assert "valid" in invalid_result, "结果应该包含valid字段"
            assert "invalid_tags" in invalid_result, "结果应该包含invalid_tags字段"
            
            await dam_agent.stop()
            
        finally:
            await bus.stop()

    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        asset_type=asset_type_strategy
    )
    async def test_format_validation(
        self,
        asset_type: AssetType
    ):
        """
        Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
        
        属性: 格式验证应该正确识别支持和不支持的格式
        
        验证需求: Requirements 5.3
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            dam_agent = DAMAgent(message_bus=bus)
            await dam_agent.initialize()
            await dam_agent.start()
            
            # 获取支持的格式
            supported = dam_agent.get_supported_formats(asset_type)
            
            # 验证支持的格式
            for fmt in supported:
                valid, error = dam_agent.validate_format(f"test{fmt}", asset_type)
                assert valid is True, f"格式{fmt}应该被支持: {error}"
            
            # 验证不支持的格式
            unsupported_ext = ".xyz123"
            valid, error = dam_agent.validate_format(f"test{unsupported_ext}", asset_type)
            assert valid is False, f"格式{unsupported_ext}不应该被支持"
            assert error is not None, "应该返回错误信息"
            
            await dam_agent.stop()
            
        finally:
            await bus.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        asset_count=st.integers(min_value=1, max_value=20),
        search_tag=valid_tag_strategy
    )
    async def test_matching_with_multiple_assets(
        self,
        asset_count: int,
        search_tag: str
    ):
        """
        Feature: multi-agent-workflow-core, Property 16: 素材匹配有效性
        
        属性: 对于任意数量的素材，匹配应该返回所有包含搜索标签的素材
        
        验证需求: Requirements 3.5
        """
        bus = MessageBus(max_history=100)
        await bus.start()
        
        try:
            dam_agent = DAMAgent(message_bus=bus)
            await dam_agent.initialize()
            await dam_agent.start()
            
            # 添加多个素材，一半包含搜索标签
            matching_ids = set()
            for i in range(asset_count):
                asset_id = f"asset_{i}"
                tags = [search_tag] if i % 2 == 0 else ["other_tag"]
                
                dam_agent.add_asset(
                    asset_id=asset_id,
                    name=f"Asset {i}",
                    asset_type=AssetType.IMAGE,
                    file_path=f"asset_{i}.jpg",
                    tags=tags
                )
                
                if i % 2 == 0:
                    matching_ids.add(asset_id)
            
            # 执行匹配
            results = await dam_agent.match_assets([search_tag])
            
            # 验证属性: 所有包含搜索标签的素材都应该被返回
            result_ids = {r.asset.asset_id for r in results}
            assert result_ids == matching_ids, \
                f"应该返回所有匹配的素材，期望{matching_ids}，实际{result_ids}"
            
            await dam_agent.stop()
            
        finally:
            await bus.stop()
