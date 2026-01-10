"""
Rule Suppression & False-Positive Handling (Phase 8.5)

Explicit, reversible, auditable suppression metadata for findings.
Suppression is a view-level control, not data deletion.
Evidence remains unchanged. Detection always runs.
"""

from datetime import datetime
from typing import Literal, Optional


# ============================================================
# SUPPRESSION METADATA
# ============================================================

def create_suppression_metadata(
    suppressed: bool,
    suppression_reason: Optional[str] = None,
    suppressed_by: Literal["user", "system"] = "system",
    suppressed_at: Optional[str] = None,
) -> dict:
    """
    Create suppression metadata structure for a finding.
    
    Args:
        suppressed: Whether the finding is suppressed
        suppression_reason: Explicit reason for suppression (required if suppressed=True)
        suppressed_by: Who/what suppressed the finding ("user" or "system")
        suppressed_at: ISO-8601 timestamp (auto-generated if None and suppressed=True)
    
    Returns:
        Suppression metadata dictionary
    
    Raises:
        ValueError: If suppressed=True but no reason provided
    """
    if suppressed and not suppression_reason:
        raise ValueError("Suppression reason is required when suppressed=True")
    
    if suppressed_at is None and suppressed:
        suppressed_at = datetime.utcnow().isoformat() + "Z"
    
    return {
        "suppressed": suppressed,
        "suppression_reason": suppression_reason if suppressed else None,
        "suppressed_by": suppressed_by if suppressed else None,
        "suppressed_at": suppressed_at if suppressed else None,
    }


# ============================================================
# SUPPRESSION OPERATIONS
# ============================================================

def suppress_finding(
    finding: dict,
    reason: str,
    suppressed_by: Literal["user", "system"] = "user",
) -> dict:
    """
    Suppress a finding with explicit reason and metadata.
    
    Creates a new finding dictionary with suppression metadata.
    Original finding is not modified. Evidence remains unchanged.
    
    Args:
        finding: Finding dictionary to suppress
        reason: Explicit reason for suppression (required)
        suppressed_by: Who/what is suppressing ("user" or "system")
    
    Returns:
        New finding dictionary with suppression metadata
    
    Raises:
        ValueError: If reason is missing or empty
    """
    if not reason or not reason.strip():
        raise ValueError("Suppression reason is required and cannot be empty")
    
    # Create new finding with suppression metadata (non-destructive)
    suppressed_finding = finding.copy()
    suppressed_finding.update(
        create_suppression_metadata(
            suppressed=True,
            suppression_reason=reason.strip(),
            suppressed_by=suppressed_by,
            suppressed_at=None,  # Auto-generate
        )
    )
    
    return suppressed_finding


def unsuppress_finding(finding: dict) -> dict:
    """
    Remove suppression from a finding (restore visibility).
    
    Creates a new finding dictionary with suppression cleared.
    Original finding is not modified. Evidence remains unchanged.
    
    Args:
        finding: Finding dictionary to unsuppress
    
    Returns:
        New finding dictionary with suppression cleared
    """
    # Create new finding with suppression cleared (non-destructive)
    unsuppressed_finding = finding.copy()
    unsuppressed_finding.update(
        create_suppression_metadata(
            suppressed=False,
            suppression_reason=None,
            suppressed_by=None,
            suppressed_at=None,
        )
    )
    
    return unsuppressed_finding


# ============================================================
# FILTERING & QUERYING
# ============================================================

def filter_findings(
    findings: list[dict],
    include_suppressed: bool = False,
) -> list[dict]:
    """
    Filter findings based on suppression status.
    
    By default, suppressed findings are excluded.
    Set include_suppressed=True to include all findings.
    
    This is a non-destructive filter - original findings are not modified.
    Evidence remains unchanged.
    
    Args:
        findings: List of finding dictionaries
        include_suppressed: If True, include suppressed findings; if False, exclude them
    
    Returns:
        Filtered list of findings (new list, original findings unchanged)
    """
    if include_suppressed:
        return findings.copy()  # Return all findings
    
    # Filter out suppressed findings (default behavior)
    return [
        f for f in findings
        if not f.get("suppressed", False)
    ]


# ============================================================
# VALIDATION
# ============================================================

def validate_suppression_metadata(finding: dict) -> bool:
    """
    Validate that suppression metadata is well-formed.
    
    Args:
        finding: Finding dictionary to validate
    
    Returns:
        True if suppression metadata is valid, False otherwise
    """
    suppressed = finding.get("suppressed", False)
    
    # If suppressed, must have reason
    if suppressed:
        reason = finding.get("suppression_reason")
        if not reason or not reason.strip():
            return False
        
        # Must have suppressed_by
        suppressed_by = finding.get("suppressed_by")
        if suppressed_by not in {"user", "system"}:
            return False
        
        # Must have suppressed_at timestamp
        suppressed_at = finding.get("suppressed_at")
        if not suppressed_at:
            return False
    
    # If not suppressed, suppression fields should be None
    if not suppressed:
        if finding.get("suppression_reason") is not None:
            return False
        if finding.get("suppressed_by") is not None:
            return False
        if finding.get("suppressed_at") is not None:
            return False
    
    return True
