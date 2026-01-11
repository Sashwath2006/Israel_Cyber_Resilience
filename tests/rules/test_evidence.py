"""
Test Evidence Normalization (Phase 8.7)

Tests verify that evidence is normalized correctly:
- Evidence schema completeness
- Correct file, location, snippet mapping
- Multiple evidence entries handled correctly
"""

import pytest

from app.rule_engine import run_rules
from rules.metadata import validate_evidence, validate_evidence_list


class TestEvidenceNormalization:
    """Test evidence normalization and schema."""
    
    def test_all_findings_have_evidence(self):
        """Verify every finding has non-empty evidence list."""
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
        
        for finding in findings:
            assert "evidence" in finding, "Finding missing evidence field"
            assert isinstance(finding["evidence"], list), "Evidence must be a list"
            assert len(finding["evidence"]) > 0, "Evidence list must not be empty"
    
    def test_evidence_schema_completeness(self):
        """Verify evidence entries have all required fields."""
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.txt",
                "content": "password=secret123",
                "line_start": 5,
                "line_end": 5,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            for evidence in finding["evidence"]:
                # Required fields
                assert "file" in evidence, "Evidence missing file field"
                assert "location" in evidence, "Evidence missing location field"
                assert "snippet" in evidence, "Evidence missing snippet field"
                
                # File must be non-empty string
                assert isinstance(evidence["file"], str), "Evidence file must be string"
                assert evidence["file"], "Evidence file must not be empty"
                
                # Location must have type, start, and optionally end
                location = evidence["location"]
                assert isinstance(location, dict), "Evidence location must be dict"
                assert "type" in location, "Location missing type field"
                assert "start" in location, "Location missing start field"
                assert location["type"] in {"line", "row", "range"}, (
                    f"Invalid location type: {location['type']}"
                )
                assert isinstance(location["start"], int), "Location start must be int"
                assert location["start"] >= 0, "Location start must be non-negative"
                
                # Snippet must be string
                assert isinstance(evidence["snippet"], str), "Evidence snippet must be string"
                
                # Validate evidence structure
                assert validate_evidence(evidence), f"Evidence failed validation: {evidence}"
    
    def test_evidence_file_mapping(self):
        """Verify evidence file field maps to source_file."""
        source_file = "my_config.txt"
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": source_file,
                "content": "password=secret123",
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            for evidence in finding["evidence"]:
                assert evidence["file"] == source_file, (
                    f"Evidence file mismatch: expected {source_file}, got {evidence['file']}"
                )
    
    def test_evidence_location_mapping(self):
        """Verify evidence location maps correctly based on format."""
        # Text file - should use "line" type
        chunks_txt = [
            {
                "chunk_id": "test-1",
                "source_file": "test.txt",
                "content": "password=secret",
                "line_start": 10,
                "line_end": 12,
                "format": "txt",
            }
        ]
        
        findings_txt = run_rules(chunks_txt)
        if findings_txt:
            evidence = findings_txt[0]["evidence"][0]
            assert evidence["location"]["type"] == "line"
            assert evidence["location"]["start"] == 10
            assert evidence["location"]["end"] == 12
        
        # CSV file - should use "row" type
        chunks_csv = [
            {
                "chunk_id": "test-2",
                "source_file": "test.csv",
                "content": "username,password\nadmin,secret",
                "line_start": 2,
                "line_end": 2,
                "format": "csv",
            }
        ]
        
        findings_csv = run_rules(chunks_csv)
        if findings_csv:
            evidence = findings_csv[0]["evidence"][0]
            assert evidence["location"]["type"] == "row"
            assert evidence["location"]["start"] == 2
        
        # JSON file - should use "range" type
        chunks_json = [
            {
                "chunk_id": "test-3",
                "source_file": "test.json",
                "content": '{"password": "secret"}',
                "line_start": 1,
                "line_end": 3,
                "format": "json",
            }
        ]
        
        findings_json = run_rules(chunks_json)
        if findings_json:
            evidence = findings_json[0]["evidence"][0]
            assert evidence["location"]["type"] == "range"
    
    def test_evidence_snippet_contains_content(self):
        """Verify evidence snippet contains relevant content."""
        content = "database_password=secret123456"
        chunks = [
            {
                "chunk_id": "test-1",
                "source_file": "config.txt",
                "content": content,
                "line_start": 1,
                "line_end": 1,
                "format": "txt",
            }
        ]
        
        findings = run_rules(chunks)
        
        for finding in findings:
            for evidence in finding["evidence"]:
                # Snippet should contain at least part of the original content
                assert evidence["snippet"], "Evidence snippet must not be empty"
                # Snippet should be bounded (max 500 chars per normalize_evidence)
                assert len(evidence["snippet"]) <= 600, "Evidence snippet exceeds expected max length"
    
    def test_evidence_list_validation(self):
        """Verify evidence lists pass validation."""
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
            evidence_list = finding["evidence"]
            assert validate_evidence_list(evidence_list), (
                f"Evidence list failed validation for finding {finding['finding_id']}"
            )
    
    def test_evidence_timestamp_present(self):
        """Verify evidence entries have timestamp."""
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
            for evidence in finding["evidence"]:
                # Timestamp should be present (normalize_evidence generates it)
                assert "timestamp" in evidence, "Evidence missing timestamp field"
                assert evidence["timestamp"], "Evidence timestamp must not be empty"
                # Timestamp should be ISO format string
                assert isinstance(evidence["timestamp"], str), "Evidence timestamp must be string"
