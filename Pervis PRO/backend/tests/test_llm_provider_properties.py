"""
LLM Provider 属性测试
Property 2: API Key 配置验证
Property 6: LLM Provider 切换
Validates: Requirements 1.3, 7.1
"""

import os
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLLMProviderConfiguration:
    """LLM Provider 配置测试"""
    
    def test_gemini_provider_requires_api_key(self):
        """
        Property 2: API Key 配置验证
        当 LLM_PROVIDER 为 gemini 且 GEMINI_API_KEY 未设置时，
        如果 LLM_AUTO_FALLBACK=false，应抛出 ValueError
        Validates: Requirements 1.3
        """
        # 清除环境变量，禁用自动回退
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': '',
            'LLM_AUTO_FALLBACK': 'false'
        }, clear=False):
            # 重新加载模块以应用新的环境变量
            from services import llm_provider
            from importlib import reload
            reload(llm_provider)
            
            with pytest.raises(ValueError) as exc_info:
                llm_provider.get_llm_provider()
            
            assert "GEMINI_API_KEY" in str(exc_info.value)
    
    def test_gemini_provider_with_valid_key(self):
        """
        当 GEMINI_API_KEY 已配置时，应返回 GeminiProvider
        Validates: Requirements 1.2
        """
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test_valid_key'
        }, clear=False):
            from services import llm_provider
            from importlib import reload
            
            # Mock GeminiClient 以避免真实 API 调用
            with patch('services.llm_provider.GeminiProvider') as mock_provider:
                mock_provider.return_value = MagicMock()
                reload(llm_provider)
                
                provider = llm_provider.get_llm_provider()
                assert provider is not None
    
    def test_ollama_provider_selection(self):
        """
        Property 6: LLM Provider 切换
        当 LLM_PROVIDER 为 local 时，应返回 OllamaProvider
        Validates: Requirements 7.1
        """
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'local',
            'OLLAMA_BASE_URL': 'http://localhost:11434/v1',
            'LOCAL_MODEL_NAME': 'qwen2.5:14b'
        }, clear=False):
            from services import llm_provider
            from importlib import reload
            reload(llm_provider)
            
            provider = llm_provider.get_llm_provider()
            assert isinstance(provider, llm_provider.OllamaProvider)
    
    @given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=10, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_api_key_any_non_empty_value_accepted(self, api_key: str):
        """
        Property 2 扩展: 任何非空 API Key 都应被接受（不验证格式）
        Validates: Requirements 1.2
        """
        if not api_key.strip():
            return  # 跳过空字符串
        
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'gemini',
            'GEMINI_API_KEY': api_key
        }, clear=False):
            from services import llm_provider
            from importlib import reload
            
            # Mock GeminiClient
            with patch('services.llm_provider.GeminiProvider') as mock_provider:
                mock_provider.return_value = MagicMock()
                reload(llm_provider)
                
                # 不应抛出异常
                try:
                    provider = llm_provider.get_llm_provider()
                    assert provider is not None
                except ValueError:
                    pytest.fail(f"Valid API key '{api_key}' was rejected")


class TestLLMProviderSwitch:
    """LLM Provider 切换测试"""
    
    @given(st.sampled_from(['gemini', 'local', 'GEMINI', 'LOCAL', 'Gemini', 'Local']))
    @settings(max_examples=100, deadline=None)
    def test_provider_type_case_insensitive(self, provider_type: str):
        """
        Property 6: Provider 类型应该不区分大小写
        Validates: Requirements 7.1
        """
        env_vars = {
            'LLM_PROVIDER': provider_type,
            'OLLAMA_BASE_URL': 'http://localhost:11434/v1',
            'LOCAL_MODEL_NAME': 'qwen2.5:14b'
        }
        
        if provider_type.lower() == 'gemini':
            env_vars['GEMINI_API_KEY'] = 'test_key'
        
        with patch.dict(os.environ, env_vars, clear=False):
            from services import llm_provider
            from importlib import reload
            
            if provider_type.lower() == 'gemini':
                with patch('services.llm_provider.GeminiProvider') as mock_provider:
                    mock_provider.return_value = MagicMock()
                    reload(llm_provider)
                    provider = llm_provider.get_llm_provider()
            else:
                reload(llm_provider)
                provider = llm_provider.get_llm_provider()
            
            assert provider is not None
            
            if provider_type.lower() == 'local':
                assert isinstance(provider, llm_provider.OllamaProvider)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
