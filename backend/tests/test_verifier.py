"""
Tests for the post-SPEAK hallucination guardrail
(backend/app/ai_engine/verifier.py).

We mock the Anthropic client so these tests run without network access or
API keys. Covers:
  - price/area/developer structural checks (no LLM needed)
  - fallback LLM adjudication for ROI / delivery / legal
  - log_hallucination_flags swallowing exceptions (fire-and-forget safety)
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure JWT secret is set before importing the app.
import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")


@pytest.fixture
def anyio_backend():
    # Force anyio (already installed in the repo) to use asyncio. This lets
    # us run async tests without pytest-asyncio.
    return "asyncio"

from app.ai_engine.verifier import (  # noqa: E402
    ClaimVerdict,
    ExtractedClaim,
    _area_match,
    _developer_match,
    _price_match,
    _verify_structurally,
    log_hallucination_flags,
    verify_response,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _text_block(text: str):
    """Minimal Anthropic SDK-compatible content block."""
    return SimpleNamespace(type="text", text=text)


def _mock_anthropic_response(payload: dict):
    resp = MagicMock()
    resp.content = [_text_block(json.dumps(payload))]
    return resp


def _mock_client(*responses):
    """Build an AsyncAnthropic mock that returns `responses` in order."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(side_effect=list(responses))
    client.close = AsyncMock()
    return client


# ─────────────────────────────────────────────────────────────────────────────
# Structural matchers
# ─────────────────────────────────────────────────────────────────────────────


class TestStructuralMatchers:
    def test_price_within_2pct_matches(self):
        prop = {"price": 10_000_000}
        assert _price_match(10_100_000, prop) is True  # +1%
        assert _price_match(9_900_000, prop) is True  # -1%

    def test_price_outside_2pct_does_not_match(self):
        prop = {"price": 10_000_000}
        assert _price_match(10_500_000, prop) is False  # +5%

    def test_area_within_5pct_matches(self):
        assert _area_match(205, {"size_sqm": 200}) is True
        assert _area_match(300, {"size_sqm": 200}) is False

    def test_developer_match_is_case_insensitive_substring(self):
        props = [{"developer": "Mountain View", "compound": "Hyde Park"}]
        assert _developer_match("mountain view", props) is True
        assert _developer_match("Hyde", props) is True
        assert _developer_match("FakeDevCo", props) is False


# ─────────────────────────────────────────────────────────────────────────────
# _verify_structurally: no LLM needed for price/area/developer with evidence
# ─────────────────────────────────────────────────────────────────────────────


class TestVerifyStructurally:
    def test_flags_wrong_price_with_high_severity(self):
        claim = ExtractedClaim(
            claim_type="price",
            text="The unit costs 5 million EGP",
            numeric_value=5_000_000,
        )
        props = [{"price": 10_000_000}]
        verdict = _verify_structurally(claim, props)
        assert verdict is not None
        assert verdict.verified is False
        assert verdict.severity == "high"

    def test_accepts_correct_price(self):
        claim = ExtractedClaim(
            claim_type="price", text="10M EGP", numeric_value=10_100_000
        )
        props = [{"price": 10_000_000}]
        verdict = _verify_structurally(claim, props)
        assert verdict is not None
        assert verdict.verified is True
        assert verdict.severity == "low"

    def test_flags_invented_developer(self):
        claim = ExtractedClaim(
            claim_type="developer",
            text="FakeDevCo is a top developer",
            subject="FakeDevCo",
        )
        props = [{"developer": "Mountain View", "compound": "iCity"}]
        verdict = _verify_structurally(claim, props)
        assert verdict is not None
        assert verdict.verified is False
        assert verdict.severity == "high"

    def test_returns_none_when_no_properties_available(self):
        """Without evidence we can't make a structural call — defer to LLM."""
        claim = ExtractedClaim(claim_type="price", text="10M", numeric_value=10_000_000)
        assert _verify_structurally(claim, []) is None

    def test_roi_claim_defers_to_llm(self):
        claim = ExtractedClaim(claim_type="roi", text="20% ROI", numeric_value=20)
        assert _verify_structurally(claim, [{"price": 10_000_000}]) is None


