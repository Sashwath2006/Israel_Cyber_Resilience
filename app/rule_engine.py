import re
import uuid


RULES = [
    {
        "rule_id": "R-001",
        "title": "Hardcoded credential detected",
        "severity": "High",
        "patterns": [
            r"\bpassword\b\s*=",
            r"api[_-]?key\s*=",
            r"secret\s*=",
        ],
    },
    {
        "rule_id": "R-004",
        "title": "Debug or verbose logging enabled",
        "severity": "Low",
        "patterns": [
            r"debug\s*=\s*true",
            r"verbose\s*=\s*true",
        ],
    },
]


def run_rules(chunks: list[dict]) -> list[dict]:
    findings: list[dict] = []

    for chunk in chunks:
        content = chunk["content"].lower()

        for rule in RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, content):
                    findings.append({
                        "finding_id": str(uuid.uuid4()),
                        "rule_id": rule["rule_id"],
                        "title": rule["title"],
                        "severity_suggested": rule["severity"],
                        "confidence": 0.9,
                        "evidence": {
                            "source_file": chunk["source_file"],
                            "chunk_id": chunk["chunk_id"],
                            "line_start": chunk["line_start"],
                            "line_end": chunk["line_end"],
                            "excerpt": content[:300],
                        },
                    })
                    break

    return findings
