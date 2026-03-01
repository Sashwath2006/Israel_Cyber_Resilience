"""
Visualization Orchestrator

Coordinates all visualization generation, export, and integration.
Main entry point for the report generation system.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging
import os

from .data_processor import ReportAnalytics, ChartData
from .charts import ChartGenerator
from .export_renderer import ExportRenderer
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class VisualizationBundle:
    """Container for all generated visualizations."""
    
    severity_image: Optional[Image.Image] = None
    category_image: Optional[Image.Image] = None
    file_distribution_image: Optional[Image.Image] = None
    confidence_image: Optional[Image.Image] = None
    risk_gauge_image: Optional[Image.Image] = None
    
    # Export paths (high resolution)
    severity_path: Optional[str] = None
    category_path: Optional[str] = None
    file_distribution_path: Optional[str] = None
    confidence_path: Optional[str] = None
    risk_gauge_path: Optional[str] = None
    
    # Metadata
    risk_score: float = 0.0
    risk_level: str = "Minimal"
    generation_time_ms: float = 0.0
    
    def get_image_paths(self) -> Dict[str, Optional[str]]:
        """Get all exported image paths."""
        return {
            "severity": self.severity_path,
            "category": self.category_path,
            "file_distribution": self.file_distribution_path,
            "confidence": self.confidence_path,
            "risk_gauge": self.risk_gauge_path,
        }


class VisualizationOrchestrator:
    """
    Orchestrates the complete visualization pipeline.
    
    Coordinates:
    1. Data aggregation (ReportAnalytics)
    2. Chart generation (ChartGenerator)
    3. Image export (ExportRenderer)
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize orchestrator.
        
        Args:
            cache_enabled: Whether to cache generated charts
        """
        self.cached_enabled = cache_enabled
        self.exporter = ExportRenderer(cache_enabled=cache_enabled)
    
    def generate_visualizations(self, findings: List[Dict[str, Any]], 
                               export_dpi: int = 300) -> VisualizationBundle:
        """
        Generate all visualizations from findings.
        
        Args:
            findings: List of vulnerability finding dictionaries
            export_dpi: DPI for exported images (300 for PDF quality)
            
        Returns:
            VisualizationBundle with all generated visualizations
        """
        import time
        start_time = time.time()
        
        bundle = VisualizationBundle()
        
        try:
            # Step 1: Aggregate data
            logger.info(f"Processing {len(findings)} findings for visualization")
            analytics = ReportAnalytics(findings)
            chart_data = analytics.get_chart_data()
            
            # Step 2: Generate charts (100 DPI, screen resolution)
            logger.info("Generating charts...")
            bundle.severity_image = ChartGenerator.generate_severity_chart(
                chart_data.severity_distribution
            )
            bundle.category_image = ChartGenerator.generate_category_chart(
                chart_data.category_distribution
            )
            bundle.file_distribution_image = ChartGenerator.generate_file_distribution_chart(
                chart_data.file_distribution
            )
            bundle.confidence_image = ChartGenerator.generate_confidence_chart(
                chart_data.confidence_distribution
            )
            bundle.risk_gauge_image = ChartGenerator.generate_risk_gauge(
                chart_data.risk_score
            )
            
            # Store metadata
            bundle.risk_score = chart_data.risk_score
            bundle.risk_level = ReportAnalytics.get_risk_level(chart_data.risk_score)
            
            # Step 3: Export to high resolution
            logger.info(f"Exporting charts to {export_dpi} DPI...")
            if bundle.severity_image:
                bundle.severity_path = self.exporter.export_image(
                    bundle.severity_image, "severity", chart_data.severity_distribution, dpi=export_dpi
                )
            
            if bundle.category_image:
                bundle.category_path = self.exporter.export_image(
                    bundle.category_image, "category", chart_data.category_distribution, dpi=export_dpi
                )
            
            if bundle.file_distribution_image:
                bundle.file_distribution_path = self.exporter.export_image(
                    bundle.file_distribution_image, "file_distribution", 
                    chart_data.file_distribution, dpi=export_dpi
                )
            
            if bundle.confidence_image:
                bundle.confidence_path = self.exporter.export_image(
                    bundle.confidence_image, "confidence", chart_data.confidence_distribution, dpi=export_dpi
                )
            
            if bundle.risk_gauge_image:
                bundle.risk_gauge_path = self.exporter.export_image(
                    bundle.risk_gauge_image, "risk_gauge", {"risk_score": chart_data.risk_score},
                    dpi=export_dpi
                )
            
            elapsed_ms = (time.time() - start_time) * 1000
            bundle.generation_time_ms = elapsed_ms
            
            logger.info(f"Visualization generation completed in {elapsed_ms:.0f}ms")
            return bundle
        
        except Exception as e:
            logger.error(f"Failed to generate visualizations: {e}", exc_info=True)
            raise
    
    def get_markdown_section(self, bundle: VisualizationBundle, 
                            embed: bool = False) -> str:
        """
        Generate markdown section with embedded/referenced charts.
        
        Args:
            bundle: VisualizationBundle with exported images
            embed: Whether to embed images as base64 or reference files
            
        Returns:
            Markdown formatted section with charts
        """
        markdown = "## Security Analysis Visualizations\n\n"
        markdown += f"**Overall Risk Score:** {bundle.risk_score:.1f}/100 ({bundle.risk_level})\n\n"
        
        # Add each chart with description
        if bundle.severity_path:
            markdown += "### Severity Distribution\n"
            markdown += ExportRenderer.export_to_markdown(
                bundle.severity_path, 
                alt_text="Severity distribution of findings",
                embed=embed
            )
            markdown += "\n"
        
        if bundle.category_path:
            markdown += "### Vulnerability Categories\n"
            markdown += ExportRenderer.export_to_markdown(
                bundle.category_path,
                alt_text="Vulnerability categories breakdown",
                embed=embed
            )
            markdown += "\n"
        
        if bundle.file_distribution_path:
            markdown += "### Findings per File\n"
            markdown += ExportRenderer.export_to_markdown(
                bundle.file_distribution_path,
                alt_text="Findings distribution across files",
                embed=embed
            )
            markdown += "\n"
        
        if bundle.confidence_path:
            markdown += "### Confidence Score Distribution\n"
            markdown += ExportRenderer.export_to_markdown(
                bundle.confidence_path,
                alt_text="Detection confidence score distribution",
                embed=embed
            )
            markdown += "\n"
        
        if bundle.risk_gauge_path:
            markdown += "### Risk Assessment Meter\n"
            markdown += ExportRenderer.export_to_markdown(
                bundle.risk_gauge_path,
                alt_text="Overall risk assessment meter",
                embed=embed
            )
            markdown += "\n"
        
        return markdown
    
    def clear_cache(self):
        """Clear all cached visualizations."""
        self.exporter.clear_cache()
        logger.info("Visualization cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return self.exporter.get_cache_stats()
