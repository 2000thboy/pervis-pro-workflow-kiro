# -*- coding: utf-8 -*-
"""
LLM服务属性测试

Feature: multi-agent-workflow-core
Property 31: AI辅助功能可用性
Property 32: AI内容验证有效性
Requirements: 6.1, 6.2
"""
import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck as HypothesisHealthCheck

from app.core.llm_service import (
    LLMService,
    LLMConfig,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMRole,
    AIUsageRecord,
    MockLLMClient,
)


class TestLLMServiceBasics:
    """LLM服务基础测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        """创建Mock LLM服务"""
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service.is_initialized
        assert service.config.provider == LLMProvider.MOCK
    
    @pytest.mark.asyncio
    async def test_service_availability(self, service):
        """测试服务可用性检查"""
        is_available = await service.is_available()
        assert is_available == True
    
    @pytest.mark.asyncio
    async def test_basic_chat(self, service):
        """测试基础聊天功能"""
        messages = [
            LLMMessage(role=LLMRole.USER, content="你好")
        ]
        response = await service.chat(messages)
        
        assert response is not None
        assert isinstance(response, LLMResponse)
        assert response.content != ""
        assert response.provider == LLMProvider.MOCK
    
    @pytest.mark.asyncio
    async def test_basic_complete(self, service):
        """测试基础补全功能"""
        response = await service.complete("请生成一段描述")
        
        assert response is not None
        assert response.content != ""


class TestAIAssistFeatures:
    """
    AI辅助功能测试
    
    Property 31: AI辅助功能可用性
    验证需求: Requirements 6.1
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        
        # 设置模拟响应
        client = service.client
        if isinstance(client, MockLLMClient):
            client.set_response("剧本", "这是一段精彩的剧本内容...")
            client.set_response("对话", "角色A：你好\n角色B：你好")
            client.set_response("场景", "夜晚，城市街道，霓虹灯闪烁...")
        
        return service
    
    @pytest.mark.asyncio
    async def test_assist_content_creation(self, service):
        """测试AI辅助内容创作"""
        response = await service.assist_content_creation(
            content_type="剧本",
            context="一个关于友情的故事",
            requirements="需要有冲突和转折"
        )
        
        assert response is not None
        assert response.content != ""
    
    @pytest.mark.asyncio
    async def test_assist_different_content_types(self, service):
        """测试不同类型的内容创作"""
        content_types = ["剧本", "对话", "场景描述"]
        
        for content_type in content_types:
            response = await service.assist_content_creation(
                content_type=content_type,
                context="测试上下文"
            )
            assert response is not None
            assert response.content != ""
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, service):
        """测试带系统提示的生成"""
        response = await service.generate_with_system(
            system_prompt="你是一个专业编剧",
            user_prompt="请写一段开场白"
        )
        
        assert response is not None
        assert response.content != ""
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        content_type=st.sampled_from(["剧本", "对话", "描述", "旁白"]),
        context=st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyz0123456789 ')
    )
    async def test_assist_content_creation_property(self, service, content_type, context):
        """
        Property 31: AI辅助功能可用性
        
        对于任何用户的文字内容创作需求，系统应该提供LLM AI生成辅助功能
        """
        response = await service.assist_content_creation(
            content_type=content_type,
            context=context
        )
        
        # 验证：AI辅助功能应该返回有效响应
        assert response is not None
        assert isinstance(response, LLMResponse)
        assert response.content is not None


