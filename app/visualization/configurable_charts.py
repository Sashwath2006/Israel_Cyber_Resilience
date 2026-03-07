"""
Configurable Chart Generator

Generates charts with custom colors, dimensions, and styling based on configuration dictionary.
Extends the base ChartGenerator with customization support.
"""

from typing import Dict, Any, Optional, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np


class ConfigurableChartGenerator:
    """Charts with full customization support."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, dpi: int = 100):
        """
        Initialize with optional configuration.
        
        Args:
            config: Configuration dictionary with colors, sizes, etc.
            dpi: DPI for the charts
        """
        self.config = config or self._get_default_config()
        self.dpi = dpi
        self._apply_theme()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "theme": "light",
            "font_size": 11,
            "severity_type": "donut",
            "severity_high_color": "#d32f2f",
            "severity_medium_color": "#f57c00",
            "severity_low_color": "#fbc02d",
            "severity_info_color": "#0288d1",
            "category_color_palette": ["#1976d2", "#388e3c", "#d32f2f", "#f57c00", 
                                       "#7b1fa2", "#0097a7", "#c2185b", "#558b2f"],
            "files_color": "#1976d2",
            "confidence_color": "#388e3c",
            "risk_high_color": "#d32f2f",
            "risk_medium_color": "#f57c00",
            "risk_low_color": "#4caf50",
            "show_value_labels": True,
            "show_percentage": True,
            "show_grid": False,
        }
    
    def _apply_theme(self):
        """Apply matplotlib theme based on config."""
        theme = self.config.get("theme", "light")
        
        if theme == "dark":
            plt.style.use("dark_background")
        else:
            plt.style.use("seaborn-v0_8-darkgrid" if "seaborn" in plt.style.available else "default")
    
    def create_severity_distribution(self, 
                                    data: Dict[str, int],
                                    width: int = 600,
                                    height: int = 500) -> Figure:
        """
        Create severity distribution chart with configuration.
        
        Args:
            data: {"High": int, "Medium": int, "Low": int, "Info": int}
            width: Figure width in pixels
            height: Figure height in pixels
            
        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        
        # Get colors from config
        colors = [
            self.config.get("severity_high_color", "#d32f2f"),
            self.config.get("severity_medium_color", "#f57c00"),
            self.config.get("severity_low_color", "#fbc02d"),
            self.config.get("severity_info_color", "#0288d1"),
        ]
        
        # Get chart type
        chart_type = self.config.get("severity_type", "donut")
        
        labels = list(data.keys())
        values = list(data.values())
        
        # Filter to only include present severity levels
        filtered_labels = []
        filtered_values = []
        filtered_colors = []
        
        severity_order = ["High", "Medium", "Low", "Info"]
        for severity in severity_order:
            if severity in data and data[severity] > 0:
                filtered_labels.append(severity)
                filtered_values.append(data[severity])
                idx = severity_order.index(severity)
                filtered_colors.append(colors[idx])
        
        if not filtered_values:
            ax.text(0.5, 0.5, "No vulnerability data", 
                   ha="center", va="center", transform=ax.transAxes)
            return fig
        
        if chart_type == "donut":
            result = ax.pie(
                filtered_values,
                labels=filtered_labels,
                colors=filtered_colors,
                autopct="%1.1f%%" if self.config.get("show_percentage", True) else None,
                startangle=90,
                wedgeprops=dict(width=0.5, edgecolor="white")
            )
            wedges = result[0]
            texts = result[1]
            autotexts = result[2] if len(result) > 2 else []
        elif chart_type == "pie":
            result = ax.pie(
                filtered_values,
                labels=filtered_labels,
                colors=filtered_colors,
                autopct="%1.1f%%" if self.config.get("show_percentage", True) else None,
                startangle=90
            )
            wedges = result[0]
            texts = result[1]
            autotexts = result[2] if len(result) > 2 else []
        else:  # bar
            ax.bar(filtered_labels, filtered_values, color=filtered_colors, edgecolor="black", linewidth=1.5)
            ax.set_ylabel("Count", fontsize=self.config.get("font_size", 11))
            if self.config.get("show_value_labels", True):
                for i, v in enumerate(filtered_values):
                    ax.text(i, v, str(v), ha="center", va="bottom")
            if self.config.get("show_grid", False):
                ax.grid(True, axis="y", alpha=0.3)
        
        ax.set_title("Severity Distribution", fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        
        # Style text
        for text in texts:
            text.set_fontsize(self.config.get("font_size", 11))
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(self.config.get("font_size", 11) - 1)
            autotext.set_fontweight("bold")
        
        plt.tight_layout()
        return fig
    
    def create_category_distribution(self,
                                    data: Dict[str, int],
                                    width: int = 800,
                                    height: int = 500,
                                    horizontal: bool = False) -> Figure:
        """
        Create category distribution chart.
        
        Args:
            data: {"category": count}
            width: Figure width in pixels
            height: Figure height in pixels
            horizontal: If True, create horizontal bar chart
            
        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        
        # Sort by value descending
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        
        categories = list(sorted_data.keys())
        values = list(sorted_data.values())
        
        # Get colors
        color_palette = self.config.get("category_color_palette", 
                                       ["#1976d2", "#388e3c", "#d32f2f", "#f57c00"])
        colors = [color_palette[i % len(color_palette)] for i in range(len(categories))]
        
        if horizontal:
            ax.barh(categories, values, color=colors, edgecolor="black", linewidth=1.5)
            ax.set_xlabel("Count", fontsize=self.config.get("font_size", 11))
            if self.config.get("show_value_labels", True):
                for i, v in enumerate(values):
                    ax.text(v, i, f" {v}", ha="left", va="center")
            if self.config.get("show_grid", False):
                ax.grid(True, axis="x", alpha=0.3)
        else:
            ax.bar(categories, values, color=colors, edgecolor="black", linewidth=1.5)
            ax.set_ylabel("Count", fontsize=self.config.get("font_size", 11))
            if self.config.get("show_value_labels", True):
                for i, v in enumerate(values):
                    ax.text(i, v, str(v), ha="center", va="bottom")
            if self.config.get("show_grid", False):
                ax.grid(True, axis="y", alpha=0.3)
            ax.tick_params(axis="x", rotation=45)
        
        ax.set_title("Vulnerability Categories", fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        plt.tight_layout()
        return fig
    
    def create_file_distribution(self,
                                data: Dict[str, int],
                                width: int = 800,
                                height: int = 500) -> Figure:
        """Create file distribution chart."""
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        
        # Sort by value descending, take top 10
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:10])
        
        files = list(sorted_data.keys())
        values = list(sorted_data.values())
        
        color = self.config.get("files_color", "#1976d2")
        
        ax.bar(files, values, color=color, edgecolor="black", linewidth=1.5)
        ax.set_ylabel("Finding Count", fontsize=self.config.get("font_size", 11))
        ax.set_title("Top 10 Files with Findings", fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        
        if self.config.get("show_value_labels", True):
            for i, v in enumerate(values):
                ax.text(i, v, str(v), ha="center", va="bottom")
        
        if self.config.get("show_grid", False):
            ax.grid(True, axis="y", alpha=0.3)
        
        ax.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        return fig
    
    def create_confidence_distribution(self,
                                      data: List[float],
                                      width: int = 800,
                                      height: int = 500,
                                      bins: int = 10) -> Figure:
        """Create confidence score distribution histogram."""
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        
        if not data or len(data) == 0:
            ax.text(0.5, 0.5, "No confidence data", 
                   ha="center", va="center", transform=ax.transAxes)
            return fig
        
        color = self.config.get("confidence_color", "#388e3c")
        
        ax.hist(data, bins=bins, color=color, edgecolor="black", linewidth=1.5, alpha=0.7)
        ax.set_xlabel("Confidence Score", fontsize=self.config.get("font_size", 11))
        ax.set_ylabel("Frequency", fontsize=self.config.get("font_size", 11))
        ax.set_title("Confidence Score Distribution", fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        
        if self.config.get("show_grid", False):
            ax.grid(True, axis="y", alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_risk_gauge(self,
                         risk_score: float,
                         width: int = 600,
                         height: int = 400) -> Figure:
        """Create risk assessment gauge chart."""
        fig, ax = plt.subplots(figsize=(width/self.dpi, height/self.dpi), dpi=self.dpi)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Determine risk level and color
        if risk_score >= 7:
            level = "HIGH"
            color = self.config.get("risk_high_color", "#d32f2f")
        elif risk_score >= 4:
            level = "MEDIUM"
            color = self.config.get("risk_medium_color", "#f57c00")
        else:
            level = "LOW"
            color = self.config.get("risk_low_color", "#4caf50")
        
        # Draw gauge background
        circle_bg = mpatches.Circle((5, 2), 4, color="#e0e0e0", zorder=1)
        ax.add_patch(circle_bg)
        
        # Draw gauge foreground (risk level)
        angle_start = 180
        angle_end = 180 - (risk_score / 10.0 * 180)
        theta = np.linspace(np.radians(angle_end), np.radians(angle_start), 100)
        r = 4
        x = 5 + r * np.cos(theta)
        y = 2 + r * np.sin(theta)
        ax.fill(np.concatenate([[5], x, [5]]), np.concatenate([[2], y, [2]]), 
               color=color, alpha=0.8, zorder=2)
        
        # Draw labels
        ax.text(1, 2, "0", ha="center", va="center", fontsize=self.config.get("font_size", 11))
        ax.text(9, 2, "10", ha="center", va="center", fontsize=self.config.get("font_size", 11))
        
        # Draw risk score and level
        ax.text(5, 5.5, f"{risk_score:.1f}", ha="center", va="center", 
               fontsize=self.config.get("font_size", 11) + 4, fontweight="bold")
        ax.text(5, 4.5, level, ha="center", va="center", 
               fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        
        ax.set_title("Risk Assessment", fontsize=self.config.get("font_size", 11) + 2, fontweight="bold")
        ax.axis("off")
        
        plt.tight_layout()
        return fig
