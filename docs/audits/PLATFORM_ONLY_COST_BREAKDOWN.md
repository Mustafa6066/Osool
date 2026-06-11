# Osool Platform Only — Detailed LLM Cost Breakdown

**Date:** May 2026  
**Last Updated:** May 3, 2026  
**Scope:** Osool-Platform (FastAPI + Next.js) excluding Osool-orchestrator  
**Currency:** USD  
**Assumption:** contract analysis endpoint excluded from monthly estimates

> [!warning] **Use The Real Project Models**
> The backend is currently configured for these exact models:
> - `claude-sonnet-4-5-20250929`
> - `gpt-4o`
> - `gpt-4o-mini`
> - `text-embedding-3-small`
>
> This document uses those pinned models and their current official prices. It does not swap the platform to GPT-5.x.

> [!info] **Pricing Sources Checked On May 3, 2026**
> - Anthropic Claude API pricing docs
> - OpenAI model pages for GPT-4o and GPT-4o-mini
> - OpenAI embeddings guide for `text-embedding-3-small`
> - Railway pricing page
> - Vercel Hobby and Pro plan docs

> [!note] **API Pricing, Not ChatGPT Subscription Pricing**
> Osool Platform pays API token pricing, not ChatGPT seat pricing.

---

## LLM Models in Use

Osool-Platform uses a **multi-model strategy** to optimize cost and latency:

**Claude Sonnet 4.5**
- Primary Use: Wolf Brain chat, real estate reasoning, streaming responses
- Base input: $3.00 per 1M tokens
- Prompt caching: $3.75 per 1M for 5-minute cache writes, $6.00 per 1M for 1-hour cache writes, $0.30 per 1M cache reads
- Output: $15.00 per 1M tokens
- Batch API: $1.50 per 1M input, $7.50 per 1M output

**GPT-4o**
- Primary Use: Market analysis, valuation reasoning, customer insights
- Input: $2.50 per 1M tokens
- Cached input: $1.25 per 1M tokens
- Output: $10.00 per 1M tokens

**GPT-4o-mini**
- Primary Use: SEO generation, lightweight summaries, list items
- Input: $0.15 per 1M tokens
- Cached input: $0.075 per 1M tokens
- Output: $0.60 per 1M tokens

**text-embedding-3-small**
- Primary Use: Property semantic search, similarity ranking
- Cost: about $0.00002 per 1K input tokens
- Features: 1536-dim vectors, vector database retrieval

**Routing Strategy:**
- **Chat turns** → Claude Sonnet 4.5 (streaming, context-aware)
- **Valuation requests** → GPT-4o (with XGBoost fallback for baseline)
- **Price comparisons** → GPT-4o-mini (lightweight, ~1K tokens)
- **Intent extraction** → GPT-4o-mini (classification task)
- **Embeddings** → text-embedding-3-small (batch, nightly)
- **SEO/content** → GPT-4o-mini (high volume, low complexity)

---

## 1. Executive Summary & Total Cost at a Glance

Osool-Platform's monthly cost is overwhelmingly driven by **LLM usage**. In this revision, the representative stage model assumes **100 chat turns per active user per month**, so Claude Sonnet chat traffic dominates every stage. Hosting, database, and services remain secondary, but they are no longer the main cost lever.

### Total Monthly Cost — All Scenarios

> [!tip] **QUICK REFERENCE - Monthly Cost By Stage**
> - **Founder MVP / Demo** (50–150 users): $147–$163/mo  
> - **Production Beta** (100–500 users): $467–$532/mo  
> - **Early Traction** (500–2K users): $1,549–$1,656/mo  
> - **Growth Stage** (2K–10K users): $7,421–$7,941/mo  
> 
> If you need commercial-compliant hosting from day one, use the Beta range as the real launch floor because Vercel Hobby is for personal / non-commercial use.

**Detailed breakdown:**
- **Founder MVP / Demo** (50–150 users): $147–$163/mo
- **Production Beta** (100–500 users): $467–$532/mo
- **Early Traction** (500–2,000 users): $1,549–$1,656/mo
- **Growth Stage** (2,000–10,000 users): $7,421–$7,941/mo

---

## Detailed Breakdown by Category

### Total Cost by Category (All Scales)

---

## 2. Infrastructure & Fixed Costs

These are paid whether you have 0 or 5,000 active users.

> [!note] **Infrastructure Cost Summary**
> - **MVP / Demo:** $6–$22/mo  
> - **Beta / Commercial Launch:** $41–$106/mo  
> - **Traction:** $125–$232/mo  
> - **Growth:** $260–$780/mo

**Detailed costs by component:**

MVP / Demo Stage:
- Vercel Hobby: $0
- Railway Hobby minimum: $5
- Extra Railway DB / storage usage: $0–$15
- Domain + SSL: $1–$2
- Monitoring / backups / email: $0 initially

Beta / Commercial Launch Stage:
- Vercel Pro platform fee: $20
- Railway Pro minimum: $20
- Additional Railway compute / DB / storage: $0–$30
- Redis: $0–$15
- Monitoring: $0–$29
- Domain, backups, email: $1–$12

Traction Stage:
- Vercel Pro + usage overages: $20–$50
- Railway Pro + compute/storage overages: $60–$120
- Redis: $10–$20
- Monitoring: $29–$50
- Email / backups / domain: $6–$12

