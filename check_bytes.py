with open('app/main_window.py', 'rb') as f:
    lines = f.readlines()
    
    # Find line with "def _handle_scan_button"
    for i, line in enumerate(lines):
        if b'def _handle_scan_button' in line:
            print(f"Found at physical line {i+1}")
            print(f"Raw bytes: {line}")
            print(f"Indent count: {len(line) - len(line.lstrip())}")
            print(f"Hex indent: {line[:20].hex()}")
            break
    
    # Also find _build_ui for comparison
    for i, line in enumerate(lines):
        if b'def _build_ui' in line:
            print(f"\n_build_ui Found at physical line {i+1}")
            print(f"Raw bytes: {line}")
            print(f"Indent count: {len(line) - len(line.lstrip())}")
            print(f"Hex indent: {line[:20].hex()}")
            break
