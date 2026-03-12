import sys
import traceback

# Try importing with more detailed error tracking
try:
    print("[1] Importing PySide6...")
    from PySide6.QtWidgets import QMainWindow, QWidget
    print("    [OK]")
    
    print("[2] Importing app modules...")
    from app.hardware import detect_hardware
    print("    [OK] hardware")
    from app.model_registry import get_model_registry
    print("    [OK] model_registry")
    from app.document_ingestion import ingest_file
    print("    [OK] document_ingestion")
    from app.rule_engine import run_rules
    print("    [OK] rule_engine")
    from app.report_edit_ui import EditUIHandler
    print("    [OK] report_edit_ui")
    from app.ui.report_editor import ReportEditor
    print("    [OK] ui.report_editor")
    
    print("[3] Attempting full MainWindow import...")
    from app.main_window import MainWindow
    print("    [OK] MainWindow")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
