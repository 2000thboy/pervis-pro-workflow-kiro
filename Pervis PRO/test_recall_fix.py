# -*- coding: utf-8 -*-
"""
测试素材召回修复

验证 MemoryVideoStore 能够正确加载缓存数据，
并且 Storyboard_Agent 能够成功召回素材。
"""

import asyncio
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


async def test_video_store_loading():
    """测试视频存储加载缓存"""
    print("\n" + "="*60)
    print("测试 1: MemoryVideoStore 缓存加载")
    print("="*60)
    
    from services.milvus_store import MemoryVideoStore, get_video_store
    
    # 创建新实例
    store = MemoryVideoStore()
    await store.initialize()
    
    count = await store.count()
    print(f"✅ 加载素材数量: {count}")
    
    # 统计有嵌入向量的素材
    embedded_count = sum(1 for s in store._segments.values() if s.embedding)
    print(f"✅ 有嵌入向量的素材: {embedded_count}")
    
    if count > 0:
        # 显示前 3 个素材
        print("\n前 3 个素材:")
        for i, (seg_id, segment) in enumerate(list(store._segments.items())[:3]):
            print(f"  [{i+1}] {seg_id}: {segment.tags.get('summary', 'N/A')[:30]}...")
            print(f"      路径: {segment.video_path[:50]}...")
            print(f"      标签: action={segment.tags.get('action_type')}, source={segment.tags.get('source_work')}")
            print(f"      嵌入: {'有' if segment.embedding else '无'}")
    
    return count > 0


async def test_tag_search():
    """测试标签搜索"""
    print("\n" + "="*60)
    print("测试 2: 标签搜索")
    print("="*60)
    
    from services.milvus_store import get_video_store
    
    store = get_video_store()
    await store.initialize()
    
    # 搜索战斗场景
    results = await store.search_by_tags({"action_type": "FIGHT"}, top_k=5)
    
    print(f"搜索 action_type=FIGHT，找到 {len(results)} 个结果:")
    for i, r in enumerate(results):
        print(f"  [{i+1}] score={r.score:.2f} - {r.segment.tags.get('summary', 'N/A')[:40]}")
    
    return len(results) > 0


async def test_vector_search():
    """测试向量搜索"""
    print("\n" + "="*60)
    print("测试 3: 向量搜索")
    print("="*60)
    
    from services.milvus_store import get_video_store
    from services.ollama_embedding import get_embedding_service
    
    store = get_video_store()
    await store.initialize()
    
    # 获取嵌入服务
    embedding_service = get_embedding_service()
    available, model = await embedding_service.check_available()
    
    if not available:
        print("⚠️ 嵌入服务不可用，跳过向量搜索测试")
        return True  # 不算失败
    
    print(f"嵌入模型: {model}")
    
    # 生成查询向量
    query = "战斗打斗场景"
    query_embedding = await embedding_service.embed(query)
    
    if not query_embedding:
        print("⚠️ 生成查询向量失败")
        return False
    
    print(f"查询: '{query}'")
    print(f"向量维度: {len(query_embedding)}")
    
    # 向量搜索
    results = await store.search(query_embedding, top_k=5)
    
    print(f"找到 {len(results)} 个结果:")
    for i, r in enumerate(results):
        print(f"  [{i+1}] score={r.score:.3f} - {r.segment.tags.get('summary', 'N/A')[:40]}")
    
    return len(results) > 0


async def test_storyboard_recall():
    """测试 Storyboard_Agent 素材召回"""
    print("\n" + "="*60)
    print("测试 4: Storyboard_Agent 素材召回")
    print("="*60)
    
    from services.agents.storyboard_agent import get_storyboard_agent_service
    
    agent = get_storyboard_agent_service()
    
    # 测试召回
    result = await agent.recall_assets(
        scene_id="test_scene_001",
        query="战斗场景",
        tags={"action_type": "FIGHT"},
        strategy="tag_only"
    )
    
    print(f"召回结果:")
    print(f"  场次ID: {result.scene_id}")
    print(f"  候选数量: {len(result.candidates)}")
    print(f"  总搜索数: {result.total_searched}")
    print(f"  有匹配: {result.has_match}")
    
    if result.candidates:
        print("\n候选素材:")
        for c in result.candidates:
            print(f"  [{c.rank}] {c.asset_id}: score={c.score:.2f}")
            print(f"      路径: {c.asset_path[:50]}...")
            print(f"      原因: {c.match_reason}")
    else:
        print(f"  占位消息: {result.placeholder_message}")
    
    return result.has_match


async def main():
    print("\n" + "="*60)
    print("素材召回修复验证测试")
    print("="*60)
    
    results = []
    
    # 测试 1: 缓存加载
    try:
        r1 = await test_video_store_loading()
        results.append(("缓存加载", r1))
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}")
        results.append(("缓存加载", False))
    
    # 测试 2: 标签搜索
    try:
        r2 = await test_tag_search()
        results.append(("标签搜索", r2))
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}")
        results.append(("标签搜索", False))
    
    # 测试 3: 向量搜索
    try:
        r3 = await test_vector_search()
        results.append(("向量搜索", r3))
    except Exception as e:
        print(f"❌ 测试 3 失败: {e}")
        results.append(("向量搜索", False))
    
    # 测试 4: Storyboard_Agent 召回
    try:
        r4 = await test_storyboard_recall()
        results.append(("Storyboard召回", r4))
    except Exception as e:
        print(f"❌ 测试 4 失败: {e}")
        results.append(("Storyboard召回", False))
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    passed = 0
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    if passed == len(results):
        print("\n🎉 素材召回修复成功！")
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
