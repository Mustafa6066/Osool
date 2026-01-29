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

        # 4a. BANK/CASH/CERTIFICATE OBJECTION KILLER (HIGHEST PRIORITY)
        # In Egypt, the #1 competitor is bank certificates (27% interest).
        # When user mentions bank/cash/certificates, show Inflation Killer immediately.
        if memory:
            objections_str = str(getattr(memory, 'objections_raised', [])).lower()
            user_query = str(getattr(memory, 'last_query', '')).lower()
            combined_text = objections_str + ' ' + user_query
            
            bank_keywords = ['bank', 'interest', 'cash', 'saving', 'certificate', 'cd ', 
                           'شهادات', 'بنك', 'فوايد', 'فوائد', 'كاش', 'سيولة', 'ادخار']
            
            if any(k in combined_text for k in bank_keywords):
                # Force inflation killer at HIGHEST priority for bank savers
                if not any(a['type'] == 'inflation_killer' for a in actions):
                    investment_amount = 5000000  # Default 5M
                    if properties:
                        investment_amount = properties[0].get('price', 5000000)
                    
                    actions.insert(0, {
                        'type': 'inflation_killer',
                        'data': {
                            'initial_investment': investment_amount,
                            'years': 5,
                            'cash_erosion': '28%',
                            'property_growth': '18%',
                            'message_ar': 'البنك بيديك 27% فوايد، بس التضخم 33%. يعني بتخسر 6% سنوياً! العقار بيحميك.',
                            'message_en': 'Bank gives 27% interest, but inflation is 33%. You lose 6% yearly! Property protects you.',
                            'bank_rate': 27,
                            'real_return': -6,
                        },
                        'priority': 12,  # HIGHEST PRIORITY - above all others
                        'trigger_reason': 'Memory: Bank/Certificate/Cash objection detected in conversation'
                    })
                    logger.info(f"WOLF: Triggered inflation_killer for bank objection: {combined_text[:50]}...")

        # 4b. Psychology-driven actions - EGYPTIAN FEAR/GREED OPTIMIZATION
        if psychology:
            psych_state = getattr(psychology, 'primary_state', None)
            psych_value = psych_state.value if psych_state else ''
            detected_triggers = getattr(psychology, 'detected_triggers', [])

            # THE INFLATION KILLER (For the "Hesitant Saver")
            # In Egypt, everyone is afraid their cash is burning due to devaluation
            if psych_value in ['RISK_AVERSE', 'ANALYSIS_PARALYSIS']:
                actions.append({
                    'type': 'inflation_killer',
                    'data': {
                        'cash_erosion': '28%',  # Egyptian inflation assumption
                        'property_growth': '18%',
                        'initial_investment': properties[0].get('price', 5000000) if properties else 5000000,
                        'years': 5,
                        'message_ar': 'شوف إيه هيحصل لـ 1 مليون في البنك vs. العقار ده على 5 سنين.',
                        'message_en': 'See what happens to 1M EGP in the bank vs. this property over 5 years.',
                        'bank_rate': 27,  # Current Egyptian bank CD rate
                        'real_return': -6,  # 27% interest - 33% inflation = -6% real return
                    },
                    'priority': 10,  # TOP PRIORITY for hesitant users
                    'trigger_reason': 'Psychology: User scared of losing money (risk_averse/analysis_paralysis)'
                })

            # THE "LA2TA" ALERT (For the "Greed Driven" or FOMO users)
            if psych_value == 'GREED_DRIVEN' or 'FOMO' in str(detected_triggers):
                # Find the property with highest ROI or wolf_score
                if properties:
                    best_deal = max(properties, key=lambda x: x.get('wolf_score', 0) or x.get('roi', 0))
                    actions.append({
                        'type': 'la2ta_alert',
                        'data': {
                            'properties': [best_deal],
                            'discount_badge': 'UNDER_MARKET_PRICE',
                            'timer': '48H',  # Artificial urgency (typical Egyptian sales tactic)
                            'wolf_score': best_deal.get('wolf_score', 85),
                            'savings': best_deal.get('savings', 250000),
                            'urgency_level': 'high',
                            'message_ar': f'🐺 لقطة! الوحدة دي تحت السوق - فاضل 48 ساعة بس',
                            'message_en': f'🐺 CATCH! This unit is below market - 48 hours only',
                        },
                        'priority': 10,  # TOP PRIORITY for greedy users
                        'trigger_reason': 'Psychology: FOMO/GREED detected - show urgency'
                    })

            # THE LAW 114 GUARDIAN (For the "Trust Deficit" users)
            if psych_value == 'TRUST_DEFICIT':
                actions.append({
                    'type': 'law_114_guardian',
                    'data': {
                        'status': 'ready',
                        'cta_text_ar': 'ارفع أي عقد وأنا هلاقي البنود المخفية.',
                        'cta_text_en': 'Upload any draft contract. I will find the hidden fees.',
                        'capabilities': [
                            'كشف البنود المخفية (Hidden Clause Detection)',
                            'التحقق من مخالفات قانون 114',
                            'مراجعة شروط الجزاءات',
                            'تحليل جدول السداد'
                        ],
                        'trust_badges': ['AI-Powered', 'Law 114 Compliant', 'Bank-Grade Security'],
                    },
                    'priority': 11,  # HIGHEST PRIORITY to build trust first
                    'trigger_reason': 'Psychology: TRUST_DEFICIT - show legal protection'
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
