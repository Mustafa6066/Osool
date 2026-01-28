"""
Osool Analytical Actions Engine
-------------------------------
Generates enhanced UI actions based on deep analysis results and user psychology.
Converts GPT-4o analysis output into prioritized frontend visualization triggers.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_analytical_ui_actions(
    deep_analysis: Dict[str, Any],
    psychology: Any,
    properties: List[Dict],
    memory: Optional[Any] = None
) -> List[Dict]:
    """
    Generate UI actions driven by deep analysis results.

    Args:
        deep_analysis: Structured analysis from GPT-4o deep analysis stage
        psychology: PsychologyProfile from psychology layer
        properties: List of property dicts from search
        memory: Optional ConversationMemory for context

    Returns:
        List of UI action dicts sorted by priority
    """
    actions = []

    try:
        # 1. Investment Scorecard from comparative analysis
        comparative = deep_analysis.get('comparative_analysis', {})
        if comparative and comparative.get('best_value'):
            actions.append({
                'type': 'investment_scorecard',
                'data': {
                    'comparative_analysis': comparative,
                    'confidence': deep_analysis.get('confidence', 0.7),
                    'key_insight': deep_analysis.get('key_insight', ''),
                },
                'priority': 9,
                'trigger_reason': 'Deep analysis found comparative insights'
            })

        # 2. Reality Check if risks detected
        risks = deep_analysis.get('risks', [])
        if risks:
            actions.append({
                'type': 'reality_check',
                'data': {
                    'risks': risks,
                    'risk_count': len(risks),
                    'recommended_action': deep_analysis.get('recommended_action', 'evaluate'),
                    'confidence': deep_analysis.get('confidence', 0.7),
                },
                'priority': 8,
                'trigger_reason': f'Deep analysis detected {len(risks)} risk(s)'
            })

        # 3. Opportunity Alert if opportunities found
        opportunities = deep_analysis.get('opportunities', [])
        if opportunities:
            actions.append({
                'type': 'la2ta_alert',
                'data': {
                    'opportunities': opportunities,
                    'key_insight': deep_analysis.get('key_insight', ''),
                    'urgency_level': 'high' if deep_analysis.get('confidence', 0) > 0.8 else 'medium',
                    'message_ar': f'تحليل معمق: {deep_analysis.get("key_insight", "فرصة استثمارية")}',
                    'message_en': f'Deep Analysis: {deep_analysis.get("key_insight", "Investment opportunity")}',
                },
                'priority': 10,
                'trigger_reason': 'Deep analysis found opportunities'
            })

        # 4. Psychology-driven actions
        if psychology:
            psych_state = getattr(psychology, 'primary_state', None)
            psych_value = psych_state.value if psych_state else ''

            if psych_value == 'GREED_DRIVEN':
                actions.append({
                    'type': 'roi_calculator',
                    'data': {
                        'properties': properties[:3],
                        'deep_analysis_roi': deep_analysis.get('comparative_analysis', {}).get('best_growth'),
                        'recommended_action': deep_analysis.get('recommended_action', 'evaluate'),
                    },
                    'priority': 9,
                    'trigger_reason': 'Psychology: GREED_DRIVEN + deep analysis'
                })

            elif psych_value == 'RISK_AVERSE':
                actions.append({
                    'type': 'law_114_guardian',
                    'data': {
                        'risks': risks,
                        'safest_option': comparative.get('safest'),
                        'confidence': deep_analysis.get('confidence', 0.7),
                    },
                    'priority': 8,
                    'trigger_reason': 'Psychology: RISK_AVERSE + risk analysis'
                })

            elif psych_value == 'FOMO':
                actions.append({
                    'type': 'inflation_killer',
                    'data': {
                        'opportunities': opportunities,
                        'urgency': 'high',
                        'recommended_action': deep_analysis.get('recommended_action'),
                    },
                    'priority': 10,
                    'trigger_reason': 'Psychology: FOMO + opportunity detected'
                })

        # 5. Memory-driven actions
        if memory:
            investment_purpose = getattr(memory, 'investment_vs_living', None)
            objections = getattr(memory, 'objections_raised', [])

            if investment_purpose in ('investment', 'both'):
                if not any(a['type'] == 'roi_calculator' for a in actions):
                    actions.append({
                        'type': 'roi_calculator',
                        'data': {'properties': properties[:3]},
                        'priority': 8,
                        'trigger_reason': 'Memory: investor profile'
                    })

            if any('price' in obj.lower() or 'غالي' in obj for obj in objections):
                actions.insert(0, {
                    'type': 'payment_plan_analysis',
                    'data': {'properties': properties},
                    'priority': 10,
                    'trigger_reason': 'Memory: price objection raised'
                })

            shown_count = len(getattr(memory, 'shown_properties', []))
            if shown_count >= 2:
                if not any(a['type'] == 'comparison_matrix' for a in actions):
                    actions.append({
                        'type': 'comparison_matrix',
                        'data': {'properties': properties[:4]},
                        'priority': 9,
                        'trigger_reason': 'Memory: multiple properties shown'
                    })

    except Exception as e:
        logger.error(f"Analytical actions generation failed: {e}")

    # Sort by priority and limit
    return sorted(actions, key=lambda x: x.get('priority', 0), reverse=True)[:4]