Growth Stage:
- Vercel Pro + usage overages: $50–$180
- Railway Pro + compute/storage overages: $160–$500
- Redis: $20–$60
- Monitoring / observability: $29–$100
- Email / backups / domain: $15–$40

**Notes:**
- Railway Hobby is a $5 minimum usage plan with $5 included usage credit.
- Railway Pro is a $20 minimum usage plan with $20 included usage credit.
- Railway reference pricing: CPU $0.00000772 per vCPU-second, memory $0.00000386 per GB-second.
- Vercel Pro is $20/month, includes 1 deploying seat, and includes $20/month in usage credit.
- Vercel Hobby is free, but intended for personal / non-commercial use.

> [!tip] **Your Fixed Production Assumption**
> If you want to model the platform using your own operational assumption instead of the wider ranges above, use:
> - **Railway:** up to **$60/mo**
> - **Vercel Pro:** **$20/mo**
> - **Fixed infrastructure baseline:** **$80/mo**
>
> In that version of the model, your total monthly cost becomes:
> **Total monthly cost = $80 fixed infra + monthly LLM cost**

---

## 3. LLM Costs by Endpoint

These are the variable costs that scale with user activity and chat volume.

### 3.1 Chat (Wolf Brain / CoInvestor)

**The core product — powered by Claude Sonnet 4.5.**

**What it pays for:**
- Streaming conversation with AI advisor (via Wolf Brain orchestrator)
- Extended thinking for complex market analysis (optional, can be disabled)
- Cross-session memory retrieval (via vector search)
- Property retrieval and ranking
- Real-time responses in Arabic and English
- Prompt caching (enabled by default)

**Model:** `claude-sonnet-4-5-20250929`

**Token estimates per turn:**
- System prompt (Egyptian RE context, Wolf Master Prompt): 1,200 tokens (Cacheable; 50%+ cache hit expected)
- User message: 200 tokens (Current turn input)
- Retrieved property context (RAG, 5 properties × 300 tokens): 1,500 tokens (Biggest variable; shrink with better ranking)
- Conversation history (last 3 turns): 600 tokens (Includable via memory system)
- **Total input: ~3,500 tokens**
- Expected output: 500 tokens (Streaming response + action suggestions)

**Model & pricing (May 2026 — Anthropic official):**
- Base input: $3.00 / 1M tokens
- Cache reads: $0.30 / 1M tokens
- Output: $15.00 / 1M tokens
- Simplified steady-state per-turn estimate: `((1500 × 0.30) + (2000 × 3.00) + (500 × 15.00)) / 1,000,000 = $0.01395`

**Monthly cost at different scales:**

> [!note] **Chat (Wolf Brain + Claude Sonnet) — Monthly Cost**
> - **Founder MVP** (100 users, 100 turns/user): $139.50/mo ($1.3950/user)  
> - **Production Beta** (300 users, 100 turns/user): $418.50/mo ($1.3950/user)  
> - **Early Traction** (1,000 users, 100 turns/user): $1,395.00/mo ($1.3950/user)  
> - **Growth** (5,000 users, 100 turns/user): $6,975.00/mo ($1.3950/user)  
> 
> Assumes: 100 chat turns/user/month, 1,500 cached read tokens, 2,000 standard input tokens, and 500 output tokens per turn.

**Cost optimization:**
- Prompt caching is already assumed in the numbers above
- Reduce RAG context from 5 properties to 2–3 where answer quality holds
- Gate extended thinking to only complex paths
- Cache repeated retrieval results in Redis

**Combined optimization potential:** Another **20–35%** on chat spend if context size and cache hit rate improve.

---

### 3.2 Property Valuation

**Hybrid approach: XGBoost baseline + GPT-4o reasoning.**

**What it pays for:**
- XGBoost statistical model (baseline valuation estimate — free)
- GPT-4o reasoning explanation (market logic, investment narrative)
- Asks user for property details (location, size, condition)
- Returns estimated fair value + market comparison + investment narrative

**Model:** `gpt-4o`

**Token estimates:**
- System prompt (valuation guidelines + Egyptian market data): 600 tokens (Cacheable)
- User property input (description + details): 150 tokens
- Retrieved comparable properties (5–10 × 100 tokens): 750 tokens (Market data, reduced from 1000)
- Market snapshot (inflation, rates, area trends): 400 tokens (Cached or Redis)
- **Total input to GPT-4o: ~1,900 tokens** (Optimized from 2,150)
- Expected output (explanation + market reasoning): 300 tokens (Short structured response)

**Model & pricing (May 2026 — OpenAI official):**
- GPT-4o input: $2.50 / 1M tokens
- GPT-4o cached input: $1.25 / 1M tokens
- GPT-4o output: $10.00 / 1M tokens
- Per-valuation cost: `(1900 × 2.50 + 300 × 10.00) / 1,000,000 = $0.00775`
- If fully batched offline, cost is roughly half that.

**Monthly cost at different scales:**

> [!note] **Property Valuation (GPT-4o) — Monthly Cost**
> - **Founder MVP** (100 users, 0.5 valuations/user): $0.39/mo ($0.0039/user)  
> - **Production Beta** (300 users, 1.5 valuations/user): $3.49/mo ($0.0116/user)  
> - **Early Traction** (1,000 users, 2 valuations/user): $15.50/mo ($0.0155/user)  
> - **Growth** (5,000 users, 3 valuations/user): $116.25/mo ($0.0233/user)  
> 
> Assumes: standard GPT-4o pricing, not Batch API pricing.

