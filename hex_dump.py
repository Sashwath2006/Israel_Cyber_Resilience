with open('app/main_window.py', 'rb') as f:
    lines = f.readlines()

# Look for the pattern around line 192  
print("Lines 190-210:")
for i in range(189, min(210, len(lines))):
    line = lines[i]
    # Show in hex for any control chars
    print(f"{i+1:3d}: {line[:80]}")
