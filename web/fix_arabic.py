# -*- coding: utf-8 -*-
import os

replacements = {
    # RealityCheck.tsx
    "ØªÙ†Ø¨ÙŠÙ‡ Ø°ÙƒÙŠ": "تنبيه ذكي",
    "Ù†ØµÙŠØØ©": "نصيحة",
    "ðŸ’¡ Ø¨Ø¯Ø§Ø¦Ù„ Ø°ÙƒÙŠØ© ØªÙ†Ø§Ø³Ø¨ Ù…ÙŠØ²Ø§Ù†ÙŠØªÙƒ Ø§Ù„ØÙ‚ÙŠÙ‚ÙŠØ©": "💡 بدائل ذكية تناسب ميزانيتك الحقيقية",
    "Ø§Ø³ØªÙƒØ´Ù": "استكشف",
    
    # La2taAlert.tsx
    "Ù„Ù‚Ø·Ø©!": "لقطة!",
    "ÙŠÙ†ØªÙ‡ÙŠ": "ينتهي",
    "ÙØ±ØµØ©": "فرصة",
    "Ø£ÙØ¶Ù„": "أفضل",
    "ØºØ±Ù": "غرف",
    "ÙˆÙÙ‘Ø±": "وفّر",
    "Ù„Ù‚Ø·Ø§Øª Ø£Ø®Ø±Ù‰": "لقطات أخرى",
    "â€¢": "•",
    
    # UnifiedAnalytics.tsx
    "ØªÙ‚ÙŠÙŠÙ…": "تقييم",
    "Ø¹Ù‚Ø§Ø±": "عقار",
    "Ù…ØªØ±Â²": "متر²",
    "Ø«Ù‚Ø©": "ثقة",
    "ØÙ…Ø§ÙŠØ©": "حماية",
    "Ø§Ù„Ø¹Ù‚Ø§Ø±": "العقار",
    "Ø³Ø¹Ø± Ø§Ù„Ù…ØªØ±": "سعر المتر",
    "Ø§Ù„Ù†Ù…Ùˆ": "النمو",
    "ØªÙØ§ØµÙŠÙ„ Ø¥Ø¶Ø§ÙÙŠØ©": "تفاصيل إضافية",
    "ØªØÙ„ÙŠÙ„Ø§Øª Ø°ÙƒÙŠØ©": "تحليلات ذكية",
}

files = [
    'components/visualizations/La2taAlert.tsx',
    'components/visualizations/RealityCheck.tsx',
    'components/visualizations/UnifiedAnalytics.tsx'
]

for fpath in files:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for bad, good in replacements.items():
            content = content.replace(bad, good)
            
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
            print(f"Fixed {fpath}")

