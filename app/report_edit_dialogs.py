"""
Diff Preview Dialog (Phase 14 - Part 3)

UI component for displaying before/after diffs of AI edits.
Shows:
- Original text
- New text
- Changes highlighted
- Justification for changes
- Accept/Reject buttons
- Validation messages
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, Signal
from typing import Optional

from app.report_edit_engine import EditPatch
from app.logging_config import get_logger

logger = get_logger("DiffPreviewDialog")


class DiffPreviewDialog(QDialog):
    """
    Dialog for previewing and approving report edits.

    Signals:
    - approved: EditPatch - User approved the patch
    - rejected: None - User rejected the patch
    """

    approved = Signal(object)  # EditPatch
    rejected = Signal()

    def __init__(self, patch: EditPatch, validation_messages: list[str], parent=None):
        """
        Initialize diff preview dialog.

        Args:
            patch: EditPatch to display
            validation_messages: List of validation result messages
            parent: Parent widget
        """
        super().__init__(parent)
        self.patch = patch
        self.validation_messages = validation_messages

        self.setWindowTitle("Review AI Edit - Diff Preview")
        self.setGeometry(100, 100, 1000, 700)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title and section info
        title_layout = QHBoxLayout()
        title_label = QLabel(f"Edit: {self.patch.section}")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        intent_label = QLabel(f"Intent: {self.patch.intent.intent_type.value}")
        intent_label.setFont(QFont("Segoe UI", 10))
        intent_label.setStyleSheet("color: #0078d4;")
        title_layout.addWidget(intent_label)

        layout.addLayout(title_layout)

        # Validation messages
        if self.validation_messages:
            validation_layout = QVBoxLayout()
            validation_layout.setContentsMargins(8, 8, 8, 8)
            validation_layout.setSpacing(4)

            validation_label = QLabel("Validation Results:")
            validation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            validation_layout.addWidget(validation_label)

            for msg in self.validation_messages:
                msg_label = QLabel(msg)
                msg_label.setFont(QFont("Consolas", 9))
                # Color based on success/failure
                if msg.startswith("✓"):
                    msg_label.setStyleSheet("color: #107C10;")
                elif msg.startswith("✗"):
                    msg_label.setStyleSheet("color: #E81123;")
                else:
                    msg_label.setStyleSheet("color: #FFB900;")
                validation_layout.addWidget(msg_label)

            validation_frame = QFrame()
            validation_frame.setLayout(validation_layout)
            validation_frame.setStyleSheet("QFrame { background-color: #f3f3f3; border: 1px solid #d0d0d0; border-radius: 4px; }")
            layout.addWidget(validation_frame)

        # Diff comparison
        diff_layout = QHBoxLayout()
        diff_layout.setSpacing(12)

        # Old text (left)
        left_layout = QVBoxLayout()
        old_label = QLabel("Original Text")
        old_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        left_layout.addWidget(old_label)

        old_text = QTextEdit()
        old_text.setPlainText(self.patch.old_text)
        old_text.setReadOnly(True)
        old_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        old_text.setFont(QFont("Consolas", 9))
        old_text.setStyleSheet("QTextEdit { background-color: #fff3f3; color: #666; border: 1px solid #e0e0e0; }")
        left_layout.addWidget(old_text)

        # New text (right)
        right_layout = QVBoxLayout()
        new_label = QLabel("Edited Text")
        new_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        right_layout.addWidget(new_label)

        new_text = QTextEdit()
        new_text.setPlainText(self.patch.new_text)
        new_text.setReadOnly(True)
        new_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        new_text.setFont(QFont("Consolas", 9))
        new_text.setStyleSheet("QTextEdit { background-color: #f3fff3; color: #333; border: 1px solid #e0e0e0; }")
        right_layout.addWidget(new_text)

        diff_layout.addLayout(left_layout)
        diff_layout.addLayout(right_layout)

        layout.addLayout(diff_layout, 1)  # Give it more space

        # Justification
        justif_layout = QVBoxLayout()
        justif_label = QLabel("Justification")
        justif_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        justif_layout.addWidget(justif_label)

        justif_text = QTextEdit()
        justif_text.setPlainText(self.patch.justification)
        justif_text.setReadOnly(True)
        justif_text.setMaximumHeight(60)
        justif_text.setFont(QFont("Segoe UI", 9))
        justif_layout.addWidget(justif_text)

        layout.addLayout(justif_layout)

        # Changes list
        if self.patch.changes:
            changes_layout = QVBoxLayout()
            changes_label = QLabel("Changes Made")
            changes_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            changes_layout.addWidget(changes_label)

            changes_text = QTextEdit()
            changes_text.setPlainText("\n".join(f"• {c}" for c in self.patch.changes))
            changes_text.setReadOnly(True)
            changes_text.setMaximumHeight(70)
            changes_text.setFont(QFont("Segoe UI", 9))
            changes_layout.addWidget(changes_text)

            layout.addLayout(changes_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reject_btn = QPushButton("Reject")
        reject_btn.setMinimumWidth(100)
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f3f3;
                color: #333;
                border: 1px solid #d0d0d0;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        reject_btn.clicked.connect(self._on_reject)
        button_layout.addWidget(reject_btn)

        approve_btn = QPushButton("Accept & Apply")
        approve_btn.setMinimumWidth(100)
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        approve_btn.clicked.connect(self._on_approve)
        button_layout.addWidget(approve_btn)

        layout.addLayout(button_layout)

    def _on_approve(self):
        """Handle approve button click."""
        logger.info(f"User approved patch for {self.patch.section}")
        self.approved.emit(self.patch)
        self.accept()

    def _on_reject(self):
        """Handle reject button click."""
        logger.info(f"User rejected patch for {self.patch.section}")
        self.rejected.emit()
        self.reject()


class EditProgressDialog(QDialog):
    """
    Progress dialog shown while LLM is generating edits.
    """

    def __init__(self, section: str, intent: str, parent=None):
        """
        Initialize progress dialog.

        Args:
            section: Report section being edited
            intent: User's intent/request
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("AI Edit in Progress")
        self.setGeometry(100, 100, 400, 150)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel(f"Editing {section}...")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # Intent
        intent_label = QLabel(f"Intent: {intent}")
        intent_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(intent_label)

        # Status
        status = QLabel("Generating improved text using AI assistant...")
        status.setFont(QFont("Segoe UI", 9))
        status.setStyleSheet("color: #666;")
        layout.addWidget(status)

        layout.addStretch()

        # Cancel button (optional)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMaximumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)


