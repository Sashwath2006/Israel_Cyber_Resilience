"""
Test Detection Determinism (Phase 8.7)

Tests verify that detection is deterministic:
- Same input → same findings
- Same ordering
- Same evidence
"""

import pytest

from app.rule_engine import run_rules


class TestDetectionDeterminism:
    """Test that rule detection is deterministic."""
    
    def test_same_input_produces_same_findings(self):
        """Verify same input produces identical findings."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123\napi_key=sk-abc123",
                "line_start": 1,
                "line_end": 2,
                "format": "txt",
            }
        ]
        
        # Run twice with same input
        findings1 = run_rules(chunks)
        findings2 = run_rules(chunks)
        
        # Should produce same number of findings
        assert len(findings1) == len(findings2), "Findings count differs between runs"
        
        # Should produce same findings (excluding finding_id and timestamp which vary)
        # Sort by rule_id for comparison
        findings1_sorted = sorted(findings1, key=lambda x: x["rule_id"])
        findings2_sorted = sorted(findings2, key=lambda x: x["rule_id"])
        
        assert len(findings1_sorted) == len(findings2_sorted)
        
        for f1, f2 in zip(findings1_sorted, findings2_sorted):
            # Compare all fields except finding_id and timestamp fields
            assert f1["rule_id"] == f2["rule_id"]
            assert f1["name"] == f2["name"]
            assert f1["category"] == f2["category"]
            assert f1["confidence_score"] == f2["confidence_score"]
            assert f1["suppressed"] == f2["suppressed"]
            
            # Compare evidence (excluding timestamp)
            assert len(f1["evidence"]) == len(f2["evidence"])
            for e1, e2 in zip(f1["evidence"], f2["evidence"]):
                assert e1["file"] == e2["file"]
                assert e1["location"] == e2["location"]
                assert e1["snippet"] == e2["snippet"]
    
    def test_password_detection(self):
        """Verify password pattern is detected."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.txt",
                "content": "database_password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Should detect password
        password_findings = [f for f in findings if f["rule_id"] == "A-001"]
        assert len(password_findings) > 0, "Password pattern not detected"
        
        finding = password_findings[0]
        assert finding["name"] == "Hardcoded password detected"
        assert finding["category"] == "Credentials"
        assert finding["default_severity_hint"] == "High"
    
    def test_api_key_detection(self):
        """Verify API key pattern is detected."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.json",
                "content": '{"api_key": "sk-1234567890abcdef"}',
                "line_start": 1,
                "line_end": 1,
                "format": "json",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Should detect API key
        api_key_findings = [f for f in findings if f["rule_id"] == "A-002"]
        assert len(api_key_findings) > 0, "API key pattern not detected"
    
    def test_no_false_positives_on_clean_content(self):
        """Verify clean content produces no findings."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "clean.txt",
                "content": "This is a clean file with no security issues.",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Should produce no findings (or only hygiene findings for common words)
        # Filter out hygiene rules which may match common words
        non_hygiene_findings = [f for f in findings if f["category"] != "Hygiene"]
        assert len(non_hygiene_findings) == 0, (
            f"Clean content produced unexpected findings: {[f['rule_id'] for f in non_hygiene_findings]}"
        )
    
    def test_finding_order_is_deterministic(self):
        """Verify findings are produced in deterministic order."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret\napi_key=sk-123\ndebug=true",
                "line_start": 1,
                "line_end": 3,
                "format": "txt",
            }
        ]
        
        findings1 = run_rules(chunks)
        findings2 = run_rules(chunks)
        
        # Extract rule_ids in order
        rule_ids1 = [f["rule_id"] for f in findings1]
        rule_ids2 = [f["rule_id"] for f in findings2]
        
        # Order should be identical
        assert rule_ids1 == rule_ids2, "Finding order differs between runs"
    
    def test_empty_chunks_list_produces_no_findings(self):
        """Verify empty chunks list produces empty findings list."""
        chunks = []
        
        findings = run_rules(chunks)
        
        assert isinstance(findings, list), "Findings should be a list"
        assert len(findings) == 0, "Empty chunks should produce no findings"