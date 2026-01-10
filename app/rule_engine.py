import re
import uuid

from rules.metadata import (
    validate_rule_metadata,
    normalize_evidence,
    validate_evidence_list,
    normalize_file_type,
    SUPPORTED_FILE_TYPES,
)
from rules.confidence import (
    calculate_confidence,
    assess_evidence_completeness,
    validate_confidence_weight,
    validate_confidence_score,
)
from rules.suppression import (
    create_suppression_metadata,
    validate_suppression_metadata,
)

# All file types for rules that should apply to all supported types (Phase 8.4)
ALL_FILE_TYPES = SUPPORTED_FILE_TYPES  # {"log", "csv", "json", "text"}

# ============================================================
# FALSE POSITIVE SUPPRESSION (DETERMINISTIC & AUDITABLE)
# ============================================================

SUPPRESSION_PATTERNS = [
    # Commented lines
    r"^\s*#",
    r"^\s*//",
    r"^\s*/\*",

    # Placeholder / dummy values
    r"(example|changeme|your_|dummy|test)",

    # Documentation / explanation context
    r"(documentation|readme|usage|how to)",

    # Explicit non-sensitive markers
    r"<redacted>",
    r"<placeholder>",
    r"not_used",
]


def is_suppressed(content: str) -> bool:
    """
    Returns True if the content matches any explicit
    false-positive suppression pattern.
    """
    for pattern in SUPPRESSION_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


# ============================================================
# PHASE 8 RULE TAXONOMY (DETERMINISTIC)
# ============================================================