**Cost optimization:**
- Cache repeated valuations by property ID + market snapshot
- Use Batch API for nightly recalculations and offline refreshes
- Shrink comparable-property payloads where possible

**Combined optimization:** Roughly **20–50%** on repeat-heavy valuation traffic.

---

### 3.3 Price Comparison

**Lightweight classification — powered by GPT-4o-mini.**

**What it pays for:**
- Compare asking price vs. estimated market value
- Identify if a property is overpriced or underpriced
- Show reasoning in Arabic and English

**Model:** `gpt-4o-mini` (cost-optimized for fast classification)

**Token estimates:**
- System prompt (price logic, market context): 400 tokens (Cacheable)
- User query (property + asking price): 100 tokens
- Retrieved comps (3–5 properties × 100 tokens): 400 tokens (Reduced from 500)
- **Total input: ~900 tokens**
- Output (verdict + reasoning): 150 tokens (Short response)

**Model & pricing (May 2026 — OpenAI official):**
- GPT-4o-mini input: $0.15 / 1M tokens
- GPT-4o-mini cached input: $0.075 / 1M tokens
- GPT-4o-mini output: $0.60 / 1M tokens
- Per-request cost: `(900 × 0.15 + 150 × 0.60) / 1,000,000 = $0.000225`

**Monthly cost at different scales:**

> [!note] **Price Comparison (GPT-4o-mini) — Monthly Cost**
> - **Founder MVP** (100 users, 0.5 comparisons): $0.011/mo ($0.00011/user)  
> - **Production Beta** (300 users, 1 comparison): $0.068/mo ($0.00023/user)  
> - **Early Traction** (1,000 users, 1.5 comparisons): $0.34/mo ($0.00034/user)  
> - **Growth** (5,000 users, 2 comparisons): $2.25/mo ($0.00045/user)  
> 
> Assumes: 0.5–2 comparisons/user/month via GPT-4o-mini.

**Cost optimization:**
- Cache the result if the same property + asking price is queried repeatedly
- Do not prioritize this before chat and valuation optimization

**Combined potential:** Small in absolute dollars; this path is already cheap.

---

### 3.4 Lead Scoring & Intent Extraction

**Classification task — powered by GPT-4o-mini.**

**What it pays for:**
- Classify user intent (buyer, investor, seller, landlord, etc.)
- Score investment readiness and lead quality
- Used by backend for analytics and notifications

**Model:** `gpt-4o-mini` (lightweight classification)

**Token estimates:**
- System prompt (intent taxonomy + scoring rubric): 300 tokens (Cacheable)
- User chat history excerpt (last 5 turns): 400 tokens (Conversation context)
- **Total input: ~700 tokens**
- Output (intent + score + confidence): 50 tokens (Structured JSON)

**Model & pricing (May 2026 — OpenAI official):**
- GPT-4o-mini input: $0.15 / 1M tokens
- GPT-4o-mini output: $0.60 / 1M tokens
- Per-extraction cost: `(700 × 0.15 + 50 × 0.60) / 1,000,000 = $0.000135`

**Monthly cost at different scales:**

> [!note] **Intent Extraction (GPT-4o-mini) — Monthly Cost**
> - **Founder MVP** (100 users, 100 extractions/user): $1.35/mo ($0.01350/user)  
> - **Production Beta** (300 users, 100 extractions/user): $4.05/mo ($0.01350/user)  
> - **Early Traction** (1,000 users, 100 extractions/user): $13.50/mo ($0.01350/user)  
> - **Growth** (5,000 users, 100 extractions/user): $67.50/mo ($0.01350/user)  
> 
> Assumes: 100 extractions/user/month via GPT-4o-mini, aligned with the 100-chat-turn model used in this revision.

**Cost optimization:**
- Use deterministic fallbacks for obvious cases
- Batch offline analytics if you ever move this path off the critical request path
- Do not prioritize this before chat or valuation optimization

**Combined potential:** Small in absolute dollars; this path is already efficient.

---

### 3.5 Embeddings & Vector Search

**Semantic search via OpenAI embeddings.**

**What it pays for:**
- Convert property descriptions → 1536-dimensional vectors
- Semantic search for "properties similar to X"
- Used at ingestion time and at query time (cached)

**Model:** `text-embedding-3-small` (1536-dim, efficient)

**Token estimates:**
- Property description (avg 200 tokens per property): 200 tokens
- **Total per property: ~200 tokens**

**Model & pricing:**
- **OpenAI text-embedding-3-small:** $0.00002 per 1K tokens
- Per-embedding cost: `(200 × $0.00002) / 1K = $0.000004` per property

**Monthly cost at different scales:**

> [!note] **Embeddings (text-embedding-3-small) — Monthly Cost**
> - **Ongoing updates:** ~$0.001/month (negligible)  
> - **One-time ingestion (3,274 properties):** $0.013 one-time  
> - **Batch updates (monthly):** ~10 properties/day × 30 days = 300 props/month = $0.0012/month  
> 
> Cost optimization: Already near-zero; local embeddings save $0.001 but add CPU cost.

---

## 4. Total LLM Cost by Scale

Summing all endpoints (Chat + Valuation + Comparison + Intent + Embeddings):

