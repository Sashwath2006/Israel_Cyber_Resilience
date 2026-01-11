"""
Test Suppression Handling (Phase 8.7)

Tests verify that suppression works correctly:
- Suppressed findings are hidden by default
- Suppressed findings can be retrieved
- Evidence remains intact
- Unsuppress restores visibility
"""

import pytest

from app.rule_engine import run_rules, run_rules_filtered
from rules.suppression import (
    suppress_finding,
    unsuppress_finding,
    filter_findings,
    validate_suppression_metadata,
)


class TestSuppressionHandling:
    """Test suppression and false-positive handling."""
    
    def test_suppressed_findings_have_metadata(self):
        """Verify suppressed findings have suppression metadata."""
        # Content that triggers suppression (commented line)
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Should have findings (detection always runs)
        assert len(findings) > 0, "No findings produced"
        
        # Check for suppressed findings
        suppressed_findings = [f for f in findings if f.get("suppressed")]
        
        if suppressed_findings:
            for finding in suppressed_findings:
                assert finding["suppressed"] is True
                assert finding.get("suppression_reason"), (
                    "Suppressed finding missing suppression_reason"
                )
                assert finding.get("suppressed_by") in {"user", "system"}, (
                    f"Invalid suppressed_by: {finding.get('suppressed_by')}"
                )
                assert finding.get("suppressed_at"), (
                    "Suppressed finding missing suppressed_at timestamp"
                )
                assert validate_suppression_metadata(finding), (
                    "Suppressed finding has invalid suppression metadata"
                )
    
    def test_unsuppressed_findings_have_no_suppression_metadata(self):
        """Verify unsuppressed findings have suppression=False."""
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
        
        unsuppressed_findings = [f for f in findings if not f.get("suppressed")]
        
        for finding in unsuppressed_findings:
            assert finding["suppressed"] is False
            assert finding.get("suppression_reason") is None
            assert finding.get("suppressed_by") is None
            assert finding.get("suppressed_at") is None
            assert validate_suppression_metadata(finding), (
                "Unsuppressed finding has invalid suppression metadata"
            )
    
    def test_filter_findings_excludes_suppressed_by_default(self):
        """Verify filter_findings excludes suppressed findings by default."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123\napi_key=sk-123",
                "line_start": 1,
                "line_end": 2,
                "format": "txt",
            }
        ]
        
        all_findings = run_rules(chunks)
        
        # Filter should exclude suppressed by default
        filtered_findings = filter_findings(all_findings, include_suppressed=False)
        
        # Should have fewer or equal findings
        assert len(filtered_findings) <= len(all_findings)
        
        # Filtered findings should not contain suppressed ones
        for finding in filtered_findings:
            assert not finding.get("suppressed"), (
                "Filtered findings should not contain suppressed findings"
            )
    
    def test_filter_findings_includes_suppressed_when_requested(self):
        """Verify filter_findings includes suppressed when include_suppressed=True."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        all_findings = run_rules(chunks)
        
        # Filter should include all when include_suppressed=True
        filtered_findings = filter_findings(all_findings, include_suppressed=True)
        
        # Should have same count
        assert len(filtered_findings) == len(all_findings)
        
        # Should contain all findings including suppressed
        finding_ids_all = {f["finding_id"] for f in all_findings}
        finding_ids_filtered = {f["finding_id"] for f in filtered_findings}
        assert finding_ids_all == finding_ids_filtered
    
    def test_suppress_finding_preserves_evidence(self):
        """Verify suppress_finding preserves evidence."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret123",
                "line_start": 10,
                "line_end": 10,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        assert len(findings) > 0, "No findings produced"
        
        finding = findings[0]
        original_evidence = finding["evidence"].copy()
        
        # Suppress the finding
        suppressed_finding = suppress_finding(finding, "Test suppression", "user")
        
        # Evidence should be unchanged
        assert suppressed_finding["evidence"] == original_evidence, (
            "Suppression should not modify evidence"
        )
        
        # Suppression metadata should be added
        assert suppressed_finding["suppressed"] is True
        assert suppressed_finding["suppression_reason"] == "Test suppression"
        assert suppressed_finding["suppressed_by"] == "user"
    
    def test_unsuppress_finding_restores_visibility(self):
        """Verify unsuppress_finding removes suppression."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        # Find a suppressed finding
        suppressed_findings = [f for f in findings if f.get("suppressed")]
        
        if suppressed_findings:
            suppressed = suppressed_findings[0]
            original_evidence = suppressed["evidence"].copy()
            
            # Unsuppress
            unsuppressed = unsuppress_finding(suppressed)
            
            # Should be unsuppressed
            assert unsuppressed["suppressed"] is False
            assert unsuppressed.get("suppression_reason") is None
            assert unsuppressed.get("suppressed_by") is None
            assert unsuppressed.get("suppressed_at") is None
            
            # Evidence should be unchanged
            assert unsuppressed["evidence"] == original_evidence, (
                "Unsuppression should not modify evidence"
            )
    
    def test_suppression_does_not_affect_evidence(self):
        """Verify suppression does not modify evidence structure."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.txt",
                "content": "# password=secret123",
                "line_start": 5,
                "line_end": 5,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            # Evidence should be present regardless of suppression
            assert "evidence" in finding, "Finding missing evidence"
            assert len(finding["evidence"]) > 0, "Finding has empty evidence"
            
            for evidence in finding["evidence"]:
                # Evidence fields should be complete
                assert "file" in evidence
                assert "location" in evidence
                assert "snippet" in evidence
                assert "timestamp" in evidence
                
                # Evidence content should not be modified
                assert evidence["file"] == "config.txt"
                assert evidence["location"]["start"] == 5
    
    def test_run_rules_filtered_excludes_suppressed_by_default(self):
        """Verify run_rules_filtered excludes suppressed findings by default."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123\napi_key=sk-123",
                "line_start": 1,
                "line_end": 2,
                "format": "txt",
            }
        ]
        
        # Default behavior: exclude suppressed
        filtered_findings = run_rules_filtered(chunks, include_suppressed=False)
        
        # Should not contain suppressed findings
        for finding in filtered_findings:
            assert not finding.get("suppressed"), (
                "run_rules_filtered should exclude suppressed findings by default"
            )
    
    def test_run_rules_filtered_includes_suppressed_when_requested(self):
        """Verify run_rules_filtered includes suppressed when include_suppressed=True."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "# password=secret123\napi_key=sk-123",
                "line_start": 1,
                "line_end": 2,
                "format": "txt",
            }
        ]
        
        # Get all findings (including suppressed)
        all_findings = run_rules(chunks)
        
        # Get filtered findings with include_suppressed=True
        filtered_findings = run_rules_filtered(chunks, include_suppressed=True)
        
        # Should have same count
        assert len(filtered_findings) == len(all_findings), (
            "run_rules_filtered(include_suppressed=True) should return all findings"
        )
        
        # Should contain all findings including suppressed
        finding_ids_all = {f["finding_id"] for f in all_findings}
        finding_ids_filtered = {f["finding_id"] for f in filtered_findings}
        assert finding_ids_all == finding_ids_filtered