"""
Tests for the verifier POLICY layer (Fix 1): risk tiers, legal-guarantee
blocking, redaction, and the streaming pre-check.

These are pure-logic tests. The verifier only touches the DB session when the
response contains price/ROI numbers AND properties carry id+price, which we
deliberately avoid here. A MagicMock session is supplied as a safety net.

Ticket creation on block (wolf_orchestrator._handle_blocked_handoff) needs a
live DB + AsyncSessionLocal, so it is covered by integration/manual testing,
not here. The handoff is best-effort and swallows its own exceptions, so a
failure there can never break chat.
"""
from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

from unittest.mock import AsyncMock, MagicMock  # noqa: E402

import pytest  # noqa: E402

from app.ai_engine.verifier_agent import VerifierAgent  # noqa: E402


@pytest.fixture
def anyio_backend():
    # Run async tests on asyncio via anyio (the repo's convention — see
    # test_verifier.py). Avoids depending on pytest-asyncio auto mode.
    return "asyncio"


def _session():
    """A session that returns 'nothing found' for any query, as a safety net.
    The cases below avoid triggering DB lookups in the first place."""
    s = MagicMock()
    row = MagicMock()
    row.first = MagicMock(return_value=None)
    row.scalar_one_or_none = MagicMock(return_value=None)
    s.execute = AsyncMock(return_value=row)
    s.rollback = AsyncMock()
    return s


@pytest.mark.anyio
async def test_arabic_legal_guarantee_is_blocked():
    agent = VerifierAgent()
    # Legal term + guarantee language in ONE sentence (no Arabic comma split).
    text = "القانون المدني بيضمن لك استرداد مضمون 100% في أي وقت."
    result = await agent.verify_response(text, [], _session())
    assert result["policy"] == "blocked"
    assert result["blocked"] is True
    assert any(c["type"] == "legal_claim" for c in result["blocked_corrections"])


@pytest.mark.anyio
async def test_english_legal_guarantee_is_blocked():
    agent = VerifierAgent()
    text = "Under the Civil Code, your return is 100% legally guaranteed."
    result = await agent.verify_response(text, [], _session())
    assert result["policy"] == "blocked"


@pytest.mark.anyio
async def test_plain_legal_reference_not_blocked():
    agent = VerifierAgent()
    # Legal terms but NO guarantee/certainty word -> must NOT block.
    text = "حسب القانون المدني المصري، التعاقد بيمر بمرحلة التسجيل العقاري."
    result = await agent.verify_response(text, [], _session())
    assert result["policy"] != "blocked"
    assert result["blocked"] is False


@pytest.mark.anyio
async def test_invented_compound_is_blocked():
    agent = VerifierAgent()
    props = [{"compound": "Mountain View iCity"}]
    text = "I recommend a unit in compound Palm Hills Katameya."
    result = await agent.verify_response(text, props, _session())
    assert any(c["type"] == "compound_name" for c in result["blocked_corrections"])
    assert result["policy"] == "blocked"


@pytest.mark.anyio
async def test_clean_response_serves():
    agent = VerifierAgent()
    text = "أهلاً بيك! تحب أساعدك في إيه النهارده؟"
    result = await agent.verify_response(text, [], _session())
    assert result["policy"] == "serve"
    assert result["blocked"] is False
    assert result["fix_count"] == 0


def test_redact_blocked_replaces_sentence_with_caveat():
    agent = VerifierAgent()
    text = "Hello there. Under the Civil Code your return is guaranteed. Anything else?"
    blocked = [{"type": "legal_claim",
                "sentence": "Under the Civil Code your return is guaranteed."}]
    out = agent.redact_blocked_claims(text, blocked)
    assert "guaranteed" not in out
    assert agent.BLOCKED_CAVEAT_EN in out
    # surrounding content preserved
    assert "Hello there." in out
    assert "Anything else?" in out


def test_is_high_risk_turn():
    agent = VerifierAgent()
    assert agent.is_high_risk_turn("كام سعر الوحدة دي؟", False) is True
    assert agent.is_high_risk_turn("What's the ROI on this?", False) is True
    assert agent.is_high_risk_turn("هل العقد مضمون قانونيا؟", False) is True
    assert agent.is_high_risk_turn("ازيك عامل ايه", False) is False
    # Any listing quote forces a high-risk (buffer-then-verify) turn.
    assert agent.is_high_risk_turn("ازيك عامل ايه", True) is True
