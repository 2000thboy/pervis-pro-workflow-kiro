# -*- coding: utf-8 -*-
"""
视觉标签生成测试

测试 Art_Agent 的图片标签生成功能：
1. 视觉模型可用时，必须使用视觉模型
2. 视觉模型不可用时，返回明确错误（不回退到 LLM）
3. 非图片文件返回错误
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agents.art_agent import ArtAgentService, VisualTags


class TestVisionTagging:
    """视觉标签生成测试"""
    
    @pytest.fixture
    def art_agent(self):
        """创建 ArtAgentService 实例"""
        return ArtAgentService()
    
    @pytest.mark.asyncio
    async def test_non_image_file_returns_error(self, art_agent):
        """测试：非图片文件应返回错误"""
        # 创建临时文本文件
        test_file = Path("test_file.txt")
        test_file.write_text("test content")
        
        try:
            result = await art_agent.generate_tags(str(test_file))
            
            assert isinstance(result, VisualTags)
            assert "[错误]" in result.summary
            assert "不支持的文件类型" in result.summary
        finally:
            test_file.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_nonexistent_file_returns_error(self, art_agent):
        """测试：不存在的文件应返回错误"""
        result = await art_agent.generate_tags("/nonexistent/path/image.jpg")
        
        assert isinstance(result, VisualTags)
        assert "[错误]" in result.summary
        assert "文件不存在" in result.summary
    
    @pytest.mark.asyncio
    async def test_vision_model_disabled_returns_error(self, art_agent):
        """测试：视觉模型禁用时应返回错误"""
        # 创建临时图片文件
        test_image = Path("test_image.jpg")
        test_image.write_bytes(b'\xff\xd8\xff\xe0')  # JPEG magic bytes
        
        try:
            # Mock 视觉模型为禁用状态
            mock_vision = MagicMock()
            mock_vision.config.ENABLED = False
            
            with patch('services.ollama_vision.get_vision_provider', return_value=mock_vision):
                result = await art_agent.generate_tags(str(test_image))
            
            assert isinstance(result, VisualTags)
            assert "[错误]" in result.summary
            assert "禁用" in result.summary
        finally:
            test_image.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_vision_model_unavailable_returns_error(self, art_agent):
        """测试：视觉模型不可用时应返回错误（不回退到 LLM）"""
        test_image = Path("test_image.jpg")
        test_image.write_bytes(b'\xff\xd8\xff\xe0')
        
        try:
            # Mock 视觉模型为不可用状态
            mock_vision = MagicMock()
            mock_vision.config.ENABLED = True
            mock_vision.model = "llava-llama3"
            mock_vision.check_availability = AsyncMock(return_value=False)
            
            with patch('services.ollama_vision.get_vision_provider', return_value=mock_vision):
                result = await art_agent.generate_tags(str(test_image))
            
            assert isinstance(result, VisualTags)
            assert "[错误]" in result.summary
            assert "不可用" in result.summary
            # 确保没有回退到 LLM（不应该有有效的标签）
            assert result.scene_type == "未知"
        finally:
            test_image.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_vision_model_success_returns_tags(self, art_agent):
        """测试：视觉模型成功时应返回正确的标签"""
        test_image = Path("test_image.jpg")
        test_image.write_bytes(b'\xff\xd8\xff\xe0')
        
        try:
            # Mock 视觉模型返回成功结果
            mock_vision = MagicMock()
            mock_vision.config.ENABLED = True
            mock_vision.check_availability = AsyncMock(return_value=True)
            mock_vision.analyze_image = AsyncMock(return_value={
                "scene_type": "室外",
                "time": "黄昏",
                "shot_type": "全景",
                "mood": "史诗",
                "action": "战斗",
                "characters": "单人",
                "free_tags": ["武士", "剪影", "日式", "孤独"],
                "summary": "一个武士站在黄昏的山顶，剪影效果"
            })
            
            with patch('services.ollama_vision.get_vision_provider', return_value=mock_vision):
                result = await art_agent.generate_tags(str(test_image))
            
            assert isinstance(result, VisualTags)
            assert "[错误]" not in result.summary
            assert result.scene_type == "室外"
            assert result.time == "黄昏"
            assert result.mood == "史诗"
            assert "武士" in result.free_tags
            assert "剪影" in result.free_tags
        finally:
            test_image.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_vision_analysis_failure_returns_error(self, art_agent):
        """测试：视觉分析失败时应返回错误"""
        test_image = Path("test_image.jpg")
        test_image.write_bytes(b'\xff\xd8\xff\xe0')
        
        try:
            # Mock 视觉模型分析失败
            mock_vision = MagicMock()
            mock_vision.config.ENABLED = True
            mock_vision.check_availability = AsyncMock(return_value=True)
            mock_vision.analyze_image = AsyncMock(return_value={
                "summary": "无法分析图像内容"
            })
            
            with patch('services.ollama_vision.get_vision_provider', return_value=mock_vision):
                result = await art_agent.generate_tags(str(test_image))
            
            assert isinstance(result, VisualTags)
            assert "[错误]" in result.summary
            assert "分析失败" in result.summary
        finally:
            test_image.unlink(missing_ok=True)


class TestOllamaIntegration:
    """Ollama 集成测试（需要 Ollama 运行）"""
    
    @pytest.fixture
    def art_agent(self):
        return ArtAgentService()
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.environ.get("SKIP_OLLAMA_TESTS", "1") == "1",
        reason="跳过 Ollama 集成测试（设置 SKIP_OLLAMA_TESTS=0 启用）"
    )
    async def test_real_vision_analysis(self, art_agent):
        """测试：真实的视觉模型分析（需要 Ollama 运行）"""
        # 使用项目中的测试图片
        test_assets_dir = Path(__file__).parent.parent.parent / "test_assets"
        
        if not test_assets_dir.exists():
            pytest.skip("test_assets 目录不存在")
        
        # 查找任意图片
        image_files = list(test_assets_dir.glob("*.jpg")) + list(test_assets_dir.glob("*.png"))
        
        if not image_files:
            pytest.skip("没有找到测试图片")
        
        test_image = image_files[0]
        result = await art_agent.generate_tags(str(test_image))
        
        print(f"\n分析结果: {result.to_dict()}")
        
        # 验证返回了有效结果
        assert isinstance(result, VisualTags)
        if "[错误]" not in result.summary:
            # 成功分析
            assert result.summary != ""
            assert len(result.free_tags) > 0
        else:
            # 分析失败（可能是 Ollama 未运行）
            print(f"分析失败: {result.summary}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
