import os
import re

files = [
    'components/AgentInterface.tsx',
    'components/dock/LiquidDock.tsx',
    'components/dock/DockContextPanel.tsx',
    'components/LanguageToggle.tsx'
]

def replace_classes(content):
    mapping = {
        'ml-': 'ms-', 'mr-': 'me-', 'pl-': 'ps-', 'pr-': 'pe-',
        'left-': 'start-', 'right-': 'end-',
        'border-l-': 'border-s-', 'border-r-': 'border-e-',
        'rounded-l-': 'rounded-s-', 'rounded-r-': 'rounded-e-',
        'rounded-tl-': 'rounded-ts-', 'rounded-tr-': 'rounded-te-',
        'rounded-bl-': 'rounded-bs-', 'rounded-br-': 'rounded-be-'
    }
    
    new_content = content
    for old, new_prefix in mapping.items():
        new_content = re.sub(r'(?<=[\s\"\'\`:\-])' + old + r'([\w\-\.\[\]\%]+)', new_prefix + r'\1', new_content)
        new_content = re.sub(r'(?<=^)' + old + r'([\w\-\.\[\]\%]+)', new_prefix + r'\1', new_content, flags=re.MULTILINE)
        
    words = {
        'text-left': 'text-start',
        'text-right': 'text-end',
        r'border-l\b': 'border-s',
        r'border-r\b': 'border-e'
    }
    for old, new_w in words.items():
        new_content = re.sub(r'(?<=[\s\"\'\`:\-])' + old, new_w, new_content)
        
    return new_content

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    new_data = replace_classes(data)
    if new_data != data:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_data)
        print('Fixed:', f)
