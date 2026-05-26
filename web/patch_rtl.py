import re

def process_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    replacements = [
      (r'([\s"\'])pl-([0-9]+(?:\.[0-9]+)?|px)', r'\1ps-\2'),
      (r'([\s"\'])pr-([0-9]+(?:\.[0-9]+)?|px)', r'\1pe-\2'),
      (r'([\s"\'])ml-([0-9]+(?:\.[0-9]+)?|px|auto)', r'\1ms-\2'),
      (r'([\s"\'])mr-([0-9]+(?:\.[0-9]+)?|px|auto)', r'\1me-\2'),
      (r'([\s"\'])text-left([\s"\'])', r'\1text-start\2'),
      (r'([\s"\'])text-right([\s"\'])', r'\1text-end\2'),
      (r'([\s"\'])border-l-([a-zA-Z0-9\-]+)', r'\1border-s-\2'),
      (r'([\s"\'])border-r-([a-zA-Z0-9\-]+)', r'\1border-e-\2'),
      (r'([\s"\'])border-l([\s"\'])', r'\1border-s\2'),
      (r'([\s"\'])border-r([\s"\'])', r'\1border-e\2'),
      (r'([\s"\'])rounded-l-([a-zA-Z0-9\-]+)', r'\1rounded-s-\2'),
      (r'([\s"\'])rounded-r-([a-zA-Z0-9\-]+)', r'\1rounded-e-\2'),
      (r'([\s"\'])rounded-tl-([a-zA-Z0-9\-]+)', r'\1rounded-ss-\2'),
      (r'([\s"\'])rounded-tr-([a-zA-Z0-9\-]+)', r'\1rounded-se-\2'),
      (r'([\s"\'])rounded-bl-([a-zA-Z0-9\-]+)', r'\1rounded-es-\2'),
      (r'([\s"\'])rounded-br-([a-zA-Z0-9\-]+)', r'\1rounded-ee-\2'),
      (r'([\s"\'])left-([a-zA-Z0-9\-/]+)', r'\1start-\2'),
      (r'([\s"\'])right-([a-zA-Z0-9\-/]+)', r'\1end-\2'),
      (r'([\s"\'])-left-([a-zA-Z0-9\-/]+)', r'\1-start-\2'),
      (r'([\s"\'])-right-([a-zA-Z0-9\-/]+)', r'\1-end-\2'),
    ]

    new_code = code
    for old, new in replacements:
        new_code = re.sub(old, new, new_code)
    
    if code != new_code:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_code)
        print(f"Updated {filename}")

process_file('components/AgentInterface.tsx')
process_file('components/dock/DockContextPanel.tsx')
process_file('components/LanguageToggle.tsx')
process_file('components/chat/ChatMain.tsx')
process_file('components/ChatInterface.tsx')
