import sys
import traceback
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

from app.main_window import MainWindow

try:
    window = MainWindow()
    print('[OK] MainWindow created')
except Exception as e:
    print('[ERROR] Exception during init:')
    traceback.print_exc()
    sys.exit(1)

# Check what attributes exist
attrs = [a for a in dir(window) if a.startswith('_') and not a.startswith('__')]
methods_h = [a for a in attrs if a.startswith('_h')]
methods_s = [a for a in attrs if a.startswith('_s')]

print(f'[INFO] Methods starting with _h: {methods_h}')
print(f'[INFO] Methods starting with _s: {methods_s}')
print(f'[INFO] Has nav_bar: {hasattr(window, "nav_bar")}')
print(f'[INFO] Has chat_interface: {hasattr(window, "chat_interface")}')
print(f'[INFO] Has report_editor: {hasattr(window, "report_editor")}')