class EditConfirmDialog(QDialog):
    """
    Simple dialog to confirm if user wants to proceed with AI editing.
    """

    def __init__(self, section: str, selected_length: int, parent=None):
        """
        Initialize confirmation dialog.

        Args:
            section: Section being edited
            selected_length: Length of selected text
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Confirm AI Edit")
        self.setGeometry(100, 100, 400, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Message
        msg = QLabel(
            f"About to send {selected_length} characters from the {section} section "
            f"to the AI for editing.\n\n"
            "The edit will be shown for your approval before applying.\n\n"
            "Continue?"
        )
        msg.setFont(QFont("Segoe UI", 10))
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Continue")
        ok_btn.setMinimumWidth(80)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)


class UndoConfirmDialog(QDialog):
    """
    Dialog to confirm undo operation.
    """

    def __init__(self, description: str, parent=None):
        """
        Initialize undo confirmation dialog.

        Args:
            description: Description of what will be undone
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Confirm Undo")
        self.setGeometry(100, 100, 400, 150)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Message
        msg = QLabel(f"Undo the following change?\n\n{description}")
        msg.setFont(QFont("Segoe UI", 10))
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        undo_btn = QPushButton("Undo")
        undo_btn.setMinimumWidth(80)
        undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #d83b01;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a62e00;
            }
        """)
        undo_btn.clicked.connect(self.accept)
        btn_layout.addWidget(undo_btn)

        layout.addLayout(btn_layout)
