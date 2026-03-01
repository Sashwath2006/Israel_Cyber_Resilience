"""
Text Formatting Actions and Utilities

Provides utility functions for applying text and paragraph formatting
to QTextCursor and QTextDocument objects.
"""

from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QTextBlockFormat, QFont, QColor
)
from PySide6.QtCore import Qt


class FormattingActions:
    """Utility class for text formatting operations."""
    
    @staticmethod
    def get_char_format(cursor: QTextCursor) -> QTextCharFormat:
        """Get current character formatting at cursor position."""
        return cursor.charFormat()
    
    @staticmethod
    def get_block_format(cursor: QTextCursor) -> QTextBlockFormat:
        """Get current block formatting at cursor position."""
        return cursor.blockFormat()
    
    @staticmethod
    def set_bold(cursor: QTextCursor, enabled: bool):
        """Toggle bold formatting."""
        fmt = cursor.charFormat()
        fmt.setFontWeight(QFont.Weight.Bold if enabled else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_italic(cursor: QTextCursor, enabled: bool):
        """Toggle italic formatting."""
        fmt = cursor.charFormat()
        fmt.setFontItalic(enabled)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_underline(cursor: QTextCursor, enabled: bool):
        """Toggle underline formatting."""
        fmt = cursor.charFormat()
        fmt.setFontUnderline(enabled)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_strikethrough(cursor: QTextCursor, enabled: bool):
        """Toggle strikethrough formatting."""
        fmt = cursor.charFormat()
        fmt.setFontStrikeOut(enabled)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_superscript(cursor: QTextCursor, enabled: bool):
        """Toggle superscript formatting."""
        fmt = cursor.charFormat()
        if enabled:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_subscript(cursor: QTextCursor, enabled: bool):
        """Toggle subscript formatting."""
        fmt = cursor.charFormat()
        if enabled:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_font_family(cursor: QTextCursor, family: str):
        """Set font family."""
        fmt = cursor.charFormat()
        fmt.setFontFamilies([family])
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_font_size(cursor: QTextCursor, size: int):
        """Set font size in points."""
        fmt = cursor.charFormat()
        fmt.setFontPointSize(size)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_text_color(cursor: QTextCursor, color: QColor):
        """Set text color."""
        fmt = cursor.charFormat()
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def set_highlight_color(cursor: QTextCursor, color: QColor):
        """Set background highlight color."""
        fmt = cursor.charFormat()
        fmt.setBackground(color)
        cursor.mergeCharFormat(fmt)
    
    @staticmethod
    def clear_formatting(cursor: QTextCursor):
        """Clear all formatting (reset to default)."""
        fmt = QTextCharFormat()
        cursor.setCharFormat(fmt)
    
    @staticmethod
    def set_alignment(cursor: QTextCursor, alignment: Qt.Alignment):
        """Set paragraph alignment."""
        fmt = cursor.blockFormat()
        fmt.setAlignment(alignment)
        cursor.mergeBlockFormat(fmt)
    
    @staticmethod
    def set_line_spacing(cursor: QTextCursor, spacing_percent: float):
        """Set line spacing as percentage (e.g., 1.0 = 100%, 1.5 = 150%)."""
        fmt = cursor.blockFormat()
        fmt.setLineHeight(spacing_percent * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight)
        cursor.mergeBlockFormat(fmt)
    
    @staticmethod
    def set_indentation(cursor: QTextCursor, indent_mm: float):
        """Set paragraph left indentation in millimeters."""
        fmt = cursor.blockFormat()
        fmt.setLeftMargin(indent_mm)
        cursor.mergeBlockFormat(fmt)
    
    @staticmethod
    def set_top_margin(cursor: QTextCursor, margin_mm: float):
        """Set paragraph top margin in millimeters."""
        fmt = cursor.blockFormat()
        fmt.setTopMargin(margin_mm)
        cursor.mergeBlockFormat(fmt)
    
    @staticmethod
    def set_bottom_margin(cursor: QTextCursor, margin_mm: float):
        """Set paragraph bottom margin in millimeters."""
        fmt = cursor.blockFormat()
        fmt.setBottomMargin(margin_mm)
        cursor.mergeBlockFormat(fmt)
    
    @staticmethod
    def is_bold(fmt: QTextCharFormat) -> bool:
        """Check if text is bold."""
        return fmt.fontWeight() >= QFont.Weight.Bold
    
    @staticmethod
    def is_italic(fmt: QTextCharFormat) -> bool:
        """Check if text is italic."""
        return fmt.fontItalic()
    
    @staticmethod
    def is_underline(fmt: QTextCharFormat) -> bool:
        """Check if text is underlined."""
        return fmt.fontUnderline()
    
    @staticmethod
    def is_strikethrough(fmt: QTextCharFormat) -> bool:
        """Check if text has strikethrough."""
        return fmt.fontStrikeOut()
    
    @staticmethod
    def get_alignment(fmt: QTextBlockFormat) -> Qt.Alignment:
        """Get current alignment."""
        return fmt.alignment()
