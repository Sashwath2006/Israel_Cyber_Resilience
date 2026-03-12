with open('app/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find _build_ui by searching
for i, line in enumerate(lines):
    if 'def _build_ui' in line:
        print(f"Found _build_ui at line {i+1}")
        # Print 50 lines from there
        for j in range(i, min(i+50, len(lines))):
            print(f"{j+1:4d}: {lines[j].rstrip()}")
        break
