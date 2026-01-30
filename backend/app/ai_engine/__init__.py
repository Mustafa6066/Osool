# Osool AI Engine Package
# Wolf Brain Architecture V5
"""
AI Engine modules for Osool real estate platform.

New Architecture (wolf_brain V5):
- wolf_orchestrator: Main reasoning loop (WolfBrain)
- wolf_router: Fast query classification
- perception_layer: Intent extraction with GPT-4o
- analytical_engine: ROI/score calculations (no LLM)
- psychology_layer: User psychology detection

Backward compatibility:
- hybrid_brain alias -> wolf_brain
"""

# Lazy imports to avoid requiring API keys at import time
def get_wolf_brain():
    from .wolf_orchestrator import wolf_brain
    return wolf_brain

def get_hybrid_brain():
    from .wolf_orchestrator import hybrid_brain
    return hybrid_brain

# Direct imports for non-API modules
from .psychology_layer import (
    analyze_psychology, 
    determine_strategy,
    PsychologyProfile,
    PsychologicalState,
    Strategy
)

__all__ = [
    "get_wolf_brain",
    "get_hybrid_brain",
    "analyze_psychology",
    "determine_strategy",
    "PsychologyProfile", 
    "PsychologicalState",
    "Strategy",
]
