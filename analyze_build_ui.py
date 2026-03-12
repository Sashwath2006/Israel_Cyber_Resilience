import re

with open('app/main_window.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find _build_ui method
match = re.search(r'def _build_ui\(self\):(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
if match:
    build_ui_code = match.group(0)
    print("_build_ui method:")
    print("-" * 70)
    
    # Check what it calls
    if '_handle_scan_button' in build_ui_code:
        print("[FOUND] References _handle_scan_button")
    else:
        print("[NOT FOUND] References _handle_scan_button")
        
    if '_show_export_menu' in build_ui_code:
        print("[FOUND] References _show_export_menu")
    else:
        print("[NOT FOUND] References _show_export_menu")
        
    if 'NavigationBar' in build_ui_code:
        print("[FOUND] Uses NavigationBar")
    else:
        print("[NOT FOUND] Uses NavigationBar")
        
    if 'ChatPane' in build_ui_code:
        print("[FOUND] Uses ChatPane")
    else:
        print("[NOT FOUND] Uses ChatPane")
        
    if 'ChatInterface' in build_ui_code:
        print("[FOUND] Uses ChatInterface")
    else:
        print("[NOT FOUND] Uses ChatInterface")
        
    print("\nFirst 50 lines of _build_ui:")
    lines = build_ui_code.split('\n')[:50]
    for i, line in enumerate(lines, 1):
        print(f"{i:3d}: {line}")
else:
    print("[ERROR] Could not find _build_ui")
