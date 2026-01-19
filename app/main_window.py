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
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QFrame,
    QStackedWidget,
    QProgressBar,
    QScrollArea,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from typing import Optional
import tempfile
import os

from app.hardware import detect_hardware
from app.model_registry import get_model_registry
from app.document_ingestion import ingest_file
from app.rule_engine import run_rules
from app.llm_reasoner import explain_single_finding
from app.ollama_client import is_ollama_available
# Phase 10: Severity Override & Report Workspace
from app.finding_integration import enhance_findings_with_severity_fields
from app.severity_override import get_final_severity, override_severity, clear_severity_override
from app.report_model import ReportWorkspace
# Phase 12: Report Generation, AI Assistance, Export
from app.report_generator import generate_sample_report
from app.ai_assistant import assist_report_editing, discuss_vulnerability
from app.report_exporter import export_to_markdown, export_to_pdf
# Workflow: Page-based guided workflow
from app.report_state import ReportState, ReportStatus


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Offline Hybrid Vulnerability Analysis Assistant")
        self.resize(1400, 1000)
        # Cinematic: Pure black background for entertainment-grade feel
        self.setStyleSheet("QMainWindow { background-color: rgb(0, 0, 0); }")

        self.models = get_model_registry()
        self.ingested_chunks: list[dict] = []
        self.rule_findings: list[dict] = []
        self.enhanced_findings: list[dict] = []  # Phase 10: Findings with severity fields
        self.llm_explanations: dict[str, dict] = {}  # finding_id -> LLM output
        # Phase 10: Report Workspace
        self.report_workspace: Optional[ReportWorkspace] = None
        # Phase 12: Sample Report Data
        self.report_data: Optional[dict] = None  # Generated report structure
        # Workflow: Central report state
        self.report_state = ReportState()
        # Current page index (0-4 for pages 1-5)
        self.current_page = 0
        # Hardware info (cached)
        self.hardware_info = detect_hardware()
        # Chat panel orientation: True = horizontal (right side), False = vertical (bottom)
        self.chat_panel_horizontal = True

        self._build_ui()

    # ======================================================
    # UI CONSTRUCTION
    # ======================================================

    def _build_ui(self) -> None:
        """Build page-based workflow UI."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar (always visible)
        layout.addWidget(self._build_top_bar())
        
        # Page stack
        self.page_stack = QStackedWidget()
        self.page_stack.addWidget(self._build_page_1_upload())  # Page 1
        self.page_stack.addWidget(self._build_page_2_scan())  # Page 2
        self.page_stack.addWidget(self._build_page_3_draft())  # Page 3
        self.page_stack.addWidget(self._build_page_4_review())  # Page 4
        self.page_stack.addWidget(self._build_page_5_export())  # Page 5
        
        layout.addWidget(self.page_stack, 1)
        
        # Navigation bar
        layout.addWidget(self._build_navigation_bar())
        
        self.setCentralWidget(container)
        self._update_navigation()

    # ======================================================
    # TOP BAR — HARDWARE + MODEL
    # ======================================================

    def _build_top_bar(self) -> QWidget:
        """Build cinematic top bar with red accent border."""
        # Hardware info icon button - minimal, optional display
        hardware_btn = QPushButton("⚙")
        hardware_btn.setToolTip("Show Hardware Information")
        hardware_btn.setMinimumWidth(32)  # Reduced from 36
        hardware_btn.setMinimumHeight(32)  # Reduced from 36
        hardware_btn.setMaximumWidth(32)  # Reduced from 36
        hardware_btn.setMaximumHeight(32)  # Reduced from 36
        hardware_btn.clicked.connect(self._show_hardware_info)
        hardware_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgb(10, 10, 10);"
            "  color: rgb(220, 220, 220);"
            "  border: 1px solid rgb(200, 0, 0);"
            "  font-size: 16pt;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: rgb(20, 0, 0);"
            "  border: 1px solid rgb(255, 50, 50);"
            "}"
        )

        # Model selector - cinematic with red accent (reduced height)
        self.model_selector = QComboBox()
        for m in self.models:
            self.model_selector.addItem(m["name"])
        self.model_selector.setMinimumHeight(32)  # Reduced from 36 (~30% reduction from original 40)
        self.model_selector.setStyleSheet(
            "QComboBox {"
            "  background-color: rgb(10, 10, 10);"
            "  color: rgb(220, 220, 220);"
            "  border: 1px solid rgb(200, 0, 0);"
            "  padding: 8px 12px;"
            "  font-weight: bold;"
            "}"
            "QComboBox::drop-down {"
            "  border: none;"
            "  background-color: rgb(20, 0, 0);"
            "  width: 30px;"
            "}"
            "QComboBox::hover {"
            "  border: 1px solid rgb(255, 50, 50);"
            "}"
            "QComboBox QAbstractItemView {"
            "  background-color: rgb(0, 0, 0);"
            "  color: rgb(220, 220, 220);"
            "  border: 2px solid rgb(200, 0, 0);"
            "  selection-background-color: rgb(200, 0, 0);"
            "}"
        )

        # Model label - bold, red accent
        model_label = QLabel("MODEL")
        model_label.setStyleSheet("color: rgb(200, 0, 0); font-weight: bold;")
        model_font = QFont()
        model_font.setPointSize(10)
        model_font.setWeight(QFont.Weight.Bold)
        model_label.setFont(model_font)

        top = QWidget()
        top.setStyleSheet("background-color: rgb(0, 0, 0); border-bottom: 3px solid rgb(200, 0, 0);")
        layout = QHBoxLayout(top)
        layout.setContentsMargins(40, 10, 40, 10)  # Reduced vertical padding by ~30% (16 → 10)
        layout.setSpacing(16)  # Reduced from 20
        layout.addWidget(hardware_btn, 0)  # Icon button on the left
        layout.addStretch()  # Push model selector to the right
        layout.addWidget(model_label, 0)
        layout.addWidget(self.model_selector, 1)

        return top

    # ======================================================
    # NAVIGATION BAR
    # ======================================================

    def _build_navigation_bar(self) -> QWidget:
        """Build cinematic navigation bar with red accent and bold buttons."""
        nav_bar = QWidget()
        nav_bar.setMaximumHeight(64)  # Reduced from 80
        nav_bar.setStyleSheet("background-color: rgb(0, 0, 0); border-top: 3px solid rgb(200, 0, 0);")
        
        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(40, 14, 40, 14)  # Reduced vertical padding from 20 to 14
        layout.setSpacing(20)  # Reduced from 24
        
        # Previous button - secondary style with red border (more compact)
        self.prev_btn = self._create_cinematic_button("◄ PREVIOUS", primary=False)
        self.prev_btn.clicked.connect(self._go_to_previous_page)
        self.prev_btn.setMinimumWidth(120)  # Reduced from 140
        layout.addWidget(self.prev_btn)
        
        # Page indicator - bold, red accent
        self.page_label = QLabel("Page 1 of 5: Document Upload")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_font = QFont("Times New Roman", 12)  # Reduced from 13
        page_font.setWeight(QFont.Weight.Bold)
        self.page_label.setFont(page_font)
        self.page_label.setStyleSheet("color: rgb(200, 0, 0);")
        layout.addWidget(self.page_label, 1)
        
        # Next button - primary style, red background (more compact)
        self.next_btn = self._create_cinematic_button("NEXT ►", primary=True)
        self.next_btn.clicked.connect(self._go_to_next_page)
        self.next_btn.setMinimumWidth(120)  # Reduced from 140
        layout.addWidget(self.next_btn)
        
        return nav_bar

    def _update_navigation(self) -> None:
        """Update navigation buttons based on current page and state."""
        # Update page label
        page_names = [
            "Page 1 of 5: START INVESTIGATION",
            "Page 2 of 5: AUTOMATED SCAN",
            "Page 3 of 5: DRAFT DOSSIER",
            "Page 4 of 5: REVIEW & EDIT",
            "Page 5 of 5: FINALIZE CASE",
        ]
        self.page_label.setText(page_names[self.current_page])
        
        # Update Previous button
        self.prev_btn.setEnabled(self.current_page > 0)
        
        # Update Next button based on page state
        if self.current_page == 0:  # Page 1
            self.next_btn.setEnabled(len(self.report_state.uploaded_paths) > 0)
        elif self.current_page == 1:  # Page 2
            self.next_btn.setEnabled(self.report_state.status == ReportStatus.SCANNED)
        elif self.current_page == 2:  # Page 3
            self.next_btn.setEnabled(self.report_state.status == ReportStatus.DRAFT_GENERATED)
        elif self.current_page == 3:  # Page 4
            self.next_btn.setEnabled(self.report_state.status == ReportStatus.IN_REVIEW)
        else:  # Page 5
            self.next_btn.setEnabled(False)  # Last page

    def _go_to_previous_page(self) -> None:
        """Navigate to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.page_stack.setCurrentIndex(self.current_page)
            self._update_navigation()

    def _go_to_next_page(self) -> None:
        """Navigate to next page."""
        if self.current_page < 4:
            # Validate current page before proceeding
            if self.current_page == 0 and len(self.report_state.uploaded_paths) == 0:
                QMessageBox.warning(self, "No Documents", "Please upload documents first.")
                return
            elif self.current_page == 1 and self.report_state.status != ReportStatus.SCANNED:
                QMessageBox.warning(self, "Scan Not Complete", "Please wait for scan to complete.")
                return
            elif self.current_page == 2 and self.report_state.status != ReportStatus.DRAFT_GENERATED:
                QMessageBox.warning(self, "Draft Not Generated", "Please wait for draft generation.")
                return
            
            self.current_page += 1
            self.page_stack.setCurrentIndex(self.current_page)
            self._update_navigation()
            
            # Trigger page-specific actions
            if self.current_page == 1:
                self._start_scan()
            elif self.current_page == 2:
                self._generate_draft_pdf()
            elif self.current_page == 3:
                self._enter_review_mode()

    # ======================================================
    # PAGE 1: DOCUMENT UPLOAD
    # ======================================================

    def _build_page_1_upload(self) -> QWidget:
        """Build Page 1: Start Investigation - cinematic black & red design."""
        page = QWidget()
        page.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(80, 50, 80, 50)  # Reduced from 100, 80, 100, 80
        layout.setSpacing(32)  # Reduced from 50
        
        # Header - bold, red, dramatic
        header = self._create_section_header("START INVESTIGATION")
        layout.addWidget(header)
        layout.addSpacing(16)  # Reduced from 24
        
        # Instructions - light gray, readable
        instructions = QLabel(
            "Upload documents for vulnerability analysis.\n"
            "Supported: Individual files (.txt, .log, .csv, .json, .conf), ZIP archives, or folders."
        )
        instructions.setWordWrap(True)
        inst_font = QFont()
        inst_font.setPointSize(11)
        instructions.setFont(inst_font)
        instructions.setStyleSheet("color: rgb(220, 220, 220); line-height: 1.8;")
        layout.addWidget(instructions)
        layout.addSpacing(24)  # Reduced from 40
        
        # Upload button - primary, red, heavy (more compact)
        upload_btn = self._create_cinematic_button("UPLOAD DOCUMENTS", primary=True)
        upload_btn.clicked.connect(self._page_1_upload_documents)
        upload_btn.setMaximumWidth(280)  # Reduced from 300
        layout.addWidget(upload_btn)
        layout.addSpacing(32)  # Reduced from 50
        
        # Upload summary - cinematic panel with red border
        summary_label = self._create_subheader("UPLOADED DOCUMENTS")
        layout.addWidget(summary_label)
        layout.addSpacing(12)  # Reduced from 16
        
        self.page_1_summary = QPlainTextEdit(readOnly=True)
        self.page_1_summary.setPlaceholderText("No documents uploaded yet.")
        self.page_1_summary.setMaximumHeight(280)  # Increased from 200 for better usability
        summary_font = QFont("Courier New", 10)
        self.page_1_summary.setFont(summary_font)
        self.page_1_summary.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 16px;"  # Reduced from 20px
        )
        layout.addWidget(self.page_1_summary)
        
        layout.addStretch()
        
        return page

    def _page_1_upload_documents(self) -> None:
        """Handle document upload on Page 1."""
        # Option 1: Select individual files or ZIP files
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select documents, ZIP files, or folders",
            "",
            "All Supported (*.txt *.log *.conf *.config *.csv *.json *.zip);;"
            "Text Files (*.txt *.log *.conf *.config);;"
            "Data Files (*.csv *.json);;"
            "ZIP Archives (*.zip);;"
            "All Files (*.*)",
        )
        
        # Option 2: Select directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Or select a folder to scan recursively",
            "",
        )
        
        paths = list(file_paths)
        if dir_path:
            paths.append(dir_path)

        if not paths:
            return

        # Store uploaded paths (don't ingest yet - that happens on Page 2)
        self.report_state.set_uploaded(paths)
        
        # Update summary
        summary_lines = []
        for path in paths:
            summary_lines.append(f"✓ {path}")
        self.page_1_summary.setPlainText("\n".join(summary_lines))
        
        self._update_navigation()

    # ======================================================
    # PAGE 2: AUTOMATED SCAN
    # ======================================================

    def _build_page_2_scan(self) -> QWidget:
        """Build Page 2: Automated Scan - cinematic black & red design."""
        page = QWidget()
        page.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(80, 50, 80, 50)  # Reduced from 100, 80, 100, 80
        layout.setSpacing(32)  # Reduced from 50
        
        # Header - bold, red
        header = self._create_section_header("AUTOMATED SCAN")
        layout.addWidget(header)
        layout.addSpacing(16)  # Reduced from 24
        
        # Instructions - light gray
        instructions = QLabel(
            "Running rule-based vulnerability scan on uploaded documents.\n"
            "This process is deterministic and does not use AI for detection."
        )
        instructions.setWordWrap(True)
        inst_font = QFont()
        inst_font.setPointSize(11)
        instructions.setFont(inst_font)
        instructions.setStyleSheet("color: rgb(220, 220, 220); line-height: 1.8;")
        layout.addWidget(instructions)
        layout.addSpacing(24)  # Reduced from 40
        
        # Progress bar - red accent
        self.page_2_progress = QProgressBar()
        self.page_2_progress.setRange(0, 0)  # Indeterminate
        self.page_2_progress.setVisible(False)
        self.page_2_progress.setMinimumHeight(4)
        self.page_2_progress.setStyleSheet(
            "QProgressBar {"
            "  border: 2px solid rgb(200, 0, 0);"
            "  background-color: rgb(10, 10, 10);"
            "}"
            "QProgressBar::chunk {"
            "  background-color: rgb(200, 0, 0);"
            "}"
        )
        layout.addWidget(self.page_2_progress)
        layout.addSpacing(24)  # Reduced from 40
        
        # Status text - cinematic panel
        status_label = self._create_subheader("SCAN STATUS")
        layout.addWidget(status_label)
        layout.addSpacing(12)  # Reduced from 16
        
        self.page_2_status = QPlainTextEdit(readOnly=True)
        self.page_2_status.setPlaceholderText("Click 'Next' from Page 1 to start scan...")
        status_font = QFont("Courier New", 10)
        self.page_2_status.setFont(status_font)
        self.page_2_status.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 16px;"  # Reduced from 20px
        )
        layout.addWidget(self.page_2_status)
        layout.addSpacing(24)  # Reduced from 40
        
        # Results summary - cinematic panel
        results_label = self._create_subheader("SCAN RESULTS")
        layout.addWidget(results_label)
        layout.addSpacing(12)  # Reduced from 16
        
        self.page_2_results = QPlainTextEdit(readOnly=True)
        self.page_2_results.setMaximumHeight(160)
        results_font = QFont("Courier New", 10)
        self.page_2_results.setFont(results_font)
        self.page_2_results.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 16px;"  # Reduced from 20px
        )
        layout.addWidget(self.page_2_results)
        
        layout.addStretch()
        
        return page

    def _start_scan(self) -> None:
        """Start automated scan (called when entering Page 2)."""
        if self.report_state.status == ReportStatus.SCANNED:
            # Already scanned, just show results
            self._display_scan_results()
            return
        
        # Show progress
        self.page_2_progress.setVisible(True)
        self.page_2_status.clear()
        self.page_2_status.appendPlainText("Starting scan...")
        self.next_btn.setEnabled(False)
        
        # Ingest documents
        self.page_2_status.appendPlainText("Ingesting documents...")
        all_chunks = []
        for path in self.report_state.uploaded_paths:
            try:
                chunks = ingest_file(path)
                all_chunks.extend(chunks)
                self.page_2_status.appendPlainText(f"✓ Processed: {path} ({len(chunks)} chunks)")
            except Exception as e:
                self.page_2_status.appendPlainText(f"✗ Error processing {path}: {str(e)}")
        
        if not all_chunks:
            self.page_2_status.appendPlainText("ERROR: No chunks extracted. Cannot proceed.")
            self.page_2_progress.setVisible(False)
            return
        
        # Run rule-based scan
        self.page_2_status.appendPlainText("Running rule-based vulnerability detection...")
        results = run_rules(all_chunks)
        self.rule_findings = results
        
        # Enhance with Phase 10 fields
        self.page_2_status.appendPlainText("Processing findings...")
        self.enhanced_findings = enhance_findings_with_severity_fields(results)
        
        # Update report state
        self.report_state.set_scanned(all_chunks, self.enhanced_findings)
        
        # Create report workspace
        if self.report_state.report_workspace is None:
            self.report_state.report_workspace = ReportWorkspace(
                scope="Vulnerability Analysis",
                analyst_name=None,
                executive_summary="",
            )
            self.report_state.report_workspace.add_findings(self.enhanced_findings)
        
        # Generate report data
        model_id = None
        if is_ollama_available():
            model_index = self.model_selector.currentIndex()
            if model_index >= 0 and model_index < len(self.models):
                model_id = self.models[model_index]["ollama_id"]
        
        self.report_data = generate_sample_report(
            findings=self.enhanced_findings,
            scope=self.report_state.report_workspace.scope,
            model_id=model_id,
        )
        
        # Populate executive summary
        if self.report_state.report_workspace and not self.report_state.report_workspace.executive_summary:
            generated_summary = self.report_data.get("executive_summary", "")
            self.report_state.report_workspace.update_executive_summary(generated_summary)
        
        self.report_state.update_report_data(self.report_data)
        
        # Hide progress, show results
        self.page_2_progress.setVisible(False)
        self.page_2_status.appendPlainText("✓ Scan completed successfully!")
        self._display_scan_results()
        self._update_navigation()

    def _display_scan_results(self) -> None:
        """Display scan results summary."""
        if not self.enhanced_findings:
            self.page_2_results.setPlainText("No findings detected.")
            return
        
        active = [f for f in self.enhanced_findings if not f.get("suppressed", False)]
        suppressed = [f for f in self.enhanced_findings if f.get("suppressed", False)]
        
        from app.severity_override import get_final_severity
        severity_counts = {"High": 0, "Medium": 0, "Low": 0}
        for finding in active:
            sev = get_final_severity(finding)
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        results_text = (
            f"Total Findings: {len(self.enhanced_findings)}\n"
            f"Active Findings: {len(active)}\n"
            f"Suppressed Findings: {len(suppressed)}\n\n"
            f"Severity Breakdown:\n"
            f"  High: {severity_counts.get('High', 0)}\n"
            f"  Medium: {severity_counts.get('Medium', 0)}\n"
            f"  Low: {severity_counts.get('Low', 0)}\n"
        )
        
        self.page_2_results.setPlainText(results_text)

    # ======================================================
    # PAGE 3: DRAFT PDF PREVIEW
    # ======================================================

    def _build_page_3_draft(self) -> QWidget:
        """Build Page 3: Draft Dossier - cinematic black & red design."""
        page = QWidget()
        page.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(80, 50, 80, 50)  # Reduced from 100, 80, 100, 80
        layout.setSpacing(32)  # Reduced from 50
        
        # Header - bold, red, dramatic
        header = self._create_section_header("DRAFT DOSSIER")
        layout.addWidget(header)
        layout.addSpacing(16)  # Reduced from 24
        
        # Instructions - light gray
        instructions = QLabel(
            "Preview of the automatically generated draft report.\n"
            "This is a DRAFT - you will be able to edit it on the next page."
        )
        instructions.setWordWrap(True)
        inst_font = QFont()
        inst_font.setPointSize(11)
        instructions.setFont(inst_font)
        instructions.setStyleSheet("color: rgb(220, 220, 220); line-height: 1.8;")
        layout.addWidget(instructions)
        layout.addSpacing(24)  # Reduced from 40
        
        # PDF preview area - cinematic dossier panel
        preview_label = self._create_subheader("DOSSIER PREVIEW")
        layout.addWidget(preview_label)
        layout.addSpacing(12)  # Reduced from 16
        
        self.page_3_pdf_view = QPlainTextEdit(readOnly=True)
        self.page_3_pdf_view.setPlaceholderText("Draft PDF will be generated when you reach this page...")
        preview_font = QFont("Courier New", 10)
        self.page_3_pdf_view.setFont(preview_font)
        self.page_3_pdf_view.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 20px;"  # Reduced from 24px
        )
        layout.addWidget(self.page_3_pdf_view)
        
        layout.addStretch()
        
        return page

    def _generate_draft_pdf(self) -> None:
        """Generate draft PDF when entering Page 3."""
        if self.report_state.draft_pdf_path and os.path.exists(self.report_state.draft_pdf_path):
            # Already generated, just display
            self._display_draft_preview()
            return
        
        if not self.report_state.report_workspace or not self.report_state.report_data:
            QMessageBox.warning(self, "No Report", "Report data not available. Please go back and complete scan.")
            return
        
        # Generate draft PDF to temporary file
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as tmp_file:
                draft_path = tmp_file.name
            
            # Mark as draft in report data
            draft_data = self.report_state.report_data.copy()
            draft_data["is_draft"] = True
            draft_data["draft_label"] = "Sample Report - Draft"
            
            success, error = export_to_pdf(
                draft_data,
                self.report_state.report_workspace,
                draft_path,
            )
            
            if success:
                self.report_state.set_draft_generated(draft_path)
                self._display_draft_preview()
                self._update_navigation()
            else:
                QMessageBox.warning(
                    self,
                    "PDF Generation Failed",
                    f"Failed to generate draft PDF: {error}\n\nNote: PDF export requires reportlab library."
                )
                # Fallback: Show markdown preview
                self._display_draft_preview_markdown()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate draft: {str(e)}")
            self._display_draft_preview_markdown()

    def _display_draft_preview(self) -> None:
        """Display draft PDF preview (as text for now - can be enhanced with PDF viewer)."""
        if self.report_state.draft_pdf_path:
            self.page_3_pdf_view.setPlainText(
                f"Draft PDF generated: {self.report_state.draft_pdf_path}\n\n"
                "Note: Full PDF preview requires PDF viewer integration.\n"
                "The draft report is ready for review on the next page."
            )
        else:
            self._display_draft_preview_markdown()

    def _display_draft_preview_markdown(self) -> None:
        """Display draft as Markdown preview (fallback)."""
        if not self.report_state.report_data:
            return
        
        # Generate markdown preview
        preview_lines = [
            "=" * 70,
            "SAMPLE REPORT - DRAFT",
            "=" * 70,
            "",
            "Executive Summary:",
            "-" * 70,
            self.report_state.report_workspace.executive_summary if self.report_state.report_workspace else "",
            "",
            "Scope & Methodology:",
            "-" * 70,
            self.report_state.report_data.get("methodology", ""),
            "",
            f"Findings: {len(self.report_state.report_data.get('findings', []))} findings",
            "",
            "=" * 70,
            "This is a DRAFT. Review and edit on the next page.",
            "=" * 70,
        ]
        
        self.page_3_pdf_view.setPlainText("\n".join(preview_lines))

    # ======================================================
    # PAGE 4: REVIEW & EDIT MODE
    # ======================================================

    def _build_page_4_review(self) -> QWidget:
        """Build Page 4: Review & Edit - cinematic black & red design with toggleable chat."""
        page = QWidget()
        page.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 12, 24, 24)  # Reduced margins: top 20→12, sides 32→24
        layout.setSpacing(8)  # Reduced from 12 - pull content up
        
        # Header - bold, red
        header = self._create_section_header("REVIEW & EDIT")
        layout.addWidget(header)
        layout.addSpacing(4)  # Reduced from 8 - minimize gap between header and content
        
        # Main container for preview and chat (with splitter)
        self.page_4_container = QWidget()
        container_layout = QVBoxLayout(self.page_4_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Splitter: PDF preview and chat (orientation can be toggled)
        self.page_4_splitter = QSplitter(Qt.Horizontal)  # Start with horizontal (right side)
        self._update_splitter_style()
        self.page_4_splitter.setChildrenCollapsible(False)  # Prevent collapsing, but we'll hide it
        self.page_4_splitter.setHandleWidth(3)  # Reduced from 4px - less dominant
        
        # PDF Preview (left) - cinematic dossier panel with chat icon
        preview_widget = QWidget()
        preview_widget.setStyleSheet("background-color: rgb(0, 0, 0);")
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(16, 12, 16, 16)  # Reduced padding: top 20→12, sides 20→16
        preview_layout.setSpacing(12)  # Reduced from 16
        
        # Header row with label and chat icon
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(12)
        
        preview_label = self._create_subheader("DOSSIER PREVIEW (EDITABLE)")
        header_row.addWidget(preview_label)
        header_row.addStretch()
        
        # Chat toggle icon button (like VS Code Copilot)
        self.page_4_chat_toggle_btn = QPushButton("💬")
        self.page_4_chat_toggle_btn.setToolTip("Toggle Assistant Console")
        self.page_4_chat_toggle_btn.setMinimumWidth(36)
        self.page_4_chat_toggle_btn.setMinimumHeight(36)
        self.page_4_chat_toggle_btn.setMaximumWidth(36)
        self.page_4_chat_toggle_btn.setMaximumHeight(36)
        self.page_4_chat_toggle_btn.clicked.connect(self._toggle_chat_panel)
        self.page_4_chat_toggle_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgb(10, 10, 10);"
            "  color: rgb(220, 220, 220);"
            "  border: 1px solid rgb(200, 0, 0);"
            "  font-size: 16pt;"
            "}"
            "QPushButton:hover {"
            "  background-color: rgb(20, 0, 0);"
            "  border: 1px solid rgb(255, 50, 50);"
            "}"
        )
        header_row.addWidget(self.page_4_chat_toggle_btn)
        
        # Orientation toggle button (right/bottom)
        self.page_4_orientation_btn = QPushButton("↔")
        self.page_4_orientation_btn.setToolTip("Toggle Chat Position (Right/Bottom)")
        self.page_4_orientation_btn.setMinimumWidth(36)
        self.page_4_orientation_btn.setMinimumHeight(36)
        self.page_4_orientation_btn.setMaximumWidth(36)
        self.page_4_orientation_btn.setMaximumHeight(36)
        self.page_4_orientation_btn.clicked.connect(self._toggle_chat_orientation)
        self.page_4_orientation_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgb(10, 10, 10);"
            "  color: rgb(220, 220, 220);"
            "  border: 1px solid rgb(200, 0, 0);"
            "  font-size: 16pt;"
            "}"
            "QPushButton:hover {"
            "  background-color: rgb(20, 0, 0);"
            "  border: 1px solid rgb(255, 50, 50);"
            "}"
        )
        header_row.addWidget(self.page_4_orientation_btn)
        
        preview_layout.addLayout(header_row)
        
        self.page_4_report_preview = QPlainTextEdit()
        self.page_4_report_preview.setPlaceholderText("Report preview will appear here...")
        preview_font = QFont("Courier New", 10)
        self.page_4_report_preview.setFont(preview_font)
        self.page_4_report_preview.textChanged.connect(self._on_report_preview_changed)
        self.page_4_report_preview.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 16px;"  # Reduced from 20px - increase content area
        )
        preview_layout.addWidget(self.page_4_report_preview)
        
        self.page_4_splitter.addWidget(preview_widget)
        
        # Chat Interface (right) - assistant console (initially hidden)
        self.page_4_chat_widget = self._build_chat_panel()
        self.page_4_splitter.addWidget(self.page_4_chat_widget)
        
        # Set initial sizes: preview takes all space, chat is hidden
        self.page_4_splitter.setSizes([1000, 0])  # Chat has 0 size initially
        self.page_4_chat_widget.setVisible(False)  # Hide chat initially
        
        # Set stretch factors - report preview is primary, assistant console is secondary
        self.page_4_splitter.setStretchFactor(0, 2)  # Increased from 1 - report preview gets more space
        self.page_4_splitter.setStretchFactor(1, 1)  # Increased from 0 - assistant console gets proper weight
        
        container_layout.addWidget(self.page_4_splitter)
        layout.addWidget(self.page_4_container)
        
        return page

    def _enter_review_mode(self) -> None:
        """Enter review mode (called when entering Page 4)."""
        self.report_state.set_in_review()
        self._update_report_preview()
        self._update_navigation()
    
    def _update_splitter_style(self) -> None:
        """Update splitter style based on current orientation."""
        if self.chat_panel_horizontal:
            # Horizontal splitter (right side)
            self.page_4_splitter.setStyleSheet(
                "QSplitter::handle {"
                "  background-color: rgb(200, 0, 0);"
                "  width: 3px;"
                "}"
                "QSplitter::handle:hover {"
                "  background-color: rgb(255, 50, 50);"
                "}"
            )
        else:
            # Vertical splitter (bottom)
            self.page_4_splitter.setStyleSheet(
                "QSplitter::handle {"
                "  background-color: rgb(200, 0, 0);"
                "  height: 3px;"
                "}"
                "QSplitter::handle:hover {"
                "  background-color: rgb(255, 50, 50);"
                "}"
            )
    
    def _toggle_chat_orientation(self) -> None:
        """Toggle chat panel orientation between right side and bottom."""
        if not hasattr(self, 'page_4_chat_widget') or not hasattr(self, 'page_4_splitter'):
            return
        
        # Store current visibility and sizes
        was_visible = self.page_4_chat_widget.isVisible()
        current_sizes = self.page_4_splitter.sizes()
        
        # Remove widgets from splitter
        preview_widget = self.page_4_splitter.widget(0)
        chat_widget = self.page_4_splitter.widget(1)
        
        # Toggle orientation
        self.chat_panel_horizontal = not self.chat_panel_horizontal
        
        # Remove old splitter from container
        container_layout = self.page_4_container.layout()
        container_layout.removeWidget(self.page_4_splitter)
        self.page_4_splitter.deleteLater()
        
        # Create new splitter with new orientation
        if self.chat_panel_horizontal:
            self.page_4_splitter = QSplitter(Qt.Horizontal)
        else:
            self.page_4_splitter = QSplitter(Qt.Vertical)
        
        self._update_splitter_style()
        self.page_4_splitter.setChildrenCollapsible(False)
        self.page_4_splitter.setHandleWidth(3)
        
        # Add widgets back in correct order
        self.page_4_splitter.addWidget(preview_widget)
        self.page_4_splitter.addWidget(chat_widget)
        
        # Restore visibility and sizes
        if was_visible:
            self.page_4_chat_widget.setVisible(True)
            if self.chat_panel_horizontal:
                # Horizontal: 65% preview, 35% chat
                total_width = self.page_4_splitter.width() if self.page_4_splitter.width() > 0 else 1400
                preview_size = int(total_width * 0.65)
                chat_size = int(total_width * 0.35)
                self.page_4_splitter.setSizes([preview_size, chat_size])
            else:
                # Vertical: 70% preview, 30% chat
                total_height = self.page_4_splitter.height() if self.page_4_splitter.height() > 0 else 800
                preview_size = int(total_height * 0.7)
                chat_size = int(total_height * 0.3)
                self.page_4_splitter.setSizes([preview_size, chat_size])
        else:
            self.page_4_chat_widget.setVisible(False)
            if self.chat_panel_horizontal:
                self.page_4_splitter.setSizes([1000, 0])
            else:
                self.page_4_splitter.setSizes([1000, 0])
        
        # Set stretch factors
        self.page_4_splitter.setStretchFactor(0, 2)
        self.page_4_splitter.setStretchFactor(1, 1)
        
        # Add splitter back to container
        container_layout.addWidget(self.page_4_splitter)
        
        # Update orientation button icon
        if self.chat_panel_horizontal:
            self.page_4_orientation_btn.setText("↔")
            self.page_4_orientation_btn.setToolTip("Toggle Chat Position (Right/Bottom) - Currently: Right")
        else:
            self.page_4_orientation_btn.setText("↕")
            self.page_4_orientation_btn.setToolTip("Toggle Chat Position (Right/Bottom) - Currently: Bottom")
    
    def _toggle_chat_panel(self) -> None:
        """Toggle chat panel visibility (like VS Code Copilot)."""
        if not hasattr(self, 'page_4_chat_widget') or not hasattr(self, 'page_4_splitter'):
            return
        
        is_visible = self.page_4_chat_widget.isVisible()
        
        if is_visible:
            # Hide chat panel - make preview full screen
            self.page_4_chat_widget.setVisible(False)
            # Set chat size to 0 to hide it completely
            self.page_4_splitter.setSizes([1000, 0])
            # Update button appearance
            self.page_4_chat_toggle_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: rgb(10, 10, 10);"
                "  color: rgb(220, 220, 220);"
                "  border: 1px solid rgb(200, 0, 0);"
                "  font-size: 16pt;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgb(20, 0, 0);"
                "  border: 1px solid rgb(255, 50, 50);"
                "}"
            )
        else:
            # Show chat panel - resize splitter based on orientation
            self.page_4_chat_widget.setVisible(True)
            if self.chat_panel_horizontal:
                # Horizontal: 65% preview, 35% chat
                total_width = self.page_4_splitter.width()
                if total_width > 0:
                    preview_size = int(total_width * 0.65)
                    chat_size = int(total_width * 0.35)
                    self.page_4_splitter.setSizes([preview_size, chat_size])
                else:
                    self.page_4_splitter.setSizes([900, 500])
            else:
                # Vertical: 70% preview, 30% chat
                total_height = self.page_4_splitter.height()
                if total_height > 0:
                    preview_size = int(total_height * 0.7)
                    chat_size = int(total_height * 0.3)
                    self.page_4_splitter.setSizes([preview_size, chat_size])
                else:
                    self.page_4_splitter.setSizes([700, 300])
            # Update button appearance to show it's active
            self.page_4_chat_toggle_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: rgb(20, 0, 0);"
                "  color: rgb(255, 255, 255);"
                "  border: 2px solid rgb(200, 0, 0);"
                "  font-size: 16pt;"
                "}"
                "QPushButton:hover {"
                "  background-color: rgb(30, 0, 0);"
                "  border: 2px solid rgb(255, 50, 50);"
                "}"
            )

    def _update_report_preview(self) -> None:
        """Update report preview with current report state."""
        if not self.report_state.report_data or not self.report_state.report_workspace:
            return
        
        # Generate markdown preview of current report state
        lines = [
            "=" * 70,
            "SAMPLE REPORT - DRAFT",
            "=" * 70,
            "",
            "Executive Summary:",
            "-" * 70,
            self.report_state.report_workspace.executive_summary,
            "",
            "Scope & Methodology:",
            "-" * 70,
            self.report_state.report_data.get("methodology", ""),
            "",
            "Findings:",
            "-" * 70,
        ]
        
        findings = self.report_state.report_data.get("findings", [])
        for finding in findings:
            lines.append(f"\n{finding.get('vulnerability_id', 'UNKNOWN')}: {finding.get('title', 'Unknown')}")
            lines.append(f"  Severity: {finding.get('severity', 'Unknown')}")
            lines.append(f"  Affected Files: {', '.join(finding.get('affected_files', []))}")
            if finding.get('ai_suggested_explanation'):
                lines.append(f"  AI Explanation: {finding.get('ai_suggested_explanation')[:100]}...")
        
        lines.append("\n" + "=" * 70)
        lines.append("This is a DRAFT. Make edits above or use AI chat below.")
        lines.append("=" * 70)
        
        self.page_4_report_preview.setPlainText("\n".join(lines))

    def _on_report_preview_changed(self) -> None:
        """Handle manual edits to report preview."""
        # Update executive summary if user edits it
        text = self.page_4_report_preview.toPlainText()
        if self.report_state.report_workspace:
            # Extract executive summary from preview (basic parsing)
            # Try to extract from "Executive Summary:" section
            if "Executive Summary:" in text:
                parts = text.split("Executive Summary:")
                if len(parts) > 1:
                    exec_part = parts[1].split("-" * 70)[0].strip()
                    if exec_part:
                        self.report_state.report_workspace.update_executive_summary(exec_part)
                        # Update report data
                        if self.report_state.report_data:
                            self.report_state.report_data["executive_summary"] = exec_part

    def _regenerate_report_preview(self) -> None:
        """Regenerate report preview after edits."""
        self._update_report_preview()

    # ======================================================
    # PAGE 5: FINAL CONFIRMATION & EXPORT
    # ======================================================

    def _build_page_5_export(self) -> QWidget:
        """Build Page 5: Finalize Case - cinematic black & red design."""
        page = QWidget()
        page.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(80, 50, 80, 50)  # Reduced from 100, 80, 100, 80
        layout.setSpacing(32)  # Reduced from 50
        
        # Header - bold, red
        header = self._create_section_header("FINALIZE CASE")
        layout.addWidget(header)
        layout.addSpacing(16)  # Reduced from 24
        
        # Instructions - light gray
        instructions = QLabel(
            "Review your report one final time.\n"
            "Once you mark it as final, you can export it in multiple formats."
        )
        instructions.setWordWrap(True)
        inst_font = QFont()
        inst_font.setPointSize(11)
        instructions.setFont(inst_font)
        instructions.setStyleSheet("color: rgb(220, 220, 220); line-height: 1.8;")
        layout.addWidget(instructions)
        layout.addSpacing(24)  # Reduced from 40
        
        # Final confirmation button - primary, red, heavy
        self.page_5_confirm_btn = self._create_cinematic_button("MARK REPORT AS FINAL", primary=True)
        self.page_5_confirm_btn.clicked.connect(self._confirm_final_report)
        self.page_5_confirm_btn.setMaximumWidth(300)  # Reduced from 320
        layout.addWidget(self.page_5_confirm_btn)
        layout.addSpacing(16)  # Reduced from 24
        
        # Status - bold, red when final
        self.page_5_status = QLabel("Report status: DRAFT (not yet confirmed as final)")
        status_font = QFont()
        status_font.setPointSize(11)
        status_font.setWeight(QFont.Weight.Bold)
        self.page_5_status.setFont(status_font)
        self.page_5_status.setStyleSheet("color: rgb(180, 180, 180);")
        layout.addWidget(self.page_5_status)
        layout.addSpacing(32)  # Reduced from 50
        
        layout.addWidget(self._create_separator())
        layout.addSpacing(24)  # Reduced from 40
        
        # Export buttons (disabled until confirmed) - cinematic
        export_label = self._create_subheader("EXPORT OPTIONS")
        layout.addWidget(export_label)
        layout.addSpacing(16)  # Reduced from 24
        
        export_layout = QHBoxLayout()
        export_layout.setSpacing(20)
        
        self.page_5_export_pdf_btn = self._create_cinematic_button("EXPORT PDF", primary=False)
        self.page_5_export_pdf_btn.clicked.connect(self._export_final_pdf)
        self.page_5_export_pdf_btn.setEnabled(False)
        export_layout.addWidget(self.page_5_export_pdf_btn)
        
        self.page_5_export_md_btn = self._create_cinematic_button("EXPORT MARKDOWN", primary=False)
        self.page_5_export_md_btn.clicked.connect(self._export_final_markdown)
        self.page_5_export_md_btn.setEnabled(False)
        export_layout.addWidget(self.page_5_export_md_btn)
        
        self.page_5_export_json_btn = self._create_cinematic_button("EXPORT JSON", primary=False)
        self.page_5_export_json_btn.clicked.connect(self._export_final_json)
        self.page_5_export_json_btn.setEnabled(False)
        export_layout.addWidget(self.page_5_export_json_btn)
        
        layout.addLayout(export_layout)
        
        layout.addStretch()
        
        return page

    def _confirm_final_report(self) -> None:
        """Confirm report as final."""
        reply = QMessageBox.question(
            self,
            "Confirm Final Report",
            "Are you sure you want to mark this report as final?\n\n"
            "Once confirmed, you will be able to export the report.\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.report_state.confirm_final()
            self.page_5_status.setText("Report status: FINAL (confirmed)")
            self.page_5_status.setStyleSheet("color: rgb(200, 0, 0); font-weight: bold;")
            self.page_5_confirm_btn.setEnabled(False)
            self.page_5_export_pdf_btn.setEnabled(True)
            self.page_5_export_md_btn.setEnabled(True)
            self.page_5_export_json_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Report Confirmed",
                "Report marked as final. You can now export it."
            )

    def _export_final_pdf(self) -> None:
        """Export final PDF (without draft label)."""
        if not self.report_state.can_export():
            QMessageBox.warning(self, "Not Final", "Report must be confirmed as final before export.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Final Report (PDF)",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not path:
            return
        
        # Create final report data (remove draft label)
        final_data = self.report_state.report_data.copy()
        final_data["is_draft"] = False
        final_data.pop("draft_label", None)
        
        try:
            success, error = export_to_pdf(
                final_data,
                self.report_state.report_workspace,
                path,
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", f"Final report exported to:\n{path}")
            else:
                QMessageBox.critical(self, "Export Failed", f"Failed to export PDF:\n{error}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def _export_final_markdown(self) -> None:
        """Export final Markdown."""
        if not self.report_state.can_export():
            QMessageBox.warning(self, "Not Final", "Report must be confirmed as final before export.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Final Report (Markdown)",
            "",
            "Markdown Files (*.md *.markdown)"
        )
        
        if not path:
            return
        
        final_data = self.report_state.report_data.copy()
        final_data["is_draft"] = False
        final_data.pop("draft_label", None)
        
        try:
            success, error = export_to_markdown(
                final_data,
                self.report_state.report_workspace,
                path,
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", f"Final report exported to:\n{path}")
            else:
                QMessageBox.critical(self, "Export Failed", f"Failed to export Markdown:\n{error}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def _export_final_json(self) -> None:
        """Export final JSON."""
        if not self.report_state.can_export():
            QMessageBox.warning(self, "Not Final", "Report must be confirmed as final before export.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Final Report (JSON)",
            "",
            "JSON Files (*.json)"
        )
        
        if not path:
            return
        
        try:
            import json
            report_dict = self.report_state.report_workspace.to_dict()
            # Add report data
            report_dict["report_data"] = self.report_state.report_data
            report_dict["is_final"] = True
            report_dict["final_confirmed_at"] = self.report_state.final_confirmed_at
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Export Successful", f"Final report exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    # ======================================================
    # MAIN WORKSPACE — DOCUMENTS + FINDINGS (LEGACY - KEEP FOR REFERENCE)
    # ======================================================

    def _build_main_workspace(self) -> QWidget:
        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(self._build_documents_panel())
        splitter.addWidget(self._build_findings_panel())
        splitter.addWidget(self._build_report_panel())  # Phase 10: Report Workspace

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        return splitter

    # ---------------- Documents ----------------

    def _build_documents_panel(self) -> QWidget:
        self.docs_view = QPlainTextEdit(readOnly=True)
        # Use monospaced font for file paths
        mono_font = QFont("Courier New", 9)
        self.docs_view.setFont(mono_font)

        load_btn = QPushButton("Load Documents")
        load_btn.clicked.connect(self._load_documents)
        load_btn.setMinimumHeight(32)

        scan_btn = QPushButton("Scan")
        scan_btn.clicked.connect(self._run_scan)
        scan_btn.setMinimumHeight(32)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(self._create_section_header("Documents"))
        layout.addWidget(load_btn)
        layout.addWidget(self.docs_view)
        layout.addWidget(scan_btn)

        return panel

    # ---------------- Findings ----------------

    def _build_findings_panel(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        # Use monospaced font for findings (better for IDs and structured data)
        mono_font = QFont("Courier New", 9)
        
        self.findings_view = QPlainTextEdit(readOnly=True)
        self.findings_view.setFont(mono_font)
        
        self.suppressed_view = QPlainTextEdit(readOnly=True)
        self.suppressed_view.setFont(mono_font)
        # Make suppressed findings visually distinct but subtle
        self.suppressed_view.setStyleSheet("color: rgb(100, 100, 100);")

        # Phase 10: Severity override button
        override_btn = QPushButton("Override Severity (Analyst Decision)")
        override_btn.clicked.connect(self._override_severity_dialog)
        override_btn.setMinimumHeight(32)

        findings_widget = QWidget()
        findings_layout = QVBoxLayout(findings_widget)
        findings_layout.setContentsMargins(8, 8, 8, 8)
        findings_layout.setSpacing(8)
        findings_layout.addWidget(self._create_section_header("Findings"))
        findings_layout.addWidget(override_btn)
        findings_layout.addWidget(self.findings_view)

        splitter.addWidget(findings_widget)
        splitter.addWidget(self._wrap("Suppressed (Audit Only)", self.suppressed_view))

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        return splitter

    # ---------------- Report Workspace (Phase 10) ----------------

    def _build_report_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(self._create_section_header("Report Workspace"))

        # Executive Summary Editor
        exec_label = QLabel("Executive Summary:")
        exec_label.setFont(QFont(exec_label.font().family(), exec_label.font().pointSize()))
        layout.addWidget(exec_label)
        self.executive_summary_editor = QPlainTextEdit()
        self.executive_summary_editor.setPlaceholderText(
            "Enter executive summary...\n\n"
            "This summary will be included in the final report."
        )
        # Better line spacing for summary editor
        editor_font = QFont()
        editor_font.setPointSize(9)
        self.executive_summary_editor.setFont(editor_font)
        self.executive_summary_editor.textChanged.connect(self._on_executive_summary_changed)
        layout.addWidget(self.executive_summary_editor)

        # Separator between editing and statistics
        layout.addWidget(self._create_separator())

        # Report Stats Display
        stats_label = QLabel("Report Statistics:")
        stats_label.setFont(QFont(stats_label.font().family(), stats_label.font().pointSize()))
        layout.addWidget(stats_label)
        
        self.report_stats_view = QPlainTextEdit(readOnly=True)
        self.report_stats_view.setMaximumHeight(150)
        # Use monospaced font for statistics (better alignment)
        stats_font = QFont("Courier New", 9)
        self.report_stats_view.setFont(stats_font)
        layout.addWidget(self.report_stats_view)

        # Note: AI-assisted editing is now available through the unified chat interface

        # Separator before save action
        layout.addWidget(self._create_separator())

        # Export Buttons (Phase 12)
        export_layout = QHBoxLayout()
        
        save_json_btn = QPushButton("Export JSON")
        save_json_btn.clicked.connect(self._save_report)
        save_json_btn.setMinimumHeight(32)
        export_layout.addWidget(save_json_btn)
        
        export_md_btn = QPushButton("Export Markdown")
        export_md_btn.clicked.connect(self._export_markdown)
        export_md_btn.setMinimumHeight(32)
        export_layout.addWidget(export_md_btn)
        
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self._export_pdf)
        export_pdf_btn.setMinimumHeight(32)
        export_layout.addWidget(export_pdf_btn)
        
        layout.addLayout(export_layout)

        return panel

    # ======================================================
    # CHAT PANEL
    # ======================================================

    def _build_chat_panel(self) -> QWidget:
        """Build cinematic assistant console with black & red theme."""
        chat_widget = QWidget()
        chat_widget.setStyleSheet("background-color: rgb(0, 0, 0);")
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced from 24, 24, 24, 24
        layout.setSpacing(16)  # Reduced from 20
        
        # Header - bold, red
        chat_header = self._create_subheader("ASSISTANT CONSOLE")
        layout.addWidget(chat_header)
        
        # Unified chat interface - cinematic panel
        self.chat_output = QPlainTextEdit(readOnly=True)
        output_font = QFont()
        output_font.setPointSize(10)
        self.chat_output.setFont(output_font)
        self.chat_output.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 14px;"  # Reduced from 16px - more content area
        )
        
        layout.addWidget(self.chat_output)
        layout.addSpacing(12)  # Reduced from 16
        
        # Input area - cinematic, deliberate
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)  # Reduced from 16
        
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(80)  # Reduced from 90
        self.chat_input.setPlaceholderText(
            "Ask about vulnerabilities, request report edits, or get explanations..."
        )
        input_font = QFont()
        input_font.setPointSize(10)
        self.chat_input.setFont(input_font)
        self.chat_input.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 8px;"  # Reduced from 10px - more content area
        )
        input_layout.addWidget(self.chat_input, 1)
        
        send_btn = self._create_cinematic_button("SEND", primary=True)
        send_btn.clicked.connect(self._send_chat)
        send_btn.setFixedWidth(90)  # Reduced from 100
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)

        return chat_widget

    # ======================================================
    # HARDWARE INFO DIALOG
    # ======================================================

    def _show_hardware_info(self) -> None:
        """Show hardware information in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Hardware Information")
        dialog.setStyleSheet("QDialog { background-color: rgb(0, 0, 0); }")
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("HARDWARE INFORMATION")
        header_font = QFont("Times New Roman", 18)
        header_font.setWeight(QFont.Weight.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: rgb(200, 0, 0); padding: 8px 0px;")
        layout.addWidget(header)
        
        # Hardware info display
        info_text = QPlainTextEdit(readOnly=True)
        gpu_text = ""
        if self.hardware_info['gpu']['available']:
            gpu_text = f"GPU: {self.hardware_info['gpu']['model']}\nGPU VRAM: {self.hardware_info['gpu']['vram_gb']} GB\n"
        else:
            gpu_text = "GPU: Not detected\n"
        
        info_text.setPlainText(
            f"CPU: {self.hardware_info['cpu']['model']}\n"
            f"CPU Cores: {self.hardware_info['cpu']['cores']}\n"
            f"CPU Threads: {self.hardware_info['cpu']['threads']}\n"
            f"\n"
            f"RAM: {self.hardware_info['ram']['total_gb']} GB\n"
            f"\n"
            f"{gpu_text}"
        )
        info_font = QFont("Courier New", 10)
        info_text.setFont(info_font)
        info_text.setStyleSheet(
            "background-color: rgb(10, 10, 10);"
            "color: rgb(220, 220, 220);"
            "border: 2px solid rgb(200, 0, 0);"
            "padding: 20px;"
        )
        layout.addWidget(info_text, 1)
        
        # Close button
        close_btn = self._create_cinematic_button("CLOSE", primary=True)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setMaximumWidth(150)
        layout.addWidget(close_btn)
        layout.setAlignment(close_btn, Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

    # ======================================================
    # HELPERS
    # ======================================================

    def _wrap(self, title: str, widget: QWidget) -> QWidget:
        """Wrap widget with section header and consistent styling."""
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        header = QLabel(title)
        header_font = QFont()
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        layout.addWidget(widget)
        return box

    def _create_section_header(self, text: str) -> QLabel:
        """Create a bold, cinematic section header with red accent."""
        header = QLabel(text)
        # Large, bold serif font - dramatic and commanding
        font = QFont("Times New Roman", 20)
        font.setWeight(QFont.Weight.Bold)
        header.setFont(font)
        header.setStyleSheet("color: rgb(200, 0, 0); padding: 12px 0px;")  # Strong red
        return header

    def _create_separator(self) -> QFrame:
        """Create a dramatic divider with red accent."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: rgb(200, 0, 0); max-height: 2px;")  # Red divider
        return line

    def _create_subheader(self, text: str) -> QLabel:
        """Create a subheader with red accent."""
        subheader = QLabel(text)
        # Bold serif for subheaders - maintains dramatic feel
        font = QFont("Times New Roman", 14)
        font.setWeight(QFont.Weight.Bold)
        subheader.setFont(font)
        subheader.setStyleSheet("color: rgb(220, 220, 220); padding: 6px 0px;")  # Light gray
        return subheader

    def _create_cinematic_button(self, text: str, primary: bool = False) -> QPushButton:
        """Create a heavy, intentional button with red accent."""
        btn = QPushButton(text)
        btn.setMinimumHeight(42)  # Reduced from 48 for better balance
        # Bold sans-serif for buttons - strong and clear
        btn_font = QFont()
        btn_font.setPointSize(11)
        btn_font.setWeight(QFont.Weight.Bold)
        btn.setFont(btn_font)
        
        if primary:
            # Primary: Red background, white text - bold and dramatic
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: rgb(200, 0, 0);"
                "  color: rgb(255, 255, 255);"
                "  border: 2px solid rgb(255, 50, 50);"
                "  padding: 10px 24px;"  # Reduced from 12px 28px
                "}"
                "QPushButton:hover {"
                "  background-color: rgb(220, 0, 0);"
                "  border: 2px solid rgb(255, 80, 80);"
                "}"
                "QPushButton:pressed {"
                "  background-color: rgb(180, 0, 0);"
                "}"
                "QPushButton:disabled {"
                "  background-color: rgb(40, 40, 40);"
                "  color: rgb(100, 100, 100);"
                "  border: 2px solid rgb(60, 60, 60);"
                "}"
            )
        else:
            # Secondary: Transparent with red border
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: transparent;"
                "  color: rgb(220, 220, 220);"
                "  border: 2px solid rgb(200, 0, 0);"
                "  padding: 10px 24px;"  # Reduced from 12px 28px
                "}"
                "QPushButton:hover {"
                "  background-color: rgb(30, 0, 0);"
                "  border: 2px solid rgb(255, 50, 50);"
                "  color: rgb(255, 255, 255);"
                "}"
                "QPushButton:pressed {"
                "  background-color: rgb(50, 0, 0);"
                "}"
                "QPushButton:disabled {"
                "  background-color: rgb(10, 10, 10);"
                "  color: rgb(80, 80, 80);"
                "  border: 2px solid rgb(40, 40, 40);"
                "}"
            )
        return btn

    # ======================================================
    # ACTIONS
    # ======================================================

    def _load_documents(self) -> None:
        """Load documents from files, ZIP archives, or directories."""
        # Option 1: Select individual files or ZIP files
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select documents, ZIP files, or folders",
            "",
            "All Supported (*.txt *.log *.conf *.config *.csv *.json *.zip);;"
            "Text Files (*.txt *.log *.conf *.config);;"
            "Data Files (*.csv *.json);;"
            "ZIP Archives (*.zip);;"
            "All Files (*.*)",
        )
        
        # Option 2: Select directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Or select a folder to scan recursively",
            "",
        )
        
        paths = list(file_paths)
        if dir_path:
            paths.append(dir_path)

        if not paths:
            return

        self.ingested_chunks.clear()
        self.docs_view.clear()
        self.findings_view.clear()
        self.suppressed_view.clear()

        total_chunks = 0
        for path in paths:
            try:
                chunks = ingest_file(path)
                self.ingested_chunks.extend(chunks)
                total_chunks += len(chunks)
                self.docs_view.appendPlainText(f"{path} → {len(chunks)} chunks")
            except Exception as e:
                self.docs_view.appendPlainText(f"{path} → ERROR: {str(e)}")
        
        if total_chunks > 0:
            self.docs_view.appendPlainText(f"\nTotal: {total_chunks} chunks from {len(paths)} source(s)")

    def _run_scan(self) -> None:
        self.findings_view.clear()
        self.suppressed_view.clear()
        self.llm_explanations.clear()

        if not self.ingested_chunks:
            self.findings_view.setPlainText("No documents loaded.")
            return

        # Run rule engine (unchanged)
        results = run_rules(self.ingested_chunks)
        self.rule_findings = results  # Store for LLM access

        # Phase 10: Enhance findings with severity override fields
        self.enhanced_findings = enhance_findings_with_severity_fields(results)

        # Phase 10: Create or update Report Workspace
        if self.report_workspace is None:
            self.report_workspace = ReportWorkspace(
                scope="Vulnerability Analysis",
                analyst_name=None,  # Can be set by user later
                executive_summary="",
            )
            # Initialize executive summary editor
            self.executive_summary_editor.setPlainText("")
        else:
            # Preserve existing executive summary
            existing_summary = self.report_workspace.executive_summary
            self.executive_summary_editor.setPlainText(existing_summary)
        
        # Add findings to report (replace existing findings)
        self.report_workspace.findings.clear()
        self.report_workspace.add_findings(self.enhanced_findings)

        # Phase 12: Generate sample report with LLM-generated executive summary
        # Get model ID for LLM generation
        model_id = None
        if is_ollama_available():
            model_index = self.model_selector.currentIndex()
            if model_index >= 0 and model_index < len(self.models):
                model_id = self.models[model_index]["ollama_id"]
        
        self.report_data = generate_sample_report(
            findings=self.enhanced_findings,
            scope=self.report_workspace.scope,
            model_id=model_id,
        )
        
        # Phase 12: Populate executive summary with generated sample if empty
        if not self.report_workspace.executive_summary:
            generated_summary = self.report_data.get("executive_summary", "")
            self.report_workspace.update_executive_summary(generated_summary)
            self.executive_summary_editor.setPlainText(generated_summary)

        # Update UI displays
        self._update_findings_display()
        self._update_report_stats()

        # Display suppressed findings (separate from active findings)
        suppressed = [r for r in self.enhanced_findings if r["suppressed"]]
        self.suppressed_view.clear()
        
        for i, r in enumerate(suppressed, 1):
            # Evidence is now a list (Phase 8.2 normalized schema)
            evidence_file = r["evidence"][0]["file"] if r["evidence"] else "unknown"
            # Format suppressed findings with clear separation
            self.suppressed_view.appendPlainText(
                f"\n[{i}] [{r['rule_id']}] {r['title']} (SUPPRESSED)\n"
                f"    Source: {evidence_file}\n"
            )


    def _send_chat(self) -> None:
        """Unified chat interface for all LLM interactions."""
        msg = self.chat_input.toPlainText().strip()
        if not msg:
            return

        # Check if Ollama is available
        if not is_ollama_available():
            self.chat_output.appendPlainText(
                f"\nUser: {msg}\n"
                "AI: Ollama is not available. Please ensure Ollama is running.\n\n"
            )
            self.chat_input.clear()
            return

        # Get model ID
        model_index = self.model_selector.currentIndex()
        if model_index < 0 or model_index >= len(self.models):
            self.chat_output.appendPlainText(
                f"\nUser: {msg}\n"
                "AI: No model selected.\n\n"
            )
            self.chat_input.clear()
            return

        model_id = self.models[model_index]["ollama_id"]

        # Display user message
        self.chat_output.appendPlainText(f"\nUser: {msg}\n")

        # Route request based on content
        msg_lower = msg.lower()
        
        # Check if this is a report editing request
        edit_keywords = ["rewrite", "improve", "edit", "change", "make more", "make less", 
                        "clarify", "simplify", "formal", "technical", "executive", "summary"]
        is_edit_request = any(keyword in msg_lower for keyword in edit_keywords)
        
        # Check if this is a request to explain a finding
        explain_keywords = ["explain", "what is", "describe", "tell me about", "analyze"]
        is_explain_request = any(keyword in msg_lower for keyword in explain_keywords)
        
        # Check if this is a vulnerability discussion
        discussion_keywords = ["why", "how", "what", "is this", "can this", "would this"]
        is_discussion = any(keyword in msg_lower for keyword in discussion_keywords)

        # Handle report editing request
        if is_edit_request and self.report_state.report_workspace is not None:
            # Get selected text from report preview (Page 4) or executive summary
            if self.current_page == 3 and hasattr(self, 'page_4_report_preview'):
                text_cursor = self.page_4_report_preview.textCursor()
                had_selection = text_cursor.hasSelection()
                if had_selection:
                    current_text = text_cursor.selectedText()
                    selection_start = text_cursor.selectionStart()
                    selection_end = text_cursor.selectionEnd()
                else:
                    current_text = self.page_4_report_preview.toPlainText()
            elif self.report_state.report_workspace:
                # Fallback: use executive summary
                current_text = self.report_state.report_workspace.executive_summary
                had_selection = False
            else:
                current_text = ""
                had_selection = False
            
            if current_text.strip():
                self.chat_output.appendPlainText("AI: Processing text editing request...\n")
                success, suggested_text = assist_report_editing(model_id, current_text, msg, temperature=0.3)
                
                if success:
                    self.chat_output.appendPlainText(
                        f"\n{'='*70}\n"
                        f"AI SUGGESTION (Advisory):\n"
                        f"{'='*70}\n"
                        f"{suggested_text}\n"
                        f"{'='*70}\n"
                    )
                    
                    # Ask if user wants to apply
                    reply = QMessageBox.question(
                        self,
                        "Apply AI Suggestion?",
                        "Do you want to apply this AI suggestion to the Executive Summary?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # Apply suggestion
                        if self.current_page == 3 and hasattr(self, 'page_4_report_preview'):
                            if had_selection:
                                # Replace selected text
                                text_cursor = self.page_4_report_preview.textCursor()
                                text_cursor.setPosition(selection_start)
                                text_cursor.setPosition(selection_end, QTextCursor.MoveMode.KeepAnchor)
                                text_cursor.insertText(suggested_text)
                                self.page_4_report_preview.setTextCursor(text_cursor)
                            else:
                                # Replace entire text
                                self.page_4_report_preview.setPlainText(suggested_text)
                            
                            # Update report workspace
                            if self.report_state.report_workspace:
                                self.report_state.report_workspace.update_executive_summary(suggested_text)
                            
                            # Regenerate preview
                            self._regenerate_report_preview()
                            self.chat_output.appendPlainText("AI: Suggestion applied to report preview.\n\n")
                        elif self.report_state.report_workspace:
                            # Update executive summary in workspace
                            self.report_state.report_workspace.update_executive_summary(suggested_text)
                            self.chat_output.appendPlainText("AI: Suggestion applied to Executive Summary.\n\n")
                    else:
                        self.chat_output.appendPlainText("AI: Suggestion not applied. You can manually copy it if desired.\n\n")
                else:
                    self.chat_output.appendPlainText(f"AI: Error - {suggested_text}\n\n")
            else:
                self.chat_output.appendPlainText(
                    "AI: No text available to edit. Please ensure the report has content.\n\n"
                )
            self.chat_input.clear()
            return

        # Handle finding explanation or discussion
        if not self.report_state.enhanced_findings:
            self.chat_output.appendPlainText(
                "AI: No findings available. Please run a scan first.\n\n"
            )
            self.chat_input.clear()
            return

        active_findings = [f for f in self.enhanced_findings if not f.get("suppressed", False)]
        if not active_findings:
            self.chat_output.appendPlainText(
                "AI: No active findings available for discussion.\n\n"
            )
            self.chat_input.clear()
            return

        # Use first active finding (can be enhanced to select specific finding by ID)
        finding = active_findings[0]
        
        # Handle full explanation request
        if is_explain_request and ("finding" in msg_lower or "vulnerability" in msg_lower or "issue" in msg_lower):
            self.chat_output.appendPlainText(
                f"AI: Generating detailed explanation for finding [{finding.get('rule_id')}] {finding.get('title')}...\n"
            )
            success, output = explain_single_finding(model_id, finding, temperature=0.2)
            
            if success and isinstance(output, dict):
                finding_id = finding.get("finding_id", "unknown")
                self.llm_explanations[finding_id] = output
                
                self.chat_output.appendPlainText(
                    f"\n{'='*70}\n"
                    f"AI SUGGESTION (Advisory Only - Analyst Review Required)\n"
                    f"{'='*70}\n"
                    f"\nSUMMARY:\n{'-'*70}\n{output.get('summary', 'N/A')}\n"
                    f"\nIMPACT:\n{'-'*70}\n{output.get('impact', 'N/A')}\n"
                    f"\nREMEDIATION:\n{'-'*70}\n"
                )
                
                for idx, step in enumerate(output.get('remediation', []), 1):
                    self.chat_output.appendPlainText(f"  {idx}. {step}")
                
                suggested_sev = output.get('suggested_severity', 'Unknown')
                self.chat_output.appendPlainText(
                    f"\nSUGGESTED SEVERITY: {suggested_sev}\n"
                    f"\nCONFIDENCE NOTE:\n{'-'*70}\n{output.get('confidence_note', 'N/A')}\n"
                    f"\n{'='*70}\n"
                    f"DISCLAIMER: {output.get('disclaimer', 'N/A')}\n"
                    f"{'='*70}\n\n"
                )
            else:
                error_msg = output if isinstance(output, str) else "Unknown error"
                self.chat_output.appendPlainText(
                    f"AI: Failed to generate explanation - {error_msg}\n\n"
                )
        else:
            # Handle general discussion about finding
            self.chat_output.appendPlainText(
                f"AI (Advisory): Discussing [{finding.get('rule_id')}] {finding.get('title')}\n"
            )
            success, answer = discuss_vulnerability(model_id, finding, msg, temperature=0.3)
            
            if success:
                self.chat_output.appendPlainText(f"{answer}\n\n")
            else:
                self.chat_output.appendPlainText(f"AI: Error - {answer}\n\n")
        
        self.chat_input.clear()

    # ======================================================
    # PHASE 10: SEVERITY OVERRIDE & REPORT WORKSPACE
    # ======================================================

    def _update_findings_display(self) -> None:
        """Update findings display with Phase 10 severity information."""
        # This is called from _run_scan, but can be called after overrides
        self.findings_view.clear()
        
        active = [r for r in self.enhanced_findings if not r["suppressed"]]
        
        for i, r in enumerate(active, 1):
            evidence_file = r["evidence"][0]["file"] if r["evidence"] else "unknown"
            suggested_sev = r.get("suggested_severity", r.get("severity_suggested", "Unknown"))
            final_sev = get_final_severity(r)
            is_overridden = r.get("severity_overridden", False)
            
            # Format severity with emphasis for high severity
            severity_marker = ""
            if final_sev == "High":
                severity_marker = "[HIGH]"
            elif final_sev == "Medium":
                severity_marker = "[MEDIUM]"
            elif final_sev == "Low":
                severity_marker = "[LOW]"
            
            severity_display = f"Suggested: {suggested_sev} | Final: {final_sev} {severity_marker}"
            if is_overridden:
                severity_display += " [OVERRIDDEN]"
                reason = r.get("severity_override_reason")
                if reason:
                    severity_display += f"\n  Override Reason: {reason}"
            
            # Format with better spacing and structure
            self.findings_view.appendPlainText(
                f"\n{'='*70}\n"
                f"Finding #{i}: {r['title']}\n"
                f"  Rule ID: {r['rule_id']}\n"
                f"  Severity: {severity_display}\n"
                f"  Source: {evidence_file}\n"
                f"  Finding ID: {r.get('finding_id', 'unknown')}\n"
            )

    def _update_report_stats(self) -> None:
        """Update report statistics display."""
        if self.report_workspace is None:
            self.report_stats_view.setPlainText("No report workspace created.")
            return

        stats = self.report_workspace.get_summary_stats()
        
        # Format statistics with better alignment (using monospaced font)
        stats_text = (
            f"{'Total Findings:':<25} {stats['total_findings']:>4}\n"
            f"{'Active Findings:':<25} {stats['active_findings']:>4}\n"
            f"{'Suppressed Findings:':<25} {stats['suppressed_findings']:>4}\n"
            f"{'Overridden Severities:':<25} {stats['overridden_severities']:>4}\n\n"
            f"{'Severity Breakdown:':<25}\n"
            f"  {'High:':<23} {stats['severity_breakdown'].get('High', 0):>4}\n"
            f"  {'Medium:':<23} {stats['severity_breakdown'].get('Medium', 0):>4}\n"
            f"  {'Low:':<23} {stats['severity_breakdown'].get('Low', 0):>4}\n"
        )
        
        self.report_stats_view.setPlainText(stats_text)

    def _override_severity_dialog(self) -> None:
        """Phase 10: Dialog to override severity for a finding."""
        if not self.enhanced_findings:
            QMessageBox.warning(
                self,
                "No Findings",
                "No findings available. Please run a scan first."
            )
            return

        active_findings = [f for f in self.enhanced_findings if not f.get("suppressed", False)]
        if not active_findings:
            QMessageBox.warning(
                self,
                "No Active Findings",
                "No active findings available. All findings are suppressed."
            )
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Override Severity (Analyst Decision)")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Finding selection
        layout.addWidget(QLabel("Select Finding:"))
        finding_list = QComboBox()
        for finding in active_findings:
            finding_id = finding.get("finding_id", "unknown")
            title = finding.get("title", "Unknown")
            current_sev = get_final_severity(finding)
            finding_list.addItem(f"[{finding_id[:8]}...] {title} (Current: {current_sev})", finding)
        layout.addWidget(finding_list)

        # Severity selection
        layout.addWidget(QLabel("Final Severity (Analyst Decision):"))
        severity_combo = QComboBox()
        severity_combo.addItems(["High", "Medium", "Low"])
        # Set current severity as default
        if active_findings:
            current_sev = get_final_severity(active_findings[0])
            index = severity_combo.findText(current_sev)
            if index >= 0:
                severity_combo.setCurrentIndex(index)
        layout.addWidget(severity_combo)

        # Override reason
        layout.addWidget(QLabel("Override Reason (Optional):"))
        reason_input = QPlainTextEdit()
        reason_input.setPlaceholderText("Enter reason for override...")
        reason_input.setMaximumHeight(100)
        # Pre-fill if already overridden
        if active_findings:
            existing_reason = active_findings[0].get("severity_override_reason")
            if existing_reason:
                reason_input.setPlainText(existing_reason)
        layout.addWidget(reason_input)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Update severity combo when finding selection changes
        def on_finding_changed(index: int) -> None:
            finding = finding_list.itemData(index)
            if finding:
                current_sev = get_final_severity(finding)
                sev_index = severity_combo.findText(current_sev)
                if sev_index >= 0:
                    severity_combo.setCurrentIndex(sev_index)
                existing_reason = finding.get("severity_override_reason")
                reason_input.setPlainText(existing_reason or "")

        finding_list.currentIndexChanged.connect(on_finding_changed)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_finding = finding_list.currentData()
            if not selected_finding:
                return

            final_severity = severity_combo.currentText()
            reason = reason_input.toPlainText().strip() or None

            # Apply override
            finding_id = selected_finding.get("finding_id")
            
            # Find and update finding in enhanced_findings
            for i, finding in enumerate(self.enhanced_findings):
                if finding.get("finding_id") == finding_id:
                    # Apply override
                    overridden_finding = override_severity(finding, final_severity, reason)
                    self.enhanced_findings[i] = overridden_finding
                    
                    # Update in report workspace
                    if self.report_workspace:
                        # Find and update in report
                        for j, report_finding in enumerate(self.report_workspace.findings):
                            if report_finding.get("finding_id") == finding_id:
                                self.report_workspace.findings[j] = overridden_finding.copy()
                                # Update timestamp
                                from datetime import datetime
                                self.report_workspace.updated_at = datetime.utcnow().isoformat() + "Z"
                                break
                    
                    break

            # Update UI
            self._update_findings_display()
            self._update_report_stats()

            QMessageBox.information(
                self,
                "Severity Overridden",
                f"Severity overridden to {final_severity}.\n"
                f"Finding ID: {finding_id[:8]}...\n"
                "This is the final severity (Analyst Decision)."
            )

    def _on_executive_summary_changed(self) -> None:
        """Phase 10: Update executive summary in report workspace."""
        if self.report_workspace is None:
            return

        summary = self.executive_summary_editor.toPlainText()
        self.report_workspace.update_executive_summary(summary)

    def _save_report(self) -> None:
        """Phase 10: Save report to JSON file."""
        if self.report_workspace is None:
            QMessageBox.warning(
                self,
                "No Report",
                "No report workspace available. Please run a scan first."
            )
            return

        import json
        from pathlib import Path

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "",
            "JSON Files (*.json)"
        )

        if not path:
            return

        try:
            report_dict = self.report_workspace.to_dict()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                "Report Saved",
                f"Report saved to:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save report:\n{str(e)}"
            )

    # ======================================================
    # PHASE 12: REPORT GENERATION, AI ASSISTANCE, EXPORT
    # ======================================================


    def _export_markdown(self) -> None:
        """Phase 12: Export report to Markdown format."""
        if self.report_workspace is None or self.report_data is None:
            QMessageBox.warning(
                self,
                "No Report",
                "No report available. Please run a scan first."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report (Markdown)",
            "",
            "Markdown Files (*.md *.markdown)"
        )

        if not path:
            return

        try:
            success, error = export_to_markdown(
                self.report_data,
                self.report_workspace,
                path,
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Report exported to Markdown:\n{path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export report:\n{error}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export report:\n{str(e)}"
            )

    def _export_pdf(self) -> None:
        """Phase 12: Export report to PDF format."""
        if self.report_workspace is None or self.report_data is None:
            QMessageBox.warning(
                self,
                "No Report",
                "No report available. Please run a scan first."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report (PDF)",
            "",
            "PDF Files (*.pdf)"
        )

        if not path:
            return

        try:
            success, error = export_to_pdf(
                self.report_data,
                self.report_workspace,
                path,
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Report exported to PDF:\n{path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export report:\n{error}\n\nNote: PDF export requires reportlab library."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export report:\n{str(e)}\n\nNote: PDF export requires reportlab library."
            )
