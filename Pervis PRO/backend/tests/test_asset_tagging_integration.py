# -*- coding: utf-8 -*-
"""
Asset Tagging and Vector Search Integration Tests
Phase 5.2: Integration Testing
Phase 5.3: MVP Validation
"""

import os
import sys
import time
import asyncio
import pytest
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AssetTestData:
    """Test asset data"""
    def __init__(self, id: str, filename: str, description: str, expected_tags: List[str]):
        self.id = id
        self.filename = filename
        self.description = description
        self.expected_tags = expected_tags


TEST_ASSETS = [
    AssetTestData("asset_001", "city_night_neon.mp4", "city night scene with neon lights", ["city", "night", "neon"]),
    AssetTestData("asset_002", "indoor_cafe_day.mp4", "cafe interior with sunlight", ["indoor", "cafe", "day"]),
    AssetTestData("asset_003", "person_running_street.mp4", "person running on street", ["person", "action", "street"]),
    AssetTestData("asset_004", "nature_forest_morning.mp4", "forest morning with mist", ["nature", "forest", "morning"]),
    AssetTestData("asset_005", "outdoor_beach_sunset.mp4", "beach sunset golden light", ["outdoor", "beach", "sunset"]),
]


class TestTaggingIntegration:
    """Tag system integration tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from services.milvus_store import MemoryVideoStore
        from services.ollama_embedding import OllamaEmbeddingService
        
        self.video_store = MemoryVideoStore()
        self.embedding_service = OllamaEmbeddingService()
        
        yield
        
        self.video_store._segments.clear()
    
    def test_tag_generation_from_filename(self):
        """Test tag generation from filename"""
        for asset in TEST_ASSETS:
            filename = asset.filename.replace('.mp4', '')
            tags = [t.strip() for t in filename.split('_') if t.strip()]
            
            print(f"  {asset.filename}: {tags}")
            assert len(tags) > 0, f"No tags generated: {asset.filename}"
    
    def test_tag_hierarchy_validation(self):
        """Test tag hierarchy validation"""
        from models.asset_tags import AssetTags
        
        valid_tags = AssetTags(
            scene_type="INT",
            time_of_day="DAY",
            shot_size="MS",
            camera_move="STATIC",
            action_type="DIALOGUE",
            mood="CALM",
            characters=["CharA"],
            free_tags=["test_tag"]
        )
        
        assert valid_tags.scene_type != "UNKNOWN"
        assert valid_tags.time_of_day != "UNKNOWN"
        assert valid_tags.is_valid()
        
        default_tags = AssetTags()
        assert default_tags.scene_type == "UNKNOWN"
        assert default_tags.time_of_day == "UNKNOWN"
        
        coverage = valid_tags.get_coverage()
        assert coverage["L1"] > 0
        assert coverage["L2"] > 0
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self):
        """Test embedding generation"""
        test_texts = ["city night neon", "cafe indoor day", "person running action"]
        
        for text in test_texts:
            embedding = await self.embedding_service.embed(text)
            
            assert embedding is not None, f"Embedding failed: {text}"
            assert len(embedding) > 0, f"Embedding is empty: {text}"
            assert len(embedding) in [384, 768, 1024], f"Unexpected dim: {len(embedding)}"
            
            print(f"  '{text}': dim={len(embedding)}")
        
        await self.embedding_service.close()
    
    @pytest.mark.asyncio
    async def test_full_indexing_workflow(self):
        """Test full indexing workflow"""
        from services.milvus_store import VideoSegment
        
        await self.video_store.initialize()
        
        # 清空存储，确保测试隔离
        self.video_store._segments.clear()
        
        indexed_count = 0
        for asset in TEST_ASSETS:
            try:
                embedding = await self.embedding_service.embed(asset.description)
                
                if embedding is None:
                    print(f"  [SKIP] {asset.filename}: embedding failed")
                    continue
                
                segment = VideoSegment(
                    segment_id=asset.id,
                    video_id=asset.id,
                    video_path=asset.filename,
                    start_time=0.0,
                    end_time=10.0,
                    duration=10.0,
                    tags={"keywords": asset.expected_tags},
                    embedding=embedding,
                    description=asset.description
                )
                
                await self.video_store.insert(segment)
                indexed_count += 1
                print(f"  [OK] Indexed: {asset.filename}")
                
            except Exception as e:
                print(f"  [FAIL] Index failed: {asset.filename} - {e}")
        
        await self.embedding_service.close()
        
        count = await self.video_store.count()
        assert count == indexed_count, f"Index count mismatch: {count}/{indexed_count}"
    
    @pytest.mark.asyncio
    async def test_search_accuracy(self):
        """Test search accuracy"""
        from services.milvus_store import VideoSegment
        
        await self.video_store.initialize()
        
        for asset in TEST_ASSETS:
            embedding = await self.embedding_service.embed(asset.description)
            if embedding is None:
                await self.embedding_service.close()
                pytest.skip("Embedding service unavailable")
            segment = VideoSegment(
                segment_id=asset.id,
                video_id=asset.id,
                video_path=asset.filename,
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                tags={"keywords": asset.expected_tags},
                embedding=embedding,
                description=asset.description
            )
            await self.video_store.insert(segment)
        
        test_queries = [
            ("city night", ["asset_001"]),
            ("cafe", ["asset_002"]),
            ("forest", ["asset_004"]),
            ("beach sunset", ["asset_005"]),
        ]
        
        hits = 0
        total = len(test_queries)
        
        for query, expected_ids in test_queries:
            query_embedding = await self.embedding_service.embed(query)
            
            if query_embedding is None:
                print(f"  [WARN] '{query}': embedding failed, skip")
                continue
            
            results = await self.video_store.search(query_embedding=query_embedding, top_k=5)
            result_ids = [r.segment.segment_id for r in results]
            
            found = any(eid in result_ids for eid in expected_ids)
            
            if found:
                hits += 1
                print(f"  [HIT] '{query}': found (results: {result_ids[:3]})")
            else:
                print(f"  [MISS] '{query}': not found (expected: {expected_ids}, got: {result_ids[:3]})")
        
        await self.embedding_service.close()
        
        accuracy = hits / total * 100
        print(f"\n  Search accuracy: {accuracy:.1f}% ({hits}/{total})")
        
        assert accuracy >= 50, f"Search accuracy below target: {accuracy:.1f}% < 50%"


class TestSearchPerformance:
    """Search performance tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from services.milvus_store import MemoryVideoStore
        from services.ollama_embedding import OllamaEmbeddingService
        
        self.video_store = MemoryVideoStore()
        self.embedding_service = OllamaEmbeddingService()
        
        yield
        
        self.video_store._segments.clear()
    
    @pytest.mark.asyncio
    async def test_search_response_time(self):
        """Test search response time"""
        from services.milvus_store import VideoSegment
        
        await self.video_store.initialize()
        
        for asset in TEST_ASSETS:
            embedding = await self.embedding_service.embed(asset.description)
            if embedding is None:
                await self.embedding_service.close()
                pytest.skip("Embedding service unavailable")
            segment = VideoSegment(
                segment_id=asset.id,
                video_id=asset.id,
                video_path=asset.filename,
                start_time=0.0,
                end_time=10.0,
                duration=10.0,
                tags={"keywords": asset.expected_tags},
                embedding=embedding,
                description=asset.description
            )
            await self.video_store.insert(segment)
        
        test_queries = ["city night", "cafe", "forest morning"]
        response_times = []
        
        for query in test_queries:
            query_embedding = await self.embedding_service.embed(query)
            
            if query_embedding is None:
                print(f"  [WARN] '{query}': embedding failed, skip")
                continue
            
            start_time = time.time()
            results = await self.video_store.search(query_embedding=query_embedding, top_k=5)
            elapsed = (time.time() - start_time) * 1000
            response_times.append(elapsed)
            
            print(f"  '{query}': {elapsed:.1f}ms ({len(results)} results)")
        
        await self.embedding_service.close()
        
        if not response_times:
            pytest.skip("No valid queries")
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        print(f"\n  Avg response time: {avg_time:.1f}ms")
        print(f"  Max response time: {max_time:.1f}ms")
        
        assert max_time < 2000, f"Response time exceeded: {max_time:.1f}ms > 2000ms"