class TestContentValidation:
    """
    内容验证测试
    
    Property 32: AI内容验证有效性
    验证需求: Requirements 6.2
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        
        # 设置模拟响应
        client = service.client
        if isinstance(client, MockLLMClient):
            client.set_response("验证", '{"valid": true, "score": 85, "issues": [], "suggestions": []}')
        
        return service
    
    @pytest.mark.asyncio
    async def test_validate_content_with_llm(self, service):
        """测试使用LLM验证内容"""
        result = await service.validate_content(
            content="这是一段测试内容",
            validation_type="quality",
            criteria="内容应该清晰、专业"
        )
        
        assert result is not None
        assert "valid" in result or "validation_type" in result
    
    @pytest.mark.asyncio
    async def test_register_custom_validator(self, service):
        """测试注册自定义验证器"""
        # 注册一个简单的长度验证器
        service.register_validator(
            "length_check",
            lambda content: len(content) >= 10
        )
        
        # 验证短内容
        result = await service.validate_content(
            content="短",
            validation_type="length_check"
        )
        assert result["valid"] == False
        
        # 验证长内容
        result = await service.validate_content(
            content="这是一段足够长的内容",
            validation_type="length_check"
        )
        assert result["valid"] == True
    
    @pytest.mark.asyncio
    @settings(max_examples=100, deadline=None, suppress_health_check=[HypothesisHealthCheck.function_scoped_fixture])
    @given(
        content=st.text(min_size=10, max_size=200, alphabet='abcdefghijklmnopqrstuvwxyz0123456789 '),
        validation_type=st.sampled_from(["quality", "format", "style", "grammar"])
    )
    async def test_content_validation_property(self, service, content, validation_type):
        """
        Property 32: AI内容验证有效性
        
        对于任何AI生成的内容，系统应该提供有效的辅助验证功能
        """
        result = await service.validate_content(
            content=content,
            validation_type=validation_type
        )
        
        # 验证：验证功能应该返回有效结果
        assert result is not None
        assert isinstance(result, dict)
        # 结果应该包含验证类型或有效性标志
        assert "validation_type" in result or "valid" in result


class TestProjectInfoCompletion:
    """项目信息补全测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        
        # 设置模拟响应
        client = service.client
        if isinstance(client, MockLLMClient):
            client.set_response("补全", '{"aspect_ratio": "16:9", "duration": 120, "genre": "剧情"}')
        
        return service
    
    @pytest.mark.asyncio
    async def test_complete_project_info(self, service):
        """测试项目信息补全"""
        partial_info = {
            "name": "测试项目",
            "description": "一个关于冒险的故事"
        }
        required_fields = ["aspect_ratio", "duration", "genre"]
        
        result = await service.complete_project_info(partial_info, required_fields)
        
        assert result is not None
        assert "name" in result
        assert result["name"] == "测试项目"


class TestScriptAnalysis:
    """剧本分析测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        
        # 设置模拟响应
        client = service.client
        if isinstance(client, MockLLMClient):
            client.set_response("分析", '''
            {
                "scenes": [{"name": "开场", "duration_estimate": 60, "description": "介绍主角"}],
                "characters": ["主角", "配角"],
                "themes": ["友情", "成长"],
                "mood": "温馨",
                "estimated_duration": 300
            }
            ''')
        
        return service
    
    @pytest.mark.asyncio
    async def test_analyze_script(self, service):
        """测试剧本分析"""
        script = """
        场景一：城市街道
        主角走在繁忙的街道上，若有所思。
        
        场景二：咖啡馆
        主角与朋友相遇，开始交谈。
        """
        
        result = await service.analyze_script(script)
        
        assert result is not None
        assert isinstance(result, dict)


class TestSearchKeywordGeneration:
    """搜索关键词生成测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        
        # 设置模拟响应
        client = service.client
        if isinstance(client, MockLLMClient):
            client.set_response("关键词", '["城市", "夜景", "霓虹灯", "街道"]')
        
        return service
    
    @pytest.mark.asyncio
    async def test_generate_search_keywords(self, service):
        """测试生成搜索关键词"""
        keywords = await service.generate_search_keywords(
            scene_description="夜晚的城市街道，霓虹灯闪烁",
            asset_type="video"
        )
        
        assert keywords is not None
        assert isinstance(keywords, list)
        assert len(keywords) > 0


class TestProfessionalAdvice:
    """专业建议测试"""
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_provide_script_advice(self, service):
        """测试编剧建议"""
        advice = await service.provide_professional_advice(
            domain="script",
            question="如何写好开场白？"
        )
        
        assert advice is not None
        assert isinstance(advice, str)
    
    @pytest.mark.asyncio
    async def test_provide_art_advice(self, service):
        """测试美术建议"""
        advice = await service.provide_professional_advice(
            domain="art",
            question="如何设计角色造型？",
            context="科幻题材的电影"
        )
        
        assert advice is not None
        assert isinstance(advice, str)
    
    @pytest.mark.asyncio
    async def test_provide_market_advice(self, service):
        """测试市场建议"""
        advice = await service.provide_professional_advice(
            domain="market",
            question="目标受众是什么？"
        )
        
        assert advice is not None


