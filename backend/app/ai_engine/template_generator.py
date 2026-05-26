from typing import Dict, List, Any, Optional

_AREA_LABEL_AR = {
    "new cairo": "القاهرة الجديدة",
    "sheikh zayed": "الشيخ زايد",
    "6th of october": "6 أكتوبر",
    "north coast": "الساحل الشمالي",
    "new capital": "العاصمة الإدارية",
    "madinaty": "مدينتي",
    "rehab": "الرحاب",
    "maadi": "المعادي",
    "shorouk": "الشروق",
}


def _area_label(area: Optional[str], lang: str) -> str:
    if not area:
        return "المنطقة المختارة" if lang == "ar" else "the selected area"
    if lang == "ar":
        return _AREA_LABEL_AR.get(area.lower(), area)
    return area.title()


class TemplateGenerator:
    """
    Generates dynamic text responses without using LLMs.
    Merges database results with analytical engine math.
    """

    @staticmethod
    def generate_response(
        properties: List[Dict],
        area: str,
        budget: int,
        language: str = "en",
        compound: Optional[str] = None,
        fallback_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates the automated response text based on the top property match.

        When ``fallback_meta`` is provided the message opens with a confident,
        sales-skilled framing that acknowledges what couldn't be matched exactly
        and pitches the next-best alternative — instead of a bare "no results
        found, widen your search" dead-end.
        """
        is_arabic = language == "ar"
        area_display = _area_label(area, "ar" if is_arabic else "en")
        target_display = (
            f"{compound} في {area_display}" if is_arabic and compound else
            f"{compound} in {area_display}" if compound else area_display
        )

        # ── Truly empty result set: tiered fallback also exhausted ─────────────
        if not properties:
            if is_arabic:
                return (
                    f"بحثت في {target_display} ضمن ميزانية {budget:,.0f} جنيه، "
                    "ومش لاقي وحدات متاحة دلوقتي حتى بعد ما وسّعت البحث في المناطق "
                    "والمطورين القريبين. لو تحب، قول لي منطقة تانية تفكر فيها (مثال: "
                    "الشيخ زايد، الساحل الشمالي، 6 أكتوبر) أو زود الميزانية شوية وأنا "
                    "هرجع لك بأقوى فرصة فورًا."
                )
            return (
                f"I searched {target_display} within {budget:,.0f} EGP and even "
                "widened the search across nearby areas and developers, but I "
                "couldn't find inventory right now. If you can share an alternate "
                "area (e.g., Sheikh Zayed, North Coast, 6th October) or stretch "
                "the budget a little, I'll come back with the strongest opportunity "
                "immediately."
            )

        top_prop = properties[0]
        count = len(properties)
        prop_compound = top_prop.get("compound") or top_prop.get("developer") or (
            "مشروع ممتاز" if is_arabic else "an excellent project"
        )
        prop_location = top_prop.get("location") or area
        sale_type = (top_prop.get("sale_type") or "Primary").capitalize()
        price = top_prop.get("price", 0)
        size = top_prop.get("size_sqm", 0)
        bedrooms = top_prop.get("bedrooms", "Multiple")
        price_sqm = top_prop.get("price_per_sqm") or (price / size if size else 0)
        area_avg_price = top_prop.get("area_avg_price") or (price_sqm * 1.15)
        discount_pct = top_prop.get("bargain_percentage") or 0
        if discount_pct == 0 and area_avg_price > 0 and price_sqm > 0:
            discount_pct = ((area_avg_price - price_sqm) / area_avg_price) * 100
        osool_score = top_prop.get("osool_score", 85)
        years = top_prop.get("installment_years", 0) or 0
        dp_amt = top_prop.get("down_payment", 0) or 0
        dp_pct = (dp_amt / price) * 100 if price and dp_amt else 10

        # ── Fallback-aware opener (the marketing/sales pitch framing) ─────────
        opener = TemplateGenerator._build_fallback_opener(
            fallback_meta=fallback_meta,
            is_arabic=is_arabic,
            area_display=area_display,
            compound=compound,
            prop_compound=prop_compound,
            prop_location=prop_location,
            price=price,
            budget=budget,
            count=count,
        )

        # ── Standard pitch body ────────────────────────────────────────────────
        if is_arabic:
            deal_desc = "🏢 **المشروع:** " + f"{prop_compound} - {sale_type}\n"
            if price <= budget:
                savings = budget - price
                deal_desc += f"💰 **السعر:** {price:,.0f} جنيه ({savings/1000:,.0f} ألف أقل من ميزانيتك)\n"
            else:
                over = price - budget
                deal_desc += (
                    f"💰 **السعر:** {price:,.0f} جنيه "
                    f"(فوق ميزانيتك بـ {over/1000:,.0f} ألف فقط — بس استنى تشوف ليه يستاهل)\n"
                )
            deal_desc += f"📐 **المساحة:** {size} متر ({bedrooms} غرف)\n\n"

            why_best = "📊 **ليه دي أفضل فرصة متاحة؟**\n"
            why_best += f"سعر المتر هنا حوالي **{price_sqm:,.0f} جنيه/متر**. "
            if discount_pct > 0:
                why_best += (
                    f"متوسط المنطقة حوالي **{area_avg_price:,.0f} جنيه/متر**، "
                    f"يعني السعر أقل من السوق بحوالي **{discount_pct:.1f}%**.\n\n"
                )
            else:
                why_best += "السعر قريب من القيمة العادلة في المنطقة.\n\n"

            score_desc = f"كمان الوحدة واخدة **تقييم أصول {int(osool_score)}/100**"
            if years > 0:
                score_desc += (
                    f" لأنها بتقدم خطة سداد {years} سنوات ومقدم حوالي {int(dp_pct)}%، "
                    "وده يخلي التدفق النقدي أريح."
                )
            else:
                score_desc += " بسبب الموقع والقيمة مقارنة بالسوق."

            closer = "\n\nتحب أعرض لك تفاصيل أكتر أو أقارنها بفرصة تانية في نفس الميزانية؟"
            return opener + deal_desc + why_best + score_desc + closer

        # English
        deal_desc = f"🏢 **Project:** {prop_compound} - {sale_type}\n"
        if price <= budget:
            savings = budget - price
            deal_desc += f"💰 **Price:** {price:,.0f} EGP ({savings/1000:,.0f}k under your budget)\n"
        else:
            over = price - budget
            deal_desc += (
                f"💰 **Price:** {price:,.0f} EGP "
                f"({over/1000:,.0f}k above your budget — here's why it's worth the stretch)\n"
            )
        deal_desc += f"📐 **Size:** {size} sqm ({bedrooms} Bedrooms)\n\n"

        why_best = "📊 **Why is this the best available match?**\n"
        why_best += f"This unit is priced at **{price_sqm:,.0f} EGP/sqm**. "
        if discount_pct > 0:
            why_best += (
                f"The current area average is **{area_avg_price:,.0f} EGP/sqm**, "
                f"so you're getting a **{discount_pct:.1f}% below-market discount**.\n\n"
            )
        else:
            why_best += "This is in line with fair market value for this sector.\n\n"

        score_desc = f"Furthermore, it scores an **Osool Rating of {int(osool_score)}/100**"
        if years > 0:
            score_desc += (
                f" because it offers an extended {years}-year payment plan with "
                f"only a {int(dp_pct)}% down payment, making it highly cash-flow efficient."
            )
        else:
            score_desc += " due to its excellent location and value proposition."

        closer = "\n\nWant me to pull more details on this one, or compare it against another option in the same budget?"
        return opener + deal_desc + why_best + score_desc + closer

    @staticmethod
    def _build_fallback_opener(
        fallback_meta: Optional[Dict[str, Any]],
        is_arabic: bool,
        area_display: str,
        compound: Optional[str],
        prop_compound: str,
        prop_location: str,
        price: int,
        budget: int,
        count: int,
    ) -> str:
        """
        Build the leading framing message. For exact matches this returns the
        standard intro. For fallback tiers it acknowledges the gap and pitches
        the alternative confidently — like a skilled salesperson, not a chatbot
        that gives up.
        """
        # Exact match path
        if not fallback_meta:
            if is_arabic:
                return (
                    f"تمام. بناءً على بيانات السوق الحالية في {area_display}، "
                    f"حللت **{count} وحدة مناسبة** ضمن ميزانية {budget:,.0f} جنيه.\n\n"
                    "أفضل فرصة ظاهرة حاليًا حسب المحرك التحليلي المحلي:\n"
                )
            return (
                f"Based on current market data for {area_display}, I analyzed "
                f"**{count} matching properties** within your {budget:,.0f} EGP budget.\n\n"
                "Here's the best deal currently available based on our local analytical engine:\n"
            )

        tier = fallback_meta.get("tier")
        prop_location_display = _area_label(prop_location, "ar" if is_arabic else "en")

        # Tier 2: just-over-budget within same compound + area
        if tier == "budget_stretch":
            over = price - budget
            if is_arabic:
                return (
                    f"بصراحة، ضمن **{compound}** في {area_display} وميزانية "
                    f"{budget:,.0f} جنيه بالظبط مفيش وحدة متاحة دلوقتي — بس فيه "
                    f"وحدة قوية فوق ميزانيتك بـ **{over/1000:,.0f} ألف فقط** "
                    "ومن وجهة نظري تستاهل تتفرج عليها قبل ما تستبعد الفكرة:\n\n"
                )
            return (
                f"Within **{compound}** in {area_display} at exactly "
                f"{budget:,.0f} EGP there's nothing available right now — but "
                f"there's a strong unit just **{over/1000:,.0f}k over budget** "
                "that's genuinely worth a look before ruling it out:\n\n"
            )

        # Tier 3: same area + budget, different compound (alternative in area)
        if tier == "compound_swap":
            missing = fallback_meta.get("missing_compound") or compound
            if is_arabic:
                return (
                    f"معلش، **{missing}** في {area_display} مفيش منها وحدات متاحة "
                    f"ضمن ميزانية {budget:,.0f} جنيه دلوقتي. بس عندنا في نفس "
                    f"المنطقة وضمن ميزانيتك بالظبط فرصة ممتازة في **{prop_compound}** "
                    "— ومن واقع البيانات، هي أقوى بديل حاليًا:\n\n"
                )
            return (
                f"Heads up — **{missing}** doesn't have inventory in {area_display} "
                f"within {budget:,.0f} EGP right now. The good news: in the same "
                f"area and exactly within your budget there's a strong option in "
                f"**{prop_compound}** that, based on the data, is the strongest "
                "alternative on the table:\n\n"
            )

        # Tier 4: same compound, different area
        if tier == "area_swap":
            missing_area = _area_label(fallback_meta.get("missing_area"), "ar" if is_arabic else "en")
            if is_arabic:
                return (
                    f"**{compound}** مفيهاش وحدات في {missing_area} ضمن ميزانيتك، "
                    f"بس بنفس المطور وضمن ميزانية {budget:,.0f} جنيه عندي فرصة "
                    f"قوية في **{prop_location_display}** — ولو هدفك الاستثمار، "
                    "ده ممكن يكون أفضل في النمو الفعلي:\n\n"
                )
            return (
                f"**{compound}** doesn't have units in {missing_area} within your "
                f"budget — but the same developer has a strong opportunity in "
                f"**{prop_location_display}** within {budget:,.0f} EGP. For "
                "investment goals, this can actually outperform on growth:\n\n"
            )

        # Tier 5: swap compound + stretch budget
        if tier == "compound_swap_budget_stretch":
            missing = fallback_meta.get("missing_compound")
            over = price - budget
            missing_phrase_ar = (
                f"**{missing}** مفيش منها وحدات " if missing else "مفيش وحدات مطابقة "
            )
            missing_phrase_en = (
                f"**{missing}** doesn't have inventory " if missing else "no exact matches "
            )
            if is_arabic:
                return (
                    f"بصراحة، {missing_phrase_ar}في {area_display} ضمن ميزانية "
                    f"{budget:,.0f} جنيه. أفضل بديل لقيته في نفس المنطقة هو "
                    f"**{prop_compound}** بسعر فوق ميزانيتك بـ "
                    f"**{over/1000:,.0f} ألف فقط** — وخليني أوريك ليه يستاهل:\n\n"
                )
            return (
                f"To be straight with you, {missing_phrase_en}in {area_display} "
                f"within {budget:,.0f} EGP. The best alternative I have in the same "
                f"area is **{prop_compound}**, priced just **{over/1000:,.0f}k "
                "over budget** — let me show you why it's worth considering:\n\n"
            )

        # Tier 6: budget cap dropped entirely (closest above-budget unit in area)
        if tier == "budget_uncapped":
            original_budget = fallback_meta.get("original_budget") or budget
            over = price - original_budget
            if is_arabic:
                return (
                    f"ضمن ميزانية {original_budget:,.0f} جنيه بالظبط في "
                    f"{area_display} مفيش وحدات متاحة. أقرب فرصة قوية فوق ميزانيتك "
                    f"بـ **{over/1000:,.0f} ألف فقط** هي وحدة في **{prop_compound}** "
                    "— ولو خطة السداد مرنة، ده ممكن يكون قرار ذكي:\n\n"
                )
            return (
                f"Within exactly {original_budget:,.0f} EGP in {area_display} "
                f"there's no available inventory. The closest strong opportunity "
                f"sits just **{over/1000:,.0f}k above your stated budget** at "
                f"**{prop_compound}** — with a flexible payment plan this can "
                "still be a smart move:\n\n"
            )

        # Unknown tier — fall back to neutral intro
        if is_arabic:
            return (
                f"ضمن ميزانية {budget:,.0f} جنيه في {area_display}، أقوى فرصة "
                "ظاهرة دلوقتي:\n\n"
            )
        return (
            f"Within {budget:,.0f} EGP in {area_display}, the strongest opportunity "
            "I see right now is:\n\n"
        )


template_generator = TemplateGenerator()
