from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPlainTextEdit,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter,
)
from PySide6.QtCore import Qt

from app.hardware import detect_hardware
from app.model_registry import get_model_registry
from app.document_ingestion import ingest_file
from app.rule_engine import run_rules


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Offline Hybrid Vulnerability Analysis Assistant")
        self.resize(1300, 900)

        self.models = get_model_registry()
        self.ingested_chunks: list[dict] = []
        self.rule_findings: list[dict] = []

        self._build_ui()

    # ======================================================
    # UI CONSTRUCTION
    # ======================================================

    def _build_ui(self) -> None:
        root_splitter = QSplitter(Qt.Vertical)

        root_splitter.addWidget(self._build_top_bar())
        root_splitter.addWidget(self._build_main_workspace())
        root_splitter.addWidget(self._build_chat_panel())

        root_splitter.setStretchFactor(0, 0)
        root_splitter.setStretchFactor(1, 3)
        root_splitter.setStretchFactor(2, 2)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(root_splitter)
        self.setCentralWidget(container)

    # ======================================================
    # TOP BAR — HARDWARE + MODEL
    # ======================================================

    def _build_top_bar(self) -> QWidget:
        hardware = detect_hardware()

        info = QPlainTextEdit(readOnly=True)
        info.setMaximumHeight(120)
        info.setPlainText(
            f"CPU: {hardware['cpu']['model']} ({hardware['cpu']['cores']} cores)\n"
            f"RAM: {hardware['ram']['total_gb']} GB\n"
            f"GPU: {hardware['gpu']['model'] if hardware['gpu']['available'] else 'Not detected'}"
        )

        self.model_selector = QComboBox()
        for m in self.models:
            self.model_selector.addItem(m["name"])

        top = QWidget()
        layout = QHBoxLayout(top)
        layout.addWidget(info, 3)
        layout.addWidget(QLabel("Model:"), 0)
        layout.addWidget(self.model_selector, 1)

        return top

    # ======================================================
    # MAIN WORKSPACE — DOCUMENTS + FINDINGS
    # ======================================================

    def _build_main_workspace(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(self._build_documents_panel())
        splitter.addWidget(self._build_findings_panel())

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        return splitter

    # ---------------- Documents ----------------

    def _build_documents_panel(self) -> QWidget:
        self.docs_view = QPlainTextEdit(readOnly=True)

        load_btn = QPushButton("Load Documents")
        load_btn.clicked.connect(self._load_documents)

        scan_btn = QPushButton("Run Rule-Based Scan")
        scan_btn.clicked.connect(self._run_scan)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Documents"))
        layout.addWidget(load_btn)
        layout.addWidget(self.docs_view)
        layout.addWidget(scan_btn)

        return panel

    # ---------------- Findings ----------------

    def _build_findings_panel(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self.findings_view = QPlainTextEdit(readOnly=True)
        self.suppressed_view = QPlainTextEdit(readOnly=True)

        splitter.addWidget(self._wrap("Findings", self.findings_view))
        splitter.addWidget(self._wrap("Suppressed (Audit Only)", self.suppressed_view))

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        return splitter

    # ======================================================
    # CHAT PANEL
    # ======================================================

    def _build_chat_panel(self) -> QWidget:
        self.chat_output = QPlainTextEdit(readOnly=True)
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(80)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_chat)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Chat (LLM is blind in Phase 8)"))
        layout.addWidget(self.chat_output)
        layout.addWidget(self.chat_input)
        layout.addWidget(send_btn)

        return panel

    # ======================================================
    # HELPERS
    # ======================================================

    def _wrap(self, title: str, widget: QWidget) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel(title))
        layout.addWidget(widget)
        return box

    # ======================================================
    # ACTIONS
    # ======================================================

    def _load_documents(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select documents",
            "",
            "Files (*.txt *.log *.conf *.config *.csv *.json)",
        )

        if not paths:
            return

        self.ingested_chunks.clear()
        self.docs_view.clear()
        self.findings_view.clear()
        self.suppressed_view.clear()

        for path in paths:
            chunks = ingest_file(path)
            self.ingested_chunks.extend(chunks)
            self.docs_view.appendPlainText(f"{path} → {len(chunks)} chunks")

    def _run_scan(self) -> None:
        self.findings_view.clear()
        self.suppressed_view.clear()

        if not self.ingested_chunks:
            self.findings_view.setPlainText("No documents loaded.")
            return

        results = run_rules(self.ingested_chunks)

        active = [r for r in results if not r["suppressed"]]
        suppressed = [r for r in results if r["suppressed"]]

        for r in active:
            # Evidence is now a list (Phase 8.2 normalized schema)
            evidence_file = r["evidence"][0]["file"] if r["evidence"] else "unknown"
            self.findings_view.appendPlainText(
                f"[{r['rule_id']}] {r['title']}\n"
                f"Severity: {r['severity_suggested']} | "
                f"Source: {evidence_file}\n"
                "----"
            )

        for r in suppressed:
            # Evidence is now a list (Phase 8.2 normalized schema)
            evidence_file = r["evidence"][0]["file"] if r["evidence"] else "unknown"
            self.suppressed_view.appendPlainText(
                f"[{r['rule_id']}] {r['title']} (SUPPRESSED)\n"
                f"Source: {evidence_file}\n"
                "----"
            )

    def _send_chat(self) -> None:
        msg = self.chat_input.toPlainText().strip()
        if not msg:
            return

        self.chat_output.appendPlainText(f"User: {msg}")
        self.chat_output.appendPlainText(
            "Assistant: (LLM context integration begins in Phase 9)\n"
        )
        self.chat_input.clear()
