"""
LLM-Assisted Vulnerability Reasoning: The "Contextual Advisor".

This module leverages Large Language Models (LLMs) to provide "human-like" analysis 
for raw findings. It focuses on the "So What?"—explaining the business impact 
and providing actionable remediation steps.

Design Philosophy:
- Advisor, Not Authority: The LLM suggests; the human analyst decides.
- Safety First: Robust validation ensures the LLM doesn't "invent" vulnerabilities.
- Preserved Integrity: Final severity is always protected from automated changes.
"""

import json

from app.ollama_client import generate
from app.context_builder import build_single_finding_context
from app.llm_validation import (
    validate_llm_reasoning_output,
    validate_output_does_not_invent_vulnerabilities,
    sanitize_llm_output,
)
from app.severity_override import (
    initialize_severity_fields,
    ensure_llm_cannot_override_severity,
)


def explain_findings(model_id: str, prompt: str) -> tuple[bool, str]:
    """
    Backward-compatible entry point for raw LLM interactions.
    """
    return generate(model_id, prompt, temperature=0.2)


def explain_single_finding(
    model_id: str,
    finding: dict,
    temperature: float = 0.2,
) -> tuple[bool, dict | str]:
    """
    Generates a structured, human-readable deep-dive for a specific vulnerability.
    
    This method builds a bridge between raw code evidence and high-level risk analysis.
    
    Args:
        model_id: The specific LLM brain to use.
        finding: The raw data point from the Rule Engine.
        temperature: Controls "creative" analysis vs "strictly factual" (default 0.2).
    
    Returns:
        A success flag and either a structured analysis dictionary or a clear error.
    """
    # Integrity Check: Ensure we have enough data to form an opinion
    if "finding_id" not in finding:
        return False, "Analysis failed: Finding is missing its unique identifier."
    
    if "evidence" not in finding or not finding["evidence"]:
        return False, "Analysis failed: No code evidence provided for context."
    
    finding_id = finding["finding_id"]
    rule_id = finding.get("rule_id", "UNKNOWN")
    
    # 1. Build the Story: Create a context window for the LLM
    context = build_single_finding_context(finding)
    
    # 2. Command Structure: Ask for a specific JSON format to ensure machine-readability
    structured_prompt = (
        f"{context}\n\n"
        f"OUTPUT FORMAT (JSON only, no other text):\n"
        f'{{\n'
        f'  "finding_id": "{finding_id}",\n'
        f'  "summary": "Brief explanation of the risk based on the finding",\n'
        f'  "impact": "Generalized business/technical impact description",\n'
        f'  "suggested_severity": "High|Medium|Low",\n'
        f'  "remediation": ["Step 1", "Step 2", ...],\n'
        f'  "confidence_note": "Note referencing rule confidence and evidence count",\n'
        f'  "disclaimer": "Suggested analysis only; analyst review required"\n'
        f'}}\n'
    )
    
    # 3. Brainstorm: Generate the AI response
    success, raw_output = generate(model_id, structured_prompt, temperature=temperature)
    
    if not success:
        return False, f"LLM Communication Error: {raw_output}"
    
    # 4. Extract Truth: Find the JSON needle in the LLM haystack
    try:
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return False, "Analysis corrupted: LLM failed to provide structured data."
        
        json_str = raw_output[start_idx:end_idx]
        output_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"Data Parsing Error: The LLM output was malformed. Details: {e}"
    
    # 5. Sanitize: Remove any digital artifacts or unsafe content
    output_dict = sanitize_llm_output(output_dict)
    
    # 6. Safety Audit: Ensure the LLM didn't hallucinate or violate boundaries
    allowed_file_names = {
        evidence.get("file", "")
        for evidence in finding.get("evidence", [])
        if evidence.get("file")
    }
    
    is_valid, error_msg = validate_llm_reasoning_output(
        output_dict,
        expected_finding_id=finding_id,
        allowed_file_names=allowed_file_names,
    )
    
    if not is_valid:
        return False, f"Security Policy Violation: {error_msg}"
    
    is_safe, safety_error = validate_output_does_not_invent_vulnerabilities(
        output_dict,
        expected_rule_id=rule_id,
    )
    
    if not is_safe:
        return False, f"Hallucination Detected: {safety_error}"
    
    # 7. Integration: Merge suggestions safely without overwriting human decisions
    if "suggested_severity" not in finding:
        finding = initialize_severity_fields(
            finding,
            rule_suggested_severity=finding.get("severity_suggested"),
            llm_suggested_severity=output_dict.get("suggested_severity"),
        )
    
    protected_finding = ensure_llm_cannot_override_severity(finding, output_dict)
    
    return True, output_dict


def explain_multiple_findings(
    model_id: str,
    findings: list[dict],
    temperature: float = 0.2,
) -> list[dict]:
    """
    Generate structured LLM reasoning for multiple findings.
    
    Processes findings one at a time to ensure clear boundaries
    and prevent cross-contamination.
    
    Args:
        model_id: Ollama model identifier
        findings: List of finding dictionaries from rule engine
        temperature: Sampling temperature (default 0.2 for low randomness)
    
    Returns:
        List of structured output dictionaries (one per finding)
        Failed findings are included with error information
    """
    results = []
    
    for finding in findings:
        success, output = explain_single_finding(model_id, finding, temperature)
        
        if success:
            results.append(output)
        else:
            # Include error information for failed findings
            # Phase 10: Use get_final_severity for backward compatibility
            from app.severity_override import get_final_severity
            
            results.append({
                "finding_id": finding.get("finding_id", "UNKNOWN"),
                "error": output,  # Error message
                "summary": "LLM reasoning generation failed",
                "impact": "N/A",
                "suggested_severity": finding.get("severity_suggested", "Unknown"),
                "remediation": [],
                "confidence_note": "Unable to generate LLM analysis",
                "disclaimer": "This finding requires manual analyst review",
            })
    
    return results
