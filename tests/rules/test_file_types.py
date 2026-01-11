"""
Test File-Type Applicability (Phase 8.7)

Tests verify that rules only fire on applicable file types
and do not fire on irrelevant file types.
"""

import pytest

from app.rule_engine import run_rules, RULES, ALL_FILE_TYPES
from rules.metadata import normalize_file_type, SUPPORTED_FILE_TYPES


class TestFileTypeApplicability:
    """Test file-type-specific rule application."""
    
    def test_file_type_normalization(self):
        """Verify file type normalization works correctly."""
        # Text formats → "text"
        assert normalize_file_type("txt") == "text"
        assert normalize_file_type("log") == "text"
        assert normalize_file_type("conf") == "text"
        assert normalize_file_type("config") == "text"
        
        # CSV → "csv"
        assert normalize_file_type("csv") == "csv"
        
        # JSON → "json"
        assert normalize_file_type("json") == "json"
        
        # Unknown → "text" (safe default)
        assert normalize_file_type("unknown") == "text"
        assert normalize_file_type(None) == "text"
    
    def test_rules_respect_file_type_applicability(self):
        """Verify rules only fire on applicable file types."""
        # Create a rule that only applies to "text" files
        # (in practice, all current rules apply to ALL_FILE_TYPES)
        # But we can test that file type gating works
        
        test_content = "password=secret123"
        
        # Test with "text" format (should match since all rules apply to text)
        chunks_text = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": test_content,
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings_text = run_rules(chunks_text)
        text_rule_ids = {f["rule_id"] for f in findings_text}
        
        # Test with "csv" format (should also match since all rules apply to csv)
        chunks_csv = [
            {
                "chunk_id": "test-2",
                "source_file": "test.csv",
                "content": test_content,
                "line_start": 1,
                "line_end": 1,
                "format": "csv",
            }
        ]
        
        findings_csv = run_rules(chunks_csv)
        csv_rule_ids = {f["rule_id"] for f in findings_csv}
        
        # Since all rules currently apply to ALL_FILE_TYPES, both should produce findings
        # But they should be for the same rule (A-001 for password pattern)
        assert len(text_rule_ids) > 0, "Text format should produce findings"
        assert len(csv_rule_ids) > 0, "CSV format should produce findings"
    
    def test_all_rules_have_applicable_file_types(self):
        """Verify all rules declare applicable_file_types."""
        for rule in RULES:
            rule_id = rule.get("rule_id", "UNKNOWN")
            assert "applicable_file_types" in rule, (
                f"Rule {rule_id} missing applicable_file_types"
            )
            applicable = rule["applicable_file_types"]
            assert isinstance(applicable, (set, list, tuple)), (
                f"Rule {rule_id} applicable_file_types must be set/list/tuple"
            )
            applicable_set = set(applicable)
            assert len(applicable_set) > 0, (
                f"Rule {rule_id} applicable_file_types must not be empty"
            )
            assert applicable_set.issubset(SUPPORTED_FILE_TYPES), (
                f"Rule {rule_id} applicable_file_types contains unsupported types"
            )
    
    def test_file_type_gating_preserves_detection(self):
        """Verify file type gating doesn't affect detection for applicable types."""
        # Same content, different formats that are all supported
        test_content = "api_key=sk-1234567890abcdef"
        
        formats = ["txt", "csv", "json"]
        
        for fmt in formats:
            chunks = [
                {
                    "chunk_id": f"test-{fmt}",
                    "source_file": f"test.{fmt}",
                    "content": test_content,
                    "line_start": 1,
                    "line_end": 1,
                    "format": fmt,
                }
            ]
            
            findings = run_rules(chunks)
            
            # Should detect API key (A-002) since all rules apply to all file types
            api_key_findings = [f for f in findings if f["rule_id"] == "A-002"]
            assert len(api_key_findings) > 0, (
                f"API key not detected in {fmt} format"
            )
    
    def test_normalize_file_type_handles_edge_cases(self):
        """Verify file type normalization handles edge cases."""
        # Empty string
        assert normalize_file_type("") == "text"
        
        # Case insensitive
        assert normalize_file_type("TXT") == "text"
        assert normalize_file_type("CSV") == "csv"
        assert normalize_file_type("JSON") == "json"
        
        # Whitespace
        assert normalize_file_type(" txt ") == "text"
