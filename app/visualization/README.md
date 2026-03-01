# Data Visualization System

Professional security audit visualization module with automatic chart generation, high-resolution export, and caching.

## Overview

The visualization system provides a complete pipeline for generating professional security audit charts from vulnerability findings:

1. **Data Processing** - Aggregate vulnerability findings into analyzable metrics
2. **Chart Generation** - Create 5 professional chart types using matplotlib
3. **Export & Caching** - Export high-resolution images (300 DPI for PDF) with intelligent caching
4. **Integration** - Easy orchestration for report generation workflow

## Architecture

```
ReportAnalytics (data_processor.py)
    ↓
    Aggregates findings → ChartData
    ↓
ChartGenerator (charts.py)
    ↓
    Creates matplotlib figures → PIL Images  
    ↓
ExportRenderer (export_renderer.py)
    ↓
    High-res export + caching → PNG files
    ↓
VisualizationOrchestrator (orchestrator.py)
    ↓
    Coordinates pipeline → VisualizationBundle
```

## Components

### ReportAnalytics (data_processor.py)

Processes vulnerability findings into analyzable metrics.

```python
from app.visualization import ReportAnalytics

findings = [
    {
        "severity": "High",
        "category": "Hardcoded Credentials",
        "file": "src/config.py",
        "confidence_score": 0.95,
    },
    # ... more findings
]

analytics = ReportAnalytics(findings)
chart_data = analytics.get_chart_data()

# Access metrics
print(chart_data.severity_distribution)      # {'High': 3, 'Medium': 2, 'Low': 1}
print(chart_data.risk_score)                  # 65.5
print(ReportAnalytics.get_risk_level(65.5))   # "High"
```

**Key Methods:**
- `get_severity_distribution()` - Count by severity level
- `get_category_distribution()` - Count by vulnerability category
- `get_file_distribution()` - Top 10 files with "Others" aggregation
- `get_confidence_distribution()` - Histogram with 5 confidence ranges
- `calculate_risk_score()` - Overall risk metric (0-100)
- `get_chart_data()` - All metrics in ChartData container

### ChartGenerator (charts.py)

Generates professional matplotlib charts at screen resolution (100 DPI).

```python
from app.visualization import ChartGenerator

# Generate individual charts
severity_img = ChartGenerator.generate_severity_chart(
    chart_data.severity_distribution
)

category_img = ChartGenerator.generate_category_chart(
    chart_data.category_distribution
)

file_img = ChartGenerator.generate_file_distribution_chart(
    chart_data.file_distribution
)

confidence_img = ChartGenerator.generate_confidence_chart(
    chart_data.confidence_distribution
)

risk_gauge = ChartGenerator.generate_risk_gauge(
    chart_data.risk_score
)
```

**Chart Types:**
1. **Severity Chart** - Donut chart showing High/Medium/Low distribution
2. **Category Chart** - Horizontal bar chart of vulnerability categories
3. **File Distribution** - Horizontal bar chart of top 10 files
4. **Confidence Chart** - Histogram of confidence score ranges
5. **Risk Gauge** - Visual meter with risk level indicator

**Customization:**
```python
# Generate at custom DPI
chart = ChartGenerator.generate_severity_chart(severity_dist, dpi=150)

# All charts return PIL Image objects for further processing
image_size = chart.size  # (width, height) in pixels
```

### ExportRenderer (export_renderer.py)

Exports charts to high-resolution PNG images with caching.

```python
from app.visualization import ExportRenderer

exporter = ExportRenderer(cache_enabled=True)

# Export single image
export_path = exporter.export_image(
    pil_image,
    chart_type="severity",
    data=chart_data.severity_distribution,
    dpi=300,  # PDF-quality resolution
    quality=95
)

# Generate markdown
markdown = ExportRenderer.export_to_markdown(
    image_path,
    alt_text="Severity distribution chart",
    embed=False  # Set True for base64 embedding
)

# Manage cache
stats = exporter.get_cache_stats()
print(f"Cache: {stats['files']} files, {stats['size_mb']}MB")

exporter.clear_cache()  # Clear all cached charts
```

**Features:**
- Automatic image scaling for different DPI resolutions
- Caching with MD5 hash-based keys  
- Cache persistence using JSON index
- High-quality PNG export at 300 DPI for PDF embedding
- Markdown integration with optional base64 embedding

### VisualizationOrchestrator (orchestrator.py)

Coordinates the complete visualization pipeline.

```python
from app.visualization import VisualizationOrchestrator

# Create orchestrator
orchestrator = VisualizationOrchestrator(cache_enabled=True)

# Generate all visualizations from findings
bundle = orchestrator.generate_visualizations(
    findings,
    export_dpi=300  # Export resolution
)

# Access results
print(f"Risk Score: {bundle.risk_score:.1f}/100 ({bundle.risk_level})")
print(f"Generated in {bundle.generation_time_ms:.0f}ms")

# Get all exported paths
paths = bundle.get_image_paths()

# Generate markdown with charts
markdown = orchestrator.get_markdown_section(bundle, embed=False)

# Cache management
stats = orchestrator.get_cache_stats()
orchestrator.clear_cache()
```

