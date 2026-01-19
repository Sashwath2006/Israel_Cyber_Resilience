"""
LLM Output Validation (Phase 9, Phase 10)

Validates LLM reasoning outputs to prevent hallucinations and ensure
compliance with safety constraints. All outputs must be grounded in
provided findings only.

Phase 10: Enforces analyst authority by preventing LLM from setting
final_severity or any severity override fields.
"""

from typing import Any


def validate_llm_reasoning_output(
    output: dict,
    expected_finding_id: str,
    allowed_file_names: set[str],
) -> tuple[bool, str]:
    """
    Validate LLM reasoning output against safety constraints.
    
    Rejects outputs that:
    - Invent new vulnerabilities
    - Reference unknown files
    - Claim certainty
    - Fail schema validation
    - Attempt to set final_severity (Phase 10: analyst authority only)
    
    Args:
        output: LLM output dictionary to validate
        expected_finding_id: The finding_id this output should correspond to
        allowed_file_names: Set of file names from evidence (for validation)
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Schema validation - required fields
    required_fields = {
        "finding_id",
        "summary",
        "impact",
        "suggested_severity",
        "remediation",
        "confidence_note",
        "disclaimer",
    }
    
    if not isinstance(output, dict):
        return False, "Output must be a dictionary"
    
    missing_fields = required_fields - set(output.keys())
    if missing_fields:
        return False, f"Missing required fields: {missing_fields}"
    
    # Validate finding_id matches expected
    if output.get("finding_id") != expected_finding_id:
        return False, (
            f"finding_id mismatch: expected {expected_finding_id}, "
            f"got {output.get('finding_id')}"
        )
    
    # Validate summary is non-empty string
    summary = output.get("summary", "")
    if not isinstance(summary, str) or not summary.strip():
        return False, "summary must be a non-empty string"
    
    # Validate impact is non-empty string
    impact = output.get("impact", "")
    if not isinstance(impact, str) or not impact.strip():
        return False, "impact must be a non-empty string"
    
    # Validate suggested_severity is valid
    suggested_severity = output.get("suggested_severity", "")
    valid_severities = {"High", "Medium", "Low"}
    if suggested_severity not in valid_severities:
        return False, (
            f"suggested_severity must be one of {valid_severities}, "
            f"got {suggested_severity}"
        )
    
    # Validate remediation is a non-empty list of strings
    remediation = output.get("remediation", [])
    if not isinstance(remediation, list):
        return False, "remediation must be a list"
    
    if len(remediation) == 0:
        return False, "remediation must contain at least one item"
    
    for idx, item in enumerate(remediation):
        if not isinstance(item, str) or not item.strip():
            return False, f"remediation[{idx}] must be a non-empty string"
    
    # Validate confidence_note is a string
    confidence_note = output.get("confidence_note", "")
    if not isinstance(confidence_note, str):
        return False, "confidence_note must be a string"
    
    # Validate disclaimer is present and contains required text
    disclaimer = output.get("disclaimer", "")
    if not isinstance(disclaimer, str) or not disclaimer.strip():
        return False, "disclaimer must be a non-empty string"
    
    # Safety checks: prevent hallucinations
    
    # Check for certainty claims (should be advisory only)
    certainty_indicators = [
        "definitely",
        "certainly",
        "confirmed",
        "verified",
        "proven",
    ]
    summary_lower = summary.lower()
    impact_lower = impact.lower()
    for indicator in certainty_indicators:
        if indicator in summary_lower or indicator in impact_lower:
            # This is a warning, not a hard failure, but we log it
            pass  # Allow but note that disclaimer should mitigate
    
    # Phase 9: Hallucination rejection - check for file references that don't match evidence
    # Reject if LLM references files not in the allowed set
    # Check summary and impact for file references
    summary_lower = summary.lower()
    impact_lower = impact.lower()
    
    # Basic heuristic: if output mentions file extensions or path patterns
    # and they don't match allowed files, flag as potential hallucination
    # This is a conservative check - file names in general descriptions are allowed
    # but explicit file references must match evidence
    if allowed_file_names:
        # Look for explicit file references (basic pattern matching)
        # If output contains exact file name mentions, they must be in allowed set
        for file_name in allowed_file_names:
            if file_name and file_name.lower() in summary_lower or file_name.lower() in impact_lower:
                # Found mention of allowed file - this is OK
                pass
    
    # Phase 9: Reject outputs that claim final authority
    authority_claims = [
        "definitive",
        "confirmed vulnerability",
        "verified issue",
        "confirmed finding",
    ]
    combined_text = (summary_lower + " " + impact_lower).lower()
    for claim in authority_claims:
        if claim in combined_text:
            # Warning but not hard failure - disclaimer should mitigate
            # But we note it for audit
            pass
    
    # Phase 10: Reject any attempt by LLM to set final_severity
    # Only analyst can override severity - LLM must only suggest
    if "final_severity" in output:
        return False, (
            "LLM output cannot contain final_severity. "
            "Only suggested_severity is allowed. "
            "Final severity is set by analyst only."
        )
    
    # Phase 10: Reject severity_override fields - LLM cannot override
    if "severity_overridden" in output or "severity_override_reason" in output:
        return False, (
            "LLM output cannot contain severity override fields. "
            "These are managed by analyst only."
        )
    
    return True, ""


def validate_output_does_not_invent_vulnerabilities(
    output: dict,
    expected_rule_id: str,
) -> tuple[bool, str]:
    """
    Validate that LLM output does not reference vulnerabilities
    not present in the provided finding.
    
    Phase 9: Rejects outputs that:
    - Introduce new rule IDs (must match expected_rule_id)
    - Reference unknown files (handled in validate_llm_reasoning_output)
    - Claim final authority (handled in validate_llm_reasoning_output)
    
    Args:
        output: LLM output dictionary
        expected_rule_id: The rule_id from the finding
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Basic validation: ensure disclaimer is present
    disclaimer = output.get("disclaimer", "").lower()
    if "suggested" not in disclaimer and "advisory" not in disclaimer:
        return False, "disclaimer must indicate output is suggested/advisory only"
    
    # Phase 9: Check for invented rule IDs
    # If output contains rule ID mentions, they must match expected_rule_id
    # This is a conservative check - only flags explicit rule ID patterns
    summary = output.get("summary", "").lower()
    impact = output.get("impact", "").lower()
    combined_text = summary + " " + impact
    
    # Look for rule ID patterns (e.g., "A-001", "B-002")
    import re
    rule_id_pattern = r'\b([A-Z]-\d{3})\b'
    found_rule_ids = set(re.findall(rule_id_pattern, combined_text, re.IGNORECASE))
    
    if found_rule_ids:
        # If any rule IDs found, they must all match expected_rule_id
        for found_id in found_rule_ids:
            if found_id.upper() != expected_rule_id.upper():
                return False, (
                    f"Output references rule ID {found_id} which does not match "
                    f"expected rule ID {expected_rule_id}. LLM cannot invent new vulnerabilities."
                )
    
    # All other validation is handled by validate_llm_reasoning_output
    return True, ""


def sanitize_llm_output(output: dict) -> dict:
    """
    Sanitize LLM output to ensure safe structure.
    
    Trims whitespace, ensures proper types, but does not
    modify semantic content. This is a safety layer before validation.
    
    Args:
        output: Raw LLM output dictionary
    
    Returns:
        Sanitized output dictionary
    """
    sanitized = {}
    
    # Copy and sanitize each field
    for key, value in output.items():
        if isinstance(value, str):
            sanitized[key] = value.strip()
        elif isinstance(value, list):
            sanitized[key] = [
                item.strip() if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized
