# Osool — Guest-Chat 403 Fix + Honest Landing Copy

Generated 2026-06-19 from a verified multi-agent investigation. Two deliverables:
1. Root cause + exact fix for the production guest-chat 403.
2. Full honest landing-copy rewrite (EN + Arabic), critic-reviewed.

---

# PART 1 — The guest-chat 403 (root cause + fix)

## Root cause (verified, confidence 0.9)

A guest on `osool-ten.vercel.app/chat` fires `POST https://osool-production.up.railway.app/api/v1/chat`
**directly cross-origin** to Railway. The backend `CSRFProtectionMiddleware` runs before the
route and returns **403 `{"error":"CSRF token missing or invalid"}`** because:
- `/api/v1/chat` is **not** in `CSRF_EXEMPT_PATHS` (`csrf_protection.py:42-53`),
- POST is a protected method and the only bypass is an `Authorization: Bearer` header, which a guest lacks (`csrf_protection.py:199-213`),
- the cross-origin browser request carries **no** `X-CSRF-Token` header and **no** `csrf_token` cookie → reject at `csrf_protection.py:224-232`.

The request never reaches the route. The **stream** path works because `web/app/api/chat/stream/route.ts`
is a *same-origin* Next proxy that GETs the backend to obtain a CSRF token+cookie and replays
them — the **non-stream** path has no such proxy. The frontend calls it via the `api` axios
instance whose `baseURL` is the Railway origin (`web/lib/api.ts:34-46`), so `page.tsx:452`'s
`api.post('/api/v1/chat')` goes cross-origin.

**Why it's 403, not 401/429/404:** `get_current_user_optional` returns `None` for guests
(never raises) so auth isn't the source; a single request is far under rate limits (429);
the route is mounted at `main.py:401` (not 404). The 403 carries a CSRF JSON body. Confirmed.

**Key constraint:** the CSRF cookie is `SameSite=Strict` (`csrf_protection.py:256`), so a
cross-origin XHR can *never* send it. Client-side token juggling cannot fix this — the request
must be made **same-origin**. That's why the proxy is the correct fix.

## Fix (recommended: same-origin proxy, mirrors the stream path)

### 1. New file: `web/app/api/v1/chat/route.ts`
```ts
import { NextRequest, NextResponse } from 'next/server';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const DEFAULT_APP_ORIGIN = process.env.NEXT_PUBLIC_APP_URL || 'https://osool-ten.vercel.app';

function extractCookieValue(h: string, k: string) { return h.match(new RegExp(`${k}=([^;]+)`))?.[1] ?? null; }
function extractCookiePairs(h: string) {
  if (!h) return '';
  return h.split(/,(?=\s*[^;,\s]+=)/).map(c => c.trim().split(';')[0]).filter(Boolean).join('; ');
}

export async function POST(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const qs = url.search; // preserve ?simulate_tier=free
    const body = await request.text();
    const origin = request.headers.get('origin') || DEFAULT_APP_ORIGIN;
    const referer = `${origin}/`;

    const bootstrap = await fetch(`${API_URL}/api/seo/projects`, {
      method: 'GET', headers: { Origin: origin, Referer: referer }, cache: 'no-store',
    });
    const setCookie = bootstrap.headers.get('set-cookie') || '';
    const csrfToken = bootstrap.headers.get('x-csrf-token') || extractCookieValue(setCookie, 'csrf_token') || '';
    const cookieHeader = extractCookiePairs(setCookie);

    const headers: Record<string, string> = { 'Content-Type': 'application/json', Origin: origin, Referer: referer };
    if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
    if (cookieHeader) headers['Cookie'] = cookieHeader;
    const authHeader = request.headers.get('authorization');
    if (authHeader) headers['Authorization'] = authHeader;

    const upstream = await fetch(`${API_URL}/api/v1/chat${qs}`, { method: 'POST', headers, body, cache: 'no-store' });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { 'Content-Type': upstream.headers.get('content-type') || 'application/json' },
    });
  } catch (e) {
    console.error('Chat proxy error:', e);
    return NextResponse.json({ detail: 'Chat proxy unavailable' }, { status: 503 });
  }
}
```

