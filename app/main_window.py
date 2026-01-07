from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QComboBox,
)
from PySide6.QtCore import Qt, QThread, Signal

from app.hardware import detect_hardware
from app.model_registry import get_model_registry, assess_model_compatibility
from app.ollama_client import is_ollama_available, pull_model


class ModelDownloadWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id

    def run(self) -> None:
        success, message = pull_model(self.model_id)
        self.finished.emit(success, message)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.models = get_model_registry()
        self.worker: ModelDownloadWorker | None = None
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

        lines: list[str] = []

        lines.append("Detected Hardware:")
        lines.append(
            f"CPU: {hardware['cpu']['model']} "
            f"({hardware['cpu']['cores']} cores / {hardware['cpu']['threads']} threads)"
        )
        lines.append(f"RAM: {hardware['ram']['total_gb']} GB")

        gpu = hardware["gpu"]
        if gpu["available"]:
            lines.append(f"GPU: {gpu['model']} ({gpu['vram_gb']} GB VRAM)")
        else:
            lines.append("GPU: Not detected")

        lines.append("")
        lines.append("Available Models:")

        for model in self.models:
            lines.append(f"• {model['name']} ({model['parameter_size']})")
            lines.append(f"  {model['description']}")
            for note in assess_model_compatibility(model, hardware):
                lines.append(f"  ⚠ {note}")
            lines.append("")

        info_label = QLabel("\n".join(lines))
        info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        info_label.setWordWrap(True)

        self.model_selector = QComboBox()
        for model in self.models:
            self.model_selector.addItem(model["name"])

        self.download_button = QPushButton("Download Selected Model")
        self.download_button.clicked.connect(self._handle_download_clicked)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(info_label)
        layout.addWidget(QLabel("Select model to download:"))
        layout.addWidget(self.model_selector)
        layout.addWidget(self.download_button)

        self.setCentralWidget(container)

    def _handle_download_clicked(self) -> None:
        if not is_ollama_available():
            QMessageBox.critical(
                self,
                "Ollama Not Available",
                "Ollama is not running or cannot be reached.\n\n"
                "Please start Ollama and try again.",
            )
            return

        selected_model = self.models[self.model_selector.currentIndex()]

        self.download_button.setEnabled(False)

        QMessageBox.information(
            self,
            "Downloading Model",
            f"Downloading model: {selected_model['name']}\n\n"
            "The application will remain responsive during the download.",
        )

        self.worker = ModelDownloadWorker(selected_model["ollama_id"])
        self.worker.finished.connect(self._on_download_finished)
        self.worker.start()

    def _on_download_finished(self, success: bool, message: str) -> None:
        self.download_button.setEnabled(True)

        if success:
            QMessageBox.information(self, "Download Complete", message)
        else:
            QMessageBox.critical(self, "Download Failed", message)

        self.worker = None

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Offline Hybrid Vulnerability Analysis Assistant\n\n"
            "Phase 4: Explicit, user-controlled model download.\n"
            "Downloads are executed in a controlled background worker.",
        )
