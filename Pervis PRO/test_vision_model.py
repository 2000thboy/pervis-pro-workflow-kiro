# -*- coding: utf-8 -*-
"""
测试 Ollama 视觉模型

用法: py test_vision_model.py [图片路径]
如果不提供图片路径，会使用测试图片
"""
import asyncio
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
load_dotenv()


async def test_vision():
    from services.ollama_vision import get_vision_provider, VisionConfig
    
    print("=" * 50)
    print("Ollama 视觉模型测试")
    print("=" * 50)
    
    # 显示配置
    config = VisionConfig()
    print(f"\n配置信息:")
    print(f"  Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"  视觉模型: {config.VISION_MODEL}")
    print(f"  超时时间: {config.TIMEOUT}s")
    print(f"  启用状态: {config.ENABLED}")
    
    # 获取 provider
    provider = get_vision_provider()
    
    # 检查可用性
    print(f"\n检查模型可用性...")
    is_available = await provider.check_availability()
    
    if not is_available:
        print("❌ 视觉模型不可用!")
        print("\n可能的原因:")
        print("  1. Ollama 服务未运行")
        print("  2. 视觉模型未安装 (运行: ollama pull llava-llama3)")
        return False
    
    print("✅ 视觉模型可用!")
    
    # 测试图片分析
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if image_path and os.path.exists(image_path):
        print(f"\n分析图片: {image_path}")
        print("处理中... (可能需要 5-15 秒)")
        
        import time
        start = time.time()
        result = await provider.analyze_image(image_path)
        elapsed = time.time() - start
        
        print(f"\n分析结果 (耗时 {elapsed:.1f}s):")
        print("-" * 40)
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        return True
    else:
        print("\n未提供测试图片，跳过图片分析测试")
        print("用法: py test_vision_model.py <图片路径>")
        return True


async def test_video_preprocessor():
    """测试视频预处理器集成"""
    print("\n" + "=" * 50)
    print("视频预处理器集成测试")
    print("=" * 50)
    
    from services.video_preprocessor import VideoPreprocessor
    
    preprocessor = VideoPreprocessor()
    print("✅ VideoPreprocessor 初始化成功")
    print("   现在支持本地视觉模型进行标签生成")


if __name__ == "__main__":
    print("\n🎬 Pervis PRO 视觉模型测试\n")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_vision())
        loop.run_until_complete(test_video_preprocessor())
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 测试完成!")
        else:
            print("⚠️ 部分测试未通过")
        print("=" * 50)
    finally:
        loop.close()
