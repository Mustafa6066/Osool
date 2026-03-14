"""
Batch Analytics - Offline Market Intelligence via Anthropic Batch API
---------------------------------------------------------------------
Uses Claude's Message Batches API for cost-efficient offline processing:
- 50% cost reduction vs real-time API
- Market trend reports
- Bulk property valuation scoring
- Competitor analysis

Usage:
    from app.ai_engine.batch_analytics import batch_engine
    
    job_id = await batch_engine.submit_market_report(areas=["New Cairo", "Sheikh Zayed"])
    results = await batch_engine.poll_results(job_id)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class BatchAnalyticsEngine:
    """
    Leverages Claude's Message Batches API for offline market intelligence.
    
    Benefits:
    - 50% cheaper than real-time API ($1.50/$7.50 per 1M tokens for Sonnet 4.5)
    - Higher rate limits (dedicated processing pool)
    - Results within 24 hours (usually much faster)
    - Ideal for nightly/weekly market reports
    """

    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self._pending_jobs: Dict[str, dict] = {}

    async def submit_market_report(
        self,
        areas: List[str],
        report_type: str = "weekly_summary",
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Submit a batch job to generate market reports for multiple areas.
        
        Args:
            areas: List of area names (e.g., ["New Cairo", "Sheikh Zayed"])
            report_type: Type of report (weekly_summary, trend_analysis, competitor_audit)
            extra_context: Optional additional context (e.g., recent DB stats)
            
        Returns:
            Batch job ID for polling results later.
        """
        requests = []
        
        for i, area in enumerate(areas):
            system_prompt = self._get_report_system_prompt(report_type)
            user_prompt = self._get_report_user_prompt(area, report_type, extra_context)
            
            requests.append({
                "custom_id": f"market_report_{area.lower().replace(' ', '_')}_{i}",
                "params": {
                    "model": self.model,
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ],
                },
            })
        
        try:
            batch = await self.anthropic.messages.batches.create(requests=requests)
            
            self._pending_jobs[batch.id] = {
                "created_at": datetime.now().isoformat(),
                "areas": areas,
                "report_type": report_type,
                "status": "processing",
                "request_count": len(requests),
            }
            
            logger.info(f"📊 Batch job submitted: {batch.id} ({len(requests)} reports for {areas})")
            return batch.id
            
        except Exception as e:
            logger.error(f"Batch submission failed: {e}", exc_info=True)
            raise

    async def submit_bulk_valuation(
        self,
        properties: List[Dict],
    ) -> str:
        """
        Submit bulk property valuation scoring.
        
        Each property gets an AI-generated market analysis + fair value estimate.
        Much cheaper than real-time for batch processing (e.g., nightly scoring).
        
        Args:
            properties: List of property dicts with location, price, size_sqm, etc.
            
        Returns:
            Batch job ID.
        """
        requests = []
        
        system_prompt = """You are a Senior Egyptian Real Estate Analyst.
Analyze this property and provide a market-calibrated valuation.

Return JSON:
{
    "fair_value_min": int,
    "fair_value_max": int,
    "price_per_sqm_assessment": "below_market" | "fair" | "above_market",
    "investment_score": 0-100,
    "key_factors": ["factor1", "factor2"],
    "recommendation": "string"
}"""
        
        for i, prop in enumerate(properties):
            user_prompt = f"""Analyze this property:
- Location: {prop.get('location', 'Unknown')}
- Price: {prop.get('price', 0):,} EGP
- Size: {prop.get('size_sqm', 0)} sqm
- Bedrooms: {prop.get('bedrooms', 'N/A')}
- Developer: {prop.get('developer', 'Unknown')}
- Property Type: {prop.get('property_type', 'apartment')}
- Price/sqm: {prop.get('price_per_sqm', 0):,} EGP"""
            
            requests.append({
                "custom_id": f"valuation_{prop.get('id', i)}",
                "params": {
                    "model": self.model,
                    "max_tokens": 1024,
                    "temperature": 0.2,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            })
        
        try:
            batch = await self.anthropic.messages.batches.create(requests=requests)
            
            self._pending_jobs[batch.id] = {
                "created_at": datetime.now().isoformat(),
                "type": "bulk_valuation",
                "property_count": len(properties),
                "status": "processing",
            }
            
            logger.info(f"📊 Bulk valuation batch submitted: {batch.id} ({len(properties)} properties)")
            return batch.id
            
        except Exception as e:
            logger.error(f"Bulk valuation batch failed: {e}", exc_info=True)
            raise

    async def get_batch_status(self, batch_id: str) -> Dict:
        """Check the status of a batch job."""
        try:
            batch = await self.anthropic.messages.batches.retrieve(batch_id)
            status = {
                "id": batch.id,
                "processing_status": batch.processing_status,
                "request_counts": {
                    "processing": batch.request_counts.processing,
                    "succeeded": batch.request_counts.succeeded,
                    "errored": batch.request_counts.errored,
                    "canceled": batch.request_counts.canceled,
                    "expired": batch.request_counts.expired,
                },
                "created_at": batch.created_at if hasattr(batch, 'created_at') else None,
            }
            
            # Update local tracking
            if batch_id in self._pending_jobs:
                self._pending_jobs[batch_id]["status"] = batch.processing_status
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            return {"id": batch_id, "error": str(e)}

    async def get_batch_results(self, batch_id: str) -> List[Dict]:
        """
        Retrieve results for a completed batch job.
        
        Returns list of result dicts with custom_id and response content.
        """
        results = []
        
        try:
            async for result in self.anthropic.messages.batches.results(batch_id):
                entry = {
                    "custom_id": result.custom_id,
                    "type": result.result.type,
                }
                
                if result.result.type == "succeeded":
                    message = result.result.message
                    text = ""
                    for block in message.content:
                        if block.type == "text":
                            text += block.text
                    
                    # Try to parse as JSON
                    try:
                        entry["data"] = json.loads(text)
                    except json.JSONDecodeError:
                        entry["data"] = {"text": text}
                    
                    entry["usage"] = {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens,
                    }
                elif result.result.type == "errored":
                    entry["error"] = str(result.result.error)
                
                results.append(entry)
            
            logger.info(f"📊 Batch {batch_id}: Retrieved {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get batch results: {e}", exc_info=True)
            return []

    def _get_report_system_prompt(self, report_type: str) -> str:
        """Get system prompt for a specific report type."""
        base = """You are an expert Egyptian Real Estate Market Analyst.
Provide data-driven analysis with specific numbers and trends.
Always reference EGP (Egyptian Pounds) for prices.
Include year-over-year comparisons where applicable."""
        
        if report_type == "weekly_summary":
            return base + """
Generate a weekly market summary covering:
1. Price trends (avg price/sqm changes)
2. Supply/demand balance
3. Top performing developers
4. Notable new launches
5. Key takeaways for investors and buyers

Return well-structured markdown report."""
            
        elif report_type == "trend_analysis":
            return base + """
Provide deep trend analysis covering:
1. 3-month price trajectory
2. Volume trends (listings vs closings)
3. Macro factors (inflation, interest rates, USD/EGP)
4. Government policy impact
5. Infrastructure development timeline
6. Investment opportunities and risks

Return well-structured markdown report with data visualizations described."""
            
        elif report_type == "competitor_audit":
            return base + """
Analyze the competitive landscape:
1. Top 10 developers by market share
2. New product launches this month
3. Pricing strategies comparison
4. Sales velocity by developer
5. Market positioning (luxury vs affordable)

Return well-structured markdown report."""
        
        return base

    def _get_report_user_prompt(
        self, area: str, report_type: str, extra_context: Optional[str]
    ) -> str:
        """Build the user prompt for a specific area report."""
        prompt = f"Generate a {report_type.replace('_', ' ')} for the **{area}** area in Egypt's real estate market."
        
        if extra_context:
            prompt += f"\n\nAdditional context from our database:\n{extra_context}"
        
        prompt += "\n\nBe specific with numbers and data points. Avoid generic statements."
        return prompt

    def get_pending_jobs(self) -> Dict[str, dict]:
        """Get all tracked pending jobs."""
        return dict(self._pending_jobs)


# Singleton instance
batch_engine = BatchAnalyticsEngine()

__all__ = ["BatchAnalyticsEngine", "batch_engine"]
