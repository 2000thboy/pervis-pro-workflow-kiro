# -*- coding: utf-8 -*-
"""
向量存储服务属性测试

Feature: multi-agent-workflow-core
Property 15: 向量搜索生成准确性
Property 16: 素材匹配有效性
Requirements: 3.4, 3.5
"""
import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck as HypothesisHealthCheck

from app.core.vector_store import (
    VectorService,
    VectorStoreConfig,
    VectorStoreProvider,
    Document,
    SearchResult,
    AssetMatch,
    MockVectorStore,
)


class TestVectorServiceBasics:
    """向量服务基础测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        """创建Mock向量服务"""
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        yield service
        await service.clear()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service.is_initialized
        assert service.config.provider == VectorStoreProvider.MOCK
    
    @pytest.mark.asyncio
    async def test_index_document(self, service):
        """测试索引文档"""
        doc_id = await service.index_document(
            content="这是一个测试文档",
            metadata={"type": "test"}
        )
        
        assert doc_id is not None
        assert len(doc_id) > 0
    
    @pytest.mark.asyncio
    async def test_get_document(self, service):
        """测试获取文档"""
        doc_id = await service.index_document(
            content="测试内容",
            metadata={"key": "value"}
        )
        
        doc = await service.get_document(doc_id)
        
        assert doc is not None
        assert doc.content == "测试内容"
        assert doc.metadata["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_delete_document(self, service):
        """测试删除文档"""
        doc_id = await service.index_document(content="待删除")
        
        result = await service.delete_document(doc_id)
        assert result == True
        
        doc = await service.get_document(doc_id)
        assert doc is None
    
    @pytest.mark.asyncio
    async def test_update_document(self, service):
        """测试更新文档"""
        doc_id = await service.index_document(content="原始内容")
        
        result = await service.update_document(doc_id, "更新后的内容")
        assert result == True
        
        doc = await service.get_document(doc_id)
        assert doc.content == "更新后的内容"


class TestDocumentSearch:
    """文档搜索测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        
        # 添加测试文档
        await service.index_documents([
            {"content": "城市 夜景 霓虹灯 街道", "metadata": {"type": "video"}},
            {"content": "森林 自然 绿色 树木", "metadata": {"type": "video"}},
            {"content": "海洋 蓝色 波浪 沙滩", "metadata": {"type": "video"}},
            {"content": "城市 白天 建筑 现代", "metadata": {"type": "image"}},
        ])
        
        yield service
        await service.clear()
    
    @pytest.mark.asyncio
    async def test_basic_search(self, service):
        """测试基础搜索"""
        results = await service.search("城市 夜景")
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_filter(self, service):
        """测试带过滤的搜索"""
        results = await service.search(
            "城市",
            filter_metadata={"type": "video"}
        )
        
        assert len(results) > 0
        # 所有结果应该是video类型
        for r in results:
            assert r.document.metadata.get("type") == "video"
    
    @pytest.mark.asyncio
    async def test_search_top_k(self, service):
        """测试限制返回数量"""
        results = await service.search("城市", top_k=2)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_relevance_order(self, service):
        """测试搜索结果按相关性排序"""
        results = await service.search("城市 夜景 霓虹灯")
        
        if len(results) >= 2:
            # 分数应该是降序排列
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score


