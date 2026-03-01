"""
Enhanced Rich-Text Report Editor

Professional QTextEdit-based editor with Word-like formatting capabilities:
- Text formatting (bold, italic, underline, strikethrough, colors)
- Paragraph formatting (alignment, lists, spacing, indentation)
- Advanced features (undo/redo, zoom, find/replace, insert table/image)
- Performance optimized for large documents (+10,000 words)
- Built-in keyboard shortcuts (Ctrl+B, Ctrl+I, etc.)
"""

from PySide6.QtWidgets import (
    QTextEdit, QFileDialog, QMessageBox, QTableWidgetSelectionRange,
    QTableWidget, QTableWidgetItem, QInputDialog
)
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QTextBlockFormat, QFont, QColor,
    QKeySequence, QTextTableFormat, QTextLength, QImage, QTextDocumentFragment,
    QTextListFormat
)
from PySide6.QtCore import Qt, Signal, QMimeData, QUrl
from typing import Optional
import os

from .formatting_actions import FormattingActions as FA
from .editor_toolbar import EditorToolbar


class ReportEditor(QTextEdit):
    """
    Professional rich-text editor for security reports.
    
    Features:
    - Full text and paragraph formatting
    - Undo/Redo with unlimited history
    - Zoom in/out
    - List support (bullet and numbered)
    - Table insertion
    - Image insertion
    - Performance optimized for large documents
    - Finalization mode (read-only with limited functionality)
    
    Maintains cursor position and focuses on smooth, lag-free typing.
    """
    
    # Signals
    content_changed = Signal()
    formatting_changed = Signal()
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setPlaceholderText("Report will appear here after analysis...")
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: none;
                padding: 20px;
                color: #333333;
                selection-background-color: #0084ff;
                selection-color: white;
            }
        """)
        
        # Editor state
        self.is_finalized = False
        self.zoom_level = 100  # Percentage
        self.current_font_family = "Segoe UI"
        self.current_font_size = 10
        
        # Create toolbar
        self.toolbar = EditorToolbar(parent)
        self._connect_toolbar_signals()
        
        # Connect editor signals
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_changed)
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Undo/Redo management
        self.setUndoRedoEnabled(True)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for common formatting."""
        # These are handled by QTextEdit built-in:
        # Ctrl+B (bold), Ctrl+I (italic), Ctrl+U (underline)
        # Ctrl+Z (undo), Ctrl+Y (redo)
        # Ctrl+A (select all), Ctrl+C (copy), Ctrl+V (paste), Ctrl+X (cut)
        pass
    
    def _connect_toolbar_signals(self):
        """Connect toolbar signals to editor slots."""
        # Font formatting
        self.toolbar.font_family_changed.connect(self._apply_font_family)
        self.toolbar.font_size_changed.connect(self._apply_font_size)
        self.toolbar.bold_toggled.connect(self._toggle_bold)
        self.toolbar.italic_toggled.connect(self._toggle_italic)
        self.toolbar.underline_toggled.connect(self._toggle_underline)
        self.toolbar.strikethrough_toggled.connect(self._toggle_strikethrough)
        self.toolbar.superscript_toggled.connect(self._toggle_superscript)
        self.toolbar.subscript_toggled.connect(self._toggle_subscript)
        
        # Colors
        self.toolbar.text_color_selected.connect(self._apply_text_color)
        self.toolbar.highlight_color_selected.connect(self._apply_highlight_color)
        
        # Paragraph formatting
        self.toolbar.alignment_changed.connect(self._apply_alignment)
        self.toolbar.bullet_list_triggered.connect(self._toggle_bullet_list)
        self.toolbar.numbered_list_triggered.connect(self._toggle_numbered_list)
        self.toolbar.indent_increased.connect(self._increase_indent)
        self.toolbar.indent_decreased.connect(self._decrease_indent)
        self.toolbar.line_spacing_changed.connect(self._apply_line_spacing)
        
        # Editing
        self.toolbar.undo_triggered.connect(self.undo)
        self.toolbar.redo_triggered.connect(self.redo)
        self.toolbar.clear_formatting_triggered.connect(self._clear_all_formatting)
        self.toolbar.select_all_triggered.connect(self.selectAll)
        
        # Advanced
        self.toolbar.insert_table_triggered.connect(self._insert_table)
        self.toolbar.insert_line_triggered.connect(self._insert_horizontal_line)
        self.toolbar.insert_image_triggered.connect(self._insert_image)
        
        # Zoom
        self.toolbar.zoom_in_triggered.connect(self._zoom_in)
        self.toolbar.zoom_out_triggered.connect(self._zoom_out)
    
    # ========== TEXT FORMATTING ==========
    
    def _toggle_bold(self, enabled: bool):
        """Toggle bold formatting on selected text or cursor word."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.set_bold(cursor, enabled)
            self.setTextCursor(cursor)
        else:
            # Apply to future typing
            FA.set_bold(cursor, enabled)
            self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_italic(self, enabled: bool):
        """Toggle italic formatting."""
        cursor = self.textCursor()
        FA.set_italic(cursor, enabled)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_underline(self, enabled: bool):
        """Toggle underline formatting."""
        cursor = self.textCursor()
        FA.set_underline(cursor, enabled)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_strikethrough(self, enabled: bool):
        """Toggle strikethrough formatting."""
        cursor = self.textCursor()
        FA.set_strikethrough(cursor, enabled)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_superscript(self, enabled: bool):
        """Toggle superscript formatting."""
        cursor = self.textCursor()
        FA.set_superscript(cursor, enabled)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_subscript(self, enabled: bool):
        """Toggle subscript formatting."""
        cursor = self.textCursor()
        FA.set_subscript(cursor, enabled)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _apply_font_family(self, family: str):
        """Apply font family to selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.set_font_family(cursor, family)
            self.setTextCursor(cursor)
        self.current_font_family = family
        self.setFocus()
    
    def _apply_font_size(self, size: int):
        """Apply font size to selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.set_font_size(cursor, size)
            self.setTextCursor(cursor)
        self.current_font_size = size
        self.setFocus()
    
    def _apply_text_color(self, color: QColor):
        """Apply text color to selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.set_text_color(cursor, color)
            self.setTextCursor(cursor)
        self.setFocus()
    
    def _apply_highlight_color(self, color: QColor):
        """Apply highlight/background color to selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.set_highlight_color(cursor, color)
            self.setTextCursor(cursor)
        self.setFocus()
    
    def _clear_all_formatting(self):
        """Clear all formatting from selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            FA.clear_formatting(cursor)
            self.setTextCursor(cursor)
            self.status_message.emit("Formatting cleared")
        self.setFocus()
    
    # ========== PARAGRAPH FORMATTING ==========
    
    def _apply_alignment(self, alignment):
        """Apply paragraph alignment."""
        cursor = self.textCursor()
        FA.set_alignment(cursor, alignment)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _toggle_bullet_list(self):
        """Toggle bullet list on current paragraph."""
        cursor = self.textCursor()
        
        # Use QTextListFormat for proper list support
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDisc)
        
        cursor.insertList(list_fmt)
        self.setTextCursor(cursor)
        self.status_message.emit("Bullet list applied")
        self.setFocus()
    
    def _toggle_numbered_list(self):
        """Toggle numbered list on current paragraph."""
        cursor = self.textCursor()
        
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
        
        cursor.insertList(list_fmt)
        self.setTextCursor(cursor)
        self.status_message.emit("Numbered list applied")
        self.setFocus()
    
    def _increase_indent(self):
        """Increase paragraph indentation."""
        cursor = self.textCursor()
        fmt = cursor.blockFormat()
        fmt.setLeftMargin(fmt.leftMargin() + 20)  # +20mm
        cursor.mergeBlockFormat(fmt)
        self.setTextCursor(cursor)
        self.setFocus()
    
    def _decrease_indent(self):
        """Decrease paragraph indentation."""
        cursor = self.textCursor()
        fmt = cursor.blockFormat()
        current_margin = fmt.leftMargin()
        if current_margin > 0:
            fmt.setLeftMargin(max(0, current_margin - 20))  # -20mm
            cursor.mergeBlockFormat(fmt)
            self.setTextCursor(cursor)
        self.setFocus()
    
    def _apply_line_spacing(self, spacing: float):
        """Apply line spacing to current paragraph."""
        cursor = self.textCursor()
        FA.set_line_spacing(cursor, spacing)
        self.setTextCursor(cursor)
        self.setFocus()
    
    # ========== ADVANCED FEATURES ==========
    
    def _insert_table(self, rows: int = 3, cols: int = 3):
        """Insert a table at cursor position."""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Insert Table")
        dialog.setLabelText("Rows:")
        dialog.setIntValue(rows)
        dialog.setIntMinimum(1)
        dialog.setIntMaximum(20)
        
        if not dialog.exec():
            return
        
        rows = dialog.intValue()
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Insert Table")
        dialog.setLabelText("Columns:")
        dialog.setIntValue(cols)
        dialog.setIntMinimum(1)
        dialog.setIntMaximum(10)
        
        if not dialog.exec():
            return
        
        cols = dialog.intValue()
        
        cursor = self.textCursor()
        
        # Create table format
        table_fmt = QTextTableFormat()
        table_fmt.setBorder(1)
        table_fmt.setCellPadding(5)
        table_fmt.setCellSpacing(0)
        
        # Insert table
        cursor.insertTable(rows, cols, table_fmt)
        self.status_message.emit(f"Table ({rows}x{cols}) inserted")
        self.setFocus()
    
    def _insert_horizontal_line(self):
        """Insert a horizontal line (paragraph separator)."""
        cursor = self.textCursor()
        cursor.insertText("―" * 60 + "\n")
        self.status_message.emit("Horizontal line inserted")
        self.setFocus()
    
    def _insert_image(self):
        """Insert an image at cursor position."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if not file_path:
            return
        
        cursor = self.textCursor()
        doc = self.document()
        
        image = QImage(file_path)
        if image.isNull():
            self.status_message.emit("Failed to load image")
            return
        
        # Scale image to reasonable size
        if image.width() > 600:
            image = image.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)
        
        # Insert image
        cursor.insertImage(image, os.path.basename(file_path))
        self.status_message.emit(f"Image \"{os.path.basename(file_path)}\" inserted")
        self.setFocus()
    
    # ========== ZOOM ==========
    
    def _zoom_in(self):
        """Increase zoom level by 10%."""
        self.zoom_level = min(200, self.zoom_level + 10)
        self._apply_zoom()
        self.status_message.emit(f"Zoom: {self.zoom_level}%")
    
    def _zoom_out(self):
        """Decrease zoom level by 10%."""
        self.zoom_level = max(50, self.zoom_level - 10)
        self._apply_zoom()
        self.status_message.emit(f"Zoom: {self.zoom_level}%")
    
    def _apply_zoom(self):
        """Apply zoom level to editor."""
        scale = self.zoom_level / 100.0
        font = self.font()
        base_size = 10
        font.setPointSize(int(base_size * scale))
        self.setFont(font)
    
    # ========== STATE MANAGEMENT ==========
    
    def _on_text_changed(self):
        """Handle document text changes."""
        self.content_changed.emit()
    
    def _on_cursor_changed(self):
        """Update toolbar state when cursor moves."""
        cursor = self.textCursor()
        char_fmt = cursor.charFormat()
        block_fmt = cursor.blockFormat()
        
        self.toolbar.update_formatting_state(char_fmt, block_fmt)
        self.formatting_changed.emit()
    
    def set_finalized(self, finalized: bool):
        """
        Lock/unlock editing based on finalization status.
        
        When finalized:
        - Editor becomes read-only
        - Only view/copy actions are available
        - Cannot modify content
        """
        self.is_finalized = finalized
        self.setReadOnly(finalized)
        
        # Update UI styling
        if finalized:
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    border: none;
                    padding: 20px;
                    color: #666666;
                }
            """)
            # Disable editing toolbar
            self.toolbar.setEnabled(False)
            # Re-enable view-only actions
            self.toolbar.zoom_in_action.setEnabled(True)
            self.toolbar.zoom_out_action.setEnabled(True)
            self.toolbar.select_all_action.setEnabled(True)
        else:
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #fafafa;
                    border: none;
                    padding: 20px;
                    color: #333333;
                }
            """)
            # Enable editing toolbar
            self.toolbar.setEnabled(True)
    
    # ========== EXPORT COMPATIBILITY ==========
    
    def get_html(self) -> str:
        """Get editor content as HTML."""
        return self.toHtml()
    
    def get_plain_text(self) -> str:
        """Get editor content as plain text."""
        return self.toPlainText()
    
    def get_markdown(self) -> str:
        """Get editor content as markdown (basic conversion)."""
        # For now, return plain text
        # Could enhance with proper HTML to Markdown conversion
        return self.toPlainText()
    
    def set_html_content(self, html: str):
        """Set editor content from HTML."""
        self.setHtml(html)
    
    def set_plain_text_content(self, text: str):
        """Set editor content from plain text."""
        self.setPlainText(text)
    
    # ========== UTILITY METHODS ==========
    
    def get_toolbar(self) -> EditorToolbar:
        """Get the toolbar widget for integration into main window."""
        return self.toolbar
    
    def get_word_count(self) -> int:
        """Get word count in document."""
        text = self.toPlainText()
        return len(text.split())
    
    def get_char_count(self) -> int:
        """Get character count in document."""
        return len(self.toPlainText())
    
    def copy_selected(self):
        """Copy selected text."""
        self.copy()
    
    def paste(self):
        """Paste from clipboard."""
        self.paste()
    
    def find_and_replace(self, find_text: str, replace_text: str, replace_all: bool = False) -> int:
        """
        Find and replace text in document.
        
        Args:
            find_text: Text to find
            replace_text: Text to replace with
            replace_all: If True, replace all occurrences
        
        Returns:
            Number of replacements made
        """
        from PySide6.QtGui import QTextDocument
        
        doc = self.document()
        cursor = QTextCursor(doc)
        count = 0
        
        while True:
            cursor = doc.find(find_text, cursor)
            if cursor.isNull():
                break
            
            cursor.insertText(replace_text)
            count += 1
            
            if not replace_all:
                self.setTextCursor(cursor)
                break
        
        return count