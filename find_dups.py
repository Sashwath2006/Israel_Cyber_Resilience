import re

with open('app/main_window.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# Find all defs
patterns = [
    ('def _handle_scan_button', 'handle_scan_button'),
    ('def _show_export_menu', 'show_export_menu'),
    ('def _build_ui', 'build_ui'),
    ('def _initialize_auth', 'initialize_auth'),
]

for pattern, name in patterns:
    matches = list(re.finditer(re.escape(pattern), content))
    print(f"\n{name}: {len(matches)} occurrence(s)")
    for i, match in enumerate(matches):
        line_num = content[:match.start()].count('\n') + 1
        # Get context
        start = max(0, match.start() - 30)
        end = min(len(content), match.end() + 50)
        context = content[start:end].replace('\n', '\\n')
        print(f"  #{i+1} at line {line_num}: ...{context}...")