# ─────────────────────────────────────────────────────────────────────────────
# verify_response — end-to-end with a mocked Anthropic client
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
class TestVerifyResponse:
    async def test_empty_response_returns_empty(self):
        assert await verify_response("") == []
        assert await verify_response("   \n  ") == []

    async def test_flags_wrong_price_without_calling_adjudicator(self):
        """Structural check should short-circuit — extractor call only."""
        extraction = _mock_anthropic_response(
            {
                "claims": [
                    {
                        "claim_type": "price",
                        "text": "The villa costs 5,000,000 EGP",
                        "numeric_value": 5_000_000,
                        "unit": "EGP",
                        "subject": "Hyde Park",
                    }
                ]
            }
        )
        client = _mock_client(extraction)

        verdicts = await verify_response(
            "The villa at Hyde Park costs 5,000,000 EGP.",
            properties_mentioned=[{"compound": "Hyde Park", "price": 10_000_000}],
            client=client,
        )

        assert len(verdicts) == 1
        assert verdicts[0].verified is False
        assert verdicts[0].severity == "high"
        # Extractor called exactly once; adjudicator NOT called (structural fallback).
        assert client.messages.create.await_count == 1

    async def test_uses_adjudicator_for_roi_claim(self):
        extraction = _mock_anthropic_response(
            {
                "claims": [
                    {
                        "claim_type": "roi",
                        "text": "Expect 25% annual ROI",
                        "numeric_value": 25,
                        "unit": "%",
                        "subject": None,
                    }
                ]
            }
        )
        adjudication = _mock_anthropic_response(
            {
                "verified": False,
                "severity": "medium",
                "reason": "No evidence supports a 25% ROI",
            }
        )
        client = _mock_client(extraction, adjudication)

        verdicts = await verify_response(
            "Expect 25% annual ROI.",
            properties_mentioned=[{"compound": "Hyde Park"}],
            client=client,
        )

        assert len(verdicts) == 1
        v = verdicts[0]
        assert v.verified is False
        assert v.severity == "medium"
        assert v.evidence_source == "adjudicator.haiku"
        assert client.messages.create.await_count == 2

    async def test_no_claims_means_no_verdicts(self):
        client = _mock_client(_mock_anthropic_response({"claims": []}))
        assert await verify_response("Hello!", properties_mentioned=[], client=client) == []

    async def test_malformed_json_is_dropped_safely(self):
        bad = MagicMock()
        bad.content = [_text_block("not JSON at all")]
        client = _mock_client(bad)
        assert await verify_response("anything", properties_mentioned=[], client=client) == []


# ─────────────────────────────────────────────────────────────────────────────
# log_hallucination_flags — fire-and-forget safety
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
class TestLogHallucinationFlags:
    async def test_swallows_exceptions_from_verify(self):
        """Even if verify_response explodes, the background task must not raise."""
        with patch(
            "app.ai_engine.verifier.verify_response",
            AsyncMock(side_effect=RuntimeError("boom")),
        ):
            summary = await log_hallucination_flags(
                response_text="hi",
                properties_mentioned=[],
                agent_name="wolf_brain",
                session_id="sess-1",
                user_id=42,
                query="what?",
            )
        assert "error" in summary
        assert summary["error"] == "boom"
        assert summary["agent_name"] == "wolf_brain"

    async def test_returns_zero_when_no_claims(self):
        with patch(
            "app.ai_engine.verifier.verify_response",
            AsyncMock(return_value=[]),
        ):
            summary = await log_hallucination_flags(
                response_text="hi",
                properties_mentioned=[],
            )
        assert summary["total_claims"] == 0
        assert summary["flagged"] == 0

    async def test_does_not_persist_verified_claims(self):
        """Only unverified verdicts should be persisted; verified ones skipped."""
        verified_verdict = ClaimVerdict(
            claim=ExtractedClaim(claim_type="price", text="10M", numeric_value=10_000_000),
            verified=True,
            severity="low",
        )
        with patch(
            "app.ai_engine.verifier.verify_response",
            AsyncMock(return_value=[verified_verdict]),
        ), patch(
            "app.ai_engine.verifier.AsyncSessionLocal"
        ) as sess_ctx:
            fake_session = MagicMock()
            fake_session.add = MagicMock()
            fake_session.commit = AsyncMock()
            sess_ctx.return_value.__aenter__.return_value = fake_session
            sess_ctx.return_value.__aexit__.return_value = AsyncMock(return_value=None)

            summary = await log_hallucination_flags(
                response_text="x", properties_mentioned=[]
            )

        assert summary["total_claims"] == 1
        assert summary["flagged"] == 0
        fake_session.add.assert_not_called()
