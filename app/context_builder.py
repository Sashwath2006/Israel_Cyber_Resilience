"""
Context Builder for LLM-Assisted Reasoning (Phase 9)

Builds grounded, restrictive prompts that ensure LLM only reasons
over provided findings without inventing vulnerabilities or accessing
raw documents.
"""


def build_context(findings: list[dict], task: str) -> str:
    """
    Build a deterministic, reviewable LLM context from selected findings.
    No raw documents. Evidence is immutable.
    
    Updated for Phase 8.2: evidence is now a list of normalized evidence entries.
    Updated for Phase 9: Enhanced with stricter boundaries and confidence references.
    
    Safety guarantees:
    - LLM never sees raw document content beyond evidence snippets
    - All findings are explicitly labeled with rule metadata
    - Confidence scores are included for context
    - Explicit boundaries prevent vulnerability discovery
    """

    header = (
        "SYSTEM INSTRUCTIONS:\n"
        "You are a security analysis assistant providing EXPLANATIONS ONLY.\n"
        "\n"
        "CRITICAL CONSTRAINTS:\n"
        "- You do NOT discover vulnerabilities\n"
        "- You do NOT parse raw documents\n"
        "- You do NOT mark findings as 'confirmed'\n"
        "- You do NOT assign final severity (only suggest)\n"
        "- You ONLY reason over the findings provided below\n"
        "- All outputs are SUGGESTED/ADVISORY ONLY\n"
        "- If uncertain, explicitly state uncertainty\n"
        "- Do NOT invent facts or reference unknown files\n"
        "\n"
    )

    body = ["PROVIDED FINDINGS:"]

    for f in sorted(findings, key=lambda x: (x["rule_id"], x["evidence"][0]["file"] if x["evidence"] else "")):
        # Evidence is now a list (Phase 8.2 normalized schema)
        evidence_list = f["evidence"]
        
        if not evidence_list:
            continue  # Skip findings with no evidence
        
        # Use first evidence entry for primary context (multiple entries supported)
        primary_evidence = evidence_list[0]
        
        # Build evidence section with normalized fields
        location = primary_evidence["location"]
        location_str = (
            f"{location['type']} {location['start']}"
            + (f"-{location['end']}" if location.get("end") else "")
        )
        
        # Include confidence_score for context (Phase 9)
        confidence_score = f.get("confidence_score", 0.0)
        
        body.append(
            f"\nFINDING ID: {f['finding_id']}\n"
            f"Rule ID: {f['rule_id']}\n"
            f"Title: {f['title']}\n"
            f"Category: {f['category']}\n"
            f"Rule Confidence Weight: {f.get('confidence_weight', 0.0):.2f}\n"
            f"Detected Confidence Score: {confidence_score:.2f}\n"
            f"Rule Suggested Severity: {f['severity_suggested']}\n"
            f"\nEvidence:\n"
            f"  File: {primary_evidence['file']}\n"
            f"  Location: {location_str}\n"
            f"  Evidence Snippet (from rule detection):\n"
            f"  {primary_evidence['snippet']}\n"
        )
        
        # Include additional evidence entries if present
        if len(evidence_list) > 1:
            body.append(f"  Additional Evidence Entries: {len(evidence_list) - 1}")
            for idx, additional_evidence in enumerate(evidence_list[1:], start=2):
                additional_location = additional_evidence["location"]
                additional_location_str = (
                    f"{additional_location['type']} {additional_location['start']}"
                    + (f"-{additional_location['end']}" if additional_location.get("end") else "")
                )
                body.append(
                    f"    Entry {idx}: {additional_evidence['file']} at {additional_location_str}"
                )

    task_block = (
        f"\n\nTASK:\n"
        f"{task}\n"
        f"\n"
        f"Remember: Your output is SUGGESTED/ADVISORY ONLY. "
        f"Analyst review is required for all findings.\n"
    )

    return header + "\n".join(body) + task_block


def build_single_finding_context(finding: dict) -> str:
    """
    Build context for a single finding (one-to-one mapping).
    
    This ensures LLM processes one finding at a time, preventing
    cross-contamination and ensuring clear boundaries.
    
    Args:
        finding: Single finding dictionary
    
    Returns:
        Formatted context string for this finding only
    """
    return build_context([finding], (
        "Provide a structured explanation for this finding:\n"
        "- Explain why this finding indicates a potential risk\n"
        "- Describe the potential impact in general terms\n"
        "- Suggest remediation steps\n"
        "- Propose a suggested severity (High/Medium/Low)\n"
        "- Reference the confidence score in your confidence_note\n"
        "- Include a disclaimer that this is suggested/advisory only"
    ))

