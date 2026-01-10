"""
Rules package for offline hybrid security analysis.

Phase 8.1: Rule taxonomy and metadata foundation.
Phase 8.2: Evidence normalization.
"""

from rules.metadata import (
    RuleMetadata,
    validate_rule_metadata,
    Evidence,
    EvidenceLocation,
    validate_evidence,
    validate_evidence_list,
    normalize_evidence,
)

__all__ = [
    "RuleMetadata",
    "validate_rule_metadata",
    "Evidence",
    "EvidenceLocation",
    "validate_evidence",
    "validate_evidence_list",
    "normalize_evidence",
]
