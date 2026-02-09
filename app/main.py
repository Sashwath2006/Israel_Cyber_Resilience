import sys
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.logging_config import setup_logging


def main() -> None:
    # Initialize logging
    setup_logging(log_level="INFO", log_file="app.log")
    
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
