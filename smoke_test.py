#!/usr/bin/env python3
"""
Smoke Tests: Verify core functionality works end-to-end
Tests: Ingestion -> Detection -> Report -> Export pipeline
"""

import os
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.document_ingestion import ingest_file
from app.rule_engine import run_rules
from app.finding_integration import enhance_findings_with_severity_fields
from app.report_generator import generate_sample_report
from app.report_exporter import export_to_markdown, export_to_pdf
from app.report_model import ReportWorkspace
from app.llm_reasoner import explain_single_finding
from app.ollama_client import is_ollama_available


def test_file_ingestion():
    """Test 1: Document ingestion works with sample files"""
    print("\n[TEST 1] Document Ingestion")
    
    test_files = [
        "test_files/01_harcoded_credentials.txt",
        "test_files/02_debug_logging.conf",
        "test_files/03_clean_config.txt",
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"  [SKIP] {test_file} not found")
            continue
            
        try:
            chunks = ingest_file(test_file)
            print(f"  [OK] {test_file}: {len(chunks)} chunks")
            if chunks:
                print(f"       First chunk preview: {chunks[0].get('content', '')[:60]}...")
            return chunks
        except Exception as e:
            print(f"  [ERROR] {test_file}: {str(e)}")
            return []
    
    print("  [SKIP] No test files available")
    return []


def test_rule_detection(chunks):
    """Test 2: Rule detection works on ingested chunks"""
    print("\n[TEST 2] Rule Detection Engine")
    
    if not chunks:
        print("  [SKIP] No chunks from ingestion")
        return []
    
    try:
        findings = run_rules(chunks)
        print(f"  [OK] Detection complete: {len(findings)} findings")
        
        if findings:
            for i, f in enumerate(findings[:3], 1):
                print(f"       Finding {i}: {f.get('rule_id', 'UNKNOWN')} - {f.get('title', 'Unknown')}")
        
        return findings
    except Exception as e:
        print(f"  [ERROR] Detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_finding_enhancement(findings):
    """Test 3: Finding enhancement with severity fields"""
    print("\n[TEST 3] Finding Enhancement")
    
    if not findings:
        print("  [SKIP] No findings to enhance")
        return []
    
    try:
        enhanced = enhance_findings_with_severity_fields(findings)
        print(f"  [OK] Enhanced {len(enhanced)} findings")
        
        if enhanced:
            sample = enhanced[0]
            print(f"       Sample finding has severity: {sample.get('final_severity', 'UNKNOWN')}")
        
        return enhanced
    except Exception as e:
        print(f"  [ERROR] Enhancement failed: {str(e)}")
        return []


def test_report_generation(enhanced_findings):
    """Test 4: Report generation works"""
    print("\n[TEST 4] Report Generation")
    
    if not enhanced_findings:
        print("  [OK] Report generation handles empty findings")
        # Test with empty findings
        findings = []
    else:
        findings = enhanced_findings[:5]  # Test with up to 5 findings
    
    try:
        report_data = generate_sample_report(
            findings=findings,
            scope="Smoke Test Analysis",
            model_id=None,  # Don't use LLM for smoke test
        )
        
        print(f"  [OK] Report generated")
        print(f"       Findings in report: {len(report_data.get('findings', []))}")
        print(f"       Executive summary length: {len(report_data.get('executive_summary', ''))}")
        
        return report_data
    except Exception as e:
        print(f"  [ERROR] Report generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_markdown_export(report_data):
    """Test 5: Markdown export works"""
    print("\n[TEST 5] Markdown Export")
    
    if not report_data:
        print("  [SKIP] No report data")
        return False
    
    try:
        # Create temporary workspace
        workspace = ReportWorkspace(
            scope=report_data.get("scope", "Test"),
            analyst_name="Test Analyst",
            executive_summary=report_data.get("executive_summary", ""),
        )
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name
        
        success, error = export_to_markdown(report_data, workspace, temp_path)
        
        if success:
            file_size = os.path.getsize(temp_path)
            print(f"  [OK] Markdown exported: {file_size} bytes")
            os.unlink(temp_path)
            return True
        else:
            print(f"  [ERROR] Markdown export failed: {error}")
            return False
    except Exception as e:
        print(f"  [ERROR] Markdown export exception: {str(e)}")
        return False


def test_pdf_export(report_data):
    """Test 6: PDF export works (or gracefully fails)"""
    print("\n[TEST 6] PDF Export")
    
    if not report_data:
        print("  [SKIP] No report data")
        return False
    
    try:
        # Create temporary workspace
        workspace = ReportWorkspace(
            scope=report_data.get("scope", "Test"),
            analyst_name="Test Analyst",
            executive_summary=report_data.get("executive_summary", ""),
        )
        
        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        success, error = export_to_pdf(report_data, workspace, temp_path)
        
        if success:
            file_size = os.path.getsize(temp_path)
            print(f"  [OK] PDF exported: {file_size} bytes")
            os.unlink(temp_path)
            return True
        else:
            print(f"  [WARNING] PDF export failed (acceptable): {error[:80]}...")
            # Clean up temp markdown file if created
            try:
                md_path = temp_path.replace('.pdf', '_temp.md')
                if os.path.exists(md_path):
                    os.unlink(md_path)
            except:
                pass
            return False
    except Exception as e:
        print(f"  [ERROR] PDF export exception: {str(e)}")
        return False


def test_ollama_availability():
    """Test 7: Check Ollama integration (non-blocking)"""
    print("\n[TEST 7] Ollama Integration")
    
    try:
        available = is_ollama_available(timeout=1.0)
        if available:
            print("  [OK] Ollama is available at localhost:11434")
            return True
        else:
            print("  [INFO] Ollama not available (optional, application works offline)")
            return False
    except Exception as e:
        print(f"  [INFO] Ollama check failed (optional): {str(e)}")
        return False


def main():
    """Run all smoke tests"""
    print("=" * 70)
    print("SMOKE TESTS: Core Application Functionality")
    print("=" * 70)
    
    # Test 1: File ingestion
    chunks = test_file_ingestion()
    
    # Test 2: Rule detection
    findings = test_rule_detection(chunks)
    
    # Test 3: Finding enhancement
    enhanced_findings = test_finding_enhancement(findings)
    
    # Test 4: Report generation
    report_data = test_report_generation(enhanced_findings)
    
    # Test 5: Markdown export
    md_success = test_markdown_export(report_data)
    
    # Test 6: PDF export
    pdf_success = test_pdf_export(report_data)
    
    # Test 7: Ollama availability
    ollama_available = test_ollama_availability()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"File Ingestion: {'PASS' if chunks else 'SKIP'}")
    print(f"Rule Detection: {'PASS' if findings else 'SKIP'}")
    print(f"Finding Enhancement: {'PASS' if enhanced_findings else 'SKIP'}")
    print(f"Report Generation: {'PASS' if report_data else 'FAIL'}")
    print(f"Markdown Export: {'PASS' if md_success else 'FAIL'}")
    print(f"PDF Export: {'PASS' if pdf_success else 'WARNING'}")
    print(f"Ollama Integration: {'AVAILABLE' if ollama_available else 'OFFLINE (optional)'}")
    print("=" * 70)
    
    # Overall result
    core_functionality = chunks and findings and report_data and md_success
    if core_functionality:
        print("RESULT: PASS - Core functionality working")
        return 0
    else:
        print("RESULT: FAIL - Core functionality issues detected")
        return 1


if __name__ == "__main__":
    sys.exit(main())