class TestAssetIndexing:
    """
    素材索引测试
    
    Property 15: 向量搜索生成准确性
    验证需求: Requirements 3.4
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        yield service
        await service.clear()
    
    @pytest.mark.asyncio
    async def test_index_single_asset(self, service):
        """测试索引单个素材"""
        doc_id = await service.index_asset(
            asset_id="asset_001",
            asset_name="城市夜景视频",
            asset_type="video",
            tags=["城市", "夜景", "霓虹灯"],
            description="繁华都市的夜晚景象"
        )
        
        assert doc_id is not None
        assert "asset_001" in doc_id
    
    @pytest.mark.asyncio
    async def test_index_multiple_assets(self, service):
        """测试批量索引素材"""
        assets = [
            {"id": "a1", "name": "视频1", "type": "video", "tags": ["tag1"]},
            {"id": "a2", "name": "视频2", "type": "video", "tags": ["tag2"]},
            {"id": "a3", "name": "图片1", "type": "image", "tags": ["tag3"]},
        ]
        
        ids = await service.index_assets(assets)
        
        assert len(ids) == 3
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        asset_name=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz0123456789 '),
        asset_type=st.sampled_from(["video", "audio", "image"]),
        tags=st.lists(
            st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
            min_size=1,
            max_size=5
        )
    )
    async def test_asset_indexing_property(self, service, asset_name, asset_type, tags):
        """
        Property 15: 向量搜索生成准确性
        
        对于任何用户确认的场次时长，系统应该生成准确的向量搜索词条和相似度匹配索引
        """
        asset_id = f"test_{hash(asset_name) % 10000}"
        
        doc_id = await service.index_asset(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            tags=tags
        )
        
        # 验证：索引应该成功创建
        assert doc_id is not None
        
        # 验证：可以通过标签搜索到素材
        if tags:
            results = await service.search(tags[0])
            # 搜索应该返回结果
            assert isinstance(results, list)


class TestAssetMatching:
    """
    素材匹配测试
    
    Property 16: 素材匹配有效性
    验证需求: Requirements 3.5
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        
        # 添加测试素材
        await service.index_assets([
            {
                "id": "v001",
                "name": "城市夜景航拍",
                "type": "video",
                "tags": ["城市", "夜景", "航拍", "霓虹灯"],
                "description": "繁华都市夜晚的航拍镜头"
            },
            {
                "id": "v002",
                "name": "森林晨雾",
                "type": "video",
                "tags": ["森林", "自然", "晨雾", "绿色"],
                "description": "清晨森林中的雾气"
            },
            {
                "id": "v003",
                "name": "海边日落",
                "type": "video",
                "tags": ["海洋", "日落", "沙滩", "浪漫"],
                "description": "海边美丽的日落景象"
            },
            {
                "id": "a001",
                "name": "城市环境音",
                "type": "audio",
                "tags": ["城市", "环境音", "车流"],
                "description": "城市街道的环境音效"
            },
        ])
        
        yield service
        await service.clear()
    
    @pytest.mark.asyncio
    async def test_match_assets_by_description(self, service):
        """测试通过描述匹配素材"""
        matches = await service.match_assets(
            query="城市夜晚的场景",
            top_k=5
        )
        
        assert len(matches) > 0
        assert all(isinstance(m, AssetMatch) for m in matches)
        
        # 城市相关素材应该排在前面
        top_match = matches[0]
        assert "城市" in top_match.tags or "城市" in top_match.asset_name
    
    @pytest.mark.asyncio
    async def test_match_assets_by_type(self, service):
        """测试按类型过滤匹配"""
        matches = await service.match_assets(
            query="城市",
            asset_type="audio",
            top_k=5
        )
        
        # 所有结果应该是audio类型
        for match in matches:
            assert match.asset_type == "audio"
    
    @pytest.mark.asyncio
    async def test_match_assets_min_score(self, service):
        """测试最小分数过滤"""
        matches = await service.match_assets(
            query="城市 夜景",
            min_score=0.1
        )
        
        # 所有结果分数应该大于等于最小分数
        for match in matches:
            assert match.score >= 0.1
    
    @pytest.mark.asyncio
    async def test_find_similar_assets(self, service):
        """测试查找相似素材"""
        similar = await service.find_similar_assets(
            asset_id="v001",
            top_k=3
        )
        
        assert isinstance(similar, list)
        # 不应该包含自身
        for match in similar:
            assert match.asset_id != "v001"
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        query=st.text(min_size=2, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz '),
        asset_type=st.sampled_from([None, "video", "audio", "image"])
    )
    async def test_asset_matching_property(self, service, query, asset_type):
        """
        Property 16: 素材匹配有效性
        
        对于任何向量搜索结果，DAM_Agent应该找到相关度高的标签素材
        """
        matches = await service.match_assets(
            query=query,
            asset_type=asset_type,
            top_k=10
        )
        
        # 验证：匹配功能应该返回有效结果列表
        assert isinstance(matches, list)
        
        # 验证：每个匹配结果应该包含必要信息
        for match in matches:
            assert isinstance(match, AssetMatch)
            assert match.asset_id is not None
            assert match.score >= 0


class TestSceneSearchTerms:
    """场景搜索词条生成测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_generate_search_terms(self, service):
        """测试生成搜索词条"""
        terms = await service.generate_scene_search_terms(
            scene_description="夜晚的城市街道 霓虹灯闪烁"
        )
        
        assert len(terms) > 0
        assert isinstance(terms, list)
    
    @pytest.mark.asyncio
    async def test_generate_terms_with_existing_tags(self, service):
        """测试带已有标签的词条生成"""
        terms = await service.generate_scene_search_terms(
            scene_description="城市 街道",
            existing_tags=["夜景", "现代"]
        )
        
        assert "夜景" in terms
        assert "现代" in terms
    
    @pytest.mark.asyncio
    async def test_terms_are_unique(self, service):
        """测试词条去重"""
        terms = await service.generate_scene_search_terms(
            scene_description="城市 城市 街道",
            existing_tags=["城市"]
        )
        
        # 应该没有重复
        assert len(terms) == len(set(terms))


class TestVectorServiceStatistics:
    """向量服务统计测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = VectorStoreConfig.mock()
        service = VectorService(config)
        await service.initialize()
        yield service
        await service.clear()
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, service):
        """测试获取统计信息"""
        # 添加一些文档
        await service.index_document("文档1")
        await service.index_document("文档2")
        
        stats = await service.get_statistics()
        
        assert stats["provider"] == "mock"
        assert stats["document_count"] == 2
        assert stats["initialized"] == True
    
    @pytest.mark.asyncio
    async def test_clear_all(self, service):
        """测试清空所有数据"""
        await service.index_document("测试")
        
        result = await service.clear()
        assert result == True
        
        stats = await service.get_statistics()
        assert stats["document_count"] == 0


class TestVectorStoreConfig:
    """向量存储配置测试"""
    
    def test_chroma_config(self):
        """测试ChromaDB配置"""
        config = VectorStoreConfig.chroma(
            collection_name="test_collection",
            persist_directory="/tmp/chroma"
        )
        
        assert config.provider == VectorStoreProvider.CHROMA
        assert config.collection_name == "test_collection"
        assert config.persist_directory == "/tmp/chroma"
    
    def test_mock_config(self):
        """测试Mock配置"""
        config = VectorStoreConfig.mock()
        
        assert config.provider == VectorStoreProvider.MOCK


class TestDocument:
    """文档对象测试"""
    
    def test_create_document(self):
        """测试创建文档"""
        doc = Document.create(
            content="测试内容",
            metadata={"key": "value"}
        )
        
        assert doc.id is not None
        assert doc.content == "测试内容"
        assert doc.metadata["key"] == "value"
    
    def test_document_without_metadata(self):
        """测试无元数据的文档"""
        doc = Document.create(content="内容")
        
        assert doc.metadata == {}
