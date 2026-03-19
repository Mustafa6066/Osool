# Osool Platform — AI Engine Architecture

> Post-consolidation (June 2025). See `_archived/` directories for deprecated modules.

## Request Flow

```
Frontend (Next.js)
│
├── POST /chat/stream  ──►  CoInvestorAgent  ──►  WolfBrain.process_turn()
├── POST /chat          ──►  CoInvestorAgent  ──►  WolfBrain.process_turn()
│
├── POST /ai/valuation       ──►  hybrid_brain_prod.get_valuation()
├── POST /ai/analyze-contract──►  hybrid_brain_prod.audit_contract()
├── POST /ai/compare-price   ──►  hybrid_brain_prod.compare_asking_price()
│
├── POST /ai/prod/valuation      ──►  hybrid_brain_prod.get_valuation()
└── POST /ai/prod/audit-contract ──►  hybrid_brain_prod.audit_contract()
```

## Active AI Components

### WolfBrain (`wolf_orchestrator.py`)

Master orchestrator for all conversational flows. 13-step pipeline:

1. Language detection
2. Parallel cognition (intent, psychology, context)
3. Property search (Supabase vector + PostgreSQL)
4. Deal analysis (ROI, comparisons)
5. Narrative generation (Claude 3.5 Sonnet with extended thinking)
6. Response verification

Entry point: `wolf_brain.process_turn(message, session_id, ...)`

### OsoolHybridBrainProd (`hybrid_brain_prod.py`)

Specialist tool for structured valuations. XGBoost (via MLOps endpoint) + GPT-4o:

- `get_valuation(area, property_type, bedrooms, ...)` — XGBoost price prediction + GPT-4o analysis
- `audit_contract(contract_text)` — Legal clause verification with Egyptian real estate rules
- `compare_asking_price(area, asking_price, ...)` — Market comparison with XGBoost baseline

### CoInvestorAgent (`app/agent/coinvestor.py`)

Thin adapter: converts LangChain message format → calls `wolf_brain.process_turn()` → maps output. Not an independent brain.

### CostTracker (`cost_tracker.py`)

Lightweight token cost accounting. Tracks cumulative input/output tokens with Claude 3.5 Sonnet pricing. Called by `/chat/stream` endpoint to report costs.

## Supporting Modules

| Module | Purpose |
|---|---|
| `wolf_router.py` | Fast query classification (property/general/comparison) |
| `perception_layer.py` | Intent extraction with GPT-4o |
| `analytical_engine.py` | ROI/score calculations, market intelligence (no LLM) |
| `psychology_layer.py` | User psychology detection & strategy |

## Archived Modules (`_archived/`)

| File | Reason |
|---|---|
| `openai_service.py` | Duplicated hybrid_brain_prod features without XGBoost |
| `claude_sales_agent.py` | 700+ lines, only cost tracking was used (extracted to `cost_tracker.py`) |
| `hybrid_brain.py` | Superseded by hybrid_brain_prod |
| `hybrid_brain_router.py` | Superseded by wolf_router |
| `parallel_brain.py` | Experimental, never deployed |
| `real_estate_os.py` | Dead placeholder stub (deleted) |

## Backward Compatibility

- `wolf_orchestrator.py` exports `hybrid_brain = wolf_brain` (line 4264)
- `__init__.py` exposes `get_hybrid_brain()` → returns wolf_brain
- These aliases exist for any external scripts that import `hybrid_brain`
