"""
Canonical Arabic copy for the free-path compound comparison flow.

All user-facing strings live here so the dialog driver and router stay focused
on logic. English fallbacks are provided where the conversation might already
be in English (detected via `_contains_arabic` on the first turn).
"""

# Initial redirect — fires when user asks something non-comparison while in
# AWAITING_NAMES (ROI, area general, inflation hedging, etc.). The free path's
# only job is compound comparison; everything else gets nudged back here.
FREE_PATH_REDIRECT_AR = (
    "أنا هنا عشان أعملك مقارنة دقيقة بين كمبوندات بعينها. "
    "قول لي 2 أو 3 كمبوندات أو مطورين وأنا أطلعلك أحسن سعر."
)

FREE_PATH_REDIRECT_EN = (
    "I'm here to give you a precise comparison between specific compounds. "
    "Name 2 or 3 compounds or developers and I'll surface the best price."
)


# User gave a single compound — announce the single-compound mode (top 3 deals).
SINGLE_COMPOUND_ANNOUNCE_AR = (
    "تمام، هاطلعلك أحسن 3 عروض في {compound} بناءً على الفرق بين سعر المطور والـ resale."
)
SINGLE_COMPOUND_ANNOUNCE_EN = (
    "Got it — I'll surface the top 3 deals in {compound} ranked by the gap "
    "between developer and resale prices."
)


# User gave too many compounds (4+).
TOO_MANY_AR = "كتير شوية. اختار 3 بس من: {names}."
TOO_MANY_EN = "That's a lot. Pick just 3 from: {names}."


# Developer named has no flagship compound with enough rows.
DEVELOPER_NO_FLAGSHIP_AR = (
    "أي كمبوند بالظبط من {developer}؟ مثلاً: {suggestions}."
)
DEVELOPER_NO_FLAGSHIP_EN = (
    "Which compound exactly from {developer}? For example: {suggestions}."
)


# Resale data missing for one of the named compounds.
MISSING_RESALE_AR = "مفيش بيانات resale لـ {compound} دلوقتي، تختار كمبوند تاني؟"
MISSING_RESALE_EN = "No resale data for {compound} yet — pick another compound?"


# Announcement before running a multi-compound comparison.
MULTI_COMPARE_ANNOUNCE_AR = "هاعملك مقارنه بين الـ {n} كمبوندات… ثانية واحدة."
MULTI_COMPARE_ANNOUNCE_EN = "Running the comparison across {n} compounds — one moment."


# After the one allowed free comparison is consumed.
COMPARISON_USED_AR = (
    "خلصت المقارنة المجانية. للوصول للنتائج الكاملة وكمبوندات إضافية، "
    "افتح الباقة المتقدمة."
)
COMPARISON_USED_EN = (
    "You've used your free comparison. To unlock full results and additional "
    "compounds, upgrade to premium."
)


# Multi-compound winner headline. {winner} compound, {gap} formatted EGP, {type_ar}/{type_en}.
MULTI_WINNER_HEADLINE_AR = (
    "أحسن سعر بين الـ {n}: {winner} — فرق {gap_egp} ج.م بين سعر المطور والـ resale ({type_ar})."
)
MULTI_WINNER_HEADLINE_EN = (
    "Best price among {n}: {winner} — {gap_egp} EGP gap between developer and resale price ({type_en})."
)


# Single-compound top-listing headline.
SINGLE_TOP_HEADLINE_AR = (
    "أحسن عرض في {compound}: {type_ar} {size}م، سعرها resale {price}، "
    "فرق {gap_egp} ج.م تحت سعر المطور."
)
SINGLE_TOP_HEADLINE_EN = (
    "Best deal in {compound}: {type_en} {size}m, resale price {price}, "
    "{gap_egp} EGP below the developer benchmark."
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
