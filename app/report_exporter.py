"""
Report Export (Phase 12)

Exports reports to Markdown and PDF formats.
Supports structured report export with all findings and evidence.

All exports require explicit user action - no auto-export.
"""

import json
from typing import Optional
from pathlib import Path


def export_to_markdown(
    report_data: dict,
    report_workspace,
    output_path: str,
) -> tuple[bool, str]:
    """
    Export report to Markdown format.
    
    Args:
        report_data: Report data structure from report_generator
        report_workspace: ReportWorkspace instance
        output_path: Path to save Markdown file
    
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        lines = []
        
        # Check if this is a draft report
        is_draft = report_data.get("is_draft", False)
        draft_label = report_data.get("draft_label", "Sample Report - Draft")
        
        # Title
        title = "# Security Assessment Report"
        if is_draft:
            title = f"# {draft_label}\n\n# Security Assessment Report"
        lines.append(title)
        lines.append("")
        
        # Metadata
        metadata = report_data.get("metadata", {})
        generated_at = metadata.get("generated_at", "")
        if generated_at:
            lines.append(f"**Generated:** {generated_at}")
            lines.append("")
        
        # Scope
        scope = report_data.get("scope", "Vulnerability Analysis")
        lines.append(f"**Scope:** {scope}")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        exec_summary = report_workspace.executive_summary or report_data.get("executive_summary", "")
        lines.append(exec_summary)
        lines.append("")
        
        # Methodology
        lines.append("## Scope & Methodology")
        lines.append("")
        methodology = report_data.get("methodology", "")
        lines.append(methodology)
        lines.append("")
        
        # Findings Section
        lines.append("## Findings")
        lines.append("")
        
        findings = report_data.get("findings", [])
        for finding in findings:
            lines.append(f"### {finding.get('vulnerability_id', 'UNKNOWN')}: {finding.get('title', 'Unknown')}")
            lines.append("")
            
            # Finding details
            lines.append(f"**Severity:** {finding.get('severity', 'Unknown')}  ")
            lines.append(f"**Confidence:** {finding.get('confidence', 0.0):.2f}  ")
            lines.append(f"**Category:** {finding.get('category', 'Unknown')}")
            lines.append("")
            
            # Affected files
            affected_files = finding.get("affected_files", [])
            if affected_files:
                lines.append("**Affected Files:**")
                for file_path in affected_files:
                    lines.append(f"- `{file_path}`")
                lines.append("")
            
            # Locations
            locations = finding.get("locations", [])
            if locations:
                lines.append("**Locations:**")
                for loc in locations:
                    file_path = loc.get("file", "unknown")
                    line_start = loc.get("line_start")
                    if line_start is not None:
                        lines.append(f"- `{file_path}` (line {line_start})")
                    else:
                        lines.append(f"- `{file_path}`")
                lines.append("")
            
            # Evidence snippets
            if locations:
                for loc in locations:
                    snippet = loc.get("snippet", "")
                    if snippet:
                        lines.append("**Evidence:**")
                        lines.append("```")
                        lines.append(snippet)
                        lines.append("```")
                        lines.append("")
            
            # AI Explanation (if available)
            ai_explanation = finding.get("ai_suggested_explanation")
            if ai_explanation:
                lines.append("**AI Suggested Explanation:**")
                lines.append("")
                lines.append(f"_{ai_explanation}_")
                lines.append("")
            
            # AI Remediation (if available)
            ai_remediation = finding.get("ai_suggested_remediation", [])
            if ai_remediation:
                lines.append("**AI Suggested Remediation:**")
                lines.append("")
                for i, step in enumerate(ai_remediation, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")
            
            # Analyst Notes (if available)
            analyst_notes = finding.get("analyst_notes")
            if analyst_notes:
                lines.append("**Analyst Notes:**")
                lines.append("")
                lines.append(analyst_notes)
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Risk Overview
        lines.append("## Risk Overview")
        lines.append("")
        risk_overview = report_data.get("risk_overview", "")
        lines.append(risk_overview)
        lines.append("")
        
        # Write to file
        content = "\n".join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, ""
        
    except Exception as e:
        return False, str(e)


def export_to_pdf(
    report_data: dict,
    report_workspace,
    output_path: str,
) -> tuple[bool, str]:
    """
    Export report to PDF format.
    
    First converts to Markdown, then uses markdown2 or similar to generate PDF.
    Falls back to basic text-to-PDF if markdown library unavailable.
    
    Args:
        report_data: Report data structure from report_generator
        report_workspace: ReportWorkspace instance
        output_path: Path to save PDF file
    
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        # Try to use reportlab for PDF generation (primary method)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
        except ImportError:
            return False, "reportlab library not installed. Install with: pip install reportlab"
            # Fallback: Use reportlab for simple PDF generation
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
        # Generate Markdown first (we'll convert to text)
        temp_md = output_path.replace('.pdf', '_temp.md')
        success, error = export_to_markdown(report_data, report_workspace, temp_md)
        if not success:
            return False, error
        
        # Read markdown content
        with open(temp_md, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Check if this is a draft report
        is_draft = report_data.get("is_draft", False)
        draft_label = report_data.get("draft_label", "Sample Report - Draft")
        
        # Convert markdown headers and lists to plain text for PDF
        lines = md_content.split('\n')
            
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='black',
            spaceAfter=12,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='black',
            spaceAfter=10,
        )
        
        # Add draft label to title if draft
        title_added = False
        
        # Parse markdown and add to PDF
        for line in lines:
            if not line.strip():
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('# '):
                title_text = line[2:]
                if is_draft and not title_added:
                    title_text = f"{draft_label}\n\n{title_text}"
                    title_added = True
                story.append(Paragraph(title_text, title_style))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], heading_style))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading3']))
            elif line.startswith('**') and line.endswith('**'):
                story.append(Paragraph(line.replace('**', ''), styles['Normal']))
            elif line.startswith('`') and line.endswith('`'):
                story.append(Paragraph(f"<i>{line[1:-1]}</i>", styles['Normal']))
            elif line.startswith('- '):
                story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
            elif line.strip():
                story.append(Paragraph(line, styles['Normal']))
        
        doc.build(story)
        
        # Clean up temp file
        try:
            Path(temp_md).unlink()
        except:
            pass
        
        return True, ""
        
    except Exception as e:
        return False, f"PDF export failed: {str(e)}"
