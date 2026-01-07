from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QPlainTextEdit,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal

from app.hardware import detect_hardware
from app.model_registry import get_model_registry, assess_model_compatibility
from app.ollama_client import is_ollama_available, pull_model
from app.llm_inference import run_inference
from app.document_ingestion import ingest_file


# ---------------- Worker Threads ---------------- #

class ModelDownloadWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            return
        success, message = pull_model(self.model_id)
        if not self._cancelled:
            self.finished.emit(success, message)


class ChatInferenceWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, model_id: str, prompt: str):
        super().__init__()
        self.model_id = model_id
        self.prompt = prompt
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if self._cancelled:
            return
        success, result = run_inference(self.model_id, self.prompt)
        if not self._cancelled:
            self.finished.emit(success, result)


# ---------------- Main Window ---------------- #

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.models = get_model_registry()
        self.download_worker: ModelDownloadWorker | None = None
        self.chat_worker: ChatInferenceWorker | None = None

        # Phase 7: runtime-only storage (no persistence)
        self.ingested_chunks: list[dict] = []

        self._initialize_ui()

    # ---------- Lifecycle Safety ---------- #

    def closeEvent(self, event) -> None:
        self._cleanup_workers()
        event.accept()

    def _cleanup_workers(self) -> None:
        for worker in (self.chat_worker, self.download_worker):
            if worker and worker.isRunning():
                worker.cancel()
                worker.quit()
                worker.wait()
        self.chat_worker = None
        self.download_worker = None

    # ---------- UI ---------- #

    def _initialize_ui(self) -> None:
        self.setWindowTitle("Offline Hybrid Vulnerability Analysis Assistant")
        self.setMinimumSize(1100, 900)

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

        # ---------- Hardware + Model Info ---------- #

        info_lines = [
            "Detected Hardware:",
            f"CPU: {hardware['cpu']['model']} "
            f"({hardware['cpu']['cores']} cores / {hardware['cpu']['threads']} threads)",
            f"RAM: {hardware['ram']['total_gb']} GB",
            f"GPU: {hardware['gpu']['model']} ({hardware['gpu']['vram_gb']} GB VRAM)"
            if hardware["gpu"]["available"]
            else "GPU: Not detected",
            "",
            "Available Models:",
        ]

        for model in self.models:
            info_lines.append(f"• {model['name']} ({model['parameter_size']})")
            info_lines.append(f"  {model['description']}")
            for note in assess_model_compatibility(model, hardware):
                info_lines.append(f"  ⚠ {note}")
            info_lines.append("")

        info_label = QLabel("\n".join(info_lines))
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # ---------- Model Controls ---------- #

        self.model_selector = QComboBox()
        for model in self.models:
            self.model_selector.addItem(model["name"])

        self.download_button = QPushButton("Download Selected Model")
        self.download_button.clicked.connect(self._handle_download)

        # ---------- Phase 7: Document Ingestion ---------- #

        self.load_docs_button = QPushButton("Load Document(s)")
        self.load_docs_button.clicked.connect(self._handle_load_documents)

        self.ingestion_status = QPlainTextEdit()
        self.ingestion_status.setReadOnly(True)
        self.ingestion_status.setPlaceholderText(
            "Loaded documents and chunk counts will appear here."
        )

        # ---------- Chat UI (Phase 6) ---------- #

        self.chat_display = QPlainTextEdit(readOnly=True)

        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(80)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._handle_send)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._handle_stop)

        self.reset_button = QPushButton("Reset Session")
        self.reset_button.clicked.connect(self._handle_reset)

        chat_buttons = QHBoxLayout()
        chat_buttons.addWidget(self.send_button)
        chat_buttons.addWidget(self.stop_button)
        chat_buttons.addWidget(self.reset_button)

        # ---------- Layout ---------- #

        layout = QVBoxLayout()
        layout.addWidget(info_label)
        layout.addWidget(QLabel("Select model:"))
        layout.addWidget(self.model_selector)
        layout.addWidget(self.download_button)

        layout.addSpacing(10)
        layout.addWidget(QLabel("Documents:"))
        layout.addWidget(self.load_docs_button)
        layout.addWidget(self.ingestion_status)

        layout.addSpacing(10)
        layout.addWidget(QLabel("Chat:"))
        layout.addWidget(self.chat_display)
        layout.addWidget(self.chat_input)
        layout.addLayout(chat_buttons)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # ---------- Phase 4: Controlled Download ---------- #

    def _handle_download(self) -> None:
        if not is_ollama_available():
            QMessageBox.critical(self, "Error", "Ollama not available.")
            return

        self._cleanup_workers()

        model = self.models[self.model_selector.currentIndex()]
        self.download_worker = ModelDownloadWorker(model["ollama_id"])
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.start()

    def _on_download_finished(self, success: bool, message: str) -> None:
        QMessageBox.information(
            self,
            "Download Result",
            message if success else f"Download failed: {message}",
        )
        self.download_worker = None

    # ---------- Phase 7: Document Ingestion ---------- #

    def _handle_load_documents(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents",
            "",
            "Supported Files (*.txt *.log *.csv *.json)",
        )

        if not file_paths:
            return

        self.ingested_chunks.clear()
        self.ingestion_status.clear()

        for path in file_paths:
            try:
                chunks = ingest_file(path)
                self.ingested_chunks.extend(chunks)
                self.ingestion_status.appendPlainText(
                    f"{path} → {len(chunks)} chunks"
                )
            except Exception as exc:
                self.ingestion_status.appendPlainText(
                    f"{path} → ERROR: {exc}"
                )

    # ---------- Phase 6: Chat ---------- #

    def _handle_send(self) -> None:
        prompt = self.chat_input.toPlainText().strip()
        if not prompt:
            return

        if not is_ollama_available():
            QMessageBox.critical(self, "Error", "Ollama not available.")
            return

        self._cleanup_workers()

        self.chat_display.appendPlainText(f"User: {prompt}\n")
        self.chat_input.clear()

        model = self.models[self.model_selector.currentIndex()]
        self.chat_worker = ChatInferenceWorker(model["ollama_id"], prompt)
        self.chat_worker.finished.connect(self._on_chat_finished)
        self.chat_worker.start()

    def _on_chat_finished(self, success: bool, result: str) -> None:
        prefix = "Assistant" if success else "Error"
        self.chat_display.appendPlainText(f"{prefix}: {result}\n")
        self.chat_worker = None

    def _handle_stop(self) -> None:
        self._cleanup_workers()
        self.chat_display.appendPlainText("⚠ Inference cancelled.\n")

    def _handle_reset(self) -> None:
        self._cleanup_workers()
        self.chat_display.clear()
        self.chat_input.clear()

    # ---------- About ---------- #

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Offline Hybrid Vulnerability Analysis Assistant\n\n"
            "Phase 7: Raw document ingestion and deterministic chunking.\n"
            "No analysis or persistence is performed.",
        )
