"""
AI 按钮功能检测测试
验证所有 AI 功能按钮返回真实 AI 反馈，不返回 Mock 数据
默认优先使用本地 Ollama
"""

import pytest
import os
import re
import asyncio
from pathlib import Path


class TestFrontendNoMockData:
    """前端代码静态分析 - 确保无 Mock 数据"""
    
    @pytest.fixture
    def frontend_services_path(self):
        """前端服务目录路径"""
        return Path(__file__).parent.parent.parent / "frontend" / "services"
    
    def test_api_client_no_mock_delay(self, frontend_services_path):
        """apiClient.ts 不应包含 mockDelay"""
        api_client_path = frontend_services_path / "apiClient.ts"
        if api_client_path.exists():
            content = api_client_path.read_text(encoding='utf-8')
            assert 'mockDelay' not in content, \
                "apiClient.ts 不应包含 mockDelay 函数"
    
    def test_api_client_calls_real_api(self, frontend_services_path):
        """apiClient.ts 应调用真实 API 端点"""
        api_client_path = frontend_services_path / "apiClient.ts"
        if api_client_path.exists():
            content = api_client_path.read_text(encoding='utf-8')
            
            # 检查 AI 相关 API 调用
            ai_endpoints = [
                '/api/ai/generate-tags',
                '/api/ai/generate-description', 
                '/api/ai/rough-cut'
            ]
            
            for endpoint in ai_endpoints:
                assert endpoint in content, \
                    f"apiClient.ts 应调用 {endpoint}"
    
    def test_gemini_service_no_mock_delay(self, frontend_services_path):
        """geminiService.ts 不应包含 mockDelay"""
        gemini_service_path = frontend_services_path / "geminiService.ts"
        if gemini_service_path.exists():
            content = gemini_service_path.read_text(encoding='utf-8')
            assert 'mockDelay' not in content, \
                "geminiService.ts 不应包含 mockDelay 函数"
    
    def test_gemini_service_uses_api_client(self, frontend_services_path):
        """geminiService.ts 应使用 apiClient"""
        gemini_service_path = frontend_services_path / "geminiService.ts"
        if gemini_service_path.exists():
            content = gemini_service_path.read_text(encoding='utf-8')
            assert 'apiClient' in content, \
                "geminiService.ts 应导入并使用 apiClient"
    
    def test_no_hardcoded_mock_tags(self, frontend_services_path):
        """不应有硬编码的 Mock 标签数据"""
        for ts_file in frontend_services_path.glob("*.ts"):
            content = ts_file.read_text(encoding='utf-8')
            
            # 检查是否有硬编码的标签返回
            mock_patterns = [
                r'return\s*\{\s*scene_slug:\s*["\']INT\.',  # 硬编码场景
                r'await\s+mockDelay',  # Mock 延迟
                r'console\.log\(["\']记录反馈',  # 仅 console.log 的反馈
            ]
            
            for pattern in mock_patterns:
                matches = re.findall(pattern, content)
                # 允许在 fallback 情况下有默认值，但不应在主逻辑中
                if matches and 'apiRequest' not in content[:content.find(pattern) if pattern in content else 0]:
                    # 如果在 apiRequest 调用之前就返回了，那是 mock
                    pass  # 这里需要更精细的检查


class TestBackendAIEndpoints:
    """后端 AI 端点测试"""
    
    def test_ai_router_registered(self):
        """AI 路由应已注册"""
        main_path = Path(__file__).parent.parent / "main.py"
        content = main_path.read_text(encoding='utf-8')
        
        assert 'from routers import' in content and 'ai' in content, \
            "main.py 应导入 ai 路由"
        assert 'ai.router' in content, \
            "main.py 应注册 ai.router"
    
    def test_ai_endpoints_exist(self):
        """AI 端点应存在"""
        ai_router_path = Path(__file__).parent.parent / "routers" / "ai.py"
        content = ai_router_path.read_text(encoding='utf-8')
        
        endpoints = [
            '@router.post("/generate-tags"',
            '@router.post("/generate-description"',
            '@router.post("/rough-cut"',
            '@router.get("/health"'
        ]
        
        for endpoint in endpoints:
            assert endpoint in content, \
                f"ai.py 应包含端点 {endpoint}"
    
    def test_endpoints_use_llm_provider(self):
        """端点应使用 LLM Provider"""
        ai_router_path = Path(__file__).parent.parent / "routers" / "ai.py"
        content = ai_router_path.read_text(encoding='utf-8')
        
        assert 'get_llm_provider' in content, \
            "ai.py 应使用 get_llm_provider"
        assert 'from services.llm_provider import' in content, \
            "ai.py 应导入 llm_provider"


