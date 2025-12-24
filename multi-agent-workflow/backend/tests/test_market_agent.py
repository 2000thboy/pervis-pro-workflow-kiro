# -*- coding: utf-8 -*-
import pytest
import pytest_asyncio

from app.agents.market_agent import (
    MarketAgent,
    MovieReference,
    TagMatchResult,
    LLMProvider,
    MatchType,
)
from app.core.message_bus import MessageBus


class TestMarketAgentInit:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def market_agent(self, message_bus):
        agent = MarketAgent(
            agent_id="test_market_agent",
            message_bus=message_bus,
            config={"llm_provider": "ollama"}
        )
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_agent_creation(self, message_bus):
        agent = MarketAgent(agent_id="test_agent", message_bus=message_bus)
        assert agent.agent_id == "test_agent"
        assert "llm_analysis" in agent.capabilities
    
    @pytest.mark.asyncio
    async def test_agent_running(self, market_agent):
        assert market_agent.is_running
        assert market_agent.work_state.value == "idle"


class TestMovieReference:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def market_agent(self, message_bus):
        agent = MarketAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_add_movie(self, market_agent):
        movie = await market_agent.add_movie_reference(
            movie_id="test_movie",
            title="Test Movie",
            tags=["action", "scifi"],
            year=2023,
            rating=8.5
        )
        assert movie.id == "test_movie"
        assert movie.title == "Test Movie"
        assert "action" in movie.tags
    
    @pytest.mark.asyncio
    async def test_get_movie(self, market_agent):
        await market_agent.add_movie_reference(
            movie_id="movie_1",
            title="Movie One",
            tags=["drama"],
            year=2020,
            rating=9.0
        )
        movie = await market_agent.get_movie("movie_1")
        assert movie is not None
        assert movie.title == "Movie One"
    
    @pytest.mark.asyncio
    async def test_list_movies(self, market_agent):
        await market_agent.add_movie_reference(
            movie_id="m1", title="M1", tags=["a"], year=2020, rating=8.0
        )
        await market_agent.add_movie_reference(
            movie_id="m2", title="M2", tags=["b"], year=2021, rating=9.0
        )
        movies = await market_agent.list_movies(limit=10)
        assert len(movies) == 2


class TestTagMatching:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def market_agent_with_movies(self, message_bus):
        agent = MarketAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        await agent.add_movie_reference(
            movie_id="m1", title="Inception",
            tags=["scifi", "action", "thriller"], year=2010, rating=9.3
        )
        await agent.add_movie_reference(
            movie_id="m2", title="Titanic",
            tags=["romance", "drama"], year=1997, rating=9.4
        )
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_match_by_tags(self, market_agent_with_movies):
        results = await market_agent_with_movies.match_by_tags(
            query_tags=["scifi", "action"],
            min_score=0.2
        )
        assert len(results) > 0
        assert results[0].matched_movie.title == "Inception"
    
    @pytest.mark.asyncio
    async def test_match_empty_tags(self, market_agent_with_movies):
        results = await market_agent_with_movies.match_by_tags(
            query_tags=[],
            min_score=0.0
        )
        assert len(results) == 0


class TestLLMAnalysis:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def market_agent(self, message_bus):
        agent = MarketAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_llm_analysis(self, market_agent):
        result = await market_agent.analyze_with_llm(query="A scifi movie")
        assert result.provider == LLMProvider.OLLAMA
        assert result.latency_ms >= 0
    
    @pytest.mark.asyncio
    async def test_custom_llm_handler(self, market_agent):
        async def mock_handler(prompt, provider):
            return {"response": "Mock", "tags": ["scifi"], "genres": [], "tokens": 10}
        
        market_agent.set_llm_handler(mock_handler)
        result = await market_agent.analyze_with_llm(query="test")
        assert result.response == "Mock"
        assert result.suggested_tags == ["scifi"]


class TestStatistics:
    
    @pytest_asyncio.fixture
    async def message_bus(self):
        bus = MessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest_asyncio.fixture
    async def market_agent(self, message_bus):
        agent = MarketAgent(agent_id="test_agent", message_bus=message_bus)
        await agent.initialize()
        await agent.start()
        await agent.add_movie_reference(
            movie_id="m1", title="Test", tags=["a"], year=2020, rating=8.0
        )
        yield agent
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, market_agent):
        stats = market_agent.get_statistics()
        assert stats["movies_count"] == 1
        assert "llm_cache_count" in stats
        assert stats["default_llm_provider"] == "ollama"
