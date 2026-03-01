"""
Test Visualization System

Tests the complete visualization pipeline with sample data.
Verifies all components work together correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.visualization import (
    ReportAnalytics, 
    ChartData,
    ChartGenerator,
    ExportRenderer,
    VisualizationOrchestrator,
    VisualizationBundle,
)


def generate_sample_findings():
    """Generate sample vulnerability findings for testing."""
    return [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "src/config.py",
            "confidence_score": 0.95,
            "message": "Database password hardcoded",
            "line": 42,
        },
        {
            "severity": "High",
            "category": "API Key Exposure",
            "file": "src/auth.py",
            "confidence_score": 0.92,
            "message": "AWS access key exposed",
            "line": 128,
        },
        {
            "severity": "Medium",
            "category": "Debug Logging",
            "file": "src/utils.py",
            "confidence_score": 0.78,
            "message": "Debug mode enabled in production",
            "line": 15,
        },
        {
            "severity": "Medium",
            "category": "Hardcoded Credentials",
            "file": "src/database.py",
            "confidence_score": 0.85,
            "message": "Database user/password hardcoded",
            "line": 56,
        },
        {
            "severity": "Low",
            "category": "Weak Cryptography",
            "file": "src/crypto.py",
            "confidence_score": 0.65,
            "message": "MD5 used instead of SHA256",
            "line": 72,
        },
        {
            "severity": "High",
            "category": "API Key Exposure",
            "file": "src/openai_client.py",
            "confidence_score": 0.98,
            "message": "OpenAI API key in environment",
            "line": 8,
        },
        {
            "severity": "Low",
            "category": "SQL Injection Risk",
            "file": "src/db_query.py",
            "confidence_score": 0.72,
            "message": "Unparameterized query detected",
            "line": 105,
        },
        {
            "severity": "Medium",
            "category": "Hardcoded Credentials",
            "file": "src/api.py",
            "confidence_score": 0.81,
            "message": "API token hardcoded",
            "line": 33,
        },
    ]


def test_data_processor():
    """Test data aggregation."""
    print("\n=== Testing Data Processor ===")
    findings = generate_sample_findings()
    
    analytics = ReportAnalytics(findings)
    chart_data = analytics.get_chart_data()
    
    print(f"✓ Processed {len(findings)} findings")
    print(f"✓ Severity distribution: {chart_data.severity_distribution}")
    print(f"✓ Category distribution: {list(chart_data.category_distribution.keys())[:3]}")
    print(f"✓ Risk score: {chart_data.risk_score:.1f}/100")
    print(f"✓ Risk level: {ReportAnalytics.get_risk_level(chart_data.risk_score)}")
    
    return findings


def test_chart_generator(findings):
    """Test chart generation."""
    print("\n=== Testing Chart Generator ===")
    analytics = ReportAnalytics(findings)
    chart_data = analytics.get_chart_data()
    
    # Test each chart type
    severity_img = ChartGenerator.generate_severity_chart(chart_data.severity_distribution)
    print(f"✓ Severity chart: {severity_img.size} pixels")
    
    category_img = ChartGenerator.generate_category_chart(chart_data.category_distribution)
    print(f"✓ Category chart: {category_img.size} pixels")
    
    file_img = ChartGenerator.generate_file_distribution_chart(chart_data.file_distribution)
    print(f"✓ File distribution chart: {file_img.size} pixels")
    
    confidence_img = ChartGenerator.generate_confidence_chart(chart_data.confidence_distribution)
    print(f"✓ Confidence chart: {confidence_img.size} pixels")
    
    risk_img = ChartGenerator.generate_risk_gauge(chart_data.risk_score)
    print(f"✓ Risk gauge: {risk_img.size} pixels")


def test_export_renderer():
    """Test image export."""
    print("\n=== Testing Export Renderer ===")
    exporter = ExportRenderer(cache_enabled=True)
    
    # Generate test image
    findings = generate_sample_findings()
    analytics = ReportAnalytics(findings)
    chart_data = analytics.get_chart_data()
    test_img = ChartGenerator.generate_severity_chart(chart_data.severity_distribution)
    
    # Export
    export_path = exporter.export_image(
        test_img, "severity", chart_data.severity_distribution, dpi=300
    )
    print(f"✓ Exported image to: {export_path}")
    print(f"✓ File exists: {os.path.exists(export_path)}")
    
    # Check cache
    stats = exporter.get_cache_stats()
    print(f"✓ Cache stats: {stats['files']} files, {stats['size_mb']}MB")


def test_orchestrator():
    """Test complete pipeline."""
    print("\n=== Testing Visualization Orchestrator ===")
    findings = generate_sample_findings()
    
    orchestrator = VisualizationOrchestrator(cache_enabled=True)
    bundle = orchestrator.generate_visualizations(findings, export_dpi=300)
    
    print(f"✓ Generated visualizations in {bundle.generation_time_ms:.0f}ms")
    print(f"✓ Risk score: {bundle.risk_score:.1f}/100 ({bundle.risk_level})")
    
    # Check all images generated
    paths = bundle.get_image_paths()
    generated = sum(1 for p in paths.values() if p)
    print(f"✓ Generated {generated}/5 charts")
    
    # Generate markdown
    markdown = orchestrator.get_markdown_section(bundle, embed=False)
    print(f"✓ Generated markdown: {len(markdown)} characters")
    
    # Check cache
    cache_stats = orchestrator.get_cache_stats()
    print(f"✓ Cache contains {cache_stats['cached_charts']} charts")


def main():
    """Run all tests."""
    print("=" * 50)
    print("VISUALIZATION SYSTEM TEST SUITE")
    print("=" * 50)
    
    try:
        findings = test_data_processor()
        test_chart_generator(findings)
        test_export_renderer()
        test_orchestrator()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
