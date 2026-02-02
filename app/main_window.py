"""
Professional Analyst Workbench - Two-Pane UI
Left: Editable Report Editor
Right: ChatGPT-Style AI Assistant
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QFileDialog, QMessageBox, QSplitter, QComboBox, QScrollArea,
    QFrame, QLineEdit, QSizePolicy, QMenu
)
from PySide6.QtGui import QFont, QTextCursor, QAction
from PySide6.QtCore import Qt, Signal, QThread
from typing import Optional
import os

from app.hardware import detect_hardware
from app.model_registry import get_model_registry
from app.document_ingestion import ingest_file
from app.rule_engine import run_rules
from app.llm_reasoner import explain_single_finding
from app.ollama_client import is_ollama_available
from app.finding_integration import enhance_findings_with_severity_fields
from app.severity_override import get_final_severity
from app.report_model import ReportWorkspace
from app.report_generator import generate_sample_report
from app.ai_assistant import assist_report_editing, discuss_vulnerability
from app.report_exporter import export_to_markdown, export_to_pdf
from app.report_state import ReportState, ReportStatus


class ScanWorker(QThread):
    """Background worker for scanning operations."""
    status_update = Signal(str)
    scan_complete = Signal(list, list)  # chunks, findings
    
    def __init__(self, file_paths: list[str]):
        super().__init__()
        self.file_paths = file_paths
        
    def run(self):
        chunks = []
        findings = []
        
        try:
            # Ingest files
            self.status_update.emit(f"[Ingesting {len(self.file_paths)} file(s)...]")
            for path in self.file_paths:
                file_chunks = ingest_file(path)
                chunks.extend(file_chunks)
                self.status_update.emit(f"  ✓ {os.path.basename(path)}: {len(file_chunks)} chunks")
            
            # Run analysis
            self.status_update.emit("[Running security analysis...]")
            findings = run_rules(chunks)
            self.status_update.emit(f"  ✓ Analysis complete: {len(findings)} finding(s)")
            
            self.scan_complete.emit(chunks, findings)
            
        except Exception as e:
            self.status_update.emit(f"[ERROR] {str(e)}")


class ChatMessage(QWidget):
    """Single chat message bubble."""
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        
        # Message bubble
        bubble = QFrame()
        bubble.setMaximumWidth(600)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        
        # Message text
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setFont(QFont("Segoe UI", 10))
        bubble_layout.addWidget(label)
        
        # Styling
        if is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #0084ff;
                    border-radius: 18px;
                    color: white;
                }
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #e4e6eb;
                    border-radius: 18px;
                    color: #050505;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()


class ChatPane(QWidget):
    """ChatGPT-style chat pane."""
    send_message = Signal(str)
    upload_files = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat messages area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        scroll.setWidget(self.messages_container)
        layout.addWidget(scroll, 1)
        
        # Input bar
        input_bar = self._create_input_bar()
        layout.addWidget(input_bar)
        
    def _create_input_bar(self) -> QWidget:
        """Create fixed bottom input bar."""
        bar = QFrame()
        bar.setFrameShape(QFrame.Shape.StyledPanel)
        bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
        """)
        bar.setFixedHeight(70)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Upload button
        upload_btn = QPushButton("+")
        upload_btn.setFixedSize(40, 40)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 20px;
                font-size: 20pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        upload_btn.clicked.connect(self._handle_upload)
        layout.addWidget(upload_btn)
        
        # Text input
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Message AI Assistant...")
        self.input_field.setFixedHeight(46)
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 10pt;
            }
        """)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field, 1)
        
        # Send button
        send_btn = QPushButton("⬆")
        send_btn.setFixedSize(40, 40)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 16pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
        """)
        send_btn.clicked.connect(self._handle_send)
        layout.addWidget(send_btn)
        
        return bar
    
    def eventFilter(self, obj, event):
        """Handle Enter/Shift+Enter in text input."""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._handle_send()
                return True
        return super().eventFilter(obj, event)
    
    def _handle_send(self):
        """Send message."""
        text = self.input_field.toPlainText().strip()
        if text:
            self.add_message(text, is_user=True)
            self.send_message.emit(text)
            self.input_field.clear()
    
    def _handle_upload(self):
        """Handle file upload."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Analyze",
            "",
            "All Files (*.*)"
        )
        if paths:
            self.upload_files.emit(paths)
    
    def add_message(self, text: str, is_user: bool):
        """Add a message to the chat."""
        msg = ChatMessage(text, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg)
        
        # Auto-scroll to bottom
        QWidget.update(self.messages_container)
        scroll = self.messages_container.parentWidget().parentWidget()
        if isinstance(scroll, QScrollArea):
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())


class ReportEditor(QTextEdit):
    """Editable report pane."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Report will appear here after analysis...")
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: none;
                padding: 20px;
            }
        """)
        self.is_finalized = False
    
    def set_finalized(self, finalized: bool):
        """Lock/unlock editing."""
        self.is_finalized = finalized
        self.setReadOnly(finalized)
        if finalized:
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #f0f0f0;
                    border: none;
                    padding: 20px;
                }
            """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vulnerability Analysis Workbench")
        self.resize(1600, 900)
        
        # State
        self.models = get_model_registry()
        self.report_workspace: Optional[ReportWorkspace] = None
        self.report_data: Optional[dict] = None
        self.ingested_chunks: list[dict] = []
        self.rule_findings: list[dict] = []
        self.report_state = ReportState()
        
        self._build_ui()
        
    def _build_ui(self):
        """Build two-pane workbench."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top toolbar
        layout.addWidget(self._create_toolbar())
        
        # Main splitter: Left (Report) | Right (Chat)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT PANE: Report Editor
        self.report_editor = ReportEditor()
        splitter.addWidget(self.report_editor)
        
        # RIGHT PANE: Chat Assistant
        self.chat_pane = ChatPane()
        self.chat_pane.send_message.connect(self._handle_user_message)
        self.chat_pane.upload_files.connect(self._handle_file_upload)
        splitter.addWidget(self.chat_pane)
        
        # Set initial sizes (60% report, 40% chat)
        splitter.setSizes([960, 640])
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #d0d0d0; }")
        
        layout.addWidget(splitter, 1)
        
        self.setCentralWidget(container)
        
        # Welcome message
        self.chat_pane.add_message(
            "Welcome to the Vulnerability Analysis Workbench.\n\n"
            "Upload files using the '+' button to begin analysis.",
            is_user=False
        )
    
    def _create_toolbar(self) -> QWidget:
        """Create top toolbar with model selector and actions."""
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.Shape.StyledPanel)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        toolbar.setFixedHeight(50)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)
        
        # Model selector
        label = QLabel("Model:")
        label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.model_selector = QComboBox()
        for m in self.models:
            self.model_selector.addItem(m["name"])
        self.model_selector.setMinimumWidth(200)
        self.model_selector.setStyleSheet("""
            QComboBox {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
        """)
        layout.addWidget(self.model_selector)
        
        layout.addStretch()
        
        # Finalize button
        self.finalize_btn = QPushButton("Finalize Report")
        self.finalize_btn.setEnabled(False)
        self.finalize_btn.clicked.connect(self._finalize_report)
        self.finalize_btn.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
            QPushButton:disabled {
                background-color: #c0c0c0;
            }
        """)
        layout.addWidget(self.finalize_btn)
        
        # Export menu
        self.export_btn = QPushButton("Export ▼")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #c0c0c0;
            }
        """)
        
        export_menu = QMenu(self)
        export_menu.addAction("Export as Markdown", self._export_markdown)
        export_menu.addAction("Export as PDF", self._export_pdf)
        self.export_btn.setMenu(export_menu)
        
        layout.addWidget(self.export_btn)
        
        return toolbar
    
    def _handle_file_upload(self, paths: list[str]):
        """Handle file upload from chat."""
        self.chat_pane.add_message(
            f"Analyzing {len(paths)} file(s)...\n" + "\n".join([f"• {os.path.basename(p)}" for p in paths]),
            is_user=False
        )
        
        # Start background scan
        self.scan_worker = ScanWorker(paths)
        self.scan_worker.status_update.connect(lambda msg: self.chat_pane.add_message(msg, is_user=False))
        self.scan_worker.scan_complete.connect(self._handle_scan_complete)
        self.scan_worker.start()
    
    def _handle_scan_complete(self, chunks: list[dict], findings: list[dict]):
        """Handle completed scan."""
        self.ingested_chunks = chunks
        self.rule_findings = findings
        
        # Generate report
        try:
            # Enhance findings with severity fields
            enhanced = enhance_findings_with_severity_fields(findings)
            
            # Create report workspace
            self.report_workspace = ReportWorkspace(
                scope="Uploaded Files Analysis",
                analyst_name=None,
                executive_summary=""
            )
            self.report_workspace.add_findings(enhanced)
            
            # Get selected model
            model_name = self.model_selector.currentText()
            model_id = None
            for m in self.models:
                if m["name"] == model_name:
                    model_id = m["ollama_id"]  # Fixed: use 'ollama_id' not 'id'
                    break
            
            # Generate sample report with template
            self.report_data = generate_sample_report(
                findings=enhanced,
                scope="Uploaded Files Analysis",
                model_id=model_id,
                template="default"
            )
            
            # Display in editor
            report_text = self._format_report_for_display(self.report_data)
            self.report_editor.setPlainText(report_text)
            
            self.finalize_btn.setEnabled(True)
            self.chat_pane.add_message(
                f"✓ Analysis complete!\n\n"
                f"Found {len(findings)} potential issue(s).\n"
                f"Report is now editable in the left pane.",
                is_user=False
            )
            
        except Exception as e:
            self.chat_pane.add_message(f"[ERROR] Failed to generate report: {str(e)}", is_user=False)
    
    def _format_report_for_display(self, report_data: dict) -> str:
        """Format report data as plain text."""
        lines = []
        lines.append("=" * 70)
        lines.append("VULNERABILITY ANALYSIS REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Metadata
        metadata = report_data.get("metadata", {})
        lines.append(f"Total Findings: {metadata.get('total_findings', 0)}")
        
        # Severity breakdown
        severity_breakdown = metadata.get('severity_breakdown', {})
        lines.append(f"High Severity: {severity_breakdown.get('High', 0)}")
        lines.append(f"Medium Severity: {severity_breakdown.get('Medium', 0)}")
        lines.append(f"Low Severity: {severity_breakdown.get('Low', 0)}")
        lines.append("")
        lines.append("=" * 70)
        lines.append("")
        
        # Executive Summary
        exec_summary = report_data.get("executive_summary", "")
        if exec_summary:
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 70)
            lines.append(exec_summary)
            lines.append("")
            lines.append("=" * 70)
            lines.append("")
        
        # Findings
        lines.append("FINDINGS")
        lines.append("-" * 70)
        lines.append("")
        
        for finding in report_data.get("findings", []):
            vuln_id = finding.get('vulnerability_id', 'UNKNOWN')
            title = finding.get('title', 'Unknown')
            severity = finding.get('severity', 'Unknown')
            rule_id = finding.get('rule_id', 'N/A')
            category = finding.get('category', 'N/A')
            
            lines.append(f"[{vuln_id}] {title}")
            lines.append(f"  Severity: {severity}")
            lines.append(f"  Rule: {rule_id}")
            lines.append(f"  Category: {category}")
            
            # Locations
            for loc in finding.get("locations", []):
                file_path = loc.get('file', 'unknown')
                line_start = loc.get('line_start')
                if line_start:
                    lines.append(f"  Location: {file_path} (line {line_start})")
                else:
                    lines.append(f"  Location: {file_path}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _handle_user_message(self, text: str):
        """Handle user message in chat."""
        # Check if asking about report
        text_lower = text.lower()
        
        if "rewrite" in text_lower or "improve" in text_lower or "summarize" in text_lower:
            # Get selected text from report
            cursor = self.report_editor.textCursor()
            selected = cursor.selectedText()
            
            if selected:
                self.chat_pane.add_message(
                    f"I can suggest improvements, but you'll need to manually apply them to the report.\n\n"
                    f"Selected text:\n{selected[:200]}...",
                    is_user=False
                )
            else:
                self.chat_pane.add_message(
                    "Please select text in the report editor first, then ask me to rewrite it.",
                    is_user=False
                )
        
        elif self.report_data and text_lower not in ["hi", "hello", "hey", "help", "what", "how"]:
            # Only show the default message for non-generic queries
            total_findings = self.report_data.get('metadata', {}).get('total_findings', 0)
            self.chat_pane.add_message(
                f"I can see your report has {total_findings} findings. "
                f"Select any section and ask me to rewrite it!",
                is_user=False
            )
        elif self.report_data and text_lower in ["hi", "hello", "hey", "help", "what", "how"]:
            # Handle common queries differently
            total_findings = self.report_data.get('metadata', {}).get('total_findings', 0)
            self.chat_pane.add_message(
                f"Hello! Your report has {total_findings} findings. "
                f"Ask me to rewrite or improve specific sections by selecting text first.",
                is_user=False
            )
        else:
            self.chat_pane.add_message(
                "Upload files first to begin analysis. Use the '+' button to select files.",
                is_user=False
            )
    
    def _finalize_report(self):
        """Finalize the report (make read-only)."""
        self.report_editor.set_finalized(True)
        self.finalize_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        
        self.chat_pane.add_message(
            "✓ Report finalized! You can now export it using the Export button.",
            is_user=False
        )
    
    def _export_markdown(self):
        """Export report to Markdown."""
        if not self.report_data:
            QMessageBox.warning(self, "No Report", "Generate a report first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", "", "Markdown (*.md)")
        if path:
            success, error = export_to_markdown(self.report_data, self.report_workspace, path)
            if success:
                self.chat_pane.add_message(f"✓ Exported to: {path}", is_user=False)
            else:
                self.chat_pane.add_message(f"✗ Export failed: {error}", is_user=False)
    
    def _export_pdf(self):
        """Export report to PDF."""
        if not self.report_data:
            QMessageBox.warning(self, "No Report", "Generate a report first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF (*.pdf)")
        if path:
            success, error = export_to_pdf(self.report_data, self.report_workspace, path)
            if success:
                self.chat_pane.add_message(f"✓ Exported to: {path}", is_user=False)
            else:
                self.chat_pane.add_message(f"✗ Export failed: {error}", is_user=False)
