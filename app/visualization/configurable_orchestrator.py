"""
Configurable Visualization Orchestrator

Generates visualizations with custom configurations and supports
updating charts when configuration changes.
"""

from typing import Dict, Any, Optional, List
from app.visualization.data_processor import ReportAnalytics
from app.visualization.configurable_charts import ConfigurableChartGenerator
from app.visualization.export_renderer import ExportRenderer
from PIL import Image
import io
import os


class VisualizationBundle:
    """Container for generated visualizations and their metadata."""
    
    def __init__(self):
        self.charts = {}
        self.image_paths = {}
        self.config = {}
    
    def add_chart(self, name: str, image_path: str, figure=None):
        """Add a chart to the bundle."""
        self.image_paths[name] = image_path
        if figure:
            self.charts[name] = figure
    
    def get_image_paths(self) -> Dict[str, str]:
        """Get all image paths."""
        return self.image_paths
    
    def get_chart(self, name: str):
        """Get a specific chart figure."""
        return self.charts.get(name)


class ConfigurableVisualizationOrchestrator:
    """
    Orchestrates visualization generation with custom configurations.
    Supports updating visualizations when config changes.
    """
    
    def __init__(self, findings: Optional[List[Dict[str, Any]]] = None,
                 config: Optional[Dict[str, Any]] = None,
                 output_dir: str = "app/visualization/output"):
        """
        Initialize orchestrator.
        
        Args:
            findings: List of finding dictionaries
            config: Visualization configuration
            output_dir: Directory for output images
        """
        self.findings = findings or []
        self.config = config or self._get_default_config()
        self.output_dir = output_dir
        self.bundle = None
        self.analytics = None
        self.renderer = ExportRenderer(cache_enabled=True)
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "theme": "light",
            "font_size": 11,
            "dpi": 300,
            "severity_enabled": True,
            "severity_type": "donut",
            "severity_width": 600,
            "severity_height": 500,
            "severity_high_color": "#d32f2f",
            "severity_medium_color": "#f57c00",
            "severity_low_color": "#fbc02d",
            "severity_info_color": "#0288d1",
            "category_enabled": True,
            "category_width": 800,
            "category_height": 500,
            "category_color_palette": ["#1976d2", "#388e3c", "#d32f2f", "#f57c00"],
            "files_enabled": True,
            "files_width": 800,
            "files_height": 500,
            "files_color": "#1976d2",
            "confidence_enabled": True,
            "confidence_width": 800,
            "confidence_height": 500,
            "confidence_color": "#388e3c",
            "risk_enabled": True,
            "risk_width": 600,
            "risk_height": 400,
            "risk_high_color": "#d32f2f",
            "risk_medium_color": "#f57c00",
            "risk_low_color": "#4caf50",
            "show_value_labels": True,
            "show_percentage": True,
            "show_grid": False,
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration and regenerate visualizations."""
        self.config.update(new_config)
        if self.findings:
            return self.generate(self.findings)
        return None
    
    def generate(self, findings: Optional[List[Dict[str, Any]]] = None) -> VisualizationBundle:
        """
        Generate all visualizations with current configuration.
        
        Args:
            findings: List of findings (if None, uses stored findings)
            
        Returns:
            VisualizationBundle with all generated charts
        """
        if findings:
            self.findings = findings
        
        # Analyze data
        self.analytics = ReportAnalytics(self.findings)
        
        # Create bundle
        self.bundle = VisualizationBundle()
        self.bundle.config = self.config.copy()
        
        # Create chart generator with custom config
        dpi = self.config.get("dpi", 300)
        generator = ConfigurableChartGenerator(config=self.config, dpi=100)  # Generate at 100 DPI
        
        # Generate each chart if enabled
        charts_generated = {}
        
        if self.config.get("severity_enabled", True):
            try:
                severity_data = self.analytics.get_severity_distribution()
                width = self.config.get("severity_width", 600)
                height = self.config.get("severity_height", 500)
                fig = generator.create_severity_distribution(severity_data, width, height)
                charts_generated["severity"] = (fig, severity_data)
            except Exception as e:
                print(f"Error generating severity chart: {e}")
        
        if self.config.get("category_enabled", True):
            try:
                category_data = self.analytics.get_category_distribution()
                width = self.config.get("category_width", 800)
                height = self.config.get("category_height", 500)
                fig = generator.create_category_distribution(category_data, width, height)
                charts_generated["category"] = (fig, category_data)
            except Exception as e:
                print(f"Error generating category chart: {e}")
        
        if self.config.get("files_enabled", True):
            try:
                file_data = self.analytics.get_file_distribution()
                width = self.config.get("files_width", 800)
                height = self.config.get("files_height", 500)
                fig = generator.create_file_distribution(file_data, width, height)
                charts_generated["file_distribution"] = (fig, file_data)
            except Exception as e:
                print(f"Error generating file distribution chart: {e}")
        
        if self.config.get("confidence_enabled", True):
            try:
                # Get confidence distribution as Dict[str, int] from ranges
                confidence_dist = self.analytics.get_confidence_distribution()
                # Convert to list of scores from the findings
                confidence_scores = []
                for finding in self.findings:
                    score = float(finding.get("confidence", 0.5))
                    confidence_scores.append(score)
                
                width = self.config.get("confidence_width", 800)
                height = self.config.get("confidence_height", 500)
                fig = generator.create_confidence_distribution(confidence_scores, width, height)
                charts_generated["confidence"] = (fig, confidence_dist)
            except Exception as e:
                print(f"Error generating confidence chart: {e}")
        
        if self.config.get("risk_enabled", True):
            try:
                risk_score = self.analytics.calculate_risk_score()
                width = self.config.get("risk_width", 600)
                height = self.config.get("risk_height", 400)
                fig = generator.create_risk_gauge(risk_score, width, height)
                charts_generated["risk_gauge"] = (fig, {"risk_score": risk_score})
            except Exception as e:
                print(f"Error generating risk gauge: {e}")
        
        # Export and save
        for chart_name, (fig, data) in charts_generated.items():
            try:
                # Convert matplotlib figure to PIL image
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                img = Image.open(buf)
                
                # Export with renderer
                export_path = self.renderer.export_image(img, chart_name, data, dpi=dpi)
                self.bundle.add_chart(chart_name, export_path, fig)
                
                buf.close()
            except Exception as e:
                print(f"Error exporting {chart_name}: {e}")
        
        return self.bundle
    
    def export_with_custom_config(self, config: Dict[str, Any], 
                                  findings: List[Dict[str, Any]]) -> VisualizationBundle:
        """
        Generate and export visualizations with custom configuration.
        
        Args:
            config: Custom configuration dictionary
            findings: List of findings
            
        Returns:
            VisualizationBundle with generated charts
        """
        self.config.update(config)
        return self.generate(findings)
    
    def get_bundle(self) -> Optional[VisualizationBundle]:
        """Get the current visualization bundle."""
        return self.bundle
