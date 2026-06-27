"""
Canonical Arabic/English copy for the free-path compound comparison flow.

Marketing principles applied:
  * Lead with the SAVING (gap_egp), not the listing's raw price.
  * Anchor against the developer benchmark so the value framing is concrete.
  * One actionable sentence per turn; the card carries the data, the text
    sells the move.
  * Always end with a low-friction next step (talk to advisor / unlock).

All string placeholders are unchanged or optional by context:
    {compound}, {n}, {gap_egp}, {type_ar}, {type_en},
    {size}, {price}, {names}, {developer}, {area}, {suggestions}.
"""

AREA_LABEL_AR = {
    "new cairo": "التجمع / القاهرة الجديدة",
    "sheikh zayed": "الشيخ زايد",
    "6th of october": "6 أكتوبر",
    "north coast": "الساحل الشمالي",
}

AREA_LABEL_EN = {
    "new cairo": "New Cairo / Tagamoa",
    "sheikh zayed": "Sheikh Zayed",
    "6th of october": "6th of October",
    "north coast": "North Coast",
}

# ── Free-path redirect ──────────────────────────────────────────────────────
# Fires when user asks something non-comparison while in AWAITING_NAMES.
FREE_PATH_REDIRECT_AR = (
    "لو سمحت حدد أسماء 2 أو 3 كمبوندات أو مطورين. "
    "هاعملك مقارنة بين سعر المطور والـ resale، وأحسن سعر عندي هو أكبر فرق لصالحك."
)

FREE_PATH_REDIRECT_EN = (
    "Please name 2 or 3 compounds or developers. I'll compare developer prices "
    "against resale prices; the best price is the biggest gap in your favor."
)

FREE_PATH_REDIRECT_WITH_AREA_AR = (
    "لو سمحت حدد أسماء 2 أو 3 كمبوندات أو مطورين في {area}. "
    "مثلاً: {suggestions}. هاعملك مقارنة بين سعر المطور والـ resale، "
    "وأحسن سعر عندي هو أكبر فرق لصالحك."
)

FREE_PATH_REDIRECT_WITH_AREA_EN = (
    "Please name 2 or 3 compounds or developers in {area}. For example: {suggestions}. "
    "I'll compare developer prices against resale prices; the best price is the biggest gap in your favor."
)

NEED_MORE_NAMES_AR = (
    "تمام، {name}. عشان أطلع أحسن سعر محتاج اسم كمبوند أو مطور كمان على الأقل للمقارنة. "
    "ابعت اسمين جنب {name} وهقارن سعر المطور مقابل الـ resale."
)

NEED_MORE_NAMES_EN = (
    "Got {name}. To find the best price, send at least one more compound or developer. "
    "I'll compare developer pricing against resale pricing side by side."
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


NO_POSITIVE_GAP_AR = (
    "قارنت {names} بس مفيش فرق resale واضح تحت سعر المطور دلوقتي. "
    "ابعتلي 2 أو 3 أسماء تانية ونشوف فين أكبر فرصة حقيقية."
)

NO_POSITIVE_GAP_EN = (
    "I compared {names}, but none has a clear resale discount below the developer benchmark right now. "
    "Send 2 or 3 other names and I'll look for the strongest real gap."
)


DEVELOPER_MISSING_DEALS_AR = (
    "مفيش بيانات resale كافية تحت {developer} دلوقتي عبر المشاريع المتاحة عندي. "
    "لو تحب، اختار كمبوند محدد من: {suggestions}."
)

DEVELOPER_MISSING_DEALS_EN = (
    "I do not have enough live resale deals under {developer} across the projects I can read right now. "
    "Pick a specific compound instead, for example: {suggestions}."
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
    "**أحسن سعر في المقارنة**\n"
    "• الفائز من الـ {n}: **{winner}**.\n"
    "• التوفير: حوالي **{gap_egp} ج.م** على {type_ar} مقارنة بسعر المطور.\n"
    "• السبب: ده أكبر خصم resale بالنسبة المئوية (حوالي **{gap_pct}%** تحت سعر المطور) في القائمة."
)
MULTI_WINNER_HEADLINE_EN = (
    "**Best price in this comparison**\n"
    "• Winner out of {n}: **{winner}**.\n"
    "• Saving: roughly **{gap_egp} EGP** on a {type_en} versus the developer benchmark.\n"
    "• Why it matters: it's the biggest resale discount (about **{gap_pct}%** below developer price) in your list."
)


# ── Single-compound top-listing headline ────────────────────────────────────
# Format mirrors a broker's pitch: name the property type, the size, the
# resale ask, then the saving against developer — in that order.
SINGLE_TOP_HEADLINE_AR = (
    "**أحسن سعر في {compound}**\n"
    "• أفضل عرض: {type_ar} {size}م² بسعر resale **{price}**.\n"
    "• التوفير: حوالي **{gap_egp} ج.م** تحت متوسط سعر المطور لنفس النوع.\n"
    "• الخطوة الجاية: افتح الكارت للتفاصيل أو ابعت ميزانيتك أرتبلك البدائل."
)
SINGLE_TOP_HEADLINE_EN = (
    "**Best price in {compound}**\n"
    "• Top deal: {type_en} {size}m² listed at **{price}**.\n"
    "• Saving: roughly **{gap_egp} EGP** below the developer benchmark for the same type.\n"
    "• Next step: open the card for details, or send your budget and I'll narrow the options."
)


DEVELOPER_TOP_HEADLINE_AR = (
    "**أحسن سعر تحت {developer}**\n"
    "• أفضل عرض: {type_ar} {size}م² في **{compound}** بسعر resale **{price}**.\n"
    "• التوفير: حوالي **{gap_egp} ج.م** تحت متوسط سعر المطور لنفس النوع.\n"
    "• ملحوظة: رتبت مشاريع {developer} حسب أكبر فرق resale لصالحك."
)
DEVELOPER_TOP_HEADLINE_EN = (
    "**Best price under {developer}**\n"
    "• Top deal: {type_en} {size}m² in **{compound}** listed at **{price}**.\n"
    "• Saving: roughly **{gap_egp} EGP** below the developer benchmark for the same type.\n"
    "• Note: I ranked {developer}'s projects by the strongest resale gap in your favor."
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