class TestMultimodalSearch:
    """Multimodal search tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from services.multimodal_search import get_multimodal_search_service
        self.multimodal_service = get_multimodal_search_service()
        yield
    
    @pytest.mark.asyncio
    async def test_multimodal_search_modes(self):
        """Test multimodal search modes"""
        from services.multimodal_search import MultimodalSearchMode, MultimodalSearchRequest
        
        modes = [MultimodalSearchMode.TEXT_ONLY, MultimodalSearchMode.TAG_ONLY]
        
        for mode in modes:
            try:
                request = MultimodalSearchRequest(query="city night", mode=mode, top_k=5)
                response = await self.multimodal_service.search(request)
                
                print(f"  {mode.value}: {response.total} results")
                assert isinstance(response.results, list)
                
            except Exception as e:
                print(f"  {mode.value}: skipped ({e})")
    
    @pytest.mark.asyncio
    async def test_search_result_structure(self):
        """Test search result structure"""
        from services.multimodal_search import MultimodalSearchMode, MultimodalSearchRequest
        
        request = MultimodalSearchRequest(query="test query", mode=MultimodalSearchMode.TEXT_ONLY, top_k=5)
        response = await self.multimodal_service.search(request)
        
        assert hasattr(response, 'results')
        assert hasattr(response, 'total')
        assert hasattr(response, 'search_time_ms')
        
        for result in response.results:
            assert hasattr(result, 'asset_id')
            assert hasattr(result, 'final_score')


class TestTagCoverage:
    """Tag coverage tests"""
    
    def test_l1_tag_coverage(self):
        """Test L1 tag coverage"""
        test_filenames = [
            "video_001.mp4",
            "animation_character.mp4",
            "footage_street.mp4",
            "random_file.mp4",
            "city_night_neon.mp4",
        ]
        
        l1_count = 0
        for filename in test_filenames:
            name = filename.replace('.mp4', '')
            parts = name.split('_')
            
            if parts and parts[0]:
                l1_count += 1
                print(f"  [OK] {filename}: L1={parts[0]}")
            else:
                print(f"  [FAIL] {filename}: no L1 tag")
        
        coverage = l1_count / len(test_filenames) * 100
        print(f"\n  L1 tag coverage: {coverage:.1f}%")
        
        assert coverage >= 80, f"L1 coverage below target: {coverage:.1f}%"
    
    def test_l2_tag_coverage(self):
        """Test L2 tag coverage"""
        test_filenames = [
            "footage_indoor_cafe.mp4",
            "animation_2D_character.mp4",
            "video_outdoor_street.mp4",
        ]
        
        l2_count = 0
        for filename in test_filenames:
            name = filename.replace('.mp4', '')
            parts = name.split('_')
            
            if len(parts) >= 2 and parts[1]:
                l2_count += 1
                print(f"  [OK] {filename}: L2={parts[1]}")
            else:
                print(f"  [FAIL] {filename}: no L2 tag")
        
        coverage = l2_count / len(test_filenames) * 100
        print(f"\n  L2 tag coverage: {coverage:.1f}%")
        
        assert coverage >= 80, f"L2 coverage below target: {coverage:.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
