with open('app/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Look for _handle_scan_button
if '_handle_scan_button' in content:
    print("Found: _handle_scan_button")
    idx = content.find('_handle_scan_button')
    line_before = content[:idx].count('\n') + 1
    print(f"  At line: {line_before}")
    # Show context
    start = max(0, idx - 100)
    end = min(len(content), idx + 100)
    print(f"  Context: {content[start:end]}")
else:
    print("NOT FOUND: _handle_scan_button")

# Look for _show_export_menu
if '_show_export_menu' in content:
    print("\nFound: _show_export_menu")
    idx = content.find('_show_export_menu')
    line_before = content[:idx].count('\n') + 1
    print(f"  At line: {line_before}")
else:
    print("\nNOT FOUND: _show_export_menu")

# Show total line count
total_lines = content.count('\n')
print(f"\nTotal lines: {total_lines}")

# Show where _build_ui actually is
if 'def _build_ui' in content:
    idx = content.find('def _build_ui')
    line_before = content[:idx].count('\n') + 1
    print(f"def _build_ui at: {line_before}")
