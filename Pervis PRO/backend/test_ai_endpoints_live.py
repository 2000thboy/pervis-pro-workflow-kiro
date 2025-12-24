"""
AI 端点实时测试脚本
测试所有 AI 功能并显示实际返回数据
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8000"

async def check_ollama_status():
    """检查 Ollama 服务状态"""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"\n{'='*60}")
    print("1. 检查 Ollama 服务状态")
    print(f"{'='*60}")
    print(f"Ollama URL: {ollama_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 检查 Ollama 是否运行
            async with session.get(f"{ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name", "unknown") for m in data.get("models", [])]
                    print(f"✅ Ollama 服务运行中")
                    print(f"   可用模型: {models}")
                    return True
                else:
                    print(f"❌ Ollama 响应异常: {resp.status}")
                    return False
    except aiohttp.ClientError as e:
        print(f"❌ 无法连接到 Ollama: {e}")
        print(f"   请确保 Ollama 已启动: ollama serve")
        return False
    except Exception as e:
        print(f"❌ 检查 Ollama 时出错: {e}")
        return False


async def check_backend_status():
    """检查后端服务状态"""
    print(f"\n{'='*60}")
    print("2. 检查后端服务状态")
    print(f"{'='*60}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ 后端服务运行中")
                    print(f"   状态: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return True
                else:
                    print(f"❌ 后端响应异常: {resp.status}")
                    return False
    except aiohttp.ClientError as e:
        print(f"❌ 无法连接到后端: {e}")
        print(f"   请启动后端: cd backend && py -m uvicorn main:app --reload")
        return False


async def check_ai_health():
    """检查 AI 服务健康状态"""
    print(f"\n{'='*60}")
    print("3. 检查 AI 服务健康状态")
    print(f"{'='*60}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/api/ai/health", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                print(f"AI 健康检查结果:")
                print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
                return data.get("status") == "healthy"
    except Exception as e:
        print(f"❌ AI 健康检查失败: {e}")
        return False


async def test_generate_tags():
    """测试标签生成 API"""
    print(f"\n{'='*60}")
    print("4. 测试标签生成 API (/api/ai/generate-tags)")
    print(f"{'='*60}")
    
    test_content = """
    内景 - 办公室 - 白天
    
    张明坐在电脑前，眉头紧锁。他的手指在键盘上飞快地敲击着。
    突然，他停下来，看着屏幕上的数据，脸上露出惊讶的表情。
    
    张明：（自言自语）这不可能...
    """
    
    print(f"测试内容: {test_content[:100]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/ai/generate-tags",
                json={"content": test_content},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                print(f"\n响应状态码: {resp.status}")
                print(f"返回数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get("status") == "success":
                    print(f"\n✅ 标签生成成功!")
                    return True
                else:
                    print(f"\n❌ 标签生成失败: {data.get('message')}")
                    return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


async def test_generate_description():
    """测试资产描述生成 API"""
    print(f"\n{'='*60}")
    print("5. 测试资产描述生成 API (/api/ai/generate-description)")
    print(f"{'='*60}")
    
    test_data = {
        "asset_id": "test-asset-001",
        "filename": "sunset_beach_drone_4k.mp4",
        "metadata": {
            "duration": 30,
            "resolution": "3840x2160",
            "fps": 24
        }
    }
    
    print(f"测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/ai/generate-description",
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                print(f"\n响应状态码: {resp.status}")
                print(f"返回数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get("status") == "success":
                    print(f"\n✅ 描述生成成功!")
                    return True
                else:
                    print(f"\n❌ 描述生成失败")
                    return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


async def test_rough_cut():
    """测试 AI 粗剪 API"""
    print(f"\n{'='*60}")
    print("6. 测试 AI 粗剪 API (/api/ai/rough-cut)")
    print(f"{'='*60}")
    
    test_data = {
        "script_content": "一个年轻人在城市街头奔跑，追逐着什么。镜头跟随他穿过人群，最后他停在一个十字路口，喘着气。",
        "video_tags": {
            "globalTags": {
                "actions": ["running", "chasing"],
                "scenes": ["urban", "street"],
                "emotions": ["tense", "urgent"]
            },
            "timeLog": [
                {"time": 0, "description": "开场", "tags": ["establishing"]},
                {"time": 5, "description": "奔跑开始", "tags": ["action"]},
                {"time": 15, "description": "穿过人群", "tags": ["crowd"]},
                {"time": 25, "description": "停下", "tags": ["pause"]}
            ],
            "assetTrustScore": 0.8
        }
    }
    
    print(f"测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)[:300]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/api/ai/rough-cut",
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                print(f"\n响应状态码: {resp.status}")
                print(f"返回数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get("status") == "success":
                    print(f"\n✅ 粗剪分析成功!")
                    print(f"   入点: {data.get('inPoint')}s")
                    print(f"   出点: {data.get('outPoint')}s")
                    print(f"   置信度: {data.get('confidence')}")
                    print(f"   理由: {data.get('reason')}")
                    return True
                else:
                    print(f"\n❌ 粗剪分析失败: {data.get('message')}")
                    return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("   Pervis PRO AI 端点实时测试")
    print("="*60)
    
    # 显示当前配置
    print(f"\n当前配置:")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'gemini')}")
    print(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
    print(f"  LOCAL_MODEL_NAME: {os.getenv('LOCAL_MODEL_NAME', 'qwen2.5:14b')}")
    print(f"  GEMINI_API_KEY: {'已配置' if os.getenv('GEMINI_API_KEY') else '未配置'}")
    
    results = {}
    
    # 1. 检查 Ollama
    results["ollama"] = await check_ollama_status()
    
    # 2. 检查后端
    results["backend"] = await check_backend_status()
    
    if not results["backend"]:
        print("\n❌ 后端服务未运行，无法继续测试")
        print("   请先启动后端: cd backend && py -m uvicorn main:app --reload")
        return
    
    # 3. 检查 AI 健康
    results["ai_health"] = await check_ai_health()
    
    # 4. 测试标签生成
    results["generate_tags"] = await test_generate_tags()
    
    # 5. 测试描述生成
    results["generate_description"] = await test_generate_description()
    
    # 6. 测试粗剪
    results["rough_cut"] = await test_rough_cut()
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("   测试结果汇总")
    print(f"{'='*60}")
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！AI 功能正常工作。")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息。")


if __name__ == "__main__":
    asyncio.run(main())
