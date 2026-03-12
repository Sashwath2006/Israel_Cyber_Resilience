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
from typing import Optional, Dict, Any
from datetime import datetime
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
from app.ai_assistant import (
    assist_report_editing_advanced,
    discuss_vulnerability,
    RewriteContext,
    detect_report_section
)
from app.report_state import ReportState, ReportStatus
from app.logging_config import get_logger
from app.auth import session_manager, user_manager, access_control, require_auth, require_permission
from app.report_edit_engine import ReportEditEngine
from app.report_version_manager import ReportVersionManager
from app.report_edit_ui import EditUIHandler
from app.ui.report_editor import ReportEditor
from app.ui.editor_toolbar import EditorToolbar
from app.ui.chat_ui import ChatInterface
from app.ui.modern_theme import (
    DeepSpaceColors, ModernTypography, ModernSpacing, ModernBorderRadius,
    ModernShadow, generate_button_stylesheet, generate_global_stylesheet
)


class ScanWorker(QThread):
    """Background worker for scanning operations."""
    status_update = Signal(str)
    scan_complete = Signal(list, list)  # chunks, findings
    error_occurred = Signal(str)  # Error signal
    
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
                try:
                    file_chunks = ingest_file(path)
                    chunks.extend(file_chunks)
                    self.status_update.emit(f"  ✓ {os.path.basename(path)}: {len(file_chunks)} chunks")
                except Exception as e:
                    self.status_update.emit(f"  ⚠ Error processing {os.path.basename(path)}: {str(e)}")
                    continue  # Continue with other files
            
            # Run analysis
            self.status_update.emit("[Running security analysis...]")
            findings = run_rules(chunks)
            self.status_update.emit(f"  ✓ Analysis complete: {len(findings)} finding(s)")
            
            self.scan_complete.emit(chunks, findings)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vulnerability Analysis Workbench")
        self.resize(1600, 900)
        
        # Apply modern theme globally
        self.setStyleSheet(generate_global_stylesheet())
        
        # Logger
        self.logger = get_logger("MainWindow")
        
        # Authentication
        self.session_token = None
        self.current_user = None
        
        # State
        self.models = get_model_registry()
        self.report_workspace: Optional[ReportWorkspace] = None
        self.report_data: Optional[dict] = None
        self.ingested_chunks: list[dict] = []
        self.rule_findings: list[dict] = []
        self.report_state = ReportState()
        
        # Edit engine and version manager
        # Will be initialized when model is selected
        self.edit_engine: Optional[ReportEditEngine] = None
        self.version_manager = ReportVersionManager(max_versions=50)
        self.edit_ui_handler: Optional[EditUIHandler] = None
        
        # Initialize auth
        self._initialize_auth()
        
        self._build_ui()
        self.logger.info("MainWindow initialized")
    
    def _initialize_auth(self):
        """Initialize authentication system."""
        # Ensure default users are available
        # Create a local_analyst user if it doesn't exist in users.json
        if "local_analyst" not in user_manager.users:
            user_manager.users["local_analyst"] = {
                "password_hash": user_manager._hash_password("local_analyst"),
                "role": "analyst",
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            user_manager._save_users(user_manager.users)
        
        # Attempt to create a default session
        self.session_token = session_manager.create_session(
            user_id="desktop_user",
            username="local_analyst"
        )
        self.current_user = "local_analyst"
        self.logger.info("Authentication initialized", user=self.current_user)
    
    def _check_permission(self, permission: str) -> bool:
        """
        Check if the current user has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.session_token or not self.current_user:
            return False
        
        # Validate session
        if not session_manager.validate_session(self.session_token):
            return False
        
        # Get user role and check permissions
        role = user_manager.get_user_role(self.current_user)
        if not role:
            return False
        
        return access_control.has_permission(role, permission)
    
    def _initialize_edit_handler(self):
        """Initialize the edit engine and UI handler."""
        if self.edit_ui_handler:
            return  # Already initialized
        
        # Get selected model
        model_name = self.model_selector.currentText()
        model_id = None
        for m in self.models:
            if m["name"] == model_name:
                model_id = m.get("ollama_id") or m.get("id")
                break
        
        if not model_id:
            self.logger.warning("No model ID found for edit engine")
            return
        
        # Initialize edit engine
        self.edit_engine = ReportEditEngine(model_id=model_id, temperature=0.3)
        
        # Initialize UI handler
        self.edit_ui_handler = EditUIHandler(
            edit_engine=self.edit_engine,
            version_manager=self.version_manager,
            main_window=self,
        )
        
        self.logger.info(f"Edit handler initialized with model: {model_id}")
        
    def _build_ui(self):
        """Build two-pane workbench with rich-text editor."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top toolbar: Model selector
        layout.addWidget(self._create_toolbar())
        
        # Main splitter: Left (Report) | Right (Chat)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT PANE: Report Editor with toolbar
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # Create enhanced report editor
        self.report_editor = ReportEditor()
        
        # Add editor toolbar
        editor_toolbar = self.report_editor.get_toolbar()
        editor_layout.addWidget(editor_toolbar)
        editor_layout.addWidget(self.report_editor, 1)
        
        splitter.addWidget(editor_container)
        
        # RIGHT PANE: Chat Assistant
        self.chat_pane = ChatInterface()
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
            f"Welcome {self.current_user} to the Vulnerability Analysis Workbench.\n\n"
            "Upload files using the '+' button to begin analysis.",
            is_user=False
        )
    
    def _create_toolbar(self) -> QWidget:
        """Create modern unified header with model selector and finalize button."""
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.Shape.NoFrame)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {DeepSpaceColors.BG_DARK};
                border-bottom: 1px solid {DeepSpaceColors.BORDER_LIGHT};
                padding: {ModernSpacing.MD}px;
            }}
        """)
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(ModernSpacing.LG, ModernSpacing.MD, ModernSpacing.LG, ModernSpacing.MD)
        layout.setSpacing(ModernSpacing.LG)
        
        # Title/Logo
        title = QLabel("🛡 Security Audit Workbench")
        title_font = QFont(ModernTypography.PRIMARY_FONT, ModernTypography.SIZE_LG)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {DeepSpaceColors.ACCENT_BLUE};")
        layout.addWidget(title)
        
        layout.addSpacing(ModernSpacing.LG)
        
        # Model selector label
        model_label = QLabel("Model:")
        model_label.setFont(QFont(ModernTypography.PRIMARY_FONT, ModernTypography.SIZE_BASE))
        model_label.setStyleSheet(f"color: {DeepSpaceColors.TEXT_SECONDARY};")
        layout.addWidget(model_label)
        
        # Model selector
        self.model_selector = QComboBox()
        for m in self.models:
            self.model_selector.addItem(m["name"])
        self.model_selector.setMinimumWidth(200)
        self.model_selector.setMaximumWidth(250)
        self.model_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {DeepSpaceColors.BG_DARK_ALT};
                color: {DeepSpaceColors.TEXT_PRIMARY};
                border: 1px solid {DeepSpaceColors.BORDER_LIGHT};
                border-radius: {ModernBorderRadius.MD}px;
                padding: 6px 10px;
                font-family: {ModernTypography.PRIMARY_FONT};
                font-size: {ModernTypography.SIZE_BASE}px;
                min-height: 32px;
            }}
            QComboBox:hover {{
                border: 1px solid {DeepSpaceColors.ACCENT_BLUE_DIM};
                background-color: {DeepSpaceColors.BG_SECONDARY};
            }}
            QComboBox:focus {{
                border: 1px solid {DeepSpaceColors.ACCENT_BLUE};
                background-color: {DeepSpaceColors.BG_SECONDARY};
            }}
        """)
        layout.addWidget(self.model_selector)
        
        # Status indicator (pulsing dot)
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"""
            QLabel {{
                color: {DeepSpaceColors.ACCENT_LIME};
                font-size: 12px;
                padding: 0px 4px;
            }}
        """)
        layout.addWidget(status_dot)
        
        layout.addStretch()
        
        # Finalize button with glow effect
        self.finalize_btn = QPushButton("✓ Finalize Report")
        self.finalize_btn.setEnabled(False)
        self.finalize_btn.clicked.connect(self._finalize_report)
        self.finalize_btn.setMinimumHeight(36)
        self.finalize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DeepSpaceColors.TEXT_PRIMARY};
                border: 1.5px solid {DeepSpaceColors.ACCENT_BLUE_DIM};
                border-radius: {ModernBorderRadius.MD}px;
                padding: 8px 20px;
                font-weight: {ModernTypography.WEIGHT_SEMIBOLD};
                font-size: {ModernTypography.SIZE_BASE}px;
                font-family: {ModernTypography.PRIMARY_FONT};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 217, 255, 0.1);
                border: 1.5px solid {DeepSpaceColors.ACCENT_BLUE};
                color: {DeepSpaceColors.ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 217, 255, 0.2);
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {DeepSpaceColors.TEXT_MUTED};
                border: 1.5px solid {DeepSpaceColors.BORDER_LIGHT};
            }}
        """)
        layout.addWidget(self.finalize_btn)
        
        # Export button
        self.export_btn = QPushButton("⤓ Export")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._show_export_menu)
        self.export_btn.setMinimumHeight(36)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DeepSpaceColors.TEXT_PRIMARY};
                border: 1.5px solid {DeepSpaceColors.ACCENT_BLUE_DIM};
                border-radius: {ModernBorderRadius.MD}px;
                padding: 8px 20px;
                font-weight: {ModernTypography.WEIGHT_SEMIBOLD};
                font-size: {ModernTypography.SIZE_BASE}px;
                font-family: {ModernTypography.PRIMARY_FONT};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 217, 255, 0.1);
                border: 1.5px solid {DeepSpaceColors.ACCENT_BLUE};
                color: {DeepSpaceColors.ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 217, 255, 0.2);
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {DeepSpaceColors.TEXT_MUTED};
                border: 1.5px solid {DeepSpaceColors.BORDER_LIGHT};
            }}
        """)
        layout.addWidget(self.export_btn)
        
        return toolbar
    
    def _handle_file_upload(self, paths: list[str]):
        """Handle file upload from chat."""
        # Check if user has permission to analyze files
        if not self._check_permission("analyze_files"):
            self.chat_pane.add_message("[ERROR] Permission denied: analyze_files required", is_user=False)
            return
        
        # Pre-flight validation: Check files are accessible and reasonable size
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB max
        invalid_files = []
        
        for path in paths:
            if not os.path.exists(path):
                invalid_files.append(f"File not found: {os.path.basename(path)}")
            elif not os.access(path, os.R_OK):
                invalid_files.append(f"Permission denied: {os.path.basename(path)}")
            elif os.path.isfile(path) and os.path.getsize(path) > MAX_FILE_SIZE:
                invalid_files.append(f"File too large (>100MB): {os.path.basename(path)}")
        
        if invalid_files:
            self.chat_pane.add_message(
                "[ERROR] Pre-flight validation failed:\n" + "\n".join(f"  • {msg}" for msg in invalid_files),
                is_user=False
            )
            return
        
        self.chat_pane.add_message(
            f"Analyzing {len(paths)} file(s)...\n" + "\n".join([f"• {os.path.basename(p)}" for p in paths]),
            is_user=False
        )
        
        # Start background scan
        try:
            self.scan_worker = ScanWorker(paths)
            self.scan_worker.status_update.connect(lambda msg: self.chat_pane.add_message(msg, is_user=False))
            self.scan_worker.scan_complete.connect(self._handle_scan_complete)
            self.scan_worker.error_occurred.connect(self._handle_scan_error)
            self.scan_worker.start()
        except Exception as e:
            self.logger.error("Failed to start scan", error=str(e))
            self.chat_pane.add_message(f"[ERROR] Failed to start scan: {str(e)}", is_user=False)
    
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
    
    def _handle_scan_error(self, error_msg: str):
        """Handle scan error with user-friendly messaging."""
        self.logger.error("Scan failed", error=error_msg)
        
        # Format error for user without raw tracebacks
        user_msg = error_msg
        if "No such file or directory" in error_msg or "FileNotFoundError" in error_msg:
            user_msg = "File not found. Please check the file path is correct."
        elif "Permission denied" in error_msg:
            user_msg = "Permission denied. Please check file accessibility and try again."
        elif "Memory" in error_msg or "OutOfMemory" in error_msg:
            user_msg = "Insufficient memory. Please close other applications and try again."
        elif "JSON" in error_msg or "decode" in error_msg:
            user_msg = "File format error. Please check the file is valid JSON/CSV/TXT."
        
        self.chat_pane.add_message(f"[ERROR] Scan failed: {user_msg}", is_user=False)
    
    def _handle_permission_denied(self, permission: str):
        """Handle permission denied events."""
        self.logger.warning("Permission denied", permission=permission, user=self.current_user)
        self.chat_pane.add_message(f"[ACCESS DENIED] Permission '{permission}' required", is_user=False)
    
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
        """
        Handle user message in chat.
        
        Improved workflow:
        1. Detect edit commands (rewrite, undo, history, etc.)
        2. Handle special commands
        3. Process edit requests with AI
        4. Fallback to report info
        """
        try:
            text_lower = text.lower()
            
            # SPECIAL COMMANDS
            if text_lower == "undo":
                if not self.edit_ui_handler:
                    self._initialize_edit_handler()
                if self.edit_ui_handler:
                    self.edit_ui_handler.handle_undo()
                return
            
            if text_lower == "history":
                if not self.edit_ui_handler:
                    self._initialize_edit_handler()
                if self.edit_ui_handler:
                    self.edit_ui_handler.show_version_history()
                return
            
            # REWRITE INTENT DETECTION
            is_rewrite_request = EditUIHandler.is_edit_command(text)
            
            if is_rewrite_request:
                # Initialize edit handler if needed
                if not self.edit_ui_handler:
                    self._initialize_edit_handler()
                
                if not self.edit_ui_handler:
                    self.chat_pane.add_message(
                        "⚠ Failed to initialize edit handler. Please try again.",
                        is_user=False
                    )
                    return
                
                # Get selected text from report
                cursor = self.report_editor.textCursor()
                selected_text = cursor.selectedText()
                
                if not selected_text:
                    self.chat_pane.add_message(
                        "📝 No text selected.\n\n"
                        "To rewrite content:\n"
                        "1. Select text in the report editor\n"
                        "2. Ask me to rewrite it (e.g., 'make this concise', 'formal tone')",
                        is_user=False
                    )
                    return
                
                # Get model
                model_name = self.model_selector.currentText()
                model_id = None
                for m in self.models:
                    if m["name"] == model_name:
                        model_id = m.get("ollama_id") or m.get("id")
                        break
                
                if not model_id:
                    self.chat_pane.add_message(
                        "⚠ No AI model selected. Please select a model.",
                        is_user=False
                    )
                    return
                
                # Check Ollama availability
                if not is_ollama_available():
                    self.chat_pane.add_message(
                        "⚠ AI service unavailable. Please ensure Ollama is running.",
                        is_user=False
                    )
                    return
                
                # Detect report section
                all_text = self.report_editor.toPlainText()
                cursor_pos = cursor.position() - len(selected_text)
                text_before = all_text[:cursor_pos]
                section = detect_report_section(text_before)
                
                # Convert section to string if it's an enum
                section_str = section.value if hasattr(section, 'value') else str(section)
                
                # Handle edit request through UI handler
                self.edit_ui_handler.handle_edit_request(
                    user_message=text,
                    selected_text=selected_text,
                    section_name=section_str
                )
                return
            
            # FALLBACK: Report-related questions
            elif self.report_data:
                total_findings = self.report_data.get('metadata', {}).get('total_findings', 0)
                
                if text_lower in ["hi", "hello", "hey"]:
                    self.chat_pane.add_message(
                        f"👋 Hello! Your report has {total_findings} finding(s).\n\n"
                        f"📝 To edit your report:\n"
                        f"   1. Select text in the left pane\n"
                        f"   2. Ask me to 'rewrite', 'simplify', 'make formal', etc.\n\n"
                        f"Commands:\n"
                        f"   'undo' - Undo last edit\n"
                        f"   'history' - Show edit history",
                        is_user=False
                    )
                else:
                    # Generic report info
                    self.chat_pane.add_message(
                        f"📊 Your report contains {total_findings} finding(s).\n\n"
                        f"Select text to edit it or ask about a specific vulnerability.",
                        is_user=False
                    )
            
            # NO REPORT YET
            else:
                self.chat_pane.add_message(
                    "📁 No report loaded yet.\n\n"
                    "Upload files using the '+' button to begin analysis.",
                    is_user=False
                )
        
        except Exception as e:
            self.logger.error("Failed to process message", error=str(e), exc_info=True)
            self.chat_pane.add_message(
                f"❌ Error: {str(e)}\n\nPlease try again.",
                is_user=False
            )
    
    def _finalize_report(self):
        """Finalize the report (make read-only)."""
        # Check if user has permission to edit reports
        if not self._check_permission("edit_reports"):
            self.chat_pane.add_message("[ERROR] Permission denied: edit_reports required", is_user=False)
            return
        
        self.report_editor.set_finalized(True)
        self.finalize_btn.setEnabled(False)
        self.export_btn.setEnabled(True)  # Enable export after finalize
        
        self.chat_pane.add_message(
            "✓ Report finalized! You can now export the report.",
            is_user=False
        )
    
    def _show_export_menu(self):
        """Show export format menu."""
        # Check if user has permission to export
        if not self._check_permission("export_reports"):
            self.chat_pane.add_message("[ERROR] Permission denied: export_reports required", is_user=False)
            return
        
        # Create export menu
        menu = QMenu(self)
        
        # Export to Markdown
        md_action = menu.addAction("Export as Markdown")
        md_action.triggered.connect(lambda: self._export_report("markdown"))
        
        # Export to PDF
        pdf_action = menu.addAction("Export as PDF")
        pdf_action.triggered.connect(lambda: self._export_report("pdf"))
        
        # Show menu at export button position
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))
    
    def _export_report(self, format: str):
        """Export report in specified format."""
        from app.report_exporter import export_to_markdown, export_to_pdf
        
        try:
            # Get reported data
            report_data = self.report_state.get_state()
            
            # Open file dialog
            filter_map = {
                "markdown": "Markdown Files (*.md)",
                "pdf": "PDF Files (*.pdf)"
            }
            ext_map = {
                "markdown": "md",
                "pdf": "pdf"
            }
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Export Report as {format.upper()}",
                f"report.{ext_map[format]}",
                filter_map[format]
            )
            
            if not file_path:
                return
            
            # Export based on format
            success = False
            error_msg = ""
            
            if format == "markdown":
                success, error_msg = export_to_markdown(report_data, self.report_workspace, file_path)
            elif format == "pdf":
                success, error_msg = export_to_pdf(report_data, self.report_workspace, file_path)
            
            # Notify user
            if success:
                self.chat_pane.add_message(
                    f"✓ Report exported successfully to {file_path}",
                    is_user=False
                )
            else:
                self.chat_pane.add_message(
                    f"[ERROR] Export failed: {error_msg}",
                    is_user=False
                )
        except Exception as e:
            self.chat_pane.add_message(
                f"[ERROR] Export error: {str(e)}",
                is_user=False
            )
