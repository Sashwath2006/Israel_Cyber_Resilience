from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.hardware import detect_hardware


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._initialize_ui()

    def _initialize_ui(self) -> None:
        self.setWindowTitle("Offline Hybrid Vulnerability Analysis Assistant")
        self.setMinimumSize(1000, 700)

        self._create_menu_bar()
        self._create_central_widget()

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about_dialog)

    def _create_central_widget(self) -> None:
        hardware = detect_hardware()

        lines = [
            f"CPU: {hardware['cpu']['model']} "
            f"({hardware['cpu']['cores']} cores / {hardware['cpu']['threads']} threads)",
            f"RAM: {hardware['ram']['total_gb']} GB",
        ]

        gpu = hardware["gpu"]
        if gpu["available"]:
            lines.append(
                f"GPU: {gpu['model']} ({gpu['vram_gb']} GB VRAM)"
            )
        else:
            lines.append("GPU: Not detected")

        label = QLabel("\n".join(lines))
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Offline Hybrid Vulnerability Analysis Assistant\n\n"
            "Phase 2: Hardware detection (informational only)."
        )