> [!summary] **Combined LLM Spend by Stage (Actual Project Models)**
>
> Representative LLM totals below assume **100 chat turns/user/month** and **100 intent checks/user/month**.
>
> **Founder MVP** — Chat: $139.50 | Valuation: $0.39 | Comparison: $0.011 | Intent: $1.35 | Embeddings: $0.001 | **TOTAL: $141.25**
>
> **Production Beta** — Chat: $418.50 | Valuation: $3.49 | Comparison: $0.068 | Intent: $4.05 | Embeddings: $0.001 | **TOTAL: $426.11**
>
> **Early Traction** — Chat: $1,395.00 | Valuation: $15.50 | Comparison: $0.34 | Intent: $13.50 | Embeddings: $0.001 | **TOTAL: $1,424.34**
>
> **Growth (5K users)** — Chat: $6,975.00 | Valuation: $116.25 | Comparison: $2.25 | Intent: $67.50 | Embeddings: $0.001 | **TOTAL: $7,161.00**
>
> **Infrastructure + LLM Combined:**
>
> **MVP:** Infra $6–$22 | LLM $141.25 | **Total: $147–$163**
>
> **Beta:** Infra $41–$106 | LLM $426.11 | **Total: $467–$532**
>
> **Traction:** Infra $125–$232 | LLM $1,424.34 | **Total: $1,549–$1,656**
>
> **Growth:** Infra $260–$780 | LLM $7,161.00 | **Total: $7,421–$7,941**

**Key observations:**
1. Chat dominates the LLM bill, now roughly 97–99% of total AI spend in the 100-turn model.
2. Valuation is the second meaningful AI cost center.
3. Price comparison, intent extraction, and embeddings remain small.
4. The biggest savings lever is reducing Claude token volume and chat frequency, not switching everything to a newer model family.

### How Consumption Per User Is Calculated

I used a two-part model:

1. **Fixed infrastructure cost**
- This is the hosting bill you pay even if no one uses the AI.
- With your assumption: `Infrastructure per user = 80 / active users`

2. **Variable LLM cost**
- This is the cost of API calls generated by each user.
- I calculate this endpoint by endpoint, then sum them.

**Per-user LLM formulas used in this document**
- Chat per user = `chat_turns_per_user × 0.01395`
- Valuation per user = `valuations_per_user × 0.00775`
- Price comparison per user = `comparisons_per_user × 0.000225`
- Intent extraction per user = `intent_extractions_per_user × 0.000135`
- Embedding cost per user is effectively ignored in the monthly user model because it is ingestion-driven and near-zero.

**High-engagement assumption used here**
- `chat_turns_per_user = 100`
- `intent_extractions_per_user = 100`
- Valuation and comparison counts still vary by stage.

**Total per-user monthly cost**
- `Total per user = (fixed infra / active users) + chat per user + valuation per user + comparison per user + intent per user`

**Concrete examples using your $80/month infra assumption**

**Example A — 100 active users, founder pattern**
- Infrastructure per user = `80 / 100 = $0.80`
- Chat per user = `100 × 0.01395 = $1.395`
- Valuation per user = `0.5 × 0.00775 = $0.003875`
- Comparison per user = `0.5 × 0.000225 = $0.0001125`
- Intent per user = `100 × 0.000135 = $0.0135`
- **Total per user = about $2.2125/month**
- **Total monthly platform cost = about $221.25**

**Example B — 300 active users, beta pattern**
- Infrastructure per user = `80 / 300 = $0.2667`
- Chat per user = `100 × 0.01395 = $1.395`
- Valuation per user = `1.5 × 0.00775 = $0.011625`
- Comparison per user = `1 × 0.000225 = $0.000225`
- Intent per user = `100 × 0.000135 = $0.0135`
- **Total per user = about $1.6870/month**
- **Total monthly platform cost = about $506.11**

**Example C — 1,000 active users, traction pattern**
- Infrastructure per user = `80 / 1000 = $0.08`
- Chat per user = `100 × 0.01395 = $1.395`
- Valuation per user = `2 × 0.00775 = $0.0155`
- Comparison per user = `1.5 × 0.000225 = $0.0003375`
- Intent per user = `100 × 0.000135 = $0.0135`
- **Total per user = about $1.5043/month**
- **Total monthly platform cost = about $1,504.34**

**Example D — 5,000 active users, growth pattern**
- Infrastructure per user = `80 / 5000 = $0.016`
- Chat per user = `100 × 0.01395 = $1.395`
- Valuation per user = `3 × 0.00775 = $0.02325`
- Comparison per user = `2 × 0.000225 = $0.00045`
- Intent per user = `100 × 0.000135 = $0.0135`
- **Total per user = about $1.4482/month**
- **Total monthly platform cost = about $7,241.00**

**Why the per-user cost drops as you scale**
- The LLM part per user stays relatively close to usage behavior.
- The infrastructure part gets divided across more users.
- That is why `80 / 100 = $0.80/user`, but `80 / 5000 = $0.016/user`.

---

## 5. Alternative Model Cost Scenarios

This section compares the current Claude chat path against cheaper hosted models and local Ollama models. The purpose is not to switch blindly. The goal is to identify which model is cheap enough, good enough in Arabic real-estate conversations, and practical enough for production.

### 5.1 Current Baseline: Claude Sonnet 4.5 For Chat

**Current chat cost formula:**
- Per chat turn = `$0.01395`
- Chat per active user = `100 × 0.01395 = $1.395/month`
- Beta chat volume = `300 users × 100 chats = 30,000 chat turns/month`
- Beta chat cost = `30,000 × 0.01395 = $418.50/month`

