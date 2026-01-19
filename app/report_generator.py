"""
Report Generation (Phase 12)

Generates sample security reports from findings after scan completion.
Reports are editable and stored in memory only.

The generator creates structured reports with:
- Executive Summary (generalized)
- Scope & Methodology
- Findings Section with evidence and locations
- Risk Overview
- Analyst Notes

All text is editable. No auto-save.
"""

from typing import Optional
from datetime import datetime
from app.severity_override import get_final_severity
from app.ollama_client import generate, is_ollama_available


def generate_sample_report(
    findings: list[dict],
    scope: Optional[str] = None,
    model_id: Optional[str] = None,
) -> dict:
    """
    Generate a sample security report from findings.
    
    Creates a structured report template that can be edited by the analyst.
    The report includes all findings with their evidence, severity, and locations.
    
    Args:
        findings: List of findings (should have Phase 10 severity fields)
        scope: Optional scope description
    
    Returns:
        Dictionary with report structure:
        {
            "executive_summary": str,
            "scope": str,
            "methodology": str,
            "findings": [...],  # Structured finding entries
            "risk_overview": str,
        }
    """
    # Filter active findings (exclude suppressed)
    active_findings = [f for f in findings if not f.get("suppressed", False)]
    
    # Count by severity
    severity_counts = {"High": 0, "Medium": 0, "Low": 0}
    for finding in active_findings:
        final_sev = get_final_severity(finding)
        severity_counts[final_sev] = severity_counts.get(final_sev, 0) + 1
    
    total_active = len(active_findings)
    total_suppressed = len(findings) - total_active
    
    # Generate executive summary using LLM if available, otherwise use template
    if model_id and is_ollama_available():
        exec_summary = _generate_executive_summary_with_llm(
            findings=active_findings,
            total_active=total_active,
            severity_counts=severity_counts,
            scope=scope,
            model_id=model_id,
        )
    else:
        # Fallback to template-based summary if LLM unavailable
        exec_summary = _generate_executive_summary(
            total_active=total_active,
            severity_counts=severity_counts,
            scope=scope,
        )
    
    # Generate scope & methodology
    scope_text = scope or "Vulnerability Analysis"
    methodology = _generate_methodology()
    
    # Generate structured findings section
    structured_findings = []
    for i, finding in enumerate(active_findings, 1):
        structured_finding = _structure_finding(finding, index=i)
        structured_findings.append(structured_finding)
    
    # Generate risk overview
    risk_overview = _generate_risk_overview(severity_counts, total_active)
    
    return {
        "executive_summary": exec_summary,
        "scope": scope_text,
        "methodology": methodology,
        "findings": structured_findings,
        "risk_overview": risk_overview,
        "metadata": {
            "total_findings": total_active,
            "suppressed_findings": total_suppressed,
            "severity_breakdown": severity_counts,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
    }


def _generate_executive_summary_with_llm(
    findings: list[dict],
    total_active: int,
    severity_counts: dict[str, int],
    scope: Optional[str],
    model_id: str,
) -> str:
    """
    Generate executive summary using LLM, grounded in findings only.
    
    The LLM creates a professional, non-technical executive summary based
    on the actual findings. No hallucination - only uses provided data.
    """
    scope_text = scope or "the analyzed system"
    high_count = severity_counts.get("High", 0)
    medium_count = severity_counts.get("Medium", 0)
    low_count = severity_counts.get("Low", 0)
    
    # Build findings summary for LLM context
    findings_summary = []
    for finding in findings[:10]:  # Limit to first 10 for context
        rule_id = finding.get("rule_id", "unknown")
        title = finding.get("title", "Unknown")
        category = finding.get("category", "Unknown")
        final_sev = get_final_severity(finding)
        findings_summary.append(f"- [{rule_id}] {title} ({category}, {final_sev})")
    
    if len(findings) > 10:
        findings_summary.append(f"... and {len(findings) - 10} more findings")
    
    system_prompt = """You are an AI assistant helping write an executive summary for a security assessment report.

CRITICAL CONSTRAINTS:
- Write a professional, non-technical executive summary suitable for executives
- Base your summary ONLY on the provided findings data
- Do NOT invent vulnerabilities, files, or locations not in the data
- Do NOT use specific technical details (file names, line numbers)
- Focus on business impact and risk overview
- Keep it concise (3-5 paragraphs)
- Use the exact numbers provided (do not estimate or round)

Findings Data:
- Total Active Findings: {total_active}
- High Severity: {high_count}
- Medium Severity: {medium_count}
- Low Severity: {low_count}
- Scope: {scope_text}

Sample Findings (for context only):
{findings_summary}

Write an executive summary that:
1. Introduces the assessment and scope
2. Summarizes the overall risk posture
3. Highlights key severity distribution
4. Emphasizes the need for analyst review
5. Concludes with next steps

Return ONLY the executive summary text. No headers, no metadata."""

    user_prompt = "Generate the executive summary based on the findings data above."

    try:
        full_prompt = system_prompt.format(
            total_active=total_active,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            scope_text=scope_text,
            findings_summary="\n".join(findings_summary),
        ) + "\n\n" + user_prompt
        
        success, llm_output = generate(model_id, full_prompt, temperature=0.3)
        
        if success and llm_output.strip():
            # Clean up the output
            summary = llm_output.strip()
            # Remove markdown headers if present
            if summary.startswith("#"):
                lines = summary.split('\n')
                summary = '\n'.join([l for l in lines if not l.strip().startswith('#')])
            return summary
        else:
            # Fallback to template if LLM fails
            return _generate_executive_summary(total_active, severity_counts, scope)
            
    except Exception as e:
        # Fallback to template on error
        return _generate_executive_summary(total_active, severity_counts, scope)


def _generate_executive_summary(
    total_active: int,
    severity_counts: dict[str, int],
    scope: Optional[str],
) -> str:
    """Generate a template-based executive summary (fallback)."""
    scope_text = scope or "the analyzed system"
    
    high_count = severity_counts.get("High", 0)
    medium_count = severity_counts.get("Medium", 0)
    low_count = severity_counts.get("Low", 0)
    
    summary_lines = [
        f"This security assessment identified {total_active} active vulnerability findings in {scope_text}.",
        "",
        f"Severity Distribution:",
        f"- High Severity: {high_count} findings",
        f"- Medium Severity: {medium_count} findings",
        f"- Low Severity: {low_count} findings",
        "",
        "Findings include evidence-based detections with specific file locations and remediation suggestions.",
        "All findings should be reviewed by a security analyst for contextual risk assessment.",
    ]
    
    return "\n".join(summary_lines)


def _generate_methodology() -> str:
    """Generate methodology section."""
    return """This assessment employed a deterministic rule-based scanning approach combined with AI-assisted analysis.

Detection Method:
- Pattern-based rule engine for vulnerability detection
- Evidence collection with exact file and line references
- Confidence scoring based on rule metadata and evidence completeness

Analysis Method:
- Local LLM (Ollama) for explanation and remediation suggestions
- Analyst review for final severity assessment
- Evidence-based validation of all findings

All findings include exact locations and evidence snippets for verification."""


def _structure_finding(finding: dict, index: int) -> dict:
    """
    Structure a finding for the report.
    
    Includes all required fields: ID, title, severity, evidence, locations, etc.
    """
    finding_id = finding.get("finding_id", "unknown")
    rule_id = finding.get("rule_id", "unknown")
    title = finding.get("title", "Unknown Vulnerability")
    category = finding.get("category", "Unknown")
    final_sev = get_final_severity(finding)
    confidence = finding.get("confidence_score", finding.get("confidence", 0.0))
    
    # Extract evidence information
    evidence_list = finding.get("evidence", [])
    affected_files = set()
    locations = []
    
    for evidence in evidence_list:
        file_path = evidence.get("file", "unknown")
        affected_files.add(file_path)
        
        line_start = evidence.get("line_start")
        line_end = evidence.get("line_end")
        snippet = evidence.get("snippet", "")
        
        location_desc = f"{file_path}"
        if line_start is not None:
            if line_end is not None and line_end != line_start:
                location_desc += f" (lines {line_start}-{line_end})"
            else:
                location_desc += f" (line {line_start})"
        
        locations.append({
            "file": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "snippet": snippet[:200] if snippet else "",  # Truncate long snippets
        })
    
    # Get AI suggestions if available
    ai_summary = finding.get("llm_summary")
    ai_remediation = finding.get("llm_remediation", [])
    
    return {
        "vulnerability_id": f"VULN-{index:03d}",
        "finding_id": finding_id,
        "rule_id": rule_id,
        "title": title,
        "category": category,
        "severity": final_sev,  # Final severity (analyst authority)
        "confidence": confidence,
        "affected_files": list(affected_files),
        "locations": locations,
        "ai_suggested_explanation": ai_summary,
        "ai_suggested_remediation": ai_remediation,
        "analyst_notes": finding.get("analyst_notes"),
    }


def _generate_risk_overview(severity_counts: dict[str, int], total_active: int) -> str:
    """Generate risk overview section."""
    high_count = severity_counts.get("High", 0)
    medium_count = severity_counts.get("Medium", 0)
    low_count = severity_counts.get("Low", 0)
    
    lines = [
        "Risk Overview",
        "=" * 70,
        "",
        f"Total Active Findings: {total_active}",
        "",
        f"High Severity ({high_count} findings):",
        "Requires immediate attention. These findings pose significant security risks",
        "and should be remediated as a priority.",
        "",
        f"Medium Severity ({medium_count} findings):",
        "Should be addressed in the near term. These findings indicate potential",
        "security concerns that should be evaluated in context.",
        "",
        f"Low Severity ({low_count} findings):",
        "May be addressed as resources permit. These findings represent lower-risk",
        "issues or hygiene improvements.",
    ]
    
    return "\n".join(lines)
