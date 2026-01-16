"""
Test LLM Output Validation (Phase 9)

Tests verify that validation:
- Rejects outputs with missing required fields
- Rejects outputs with invalid finding_ids
- Rejects outputs that invent vulnerabilities
- Validates schema correctly
- Fails loudly on violations
"""

from app.llm_validation import (
    validate_llm_reasoning_output,
    validate_output_does_not_invent_vulnerabilities,
    sanitize_llm_output,
)


class TestLLMOutputValidation:
    """Test LLM output validation safety."""
    
    def test_validation_rejects_missing_fields(self):
        """Verify validation rejects outputs with missing required fields."""
        output = {
            "finding_id": "test-123",
            "summary": "Test summary",
            # Missing: impact, suggested_severity, remediation, confidence_note, disclaimer
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid, "Validation should reject missing fields"
        assert "Missing required fields" in error_msg or len(error_msg) > 0
    
    def test_validation_rejects_invalid_finding_id(self):
        """Verify validation rejects outputs with mismatched finding_id."""
        output = {
            "finding_id": "wrong-id",
            "summary": "Test summary",
            "impact": "Test impact",
            "suggested_severity": "High",
            "remediation": ["Step 1"],
            "confidence_note": "Test note",
            "disclaimer": "Suggested analysis only",
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="correct-id",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid, "Validation should reject mismatched finding_id"
        assert "finding_id mismatch" in error_msg
    
    def test_validation_rejects_invalid_severity(self):
        """Verify validation rejects invalid severity values."""
        output = {
            "finding_id": "test-123",
            "summary": "Test summary",
            "impact": "Test impact",
            "suggested_severity": "Critical",  # Invalid - must be High/Medium/Low
            "remediation": ["Step 1"],
            "confidence_note": "Test note",
            "disclaimer": "Suggested analysis only",
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid, "Validation should reject invalid severity"
        assert "suggested_severity" in error_msg.lower()
    
    def test_validation_rejects_empty_remediation(self):
        """Verify validation rejects empty remediation lists."""
        output = {
            "finding_id": "test-123",
            "summary": "Test summary",
            "impact": "Test impact",
            "suggested_severity": "High",
            "remediation": [],  # Empty - should be rejected
            "confidence_note": "Test note",
            "disclaimer": "Suggested analysis only",
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid, "Validation should reject empty remediation"
        assert "remediation" in error_msg.lower()
    
    def test_validation_rejects_missing_disclaimer(self):
        """Verify validation rejects outputs without proper disclaimer."""
        output = {
            "finding_id": "test-123",
            "summary": "Test summary",
            "impact": "Test impact",
            "suggested_severity": "High",
            "remediation": ["Step 1"],
            "confidence_note": "Test note",
            "disclaimer": "",  # Empty disclaimer
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid, "Validation should reject empty disclaimer"
        assert "disclaimer" in error_msg.lower()
    
    def test_validation_accepts_valid_output(self):
        """Verify validation accepts properly formatted outputs."""
        output = {
            "finding_id": "test-123",
            "summary": "Test summary explaining the risk",
            "impact": "Generalized impact description",
            "suggested_severity": "High",
            "remediation": ["Step 1: Remove credential", "Step 2: Use secrets manager"],
            "confidence_note": "Based on rule confidence 0.95 and evidence count",
            "disclaimer": "Suggested analysis only; analyst review required",
        }
        
        is_valid, error_msg = validate_llm_reasoning_output(
            output,
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert is_valid, f"Validation should accept valid output: {error_msg}"
        assert error_msg == ""
    
    def test_validate_does_not_invent_vulnerabilities_checks_disclaimer(self):
        """Verify validation checks for required disclaimer language."""
        output = {
            "finding_id": "test-123",
            "summary": "Test",
            "impact": "Test",
            "suggested_severity": "High",
            "remediation": ["Step 1"],
            "confidence_note": "Test",
            "disclaimer": "This is definitely a vulnerability",  # Missing "suggested" or "advisory"
        }
        
        is_safe, error_msg = validate_output_does_not_invent_vulnerabilities(
            output,
            expected_rule_id="A-001",
        )
        
        assert not is_safe, "Validation should reject disclaimer without 'suggested' or 'advisory'"
        assert "disclaimer" in error_msg.lower()
    
    def test_sanitize_output_handles_strings(self):
        """Verify sanitization properly handles string fields."""
        output = {
            "finding_id": "  test-123  ",
            "summary": "  Test summary  ",
            "impact": "Test impact",
            "suggested_severity": "High",
            "remediation": ["  Step 1  ", "Step 2"],
            "confidence_note": "Test",
            "disclaimer": "Suggested only",
        }
        
        sanitized = sanitize_llm_output(output)
        
        assert sanitized["finding_id"] == "test-123"
        assert sanitized["summary"] == "Test summary"
        assert sanitized["remediation"][0] == "Step 1"
        assert sanitized["remediation"][1] == "Step 2"
    
    def test_validation_fails_loudly(self):
        """Verify validation returns clear error messages (fails loudly)."""
        # Invalid output (not a dict)
        is_valid, error_msg = validate_llm_reasoning_output(
            "not a dict",
            expected_finding_id="test-123",
            allowed_file_names={"test.txt"},
        )
        
        assert not is_valid
        assert len(error_msg) > 0, "Error message should not be empty"
        assert "dictionary" in error_msg.lower() or "dict" in error_msg.lower()
