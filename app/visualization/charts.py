"""
Chart Generation Using Matplotlib

Creates professional security audit charts for visualization and export.
All charts are generated offline with no external dependencies.
"""

import io
from typing import Dict, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from PIL import Image

# Security theme colors
SEVERITY_COLORS = {
    "High": "#d32f2f",      # Red
    "Medium": "#f57c00",    # Orange
    "Low": "#fbc02d",       # Yellow
}

CHART_THEME = {
    "bg_color": "#fafafa",
    "text_color": "#333333",
    "grid_color": "#e0e0e0",
    "accent_color": "#0084ff",
}


class ChartGenerator:
    """Generates matplotlib charts for vulnerability analysis."""
    
    DPI = 100  # Standard screen DPI
    EXPORT_DPI = 300  # High resolution for PDF export
    
    @staticmethod
    def generate_severity_chart(severity_dist: Dict[str, int], dpi: int = 100) -> Image.Image:
        """
        Generate pie/donut chart for severity distribution.
        
        Args:
            severity_dist: Dict with "High", "Medium", "Low" counts
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        fig, ax = plt.subplots(figsize=(8, 6), dpi=dpi)
        fig.patch.set_facecolor(CHART_THEME["bg_color"])
        
        # Prepare data
        labels = list(severity_dist.keys())
        sizes = list(severity_dist.values())
        colors = [SEVERITY_COLORS.get(label, "#999999") for label in labels]
        
        # Handle zero findings
        if sum(sizes) == 0:
            ax.text(0.5, 0.5, "No findings", ha="center", va="center", 
                   fontsize=14, color=CHART_THEME["text_color"])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return ChartGenerator._fig_to_image(fig, dpi)
        
        # Create donut chart
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct="%1.1f%%",
            startangle=90, textprops={"fontsize": 11, "color": CHART_THEME["text_color"]},
            pctdistance=0.85,
        )
        
        # Make percentage text white/bold
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
        
        # Draw circle for donut
        centre_circle = plt.Circle((0, 0), 0.70, fc=CHART_THEME["bg_color"])
        ax.add_artist(centre_circle)
        
        ax.set_title("Severity Distribution", fontsize=14, fontweight="bold",
                    color=CHART_THEME["text_color"], pad=20)
        
        return ChartGenerator._fig_to_image(fig, dpi)
    
    @staticmethod
    def generate_category_chart(category_dist: Dict[str, int], dpi: int = 100) -> Image.Image:
        """
        Generate bar chart for vulnerability categories.
        
        Args:
            category_dist: Dict with category names as keys, counts as values
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
        fig.patch.set_facecolor(CHART_THEME["bg_color"])
        
        if not category_dist or sum(category_dist.values()) == 0:
            ax.text(0.5, 0.5, "No findings", ha="center", va="center",
                   fontsize=14, color=CHART_THEME["text_color"])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return ChartGenerator._fig_to_image(fig, dpi)
        
        # Prepare data (limit to top 10)
        categories = list(category_dist.keys())[:10]
        counts = [category_dist[c] for c in categories]
        
        # Create bar chart
        bars = ax.barh(categories, counts, color=CHART_THEME["accent_color"], edgecolor="white", linewidth=1.5)
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.1, bar.get_y() + bar.get_height() / 2, str(count),
                   ha="left", va="center", fontsize=10, color=CHART_THEME["text_color"])
        
        ax.set_xlabel("Count", fontsize=11, color=CHART_THEME["text_color"])
        ax.set_title("Vulnerability Categories", fontsize=14, fontweight="bold",
                    color=CHART_THEME["text_color"], pad=20)
        ax.grid(axis="x", color=CHART_THEME["grid_color"], linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)
        
        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(CHART_THEME["grid_color"])
        ax.spines["bottom"].set_color(CHART_THEME["grid_color"])
        ax.tick_params(colors=CHART_THEME["text_color"])
        
        fig.tight_layout()
        return ChartGenerator._fig_to_image(fig, dpi)
    
    @staticmethod
    def generate_file_distribution_chart(file_dist: Dict[str, int], dpi: int = 100) -> Image.Image:
        """
        Generate horizontal bar chart for findings per file.
        
        Args:
            file_dist: Dict with filenames as keys, finding counts as values
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
        fig.patch.set_facecolor(CHART_THEME["bg_color"])
        
        if not file_dist or sum(file_dist.values()) == 0:
            ax.text(0.5, 0.5, "No findings", ha="center", va="center",
                   fontsize=14, color=CHART_THEME["text_color"])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return ChartGenerator._fig_to_image(fig, dpi)
        
        # Prepare data (limit to top 10)
        files = list(file_dist.keys())[:10]
        counts = [file_dist[f] for f in files]
        
        # Create bar chart
        bars = ax.barh(files, counts, color="#ff6f00", edgecolor="white", linewidth=1.5)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            ax.text(count + 0.1, bar.get_y() + bar.get_height() / 2, str(count),
                   ha="left", va="center", fontsize=10, color=CHART_THEME["text_color"])
        
        ax.set_xlabel("Finding Count", fontsize=11, color=CHART_THEME["text_color"])
        ax.set_title("Findings per File", fontsize=14, fontweight="bold",
                    color=CHART_THEME["text_color"], pad=20)
        ax.grid(axis="x", color=CHART_THEME["grid_color"], linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)
        
        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(CHART_THEME["grid_color"])
        ax.spines["bottom"].set_color(CHART_THEME["grid_color"])
        ax.tick_params(colors=CHART_THEME["text_color"])
        
        fig.tight_layout()
        return ChartGenerator._fig_to_image(fig, dpi)
    
    @staticmethod
    def generate_confidence_chart(confidence_dist: Dict[str, int], dpi: int = 100) -> Image.Image:
        """
        Generate bar chart for confidence score distribution.
        
        Args:
            confidence_dist: Dict with confidence ranges as keys, counts as values
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=dpi)
        fig.patch.set_facecolor(CHART_THEME["bg_color"])
        
        if not confidence_dist or sum(confidence_dist.values()) == 0:
            ax.text(0.5, 0.5, "No findings", ha="center", va="center",
                   fontsize=14, color=CHART_THEME["text_color"])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return ChartGenerator._fig_to_image(fig, dpi)
        
        # Prepare data
        confidence_ranges = list(confidence_dist.keys())
        counts = list(confidence_dist.values())
        
        # Create bar chart
        bars = ax.bar(confidence_ranges, counts, color="#4caf50", edgecolor="white", linewidth=1.5)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, str(int(count)),
                       ha="center", va="bottom", fontsize=10, color=CHART_THEME["text_color"])
        
        ax.set_ylabel("Count", fontsize=11, color=CHART_THEME["text_color"])
        ax.set_xlabel("Confidence Score", fontsize=11, color=CHART_THEME["text_color"])
        ax.set_title("Confidence Score Distribution", fontsize=14, fontweight="bold",
                    color=CHART_THEME["text_color"], pad=20)
        ax.grid(axis="y", color=CHART_THEME["grid_color"], linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)
        
        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(CHART_THEME["grid_color"])
        ax.spines["bottom"].set_color(CHART_THEME["grid_color"])
        ax.tick_params(colors=CHART_THEME["text_color"])
        
        fig.tight_layout()
        return ChartGenerator._fig_to_image(fig, dpi)
    
    @staticmethod
    def generate_risk_gauge(risk_score: float, dpi: int = 100) -> Image.Image:
        """
        Generate a simple risk meter/gauge visualization.
        
        Args:
            risk_score: Risk score from 0-100
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        fig, ax = plt.subplots(figsize=(8, 4), dpi=dpi)
        fig.patch.set_facecolor(CHART_THEME["bg_color"])
        
        # Determine color based on score
        if risk_score >= 80:
            color = "#d32f2f"  # Red
            label = "CRITICAL"
        elif risk_score >= 60:
            color = "#f57c00"  # Orange
            label = "HIGH"
        elif risk_score >= 40:
            color = "#fbc02d"  # Yellow
            label = "MEDIUM"
        elif risk_score >= 20:
            color = "#7cb342"  # Green
            label = "LOW"
        else:
            color = "#388e3c"  # Dark Green
            label = "MINIMAL"
        
        # Create horizontal bar (gauge)
        bar_width = risk_score / 100
        ax.barh([0], [bar_width], color=color, height=0.5, left=0)
        ax.barh([0], [1 - bar_width], left=bar_width, color=CHART_THEME["grid_color"], height=0.5)
        
        # Add text
        ax.text(0.5, 0, f"{risk_score:.1f}", ha="center", va="center",
               fontsize=28, fontweight="bold", color="white")
        
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.axis("off")
        
        # Add title and label
        ax.text(0.5, 0.35, "Risk Score", ha="center", fontsize=12,
               color=CHART_THEME["text_color"], fontweight="bold")
        ax.text(0.5, -0.35, label, ha="center", fontsize=12,
               color=CHART_THEME["text_color"], fontweight="bold")
        
        return ChartGenerator._fig_to_image(fig, dpi)
    
    @staticmethod
    def _fig_to_image(fig: Figure, dpi: int) -> Image.Image:
        """
        Convert matplotlib figure to PIL Image.
        
        Args:
            fig: Matplotlib figure
            dpi: DPI for rendering
            
        Returns:
            PIL Image object
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight", 
                   facecolor=CHART_THEME["bg_color"], edgecolor="none")
        buffer.seek(0)
        image = Image.open(buffer)
        image.load()
        plt.close(fig)
        return image
