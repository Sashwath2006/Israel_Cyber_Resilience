"""
Chart Configuration and Customization UI

Allows users to customize chart appearance, size, colors, and types.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSpinBox,
    QComboBox, QPushButton, QColorDialog, QCheckBox, QFrame, QGridLayout,
    QScrollArea, QDoubleSpinBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, Optional


class ColorPickerButton(QPushButton):
    """Button that opens a color picker dialog."""
    color_changed = Signal(str)  # Emits hex color
    
    def __init__(self, initial_color: str = "#0084ff", label: str = "Color", parent=None):
        super().__init__(parent)
        self.color = initial_color
        self.label = label
        self.setText(label)
        self.clicked.connect(self._pick_color)
        self._update_style()
    
    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self, "Choose Color")
        if color.isValid():
            self.color = color.name()
            self.color_changed.emit(self.color)
            self._update_style()
    
    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }}
        """)


class ChartConfigPanel(QWidget):
    """Panel for configuring chart appearance and behavior."""
    
    config_changed = Signal(dict)  # Emitted when configuration changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self._get_default_config()
        self._build_ui()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default chart configuration."""
        return {
            # Severity chart
            "severity_enabled": True,
            "severity_type": "donut",  # donut, pie, bar
            "severity_width": 600,
            "severity_height": 500,
            "severity_show_labels": True,
            "severity_show_percentages": True,
            "severity_high_color": "#d32f2f",
            "severity_medium_color": "#f57c00",
            "severity_low_color": "#fbc02d",
            
            # Category chart
            "category_enabled": True,
            "category_type": "bar",  # bar, horizontal_bar
            "category_width": 800,
            "category_height": 500,
            "category_show_values": True,
            "category_color": "#0084ff",
            
            # File distribution chart
            "files_enabled": True,
            "files_type": "bar",
            "files_width": 800,
            "files_height": 500,
            "files_show_values": True,
            "files_color": "#ff6f00",
            
            # Confidence chart
            "confidence_enabled": True,
            "confidence_type": "histogram",
            "confidence_width": 800,
            "confidence_height": 500,
            "confidence_show_values": True,
            "confidence_color": "#4caf50",
            
            # Risk gauge
            "risk_enabled": True,
            "risk_type": "gauge",
            "risk_width": 600,
            "risk_height": 400,
            "risk_show_label": True,
            
            # Global settings
            "dpi": 300,
            "theme": "light",  # light, dark
            "font_size": 11,
            "show_grid": True,
        }
    
    def _build_ui(self):
        """Build the configuration UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Chart Configuration")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create scroll area for many options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(10)
        
        # Global settings
        scroll_layout.addWidget(self._create_global_settings_group())
        
        # Severity chart settings
        scroll_layout.addWidget(self._create_severity_settings_group())
        
        # Category chart settings
        scroll_layout.addWidget(self._create_category_settings_group())
        
        # Files chart settings
        scroll_layout.addWidget(self._create_files_settings_group())
        
        # Confidence chart settings
        scroll_layout.addWidget(self._create_confidence_settings_group())
        
        # Risk gauge settings
        scroll_layout.addWidget(self._create_risk_settings_group())
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self._apply_changes)
        apply_btn.setStyleSheet("""
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
        """)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #999999;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_global_settings_group(self) -> QGroupBox:
        """Create global settings group."""
        group = QGroupBox("Global Settings")
        layout = QGridLayout()
        
        # DPI
        layout.addWidget(QLabel("Export DPI:"), 0, 0)
        dpi_spin = QSpinBox()
        dpi_spin.setRange(72, 600)
        dpi_spin.setValue(self.config["dpi"])
        dpi_spin.setSuffix(" DPI")
        dpi_spin.valueChanged.connect(lambda v: self._update_config("dpi", v))
        layout.addWidget(dpi_spin, 0, 1)
        
        # Theme
        layout.addWidget(QLabel("Theme:"), 1, 0)
        theme_combo = QComboBox()
        theme_combo.addItems(["light", "dark"])
        theme_combo.setCurrentText(self.config["theme"])
        theme_combo.currentTextChanged.connect(lambda v: self._update_config("theme", v))
        layout.addWidget(theme_combo, 1, 1)
        
        # Font size
        layout.addWidget(QLabel("Font Size:"), 2, 0)
        font_spin = QSpinBox()
        font_spin.setRange(8, 16)
        font_spin.setValue(self.config["font_size"])
        font_spin.valueChanged.connect(lambda v: self._update_config("font_size", v))
        layout.addWidget(font_spin, 2, 1)
        
        # Show grid
        layout.addWidget(QLabel("Show Grid Lines:"), 3, 0)
        grid_check = QCheckBox()
        grid_check.setChecked(self.config["show_grid"])
        grid_check.stateChanged.connect(lambda v: self._update_config("show_grid", bool(v)))
        layout.addWidget(grid_check, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_severity_settings_group(self) -> QGroupBox:
        """Create severity chart settings."""
        group = QGroupBox("Severity Distribution Chart")
        layout = QGridLayout()
        
        row = 0
        
        # Enabled
        enable_check = QCheckBox("Enable")
        enable_check.setChecked(self.config["severity_enabled"])
        enable_check.stateChanged.connect(lambda v: self._update_config("severity_enabled", bool(v)))
        layout.addWidget(enable_check, row, 0, 1, 2)
        row += 1
        
        # Type
        layout.addWidget(QLabel("Chart Type:"), row, 0)
        type_combo = QComboBox()
        type_combo.addItems(["donut", "pie", "bar"])
        type_combo.setCurrentText(self.config["severity_type"])
        type_combo.currentTextChanged.connect(lambda v: self._update_config("severity_type", v))
        layout.addWidget(type_combo, row, 1)
        row += 1
        
        # Dimensions
        layout.addWidget(QLabel("Width:"), row, 0)
        width_spin = QSpinBox()
        width_spin.setRange(200, 1200)
        width_spin.setValue(self.config["severity_width"])
        width_spin.setSuffix(" px")
        width_spin.valueChanged.connect(lambda v: self._update_config("severity_width", v))
        layout.addWidget(width_spin, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Height:"), row, 0)
        height_spin = QSpinBox()
        height_spin.setRange(200, 1200)
        height_spin.setValue(self.config["severity_height"])
        height_spin.setSuffix(" px")
        height_spin.valueChanged.connect(lambda v: self._update_config("severity_height", v))
        layout.addWidget(height_spin, row, 1)
        row += 1
        
        # Colors
        layout.addWidget(QLabel("High Severity Color:"), row, 0)
        high_color_btn = ColorPickerButton(self.config["severity_high_color"], "Pick Color")
        high_color_btn.color_changed.connect(lambda v: self._update_config("severity_high_color", v))
        layout.addWidget(high_color_btn, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Medium Severity Color:"), row, 0)
        med_color_btn = ColorPickerButton(self.config["severity_medium_color"], "Pick Color")
        med_color_btn.color_changed.connect(lambda v: self._update_config("severity_medium_color", v))
        layout.addWidget(med_color_btn, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Low Severity Color:"), row, 0)
        low_color_btn = ColorPickerButton(self.config["severity_low_color"], "Pick Color")
        low_color_btn.color_changed.connect(lambda v: self._update_config("severity_low_color", v))
        layout.addWidget(low_color_btn, row, 1)
        row += 1
        
        # Options
        labels_check = QCheckBox("Show Labels")
        labels_check.setChecked(self.config["severity_show_labels"])
        labels_check.stateChanged.connect(lambda v: self._update_config("severity_show_labels", bool(v)))
        layout.addWidget(labels_check, row, 0, 1, 2)
        row += 1
        
        pct_check = QCheckBox("Show Percentages")
        pct_check.setChecked(self.config["severity_show_percentages"])
        pct_check.stateChanged.connect(lambda v: self._update_config("severity_show_percentages", bool(v)))
        layout.addWidget(pct_check, row, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_category_settings_group(self) -> QGroupBox:
        """Create category chart settings."""
        group = QGroupBox("Vulnerability Categories Chart")
        layout = QGridLayout()
        
        row = 0
        
        # Enabled
        enable_check = QCheckBox("Enable")
        enable_check.setChecked(self.config["category_enabled"])
        enable_check.stateChanged.connect(lambda v: self._update_config("category_enabled", bool(v)))
        layout.addWidget(enable_check, row, 0, 1, 2)
        row += 1
        
        # Type
        layout.addWidget(QLabel("Chart Type:"), row, 0)
        type_combo = QComboBox()
        type_combo.addItems(["bar", "horizontal_bar"])
        type_combo.setCurrentText(self.config["category_type"])
        type_combo.currentTextChanged.connect(lambda v: self._update_config("category_type", v))
        layout.addWidget(type_combo, row, 1)
        row += 1
        
        # Dimensions
        layout.addWidget(QLabel("Width:"), row, 0)
        width_spin = QSpinBox()
        width_spin.setRange(200, 1200)
        width_spin.setValue(self.config["category_width"])
        width_spin.setSuffix(" px")
        width_spin.valueChanged.connect(lambda v: self._update_config("category_width", v))
        layout.addWidget(width_spin, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Height:"), row, 0)
        height_spin = QSpinBox()
        height_spin.setRange(200, 1200)
        height_spin.setValue(self.config["category_height"])
        height_spin.setSuffix(" px")
        height_spin.valueChanged.connect(lambda v: self._update_config("category_height", v))
        layout.addWidget(height_spin, row, 1)
        row += 1
        
        # Color
        layout.addWidget(QLabel("Color:"), row, 0)
        color_btn = ColorPickerButton(self.config["category_color"], "Pick Color")
        color_btn.color_changed.connect(lambda v: self._update_config("category_color", v))
        layout.addWidget(color_btn, row, 1)
        row += 1
        
        # Options
        values_check = QCheckBox("Show Values")
        values_check.setChecked(self.config["category_show_values"])
        values_check.stateChanged.connect(lambda v: self._update_config("category_show_values", bool(v)))
        layout.addWidget(values_check, row, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_files_settings_group(self) -> QGroupBox:
        """Create files distribution chart settings."""
        group = QGroupBox("Findings per File Chart")
        layout = QGridLayout()
        
        row = 0
        
        # Enabled
        enable_check = QCheckBox("Enable")
        enable_check.setChecked(self.config["files_enabled"])
        enable_check.stateChanged.connect(lambda v: self._update_config("files_enabled", bool(v)))
        layout.addWidget(enable_check, row, 0, 1, 2)
        row += 1
        
        # Dimensions
        layout.addWidget(QLabel("Width:"), row, 0)
        width_spin = QSpinBox()
        width_spin.setRange(200, 1200)
        width_spin.setValue(self.config["files_width"])
        width_spin.setSuffix(" px")
        width_spin.valueChanged.connect(lambda v: self._update_config("files_width", v))
        layout.addWidget(width_spin, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Height:"), row, 0)
        height_spin = QSpinBox()
        height_spin.setRange(200, 1200)
        height_spin.setValue(self.config["files_height"])
        height_spin.setSuffix(" px")
        height_spin.valueChanged.connect(lambda v: self._update_config("files_height", v))
        layout.addWidget(height_spin, row, 1)
        row += 1
        
        # Color
        layout.addWidget(QLabel("Color:"), row, 0)
        color_btn = ColorPickerButton(self.config["files_color"], "Pick Color")
        color_btn.color_changed.connect(lambda v: self._update_config("files_color", v))
        layout.addWidget(color_btn, row, 1)
        row += 1
        
        # Options
        values_check = QCheckBox("Show Values")
        values_check.setChecked(self.config["files_show_values"])
        values_check.stateChanged.connect(lambda v: self._update_config("files_show_values", bool(v)))
        layout.addWidget(values_check, row, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_confidence_settings_group(self) -> QGroupBox:
        """Create confidence chart settings."""
        group = QGroupBox("Confidence Score Distribution Chart")
        layout = QGridLayout()
        
        row = 0
        
        # Enabled
        enable_check = QCheckBox("Enable")
        enable_check.setChecked(self.config["confidence_enabled"])
        enable_check.stateChanged.connect(lambda v: self._update_config("confidence_enabled", bool(v)))
        layout.addWidget(enable_check, row, 0, 1, 2)
        row += 1
        
        # Dimensions
        layout.addWidget(QLabel("Width:"), row, 0)
        width_spin = QSpinBox()
        width_spin.setRange(200, 1200)
        width_spin.setValue(self.config["confidence_width"])
        width_spin.setSuffix(" px")
        width_spin.valueChanged.connect(lambda v: self._update_config("confidence_width", v))
        layout.addWidget(width_spin, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Height:"), row, 0)
        height_spin = QSpinBox()
        height_spin.setRange(200, 1200)
        height_spin.setValue(self.config["confidence_height"])
        height_spin.setSuffix(" px")
        height_spin.valueChanged.connect(lambda v: self._update_config("confidence_height", v))
        layout.addWidget(height_spin, row, 1)
        row += 1
        
        # Color
        layout.addWidget(QLabel("Color:"), row, 0)
        color_btn = ColorPickerButton(self.config["confidence_color"], "Pick Color")
        color_btn.color_changed.connect(lambda v: self._update_config("confidence_color", v))
        layout.addWidget(color_btn, row, 1)
        row += 1
        
        # Options
        values_check = QCheckBox("Show Values")
        values_check.setChecked(self.config["confidence_show_values"])
        values_check.stateChanged.connect(lambda v: self._update_config("confidence_show_values", bool(v)))
        layout.addWidget(values_check, row, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def _create_risk_settings_group(self) -> QGroupBox:
        """Create risk gauge settings."""
        group = QGroupBox("Risk Assessment Gauge")
        layout = QGridLayout()
        
        row = 0
        
        # Enabled
        enable_check = QCheckBox("Enable")
        enable_check.setChecked(self.config["risk_enabled"])
        enable_check.stateChanged.connect(lambda v: self._update_config("risk_enabled", bool(v)))
        layout.addWidget(enable_check, row, 0, 1, 2)
        row += 1
        
        # Dimensions
        layout.addWidget(QLabel("Width:"), row, 0)
        width_spin = QSpinBox()
        width_spin.setRange(200, 1200)
        width_spin.setValue(self.config["risk_width"])
        width_spin.setSuffix(" px")
        width_spin.valueChanged.connect(lambda v: self._update_config("risk_width", v))
        layout.addWidget(width_spin, row, 1)
        row += 1
        
        layout.addWidget(QLabel("Height:"), row, 0)
        height_spin = QSpinBox()
        height_spin.setRange(200, 1200)
        height_spin.setValue(self.config["risk_height"])
        height_spin.setSuffix(" px")
        height_spin.valueChanged.connect(lambda v: self._update_config("risk_height", v))
        layout.addWidget(height_spin, row, 1)
        row += 1
        
        # Options
        label_check = QCheckBox("Show Label")
        label_check.setChecked(self.config["risk_show_label"])
        label_check.stateChanged.connect(lambda v: self._update_config("risk_show_label", bool(v)))
        layout.addWidget(label_check, row, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def _update_config(self, key: str, value: Any):
        """Update configuration value."""
        self.config[key] = value
    
    def _apply_changes(self):
        """Emit configuration changes."""
        self.config_changed.emit(self.config.copy())
    
    def _reset_to_defaults(self):
        """Reset to default configuration."""
        self.config = self._get_default_config()
        # Rebuild UI to reflect defaults
        self._build_ui()
        self._apply_changes()
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
