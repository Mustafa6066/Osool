"""
Canonical Arabic/English copy for the free-path compound comparison flow.

Marketing principles applied:
  * Lead with the SAVING (gap_egp), not the listing's raw price.
  * Anchor against the developer benchmark so the value framing is concrete.
  * One actionable sentence per turn; the card carries the data, the text
    sells the move.
  * Always end with a low-friction next step (talk to advisor / unlock).

All string placeholders are unchanged:
    {compound}, {n}, {gap_egp}, {type_ar}, {type_en},
    {size}, {price}, {names}, {developer}, {suggestions}.
"""

# ── Free-path redirect ──────────────────────────────────────────────────────
# Fires when user asks something non-comparison while in AWAITING_NAMES.
FREE_PATH_REDIRECT_AR = (
    "خليني أوفّر عليك مفاوضات أسبوعين في 10 ثواني. "
    "اكتبلي اسم 2 أو 3 كمبوندات (أو مطورين) — وهاطلعلك فين فيه أكبر فرق بين "
    "سعر المطور والـ resale بأرقام موثّقة من السوق."
)

FREE_PATH_REDIRECT_EN = (
    "Tell me 2 or 3 compounds (or developers) and I'll show you exactly where "
    "the resale market is undercutting the developer — with real numbers, not "
    "marketing talk. Free, takes 10 seconds."
)


# ── Single-compound mode announcement ───────────────────────────────────────
SINGLE_COMPOUND_ANNOUNCE_AR = (
    "تمام، {compound} اختيار ذكي. هاطلعلك أحسن 3 صفقات resale النهارده — "
    "مرتبة بالفرق الحقيقي تحت سعر المطور."
)
SINGLE_COMPOUND_ANNOUNCE_EN = (
    "Good pick — {compound}. Pulling the top 3 resale deals live, ranked by "
    "the real gap below the developer's current price list."
)


# ── User gave too many compounds ────────────────────────────────────────────
TOO_MANY_AR = (
    "كتير شوية. عشان المقارنة تطلع دقيقة، اختار 3 بس من: {names}. "
    "هاركّز عليهم وأديك تحليل أعمق."
)
TOO_MANY_EN = (
    "That's a lot. For a sharp comparison pick just 3 from: {names}. "
    "I'll go deeper on those."
)


# ── Developer has no flagship compound ──────────────────────────────────────
DEVELOPER_NO_FLAGSHIP_AR = (
    "{developer} عنده مشاريع متعددة وكل واحد ليه ديناميكية سعر مختلفة. "
    "أي كمبوند بالظبط تحب أحللّه؟ مثلاً: {suggestions}."
)
DEVELOPER_NO_FLAGSHIP_EN = (
    "{developer} has several projects and each one has its own price curve. "
    "Which compound exactly — for example {suggestions}?"
)


# ── Missing resale data ─────────────────────────────────────────────────────
MISSING_RESALE_AR = (
    "مفيش بيانات resale كافية في {compound} دلوقتي — ودي علامة كويسة "
    "(السوق ساكن أو الطلب أعلى من العرض). تختار كمبوند تاني نقارن بيه؟"
)
MISSING_RESALE_EN = (
    "Not enough live resale data in {compound} right now — usually a sign of "
    "tight supply. Pick another compound to compare?"
)


# ── Multi-compound announce ─────────────────────────────────────────────────
MULTI_COMPARE_ANNOUNCE_AR = (
    "بقارن الـ {n} كمبوندات دلوقتي… بشيك على أحدث resale + قائمة سعر المطور. "
    "ثانية واحدة."
)
MULTI_COMPARE_ANNOUNCE_EN = (
    "Cross-checking the {n} compounds against live resale and developer price "
    "lists — one moment."
)


# ── After the one free comparison is consumed ───────────────────────────────
COMPARISON_USED_AR = (
    "ده كان آخر مقارنة مجانية. في الباقة المتقدمة هاتشوف:\n"
    "• الفرق الكامل بين كل كمبوند والـ resale، مش الفائز بس\n"
    "• تحليل العائد لمدة 5 سنين (ROI + إيجار متوقع)\n"
    "• تنبيه فوري لما ينزل عرض أحسن من اللي شفته\n"
    "افتح الباقة المتقدمة أو اتكلم مع مستشار يشرحلك."
)
COMPARISON_USED_EN = (
    "That was your free comparison. Premium unlocks:\n"
    "• Full developer-vs-resale gap on every compound — not just the winner\n"
    "• 5-year ROI + expected rental yield per listing\n"
    "• Live alerts when a better deal than this one hits the market\n"
    "Unlock premium, or talk to a consultant."
)


# ── Multi-compound winner headline ──────────────────────────────────────────
# Leads with the saving, anchors on the developer benchmark, ends with the
# compound name so the user remembers the answer.
MULTI_WINNER_HEADLINE_AR = (
    "الفائز من الـ {n}: **{winner}**. "
    "هتوفّر حوالي **{gap_egp} ج.م** على {type_ar} مقارنة بسعر المطور المعلن. "
    "ده الكمبوند الوحيد في القائمة بفرق بالحجم ده."
)
MULTI_WINNER_HEADLINE_EN = (
    "Winner of the {n}: **{winner}**. "
    "Roughly **{gap_egp} EGP** in savings on a {type_en} versus the developer's "
    "listed price — the only compound in the set with a gap this size."
)


# ── Single-compound top-listing headline ────────────────────────────────────
# Format mirrors a broker's pitch: name the property type, the size, the
# resale ask, then the saving against developer — in that order.
SINGLE_TOP_HEADLINE_AR = (
    "أحسن صفقة في **{compound}** دلوقتي: {type_ar} {size}م² "
    "بسعر resale **{price}** — أقل بـ **{gap_egp} ج.م** من سعر المطور "
    "لنفس النوع. لو الميزانية متاحة، ده تايمنج كويس."
)
SINGLE_TOP_HEADLINE_EN = (
    "Top deal in **{compound}** right now: {type_en} {size}m² listed at "
    "**{price}** — **{gap_egp} EGP** below the developer benchmark for the "
    "same type. If the budget fits, this is good timing."
)


# Type labels (Arabic <-> English mapping for headline rendering)
TYPE_LABEL_AR = {
    "apartment": "شقة",
    "villa": "فيلا",
    "townhouse": "تاون هاوس",
    "twinhouse": "توين هاوس",
    "duplex": "دوبلكس",
    "studio": "استوديو",
}
