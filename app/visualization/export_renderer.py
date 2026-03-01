"""
Chart Export and Rendering Module

Handles high-resolution image export for PDF embedding and markdown.
Manages temporary files and implements caching for performance.
"""

import os
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image
import json
import logging

logger = logging.getLogger(__name__)


class ExportRenderer:
    """Manages chart export to high-resolution images."""
    
    # Cache directory for generated charts
    CACHE_DIR = None  # Will use system temp dir
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the export renderer.
        
        Args:
            cache_enabled: Whether to cache generated charts
        """
        self.cache_enabled = cache_enabled
        self.cache_index: Dict[str, str] = {}
        
        if cache_enabled:
            self._init_cache()
    
    def _init_cache(self):
        """Initialize cache directory and index."""
        if self.CACHE_DIR is None:
            self.CACHE_DIR = os.path.join(tempfile.gettempdir(), "security_audit_charts")
        
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        
        # Load cache index if exists
        index_file = os.path.join(self.CACHE_DIR, "cache_index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, "r") as f:
                    self.cache_index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.cache_index = {}
        else:
            self.cache_index = {}
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        if not self.cache_enabled or not self.CACHE_DIR:
            return
        
        index_file = os.path.join(self.CACHE_DIR, "cache_index.json")
        try:
            with open(index_file, "w") as f:
                json.dump(self.cache_index, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    def _get_cache_key(self, chart_type: str, data: Dict) -> str:
        """
        Generate cache key from chart type and data.
        
        Args:
            chart_type: Type of chart (severity, category, etc.)
            data: Data dictionary for the chart
            
        Returns:
            Cache key string
        """
        # Create deterministic hash of data
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{chart_type}_{data_hash}"
    
    def _get_cached_path(self, cache_key: str, dpi: int = 300) -> Optional[str]:
        """
        Get cached image path if exists.
        
        Args:
            cache_key: Cache key for the chart
            dpi: Resolution requirement
            
        Returns:
            Path to cached image or None
        """
        if not self.cache_enabled or cache_key not in self.cache_index:
            return None
        
        cached_path = self.cache_index[cache_key]
        
        # Verify file still exists and has correct DPI
        if os.path.exists(cached_path):
            try:
                # Store DPI in filename for verification
                if f"_{dpi}dpi" in cached_path:
                    return cached_path
            except Exception:
                pass
        
        # Cache miss - remove from index
        del self.cache_index[cache_key]
        self._save_cache_index()
        return None
    
    def export_image(self, image: Image.Image, chart_type: str, data: Dict, 
                    dpi: int = 300, quality: int = 95) -> str:
        """
        Export PIL image to high-resolution PNG file.
        
        Args:
            image: PIL Image object
            chart_type: Type of chart for cache key
            data: Original chart data
            dpi: Dots per inch (300 for PDF quality)
            quality: JPEG quality (1-100)
            
        Returns:
            Path to exported image file
        """
        # Check cache first
        cache_key = self._get_cache_key(chart_type, data)
        cached_path = self._get_cached_path(cache_key, dpi) if self.cache_enabled else None
        
        if cached_path:
            logger.debug(f"Using cached chart: {chart_type}")
            return cached_path
        
        # Generate new image
        if not self.CACHE_DIR:
            self._init_cache()
        
        if not self.CACHE_DIR:
            raise RuntimeError("Failed to initialize cache directory")
        
        filename = f"{chart_type}_{cache_key}_{dpi}dpi.png"
        output_path = os.path.join(self.CACHE_DIR, filename)
        
        # Scale image to target DPI if needed
        current_dpi = 100  # Charts are generated at 100 DPI
        if dpi != current_dpi:
            scale_factor = dpi / current_dpi
            new_size = (
                int(image.width * scale_factor),
                int(image.height * scale_factor)
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save high-quality PNG
        try:
            image.save(output_path, "PNG", quality=quality, optimize=False)
            logger.info(f"Exported chart to: {output_path}")
            
            # Update cache
            if self.cache_enabled:
                self.cache_index[cache_key] = output_path
                self._save_cache_index()
            
            return output_path
        
        except IOError as e:
            logger.error(f"Failed to export image: {e}")
            raise
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache info (entries, size, location)
        """
        if not self.cache_enabled or not self.CACHE_DIR:
            return {"enabled": False}
        
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(self.CACHE_DIR):
            if filename.endswith(".png"):
                filepath = os.path.join(self.CACHE_DIR, filename)
                try:
                    total_size += os.path.getsize(filepath)
                    file_count += 1
                except OSError:
                    pass
        
        return {
            "enabled": True,
            "location": self.CACHE_DIR,
            "files": file_count,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "cached_charts": len(self.cache_index),
        }
    
    def clear_cache(self):
        """Clear all cached charts."""
        if not self.cache_enabled or not self.CACHE_DIR:
            return
        
        try:
            for filename in os.listdir(self.CACHE_DIR):
                if filename.endswith(".png"):
                    filepath = os.path.join(self.CACHE_DIR, filename)
                    os.remove(filepath)
            
            self.cache_index.clear()
            self._save_cache_index()
            logger.info("Chart cache cleared")
        
        except OSError as e:
            logger.error(f"Failed to clear cache: {e}")
    
    @staticmethod
    def export_to_pdf_format(image: Image.Image, dpi: int = 300) -> bytes:
        """
        Convert image to PDF-ready bytes (PNG format at high DPI).
        
        Args:
            image: PIL Image object
            dpi: Target DPI for PDF
            
        Returns:
            PNG image bytes suitable for PDF embedding
        """
        import io
        
        # Scale for DPI
        current_dpi = 100
        if dpi != current_dpi:
            scale_factor = dpi / current_dpi
            new_size = (
                int(image.width * scale_factor),
                int(image.height * scale_factor)
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", quality=95, optimize=False)
        return buffer.getvalue()
    
    @staticmethod
    def export_to_markdown(image_path: str, alt_text: str = "", 
                          embed: bool = False) -> str:
        """
        Generate markdown image reference.
        
        Args:
            image_path: Path to image file (absolute or relative)
            alt_text: Alt text for markdown
            embed: Whether to embed image (base64) or reference
            
        Returns:
            Markdown image syntax
        """
        if embed:
            # Base64 encode for embedding
            try:
                from PIL import Image as PILImage
                import base64
                
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                b64_string = base64.b64encode(image_data).decode()
                return f'![{alt_text}](data:image/png;base64,{b64_string})\n'
            
            except Exception as e:
                logger.warning(f"Failed to embed image, using reference: {e}")
                # Fall back to reference
        
        # Use relative path reference
        rel_path = image_path.replace("\\", "/")
        return f'![{alt_text}]({rel_path})\n'
