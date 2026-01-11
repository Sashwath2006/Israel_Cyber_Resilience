"""
Test Rule Metadata Validation (Phase 8.7)

Tests verify that all rules have required metadata fields
and that missing metadata raises explicit errors.
"""

from app.rule_engine import RULES
from rules.metadata import validate_rule_metadata, SUPPORTED_FILE_TYPES


class TestRuleMetadata:
    """Test rule metadata structure and validation."""
    
    def test_all_rules_have_required_metadata(self):
        """Verify every rule has all required metadata fields."""
        required_fields = {
            "rule_id",
            "name",
            "category",
            "default_severity_hint",
            "confidence_weight",
            "references",
            "applicable_file_types",
        }
        
        for rule in RULES:
            rule_id = rule.get("rule_id", "UNKNOWN")
            
            # Check all required fields are present
            for field in required_fields:
                assert field in rule, f"Rule {rule_id} missing required field: {field}"
            
            # Verify rule_id is non-empty
            assert rule["rule_id"], f"Rule {rule_id} has empty rule_id"
            
            # Verify name is non-empty
            assert rule["name"], f"Rule {rule_id} has empty name"
            
            # Verify category is non-empty
            assert rule["category"], f"Rule {rule_id} has empty category"
            
            # Verify default_severity_hint is valid
            valid_severities = {"Low", "Medium", "High", "Critical"}
            assert rule["default_severity_hint"] in valid_severities, (
                f"Rule {rule_id} has invalid default_severity_hint: {rule['default_severity_hint']}"
            )
            
            # Verify confidence_weight is in valid range
            assert isinstance(rule["confidence_weight"], (int, float)), (
                f"Rule {rule_id} confidence_weight must be numeric"
            )
            assert 0.0 <= rule["confidence_weight"] <= 1.0, (
                f"Rule {rule_id} confidence_weight out of range [0.0, 1.0]: {rule['confidence_weight']}"
            )
            
            # Verify references is a list
            assert isinstance(rule["references"], list), (
                f"Rule {rule_id} references must be a list"
            )
            
            # Verify applicable_file_types is a set and contains only supported types
            assert isinstance(rule["applicable_file_types"], (set, list, tuple)), (
                f"Rule {rule_id} applicable_file_types must be a set, list, or tuple"
            )
            applicable_set = set(rule["applicable_file_types"])
            assert len(applicable_set) > 0, (
                f"Rule {rule_id} applicable_file_types must not be empty"
            )
            assert applicable_set.issubset(SUPPORTED_FILE_TYPES), (
                f"Rule {rule_id} applicable_file_types contains unsupported types: "
                f"{applicable_set - SUPPORTED_FILE_TYPES}"
            )
    
    def test_validate_rule_metadata_passes_for_valid_rules(self):
        """Verify validate_rule_metadata returns True for all rules."""
        for rule in RULES:
            assert validate_rule_metadata(rule), (
                f"Rule {rule.get('rule_id', 'UNKNOWN')} failed metadata validation"
            )
    
    def test_validate_rule_metadata_fails_for_missing_fields(self):
        """Verify validate_rule_metadata returns False for invalid rules."""
        # Rule missing required field
        invalid_rule = {
            "rule_id": "TEST-001",
            "name": "Test rule",
            "category": "Test",
            # Missing default_severity_hint
            "confidence_weight": 0.9,
            "references": [],
            "applicable_file_types": {"text"},
        }
        
        assert not validate_rule_metadata(invalid_rule)
    
    def test_validate_rule_metadata_fails_for_invalid_file_types(self):
        """Verify validate_rule_metadata fails for unsupported file types."""
        invalid_rule = {
            "rule_id": "TEST-002",
            "name": "Test rule",
            "category": "Test",
            "default_severity_hint": "Low",
            "confidence_weight": 0.9,
            "references": [],
            "applicable_file_types": {"unsupported_type"},  # Invalid
        }
        
        assert not validate_rule_metadata(invalid_rule)
    
    def test_all_rules_have_patterns(self):
        """Verify every rule has at least one pattern."""
        for rule in RULES:
            rule_id = rule.get("rule_id", "UNKNOWN")
            assert "patterns" in rule, f"Rule {rule_id} missing patterns field"
            assert len(rule["patterns"]) > 0, f"Rule {rule_id} has no patterns"
            assert isinstance(rule["patterns"], list), f"Rule {rule_id} patterns must be a list"
    
    def test_all_rules_have_compiled_patterns(self):
        """Verify every rule has compiled_patterns (Phase 8.6 optimization)."""
        for rule in RULES:
            rule_id = rule.get("rule_id", "UNKNOWN")
            assert "compiled_patterns" in rule, (
                f"Rule {rule_id} missing compiled_patterns (Phase 8.6)"
            )
            assert len(rule["compiled_patterns"]) == len(rule["patterns"]), (
                f"Rule {rule_id} compiled_patterns count doesn't match patterns count"
            )