**Representative Beta total using your fixed infra assumption:**
- Fixed Railway + Vercel baseline: `$80/month`
- Claude chat: `$418.50/month`
- Other AI paths: about `$7.61/month`
- **Total platform cost: about `$506.11/month`**

**Meaning:** Claude is the quality baseline, but it is also the cost problem. At 100 chats per user, the rest of the AI stack is small compared with chat.

### 5.2 Hosted Cheap Model Scenario: DeepSeek V4 Flash

DeepSeek V4 Flash is the lowest-cost hosted option in this analysis. It exposes OpenAI-compatible and Anthropic-compatible endpoints, which makes it easier to test than a fully local model.

**Pricing used, checked May 4, 2026:**
- Cache-hit input: `$0.0028 / 1M tokens`
- Cache-miss input: `$0.14 / 1M tokens`
- Output: `$0.28 / 1M tokens`

**Same chat-token profile as the current Claude estimate:**
- Cached read input: `1,500 tokens`
- Standard input: `2,000 tokens`
- Output: `500 tokens`

**Per-turn cost:**
- `(1500 × 0.0028 + 2000 × 0.14 + 500 × 0.28) / 1,000,000 = $0.0004242`

**Beta scenario, 300 users, 100 chats/user:**
- Chat turns: `30,000/month`
- DeepSeek V4 Flash chat cost: `30,000 × 0.0004242 = $12.73/month`
- Other AI paths unchanged: about `$7.61/month`
- Fixed Railway + Vercel baseline: `$80/month`
- **Total platform cost: about `$100.33/month`**

**Stage totals with DeepSeek V4 Flash for chat only, using fixed `$80/month` infra:**
- **100 users:** about `$85.99/month`
- **300 users:** about `$100.33/month`
- **1,000 users:** about `$151.76/month`
- **5,000 users:** about `$478.10/month`

**Tradeoff:** This is the strongest cost-saving candidate. The risk is quality: Arabic fluency, Egyptian real-estate nuance, tool-following, long-context consistency, and hallucination control must be benchmarked before production.

### 5.3 Hosted Better-Cheap Scenario: DeepSeek V4 Pro

DeepSeek V4 Pro costs more than Flash but may be a better test candidate if Flash is too weak for sales-quality chat.

**Discounted pricing used, checked May 4, 2026:**
- Cache-hit input: `$0.003625 / 1M tokens`
- Cache-miss input: `$0.435 / 1M tokens`
- Output: `$0.87 / 1M tokens`

**Per-turn cost using the same profile:**
- `(1500 × 0.003625 + 2000 × 0.435 + 500 × 0.87) / 1,000,000 = about $0.0013104`

**Beta scenario, 300 users, 100 chats/user:**
- DeepSeek V4 Pro chat cost: about `$39.31/month`
- Other AI paths unchanged: about `$7.61/month`
- Fixed Railway + Vercel baseline: `$80/month`
- **Total platform cost: about `$126.92/month`**

**Stage totals with DeepSeek V4 Pro for chat only, using fixed `$80/month` infra:**
- **100 users:** about `$94.86/month`
- **300 users:** about `$126.92/month`
- **1,000 users:** about `$240.39/month`
- **5,000 users:** about `$921.22/month`

**Tradeoff:** More expensive than Flash, still far cheaper than Claude. This is a good second candidate if Flash underperforms on Arabic persuasion, reasoning, or grounding.

### 5.4 Local Model Scenario: Gemma / DeepSeek Distill Via Ollama

Ollama removes per-token API spend for chat, but it does not make inference free. It moves cost from API tokens to GPU infrastructure, operations, monitoring, and reliability.

**Planning assumption:**
- Existing Railway + Vercel baseline remains: `$80/month`
- Dedicated GPU inference box: roughly `$120–$300+/month`
- Non-chat cloud AI paths stay unchanged for the first test: valuations, comparisons, intent, embeddings

**Stage totals with local Ollama chat only:**
- **100 users:** about `$201.75–$381.75/month`
- **300 users:** about `$207.61–$387.61/month`
- **1,000 users:** about `$229.34–$409.34/month`
- **5,000 users:** about `$386.00–$566.00/month`

**Meaning:** Ollama is much cheaper than Claude at 5,000 users, but not necessarily cheaper than DeepSeek hosted at 100–1,000 users. The fixed GPU cost only becomes attractive when usage is high enough to keep the machine busy.

**Best use of Ollama in this platform:**
- Internal summaries
- Intent extraction
- Lead qualification drafts
- Admin-side analysis
- Offline batch enrichment
- Privacy-sensitive experiments

**Risk for main chat:** Local Gemma-family models or DeepSeek distills may be weaker at Egyptian Arabic, long sales conversations, strict property grounding, and nuanced buyer objections. They need a benchmark before replacing the public CoInvestor chat.

### 5.5 Recommendation

**Best cost experiment:** DeepSeek V4 Flash for chat.

**Best quality/cost compromise experiment:** DeepSeek V4 Pro for chat.

**Best control/privacy experiment:** Ollama with Gemma-family or DeepSeek-distilled models.

**Do not switch the full platform in one step.** Start with a provider abstraction, route 0% production traffic at first, run the benchmark below, then use shadow traffic before exposing users.

### 5.6 Arabic Real-Estate Chat Benchmark Plan

