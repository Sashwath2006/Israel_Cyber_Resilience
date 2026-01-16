"""
Severity Override Management (Phase 10)

Enables analyst to override suggested severity and establish final severity.
All overrides are explicit, reversible, and auditable.

Analyst authority is preserved - final_severity is the authoritative value.
"""

from typing import Literal, Optional


# ============================================================
# VALID SEVERITY VALUES
# ============================================================

VALID_SEVERITIES = {"High", "Medium", "Low"}


def is_valid_severity(severity: str) -> bool:
    """
    Validate that a severity value is in the allowed set.
    
    Args:
        severity: Severity value to validate
    
    Returns:
        True if valid, False otherwise
    """
    return severity in VALID_SEVERITIES


# ============================================================
# SEVERITY OVERRIDE OPERATIONS
# ============================================================

def initialize_severity_fields(
    finding: dict,
    rule_suggested_severity: Optional[str] = None,
    llm_suggested_severity: Optional[str] = None,
) -> dict:
    """
    Initialize severity override fields for a finding.
    
    This function adds Phase 10 severity override fields to a finding
    without modifying upstream rule engine logic.
    
    Args:
        finding: Finding dictionary from rule engine or with existing fields
        rule_suggested_severity: Rule-based suggested severity (defaults to finding["severity_suggested"])
        llm_suggested_severity: LLM suggested severity (optional)
    
    Returns:
        New finding dictionary with severity override fields initialized
        - suggested_severity: Primary suggestion (rule-based, falls back to LLM if rule missing)
        - final_severity: Initially equals suggested_severity
        - severity_overridden: False initially
        - severity_override_reason: None initially
        - llm_suggested_severity: LLM suggestion (if provided)
    
    Note:
        This does not modify the original finding. Creates a new dict.
        Defaults final_severity to rule_suggested_severity if available,
        otherwise to llm_suggested_severity.
    """
    # Create new finding to avoid modifying original
    enhanced_finding = finding.copy()
    
    # Determine suggested_severity (rule takes precedence, fallback to LLM)
    rule_sev = rule_suggested_severity or enhanced_finding.get("severity_suggested")
    suggested = rule_sev or llm_suggested_severity or "Medium"  # Safe default
    
    # Validate suggested severity
    if not is_valid_severity(suggested):
        raise ValueError(
            f"Invalid suggested_severity: {suggested}. Must be one of {VALID_SEVERITIES}"
        )
    
    # Initialize Phase 10 fields
    enhanced_finding["suggested_severity"] = suggested
    enhanced_finding["final_severity"] = suggested  # Initially equals suggested
    enhanced_finding["severity_overridden"] = False
    enhanced_finding["severity_override_reason"] = None
    
    # Store LLM suggestion separately if provided
    if llm_suggested_severity:
        enhanced_finding["llm_suggested_severity"] = llm_suggested_severity
    
    return enhanced_finding


def override_severity(
    finding: dict,
    final_severity: Literal["High", "Medium", "Low"],
    reason: Optional[str] = None,
) -> dict:
    """
    Override the final severity for a finding.
    
    This establishes analyst authority - final_severity becomes the
    authoritative value everywhere in the system.
    
    Args:
        finding: Finding dictionary (must have severity fields initialized)
        final_severity: The final severity assigned by analyst
        reason: Optional reason for the override
    
    Returns:
        New finding dictionary with severity overridden
    
    Raises:
        ValueError: If final_severity is invalid or finding lacks required fields
    
    Note:
        This does not modify the original finding. Creates a new dict.
        Once overridden, final_severity is treated as final everywhere.
    """
    # Validate severity
    if not is_valid_severity(final_severity):
        raise ValueError(
            f"Invalid final_severity: {final_severity}. Must be one of {VALID_SEVERITIES}"
        )
    
    # Ensure finding has required fields
    if "suggested_severity" not in finding:
        raise ValueError(
            "Finding must have severity fields initialized before override. "
            "Call initialize_severity_fields() first."
        )
    
    # Create new finding to avoid modifying original
    overridden_finding = finding.copy()
    
    # Set final severity (analyst authority)
    overridden_finding["final_severity"] = final_severity
    overridden_finding["severity_overridden"] = True
    overridden_finding["severity_override_reason"] = reason.strip() if reason else None
    
    return overridden_finding


