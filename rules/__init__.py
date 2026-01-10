"""
Rules package for offline hybrid security analysis.

Phase 8.1: Rule taxonomy and metadata foundation.
Phase 8.2: Evidence normalization.
Phase 8.3: Deterministic confidence scoring.
Phase 8.4: File-type-specific rule sets.
Phase 8.5: Rule suppression and false-positive handling.
"""

from rules.metadata import (
    RuleMetadata,
    validate_rule_metadata,
    Evidence,
    EvidenceLocation,
    validate_evidence,
    validate_evidence_list,
    normalize_evidence,
    SUPPORTED_FILE_TYPES,
    FORMAT_TO_FILE_TYPE,
    normalize_file_type,
)
from rules.confidence import (
    calculate_confidence,
    assess_evidence_completeness,
    validate_confidence_weight,
    validate_confidence_score,
)
from rules.suppression import (
    create_suppression_metadata,
    suppress_finding,
    unsuppress_finding,
    filter_findings,
    validate_suppression_metadata,
)

__all__ = [
    "RuleMetadata",
    "validate_rule_metadata",
    "Evidence",
    "EvidenceLocation",
    "validate_evidence",
    "validate_evidence_list",
    "normalize_evidence",
    "calculate_confidence",
    "assess_evidence_completeness",
    "validate_confidence_weight",
    "validate_confidence_score",
    "SUPPORTED_FILE_TYPES",
    "FORMAT_TO_FILE_TYPE",
    "normalize_file_type",
    "create_suppression_metadata",
    "suppress_finding",
    "unsuppress_finding",
    "filter_findings",
    "validate_suppression_metadata",
]
