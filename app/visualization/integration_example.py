"""
Visualization Integration Example

Demonstrates how to integrate the visualization system into a security audit workflow.
This example shows a complete flow from findings to report generation with visualizations.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from app.visualization import VisualizationOrchestrator


class SecurityAuditReport:
    """Example report generator with visualization integration."""
    
    def __init__(self, output_dir: str = "./reports"):
        """Initialize report generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.orchestrator = VisualizationOrchestrator(cache_enabled=True)
        self.findings: List[Dict[str, Any]] = []
        self.visualizations = None
    
    def load_findings(self, findings_file: str) -> None:
        """Load findings from JSON file."""
        with open(findings_file, "r") as f:
            self.findings = json.load(f)
        
        print(f"Loaded {len(self.findings)} findings")
    
    def add_findings(self, findings: List[Dict[str, Any]]) -> None:
        """Add findings programmatically."""
        self.findings.extend(findings)
        print(f"Now have {len(self.findings)} total findings")
    
    def generate_visualizations(self) -> None:
        """Generate all visualizations from current findings."""
        print(f"\nGenerating visualizations for {len(self.findings)} findings...")
        
        self.visualizations = self.orchestrator.generate_visualizations(
            self.findings,
            export_dpi=300
        )
        
        print(f"✓ Visualizations generated in {self.visualizations.generation_time_ms:.0f}ms")
        print(f"✓ Risk Score: {self.visualizations.risk_score:.1f}/100 ({self.visualizations.risk_level})")
    
    def build_markdown_report(self) -> str:
        """Build complete markdown report with visualizations."""
        content = """# Security Audit Report

## Executive Summary

"""
        # Add risk overview
        if self.visualizations:
            content += f"**Overall Risk Level:** {self.visualizations.risk_level}\n"
            content += f"**Risk Score:** {self.visualizations.risk_score:.1f}/100\n"
            content += f"**Total Findings:** {len(self.findings)}\n\n"
        
        # Add visualizations section
        if self.visualizations:
            content += self.orchestrator.get_markdown_section(
                self.visualizations,
                embed=False  # Use file references for smaller file size
            )
        
        # Add detailed findings
        content += "\n## Detailed Findings\n\n"
        
        # Group by severity
        for severity in ["High", "Medium", "Low"]:
            severity_findings = [
                f for f in self.findings 
                if f.get("severity") == severity
            ]
            
            if severity_findings:
                content += f"\n### {severity} Severity ({len(severity_findings)})\n\n"
                
                for i, finding in enumerate(severity_findings, 1):
                    content += f"#### {i}. {finding.get('category', 'Unknown')}\n\n"
                    content += f"**File:** `{finding.get('file', 'N/A')}`\n\n"
                    content += f"**Description:** {finding.get('message', 'N/A')}\n\n"
                    content += f"**Confidence:** {finding.get('confidence_score', 0):.1%}\n\n"
                    content += "---\n\n"
        
        return content
    
    def export_markdown(self, filename: str = "audit_report.md") -> str:
        """Export report to markdown file."""
        report_path = self.output_dir / filename
        
        with open(report_path, "w") as f:
            f.write(self.build_markdown_report())
        
        print(f"✓ Report exported to: {report_path}")
        return str(report_path)
    
    def export_pdf(self, filename: str = "audit_report.pdf") -> None:
        """Export report to PDF with embedded charts."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            print("reportlab not installed. Install with: pip install reportlab")
            return
        
        pdf_path = self.output_dir / filename
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=styles['Heading1'].textColor,
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Security Audit Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive summary
        if self.visualizations:
            summary = f"""
            <b>Risk Level:</b> {self.visualizations.risk_level}<br/>
            <b>Risk Score:</b> {self.visualizations.risk_score:.1f}/100<br/>
            <b>Total Findings:</b> {len(self.findings)}
            """
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Add visualization images
            story.append(PageBreak())
            story.append(Paragraph("Visualizations", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            paths = self.visualizations.get_image_paths()
            image_labels = {
                "severity": "Severity Distribution",
                "category": "Vulnerability Categories",
                "file_distribution": "Findings by File",
                "confidence": "Confidence Scores",
                "risk_gauge": "Risk Assessment",
            }
            
            for key, label in image_labels.items():
                path = paths.get(key)
                if path and Path(path).exists():
                    story.append(Paragraph(label, styles['Heading3']))
                    story.append(Spacer(1, 0.1*inch))
                    
                    try:
                        img = RLImage(path, width=5*inch, height=3.75*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.2*inch))
                    except Exception as e:
                        print(f"Warning: Could not embed image {path}: {e}")
        
        # Build PDF
        try:
            doc.build(story)
            print(f"✓ PDF exported to: {pdf_path}")
        except Exception as e:
            print(f"✗ PDF export failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about current findings and visualizations."""
        if not self.visualizations:
            return {"findings": len(self.findings)}
        
        return {
            "total_findings": len(self.findings),
            "risk_score": self.visualizations.risk_score,
            "risk_level": self.visualizations.risk_level,
            "high_count": self.visualizations.severity_image is not None,
            "severity_distribution": self._get_severity_dist(),
            "generation_time_ms": self.visualizations.generation_time_ms,
        }
    
    def _get_severity_dist(self) -> Dict[str, int]:
        """Get severity distribution from findings."""
        dist = {"High": 0, "Medium": 0, "Low": 0}
        for finding in self.findings:
            severity = finding.get("severity", "Low")
            if severity in dist:
                dist[severity] += 1
        return dist
    
    def clear_cache(self) -> None:
        """Clear visualization cache."""
        self.orchestrator.clear_cache()
        print("✓ Visualization cache cleared")


# Example usage
def main():
    """Run example audit report generation."""
    
    print("=" * 60)
    print("SECURITY AUDIT REPORT GENERATION EXAMPLE")
    print("=" * 60)
    
    # Create report generator
    report = SecurityAuditReport(output_dir="./sample_reports")
    
    # Example findings
    sample_findings = [
        {
            "severity": "High",
            "category": "Hardcoded Credentials",
            "file": "src/config.py",
            "confidence_score": 0.95,
            "message": "Database password hardcoded in configuration file",
            "line": 42,
        },
        {
            "severity": "High",
            "category": "API Key Exposure",
            "file": "src/auth.py",
            "confidence_score": 0.92,
            "message": "AWS access key exposed in source code",
            "line": 128,
        },
        {
            "severity": "Medium",
            "category": "Debug Logging",
            "file": "src/utils.py",
            "confidence_score": 0.78,
            "message": "Debug mode enabled in production environment",
            "line": 15,
        },
        {
            "severity": "Medium",
            "category": "Hardcoded Credentials",
            "file": "src/database.py",
            "confidence_score": 0.85,
            "message": "Database credentials hardcoded",
            "line": 56,
        },
        {
            "severity": "Low",
            "category": "Weak Cryptography",
            "file": "src/crypto.py",
            "confidence_score": 0.65,
            "message": "MD5 hash used instead of SHA256",
            "line": 72,
        },
    ]
    
    # Add findings
    report.add_findings(sample_findings)
    
    # Generate visualizations
    report.generate_visualizations()
    
    # Export reports
    print("\nExporting reports...")
    report.export_markdown("sample_audit_report.md")
    report.export_pdf("sample_audit_report.pdf")
    
    # Show statistics
    print("\nReport Statistics:")
    stats = report.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✓ REPORT GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
