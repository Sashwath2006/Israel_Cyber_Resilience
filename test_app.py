import sys
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

from app.main_window import MainWindow

try:
    window = MainWindow()
    print('[SUCCESS] MainWindow instantiated!')
    print(f'[INFO] Has nav_bar: {hasattr(window, "nav_bar")}')
    print(f'[INFO] Has chat_interface: {hasattr(window, "chat_interface")}')
    print(f'[INFO] Has report_editor: {hasattr(window, "report_editor")}')
    print(f'[INFO] Window type: {type(window).__name__}')
    
except Exception as e:
    print(f'[ERROR] {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
