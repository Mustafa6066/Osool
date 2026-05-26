import re

def process_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    replacements = [
      (r'([\s"\'])left-1/2([\s"\'])', r'\1start-1/2\2'),
      (r'([\s"\'])-translate-x-1/2([\s"\'])', r'\1rtl:translate-x-1/2 ltr:-translate-x-1/2\2'),
    ]

    new_code = code
    for old, new in replacements:
        new_code = re.sub(old, new, new_code)
    
    if code != new_code:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print(f"Updated {filename}")

process_file('components/dock/LiquidDock.tsx')