class TestUsageRecording:
    """
    使用记录测试
    
    验证需求: Requirements 6.5
    """
    
    @pytest_asyncio.fixture
    async def service(self):
        config = LLMConfig.mock()
        service = LLMService(config)
        await service.initialize()
        service.clear_usage_records()
        return service
    
    @pytest.mark.asyncio
    async def test_usage_recording(self, service):
        """测试使用记录"""
        # 执行一些操作
        await service.complete("测试提示1")
        await service.complete("测试提示2")
        
        records = service.get_usage_records()
        
        assert len(records) == 2
        assert all(isinstance(r, AIUsageRecord) for r in records)
    
    @pytest.mark.asyncio
    async def test_usage_statistics(self, service):
        """测试使用统计"""
        # 执行一些操作
        await service.complete("测试1", operation="test_op")
        await service.complete("测试2", operation="test_op")
        await service.complete("测试3", operation="other_op")
        
        stats = service.get_usage_statistics()
        
        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 3
        assert stats["failed_requests"] == 0
        assert "test_op" in stats["operations"]
        assert stats["operations"]["test_op"] == 2
    
    @pytest.mark.asyncio
    async def test_filter_records_by_operation(self, service):
        """测试按操作类型过滤记录"""
        await service.complete("测试1", operation="op_a")
        await service.complete("测试2", operation="op_b")
        await service.complete("测试3", operation="op_a")
        
        records_a = service.get_usage_records(operation="op_a")
        records_b = service.get_usage_records(operation="op_b")
        
        assert len(records_a) == 2
        assert len(records_b) == 1
    
    @pytest.mark.asyncio
    async def test_clear_usage_records(self, service):
        """测试清空使用记录"""
        await service.complete("测试")
        assert len(service.get_usage_records()) > 0
        
        service.clear_usage_records()
        assert len(service.get_usage_records()) == 0


class TestLLMConfig:
    """LLM配置测试"""
    
    def test_ollama_config(self):
        """测试Ollama配置"""
        config = LLMConfig.ollama(model="llama2")
        
        assert config.provider == LLMProvider.OLLAMA
        assert config.model == "llama2"
        assert "localhost" in config.base_url
    
    def test_openai_config(self):
        """测试OpenAI配置"""
        config = LLMConfig.openai(model="gpt-4", api_key="test-key")
        
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
    
    def test_gemini_config(self):
        """测试Gemini配置"""
        config = LLMConfig.gemini(model="gemini-pro", api_key="test-key")
        
        assert config.provider == LLMProvider.GEMINI
        assert config.model == "gemini-pro"
    
    def test_mock_config(self):
        """测试Mock配置"""
        config = LLMConfig.mock()
        
        assert config.provider == LLMProvider.MOCK


class TestLLMMessage:
    """LLM消息测试"""
    
    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = LLMMessage(role=LLMRole.USER, content="你好")
        d = msg.to_dict()
        
        assert d["role"] == "user"
        assert d["content"] == "你好"
    
    def test_different_roles(self):
        """测试不同角色"""
        roles = [LLMRole.SYSTEM, LLMRole.USER, LLMRole.ASSISTANT]
        
        for role in roles:
            msg = LLMMessage(role=role, content="测试")
            d = msg.to_dict()
            assert d["role"] == role.value


class TestMockLLMClient:
    """Mock LLM客户端测试"""
    
    @pytest.mark.asyncio
    async def test_set_custom_response(self):
        """测试设置自定义响应"""
        config = LLMConfig.mock()
        client = MockLLMClient(config)
        
        client.set_response("特定关键词", "自定义响应内容")
        
        messages = [LLMMessage(role=LLMRole.USER, content="包含特定关键词的问题")]
        response = await client.chat(messages)
        
        assert response.content == "自定义响应内容"
    
    @pytest.mark.asyncio
    async def test_set_unavailable(self):
        """测试设置不可用状态"""
        config = LLMConfig.mock()
        client = MockLLMClient(config)
        
        client.set_available(False)
        
        assert await client.is_available() == False
        
        with pytest.raises(ConnectionError):
            messages = [LLMMessage(role=LLMRole.USER, content="测试")]
            await client.chat(messages)
