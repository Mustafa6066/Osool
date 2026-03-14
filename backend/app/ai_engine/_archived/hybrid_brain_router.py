"""
Osool Hybrid Brain - Multi-Model AI Orchestrator
-------------------------------------------------
Combines Claude 3.5 Sonnet and GPT-4o for optimal performance.

Architecture:
- Router Pattern: Analyzes intent and routes to best model
- Claude: Complex reasoning, property analysis, Arabic language
- GPT-4o: Quick responses, creative content, general queries

Phase 1: Real Estate AI Advisor with Hybrid Intelligence
"""

import os
import json
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv

# AI Clients
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

load_dotenv()


class ModelRoute(Enum):
    """Model routing decisions."""
    CLAUDE = "claude"       # Complex reasoning, Arabic, property analysis
    GPT = "gpt"            # Quick responses, general queries
    HYBRID = "hybrid"      # Use both (Claude generates, GPT reviews)


class HybridBrain:
    """
    Osool's Hybrid AI Brain - Combines Claude + GPT intelligently.
    
    Routing Logic:
    - CLAUDE: Property search, valuation, Arabic, complex analysis, legal
    - GPT: Simple greetings, general chat, quick questions
    - HYBRID: High-stakes decisions (reservation, contracts)
    """
    
    def __init__(self):
        # Initialize clients
        self.claude_client = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ) if os.getenv("ANTHROPIC_API_KEY") else None
        
        self.gpt_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        ) if os.getenv("OPENAI_API_KEY") else None
        
        # Model configurations
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
        self.gpt_model = os.getenv("GPT_MODEL", "gpt-4o")
        self.router_model = "gpt-4o-mini"  # Fast routing decisions
        
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # Route-specific keywords
        self.claude_keywords = [
            # Arabic
            "أريد", "ابحث", "شقة", "فيلا", "عقار", "سعر", "تحليل",
            # Complex tasks
            "analyze", "valuation", "roi", "investment", "compare",
            "contract", "legal", "mortgage", "calculate", "search",
            "property", "compound", "developer", "payment plan"
        ]
        
        self.gpt_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "bye",
            "what is", "who are", "tell me about", "مرحبا", "شكرا"
        ]
        
        print("✅ [Hybrid Brain] Initialized with Claude + GPT")
    
    def _detect_route(self, prompt: str, context: Optional[str] = None) -> ModelRoute:
        """
        Determine which model to use based on prompt analysis.
        Fast, rule-based routing (no LLM call overhead).
        """
        prompt_lower = prompt.lower()
        
        # Check for complex/Claude keywords
        claude_score = sum(1 for kw in self.claude_keywords if kw in prompt_lower)
        gpt_score = sum(1 for kw in self.gpt_keywords if kw in prompt_lower)
        
        # Arabic text detection (Claude is better at Arabic)
        arabic_chars = sum(1 for c in prompt if '\u0600' <= c <= '\u06FF')
        if arabic_chars > len(prompt) * 0.3:
            claude_score += 5
        
        # Length-based heuristic (longer = more complex)
        if len(prompt) > 200:
            claude_score += 2
        
        # High-stakes keywords trigger Hybrid mode
        high_stakes = ["reserve", "book", "contract", "sign", "payment", "deposit"]
        if any(kw in prompt_lower for kw in high_stakes):
            return ModelRoute.HYBRID
        
        # Route decision
        if claude_score > gpt_score:
            return ModelRoute.CLAUDE
        elif gpt_score > claude_score:
            return ModelRoute.GPT
        else:
            # Default to Claude for real estate domain
            return ModelRoute.CLAUDE
    
    async def _call_claude(
        self,
        prompt: str,
        system_prompt: str,
        chat_history: List[Dict] = None,
        max_tokens: int = 4096
    ) -> str:
        """Call Claude 3.5 Sonnet for complex reasoning."""
        if not self.claude_client:
            raise ValueError("Claude client not initialized")
        
        messages = []
        if chat_history:
            for msg in chat_history:
                if isinstance(msg, dict):
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        
        # Track tokens
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        
        return response.content[0].text
    
    async def _call_gpt(
        self,
        prompt: str,
        system_prompt: str,
        chat_history: List[Dict] = None,
        max_tokens: int = 4096
    ) -> str:
        """Call GPT-4o for general/quick responses."""
        if not self.gpt_client:
            raise ValueError("GPT client not initialized")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            for msg in chat_history:
                if isinstance(msg, dict):
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.gpt_client.chat.completions.create(
            model=self.gpt_model,
            max_tokens=max_tokens,
            messages=messages
        )
        
        # Track tokens
        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens
        
        return response.choices[0].message.content
    
    async def _call_hybrid(
        self,
        prompt: str,
        system_prompt: str,
        chat_history: List[Dict] = None
    ) -> str:
        """
        Hybrid mode: Claude generates, GPT reviews.
        Used for high-stakes decisions.
        """
        # Step 1: Claude generates primary response
        claude_response = await self._call_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            chat_history=chat_history
        )
        
        # Step 2: GPT reviews for accuracy/clarity
        review_prompt = f"""Review this real estate advisory response for:
1. Accuracy of any numbers/prices
2. Clarity of explanation
3. Missing important information

Original user question: {prompt}

Response to review:
{claude_response}

If the response is good, return it unchanged. If improvements are needed, provide the improved version."""

        reviewed_response = await self._call_gpt(
            prompt=review_prompt,
            system_prompt="You are a quality reviewer for a real estate AI advisor. Be concise.",
            max_tokens=2048
        )
        
        return reviewed_response
    
    async def think(
        self,
        user_input: str,
        system_prompt: str,
        chat_history: List[Dict] = None,
        force_route: Optional[ModelRoute] = None
    ) -> Dict[str, Any]:
        """
        Main thinking function - routes to appropriate model.
        
        Args:
            user_input: User's message
            system_prompt: System instructions
            chat_history: Previous conversation
            force_route: Force a specific route (optional)
        
        Returns:
            Dict with response, model_used, and routing info
        """
        start_time = datetime.now()
        
        # Determine route
        route = force_route or self._detect_route(user_input)
        
        try:
            if route == ModelRoute.CLAUDE:
                response = await self._call_claude(
                    prompt=user_input,
                    system_prompt=system_prompt,
                    chat_history=chat_history
                )
                model_used = f"Claude ({self.claude_model})"
                
            elif route == ModelRoute.GPT:
                response = await self._call_gpt(
                    prompt=user_input,
                    system_prompt=system_prompt,
                    chat_history=chat_history
                )
                model_used = f"GPT ({self.gpt_model})"
                
            else:  # HYBRID
                response = await self._call_hybrid(
                    prompt=user_input,
                    system_prompt=system_prompt,
                    chat_history=chat_history
                )
                model_used = "Hybrid (Claude + GPT)"
            
            latency = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response,
                "model_used": model_used,
                "route": route.value,
                "latency_seconds": round(latency, 2),
                "tokens": {
                    "input": self.total_input_tokens,
                    "output": self.total_output_tokens
                }
            }
            
        except Exception as e:
            # Fallback: try the other model
            fallback_route = ModelRoute.GPT if route == ModelRoute.CLAUDE else ModelRoute.CLAUDE
            print(f"⚠️ [Hybrid Brain] {route.value} failed, falling back to {fallback_route.value}: {e}")
            
            try:
                if fallback_route == ModelRoute.GPT:
                    response = await self._call_gpt(
                        prompt=user_input,
                        system_prompt=system_prompt,
                        chat_history=chat_history
                    )
                else:
                    response = await self._call_claude(
                        prompt=user_input,
                        system_prompt=system_prompt,
                        chat_history=chat_history
                    )
                
                return {
                    "response": response,
                    "model_used": f"Fallback ({fallback_route.value})",
                    "route": fallback_route.value,
                    "error": str(e)
                }
            except Exception as fallback_error:
                return {
                    "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                    "model_used": "None",
                    "route": "error",
                    "error": str(fallback_error)
                }
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(
                (self.total_input_tokens * 3.0 / 1_000_000) +  # Claude input
                (self.total_output_tokens * 15.0 / 1_000_000),  # Claude output
                4
            )
        }


# Singleton instance
hybrid_brain = HybridBrain()


# Convenience function for direct usage
async def think(
    user_input: str,
    system_prompt: str,
    chat_history: List[Dict] = None
) -> Dict[str, Any]:
    """Quick access to hybrid brain thinking."""
    return await hybrid_brain.think(
        user_input=user_input,
        system_prompt=system_prompt,
        chat_history=chat_history
    )
