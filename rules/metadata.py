"""
Rule Metadata Definitions (Phase 8.1)

Structural metadata definitions for rule taxonomy.
No detection logic, confidence formulas, or suppression logic.
"""

from typing import TypedDict, Literal


# ============================================================
# RULE METADATA STRUCTURE
# ============================================================

class RuleMetadata(TypedDict):
    """
    Required metadata fields for every rule.
    All rules must provide these fields.
    """
    rule_id: str
    name: str
    category: str
    default_severity_hint: Literal["Low", "Medium", "High", "Critical"]
    confidence_weight: float
    references: list[str]


# ============================================================
# METADATA VALIDATION
# ============================================================

def validate_rule_metadata(rule: dict) -> bool:
    """
    Validate that a rule dictionary contains all required metadata fields.
    Returns True if valid, False otherwise.
    
    This is structural validation only. Does not validate detection patterns
    or modify rule behavior.
    """
    required_fields = {
        "rule_id",
        "name",
        "category",
        "default_severity_hint",
        "confidence_weight",
        "references",
    }
    
    return all(field in rule for field in required_fields)
