with open('app/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    for i in range(max(0, 35), min(len(lines), 45)):
        print(f"{i+1:3d}: {lines[i].rstrip()}")
