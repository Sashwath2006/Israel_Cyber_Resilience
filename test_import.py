import ast

with open('app/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Try to parse and see if there are import errors
try:
    tree = ast.parse(content)
    print("[OK] File parses successfully")
except ModuleNotFoundError as e:
    print(f"[ERROR] Module not found: {e}")
except SyntaxError as e:
    print(f"[SYNTAX ERROR] {e}")

# Now try to actually import it
try:
    from app.main_window import MainWindow
    print("[OK] MainWindow imported successfully")
except ModuleNotFoundError as e:
    print(f"[IMPORT ERROR] {e}")