### 2. `web/app/chat/page.tsx` (~line 452) — call same-origin (no Railway baseURL)
```ts
// BEFORE:
const res = await api.post(url, { message: trimmed, session_id: sessionId, language: 'auto', is_authenticated: isAuthenticated }, { signal: controller.signal });

// AFTER (axios is already imported at page.tsx:4):
const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
const res = await axios.post(
  url, // '/api/v1/chat' — resolved same-origin (no baseURL), hits the new Next proxy
  { message: trimmed, session_id: sessionId, language: 'auto', is_authenticated: isAuthenticated },
  { signal: controller.signal, headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined },
);
```

### Alternative (one-line backend hotfix, also CSRF-safe)
Add `"/api/v1/chat"` to `CSRF_EXEMPT_PATHS` in `backend/app/middleware/csrf_protection.py:42-53`.
Fastest unblock; the proxy is preferred for consistency with the stream path.

## CRITICAL secondary finding — "no account needed" is doubly broken
Even after the CSRF fix, `chat.py:169` **gates anonymous users with 401 + `requires_auth`**,
and the frontend then redirects them to `/signup` (`page.tsx:497-505`). So your landing
promise *"Three free questions. No account needed"* is contradicted **twice**: by CSRF (now
fixed) and by the route's own anonymous gate. **Decide one of:**
- (a) genuinely allow guest free questions → loosen the anonymous 401 gate in `chat.py:169` for the free path, **or**
- (b) keep it gated → change the landing copy to "Ask in seconds (free with a quick sign-up)" — which the honest copy in Part 2 already does (invite-only beta).

Recommendation: pick (b) for now (matches the invite-only reality), revisit (a) later if you
want a frictionless top-of-funnel.

## Other secondary issues
- The CSRF bootstrap piggybacks on `GET /api/seo/projects`; if that endpoint changes, both proxies break. Consider a dedicated lightweight CSRF-bootstrap GET.
- `lib/api.ts:471-473` retries 403-once only for the stream path; the non-stream path surfaces a transient CSRF miss immediately as the generic "Couldn't reach Osool."

---

# PART 2 — Honest landing copy (v2, critic-reviewed)

Every claim below is something the product can do today, or a clearly-labeled future
statement. No transaction count, verified registry, escrow rail, contract feature, measured
accuracy figure, or live market-data read — none of those exist yet. Where Osool compares
prices, it compares against what similar units are *listed* at, not a live market feed.

## 0. Metadata (`layout.tsx`)
- **title:** `Osool — The honest way to buy property in Egypt`
- **description:** `An AI property advisor built for Egypt. Ask in Arabic or English, get a straight read on whether an asking price is fair against similar listed units. Private beta in New Cairo & Sheikh Zayed.`
- **og:title:** `Osool — The honest way to buy property in Egypt`
- **og:description:** `Ask about any Egyptian property in Arabic or English. An honest read on price, no hype, no fake numbers. Private beta.`

## 1. Hero
**Eyebrow** (drop the ٤١٢ deal count):
- EN: `Private beta · New Cairo & Sheikh Zayed`
- optional numeral signature: `٢ neighbourhoods, to start`

**Headline (bilingual stacked):**
- EN (italic on "buy property"): `The honest way to buy property in Egypt.`
- AR (Cairo Display, dialect): `الطريقة الصادقة عشان تشتري عقار في مصر.`

**Subtitle** (downgraded from "reads the market"):
- EN: `Ask about any property in Egypt — in Arabic or English. Osool compares the asking price against what similar units in the area are listed at, and tells you plainly whether it makes sense. No inflated promises, no numbers we can't stand behind.`
- AR: `اسأل عن أي عقار في مصر، بالعربي أو الإنجليزي. أصول بيقارن السعر المطلوب بالوحدات الشبهها المعروضة في نفس المنطقة، ويقولّك بصراحة السعر معقول ولا لأ. من غير وعود مفيهاش لازمة، ولا أرقام مش قادرين نقف وراها.`

**Composer placeholder:** EN `Ask Osool about any property in Egypt…` · AR `اسأل أصول عن أي عقار في مصر…`