The benchmark should answer one question: can the cheaper model replace Claude for Osool's buyer-facing Arabic real-estate advisor without hurting trust, accuracy, or conversion?

**Models to compare:**
- Claude Sonnet 4.5, current baseline
- DeepSeek V4 Flash, cheapest hosted candidate
- DeepSeek V4 Pro, stronger hosted candidate
- Local Gemma-family model via Ollama
- Optional local DeepSeek-distilled model via Ollama

**Benchmark dataset:**
- 100 Arabic and bilingual chat tasks
- 40 Egyptian Arabic buyer-advisor conversations
- 20 investment/ROI conversations
- 15 property search and filtering conversations
- 10 objection-handling conversations, such as price, trust, installment risk, developer reputation
- 10 compliance-sensitive conversations, including payment restrictions and fractional ownership claims
- 5 adversarial hallucination tests where the model must say it does not know or ask for missing data

**Each test case should include:**
- User message
- Conversation history, if relevant
- Retrieved property snippets, same for every model
- Expected business outcome
- Ground-truth property facts
- Forbidden claims
- Preferred language style, such as Arabic, English, or mixed Egyptian Arabic

**Scoring rubric, 100 points:**
- Arabic fluency and tone: 15 points
- Real-estate domain usefulness: 20 points
- Grounding in provided property data: 20 points
- Reasoning and recommendation quality: 15 points
- Sales effectiveness without pushiness: 10 points
- Compliance and safety: 10 points
- Latency and streaming feel: 5 points
- Cost per successful conversation: 5 points

**Hard fail conditions:**
- Invents property prices, availability, developer names, or payment terms
- Gives legal or financial certainty where the platform should be cautious
- Breaks Arabic badly enough to reduce trust
- Ignores retrieved property context
- Cannot maintain a coherent multi-turn conversation

**Acceptance gates before switching production chat:**
- Cheaper model reaches at least `85%` of Claude's total benchmark score
- Property factuality is at least `95%`
- Zero critical compliance hallucinations
- Hosted model p95 latency below `8 seconds`
- Local Ollama p95 latency below `15 seconds`
- Cost is at least `60%` lower than Claude for the same benchmark set

**Test procedure:**
1. Freeze 100 benchmark prompts and their retrieved property context.
2. Run every model against the exact same prompts and context.
3. Log input tokens, output tokens, latency, model errors, and estimated cost.
4. Score with one human reviewer and one LLM judge, then manually inspect disagreements.
5. Run a 5% shadow-traffic test where cheaper models answer in the background but users still see Claude.
6. If results hold, expose 5% of real traffic to the cheaper model with instant fallback to Claude.
7. Increase gradually to 25%, 50%, then 100% only if quality and support metrics stay stable.

**Recommended first benchmark winner:** If DeepSeek V4 Flash scores above the acceptance gates, use it for main chat. If it misses on tone or reasoning but V4 Pro passes, use V4 Pro. If both hosted models fail, keep Claude for public chat and use Ollama only for internal or offline tasks.

---

## 6. Cost Reduction Roadmap

Apply these in priority order for the current **Claude Sonnet 4.5 + GPT-4o + GPT-4o-mini** setup.

### Phase 1: Before Launch (Highest ROI, Quickest Implementation)

#### 6.1 Keep Prompt Caching On Chat (Already Enabled)
- Claude Sonnet 4.5 prompt caching is enabled by default (`ENABLE_PROMPT_CACHING=true`)
- Savings from caching are already assumed in the chat numbers above
- The next optimization step is improving cache hit rate and reducing uncached context size

#### 6.2 Model Routing Already Optimized
- Chat → Claude Sonnet 4.5 (streaming, reasoning)
- Valuation → GPT-4o (market analysis)
- Comparison → GPT-4o-mini (lightweight classification)
- Intent → GPT-4o-mini (fast classification)
- **Savings: Already realized by using right model for each task**

#### 6.3 Cache Valuations & Price Comparisons
- Implement 24h Redis cache keyed by `property_id + market_snapshot_date`
- Repeat lookups should not recompute identical reasoning
- This matters more for valuations than for simple comparisons

#### 6.4 Reduce RAG Context In Chat
- Instead of 5 properties at 300 tokens, aim for 2–3 properties or shorter snippets
- Measure answer quality before and after trimming context
- This is the highest-impact token reduction lever

**Total Phase 1 savings:** usually **20–35%** on chat-heavy workloads if retrieval and cache behavior improve.

### Phase 2: After Launch (Medium Effort, Sustainable)

#### 6.5 Use Batch API For Non-Real-Time GPT-4o Jobs
- Identify batch workloads: nightly valuation refreshes and offline recalculations
- Any workload that is not user-facing in real time should not pay synchronous prices

#### 6.6 Monitor & Extend Cache Hit Rate to 70%+ (Already Included)
- Claude Sonnet 4.5 cache hit rate monitoring via logs
- Tweak prompt structure iteratively
- **Savings: Already in model estimates**

#### 6.7 Implement Client-Side Deduplication
- Debounce chat input (user mashes Enter)
- Collapse repeat queries within 30s

**Total Phase 2 savings:** meaningful but secondary compared with chat-context reduction.

### Phase 3: Post-Product-Market-Fit (Nice-To-Have)

#### 6.8 Switch to Local Embeddings (Save $0.001/month, add CPU)
- Only worthwhile if you're ingesting 10K+ properties/month
- **Savings: Negligible for now**

