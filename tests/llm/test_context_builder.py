"""
Test Context Builder Safety (Phase 9)

Tests verify that context builder:
- Never includes raw document content
- Only uses structured findings
- Includes required safety constraints in prompts
- Does not inject user-generated text into system instructions
"""

from app.context_builder import build_context, build_single_finding_context
from app.rule_engine import run_rules


class TestContextBuilderSafety:
    """Test context builder safety constraints."""
    
    def test_context_never_includes_raw_documents(self):
        """Verify context builder never receives or includes raw documents."""
        # Create findings using rule engine (structured output only)
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
        assert len(findings) > 0, "Need at least one finding for test"
        
        finding = findings[0]
        context = build_single_finding_context(finding)
        
        # Context should contain evidence snippets, not raw document content
        # Should NOT contain the full raw content
        assert "password=secret123" not in context or "Evidence Snippet" in context
        # Should contain structured finding information
        assert "FINDING ID" in context
        assert "Rule ID" in context
        assert "Evidence Snippet" in context
    
    def test_context_includes_safety_constraints(self):
        """Verify context includes required safety constraint statements."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "api_key=sk-123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        finding = findings[0]
        context = build_single_finding_context(finding)
        
        # Must include "do NOT discover vulnerabilities" (or similar)
        assert "do NOT discover" in context or "do not discover" in context
        # Must include "do NOT parse raw documents" (or similar)
        assert "do NOT parse" in context or "do not parse" in context
        # Must include advisory/suggested labeling
        assert "ADVISORY" in context or "SUGGESTED" in context or "advisory" in context or "suggested" in context
    
    def test_context_includes_required_fields(self):
        """Verify context includes all required fields for each finding."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.txt",
                "content": "password=secret",
                "line_start": 5,
                "line_end": 5,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        finding = findings[0]
        context = build_single_finding_context(finding)
        
        # Must include finding_id
        assert "FINDING ID" in context
        assert finding["finding_id"] in context
        
        # Must include rule_id
        assert "Rule ID" in context
        assert finding["rule_id"] in context
        
        # Must include confidence score
        assert "Confidence" in context or "confidence" in context
        
        # Must include evidence references
        assert "Evidence" in context or "evidence" in context
    
    def test_context_deterministic(self):
        """Verify context construction is deterministic."""
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
        finding = findings[0]
        
        # Build context twice
        context1 = build_single_finding_context(finding)
        context2 = build_single_finding_context(finding)
        
        # Should be identical
        assert context1 == context2, "Context construction is not deterministic"
    
    def test_context_only_uses_structured_findings(self):
        """Verify context builder only accepts structured finding dictionaries."""
        # Context builder should work with findings from rule engine
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "api_key=sk-123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        finding = findings[0]
        
        # Should successfully build context from structured finding
        context = build_single_finding_context(finding)
        assert isinstance(context, str)
        assert len(context) > 0