**Suggestion chips (all bilingual):**
1. EN `Show apartments in New Cairo under 8M` · AR `وريني شقق في التجمع تحت ٨ مليون`
2. EN `Is 8.4M fair for a 3-bedroom in Sheikh Zayed?` · AR `سعر ٨.٤ مليون لشقة ٣ أوض في الشيخ زايد معقول؟`
3. EN `What are similar units in 5th Settlement listed at?` · AR `الوحدات الشبهها في التجمع الخامس معروضة بكام؟`

**Trust pills** (remove CBE-compliant / Civil Code 131 / FRA-125 / escrow). Replace:
- `Prices in EGP` / `الأسعار بالجنيه`
- `Arabic & English` / `عربي وإنجليزي`
- `Built in Cairo, for Egypt` / `اتعمل في القاهرة، لمصر`
- `Private beta` / `بيتا مقفولة`

## 2. Pillars — "Three honest reasons"
**Head:** eyebrow `What Osool actually does` · title `Three honest reasons to ask Osool first.`
- Lead EN: `Property listings in Egypt are written to sell, not to inform. Osool exists to give you the other side of the conversation — straight, in your language, before you put money down.`
- Lead AR: `إعلانات العقارات في مصر مكتوبة عشان تبيعلك، مش عشان تفهّمك. أصول موجود يدّيك الطرف التاني من الكلام — بصراحة، بلغتك، قبل ما تدفع.`

**Dossier 1 — An honest read on price.** Body: `Tell Osool the unit and the asking price. It compares against what similar units in the area are listed at, and tells you where this one sits — high, fair, or worth a second look. When the data is thin, it says so instead of inventing confidence.` Footer: `No precision we haven't earned · Ranges, not false decimals`

**Dossier 2 — Speaks Egyptian.** Body: `Ask in Egyptian Arabic or English — switch mid-sentence if you like. Prices are in EGP, areas are the ones you actually search, and the market it knows is the Egyptian one. Not a foreign tool with Cairo bolted on.` Footer: `EGP · العربية / English · Native, not translated`

**Dossier 3 — Refuses to oversell.** Body: `Osool won't tell you a unit is a once-in-a-lifetime deal, and it won't quote a number it can't trace. If it doesn't know, it tells you it doesn't know. That restraint is the product.` Footer: `Honesty over hype`

## 3. Chat preview (scrub all fabricated figures)
**Head:** eyebrow `See how it answers` · title `A straight answer, in the time it takes to ask.`
- Lead EN: `Real questions in plain language. When Osool gives you a number it tells you where it came from — and when the data is thin, it says that too.`
- Lead AR: `أسئلة عادية بكلام بسيط. لما أصول يقولّك رقم، بيقولّك جه منين — ولو الداتا قليلة، بيقولّك على كده برضه.`

**User msg:** `Looking at 3-bedroom apartments in New Cairo around 8M EGP. Where should I be looking, and is 8M reasonable?`

**AI reply (hedged, no invented %):** `Around 8M in New Cairo, three-bedroom apartments are realistic in several of the larger compounds, though finished, ready-to-move units sit at the top of that budget. Asking prices vary widely by compound, finish, and delivery stage — so 8M is reasonable for some and a stretch for others. Tell me the specific unit and I'll give you a sharper read.`
- AR: `حوالي ٨ مليون في التجمع، تلاقي شقق ٣ أوض في كذا كمبوند كبير، بس المتشطبة والجاهزة بتكون في آخر الميزانية دي. الأسعار بتفرق كتير حسب الكمبوند والتشطيب ومرحلة التسليم — فـ ٨ مليون معقولة لبعضها وعالية لغيرها. قولّي على الوحدة بالظبط وأديك قراية أدق.`

**Summary strip** (delete fake 54.2K/5.8%/62d): `Budget/الميزانية → ~8M EGP/حوالي ٨ مليون` · `Area/المنطقة → New Cairo/التجمع` · `Read/القراية → Reasonable, unit-dependent/معقول، على حسب الوحدة`

**Property cards** (delete 0–100 scores; default to anonymized + visible `Illustrative`/`للتوضيح` badge):
- `Compound A` / New Cairo / `from ~9M` · `Above your budget — finished units`
- `Compound B` / 5th Settlement / `~7M` · `Within budget, varies by phase`
- `Compound C` / New Cairo / `~8M` · `Right at your number`
- Caption: EN `Illustrative example — not live listings or quoted prices.` · AR `مثال للتوضيح — مش إعلانات حقيقية ولا أسعار مطلوبة.`

