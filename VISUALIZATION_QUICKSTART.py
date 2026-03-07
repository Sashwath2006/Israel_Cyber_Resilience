#!/usr/bin/env python3
"""
Quick Start Guide for Data Visualization System

Run this script for examples of all visualization capabilities.
"""

def example_basic_usage():
    """Example 1: Basic chart generation."""
    from app.visualization import VisualizationOrchestrator
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
        {
            "severity": "Medium",
            "category": "Debug Logging",
            "file": "utils.py",
            "confidence_score": 0.78,
        },
    ]
    
    # One line to generate all charts
    orchestrator = VisualizationOrchestrator()
    bundle = orchestrator.generate_visualizations(findings)
    
    print(f"Risk Score: {bundle.risk_score:.1f}/100 ({bundle.risk_level})")


def example_data_analysis():
    """Example 2: Analyze findings without generating charts."""
    from app.visualization import ReportAnalytics
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    analytics = ReportAnalytics(findings)
    
    # Access any metric
    risk_score = analytics.calculate_risk_score()
    severity_dist = analytics.get_severity_distribution()
    categories = analytics.get_category_distribution()
    files = analytics.get_file_distribution()
    confidence = analytics.get_confidence_distribution()


def example_custom_charts():
    """Example 3: Generate specific charts only."""
    from app.visualization import ChartGenerator, ReportAnalytics
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    analytics = ReportAnalytics(findings)
    data = analytics.get_chart_data()
    
    # Generate only what you need
    severity_chart = ChartGenerator.generate_severity_chart(data.severity_distribution)
    category_chart = ChartGenerator.generate_category_chart(data.category_distribution)
    
    # Charts are PIL Images - process as needed
    severity_chart.save("severity.png")
    category_chart.show()


def example_export_control():
    """Example 4: Control export resolution and format."""
    from app.visualization import ExportRenderer, ChartGenerator, ReportAnalytics
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    analytics = ReportAnalytics(findings)
    chart_data = analytics.get_chart_data()
    image = ChartGenerator.generate_severity_chart(chart_data.severity_distribution)
    
    exporter = ExportRenderer(cache_enabled=True)
    
    # Export at different resolutions
    screen_path = exporter.export_image(image, "chart", chart_data.severity_distribution, dpi=100)
    print_path = exporter.export_image(image, "chart", chart_data.severity_distribution, dpi=300)
    hires_path = exporter.export_image(image, "chart", chart_data.severity_distribution, dpi=600)
    
    # Cache management
    stats = exporter.get_cache_stats()
    exporter.clear_cache()


def example_markdown_integration():
    """Example 5: Generate markdown with embedded charts."""
    from app.visualization import VisualizationOrchestrator
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    orchestrator = VisualizationOrchestrator()
    bundle = orchestrator.generate_visualizations(findings)
    
    # Generate markdown with file references (smaller file size)
    markdown = orchestrator.get_markdown_section(bundle, embed=False)
    
    # Or embed as base64 (no external files needed)
    markdown = orchestrator.get_markdown_section(bundle, embed=True)
    
    with open("report.md", "w") as f:
        f.write(markdown)


def example_report_generation():
    """Example 6: Complete audit report generation."""
    from app.visualization.integration_example import SecurityAuditReport
    
    findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
        {
            "severity": "Medium",
            "category": "Debug Logging",
            "file": "debug.py",
            "confidence_score": 0.78,
        },
    ]
    
    # Create report
    report = SecurityAuditReport(output_dir="./reports")
    
    # Add findings
    report.add_findings(findings)
    
    # Generate visualizations
    report.generate_visualizations()
    
    # Export formats
    report.export_markdown("audit_report.md")
    report.export_pdf("audit_report.pdf")
    
    # Get statistics
    stats = report.get_statistics()
    print(f"Risk Level: {stats['risk_level']}")
    print(f"Risk Score: {stats['risk_score']:.1f}/100")


def example_real_time_updates():
    """Example 7: Real-time visualization updates."""
    from app.visualization import VisualizationOrchestrator
    
    initial_findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    modified_findings = [
        {
            "severity": "Medium",  # Changed from High
            "category": "Hardcoded Credentials",
            "file": "config.py",
            "confidence_score": 0.95,
        },
    ]
    
    orchestrator = VisualizationOrchestrator()
    
    # Initial report generation
    bundle = orchestrator.generate_visualizations(initial_findings)
    
    # Later, user modifies finding's severity
    # Regenerate with updated data (uses cache efficiently)
    updated_bundle = orchestrator.generate_visualizations(modified_findings)
    
    # Only changed metrics trigger re-renders
    # Identical data pulled from cache in <50ms


