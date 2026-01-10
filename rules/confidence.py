"""
Deterministic Confidence Scoring (Phase 8.3)

Confidence calculation derived solely from rule metadata and evidence
characteristics. No AI, ML, randomness, or probabilistic models.

Confidence is supporting data, not a decision.
"""

import math


# ============================================================
# CONFIDENCE CALCULATION
# ============================================================

def calculate_confidence(
    confidence_weight: float,
    evidence_count: int,
    evidence_completeness: float = 1.0,
) -> float:
    """
    Calculate deterministic confidence score for a finding.
    
    Formula:
        base = confidence_weight
        occurrence_factor = min(1.0, log(1 + evidence_count))
        completeness_factor = evidence_completeness
        confidence = clamp(base * occurrence_factor * completeness_factor, 0.0, 1.0)
    
    The formula is:
    - Deterministic: same inputs always yield same output
    - Bounded: always returns value in [0.0, 1.0]
    - Explainable: based on rule weight, evidence count, and completeness
    
    Args:
        confidence_weight: Base confidence weight from rule metadata (0.0-1.0)
        evidence_count: Number of evidence entries (>= 1)
        evidence_completeness: Completeness factor for evidence (0.0-1.0, default 1.0)
                              Based on presence of location, snippet, etc.
    
    Returns:
        Confidence score in range [0.0, 1.0]
        
    Raises:
        ValueError: If inputs are invalid (confidence_weight missing, evidence_count < 1)
    """
    # Validate inputs
    if confidence_weight is None:
        raise ValueError("confidence_weight is required but was None")
    
    if not isinstance(confidence_weight, (int, float)):
        raise ValueError(
            f"confidence_weight must be numeric, got {type(confidence_weight).__name__}"
        )
    
    if evidence_count < 1:
        raise ValueError(
            f"evidence_count must be >= 1, got {evidence_count}"
        )
    
    if not isinstance(evidence_completeness, (int, float)):
        raise ValueError(
            f"evidence_completeness must be numeric, got {type(evidence_completeness).__name__}"
        )
    
    # Clamp confidence_weight to [0.0, 1.0]
    base = max(0.0, min(1.0, float(confidence_weight)))
    
    # Occurrence factor: logarithmic scaling with evidence count
    # log(1 + count) gives diminishing returns
    # For count=1: log(2) ≈ 0.693
    # For count=2: log(3) ≈ 1.099 → capped at 1.0
    # For count=3: log(4) ≈ 1.386 → capped at 1.0
    occurrence_factor = min(1.0, math.log(1 + evidence_count))
    
    # Completeness factor: how complete is the evidence
    # Clamp to [0.0, 1.0]
    completeness_factor = max(0.0, min(1.0, float(evidence_completeness)))
    
    # Compute final confidence
    confidence = base * occurrence_factor * completeness_factor
    
    # Clamp to [0.0, 1.0] to ensure bounded output
    confidence = max(0.0, min(1.0, confidence))
    
    return confidence


def assess_evidence_completeness(evidence_list: list[dict]) -> float:
    """
    Assess evidence completeness factor based on evidence characteristics.
    
    Returns 1.0 if all evidence entries have complete location and snippet.
    Returns < 1.0 if evidence is incomplete (missing location, empty snippet, etc.).
    
    Args:
        evidence_list: List of normalized evidence entries
    
    Returns:
        Completeness factor in range [0.0, 1.0]
    """
    if not evidence_list:
        return 0.0
    
    total_score = 0.0
    entry_count = len(evidence_list)
    
    for evidence in evidence_list:
        entry_score = 1.0
        
        # Check location presence
        if "location" not in evidence or not evidence["location"]:
            entry_score *= 0.5
        else:
            location = evidence["location"]
            # Check if location has valid start
            if "start" not in location or location["start"] is None:
                entry_score *= 0.5
        
        # Check snippet presence and non-empty
        if "snippet" not in evidence or not evidence.get("snippet", "").strip():
            entry_score *= 0.5
        
        # Check file presence
        if "file" not in evidence or not evidence.get("file", "").strip():
            entry_score *= 0.5
        
        total_score += entry_score
    
    # Average completeness across all evidence entries
    completeness = total_score / entry_count if entry_count > 0 else 0.0
    
    return max(0.0, min(1.0, completeness))


# ============================================================
# VALIDATION GUARDS
# ============================================================

def validate_confidence_weight(confidence_weight: float | None) -> bool:
    """
    Validate that confidence_weight is present and in valid range.
    
    Args:
        confidence_weight: Confidence weight to validate
    
    Returns:
        True if valid, False otherwise
    """
    if confidence_weight is None:
        return False
    
    if not isinstance(confidence_weight, (int, float)):
        return False
    
    # Allow values outside [0.0, 1.0] but warn - will be clamped in calculation
    return True


def validate_confidence_score(confidence: float) -> bool:
    """
    Validate that confidence score is in valid range [0.0, 1.0].
    
    Args:
        confidence: Confidence score to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(confidence, (int, float)):
        return False
    
    return 0.0 <= confidence <= 1.0
