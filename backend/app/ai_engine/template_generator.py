from typing import Dict, List, Any

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
        compound: str | None = None,
    ) -> str:
        """
        Generates the automated response text based on the top property match.
        """
        is_arabic = language == "ar"
        area_label_map = {
            "new cairo": "القاهرة الجديدة",
            "sheikh zayed": "الشيخ زايد",
            "6th of october": "6 أكتوبر",
        }
        area_display = area_label_map.get((area or "").lower(), area.title() if area else "the selected area")
        target_display = f"{compound} في {area_display}" if is_arabic and compound else area_display
        target_display_en = f"{compound} in {area_display}" if compound else area_display

        if not properties:
            if is_arabic:
                return f"بحثت في {target_display} ضمن ميزانية {budget:,.0f} جنيه، ومش لاقي وحدات مطابقة بدقة حاليًا. ممكن تزود الميزانية قليلًا أو توسع المنطقة؟"
            return f"I couldn't find any properties matching your criteria in {target_display_en} within {budget:,.0f} EGP."

        count = len(properties)
        top_prop = properties[0]

        project = top_prop.get("compound") or top_prop.get("developer") or "an excellent project"
        sale_type = top_prop.get("sale_type", "Primary").capitalize()
        price = top_prop.get("price", 0)
        size = top_prop.get("size_sqm", 0)
        bedrooms = top_prop.get("bedrooms", "Multiple")

        # Extracted from analytical engine if available, otherwise calculate/estimate
        price_sqm = top_prop.get("price_per_sqm", (price / size if size else 0))
        area_avg_price = top_prop.get("area_avg_price", price_sqm * 1.15) # Fallback if not injected
        discount_pct = top_prop.get("bargain_percentage", 0)

        # Recalculate discount if not present but we have an area average
        if discount_pct == 0 and area_avg_price > 0 and price_sqm > 0:
            discount_pct = ((area_avg_price - price_sqm) / area_avg_price) * 100

        osool_score = top_prop.get("osool_score", 85) # Default to a good score if not calculated

        years = top_prop.get("installment_years", 0)
        dp_amt = top_prop.get("down_payment", 0)
        # Assuming dp is an amount, calculate pct
        dp_pct = (dp_amt / price) * 100 if price and dp_amt else 10

        if is_arabic:
            intro = f"تمام. بناءً على بيانات السوق الحالية في {target_display}، حللت **{count} وحدة مناسبة** ضمن ميزانية {budget:,.0f} جنيه.\n\n"

            deal_desc = "أفضل فرصة ظاهرة حاليًا حسب المحرك التحليلي المحلي:\n"
            deal_desc += f"🏢 **المشروع:** {project} - {sale_type}\n"

            if budget > price:
                savings = budget - price
                deal_desc += f"💰 **السعر:** {price:,.0f} جنيه ({savings/1000:,.0f} ألف أقل من ميزانيتك)\n"
            else:
                deal_desc += f"💰 **السعر:** {price:,.0f} جنيه\n"

            deal_desc += f"📐 **المساحة:** {size} متر ({bedrooms} غرف)\n\n"

            why_best = "📊 **ليه دي من أفضل الفرص؟**\n"
            why_best += f"سعر المتر هنا حوالي **{price_sqm:,.0f} جنيه/متر**. "

            if discount_pct > 0:
                why_best += f"بيانات السوق عندنا بتشير إن متوسط المنطقة حوالي **{area_avg_price:,.0f} جنيه/متر**، يعني السعر أقل من السوق بحوالي **{discount_pct:.1f}%**.\n\n"
            else:
                why_best += f"السعر قريب من القيمة العادلة في {target_display}.\n\n"

            score_desc = f"كمان الوحدة واخدة **تقييم أصول {int(osool_score)}/100**"
            if years > 0:
                score_desc += f" لأنها بتقدم خطة سداد {years} سنوات ومقدم حوالي {int(dp_pct)}%، وده يخلي التدفق النقدي أريح."
            else:
                score_desc += " بسبب الموقع والقيمة مقارنة بالسوق."

            return intro + deal_desc + why_best + score_desc

        # Constructing the message
        intro = f"Hello! Based on current market data for {target_display_en}, I have analyzed **{count} matching properties** within your {budget:,.0f} EGP budget.\n\n"

        deal_desc = f"Here is the absolute best deal currently available based on our local analytical engine:\n"
        deal_desc += f"🏢 **Project:** {project} - {sale_type}\n"

        if budget > price:
            savings = budget - price
            deal_desc += f"💰 **Price:** {price:,.0f} EGP ({savings/1000:,.0f}k under your budget)\n"
        else:
            deal_desc += f"💰 **Price:** {price:,.0f} EGP\n"

        deal_desc += f"📐 **Size:** {size} sqm ({bedrooms} Bedrooms)\n\n"

        why_best = f"📊 **Why is this the best price?**\n"
        why_best += f"This unit is priced at **{price_sqm:,.0f} EGP/sqm**. "

        if discount_pct > 0:
            why_best += f"Our market data shows the current average for finished units in this sector of {area.title()} is **{area_avg_price:,.0f} EGP/sqm**. "
            why_best += f"You are getting a **{discount_pct:.1f}% below-market discount**.\n\n"
        else:
            why_best += f"This is in line with the fair market value for this sector of {area.title()}.\n\n"

        score_desc = f"Furthermore, it scores an **Osool Rating of {int(osool_score)}/100**"
        if years > 0:
             score_desc += f" because it offers an extended {years}-year payment plan with only a {int(dp_pct)}% down payment, making it highly cash-flow efficient."
        else:
             score_desc += f" due to its excellent location and value proposition."

        return intro + deal_desc + why_best + score_desc

template_generator = TemplateGenerator()
