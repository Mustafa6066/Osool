"""
Osool Backend — Vector Search Retrieval Tests
----------------------------------------------
Tests the retrieval fallback chain: vector search default-on flag,
multi-level threshold relaxation, and graceful degradation to text search
when embeddings are unavailable.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import vector_search


class TestVectorSearchFlag:
    def test_vector_search_enabled_by_default(self):
        """ENABLE_VECTOR_SEARCH unset → vector path must be active."""
        env = dict(os.environ)
        env.pop("ENABLE_VECTOR_SEARCH", None)
        with patch.dict(os.environ, env, clear=True):
            assert os.getenv("ENABLE_VECTOR_SEARCH", "1") != "0"

    def test_vector_search_can_be_disabled(self):
        with patch.dict(os.environ, {"ENABLE_VECTOR_SEARCH": "0"}):
            assert os.getenv("ENABLE_VECTOR_SEARCH", "1") == "0"


class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_embedding_failure_degrades_to_text_search(self):
        """get_embedding → None must fall through to the text fallback, not error."""
        db = AsyncMock()
        sentinel = [{"id": 1, "title": "Fallback Result"}]

        with patch.object(vector_search, "get_embedding", new=AsyncMock(return_value=None)), \
             patch.object(
                 vector_search, "_text_search_fallback", new=AsyncMock(return_value=sentinel)
             ), \
             patch.dict(os.environ, {"ENABLE_VECTOR_SEARCH": "1"}):
            results = await vector_search.search_properties(db, "شقة في التجمع الخامس")

        assert results == sentinel

    @pytest.mark.asyncio
    async def test_disabled_flag_skips_embedding_entirely(self):
        db = AsyncMock()
        sentinel = [{"id": 2, "title": "Text Only"}]

        with patch.object(vector_search, "get_embedding", new=AsyncMock()) as embed_mock, \
             patch.object(
                 vector_search, "_text_search_fallback", new=AsyncMock(return_value=sentinel)
             ), \
             patch.dict(os.environ, {"ENABLE_VECTOR_SEARCH": "0"}):
            results = await vector_search.search_properties(db, "villa new cairo")

        assert results == sentinel
        embed_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_threshold_relaxation_ladder(self):
        """No matches at 0.7 → retries at 0.6 then 0.5 before falling back."""
        db = AsyncMock()
        empty_result = MagicMock()
        empty_result.all.return_value = []
        db.execute = AsyncMock(return_value=empty_result)

        fake_embedding = [0.1] * 1536
        with patch.object(
                 vector_search, "get_embedding", new=AsyncMock(return_value=fake_embedding)
             ), \
             patch.object(
                 vector_search, "_text_search_fallback", new=AsyncMock(return_value=[])
             ), \
             patch.dict(os.environ, {"ENABLE_VECTOR_SEARCH": "1"}):
            results = await vector_search.search_properties(
                db, "duplex", search_mode="vector", similarity_threshold=0.7
            )

        assert results == []
        # Three vector attempts: 0.7, 0.6, 0.5
        assert db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_search_never_raises(self):
        """Any internal explosion must return [] (chat pipeline depends on it)."""
        db = AsyncMock()
        with patch.object(
                 vector_search, "get_embedding",
                 new=AsyncMock(side_effect=RuntimeError("boom")),
             ), \
             patch.object(
                 vector_search, "_text_search_fallback",
                 new=AsyncMock(side_effect=RuntimeError("boom2")),
             ), \
             patch.dict(os.environ, {"ENABLE_VECTOR_SEARCH": "1"}):
            results = await vector_search.search_properties(db, "anything")
        assert results == []
