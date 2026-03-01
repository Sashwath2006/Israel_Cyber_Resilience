"""
Professional Rich-Text Editor Toolbar

Provides a Word-like toolbar with sections for:
- Font formatting (family, size, bold, italic, etc.)
- Paragraph formatting (alignment, lists, spacing)
- Editing tools (undo, redo, clear formatting)
- Insert tools (table, line, image)
"""

from PySide6.QtWidgets import (
    QToolBar, QComboBox, QSpinBox, QPushButton, QColorDialog,
    QVBoxLayout, QHBoxLayout, QWidget
)
from PySide6.QtGui import QIcon, QColor, QAction, QFont, QPixmap
from PySide6.QtCore import Qt, Signal, QSize
from typing import Optional, Callable


class EditorToolbar(QToolBar):
    """
    Professional rich-text editor toolbar.
    
    Organized in sections:
    1. Font formatting (family, size, bold, italic, underline, color)
    2. Paragraph formatting (alignment, lists, indentation)
    3. Editing tools (undo, redo, clear formatting)
    4. Insert tools (table, line, image)
    """
    
    # Signals for formatting actions
    bold_toggled = Signal(bool)
    italic_toggled = Signal(bool)
    underline_toggled = Signal(bool)
    strikethrough_toggled = Signal(bool)
    superscript_toggled = Signal(bool)
    subscript_toggled = Signal(bool)
    
    font_family_changed = Signal(str)
    font_size_changed = Signal(int)
    text_color_selected = Signal(QColor)
    highlight_color_selected = Signal(QColor)
    
    alignment_changed = Signal(Qt.Alignment)
    bullet_list_triggered = Signal()
    numbered_list_triggered = Signal()
    indent_increased = Signal()
    indent_decreased = Signal()
    line_spacing_changed = Signal(float)
    
    undo_triggered = Signal()
    redo_triggered = Signal()
    clear_formatting_triggered = Signal()
    select_all_triggered = Signal()
    
    insert_table_triggered = Signal()
    insert_line_triggered = Signal()
    insert_image_triggered = Signal()
    
    zoom_in_triggered = Signal()
    zoom_out_triggered = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Editor Toolbar", parent)
        self.setMovable(False)
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 6px;
                spacing: 2px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
            QToolButton:checked {
                background-color: #0084ff;
                color: white;
                border: 1px solid #0073e6;
            }
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 3px 6px;
                background-color: white;
                min-width: 80px;
            }
            QSpinBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 3px 6px;
                background-color: white;
                min-width: 60px;
            }
        """)
        
        self._setup_toolbar()
    
    def _setup_toolbar(self):
        """Setup toolbar sections."""
        # SECTION 1: Editing (Undo/Redo)
        self._add_editing_section()
        self.addSeparator()
        
        # SECTION 2: Font Formatting
        self._add_font_section()
        self.addSeparator()
        
        # SECTION 3: Text Color & Highlight
        self._add_color_section()
        self.addSeparator()
        
        # SECTION 4: Paragraph Formatting
        self._add_paragraph_section()
        self.addSeparator()
        
        # SECTION 5: Lists & Indentation
        self._add_list_section()
        self.addSeparator()
        
        # SECTION 6: Advanced
        self._add_advanced_section()
        self.addSeparator()
        
        # SECTION 7: View/Zoom
        self._add_view_section()
    
    def _add_editing_section(self):
        """Add undo/redo/select all/clear formatting section."""
        self.undo_action = self.addAction("↶ Undo")
        self.undo_action.setToolTip("Undo (Ctrl+Z)")
        self.undo_action.triggered.connect(self.undo_triggered.emit)
        
        self.redo_action = self.addAction("↷ Redo")
        self.redo_action.setToolTip("Redo (Ctrl+Y)")
        self.redo_action.triggered.connect(self.redo_triggered.emit)
        
        self.addSeparator()
        
        self.clear_fmt_action = self.addAction("⌫ Clear")
        self.clear_fmt_action.setToolTip("Clear formatting")
        self.clear_fmt_action.triggered.connect(self.clear_formatting_triggered.emit)
        
        self.select_all_action = self.addAction("☐ Select All")
        self.select_all_action.setToolTip("Select All (Ctrl+A)")
        self.select_all_action.triggered.connect(self.select_all_triggered.emit)
    
    def _add_font_section(self):
        """Add font family, size, and text styles (bold, italic, underline)."""
        # Font family dropdown
        self.font_family = QComboBox()
        self.font_family.addItems([
            "Segoe UI", "Consolas", "Arial", "Times New Roman",
            "Courier New", "Georgia", "Verdana", "Trebuchet MS"
        ])
        self.font_family.setCurrentText("Segoe UI")
        self.font_family.currentTextChanged.connect(
            lambda text: self.font_family_changed.emit(text)
        )
        self.addWidget(self.font_family)
        
        # Font size spinbox
        self.font_size = QSpinBox()
        self.font_size.setMinimum(8)
        self.font_size.setMaximum(72)
        self.font_size.setValue(10)
        self.font_size.setSuffix(" pt")
        self.font_size.valueChanged.connect(
            lambda value: self.font_size_changed.emit(value)
        )
        self.addWidget(self.font_size)
        
        # Bold button
        self.bold_action = self.addAction("B")
        self.bold_action.setToolTip("Bold (Ctrl+B)")
        self.bold_action.setCheckable(True)
        font = QFont()
        font.setBold(True)
        self.bold_action.setFont(font)
        self.bold_action.triggered.connect(lambda checked: self.bold_toggled.emit(checked))
        
        # Italic button
        self.italic_action = self.addAction("I")
        self.italic_action.setToolTip("Italic (Ctrl+I)")
        self.italic_action.setCheckable(True)
        font = QFont()
        font.setItalic(True)
        self.italic_action.setFont(font)
        self.italic_action.triggered.connect(lambda checked: self.italic_toggled.emit(checked))
        
        # Underline button
        self.underline_action = self.addAction("U")
        self.underline_action.setToolTip("Underline (Ctrl+U)")
        self.underline_action.setCheckable(True)
        font = QFont()
        font.setUnderline(True)
        self.underline_action.setFont(font)
        self.underline_action.triggered.connect(lambda checked: self.underline_toggled.emit(checked))
        
        # Strikethrough button
        self.strikethrough_action = self.addAction("S̶")
        self.strikethrough_action.setToolTip("Strikethrough")
        self.strikethrough_action.setCheckable(True)
        self.strikethrough_action.triggered.connect(
            lambda checked: self.strikethrough_toggled.emit(checked)
        )
        
        # Superscript button
        self.superscript_action = self.addAction("X²")
        self.superscript_action.setToolTip("Superscript")
        self.superscript_action.setCheckable(True)
        self.superscript_action.triggered.connect(
            lambda checked: self.superscript_toggled.emit(checked)
        )
        
        # Subscript button
        self.subscript_action = self.addAction("X₂")
        self.subscript_action.setToolTip("Subscript")
        self.subscript_action.setCheckable(True)
        self.subscript_action.triggered.connect(
            lambda checked: self.subscript_toggled.emit(checked)
        )
    
    def _add_color_section(self):
        """Add text color and highlight color pickers."""
        # Text color button
        self.text_color_action = self.addAction("A")
        self.text_color_action.setToolTip("Text Color")
        self.text_color_action.triggered.connect(self._pick_text_color)
        self.text_color_pixmap = QPixmap(20, 20)
        self.text_color_pixmap.fill(QColor(0, 0, 0))
        self.text_color_action.setIcon(QIcon(self.text_color_pixmap))
        
        # Highlight color button
        self.highlight_color_action = self.addAction("⊟")
        self.highlight_color_action.setToolTip("Highlight Color")
        self.highlight_color_action.triggered.connect(self._pick_highlight_color)
        self.highlight_color_pixmap = QPixmap(20, 20)
        self.highlight_color_pixmap.fill(QColor(255, 255, 0))
        self.highlight_color_action.setIcon(QIcon(self.highlight_color_pixmap))
    
    def _add_paragraph_section(self):
        """Add paragraph alignment buttons."""
        self.align_left_action = self.addAction("≣⬅")
        self.align_left_action.setToolTip("Align Left")
        self.align_left_action.setCheckable(True)
        self.align_left_action.triggered.connect(
            lambda: self._handle_alignment_change(self.align_left_action, Qt.AlignmentFlag.AlignLeft)
        )
        
        self.align_center_action = self.addAction("≣↔")
        self.align_center_action.setToolTip("Align Center")
        self.align_center_action.setCheckable(True)
        self.align_center_action.triggered.connect(
            lambda: self._handle_alignment_change(self.align_center_action, Qt.AlignmentFlag.AlignCenter)
        )
        
        self.align_right_action = self.addAction("≣⬈")
        self.align_right_action.setToolTip("Align Right")
        self.align_right_action.setCheckable(True)
        self.align_right_action.triggered.connect(
            lambda: self._handle_alignment_change(self.align_right_action, Qt.AlignmentFlag.AlignRight)
        )
        
        self.align_justify_action = self.addAction("≡")
        self.align_justify_action.setToolTip("Justify")
        self.align_justify_action.setCheckable(True)
        self.align_justify_action.triggered.connect(
            lambda: self._handle_alignment_change(self.align_justify_action, Qt.AlignmentFlag.AlignJustify)
        )
        
        # Connect alignment buttons to handle exclusivity
        self.align_left_action.triggered.connect(
            lambda: self._handle_alignment_change(self.align_left_action, Qt.AlignmentFlag.AlignLeft)
        )
    
    def _add_list_section(self):
        """Add bullet list, numbered list, and indentation buttons."""
        # Bullet list button
        self.bullet_list_action = self.addAction("• List")
        self.bullet_list_action.setToolTip("Bullet List")
        self.bullet_list_action.setCheckable(True)
        self.bullet_list_action.triggered.connect(self.bullet_list_triggered.emit)
        
        # Numbered list button
        self.numbered_list_action = self.addAction("1. List")
        self.numbered_list_action.setToolTip("Numbered List")
        self.numbered_list_action.setCheckable(True)
        self.numbered_list_action.triggered.connect(self.numbered_list_triggered.emit)
        
        # Increase indent button
        self.indent_increase_action = self.addAction("➘")
        self.indent_increase_action.setToolTip("Increase Indent")
        self.indent_increase_action.triggered.connect(self.indent_increased.emit)
        
        # Decrease indent button
        self.indent_decrease_action = self.addAction("➙")
        self.indent_decrease_action.setToolTip("Decrease Indent")
        self.indent_decrease_action.triggered.connect(self.indent_decreased.emit)
        
        # Line spacing dropdown
        self.line_spacing = QComboBox()
        self.line_spacing.addItems(["1.0", "1.15", "1.5", "2.0"])
        self.line_spacing.currentTextChanged.connect(
            lambda text: self.line_spacing_changed.emit(float(text))
        )
        self.addWidget(self.line_spacing)
    
    def _add_advanced_section(self):
        """Add insert table, line, and image buttons."""
        self.insert_table_action = self.addAction("📊 Table")
        self.insert_table_action.setToolTip("Insert Table")
        self.insert_table_action.triggered.connect(self.insert_table_triggered.emit)
        
        self.insert_line_action = self.addAction("―――")
        self.insert_line_action.setToolTip("Insert Horizontal Line")
        self.insert_line_action.triggered.connect(self.insert_line_triggered.emit)
        
        self.insert_image_action = self.addAction("📷 Image")
        self.insert_image_action.setToolTip("Insert Image")
        self.insert_image_action.triggered.connect(self.insert_image_triggered.emit)
    
    def _add_view_section(self):
        """Add zoom in/out buttons."""
        self.zoom_in_action = self.addAction("🔍+")
        self.zoom_in_action.setToolTip("Zoom In")
        self.zoom_in_action.triggered.connect(self.zoom_in_triggered.emit)
        
        self.zoom_out_action = self.addAction("🔍−")
        self.zoom_out_action.setToolTip("Zoom Out")
        self.zoom_out_action.triggered.connect(self.zoom_out_triggered.emit)
    
    def _pick_text_color(self):
        """Open color picker for text color."""
        color = QColorDialog.getColor(
            QColor(0, 0, 0), self, "Choose Text Color"
        )
        if color.isValid():
            self.text_color_pixmap.fill(color)
            self.text_color_action.setIcon(QIcon(self.text_color_pixmap))
            self.text_color_selected.emit(color)
    
    def _pick_highlight_color(self):
        """Open color picker for highlight color."""
        color = QColorDialog.getColor(
            QColor(255, 255, 0), self, "Choose Highlight Color"
        )
        if color.isValid():
            self.highlight_color_pixmap.fill(color)
            self.highlight_color_action.setIcon(QIcon(self.highlight_color_pixmap))
            self.highlight_color_selected.emit(color)
    
    def _handle_alignment_change(self, clicked_action, alignment):
        """Handle alignment button clicks with mutual exclusivity."""
        # Uncheck all alignment buttons except the clicked one
        for action in [self.align_left_action, self.align_center_action, 
                       self.align_right_action, self.align_justify_action]:
            action.blockSignals(True)
            action.setChecked(action == clicked_action)
            action.blockSignals(False)
        
        # Emit the alignment changed signal
        self.alignment_changed.emit(alignment)
    
    def update_formatting_state(self, char_fmt, block_fmt):
        """
        Update toolbar buttons to reflect current formatting state.
        
        Args:
            char_fmt: QTextCharFormat at cursor position
            block_fmt: QTextBlockFormat at cursor position
        """
        from .formatting_actions import FormattingActions as FA
        
        # Update text style buttons
        self.bold_action.setChecked(FA.is_bold(char_fmt))
        self.italic_action.setChecked(FA.is_italic(char_fmt))
        self.underline_action.setChecked(FA.is_underline(char_fmt))
        self.strikethrough_action.setChecked(FA.is_strikethrough(char_fmt))
        
        # Update font info
        font = char_fmt.font()
        families = char_fmt.fontFamilies()
        if families:
            self.font_family.setCurrentText(families[0])
        if char_fmt.fontPointSize() > 0:
            self.font_size.setValue(int(char_fmt.fontPointSize()))
        
        # Update alignment
        alignment = FA.get_alignment(block_fmt)
        if alignment == Qt.AlignmentFlag.AlignCenter:
            self.align_center_action.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight:
            self.align_right_action.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify:
            self.align_justify_action.setChecked(True)
        else:
            self.align_left_action.setChecked(True)
    
    def set_undo_enabled(self, enabled: bool):
        """Enable/disable undo button."""
        self.undo_action.setEnabled(enabled)
    
    def set_redo_enabled(self, enabled: bool):
        """Enable/disable redo button."""
        self.redo_action.setEnabled(enabled)
