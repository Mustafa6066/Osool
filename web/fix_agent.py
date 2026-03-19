import os

replacements = {
    # AgentInterface.tsx specifics
    "Ø´ØºÙ‘Ù„ ØªÙ‚ÙŠÙŠÙ… AI Ø¹Ù„Ù‰": "شغّل تقييم AI على",
    "ÙÙŠ ": "في ",
    " - Ø³Ø¹Ø±Ù‡ ": " - سعره ",
    " Ù…Ù„ÙŠÙˆÙ† Ø¬Ù†ÙŠÙ‡": " مليون جنيه",
    "mÂ²": "m²",
}

fpath = 'components/AgentInterface.tsx'

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
    
for bad, good in replacements.items():
    content = content.replace(bad, good)
    
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
    print(f"Fixed {fpath}")

