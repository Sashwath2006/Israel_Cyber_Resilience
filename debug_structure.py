#!/usr/bin/env python3

with open('app/main_window.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find the MainWindow class and check indentation levels
print("Scanning file structure:\n")

main_window_line = None
for i, line in enumerate(lines, 1):
    if 'class MainWindow(QMainWindow)' in line:
        main_window_line = i
        print(f"Line {i}: Found MainWindow class definition")
        break

if main_window_line:
    # Check indentation of methods after MainWindow
    print(f"\nMethods after MainWindow (starting at line {main_window_line}):")
    for i in range(main_window_line, min(main_window_line + 500, len(lines))):
        line = lines[i-1]
        if line.strip().startswith('def ') and not line.strip().startswith('def __'):
            indent = len(line) - len(line.lstrip())
            method_name = line.strip().split('(')[0].replace('def ', '')
            print(f"  Line {i}: indent={indent} spaces, method={method_name}")

print("\n\nChecking for _handle_scan_button and _show_export_menu:")
for i, line in enumerate(lines, 1):
    if '_handle_scan_button' in line or '_show_export_menu' in line:
        indent = len(line) - len(line.lstrip())
        print(f"  Line {i}: indent={indent} spaces: {line.rstrip()}")