def example_batch_processing():
    """Example 8: Generate reports for multiple audits."""
    from app.visualization.integration_example import SecurityAuditReport
    
    audit_results = [
        ("client_a", [
            {
                "severity": "High",
                "category": "Hardcoded Credentials",
                "file": "config.py",
                "confidence_score": 0.95,
            },
        ]),
        ("client_b", [
            {
                "severity": "Medium",
                "category": "Debug Logging",
                "file": "debug.py",
                "confidence_score": 0.78,
            },
        ]),
        ("client_c", [
            {
                "severity": "Low",
                "category": "Weak Cryptography",
                "file": "crypto.py",
                "confidence_score": 0.65,
            },
        ]),
    ]
    
    for client_name, findings in audit_results:
        report = SecurityAuditReport(output_dir=f"./reports/{client_name}")
        report.add_findings(findings)
        report.generate_visualizations()
        report.export_markdown(f"{client_name}_report.md")
        report.export_pdf(f"{client_name}_report.pdf")
        report.clear_cache()


# Chart Types Available
CHART_TYPES = {
    "Severity Distribution": {
        "type": "Donut Chart",
        "shows": "Count of High/Medium/Low findings",
        "example": "High (40%), Medium (45%), Low (15%)",
    },
    "Vulnerability Categories": {
        "type": "Horizontal Bar Chart",
        "shows": "Top vulnerability types",
        "example": "Hardcoded Credentials (12), SQL Injection (8), ...",
    },
    "Findings per File": {
        "type": "Horizontal Bar Chart",
        "shows": "Top 10 files with most findings",
        "example": "config.py (8), auth.py (6), utils.py (4), ...",
    },
    "Confidence Score Distribution": {
        "type": "Histogram",
        "shows": "Detection confidence ranges",
        "example": "0.0-0.2 (2 findings), 0.2-0.4 (3), ..., 0.8-1.0 (5)",
    },
    "Risk Assessment": {
        "type": "Gauge/Meter",
        "shows": "Overall risk score color-coded by level",
        "example": "73.3/100 (HIGH RISK) - Red gauge",
    },
}

# Required Finding Structure
FINDING_STRUCTURE = {
    "severity": "str (High/Medium/Low)",
    "category": "str (vulnerability type)",
    "file": "str (source file path)",
    "confidence_score": "float (0.0-1.0)",
    "message": "str (description)",
    "line": "int (optional)",
}

# Risk Score Calculation
RISK_SCORE_FORMULA = """
Risk Score = (High × 3 + Medium × 2 + Low × 1) / (Total × 3) × 100

Risk Levels:
- Critical (≥80): Immediate action required
- High (≥60): Urgent remediation needed
- Medium (≥40): Plan remediation
- Low (≥20): Monitor and plan
- Minimal (<20): Acceptable risk
"""

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         DATA VISUALIZATION SYSTEM - QUICK START GUIDE           ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Available Examples:
    1. Basic Usage           - One-line chart generation
    2. Data Analysis         - Extract metrics without charts
    3. Custom Charts         - Generate specific chart types
    4. Export Control        - Fine-tune DPI and formats
    5. Markdown Integration  - Embed charts in reports
    6. Report Generation     - Complete audit report workflow
    7. Real-time Updates     - Update visualizations dynamically
    8. Batch Processing      - Generate multiple reports
    
    For detailed documentation, see:
    - app/visualization/README.md
    - app/visualization/integration_example.py
    
    To run tests:
    - python tests/test_visualization.py
    
    To generate example report:
    - python app/visualization/integration_example.py
    
    Key Classes:
    - ReportAnalytics        - Aggregates metrics
    - ChartGenerator         - Creates visualizations
    - ExportRenderer         - High-res export + caching
    - VisualizationOrchestrator - Coordinates pipeline
    """)
    
    print("\nChart Types:")
    for chart_name, details in CHART_TYPES.items():
        print(f"\n  {chart_name}")
        print(f"    Type: {details['type']}")
        print(f"    Shows: {details['shows']}")
        print(f"    Example: {details['example']}")
    
    print(f"\n\nRequired Finding Structure:")
    for field, type_info in FINDING_STRUCTURE.items():
        print(f"  {field}: {type_info}")
    
    print(f"\n{RISK_SCORE_FORMULA}")
