# -*- coding: utf-8 -*-
"""
P1: 增强版渲染服务测试
测试多格式、多分辨率、多帧率支持
"""

import os
import sys
import pytest
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRenderServiceEnhanced:
    """增强版渲染服务测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        from database import SessionLocal, init_database
        init_database()
        self.db = SessionLocal()
        
        yield
        
        self.db.close()
    
    def test_service_initialization(self):
        """测试服务初始化"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        
        assert service is not None
        assert service.output_dir.exists()
        assert service.temp_dir.exists()
        
        print(f"\n  ✅ 服务初始化成功")
    
    def test_supported_formats(self):
        """测试支持的格式"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        formats = service.get_supported_formats()
        
        assert len(formats) >= 3
        format_values = [f['value'] for f in formats]
        assert 'mp4' in format_values
        assert 'mov' in format_values
        assert 'webm' in format_values
        
        print(f"\n  ✅ 支持 {len(formats)} 种格式: {format_values}")
    
    def test_supported_resolutions(self):
        """测试支持的分辨率"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        resolutions = service.get_supported_resolutions()
        
        assert len(resolutions) >= 4
        res_values = [r['value'] for r in resolutions]
        assert '720p' in res_values
        assert '1080p' in res_values
        assert '2k' in res_values
        assert '4k' in res_values
        
        print(f"\n  ✅ 支持 {len(resolutions)} 种分辨率: {res_values}")
    
    def test_supported_framerates(self):
        """测试支持的帧率"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        framerates = service.get_supported_framerates()
        
        assert len(framerates) >= 5
        assert 24 in framerates
        assert 30 in framerates
        assert 60 in framerates
        
        print(f"\n  ✅ 支持 {len(framerates)} 种帧率: {framerates}")
    
    def test_quality_presets(self):
        """测试质量预设"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        presets = service.get_quality_presets()
        
        assert len(presets) >= 4
        preset_values = [p['value'] for p in presets]
        assert 'low' in preset_values
        assert 'medium' in preset_values
        assert 'high' in preset_values
        assert 'ultra' in preset_values
        
        print(f"\n  ✅ 支持 {len(presets)} 种质量预设: {preset_values}")
    
    def test_render_options_dataclass(self):
        """测试渲染选项数据类"""
        from services.render_service_enhanced import (
            RenderOptions, VideoFormat, Resolution, Quality
        )
        
        # 默认选项
        default_options = RenderOptions()
        assert default_options.format == VideoFormat.MP4
        assert default_options.resolution == Resolution.FHD_1080
        assert default_options.quality == Quality.HIGH
        assert default_options.framerate == 30.0
        
        # 自定义选项
        custom_options = RenderOptions(
            format=VideoFormat.MOV,
            resolution=Resolution.UHD_4K,
            quality=Quality.ULTRA,
            framerate=24.0,
            custom_bitrate=20000,
            audio_bitrate=320
        )
        assert custom_options.format == VideoFormat.MOV
        assert custom_options.resolution == Resolution.UHD_4K
        assert custom_options.custom_bitrate == 20000
        
        print(f"\n  ✅ 渲染选项数据类正常")
    
    def test_resolution_configs(self):
        """测试分辨率配置"""
        from services.render_service_enhanced import RESOLUTION_CONFIGS, Resolution
        
        # 720p
        config_720 = RESOLUTION_CONFIGS[Resolution.HD_720]
        assert config_720.width == 1280
        assert config_720.height == 720
        
        # 1080p
        config_1080 = RESOLUTION_CONFIGS[Resolution.FHD_1080]
        assert config_1080.width == 1920
        assert config_1080.height == 1080
        
        # 4K
        config_4k = RESOLUTION_CONFIGS[Resolution.UHD_4K]
        assert config_4k.width == 3840
        assert config_4k.height == 2160
        
        print(f"\n  ✅ 分辨率配置正确")
    
    def test_quality_presets_config(self):
        """测试质量预设配置"""
        from services.render_service_enhanced import QUALITY_PRESETS, Quality
        
        # Low
        low = QUALITY_PRESETS[Quality.LOW]
        assert low.crf == 28
        assert low.preset == "fast"
        
        # High
        high = QUALITY_PRESETS[Quality.HIGH]
        assert high.crf == 18
        assert high.preset == "slow"
        
        # Ultra
        ultra = QUALITY_PRESETS[Quality.ULTRA]
        assert ultra.crf == 15
        assert ultra.preset == "slower"
        
        print(f"\n  ✅ 质量预设配置正确")
    
    def test_format_codecs(self):
        """测试格式编解码器配置"""
        from services.render_service_enhanced import FORMAT_CODECS, VideoFormat
        
        # MP4
        mp4 = FORMAT_CODECS[VideoFormat.MP4]
        assert mp4['video'] == 'libx264'
        assert mp4['audio'] == 'aac'
        assert mp4['ext'] == 'mp4'
        
        # WebM
        webm = FORMAT_CODECS[VideoFormat.WEBM]
        assert webm['video'] == 'libvpx-vp9'
        assert webm['audio'] == 'libopus'
        assert webm['ext'] == 'webm'
        
        print(f"\n  ✅ 格式编解码器配置正确")
    
    @pytest.mark.asyncio
    async def test_check_render_requirements_no_timeline(self):
        """测试渲染检查 - 时间轴不存在"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        
        result = await service.check_render_requirements("non_existent_timeline")
        
        assert result['can_render'] == False
        assert len(result['errors']) > 0
        
        print(f"\n  ✅ 正确检测到时间轴不存在")
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self):
        """测试列出任务 - 空列表"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        
        tasks = await service.list_tasks(limit=10)
        
        assert isinstance(tasks, list)
        
        print(f"\n  ✅ 任务列表查询正常，当前 {len(tasks)} 个任务")
    
    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self):
        """测试获取任务状态 - 任务不存在"""
        from services.render_service_enhanced import get_enhanced_render_service
        
        service = get_enhanced_render_service(self.db)
        
        status = await service.get_task_status("non_existent_task")
        
        assert status is None
        
        print(f"\n  ✅ 正确处理不存在的任务")


class TestRenderServiceEnhancedIntegration:
    """增强版渲染服务集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        from database import SessionLocal, init_database
        init_database()
        self.db = SessionLocal()
        
        yield
        
        self.db.close()
    
    def test_export_router_config_endpoint(self):
        """测试导出路由配置端点"""
        # 验证路由模块可以导入
        from routers.export import router
        
        # 检查路由是否包含配置端点
        routes = [r.path for r in router.routes]
        
        assert '/timeline/video/config' in routes or any('config' in r for r in routes)
        
        print(f"\n  ✅ 导出路由配置端点存在")
    
    def test_render_service_backward_compatible(self):
        """测试渲染服务向后兼容"""
        # 原版服务
        from services.render_service import RenderService
        old_service = RenderService(self.db)
        
        assert hasattr(old_service, 'start_render')
        assert hasattr(old_service, 'get_task_status')
        assert hasattr(old_service, 'cancel_render')
        
        # 增强版服务
        from services.render_service_enhanced import get_enhanced_render_service
        new_service = get_enhanced_render_service(self.db)
        
        assert hasattr(new_service, 'start_render')
        assert hasattr(new_service, 'get_task_status')
        assert hasattr(new_service, 'cancel_render')
        
        print(f"\n  ✅ 渲染服务向后兼容")


def run_render_tests():
    """运行渲染服务测试"""
    print("\n" + "="*60)
    print("P1: 增强版渲染服务测试")
    print("="*60)
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_render_tests()