## 4. How it works (remove the escrow/reserve step 3)
**Head:** eyebrow `How it works` · title `From "is this worth it" to a clear answer.`
- 01 **Ask in your own words** — EN `Budget, area, bedrooms — or paste a listing you're looking at. Type it in Arabic or English, whichever's easier.` · AR `الميزانية، المنطقة، عدد الأوض — أو الزق لينك إعلان شايفه. اكتبها بالعربي أو الإنجليزي، أنهي أسهل.`
- 02 **Get a straight read** — EN `Osool tells you where the asking price sits against similar units nearby, and what to watch for — in plain language, with the reasoning shown, not hidden.` · AR `أصول يقولّك السعر المطلوب واقف فين بالنسبة للوحدات الشبهها حواليك، وتخلي بالك من إيه — بكلام بسيط، والمنطق قدامك، مش مخبّي.`
- 03 **Decide with your eyes open** — EN `Take the read into your own negotiation. Osool's job is to make sure you walk in knowing what's fair — the deal stays yours to make.` · AR `خد القراية معاك في التفاوض بتاعك. شغلة أصول إنك تدخل عارف الصح فين — الصفقة تفضل قرارك إنت.`

## 5. Numbers band → ANTI-numbers statement (the strategic centerpiece)
- Eyebrow: `Why we don't show you a wall of numbers`
- Title: `Most property sites lead with numbers. We won't show you ones we made up.`
- Body EN: `We're a private beta. We haven't closed deals, so we won't claim a deal count. We don't run a verified registry, so we won't pretend to. When Osool gives you a number, it's because the data is real — and when it isn't, we say nothing. That's the whole promise.`
- Body AR: `إحنا لسه في بيتا مقفولة. ما عملناش صفقات، فمش هنقولّك رقم صفقات. ما عندناش سجل موثّق، فمش هندّعي. لما أصول يقولّك رقم، يبقى لإن الداتا حقيقية — ولو مش حقيقية، مش بنقول حاجة. دي كل الحكاية.`
- Signature (use this line ONLY here): `No fake numbers — ever.` / `أرقام مزيفة؟ أبداً.`

## 6. Developers strip (kill "trusted partnerships" + logos)
- Label EN: `Osool reads public listings across Egypt's major compounds` · AR `أصول بيقرا الإعلانات المتاحة للعامة في أكبر كمبوندات مصر`
- Sub: `Public data, not partnerships.` / `داتا عامة، مش شراكات.`
- Names as plain text (no logos), or cut entirely for max legal safety: `EMAAR · Mountain View · Hyde Park · Talaat Moustafa · Palm Hills · SODIC · Madinaty`

## 7. Closing CTA (invite-only reality)
- Headline EN: `Start with one honest question.` · AR `ابدأ بسؤال واحد، بصراحة.`
- Sub EN: `Ask about any property in Egypt, in Arabic or English. Osool is in private beta in New Cairo and Sheikh Zayed — invite-only for now.` · AR `اسأل عن أي عقار في مصر، بالعربي أو الإنجليزي. أصول في بيتا مقفولة في التجمع والشيخ زايد — بالدعوة بس دلوقتي.`
- Primary button: `Request an invite` / `اطلب دعوة`
- Remove "talk to a licensed advisor" and the "9 AM–11 PM" availability line.

## 8. Footer tagline
- EN: `Osool — the honest way to buy property in Egypt.` · AR `أصول — الطريقة الصادقة عشان تشتري عقار في مصر.`
- Small print: `Private beta · New Cairo & Sheikh Zayed · Prices in EGP` / `بيتا مقفولة · التجمع والشيخ زايد · الأسعار بالجنيه`

---

### Fabrications removed (for the record)
٤١٢ deals closed · "0 double-sells" · verified registry · ±2.4% accuracy · 412 verified units ·
1.8s valuation time · 54.2K/5.8%/62d market stats · 0–100 property scores · CBE-compliant /
Civil Code 131 / FRA-125-ready pills · InstaPay/Fawry escrow + reserve step · contract review ·
"trusted listings from leading developers" partnership framing + logo wall.