RULES = [

    # -----------------------------
    # A — Credentials & Secrets
    # -----------------------------

    {
        "rule_id": "A-001",
        "name": "Hardcoded password detected",
        "category": "Credentials",
        "title": "Hardcoded password detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.95,
        "confidence": 0.95,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\bpassword\b\s*=", r"\bpwd\b\s*="],
    },
    {
        "rule_id": "A-002",
        "name": "API key or token detected",
        "category": "Credentials",
        "title": "API key or token detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.95,
        "confidence": 0.95,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\bapi[_-]?key\b\s*=", r"\btoken\b\s*="],
    },
    {
        "rule_id": "A-003",
        "name": "Private key material detected",
        "category": "Credentials",
        "title": "Private key material detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 1.0,
        "confidence": 1.0,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [
            r"-----begin private key-----",
            r"-----begin rsa private key-----",
        ],
    },
    {
        "rule_id": "A-004",
        "name": "Cloud provider credential detected",
        "category": "Credentials",
        "title": "Cloud provider credential detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.98,
        "confidence": 0.98,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [
            r"akia[0-9a-z]{16}",      # AWS
            r"accountkey\s*=",        # Azure
        ],
    },

    # -----------------------------
    # B — Authentication Weakening
    # -----------------------------

    {
        "rule_id": "B-001",
        "name": "Authentication disabled",
        "category": "Authentication",
        "title": "Authentication disabled",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\bauth\b\s*=\s*false", r"\bauthentication\b\s*=\s*off"],
    },
    {
        "rule_id": "B-002",
        "name": "Anonymous access enabled",
        "category": "Authentication",
        "title": "Anonymous access enabled",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"anonymous\s*=\s*true", r"allow_anonymous"],
    },
    {
        "rule_id": "B-003",
        "name": "Default credentials present",
        "category": "Authentication",
        "title": "Default credentials present",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"admin\s*:\s*admin", r"root\s*:\s*root"],
    },

    # -----------------------------
    # C — Authorization & Permissions
    # -----------------------------

    {
        "rule_id": "C-001",
        "name": "World-writable permissions detected",
        "category": "Authorization",
        "title": "World-writable permissions detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.95,
        "confidence": 0.95,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"chmod\s+777", r"permissions\s*=\s*777"],
    },
    {
        "rule_id": "C-002",
        "name": "Overly permissive access configuration",
        "category": "Authorization",
        "title": "Overly permissive access configuration",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"allow_all", r"public_access\s*=\s*true"],
    },
    {
        "rule_id": "C-003",
        "name": "Open firewall or security group rule",
        "category": "Authorization",
        "title": "Open firewall or security group rule",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.95,
        "confidence": 0.95,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"0\.0\.0\.0/0"],
    },

    # -----------------------------
    # D — Network Exposure
    # -----------------------------

    {
        "rule_id": "D-001",
        "name": "Service bound to all interfaces",
        "category": "Network",
        "title": "Service bound to all interfaces",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\b0\.0\.0\.0\b"],
    },
    {
        "rule_id": "D-002",
        "name": "Exposed administrative or database port",
        "category": "Network",
        "title": "Exposed administrative or database port",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.8,
        "confidence": 0.8,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r":22\b", r":3389\b", r":3306\b"],
    },

    # -----------------------------
    # E — Insecure Protocols
    # -----------------------------

    {
        "rule_id": "E-001",
        "name": "Insecure plaintext protocol detected",
        "category": "Transport",
        "title": "Insecure plaintext protocol detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"http://", r"ftp://", r"\btelnet\b"],
    },
    {
        "rule_id": "E-002",
        "name": "TLS/SSL verification disabled",
        "category": "Transport",
        "title": "TLS/SSL verification disabled",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.95,
        "confidence": 0.95,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"ssl_verify\s*=\s*false", r"tls\s*=\s*false"],
    },

    # -----------------------------
    # F — Cryptographic Weaknesses
    # -----------------------------

    {
        "rule_id": "F-001",
        "name": "Weak hash algorithm detected",
        "category": "Crypto",
        "title": "Weak hash algorithm detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\bmd5\b", r"\bsha1\b"],
    },
    {
        "rule_id": "F-002",
        "name": "Weak encryption algorithm detected",
        "category": "Crypto",
        "title": "Weak encryption algorithm detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\bdes\b", r"\brc4\b"],
    },
    {
        "rule_id": "F-003",
        "name": "Weak cryptographic key size detected",
        "category": "Crypto",
        "title": "Weak cryptographic key size detected",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"rsa_1024", r"key_size\s*=\s*1024"],
    },

    # -----------------------------
    # G — Debug / Test Modes
    # -----------------------------

    {
        "rule_id": "G-001",
        "name": "Debug mode enabled",
        "category": "Debug",
        "title": "Debug mode enabled",
        "default_severity_hint": "Low",
        "severity": "Low",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"debug\s*=\s*true"],
    },
    {
        "rule_id": "G-002",
        "name": "Verbose logging enabled",
        "category": "Debug",
        "title": "Verbose logging enabled",
        "default_severity_hint": "Low",
        "severity": "Low",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"verbose\s*=\s*true"],
    },
    {
        "rule_id": "G-003",
        "name": "Development or test environment indicator",
        "category": "Debug",
        "title": "Development or test environment indicator",
        "default_severity_hint": "Low",
        "severity": "Low",
        "confidence_weight": 0.8,
        "confidence": 0.8,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"env\s*=\s*dev", r"environment\s*=\s*test"],
    },

    # -----------------------------
    # H — Logging & Monitoring
    # -----------------------------

    {
        "rule_id": "H-001",
        "name": "Audit logging disabled",
        "category": "Logging",
        "title": "Audit logging disabled",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.85,
        "confidence": 0.85,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"audit\s*=\s*false"],
    },
    {
        "rule_id": "H-002",
        "name": "Security event logging disabled",
        "category": "Logging",
        "title": "Security event logging disabled",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.8,
        "confidence": 0.8,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"log_security\s*=\s*false"],
    },

    # -----------------------------
    # I — Injection Primitives
    # -----------------------------

    {
        "rule_id": "I-001",
        "name": "SQL string concatenation detected",
        "category": "Injection",
        "title": "SQL string concatenation detected",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.6,
        "confidence": 0.6,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"select\s+.*\+"],
    },
    {
        "rule_id": "I-002",
        "name": "Command execution primitive detected",
        "category": "Injection",
        "title": "Command execution primitive detected",
        "default_severity_hint": "High",
        "severity": "High",
        "confidence_weight": 0.7,
        "confidence": 0.7,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"os\.system\(", r"\beval\(", r"\bexec\("],
    },

    # -----------------------------
    # J — File Handling Risks
    # -----------------------------

    {
        "rule_id": "J-001",
        "name": "Unsafe temporary directory usage",
        "category": "Filesystem",
        "title": "Unsafe temporary directory usage",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.75,
        "confidence": 0.75,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"/tmp", r"temp/"],
    },
    {
        "rule_id": "J-002",
        "name": "Unvalidated upload directory configuration",
        "category": "Filesystem",
        "title": "Unvalidated upload directory configuration",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.8,
        "confidence": 0.8,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"upload_dir\s*="],
    },

    # -----------------------------
    # K — Dependency Risks
    # -----------------------------

    {
        "rule_id": "K-001",
        "name": "End-of-life platform or library detected",
        "category": "Dependency",
        "title": "End-of-life platform or library detected",
        "default_severity_hint": "Medium",
        "severity": "Medium",
        "confidence_weight": 0.9,
        "confidence": 0.9,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"python\s+2\.7", r"openssl\s+1\.0"],
    },

    # -----------------------------
    # L — Hygiene & Compliance
    # -----------------------------

    {
        "rule_id": "L-001",
        "name": "TODO or FIXME marker in production files",
        "category": "Hygiene",
        "title": "TODO or FIXME marker in production files",
        "default_severity_hint": "Low",
        "severity": "Low",
        "confidence_weight": 0.8,
        "confidence": 0.8,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"\btodo\b", r"\bfixme\b"],
    },
    {
        "rule_id": "L-002",
        "name": "Example or sample configuration reference",
        "category": "Hygiene",
        "title": "Example or sample configuration reference",
        "default_severity_hint": "Low",
        "severity": "Low",
        "confidence_weight": 0.75,
        "confidence": 0.75,
        "references": [],
        "applicable_file_types": ALL_FILE_TYPES,
        "patterns": [r"example_config", r"sample\.conf"],
    },
]


