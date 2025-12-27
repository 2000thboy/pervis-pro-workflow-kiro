# -*- coding: utf-8 -*-
"""
向量搜索功能检测脚本

检测项目：
1. Ollama 服务连接
2. 嵌入模型可用性
3. 向量生成功能
4. 搜索服务功能
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_ollama_connection():
    """测试 Ollama 服务连接"""
    print("\n" + "="*60)
    print("1. 测试 Ollama 服务连接")
    print("="*60)
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                    print(f"✅ Ollama 服务正常")
                    print(f"   已安装模型: {models}")
                    return True, models
                else:
                    print(f"❌ Ollama 服务响应异常: HTTP {resp.status}")
                    return False, []
    except Exception as e:
        print(f"❌ Ollama 服务连接失败: {e}")
        return False, []

async def test_embedding_service():
    """测试嵌入服务"""
    print("\n" + "="*60)
    print("2. 测试嵌入服务")
    print("="*60)
    
    try:
        from services.ollama_embedding import OllamaEmbeddingService, cosine_similarity
        
        service = OllamaEmbeddingService()
        available, model = await service.check_available()
        
        if not available:
            print(f"❌ 嵌入服务不可用")
            return False
        
        print(f"✅ 嵌入服务可用")
        print(f"   使用模型: {model}")
        print(f"   向量维度: {service.dimension}")
        
        # 测试嵌入生成
        test_text = "炭治郎使用水之呼吸战斗"
        print(f"\n   测试文本: '{test_text}'")
        
        embedding = await service.embed(test_text)
        if embedding:
            print(f"✅ 嵌入生成成功")
            print(f"   向量长度: {len(embedding)}")
            print(f"   向量前5维: {embedding[:5]}")
        else:
            print(f"❌ 嵌入生成失败")
            return False
        
        # 测试相似度计算
        text2 = "水之呼吸 第一型"
        text3 = "善逸使用雷之呼吸"
        
        emb2 = await service.embed(text2)
        emb3 = await service.embed(text3)
        
        if emb2 and emb3:
            sim1_2 = cosine_similarity(embedding, emb2)
            sim1_3 = cosine_similarity(embedding, emb3)
            print(f"\n   相似度测试:")
            print(f"   '{test_text}' vs '{text2}': {sim1_2:.4f}")
            print(f"   '{test_text}' vs '{text3}': {sim1_3:.4f}")
            
            if sim1_2 > sim1_3:
                print(f"✅ 相似度计算合理（水之呼吸相关文本更相似）")
            else:
                print(f"⚠️ 相似度计算可能有问题")
        
        await service.close()
        return True
        
    except Exception as e:
        print(f"❌ 嵌入服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_memory_store():
    """测试内存存储"""
    print("\n" + "="*60)
    print("3. 测试内存向量存储")
    print("="*60)
    
    try:
        from services.milvus_store import MemoryVideoStore, VideoSegment
        from services.ollama_embedding import get_embedding_service
        
        store = MemoryVideoStore()
        await store.initialize()
        print(f"✅ MemoryVideoStore 初始化成功")
        
        # 创建测试数据
        embedding_service = get_embedding_service()
        
        test_segments = [
            {
                "id": "seg_001",
                "video": "demon_slayer_ep01.mp4",
                "desc": "炭治郎使用水之呼吸第一型战斗",
                "tags": {"action_type": "FIGHT", "characters": ["炭治郎"], "mood": "EPIC"}
            },
            {
                "id": "seg_002", 
                "video": "demon_slayer_ep02.mp4",
                "desc": "善逸使用雷之呼吸霹雳一闪",
                "tags": {"action_type": "FIGHT", "characters": ["善逸"], "mood": "EPIC"}
            },
            {
                "id": "seg_003",
                "video": "demon_slayer_ep03.mp4",
                "desc": "炭治郎和弥豆子的温馨对话",
                "tags": {"action_type": "DIALOGUE", "characters": ["炭治郎", "弥豆子"], "mood": "WARM"}
            }
        ]
        
        print(f"\n   插入测试数据...")
        for seg_data in test_segments:
            embedding = await embedding_service.embed(seg_data["desc"])
            segment = VideoSegment(
                segment_id=seg_data["id"],
                video_id=seg_data["video"].replace(".mp4", ""),
                video_path=seg_data["video"],
                start_time=0,
                end_time=10,
                duration=10,
                tags=seg_data["tags"],
                embedding=embedding,
                description=seg_data["desc"]
            )
            await store.insert(segment)
            print(f"   ✅ 插入: {seg_data['id']} - {seg_data['desc'][:20]}...")
        
        count = await store.count()
        print(f"\n   存储数量: {count}")
        
        # 测试向量搜索
        print(f"\n   测试向量搜索...")
        query = "水之呼吸战斗场景"
        query_embedding = await embedding_service.embed(query)
        
        results = await store.search(query_embedding, top_k=3)
        print(f"   查询: '{query}'")
        print(f"   结果数: {len(results)}")
        for i, r in enumerate(results):
            print(f"   {i+1}. {r.segment.segment_id}: {r.segment.description[:30]}... (score: {r.score:.4f})")
        
        # 测试标签搜索
        print(f"\n   测试标签搜索...")
        tag_results = await store.search_by_tags({"action_type": "FIGHT"}, top_k=3)
        print(f"   查询标签: action_type=FIGHT")
        print(f"   结果数: {len(tag_results)}")
        for i, r in enumerate(tag_results):
            print(f"   {i+1}. {r.segment.segment_id}: {r.segment.description[:30]}... (score: {r.score:.4f})")
        
        await embedding_service.close()
        return True
        
    except Exception as e:
        print(f"❌ 内存存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_search_service():
    """测试混合搜索服务"""
    print("\n" + "="*60)
    print("4. 测试混合搜索服务")
    print("="*60)
    
    try:
        from services.search_service import HybridSearchService, SearchRequest, SearchMode
        from services.milvus_store import MemoryVideoStore, VideoSegment, set_video_store
        from services.ollama_embedding import get_embedding_service
        
        # 准备测试数据
        store = MemoryVideoStore()
        await store.initialize()
        set_video_store(store)
        
        embedding_service = get_embedding_service()
        
        test_segments = [
            {"id": "seg_001", "desc": "炭治郎使用水之呼吸第一型战斗", "tags": {"action_type": "FIGHT", "characters": ["炭治郎"]}},
            {"id": "seg_002", "desc": "善逸使用雷之呼吸霹雳一闪", "tags": {"action_type": "FIGHT", "characters": ["善逸"]}},
            {"id": "seg_003", "desc": "炭治郎和弥豆子的温馨对话", "tags": {"action_type": "DIALOGUE", "characters": ["炭治郎", "弥豆子"]}},
            {"id": "seg_004", "desc": "伊之助的搞笑场景", "tags": {"action_type": "COMEDY", "characters": ["伊之助"]}},
        ]
        
        for seg_data in test_segments:
            embedding = await embedding_service.embed(seg_data["desc"])
            segment = VideoSegment(
                segment_id=seg_data["id"],
                video_id=f"video_{seg_data['id']}",
                video_path=f"{seg_data['id']}.mp4",
                start_time=0, end_time=10, duration=10,
                tags=seg_data["tags"],
                embedding=embedding,
                description=seg_data["desc"]
            )
            await store.insert(segment)
        
        # 创建搜索服务
        search_service = HybridSearchService(video_store=store, embedding_service=embedding_service)
        await search_service.initialize()
        print(f"✅ HybridSearchService 初始化成功")
        
        # 测试各种搜索模式
        test_cases = [
            {"name": "VECTOR_ONLY", "query": "水之呼吸战斗", "tags": {}, "mode": SearchMode.VECTOR_ONLY},
            {"name": "TAG_ONLY", "query": "", "tags": {"action_type": "FIGHT"}, "mode": SearchMode.TAG_ONLY},
            {"name": "HYBRID", "query": "炭治郎战斗", "tags": {"action_type": "FIGHT"}, "mode": SearchMode.HYBRID},
        ]
        
        for tc in test_cases:
            print(f"\n   测试模式: {tc['name']}")
            request = SearchRequest(
                query=tc["query"],
                tags=tc["tags"],
                mode=tc["mode"],
                top_k=3
            )
            response = await search_service.search(request)
            print(f"   查询: '{tc['query']}' + 标签: {tc['tags']}")
            print(f"   结果数: {response.total}, 耗时: {response.search_time_ms:.2f}ms")
            for i, r in enumerate(response.results):
                print(f"   {i+1}. {r.segment_id}: score={r.score:.4f} (tag={r.tag_score:.4f}, vec={r.vector_score:.4f})")
        
        await embedding_service.close()
        return True
        
    except Exception as e:
        print(f"❌ 混合搜索服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("="*60)
    print("向量搜索功能检测")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    # 1. Ollama 连接
    success, models = await test_ollama_connection()
    results["ollama_connection"] = success
    
    if not success:
        print("\n❌ Ollama 服务未运行，无法继续测试")
        return results
    
    # 检查嵌入模型
    embedding_models = ["nomic-embed-text", "bge-m3", "mxbai-embed-large", "all-minilm"]
    has_embedding_model = any(m in models for m in embedding_models)
    
    if not has_embedding_model:
        print(f"\n⚠️ 未找到嵌入模型，请安装: ollama pull nomic-embed-text")
        results["embedding_model"] = False
        return results
    
    results["embedding_model"] = True
    
    # 2. 嵌入服务
    results["embedding_service"] = await test_embedding_service()
    
    # 3. 内存存储
    results["memory_store"] = await test_memory_store()
    
    # 4. 搜索服务
    results["search_service"] = await test_search_service()
    
    # 总结
    print("\n" + "="*60)
    print("检测结果总结")
    print("="*60)
    
    all_passed = all(results.values())
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 向量搜索功能全部正常！")
    else:
        print("⚠️ 部分功能存在问题，请检查上述错误信息")
    print("="*60)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
