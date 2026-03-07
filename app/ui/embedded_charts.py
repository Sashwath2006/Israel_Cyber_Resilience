"""
Embedded Chart Handler

Manages embedding charts directly into the report editor with custom sizing
and styling based on configuration.
"""

import os
from typing import Dict, Any, Optional
from PIL import Image
import io
from PySide6.QtGui import QTextDocument, QTextCursor, QTextImageFormat
from PySide6.QtWidgets import QTextEdit


class EmbeddedChartHandler:
    """Handles embedding charts into the report editor."""
    
    def __init__(self, visualizations=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize handler.
        
        Args:
            visualizations: VisualizationBundle from orchestrator
            config: Chart configuration dictionary
        """
        self.visualizations = visualizations
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "severity_enabled": True,
            "category_enabled": True,
            "files_enabled": True,
            "confidence_enabled": True,
            "risk_enabled": True,
            "severity_width": 600,
            "severity_height": 500,
            "category_width": 800,
            "category_height": 500,
            "files_width": 800,
            "files_height": 500,
            "confidence_width": 800,
            "confidence_height": 500,
            "risk_width": 600,
            "risk_height": 400,
        }
    
    def embed_charts_into_editor(self, editor: QTextEdit, position: int = -1) -> bool:
        """
        Embed charts directly into the report editor.
        
        Args:
            editor: QTextEdit instance (ReportEditor)
            position: Position to insert charts (-1 for end)
            
        Returns:
            True if successful
        """
        if not self.visualizations:
            return False
        
        try:
            cursor = editor.textCursor()
            if position >= 0:
                cursor.setPosition(position)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            
            # Add charts section header
            cursor.insertText("\n\n")
            cursor.insertText("=" * 70 + "\n")
            cursor.insertText("VULNERABILITY VISUALIZATIONS\n")
            cursor.insertText("=" * 70 + "\n\n")
            
            # Try to insert each chart
            paths = self.visualizations.get_image_paths()
            titles = {
                "severity": "Severity Distribution",
                "category": "Vulnerability Categories",
                "file_distribution": "Findings per File",
                "confidence": "Confidence Score Distribution",
                "risk_gauge": "Risk Assessment",
            }
            
            for key, title in titles.items():
                if not self.config.get(f"{key.replace('_', '')}_enabled", True):
                    continue
                
                path = paths.get(key)
                if path and os.path.exists(path):
                    # Insert chart title
                    cursor.insertText(f"\n{title}\n")
                    cursor.insertText("-" * 70 + "\n\n")
                    
                    # Get configured dimensions
                    key_prefix = key.replace("_", "")
                    width = self.config.get(f"{key_prefix}_width", 800)
                    height = self.config.get(f"{key_prefix}_height", 500)
                    
                    # Insert image
                    image_format = QTextImageFormat()
                    image_format.setName(path)
                    image_format.setWidth(width)
                    image_format.setHeight(height)
                    
                    cursor.insertImage(image_format)
                    cursor.insertText("\n\n")
            
            return True
        
        except Exception as e:
            print(f"Error embedding charts: {e}")
            return False
    
    def get_chart_html(self) -> str:
        """
        Generate HTML representation of charts for export.
        
        Returns:
            HTML string with embedded chart images
        """
        if not self.visualizations:
            return ""
        
        html_parts = []
        html_parts.append("<hr style='margin: 30px 0;'>")
        html_parts.append("<h2>Vulnerability Visualizations</h2>")
        
        paths = self.visualizations.get_image_paths()
        titles = {
            "severity": "Severity Distribution",
            "category": "Vulnerability Categories",
            "file_distribution": "Findings per File",
            "confidence": "Confidence Score Distribution",
            "risk_gauge": "Risk Assessment",
        }
        
        for key, title in titles.items():
            if not self.config.get(f"{key.replace('_', '')}_enabled", True):
                continue
            
            path = paths.get(key)
            if path and os.path.exists(path):
                key_prefix = key.replace("_", "")
                width = self.config.get(f"{key_prefix}_width", 800)
                height = self.config.get(f"{key_prefix}_height", 500)
                
                html_parts.append(f"<h3>{title}</h3>")
                html_parts.append(f"<img src='{path}' width='{width}' height='{height}' style='margin: 20px 0; border: 1px solid #e0e0e0;'>")
        
        return "\n".join(html_parts)
    
    def insert_chart_section(self, editor: QTextEdit, 
                            after_section: Optional[str] = None) -> bool:
        """
        Insert chart section at a specific location in the report.
        
        Args:
            editor: QTextEdit instance
            after_section: Insert after this section name (e.g., "EXECUTIVE SUMMARY")
            
        Returns:
            True if successful
        """
        if not self.visualizations:
            return False
        
        try:
            doc = editor.document()
            text = doc.toPlainText()
            
            # Find insertion point
            if after_section:
                # Find the section in the document
                section_pos = text.find(after_section)
                if section_pos >= 0:
                    # Find the next line after section
                    next_line = text.find("\n", section_pos)
                    insert_pos = next_line + 1 if next_line >= 0 else len(text)
                else:
                    insert_pos = len(text)
            else:
                insert_pos = len(text)
            
            cursor = editor.textCursor()
            cursor.setPosition(insert_pos)
            editor.setTextCursor(cursor)
            
            return self.embed_charts_into_editor(editor, insert_pos)
        
        except Exception as e:
            print(f"Error inserting chart section: {e}")
            return False
