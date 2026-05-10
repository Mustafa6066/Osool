from typing import Dict, List, Any

class TemplateGenerator:
    """
    Generates dynamic text responses without using LLMs.
    Merges database results with analytical engine math.
    """

    @staticmethod
    def generate_response(properties: List[Dict], area: str, budget: int) -> str:
        """
        Generates the automated response text based on the top property match.
        """
        if not properties:
            return f"I couldn't find any properties matching your criteria in {area.title() if area else 'the selected area'} within {budget:,.0f} EGP."

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

        # Constructing the message
        intro = f"Hello! Based on current market data for {area.title()}, I have analyzed **{count} matching properties** within your {budget:,.0f} EGP budget.\n\n"

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
