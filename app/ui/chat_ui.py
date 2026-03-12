"""
Modern Chat Interface Component

ChatGPT-style conversation UI with glassmorphism message bubbles, typing indicators, and input field.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton,
    QTextEdit, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont, QTextCursor, QTextOption, QDesktopServices
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from app.ui.modern_theme import (
    DeepSpaceColors, ModernTypography, ModernSpacing, ModernBorderRadius,
    ModernShadow
)


class MessageBubble(QFrame):
    """
    Minimalist message display - simple text stream without bubbles.
    
    Messages are distinguished by labels and indentation rather than visual containers.
    """
    
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        
        # Frame setup - transparent, no decoration
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: transparent; border: none;")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label: "You" or "AI"
        label_text = "You" if is_user else "AI"
        label = QLabel(label_text)
        label_font = QFont(ModernTypography.PRIMARY_FONT)
        label_font.setPixelSize(ModernTypography.SIZE_SM)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {DeepSpaceColors.TEXT_PRIMARY}; font-weight: 700;")
        layout.addWidget(label)
        
        # Message text - no bubble, just text
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        text_font = QFont(ModernTypography.MONO_FONT)
        text_font.setPixelSize(ModernTypography.SIZE_BASE)
        message_label.setFont(text_font)
        message_label.setStyleSheet(f"color: {DeepSpaceColors.TEXT_PRIMARY}; margin-left: 12px;")
        layout.addWidget(message_label)
        
        # Add bottom margin for spacing between messages
        layout.addSpacing(ModernSpacing.MD)
        
        # Set sizing policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class ChatInterface(QWidget):
    """
    Minimalist Chat Interface - Clean, flat design inspired by Ollama.
    
    Features:
    - Vertical text stream (no bubbles)
    - Simple borderless input with divider
    - Clean, ghost-style buttons
    - High-contrast typography
    """
    
    send_message = Signal(str)
    upload_files = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # White background for clean look
        self.setStyleSheet(f"background-color: {DeepSpaceColors.WHITE};")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Messages scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {DeepSpaceColors.WHITE};
                border: none;
            }}
            QScrollBar:vertical {{
                width: 8px;
                background-color: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {DeepSpaceColors.BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {DeepSpaceColors.BORDER_DARK};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: transparent;
                border: none;
            }}
        """)
        
        # Messages container
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(ModernSpacing.LG, ModernSpacing.LG, ModernSpacing.LG, ModernSpacing.LG)
        self.messages_layout.setSpacing(ModernSpacing.MD)
        self.messages_layout.addStretch()
        
        self.messages_container.setStyleSheet(f"background-color: {DeepSpaceColors.WHITE};")
        self.messages_container.setLayout(self.messages_layout)
        scroll_area.setWidget(self.messages_container)
        layout.addWidget(scroll_area, 1)
        
        # Separator line - subtle divider above input
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {DeepSpaceColors.BORDER};
                border: none;
                height: 1px;
                margin: 0px;
            }}
        """)
        layout.addWidget(separator)
        
        # Input area
        input_area = self._create_input_area()
        layout.addWidget(input_area)
        
        self.scroll_area = scroll_area
    
    def _create_input_area(self) -> QWidget:
        """Create the minimalist input area with ghost buttons."""
        container = QWidget()
        container.setStyleSheet(f"background-color: {DeepSpaceColors.WHITE};")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(ModernSpacing.LG, ModernSpacing.MD, ModernSpacing.LG, ModernSpacing.MD)
        layout.setSpacing(ModernSpacing.SM)
        
        # Upload button - ghost style (border only)
        upload_btn = QPushButton("+")
        upload_btn.setFixedSize(32, 32)
        upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DeepSpaceColors.TEXT_PRIMARY};
                border: 1px solid transparent;
                border-radius: {ModernBorderRadius.MD}px;
                font-size: 16px;
                font-weight: 600;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {DeepSpaceColors.GREY_LIGHT};
                border: 1px solid {DeepSpaceColors.BORDER};
            }}
            QPushButton:pressed {{
                background-color: {DeepSpaceColors.BORDER};
            }}
        """)
        upload_btn.clicked.connect(self._handle_upload)
        layout.addWidget(upload_btn)
        
        # Text input - borderless with divider above
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Ask about vulnerabilities...")
        self.input_field.setMinimumHeight(40)
        self.input_field.setMaximumHeight(120)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {DeepSpaceColors.WHITE};
                color: {DeepSpaceColors.TEXT_PRIMARY};
                border: none;
                border-radius: 0px;
                padding: 0px 8px;
                font-family: {ModernTypography.PRIMARY_FONT};
                font-size: {ModernTypography.SIZE_BASE}px;
                font-weight: {ModernTypography.WEIGHT_NORMAL};
                selection-background-color: {DeepSpaceColors.GREY_LIGHT};
            }}
            QTextEdit:focus {{
                border: none;
                background-color: {DeepSpaceColors.WHITE};
                outline: none;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background-color: transparent;
            }}
            QScrollBar::handle:vertical {{
                background-color: {DeepSpaceColors.BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
        """)
        self.input_field.textChanged.connect(self._on_text_changed)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field, 1)
        
        # Send button - primary action (solid black)
        send_btn = QPushButton("⤴")
        send_btn.setFixedSize(32, 32)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DeepSpaceColors.TEXT_PRIMARY};
                color: {DeepSpaceColors.WHITE};
                border: 1px solid {DeepSpaceColors.TEXT_PRIMARY};
                border-radius: {ModernBorderRadius.MD}px;
                font-size: 14px;
                font-weight: {ModernTypography.WEIGHT_BOLD};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {DeepSpaceColors.GREY_DARK};
                border: 1px solid {DeepSpaceColors.GREY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {DeepSpaceColors.TEXT_PRIMARY};
            }}
        """)
        send_btn.clicked.connect(self._handle_send)
        layout.addWidget(send_btn)
        
        return container
    
    def _on_text_changed(self):
        """Handle text changes - auto-expand input field."""
        doc_height = self.input_field.document().size().height()
        current_height = self.input_field.height()
        min_height = 40
        max_height = 120
        
        if doc_height < min_height:
            self.input_field.setFixedHeight(min_height)
        elif doc_height > max_height:
            self.input_field.setFixedHeight(max_height)
        else:
            self.input_field.setFixedHeight(int(doc_height) + 10)
    
    def _handle_send(self):
        """Send message."""
        text = self.input_field.toPlainText().strip()
        if text:
            self.add_message(text, is_user=True)
            self.send_message.emit(text)
            self.input_field.clear()
            self._on_text_changed()
    
    def _handle_upload(self):
        """Handle file upload."""
        from PySide6.QtWidgets import QFileDialog
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Analyze",
            "",
            "All Files (*.*)"
        )
        if paths:
            self.upload_files.emit(paths)
    
    def eventFilter(self, obj, event):
        """Handle Enter/Shift+Enter in text input."""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: add new line
                    self.input_field.insertPlainText("\n")
                    return True
                else:
                    # Enter: send message
                    self._handle_send()
                    return True
        return super().eventFilter(obj, event)
    
    def add_message(self, text: str, is_user: bool):
        """Add a message to the chat."""
        bubble = MessageBubble(text, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        
        # Auto-scroll to bottom
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll messages area to bottom."""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def clear_messages(self):
        """Clear all messages from chat."""
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()