# ============================================================
# RULE EXECUTION ENGINE (DETERMINISTIC)
# ============================================================

def run_rules(chunks: list[dict]) -> list[dict]:
    """
    Run all rules against ingested document chunks.
    Returns findings with complete rule metadata, normalized evidence,
    and deterministic confidence scores.
    
    Evidence is structured as a list of normalized evidence entries,
    allowing multiple evidence entries per finding (Phase 8.2).
    
    Confidence scores are computed deterministically from rule metadata
    and evidence characteristics (Phase 8.3).
    
    Rules are gated by file type applicability - only rules declared
    applicable to a chunk's file type are executed (Phase 8.4).
    
    All findings are generated. Pattern-based suppression is applied
    as system-level suppression metadata (Phase 8.5). Suppression does
    not affect detection, evidence, or confidence calculation.
    """
    findings: list[dict] = []

    # Validate all rules have required metadata (structural check only)
    for rule in RULES:
        if not validate_rule_metadata(rule):
            raise ValueError(
                f"Rule {rule.get('rule_id', 'UNKNOWN')} is missing required metadata fields"
            )
        
        # Validate confidence_weight is present and valid (Phase 8.3)
        if not validate_confidence_weight(rule.get("confidence_weight")):
            raise ValueError(
                f"Rule {rule.get('rule_id', 'UNKNOWN')} has invalid or missing confidence_weight"
            )

    for chunk in chunks:
        content = chunk["content"].lower()
        
        # Normalize file type from chunk format (Phase 8.4)
        chunk_file_type = normalize_file_type(chunk.get("format"))

        for rule in RULES:
            # Gate rule execution based on file type applicability (Phase 8.4)
            if chunk_file_type not in rule.get("applicable_file_types", set()):
                continue  # Skip silently when rule is not applicable to this file type
            
            for pattern in rule["patterns"]:
                if re.search(pattern, content):
                    # Detection always runs - all findings are generated
                    # Pattern-based suppression is applied AFTER detection (Phase 8.5)
                    pattern_suppressed = is_suppressed(content)

                    # Normalize evidence to Phase 8.2 schema
                    try:
                        evidence_entry = normalize_evidence(
                            source_file=chunk["source_file"],
                            line_start=chunk["line_start"],
                            line_end=chunk["line_end"],
                            content=chunk["content"],
                            format_type=chunk.get("format", "text"),
                            timestamp=None,  # Will be generated by normalize_evidence
                            max_snippet_length=500,
                        )
                    except ValueError as e:
                        raise ValueError(
                            f"Failed to normalize evidence for chunk {chunk.get('chunk_id', 'UNKNOWN')}: {e}"
                        )

                    # Evidence is a list to support multiple entries per finding
                    evidence_list = [evidence_entry]

                    # Validate normalized evidence
                    if not validate_evidence_list(evidence_list):
                        raise ValueError(
                            f"Normalized evidence failed validation for chunk {chunk.get('chunk_id', 'UNKNOWN')}"
                        )

                    # Calculate deterministic confidence score (Phase 8.3)
                    # Suppression does NOT affect confidence calculation
                    try:
                        # Assess evidence completeness
                        evidence_completeness = assess_evidence_completeness(evidence_list)
                        
                        # Calculate confidence from rule weight, evidence count, and completeness
                        confidence_score = calculate_confidence(
                            confidence_weight=rule["confidence_weight"],
                            evidence_count=len(evidence_list),
                            evidence_completeness=evidence_completeness,
                        )
                    except ValueError as e:
                        raise ValueError(
                            f"Failed to calculate confidence for rule {rule['rule_id']}: {e}"
                        )
                    
                    # Validate computed confidence score
                    if not validate_confidence_score(confidence_score):
                        raise ValueError(
                            f"Computed confidence score {confidence_score} is out of valid range [0.0, 1.0]"
                        )

                    # Create suppression metadata (Phase 8.5)
                    # Pattern-based suppression uses "system" as suppressed_by
                    suppression_metadata = create_suppression_metadata(
                        suppressed=pattern_suppressed,
                        suppression_reason=(
                            "Matched suppression pattern"
                            if pattern_suppressed else None
                        ),
                        suppressed_by="system" if pattern_suppressed else None,
                        suppressed_at=None,  # Auto-generated
                    )

                    # Include all required rule metadata in finding
                    finding = {
                        "finding_id": str(uuid.uuid4()),
                        # Rule metadata (required fields)
                        "rule_id": rule["rule_id"],
                        "name": rule["name"],
                        "category": rule["category"],
                        "default_severity_hint": rule["default_severity_hint"],
                        "confidence_weight": rule["confidence_weight"],
                        "references": rule["references"],
                        # Deterministic confidence score (Phase 8.3)
                        "confidence_score": confidence_score,
                        # Backward compatibility fields (for UI)
                        "title": rule["title"],
                        "severity_suggested": rule["severity"],
                        "confidence": rule["confidence"],  # Legacy field for backward compatibility
                        # Suppression metadata (Phase 8.5 - explicit, reversible, auditable)
                        **suppression_metadata,
                        # Normalized evidence (Phase 8.2 - list format, unchanged by suppression)
                        "evidence": evidence_list,
                    }

                    # Validate finding has non-empty evidence
                    if not finding["evidence"]:
                        raise ValueError(
                            f"Finding {finding['finding_id']} has empty evidence list"
                        )
                    
                    # Validate suppression metadata structure
                    if not validate_suppression_metadata(finding):
                        raise ValueError(
                            f"Finding {finding['finding_id']} has invalid suppression metadata"
                        )

                    findings.append(finding)
                    break

    return findings


def run_rules_filtered(
    chunks: list[dict],
    include_suppressed: bool = False,
) -> list[dict]:
    """
    Run all rules and return filtered findings (Phase 8.5).
    
    This is a convenience wrapper around run_rules() that applies
    suppression filtering. By default, suppressed findings are excluded.
    
    Args:
        chunks: List of document chunks to analyze
        include_suppressed: If True, include suppressed findings; if False, exclude them (default)
    
    Returns:
        Filtered list of findings
    
    Note:
        All findings are generated (detection always runs). Filtering is
        applied after detection. Evidence remains unchanged.
    """
    from rules.suppression import filter_findings
    
    all_findings = run_rules(chunks)
    return filter_findings(all_findings, include_suppressed=include_suppressed)

