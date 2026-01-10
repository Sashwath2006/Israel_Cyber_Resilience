"""
Rule Metadata Definitions (Phase 8.1)
Evidence Normalization (Phase 8.2)
Deterministic Confidence Scoring (Phase 8.3)
File-Type-Specific Rule Sets (Phase 8.4)

Structural metadata definitions for rule taxonomy.
Normalized evidence schema for consistent finding evidence.
Deterministic confidence calculation in rules/confidence.py.
File-type applicability constraints for rule precision.
No detection logic or suppression logic.
"""

from typing import TypedDict, Literal
from datetime import datetime


# ============================================================
# FILE TYPE CONSTANTS (Phase 8.4)
# ============================================================

# Supported file types (small, explicit enum - extendable later)
SUPPORTED_FILE_TYPES = {"log", "csv", "json", "text"}

# Mapping from chunk format to normalized file type
# txt, log, conf, config → "text"
# csv → "csv"
# json → "json"
# Unknown → "text" (safe default)
FORMAT_TO_FILE_TYPE = {
    "txt": "text",
    "log": "text",
    "conf": "text",
    "config": "text",
    "csv": "csv",
    "json": "json",
}


def normalize_file_type(chunk_format: str | None) -> str:
    """
    Normalize chunk format to standard file type.
    
    Maps ingestion format strings to normalized file types:
    - txt, log, conf, config → "text"
    - csv → "csv"
    - json → "json"
    - None or unknown → "text" (safe default)
    
    Args:
        chunk_format: Format string from chunk (e.g., "txt", "log", "csv", "json")
    
    Returns:
        Normalized file type string: "log", "csv", "json", or "text"
    """
    if chunk_format is None:
        return "text"
    
    normalized = chunk_format.lower().strip()
    return FORMAT_TO_FILE_TYPE.get(normalized, "text")


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
    applicable_file_types: set[str]  # Phase 8.4: file types this rule applies to


# ============================================================
# METADATA VALIDATION
# ============================================================

def validate_rule_metadata(rule: dict) -> bool:
    """
    Validate that a rule dictionary contains all required metadata fields.
    Returns True if valid, False otherwise.
    
    This is structural validation only. Does not validate detection patterns
    or modify rule behavior.
    
    Phase 8.4: Also validates applicable_file_types is present and valid.
    """
    required_fields = {
        "rule_id",
        "name",
        "category",
        "default_severity_hint",
        "confidence_weight",
        "references",
        "applicable_file_types",  # Phase 8.4: required field
    }
    
    if not all(field in rule for field in required_fields):
        return False
    
    # Validate applicable_file_types is a set and contains only supported types
    applicable = rule.get("applicable_file_types")
    if not isinstance(applicable, (set, list, tuple)):
        return False
    
    applicable_set = set(applicable)
    if not applicable_set:
        return False  # Must declare at least one applicable file type
    
    # All declared types must be in supported set
    if not applicable_set.issubset(SUPPORTED_FILE_TYPES):
        return False
    
    return True


# ============================================================
# EVIDENCE SCHEMA (Phase 8.2)
# ============================================================

class EvidenceLocation(TypedDict):
    """
    Location information for evidence within a source file.
    """
    type: Literal["line", "row", "range"]
    start: int
    end: int | None


class Evidence(TypedDict):
    """
    Normalized evidence entry for a rule finding.
    Every finding must include at least one evidence entry.
    Multiple evidence entries per finding are supported.
    """
    file: str
    location: EvidenceLocation
    snippet: str
    timestamp: str | None


# ============================================================
# EVIDENCE VALIDATION
# ============================================================

def validate_evidence(evidence: dict) -> bool:
    """
    Validate that an evidence dictionary conforms to the normalized schema.
    Returns True if valid, False otherwise.
    
    Raises ValueError with clear message if validation fails.
    """
    if not isinstance(evidence, dict):
        return False
    
    # Required top-level fields
    required_fields = {"file", "location", "snippet"}
    if not all(field in evidence for field in required_fields):
        return False
    
    # File must be non-empty string
    if not isinstance(evidence["file"], str) or not evidence["file"]:
        return False
    
    # Location must be dict with required fields
    location = evidence["location"]
    if not isinstance(location, dict):
        return False
    
    required_location_fields = {"type", "start"}
    if not all(field in location for field in required_location_fields):
        return False
    
    # Location type must be valid
    if location["type"] not in {"line", "row", "range"}:
        return False
    
    # Start must be non-negative integer
    if not isinstance(location["start"], int) or location["start"] < 0:
        return False
    
    # End must be None or non-negative integer >= start
    if "end" in location and location["end"] is not None:
        if not isinstance(location["end"], int):
            return False
        if location["end"] < 0 or location["end"] < location["start"]:
            return False
    
    # Snippet must be string (length validation happens in normalization)
    if not isinstance(evidence["snippet"], str):
        return False
    
    # Timestamp must be None or string (ISO format validation optional)
    if "timestamp" in evidence and evidence["timestamp"] is not None:
        if not isinstance(evidence["timestamp"], str):
            return False
    
    return True


def validate_evidence_list(evidence_list: list) -> bool:
    """
    Validate that a list of evidence entries is non-empty and all entries are valid.
    Returns True if valid, False otherwise.
    """
    if not isinstance(evidence_list, list):
        return False
    
    if len(evidence_list) == 0:
        return False
    
    return all(validate_evidence(entry) for entry in evidence_list)


# ============================================================
# EVIDENCE NORMALIZATION
# ============================================================

def normalize_evidence(
    source_file: str,
    line_start: int | None,
    line_end: int | None,
    content: str,
    format_type: str = "text",
    timestamp: str | None = None,
    max_snippet_length: int = 500,
) -> Evidence:
    """
    Normalize chunk data into standardized evidence schema.
    
    Maps ingestion chunk fields to normalized evidence structure:
    - source_file → file
    - line_start/line_end → location (type: "line" | "row" | "range")
    - content excerpt → snippet (bounded length)
    - Optional timestamp
    
    Args:
        source_file: Source filename
        line_start: Starting line/row number (None for unknown)
        line_end: Ending line/row number (None for single line/unknown)
        content: Content snippet (will be truncated to max_snippet_length)
        format_type: File format ("csv" → row, "text"/"log"/"conf" → line, "json" → range)
        timestamp: Optional ISO timestamp string
        max_snippet_length: Maximum snippet length (default 500 chars)
    
    Returns:
        Normalized Evidence dictionary conforming to schema
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Determine location type from format
    if format_type == "csv":
        loc_type = "row"
    elif format_type in {"txt", "log", "conf", "config"}:
        loc_type = "line"
    else:  # json or other
        loc_type = "range"
    
    # Normalize line/row numbers (default to 1 if None for valid location)
    if line_start is None:
        start = 1
    else:
        start = max(0, line_start)
    
    if line_end is None:
        # Single line/row if only start is provided
        end = start if line_start is not None else None
    else:
        end = max(start, line_end) if line_end >= start else start
    
    # Normalize snippet (truncate to max length, preserve newlines for readability)
    snippet = content.strip()
    if len(snippet) > max_snippet_length:
        snippet = snippet[:max_snippet_length].rsplit("\n", 1)[0] + "\n[... truncated ...]"
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"
    
    evidence: Evidence = {
        "file": source_file,
        "location": {
            "type": loc_type,
            "start": start,
            "end": end,
        },
        "snippet": snippet,
        "timestamp": timestamp,
    }
    
    # Validate before returning
    if not validate_evidence(evidence):
        raise ValueError(
            f"Failed to create valid evidence for file {source_file}: "
            f"validation failed"
        )
    
    return evidence
