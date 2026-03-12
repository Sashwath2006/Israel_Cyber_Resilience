#!/usr/bin/env python
"""Debug MainWindow class structure."""
import ast
import sys

with open('app/main_window.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

try:
    tree = ast.parse(content)
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)

# Find the MainWindow class
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'MainWindow':
        print(f"Found MainWindow class at line {node.lineno}")
        print(f"Methods defined:")
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                print(f"  Line {item.lineno}: {item.name}")
        break
