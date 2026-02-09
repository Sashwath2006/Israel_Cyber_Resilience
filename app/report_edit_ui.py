"""
UI Integration Module for Report Editing (Phase 14 - Part 4)

Bridges the report editing engine with the main window UI.
Handles:
- Edit command detection
- LLM inference with progress tracking
- Patch preview and approval workflow
- Undo integration
"""

from PySide6.QtCore import QThread, Signal
from typing import Optional

from app.report_edit_engine import (
    ReportEditEngine,
    EditIntent,
    EditPatch,
)
from app.report_version_manager import ReportVersionManager, ChangeType
from app.report_edit_dialogs import (
    DiffPreviewDialog,
    EditProgressDialog,
    EditConfirmDialog,
    UndoConfirmDialog,
)
from app.logging_config import get_logger

logger = get_logger("EditUIIntegration")


class EditWorker(QThread):
    """Background worker for LLM-powered report editing."""

    patch_generated = Signal(object)  # EditPatch
    error_occurred = Signal(str)
    progress_update = Signal(str)

    def __init__(
        self,
        edit_engine: ReportEditEngine,
        section: str,
        text_to_edit: str,
        intent: EditIntent,
    ):
        super().__init__()
        self.edit_engine = edit_engine
        self.section = section
        self.text_to_edit = text_to_edit
        self.intent = intent

    def run(self):
        """Run LLM edit generation."""
        try:
            self.progress_update.emit("Building context...")

            # Build context
            context = self.edit_engine.build_context(
                section_name=self.section,
                text_to_edit=self.text_to_edit,
                intent=self.intent,
            )

            self.progress_update.emit("Calling AI assistant...")

            # Generate patch
            success, patch, error = self.edit_engine.generate_patch(
                section=self.section,
                text_to_edit=self.text_to_edit,
                intent=self.intent,
                context=context,
            )

            if not success:
                self.error_occurred.emit(f"AI generation failed: {error}")
                return

            if patch is None:
                self.error_occurred.emit("Generated patch is None")
                return

            self.progress_update.emit("Validating patch...")

            # Validate patch
            valid, validation_messages = self.edit_engine.validate_patch(patch)
            patch.metadata = {"validation_passed": valid, "validation_messages": validation_messages}

            logger.info(f"Patch validation: {valid}")
            self.patch_generated.emit(patch)

        except Exception as e:
            logger.error(f"Edit worker error: {str(e)}")
            self.error_occurred.emit(f"Unexpected error: {str(e)}")


