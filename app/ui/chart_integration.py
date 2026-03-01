"""
Chart Integration Manager

Manages the complete workflow of customizing and embedding charts into the report.
Bridges between ChartConfigPanel, ConfigurableVisualizationOrchestrator, and ReportEditor.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
    QScrollArea, QLabel, QMessageBox, QTabWidget
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, Signal
from app.ui.chart_config import ChartConfigPanel
from app.visualization.configurable_orchestrator import ConfigurableVisualizationOrchestrator
from app.ui.embedded_charts import EmbeddedChartHandler
import os


class ChartIntegrationDialog(QDialog):
    """
    Dialog that manages chart customization and embedding.
    Combines configuration, preview, and embedding all in one place.
    """
    
    charts_applied = Signal(dict)  # Emits final configuration
    
    def __init__(self, findings: list[dict], parent=None):
        """
        Initialize chart integration dialog.
        
        Args:
            findings: List of vulnerability findings
            parent: Parent widget
        """
        super().__init__(parent)
        self.findings = findings
        self.parent_window = parent
        self.orchestrator = None
        self.current_bundle = None
        self.current_config = {}
        
        self.setWindowTitle("Chart Customization & Embedding")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QTabWidget {
                background-color: white;
            }
        """)
        
        self._build_ui()
        self._initialize_orchestrator()
        self._generate_default_charts()
    
    def _build_ui(self):
        """Build the UI layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Tab 1: Configuration
        self.config_panel = ChartConfigPanel()
        self.config_panel.config_changed.connect(self._on_config_changed)
        tabs.addTab(self.config_panel, "📊 Configuration")
        
        # Tab 2: Preview
        preview_widget = self._create_preview_tab()
        tabs.addTab(preview_widget, "👁 Preview")
        
        # Tab 3: Embedding Options
        embed_widget = self._create_embedding_tab()
        tabs.addTab(embed_widget, "📌 Embedding")
        
        layout.addWidget(tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Reset button
        reset_btn = QPushButton("↻ Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        reset_btn.clicked.connect(self._reset_config)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("✕ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Apply button
        apply_btn = QPushButton("✓ Apply & Embed in Report")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self._apply_and_embed)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_preview_tab(self) -> QWidget:
        """Create preview tab showing current charts."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Chart Preview")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Info text
        info = QLabel("The charts below will update as you adjust configuration settings.")
        info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info)
        
        # Scroll area for chart previews
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout()
        self.preview_layout.setSpacing(20)
        self.preview_container.setLayout(self.preview_layout)
        
        scroll.setWidget(self.preview_container)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def _create_embedding_tab(self) -> QWidget:
        """Create embedding options tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Embedding Options")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Embedding location options
        info = QLabel("Choose where to embed the charts in your report:")
        layout.addWidget(info)
        
        # Option 1: End of report
        opt1 = QLabel("✓ End of Report (Default)")
        opt1.setStyleSheet("padding: 8px; background-color: white; border-radius: 4px;")
        layout.addWidget(opt1)
        
        # Option 2: After findings
        opt2 = QLabel("✓ After Findings Section")
        opt2.setStyleSheet("padding: 8px; background-color: white; border-radius: 4px;")
        layout.addWidget(opt2)
        
        # Info box
        info_box = QLabel(
            "💡 <b>Note:</b> The charts will be embedded as images in your report. "
            "You can edit the report text but the chart images will remain intact. "
            "Export to PDF to preserve all formatting."
        )
        info_box.setWordWrap(True)
        info_box.setStyleSheet("""
            padding: 12px;
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            border-radius: 4px;
        """)
        layout.addWidget(info_box)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _initialize_orchestrator(self):
        """Initialize the configurable visualization orchestrator."""
        try:
            self.orchestrator = ConfigurableVisualizationOrchestrator(
                findings=self.findings,
                output_dir="app/visualization/output"
            )
        except Exception as e:
            print(f"Error initializing orchestrator: {e}")
    
    def _generate_default_charts(self):
        """Generate charts with default configuration."""
        if not self.orchestrator:
            return
        
        try:
            self.current_bundle = self.orchestrator.generate(self.findings)
            self._update_preview()
        except Exception as e:
            print(f"Error generating default charts: {e}")
    
    def _on_config_changed(self):
        """Handle configuration changes - regenerate charts."""
        if not self.orchestrator:
            return
        
        try:
            config = self.config_panel.get_config()
            self.current_bundle = self.orchestrator.update_config(config)
            self.current_config = config
            self._update_preview()
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def _update_preview(self):
        """Update the preview tab with current charts."""
        # Clear previous preview
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        
        if not self.current_bundle:
            label = QLabel("No charts generated")
            self.preview_layout.addWidget(label)
            return
        
        # Get chart paths
        paths = self.current_bundle.get_image_paths()
        titles = {
            "severity": "📊 Severity Distribution",
            "category": "📁 Vulnerability Categories",
            "file_distribution": "📄 Findings per File",
            "confidence": "🎯 Confidence Distribution",
            "risk_gauge": "⚠ Risk Assessment",
        }
        
        for key, title in titles.items():
            path = paths.get(key)
            if path and os.path.exists(path):
                # Chart title
                chart_title = QLabel(title)
                chart_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                self.preview_layout.addWidget(chart_title)
                
                # Chart image
                try:
                    img_label = QLabel()
                    pixmap = QPixmap(path)
                    
                    # Scale to preview size
                    scaled = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
                    img_label.setPixmap(scaled)
                    img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    self.preview_layout.addWidget(img_label)
                    self.preview_layout.addSpacing(20)
                except Exception as e:
                    print(f"Error loading preview {key}: {e}")
        
        self.preview_layout.addStretch()
    
    def _reset_config(self):
        """Reset configuration to defaults."""
        self.config_panel._reset_to_defaults()
        self._on_config_changed()
    
    def _apply_and_embed(self):
        """Apply configuration and embed charts in report."""
        try:
            # Get final configuration
            config = self.config_panel.get_config()
            
            # Get the parent report editor
            if self.parent_window and hasattr(self.parent_window, 'report_editor'):
                report_editor = self.parent_window.report_editor
                
                # Create embedded chart handler
                handler = EmbeddedChartHandler(
                    visualizations=self.current_bundle,
                    config=config
                )
                
                # Embed charts into the report
                success = handler.embed_charts_into_editor(report_editor)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        "✓ Charts have been embedded into your report!\n\n"
                        "You can now:\n"
                        "• Edit the text around the charts\n"
                        "• Export to PDF with embedded visualizations\n"
                        "• Adjust settings in Configuration tab to re-embed"
                    )
                    self.charts_applied.emit(config)
                    self.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Embedding Failed",
                        "Failed to embed charts in the report."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Report editor not found. Cannot embed charts."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error embedding charts: {str(e)}"
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get the final configuration."""
        return self.config_panel.get_config()