#### 6.9 Add SEO Generation With GPT-4o-mini
- If you build an SEO feature, GPT-4o-mini is still cheap enough for bulk content support jobs
- It should remain an add-on line item, not a core cost driver

---

## 7. Monthly Cost Scenarios

### 7.1 Lean Founder MVP

**Profile:** Solo founder, 50–150 active users, manual customer support, no paid services beyond domain.

**LLM breakdown (100 users):**
- Chat: $139.50
- Valuation: $0.39
- Comparison: $0.011
- Intent: $1.35
- Embeddings: $0.001

**Total LLM: $141.25/month**

**Infrastructure Breakdown:**
- Vercel Hobby: $0
- Railway Hobby minimum: $5
- Extra DB / storage usage: $0–$15
- Domain: $1–$2
- Misc buffer: $0–$5

**TOTAL: $147–$163/month**

**Realistic outcome:** Good for founder demos and validation. If you launch commercially, move to Beta assumptions.

---

### 7.2 Production-Ready Beta

**Profile:** Early-stage startup, 200–500 active users, some investor demo activity, need basic monitoring & backups.

**LLM breakdown (300 users):**
- Chat: $418.50
- Valuation: $3.49
- Comparison: $0.068
- Intent: $4.05
- Embeddings: $0.001

**Total LLM: $426.11/month**

**Infrastructure Breakdown:**
- Vercel Pro: $20
- Railway Pro minimum: $20
- Additional Railway usage: $0–$30
- Redis: $0–$15
- Monitoring: $0–$29
- Domain / backups / email: $1–$12

**TOTAL: $467–$532/month**

**Realistic outcome:** This is the most realistic early commercial operating range.

---

### 7.3 Early Traction

**Profile:** Funded pre-seed or strong organic growth, 500–2,000 active users, content marketing starting.

**LLM breakdown (1,000 users):**
- Chat: $1,395.00
- Valuation: $15.50
- Comparison: $0.34
- Intent: $13.50
- Embeddings: $0.001

**Total LLM: $1,424.34/month**

**Infrastructure Breakdown:**
- Vercel Pro + usage: $20–$50
- Railway Pro + overages: $60–$120
- Redis: $10–$20
- Monitoring: $29–$50
- Email / backups / domain: $6–$12

**TOTAL: $1,549–$1,656/month**

**Realistic outcome:** Early traction is still manageable, but chat efficiency starts to matter materially.

---

### 7.4 Growth Stage (2K–10K Users)

**Profile:** Strong product-market fit, 5,000+ active users, content marketing at scale.

**LLM breakdown (5,000 users):**
- Chat: $6,975.00
- Valuation: $116.25
- Comparison: $2.25
- Intent: $67.50
- Embeddings: $0.001

**Total LLM: $7,161.00/month**

**Infrastructure Breakdown:**
- Vercel Pro + overages: $50–$180
- Railway Pro + overages: $160–$500
- Redis: $20–$60
- Monitoring / observability: $29–$100
- Email / backups / domain: $15–$40

**TOTAL: $7,421–$7,941/month**

**Realistic outcome:** At this stage, reducing chat tokens matters more than shaving minor fixed infra costs.

---

## 8. Cost Control Checklist

Before launch, implement these controls to stay within budget:

- [ ] **LLM Usage Logging:** Log every API call with model, tokens, cost, endpoint, user, session. Daily rollup by endpoint and user.
- [ ] **Daily Budget Alerts:** Warn if spend > 50% of daily threshold. Alert at 80%. Block non-critical calls at 100%.
- [ ] **Cache Monitoring:** Log `cache_read_input_tokens` from Anthropic responses. Track hit rate % by agent. Target 70%+.
- [ ] **RAG Monitoring:** Log avg retrieved context size per chat turn. Shrink if > 2,000 tokens.
- [ ] **Model Routing:** Verify Sonnet 4.5 is used for chat, GPT-4o for valuation, and GPT-4o-mini for intent/comparisons.
- [ ] **Batch Job Inventory:** Document which jobs are daily recalculations, eligible for Batch API, not yet switched.
- [ ] **Error Budget:** Reserve 10% of daily budget for retries, rate-limit backoff, and operator error.
- [ ] **Weekly Review:** 15 min every Monday — which endpoint grew? Why? Any cost anomalies?

---

## 9. Frequently Asked Questions

**Q: Why Claude Sonnet 4.5 for chat instead of GPT-4o?**  
A: Claude Sonnet 4.5 fits the conversational path the platform is already built around: long-context chat, streaming, and reasoning-heavy replies. GPT-4o is kept for valuation-style analytical tasks, while Claude chat cost is managed primarily through prompt caching and context control.

**Q: Can I downgrade Claude Sonnet to Claude Haiku to save cost?**  
A: Only after validation. A cheaper Claude tier can reduce cost, but you should test Arabic fluency, reasoning quality, and sales-conversation performance before changing the production chat path.

**Q: Why use GPT-4o for valuations instead of Claude?**  
A: GPT-4o offers better market analysis and reasoning for financial estimates. Claude Sonnet focuses on conversational continuity. Using both models optimizes cost vs. quality per task.

**Q: Should I enable Extended Thinking for valuations?**  
A: Only for genuinely complex cases. For most residential MVP traffic, keep prompts tight and rely on good context retrieval first.