def clear_severity_override(finding: dict) -> dict:
    """
    Clear a severity override, reverting to suggested_severity.
    
    This makes the override reversible and auditable.
    
    Args:
        finding: Finding dictionary with override
    
    Returns:
        New finding dictionary with override cleared
    
    Note:
        This does not modify the original finding. Creates a new dict.
        After clearing, final_severity reverts to suggested_severity.
    """
    if "suggested_severity" not in finding:
        raise ValueError(
            "Finding must have severity fields initialized. "
            "Call initialize_severity_fields() first."
        )
    
    # Create new finding to avoid modifying original
    cleared_finding = finding.copy()
    
    # Revert to suggested severity
    suggested = cleared_finding.get("suggested_severity", "Medium")
    cleared_finding["final_severity"] = suggested
    cleared_finding["severity_overridden"] = False
    cleared_finding["severity_override_reason"] = None
    
    return cleared_finding


# ============================================================
# SEVERITY AGGREGATION
# ============================================================

def get_final_severity(finding: dict) -> str:
    """
    Get the final severity for a finding.
    
    This is the authoritative severity value that should be used
    throughout the system. Respects analyst overrides.
    
    Args:
        finding: Finding dictionary
    
    Returns:
        Final severity string ("High", "Medium", or "Low")
    
    Note:
        If severity fields are not initialized, falls back to
        severity_suggested for backward compatibility.
    """
    # Phase 10: Use final_severity if available
    if "final_severity" in finding:
        return finding["final_severity"]
    
    # Backward compatibility: fall back to suggested severity
    return finding.get("severity_suggested", "Medium")


# ============================================================
# VALIDATION
# ============================================================

def validate_severity_fields(finding: dict) -> tuple[bool, Optional[str]]:
    """
    Validate that severity override fields are well-formed.
    
    Args:
        finding: Finding dictionary to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Check required fields
    if "suggested_severity" not in finding:
        return False, "Missing required field: suggested_severity"
    
    if "final_severity" not in finding:
        return False, "Missing required field: final_severity"
    
    if "severity_overridden" not in finding:
        return False, "Missing required field: severity_overridden"
    
    # Validate severity values
    suggested = finding.get("suggested_severity")
    if not is_valid_severity(suggested):
        return False, f"Invalid suggested_severity: {suggested}"
    
    final = finding.get("final_severity")
    if not is_valid_severity(final):
        return False, f"Invalid final_severity: {final}"
    
    # Validate override metadata consistency
    is_overridden = finding.get("severity_overridden", False)
    if is_overridden:
        # If overridden, reason is optional but should be a string if present
        reason = finding.get("severity_override_reason")
        if reason is not None and not isinstance(reason, str):
            return False, "severity_override_reason must be a string or None"
    else:
        # If not overridden, reason should be None
        reason = finding.get("severity_override_reason")
        if reason is not None:
            return False, "severity_override_reason must be None when severity_overridden is False"
    
    return True, None


def ensure_llm_cannot_override_severity(
    finding: dict,
    llm_output: dict,
) -> dict:
    """
    Guard against LLM modifying final_severity.
    
    This ensures analyst authority is preserved - LLM suggestions
    are accepted as suggested_severity only, never as final_severity.
    
    Args:
        finding: Current finding dictionary
        llm_output: LLM reasoning output (may contain suggested_severity)
    
    Returns:
        Updated finding dictionary with LLM suggestion integrated safely
    
    Note:
        This function:
        - Accepts LLM suggested_severity as input for consideration
        - Never allows LLM to set final_severity
        - Never allows LLM to clear an existing override
        - Preserves analyst's final_severity if already set
    """
    # Create new finding to avoid modifying original
    protected_finding = finding.copy()
    
    # Extract LLM suggestion if present
    llm_suggested = llm_output.get("suggested_severity")
    
    if llm_suggested and is_valid_severity(llm_suggested):
        # Store LLM suggestion for reference only
        protected_finding["llm_suggested_severity"] = llm_suggested
        
        # If no override exists, analyst may consider updating suggested_severity
        # but final_severity is only set by analyst via override_severity()
        if not protected_finding.get("severity_overridden", False):
            # LLM suggestion can inform but not override
            # The rule-based suggested_severity remains primary
            # Analyst must explicitly override to change final_severity
            pass  # Do nothing - preserve rule-based suggestion
    
    # Critical: Remove any final_severity that LLM might have attempted to set
    if "final_severity" in llm_output:
        # This is a security violation - LLM attempted to set final_severity
        # We ignore it and preserve the existing final_severity
        pass  # Already using finding's final_severity above
    
    return protected_finding
