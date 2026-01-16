"""
Finding Integration Utilities (Phase 10)

Helper functions to integrate findings from rule engine and LLM
reasoning with Phase 10 severity override fields.

This module provides glue logic that doesn't modify upstream
rule engine or LLM reasoning logic.
"""

from typing import Optional

from app.severity_override import (
    initialize_severity_fields,
    override_severity,
    clear_severity_override,
    get_final_severity,
    validate_severity_fields,
)


def enhance_findings_with_severity_fields(findings: list[dict]) -> list[dict]:
    """
    Enhance findings from rule engine with Phase 10 severity override fields.
    
    This function is called AFTER rule_engine.run_rules() to add
    Phase 10 fields without modifying the rule engine.
    
    Args:
        findings: List of findings from rule engine
    
    Returns:
        List of enhanced findings with Phase 10 severity fields initialized
    
    Note:
        This does not modify the original findings. Creates new dicts.
        Rule-based suggested_severity is preserved as suggested_severity.
        final_severity initially equals suggested_severity.
    """
    enhanced = []
    
    for finding in findings:
        # Initialize Phase 10 severity fields
        # Rule-based severity becomes suggested_severity
        rule_severity = finding.get("severity_suggested")
        
        enhanced_finding = initialize_severity_fields(
            finding,
            rule_suggested_severity=rule_severity,
            llm_suggested_severity=None,  # LLM suggestion comes later if available
        )
        
        enhanced.append(enhanced_finding)
    
    return enhanced


def integrate_llm_suggestions(
    findings: list[dict],
    llm_outputs: list[dict],
) -> list[dict]:
    """
    Integrate LLM suggestions into findings without allowing override.
    
    This function merges LLM reasoning outputs with findings, ensuring
    that LLM suggestions are stored but do not override final_severity.
    
    Args:
        findings: List of findings with Phase 10 fields initialized
        llm_outputs: List of LLM reasoning outputs (one per finding)
    
    Returns:
        List of findings with LLM suggestions integrated
    
    Note:
        This creates a mapping by finding_id to merge LLM outputs.
        LLM suggested_severity is stored as llm_suggested_severity.
        final_severity remains unchanged unless analyst explicitly overrides.
    """
    # Create mapping of finding_id -> LLM output
    llm_map = {output.get("finding_id"): output for output in llm_outputs}
    
    integrated = []
    
    for finding in findings:
        finding_id = finding.get("finding_id")
        llm_output = llm_map.get(finding_id)
        
        if llm_output:
            # Store LLM suggestion as llm_suggested_severity
            llm_suggested = llm_output.get("suggested_severity")
            
            if llm_suggested:
                finding["llm_suggested_severity"] = llm_suggested
            
            # Merge other LLM fields (summary, impact, remediation, etc.)
            # but preserve finding structure
            # Note: LLM cannot modify final_severity (handled by validation)
            
            # Add LLM reasoning fields for reference
            finding["llm_summary"] = llm_output.get("summary")
            finding["llm_impact"] = llm_output.get("impact")
            finding["llm_remediation"] = llm_output.get("remediation", [])
            finding["llm_confidence_note"] = llm_output.get("confidence_note")
            finding["llm_disclaimer"] = llm_output.get("disclaimer")
        
        integrated.append(finding)
    
    return integrated


def apply_severity_override_to_finding(
    finding: dict,
    final_severity: str,
    reason: Optional[str] = None,
) -> dict:
    """
    Apply severity override to a single finding.
    
    This is a convenience wrapper for override_severity() that ensures
    finding has required fields first.
    
    Args:
        finding: Finding dictionary
        final_severity: Final severity to set ("High", "Medium", or "Low")
        reason: Optional reason for override
    
    Returns:
        Finding dictionary with severity overridden
    
    Raises:
        ValueError: If final_severity is invalid or finding lacks required fields
    """
    # Ensure finding has Phase 10 fields
    if "suggested_severity" not in finding:
        finding = initialize_severity_fields(
            finding,
            rule_suggested_severity=finding.get("severity_suggested"),
        )
    
    # Apply override
    return override_severity(finding, final_severity, reason)


def ensure_all_findings_have_severity_fields(findings: list[dict]) -> list[dict]:
    """
    Ensure all findings have Phase 10 severity fields initialized.
    
    This is a safety function that adds missing severity fields to findings
    that may have been created before Phase 10 or from external sources.
    
    Args:
        findings: List of findings (may have mixed Phase 10 fields)
    
    Returns:
        List of findings with all Phase 10 fields guaranteed
    """
    enhanced = []
    
    for finding in findings:
        # If already has Phase 10 fields, validate and use as-is
        if "suggested_severity" in finding and "final_severity" in finding:
            # Validate existing fields
            is_valid, error = validate_severity_fields(finding)
            if is_valid:
                enhanced.append(finding)
                continue
        
        # Otherwise, initialize Phase 10 fields
        rule_severity = finding.get("severity_suggested", "Medium")
        llm_severity = finding.get("llm_suggested_severity")
        
        enhanced_finding = initialize_severity_fields(
            finding,
            rule_suggested_severity=rule_severity,
            llm_suggested_severity=llm_severity,
        )
        
        enhanced.append(enhanced_finding)
    
    return enhanced
