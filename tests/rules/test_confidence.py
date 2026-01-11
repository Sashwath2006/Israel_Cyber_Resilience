"""
Test Confidence Scoring (Phase 8.7)

Tests verify that confidence scoring is correct:
- Confidence exists on every finding
- Confidence ∈ [0.0, 1.0]
- Confidence is deterministic
"""

import pytest

from app.rule_engine import run_rules
from rules.confidence import validate_confidence_score


class TestConfidenceScoring:
    """Test deterministic confidence scoring."""
    
    def test_all_findings_have_confidence_score(self):
        """Verify every finding has confidence_score field."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        assert len(findings) > 0, "No findings produced"
        
        for finding in findings:
            assert "confidence_score" in finding, "Finding missing confidence_score field"
            assert isinstance(finding["confidence_score"], (int, float)), (
                "confidence_score must be numeric"
            )
    
    def test_confidence_score_in_valid_range(self):
        """Verify confidence_score is always in [0.0, 1.0]."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            confidence = finding["confidence_score"]
            assert 0.0 <= confidence <= 1.0, (
                f"confidence_score out of range [0.0, 1.0]: {confidence}"
            )
            assert validate_confidence_score(confidence), (
                f"confidence_score failed validation: {confidence}"
            )
    
    def test_confidence_score_is_deterministic(self):
        """Verify same input produces same confidence scores."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings1 = run_rules(chunks)
        findings2 = run_rules(chunks)
        
        # Sort by rule_id for comparison
        findings1_sorted = sorted(findings1, key=lambda x: x["rule_id"])
        findings2_sorted = sorted(findings2, key=lambda x: x["rule_id"])
        
        assert len(findings1_sorted) == len(findings2_sorted)
        
        for f1, f2 in zip(findings1_sorted, findings2_sorted):
            assert f1["rule_id"] == f2["rule_id"]
            assert f1["confidence_score"] == f2["confidence_score"], (
                f"Confidence score differs for rule {f1['rule_id']}: "
                f"{f1['confidence_score']} != {f2['confidence_score']}"
            )
    
    def test_confidence_score_based_on_rule_weight(self):
        """Verify confidence_score is related to rule confidence_weight."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            confidence_score = finding["confidence_score"]
            confidence_weight = finding["confidence_weight"]
            
            # Confidence score should be related to confidence_weight
            # (not necessarily equal due to evidence factors)
            # But should be in same ballpark (within reasonable bounds)
            assert confidence_score > 0.0, "confidence_score should be positive"
            # Confidence score should not exceed confidence_weight significantly
            # (it's multiplied by factors <= 1.0)
            assert confidence_score <= confidence_weight + 0.01, (
                f"confidence_score ({confidence_score}) exceeds confidence_weight "
                f"({confidence_weight}) significantly"
            )
    
    def test_confidence_score_preserved_on_suppression(self):
        """Verify suppression does not affect confidence_score."""
        # Content that triggers both detection and suppression
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123  # Commented out",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Should still have confidence_score even if suppressed
        for finding in findings:
            assert "confidence_score" in finding, "Suppressed finding missing confidence_score"
            assert 0.0 <= finding["confidence_score"] <= 1.0, (
                "Suppressed finding has invalid confidence_score"
            )
