"""
Unit Tests for Rule Engine Module

Tests for vulnerability detection, rule execution, confidence scoring, and 
suppression functionality of the rule engine.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.rule_engine import (
    run_rules,
    run_rules_filtered,
    is_suppressed,
    RULES
)


class TestRuleEngine:
    """Test suite for rule engine functionality."""
    
    def test_run_rules_detects_hardcoded_password(self):
        """Test that hardcoded passwords are detected."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "config.txt",
            "content": "database_password=secret123",
            "line_start": 1,
            "line_end": 1,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        # Should detect password pattern
        password_findings = [f for f in findings if f["rule_id"] == "A-001"]
        assert len(password_findings) > 0, "Password pattern not detected"
        
        finding = password_findings[0]
        assert finding["name"] == "Hardcoded password detected"
        assert finding["category"] == "Credentials"
        assert finding["default_severity_hint"] == "High"
        assert finding["confidence_score"] > 0.9  # High confidence for this rule
    
    def test_run_rules_detects_api_key(self):
        """Test that API keys are detected."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "config.json",
            "content": '{"api_key": "sk-1234567890abcdef"}',
            "line_start": 1,
            "line_end": 1,
            "format": "json",
        }]
        
        findings = run_rules(chunks)
        
        # Should detect API key
        api_key_findings = [f for f in findings if f["rule_id"] == "A-002"]
        assert len(api_key_findings) > 0, "API key pattern not detected"
    
    def test_run_rules_detects_private_key(self):
        """Test that private keys are detected."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "private.pem",
            "content": "-----BEGIN PRIVATE KEY-----\nsomekeydata\n-----END PRIVATE KEY-----",
            "line_start": 1,
            "line_end": 3,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        # Should detect private key
        private_key_findings = [f for f in findings if f["rule_id"] == "A-003"]
        assert len(private_key_findings) > 0, "Private key pattern not detected"
    
    def test_run_rules_no_findings_for_clean_content(self):
        """Test that clean content produces no findings."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "clean.txt",
            "content": "This is a clean file with no security issues.",
            "line_start": 1,
            "line_end": 1,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        # Should produce no findings (or only hygiene findings for common words)
        non_hygiene_findings = [f for f in findings if f["category"] != "Hygiene"]
        assert len(non_hygiene_findings) == 0, (
            f"Clean content produced unexpected findings: {[f['rule_id'] for f in non_hygiene_findings]}"
        )
    
    def test_run_rules_multiple_findings(self):
        """Test that multiple findings can be detected in one chunk."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "mixed.txt",
            "content": "password=secret123\napi_key=sk-abc123\ndebug=true",
            "line_start": 1,
            "line_end": 3,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        # Should detect multiple types of issues
        rule_ids = {f["rule_id"] for f in findings}
        expected_rules = {"A-001", "A-002", "G-001"}  # Password, API key, debug
        assert expected_rules.issubset(rule_ids), f"Expected rules {expected_rules} not found in {rule_ids}"
    
    def test_run_rules_with_file_type_filtering(self):
        """Test that rules only apply to appropriate file types."""
        # Create a chunk with JSON format
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "config.json",
            "content": "password=secret123",
            "line_start": 1,
            "line_end": 1,
            "format": "json",
        }]
        
        findings = run_rules(chunks)
        
        # Should still detect password because password rule applies to all file types
        password_findings = [f for f in findings if f["rule_id"] == "A-001"]
        assert len(password_findings) > 0, "Password should be detected in JSON file"
    
    def test_run_rules_evidence_structure(self):
        """Test that findings include proper evidence structure."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "config.txt",
            "content": "password=secret123",
            "line_start": 1,
            "line_end": 1,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        assert len(findings) > 0, "Should have at least one finding"
        finding = findings[0]
        
        # Check evidence structure
        assert "evidence" in finding
        assert isinstance(finding["evidence"], list)
        assert len(finding["evidence"]) > 0
        
        evidence = finding["evidence"][0]
        assert "file" in evidence
        assert "location" in evidence
        assert "snippet" in evidence
        assert evidence["file"] == "config.txt"


class TestSuppression:
    """Test suite for suppression functionality."""
    
    def test_suppression_patterns_match_comments(self):
        """Test that comment patterns are suppressed."""
        test_cases = [
            "# This is a commented password=password123",
            "// API key=secret123 here",
            "/* debug=true for testing */",
        ]
        
        for content in test_cases:
            assert is_suppressed(content) == True, f"Content should be suppressed: {content}"
    
    def test_suppression_patterns_match_placeholders(self):
        """Test that placeholder patterns are suppressed."""
        test_cases = [
            "password=CHANGEME",
            "api_key=your_api_key_here",
            "password=example_password",
        ]
        
        for content in test_cases:
            assert is_suppressed(content) == True, f"Content should be suppressed: {content}"
    
    def test_real_vulnerabilities_not_suppressed(self):
        """Test that actual vulnerabilities are not suppressed."""
        test_cases = [
            "password=actual_secret123",
            "api_key=real_api_key_12345",
            "debug=false in production",
        ]
        
        for content in test_cases:
            assert is_suppressed(content) == False, f"Real vulnerability should not be suppressed: {content}"
    
    def test_run_rules_filtered_include_suppressed(self):
        """Test that run_rules_filtered can include suppressed findings."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "commented.txt",
            "content": "# password=secret123 this is commented out",
            "line_start": 1,
            "line_end": 1,
            "format": "txt",
        }]
        
        # Get all findings including suppressed
        all_findings = run_rules_filtered(chunks, include_suppressed=True)
        
        # Should have findings (even if suppressed)
        assert len(all_findings) > 0
        assert all_findings[0]["suppressed"] == True
    
    def test_run_rules_filtered_exclude_suppressed(self):
        """Test that run_rules_filtered excludes suppressed findings by default."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "commented.txt",
            "content": "# password=secret123 this is commented out",
            "line_start": 1,
            "line_end": 1,
            "format": "txt",
        }]
        
        # Get only non-suppressed findings
        active_findings = run_rules_filtered(chunks, include_suppressed=False)
        
        # Should have no findings since the vulnerable content is commented
        assert len(active_findings) == 0


class TestConfidenceScoring:
    """Test suite for confidence scoring."""
    
    def test_high_confidence_for_strong_indicators(self):
        """Test that strong indicators get high confidence scores."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "keys.pem",
            "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
            "line_start": 1,
            "line_end": 3,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        private_key_findings = [f for f in findings if f["rule_id"] == "A-003"]
        
        assert len(private_key_findings) > 0
        # Private key detection should have very high confidence (1.0)
        assert private_key_findings[0]["confidence_score"] == 1.0
    
    def test_confidence_score_range(self):
        """Test that confidence scores are within valid range [0.0, 1.0]."""
        chunks = [{
            "chunk_id": "test-1",
            "source_file": "config.txt",
            "content": "password=secret123\napi_key=sk-12345",
            "line_start": 1,
            "line_end": 2,
            "format": "txt",
        }]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            confidence = finding["confidence_score"]
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} not in range [0.0, 1.0]"


class TestRuleStructure:
    """Test suite for rule structure validation."""
    
    def test_all_rules_have_required_fields(self):
        """Test that all rules have required metadata fields."""
        required_fields = {
            "rule_id", "name", "category", "default_severity_hint", 
            "confidence_weight", "references", "applicable_file_types"
        }
        
        for rule in RULES:
            for field in required_fields:
                assert field in rule, f"Rule {rule.get('rule_id', 'UNKNOWN')} missing required field: {field}"
    
    def test_all_rules_have_compiled_patterns(self):
        """Test that all rules have compiled patterns after initialization."""
        for rule in RULES:
            assert "compiled_patterns" in rule, f"Rule {rule['rule_id']} missing compiled_patterns"
            assert isinstance(rule["compiled_patterns"], list), f"Rule {rule['rule_id']} compiled_patterns not a list"


if __name__ == "__main__":
    pytest.main([__file__])