class EditUIHandler:
    """
    Handles UI integration for report editing.

    Responsibilities:
    - Detect edit commands from user input
    - Manage edit workflow (intent -> LLM -> preview -> apply)
    - Handle undo/versioning
    - Coordinate with main window UI
    """

    def __init__(
        self,
        edit_engine: ReportEditEngine,
        version_manager: ReportVersionManager,
        main_window,
    ):
        """
        Initialize edit UI handler.

        Args:
            edit_engine: ReportEditEngine instance
            version_manager: ReportVersionManager instance
            main_window: Reference to main window for UI updates
        """
        self.edit_engine = edit_engine
        self.version_manager = version_manager
        self.main_window = main_window
        self.current_patch: Optional[EditPatch] = None
        self.edit_worker: Optional[EditWorker] = None
        self.progress_dialog: Optional[EditProgressDialog] = None

    @staticmethod
    def is_edit_command(user_message: str) -> bool:
        """
        Detect if user message is an edit command.

        Args:
            user_message: User's chat message

        Returns:
            True if message appears to be an edit request
        """
        keywords = [
            "rewrite",
            "improve",
            "clarify",
            "simplify",
            "formal",
            "professional",
            "technical",
            "shorten",
            "compress",
            "expand",
            "more detail",
            "elaborate",
            "grammar",
            "spelling",
            "proofread",
            "summarize",
            "summary",
            "one line",
            "single line",
        ]
        msg_lower = user_message.lower()
        return any(keyword in msg_lower for keyword in keywords)

    def handle_edit_request(self, user_message: str, selected_text: str, section_name: str = "SELECTION"):
        """
        Handle an edit request from the user.

        Args:
            user_message: User's request message
            selected_text: Selected text from report
            section_name: Name of report section being edited
        """
        if not selected_text:
            self.main_window.chat_pane.add_message(
                "📝 No text selected.\n\n"
                "Please select text in the report editor before requesting an edit.",
                is_user=False,
            )
            return

        # Show confirmation dialog
        confirm_dialog = EditConfirmDialog(
            section=section_name,
            selected_length=len(selected_text),
            parent=self.main_window,
        )

        if confirm_dialog.exec() != EditConfirmDialog.DialogCode.Accepted:
            logger.info("User cancelled edit request")
            return

        # Parse intent
        intent = self.edit_engine.analyze_intent(user_message, selected_text)

        # Show progress dialog
        self.progress_dialog = EditProgressDialog(
            section=section_name,
            intent=intent.intent_type.value,
            parent=self.main_window,
        )

        # Start edit worker
        self.edit_worker = EditWorker(
            edit_engine=self.edit_engine,
            section=section_name,
            text_to_edit=selected_text,
            intent=intent,
        )

        self.edit_worker.patch_generated.connect(self._on_patch_generated)
        self.edit_worker.error_occurred.connect(self._on_edit_error)
        self.edit_worker.progress_update.connect(self._on_progress_update)

        self.edit_worker.start()

        # Show progress dialog (non-blocking)
        self.progress_dialog.exec()

    def _on_progress_update(self, message: str):
        """Handle progress update from edit worker."""
        if self.progress_dialog:
            self.progress_dialog.setWindowTitle(f"AI Edit in Progress - {message}")

    def _on_patch_generated(self, patch: EditPatch):
        """Handle patch generation completion."""
        try:
            # Close progress dialog
            if self.progress_dialog:
                self.progress_dialog.accept()
                self.progress_dialog = None

            # Store current patch
            self.current_patch = patch

            # Get validation messages
            validation_messages = patch.metadata.get("validation_messages", [])

            # Show diff preview
            diff_dialog = DiffPreviewDialog(
                patch=patch,
                validation_messages=validation_messages,
                parent=self.main_window,
            )

            diff_dialog.approved.connect(self._on_patch_approved)
            diff_dialog.rejected.connect(self._on_patch_rejected)

            diff_dialog.exec()

        except Exception as e:
            logger.error(f"Error in patch generation handler: {str(e)}")
            self.main_window.chat_pane.add_message(
                f"[ERROR] Failed to process patch: {str(e)}", is_user=False
            )

    def _on_edit_error(self, error_msg: str):
        """Handle edit error."""
        logger.error(f"Edit error: {error_msg}")

        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.reject()
            self.progress_dialog = None

        # Show error to user
        self.main_window.chat_pane.add_message(
            f"[ERROR] Edit failed: {error_msg}", is_user=False
        )

    def _on_patch_approved(self, patch: EditPatch):
        """Handle user approving a patch."""
        try:
            logger.info(f"User approved patch for {patch.section}")

            # Save snapshot before applying
            current_report_text = self.main_window.report_editor.toPlainText()

            self.version_manager.save_snapshot(
                report_content={"text": current_report_text},
                change_type=ChangeType.MANUAL_EDIT,
                description=f"Before AI edit to {patch.section}",
                section=patch.section,
                old_content=patch.old_text,
                new_content=patch.new_text,
            )

            # Apply patch
            new_text = self.edit_engine.apply_patch(current_report_text, patch)

            # Check if patch was actually applied
            if new_text == current_report_text:
                # Patch application failed
                self.main_window.chat_pane.add_message(
                    "⚠️ **Patch Application Failed**\n\n"
                    "The edited text could not be found in the report. This usually happens when:\n"
                    "• The report was modified after you selected the text\n"
                    "• The text formatting changed (spacing, line breaks)\n"
                    "• You edited the same section multiple times\n\n"
                    "**Solution**: Try selecting the updated text and requesting the edit again.",
                    is_user=False,
                )
                logger.error(f"Patch application failed for {patch.section}")
                return

            # Update editor with new text
            self.main_window.report_editor.setPlainText(new_text)

            # Save snapshot after applying
            self.version_manager.save_snapshot(
                report_content={"text": new_text},
                change_type=ChangeType.AI_EDIT,
                description=f"AI edit applied: {patch.intent.intent_type.value}",
                section=patch.section,
                old_content=patch.old_text,
                new_content=patch.new_text,
                metadata={"justification": patch.justification},
            )

            # Notify user of success
            self.main_window.chat_pane.add_message(
                f"✓ **Edit applied to {patch.section}**\n\n"
                f"**Justification**: {patch.justification}\n\n"
                f"You can type **'undo'** to revert this change if needed.",
                is_user=False,
            )

            self.current_patch = None

        except Exception as e:
            logger.error(f"Error applying patch: {str(e)}")
            self.main_window.chat_pane.add_message(
                f"[ERROR] Failed to apply patch: {str(e)}", is_user=False
            )

    def _on_patch_rejected(self):
        """Handle user rejecting a patch."""
        logger.info("User rejected patch")
        self.main_window.chat_pane.add_message(
            "Edit cancelled. Report remains unchanged.", is_user=False
        )
        self.current_patch = None

    def handle_undo(self):
        """Handle undo request."""
        if not self.version_manager.versions:
            self.main_window.chat_pane.add_message("Nothing to undo.", is_user=False)
            return

        # Get last version
        last_version = self.version_manager.get_current_version()
        if not last_version or len(self.version_manager.versions) < 2:
            self.main_window.chat_pane.add_message("Nothing to undo.", is_user=False)
            return

        # Show confirmation
        undo_dialog = UndoConfirmDialog(
            description=last_version.snapshot.description,
            parent=self.main_window,
        )

        if undo_dialog.exec() != UndoConfirmDialog.DialogCode.Accepted:
            return

        # Perform undo
        success, msg, prev_version = self.version_manager.undo_last()

        if success and prev_version:
            # Restore text from previous version
            prev_text = prev_version.report_content.get("text", "")
            self.main_window.report_editor.setPlainText(prev_text)

            self.main_window.chat_pane.add_message(
                f"✓ Undone: {msg}\n\nReport restored to previous state.", is_user=False
            )
        else:
            self.main_window.chat_pane.add_message(f"[ERROR] Undo failed: {msg}", is_user=False)

    def show_version_history(self):
        """Show version history to user."""
        history = self.version_manager.get_version_history()

        if not history:
            self.main_window.chat_pane.add_message("No edit history.", is_user=False)
            return

        msg_lines = ["📋 Edit History:\n"]
        for i, v in enumerate(history, 1):
            mark = "→ " if v["is_current"] else "  "
            msg_lines.append(
                f"{mark}[{v['version_id']}] {v['change_type'].upper()} - {v['description']}"
            )

        self.main_window.chat_pane.add_message("\n".join(msg_lines), is_user=False)