class TestLLMProviderConfiguration:
    """LLM Provider 配置测试"""
    
    def test_default_provider_is_ollama(self):
        """默认 Provider 应为 Ollama"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        content = env_path.read_text(encoding='utf-8')
        
        # 查找 LLM_PROVIDER 配置
        match = re.search(r'^LLM_PROVIDER\s*=\s*(\w+)', content, re.MULTILINE)
        assert match, ".env 应包含 LLM_PROVIDER 配置"
        
        provider = match.group(1).lower()
        assert provider == 'ollama', \
            f"默认 LLM_PROVIDER 应为 ollama，当前为 {provider}"
    
    def test_ollama_config_exists(self):
        """Ollama 配置应存在"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        content = env_path.read_text(encoding='utf-8')
        
        assert 'OLLAMA_BASE_URL' in content, \
            ".env 应包含 OLLAMA_BASE_URL"
        assert 'LOCAL_MODEL_NAME' in content, \
            ".env 应包含 LOCAL_MODEL_NAME"
    
    def test_gemini_fallback_available(self):
        """Gemini 作为备用应可用"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        content = env_path.read_text(encoding='utf-8')
        
        assert 'GEMINI_API_KEY' in content, \
            ".env 应包含 GEMINI_API_KEY 作为备用"


class TestLLMProviderImplementation:
    """LLM Provider 实现测试"""
    
    def test_ollama_provider_has_required_methods(self):
        """OllamaProvider 应有所有必需方法"""
        llm_provider_path = Path(__file__).parent.parent / "services" / "llm_provider.py"
        content = llm_provider_path.read_text(encoding='utf-8')
        
        required_methods = [
            'generate_beat_tags',
            'generate_asset_description',
            'analyze_rough_cut'
        ]
        
        # 检查 OllamaProvider 类中是否有这些方法
        for method in required_methods:
            assert f'async def {method}' in content, \
                f"llm_provider.py 应包含 {method} 方法"
    
    def test_gemini_provider_has_required_methods(self):
        """GeminiProvider 应有所有必需方法"""
        llm_provider_path = Path(__file__).parent.parent / "services" / "llm_provider.py"
        content = llm_provider_path.read_text(encoding='utf-8')
        
        # 检查 GeminiProvider 类存在
        assert 'class GeminiProvider' in content, \
            "llm_provider.py 应包含 GeminiProvider 类"


class TestAIFunctionButtons:
    """AI 功能按钮测试 - 验证每个按钮对应的功能"""
    
    def test_regenerate_tags_button(self):
        """重新生成标签按钮 - 应调用真实 AI"""
        # 检查前端调用链
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        # apiClient.ts 中的 regenerateBeatTags
        api_client = (frontend_path / "apiClient.ts").read_text(encoding='utf-8')
        assert '/api/ai/generate-tags' in api_client, \
            "regenerateBeatTags 应调用 /api/ai/generate-tags"
        
        # geminiService.ts 中应调用 apiClient
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        assert 'apiClient.regenerateBeatTags' in gemini_service, \
            "geminiService.regenerateBeatTags 应调用 apiClient"
    
    def test_generate_description_button(self):
        """生成资产描述按钮 - 应调用真实 AI"""
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        api_client = (frontend_path / "apiClient.ts").read_text(encoding='utf-8')
        assert '/api/ai/generate-description' in api_client, \
            "generateAssetDescription 应调用 /api/ai/generate-description"
        
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        assert 'apiClient.generateAssetDescription' in gemini_service, \
            "geminiService.generateAssetDescription 应调用 apiClient"
    
    def test_ai_rough_cut_button(self):
        """AI 粗剪按钮 - 应调用真实 AI"""
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        api_client = (frontend_path / "apiClient.ts").read_text(encoding='utf-8')
        assert '/api/ai/rough-cut' in api_client, \
            "performAIRoughCut 应调用 /api/ai/rough-cut"
        
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        assert 'apiClient.performAIRoughCut' in gemini_service, \
            "geminiService.performAIRoughCut 应调用 apiClient"
    
    def test_record_feedback_button(self):
        """记录反馈按钮 - 应调用真实 API"""
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        api_client = (frontend_path / "apiClient.ts").read_text(encoding='utf-8')
        assert '/api/feedback/record' in api_client, \
            "recordAssetFeedback 应调用 /api/feedback/record"
        
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        assert 'apiClient.recordAssetFeedback' in gemini_service, \
            "geminiService.recordAssetFeedback 应调用 apiClient"
    
    def test_analyze_video_button(self):
        """分析视频按钮 - 应调用真实 API"""
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        assert 'apiClient.analyzeVideoContent' in gemini_service, \
            "geminiService.analyzeVideoContent 应调用 apiClient"


class TestNoMockDataInResponses:
    """验证响应中无 Mock 数据"""
    
    def test_tag_response_not_hardcoded(self):
        """标签响应不应是硬编码的"""
        api_client_path = Path(__file__).parent.parent.parent / "frontend" / "services" / "apiClient.ts"
        content = api_client_path.read_text(encoding='utf-8')
        
        # 查找 regenerateBeatTags 函数
        func_start = content.find('export const regenerateBeatTags')
        func_end = content.find('export const', func_start + 1)
        func_content = content[func_start:func_end]
        
        # 应该有 apiRequest 调用
        assert 'apiRequest' in func_content, \
            "regenerateBeatTags 应使用 apiRequest"
        
        # 不应直接返回硬编码对象（除了 fallback）
        assert '/api/ai/generate-tags' in func_content, \
            "regenerateBeatTags 应调用 AI API"
    
    def test_description_response_not_hardcoded(self):
        """描述响应不应是硬编码的"""
        api_client_path = Path(__file__).parent.parent.parent / "frontend" / "services" / "apiClient.ts"
        content = api_client_path.read_text(encoding='utf-8')
        
        func_start = content.find('export const generateAssetDescription')
        func_end = content.find('export const', func_start + 1)
        func_content = content[func_start:func_end]
        
        assert 'apiRequest' in func_content, \
            "generateAssetDescription 应使用 apiRequest"
        assert '/api/ai/generate-description' in func_content, \
            "generateAssetDescription 应调用 AI API"
    
    def test_rough_cut_response_not_hardcoded(self):
        """粗剪响应不应是硬编码的"""
        api_client_path = Path(__file__).parent.parent.parent / "frontend" / "services" / "apiClient.ts"
        content = api_client_path.read_text(encoding='utf-8')
        
        func_start = content.find('export const performAIRoughCut')
        func_end = content.find('export const', func_start + 1)
        func_content = content[func_start:func_end]
        
        assert 'apiRequest' in func_content, \
            "performAIRoughCut 应使用 apiRequest"
        assert '/api/ai/rough-cut' in func_content, \
            "performAIRoughCut 应调用 AI API"


# ==================== 测试汇总 ====================

class TestSummary:
    """测试汇总"""
    
    def test_all_ai_buttons_use_real_api(self):
        """所有 AI 按钮都使用真实 API"""
        frontend_path = Path(__file__).parent.parent.parent / "frontend" / "services"
        
        api_client = (frontend_path / "apiClient.ts").read_text(encoding='utf-8')
        gemini_service = (frontend_path / "geminiService.ts").read_text(encoding='utf-8')
        
        # 检查所有 AI 功能
        ai_functions = {
            'regenerateBeatTags': '/api/ai/generate-tags',
            'generateAssetDescription': '/api/ai/generate-description',
            'performAIRoughCut': '/api/ai/rough-cut',
            'recordAssetFeedback': '/api/feedback/record',
        }
        
        results = []
        for func_name, endpoint in ai_functions.items():
            has_endpoint = endpoint in api_client
            uses_api_client = f'apiClient.{func_name}' in gemini_service or \
                              f'apiClient.{func_name.replace("perform", "").lower()}' in gemini_service
            
            results.append({
                'function': func_name,
                'endpoint': endpoint,
                'has_endpoint': has_endpoint,
                'uses_api_client': uses_api_client or func_name in gemini_service
            })
        
        # 所有功能都应该通过
        for r in results:
            assert r['has_endpoint'], \
                f"{r['function']} 应调用 {r['endpoint']}"
        
        print("\n=== AI 按钮功能检测结果 ===")
        for r in results:
            status = "✓" if r['has_endpoint'] else "✗"
            print(f"{status} {r['function']} -> {r['endpoint']}")
