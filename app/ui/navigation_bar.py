"""
Modern Navigation Bar Component

Top navigation bar with project title, model selector, and action buttons.
Minimal design matching ChatGPT interface.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox, QSizePolicy
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from app.ui.styles import Theme, Colors, Spacing, Typography


class NavigationBar(QWidget):
    """
    Modern top navigation bar.
    
    Contains:
    - Project title
    - Model selector
    - Scan button
    - Finalize report button
    - Export button
    - Settings icon
    """
    
    scan_clicked = Signal()
    finalize_clicked = Signal()
    export_clicked = Signal()
    model_changed = Signal(str)
    settings_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(Theme.components.NAV_HEIGHT)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_PRIMARY};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            Theme.components.NAV_PADDING,
            Theme.components.NAV_PADDING,
            Theme.components.NAV_PADDING,
            Theme.components.NAV_PADDING
        )
        layout.setSpacing(Spacing.MD)
        
        # Project title
        self.title_label = QLabel("Security Audit Workbench")
        title_font = QFont(Typography.PRIMARY_FONT)
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight(Typography.SEMIBOLD))
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(self.title_label)
        
        # Spacer
        layout.addStretch()
        
        # Model selector
        self.model_selector = QComboBox()
        self.model_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: {Theme.border_radius.MD}px;
                padding: 6px 10px;
                font-size: {Typography.BODY_SIZE}px;
                min-width: 150px;
            }}
            QComboBox:hover {{
                border: 1px solid {Colors.TEXT_SECONDARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        """)
        layout.addWidget(self.model_selector)
        self.model_selector.currentTextChanged.connect(self.model_changed.emit)
        
        # Scan button
        self.scan_btn = self._create_button("🔍 Scan", self.scan_clicked.emit)
        layout.addWidget(self.scan_btn)
        
        # Finalize button
        self.finalize_btn = self._create_button(
            "✓ Finalize", self.finalize_clicked.emit, primary=False
        )
        self.finalize_btn.setEnabled(False)
        layout.addWidget(self.finalize_btn)
        
        # Export button
        self.export_btn = self._create_button(
            "⤓ Export", self.export_clicked.emit, primary=False
        )
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        # Settings button
        self.settings_btn = self._create_button(
            "⚙", self.settings_clicked.emit, primary=False, icon_only=True
        )
        layout.addWidget(self.settings_btn)
    
    def _create_button(self, text: str, callback, primary: bool = False, 
                       icon_only: bool = False) -> QPushButton:
        """Create a styled button."""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        
        if primary:
            btn.setProperty("accent", True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.ACCENT};
                    color: {Colors.TEXT_INVERSE};
                    border: none;
                    border-radius: {Theme.border_radius.MD}px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: {Typography.BODY_SIZE}px;
                }}
                QPushButton:hover {{
                    background-color: #1A1A1A;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.ACCENT};
                }}
                QPushButton:disabled {{
                    background-color: {Colors.BORDER};
                    color: {Colors.TEXT_SECONDARY};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: {Theme.border_radius.MD}px;
                    padding: 8px 16px;
                    font-weight: 500;
                    font-size: {Typography.BODY_SIZE}px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.HOVER};
                    border: 1px solid {Colors.BORDER};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BORDER};
                }}
                QPushButton:disabled {{
                    color: {Colors.TEXT_SECONDARY};
                    border: 1px solid {Colors.BORDER};
                    background-color: transparent;
                }}
            """)
        
        if icon_only:
            btn.setFixedWidth(40)
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: {Theme.border_radius.MD}px;
                    padding: 0px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BORDER};
                }}
            """)
        
        return btn
    
    def set_model_options(self, models: list[str]):
        """Set available model options."""
        self.model_selector.clear()
        self.model_selector.addItems(models)
    
    def get_selected_model(self) -> str:
        """Get currently selected model."""
        return self.model_selector.currentText()
    
    def set_scan_enabled(self, enabled: bool):
        """Enable/disable scan button."""
        self.scan_btn.setEnabled(enabled)
    
    def set_finalize_enabled(self, enabled: bool):
        """Enable/disable finalize button."""
        self.finalize_btn.setEnabled(enabled)
    
    def set_export_enabled(self, enabled: bool):
        """Enable/disable export button."""
        self.export_btn.setEnabled(enabled)