**Q: Can I use local embeddings instead of OpenAI?**  
A: Yes, for cost savings, but trade-offs: local embeddings (sentence-transformers) cost CPU but save $0.001/month. Only worthwhile at 10K+ properties/month or if you're already running self-hosted models.

**Q: Should I launch with Redis?**  
A: For MVP, no. Adds operational complexity ($0). Add at 100–200 active users for rate limiting and token blacklist. Caching is optional early.

**Q: What if my users chat even more than 100 turns/month?**  
A: Cost scales almost linearly with chat volume. In the current Claude Sonnet model, every extra 10 chats per user per month adds about `10 × 0.01395 = $0.1395` per active user per month. If engagement keeps rising, reduce RAG payload size first, then improve cache hit rate, then test cheaper chat models on a benchmark set before switching production traffic.

**Q: What if I switch the chat path to DeepSeek or another cheaper hosted Chinese model?**  
A: See Section 5. The short version: DeepSeek V4 Flash can reduce the representative Beta total from about `$506.11/month` to about `$100.33/month` if it replaces only Claude chat and quality holds. DeepSeek V4 Pro lands closer to `$126.92/month`. The catch is migration work: this codebase currently initializes Anthropic and OpenAI clients directly, so you need a provider abstraction or configurable base URLs before swapping providers safely.

**Q: What if I run Gemma, DeepSeek distills, or similar open models locally via Ollama?**  
A: See Section 5. Ollama makes chat token cost near-zero, but adds fixed GPU infrastructure. In the representative Beta scenario, local-chat-only with Ollama usually lands around `$207.61–$387.61/month`, depending on the GPU host. That is much cheaper than Claude, but usually not cheaper than DeepSeek V4 Flash at current scale.

**Q: Can I auto-switch models if Sonnet costs spike?**  
A: Yes, for non-critical paths only. For customer-facing chat and market analysis, maintain Claude Sonnet quality. Quality issues cost more in user churn than LLM savings.

**Q: What's the LLM cost per paying customer?**  
A: Depends on your unit economics. If customer LTV is $500, then $50/customer LLM cost is acceptable. If LTV is $20, optimize to <$5/customer LLM (use more caching + RAG shrinking).

**Q: What if I want to add SEO pages?**  
A: Use GPT-4o-mini (already in stack). Assume 2,000 tokens per page × $0.15/1M input = $0.0003/page. 100 pages/month = $0.03/month. Already cost-effective.

---

## 10. Master Summary — Models & Costs

### Models Used

> [!summary] **Osool Platform LLM Stack (Actual Config)**
>
> **Claude Sonnet 4.5** -- Chat, Wolf Brain reasoning, streaming  
> Base input $3.00 / MTok, cache read $0.30 / MTok, output $15.00 / MTok
>
> **GPT-4o** -- Valuations, market analysis  
> Input $2.50 / MTok, cached input $1.25 / MTok, output $10.00 / MTok
>
> **GPT-4o-mini** -- Intent, comparisons, lightweight tasks  
> Input $0.15 / MTok, cached input $0.075 / MTok, output $0.60 / MTok
>
> **text-embedding-3-small** -- Property semantic search  
> About $0.00002 per 1K input tokens
>
> **Representative Beta LLM total (300 users, 100 chats/user): $426.11/mo**

### Cost by Stage

> [!summary] **Monthly Cost Summary**
>
> Representative LLM totals below assume 100 chat turns/user/month and 100 intent checks/user/month.
>
> **MVP / Demo** -- 50-150 users | Infra: $6-22 | LLM: $141.25 | **Total: $147-163/mo**
>
> **Beta** -- 100-500 users | Infra: $41-106 | LLM: $426.11 | **Total: $467-532/mo**
>
> **Traction** -- 500-2K users | Infra: $125-232 | LLM: $1,424.34 | **Total: $1,549-1,656/mo**
>
> **Growth** -- 2K-10K users | Infra: $260-780 | LLM: $7,161.00 | **Total: $7,421-7,941/mo**

**Key takeaways:**
- Claude Sonnet 4.5 is still the dominant spend driver.
- GPT-4o remains the second meaningful cost center.
- GPT-4o-mini stays cheap enough that it is not an urgent optimization target.
- Railway Pro is a $20 minimum plan and Vercel Pro is $20/month with one deploying seat included.

---

## 11. Recommendation by Stage

> [!tip] **Stage-by-Stage Roadmap**
>
> - **MVP / Demo** ($147-163/mo): only realistic if 100 chat turns/user/month is your founder assumption
> - **Beta** ($467-532/mo): move to Vercel Pro + Railway Pro, add monitoring and optional Redis
> - **Traction** ($1,549-1,656/mo): improve Claude cache hit rate, batch offline GPT-4o work, reduce RAG payloads
> - **Growth** ($7,421-7,941/mo): treat chat volume and token efficiency as a core operating metric

**Updated guidance for May 2026:**
1. Keep the current routing based on actual configured models.
2. Use Vercel Pro as the commercial launch baseline.
3. Use Batch API for any non-real-time GPT-4o workload.
4. Push Claude cache hit rate up and reduce RAG token volume.
5. Re-check pricing monthly, but do not rewrite the cost model around unrelated model families.

**Bottom line:** For the platform as it is actually configured today, and assuming **100 chat turns per active user per month**, expect roughly **$147-163/month** for founder demos, **$467-532/month** for a first commercial beta, **$1,549-1,656/month** at early traction, and **$7,421-7,941/month** around a 5,000-user growth load.