## Integration Example

### Basic Integration with Report Generator

```python
from app.visualization import VisualizationOrchestrator
from app.report_generator import ReportGenerator

# Generate visualizations
orchestrator = VisualizationOrchestrator()
bundle = orchestrator.generate_visualizations(findings)

# Add to report
report = ReportGenerator()
report.add_section("Visualizations", 
    orchestrator.get_markdown_section(bundle))

# Export
report.export_pdf(
    output_path="audit_report.pdf",
    include_images=True
)
```

### Real-time Visualization During Scan

```python
class SecurityScanner:
    def __init__(self):
        self.orchestrator = VisualizationOrchestrator(cache_enabled=True)
        self.visualizations = None
    
    def on_scan_complete(self, findings):
        """Generate visualizations after scan completes."""
        # Generate charts
        self.visualizations = self.orchestrator.generate_visualizations(findings)
        
        # Update UI with risk score
        self.ui.update_risk_score(
            self.visualizations.risk_score,
            self.visualizations.risk_level
        )
        
        # Display charts
        self.ui.show_charts(self.visualizations)
    
    def on_severity_override(self, finding, new_severity):
        """Regenerate charts after finding severity changes."""
        # Update finding
        self.findings[finding_id]["severity"] = new_severity
        
        # Regenerate visualizations
        self.visualizations = self.orchestrator.generate_visualizations(
            self.findings
        )
        
        # Update UI
        self.ui.update_visualizations(self.visualizations)
```

## Risk Score Calculation

The risk score represents overall vulnerability severity on a 0-100 scale:

```
Risk Score = (High × 3 + Medium × 2 + Low × 1) / (Total Findings × 3) × 100
```

**Risk Levels:**
- **Critical** (≥80): Immediate action required
- **High** (≥60): Urgent remediation needed
- **Medium** (≥40): Plan remediation
- **Low** (≥20): Monitor and plan
- **Minimal** (<20): Acceptable risk

## Performance Considerations

### Caching Strategy

- Charts are cached based on MD5 hash of data
- Cache stored in system temp directory
- Identical data = instant retrieval (no regeneration)
- Automatic cache invalidation when data changes

### Memory Usage

- Each chart is ~500KB in cache (300 DPI PNG)
- Typical report: 5 charts × 500KB = 2.5MB
- Cache directory auto-managed (no size limits)

### Generation Time

- 8 findings → 5 charts: ~800ms
- Cached retrieval: <50ms
- Scales linearly with finding count
- No blocking operations (can add threading in future)

## Export Formats

### PDF Export (300 DPI)

```python
# Automatic scaling to 300 DPI
export_path = exporter.export_image(image, "chart", data, dpi=300)

# Embed in PDF report
from reportlab.platypus import Image as RLImage
report_image = RLImage(export_path, width=6*inch, height=4*inch)
```

### Markdown Export

```python
# File reference
markdown = ExportRenderer.export_to_markdown(
    image_path="charts/severity.png",
    alt_text="Severity distribution"
)
# Output: ![Severity distribution](charts/severity.png)

# Base64 embedding (no external files)
markdown = ExportRenderer.export_to_markdown(
    image_path="severity.png",
    embed=True
)
# Output: ![...](data:image/png;base64,iVBORw0KGgo...)
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_visualization.py
```

Tests cover:
- Data aggregation accuracy
- Chart generation quality validation
- Export functionality
- Cache performance
- End-to-end orchestration
- Risk score calculations
- Risk level classification

## Dependencies

- **matplotlib** - Chart rendering
- **Pillow (PIL)** - Image manipulation
- **numpy** - Numerical computations
- **Python 3.10+**

All dependencies are offline-capable with no external API calls.

## Troubleshooting

### Charts not rendering
- Verify matplotlib backend: `matplotlib.use('Agg')` for headless environments
- Check memory availability (large datasets need >512MB)
- Validate finding data structure (required fields: severity, category, file)

### Export failed
- Ensure temp directory is writable (checking /tmp or %TEMP%)
- Verify disk space available
- Check file permissions

### Cache issues
- Clear cache: `orchestrator.clear_cache()`
- Cache location: `exporter.CACHE_DIR`
- Cache index: `cache_dir/cache_index.json`

## Future Enhancements

- [ ] Threading for large dataset generation
- [ ] Custom color schemes
- [ ] Interactive HTML charts (Plotly)
- [ ] Real-time streaming updates
- [ ] Multi-report correlations
- [ ] Trend analysis (historical comparison)
