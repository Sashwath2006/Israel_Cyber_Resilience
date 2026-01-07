import re
import uuid

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
        "category": "Credentials",
        "title": "Hardcoded password detected",
        "severity": "High",
        "confidence": 0.95,
        "patterns": [r"\bpassword\b\s*=", r"\bpwd\b\s*="],
    },
    {
        "rule_id": "A-002",
        "category": "Credentials",
        "title": "API key or token detected",
        "severity": "High",
        "confidence": 0.95,
        "patterns": [r"\bapi[_-]?key\b\s*=", r"\btoken\b\s*="],
    },
    {
        "rule_id": "A-003",
        "category": "Credentials",
        "title": "Private key material detected",
        "severity": "High",
        "confidence": 1.0,
        "patterns": [
            r"-----begin private key-----",
            r"-----begin rsa private key-----",
        ],
    },
    {
        "rule_id": "A-004",
        "category": "Credentials",
        "title": "Cloud provider credential detected",
        "severity": "High",
        "confidence": 0.98,
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
        "category": "Authentication",
        "title": "Authentication disabled",
        "severity": "High",
        "confidence": 0.9,
        "patterns": [r"\bauth\b\s*=\s*false", r"\bauthentication\b\s*=\s*off"],
    },
    {
        "rule_id": "B-002",
        "category": "Authentication",
        "title": "Anonymous access enabled",
        "severity": "High",
        "confidence": 0.9,
        "patterns": [r"anonymous\s*=\s*true", r"allow_anonymous"],
    },
    {
        "rule_id": "B-003",
        "category": "Authentication",
        "title": "Default credentials present",
        "severity": "High",
        "confidence": 0.85,
        "patterns": [r"admin\s*:\s*admin", r"root\s*:\s*root"],
    },

    # -----------------------------
    # C — Authorization & Permissions
    # -----------------------------

    {
        "rule_id": "C-001",
        "category": "Authorization",
        "title": "World-writable permissions detected",
        "severity": "High",
        "confidence": 0.95,
        "patterns": [r"chmod\s+777", r"permissions\s*=\s*777"],
    },
    {
        "rule_id": "C-002",
        "category": "Authorization",
        "title": "Overly permissive access configuration",
        "severity": "High",
        "confidence": 0.9,
        "patterns": [r"allow_all", r"public_access\s*=\s*true"],
    },
    {
        "rule_id": "C-003",
        "category": "Authorization",
        "title": "Open firewall or security group rule",
        "severity": "High",
        "confidence": 0.95,
        "patterns": [r"0\.0\.0\.0/0"],
    },

    # -----------------------------
    # D — Network Exposure
    # -----------------------------

    {
        "rule_id": "D-001",
        "category": "Network",
        "title": "Service bound to all interfaces",
        "severity": "Medium",
        "confidence": 0.85,
        "patterns": [r"\b0\.0\.0\.0\b"],
    },
    {
        "rule_id": "D-002",
        "category": "Network",
        "title": "Exposed administrative or database port",
        "severity": "Medium",
        "confidence": 0.8,
        "patterns": [r":22\b", r":3389\b", r":3306\b"],
    },

    # -----------------------------
    # E — Insecure Protocols
    # -----------------------------

    {
        "rule_id": "E-001",
        "category": "Transport",
        "title": "Insecure plaintext protocol detected",
        "severity": "High",
        "confidence": 0.9,
        "patterns": [r"http://", r"ftp://", r"\btelnet\b"],
    },
    {
        "rule_id": "E-002",
        "category": "Transport",
        "title": "TLS/SSL verification disabled",
        "severity": "High",
        "confidence": 0.95,
        "patterns": [r"ssl_verify\s*=\s*false", r"tls\s*=\s*false"],
    },

    # -----------------------------
    # F — Cryptographic Weaknesses
    # -----------------------------

    {
        "rule_id": "F-001",
        "category": "Crypto",
        "title": "Weak hash algorithm detected",
        "severity": "High",
        "confidence": 0.85,
        "patterns": [r"\bmd5\b", r"\bsha1\b"],
    },
    {
        "rule_id": "F-002",
        "category": "Crypto",
        "title": "Weak encryption algorithm detected",
        "severity": "High",
        "confidence": 0.9,
        "patterns": [r"\bdes\b", r"\brc4\b"],
    },
    {
        "rule_id": "F-003",
        "category": "Crypto",
        "title": "Weak cryptographic key size detected",
        "severity": "Medium",
        "confidence": 0.85,
        "patterns": [r"rsa_1024", r"key_size\s*=\s*1024"],
    },

    # -----------------------------
    # G — Debug / Test Modes
    # -----------------------------

    {
        "rule_id": "G-001",
        "category": "Debug",
        "title": "Debug mode enabled",
        "severity": "Low",
        "confidence": 0.9,
        "patterns": [r"debug\s*=\s*true"],
    },
    {
        "rule_id": "G-002",
        "category": "Debug",
        "title": "Verbose logging enabled",
        "severity": "Low",
        "confidence": 0.85,
        "patterns": [r"verbose\s*=\s*true"],
    },
    {
        "rule_id": "G-003",
        "category": "Debug",
        "title": "Development or test environment indicator",
        "severity": "Low",
        "confidence": 0.8,
        "patterns": [r"env\s*=\s*dev", r"environment\s*=\s*test"],
    },

    # -----------------------------
    # H — Logging & Monitoring
    # -----------------------------

    {
        "rule_id": "H-001",
        "category": "Logging",
        "title": "Audit logging disabled",
        "severity": "Medium",
        "confidence": 0.85,
        "patterns": [r"audit\s*=\s*false"],
    },
    {
        "rule_id": "H-002",
        "category": "Logging",
        "title": "Security event logging disabled",
        "severity": "Medium",
        "confidence": 0.8,
        "patterns": [r"log_security\s*=\s*false"],
    },

    # -----------------------------
    # I — Injection Primitives
    # -----------------------------

    {
        "rule_id": "I-001",
        "category": "Injection",
        "title": "SQL string concatenation detected",
        "severity": "Medium",
        "confidence": 0.6,
        "patterns": [r"select\s+.*\+"],
    },
    {
        "rule_id": "I-002",
        "category": "Injection",
        "title": "Command execution primitive detected",
        "severity": "High",
        "confidence": 0.7,
        "patterns": [r"os\.system\(", r"\beval\(", r"\bexec\("],
    },

    # -----------------------------
    # J — File Handling Risks
    # -----------------------------

    {
        "rule_id": "J-001",
        "category": "Filesystem",
        "title": "Unsafe temporary directory usage",
        "severity": "Medium",
        "confidence": 0.75,
        "patterns": [r"/tmp", r"temp/"],
    },
    {
        "rule_id": "J-002",
        "category": "Filesystem",
        "title": "Unvalidated upload directory configuration",
        "severity": "Medium",
        "confidence": 0.8,
        "patterns": [r"upload_dir\s*="],
    },

    # -----------------------------
    # K — Dependency Risks
    # -----------------------------

    {
        "rule_id": "K-001",
        "category": "Dependency",
        "title": "End-of-life platform or library detected",
        "severity": "Medium",
        "confidence": 0.9,
        "patterns": [r"python\s+2\.7", r"openssl\s+1\.0"],
    },

    # -----------------------------
    # L — Hygiene & Compliance
    # -----------------------------

    {
        "rule_id": "L-001",
        "category": "Hygiene",
        "title": "TODO or FIXME marker in production files",
        "severity": "Low",
        "confidence": 0.8,
        "patterns": [r"\btodo\b", r"\bfixme\b"],
    },
    {
        "rule_id": "L-002",
        "category": "Hygiene",
        "title": "Example or sample configuration reference",
        "severity": "Low",
        "confidence": 0.75,
        "patterns": [r"example_config", r"sample\.conf"],
    },
]


# ============================================================
# RULE EXECUTION ENGINE (DETERMINISTIC)
# ============================================================

def run_rules(chunks: list[dict]) -> list[dict]:
    findings: list[dict] = []

    for chunk in chunks:
        content = chunk["content"].lower()

        for rule in RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, content):
                    suppressed = is_suppressed(content)

                    findings.append({
                        "finding_id": str(uuid.uuid4()),
                        "rule_id": rule["rule_id"],
                        "category": rule["category"],
                        "title": rule["title"],
                        "severity_suggested": rule["severity"],
                        "confidence": rule["confidence"],
                        "suppressed": suppressed,
                        "suppression_reason": (
                            "Matched suppression pattern"
                            if suppressed else None
                        ),
                        "evidence": {
                            "source_file": chunk["source_file"],
                            "chunk_id": chunk["chunk_id"],
                            "line_start": chunk["line_start"],
                            "line_end": chunk["line_end"],
                            "excerpt": chunk["content"][:300],
                        },
                    })
                    break

    return findings

