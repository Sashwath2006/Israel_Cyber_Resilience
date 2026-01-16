"""
LLM-Assisted Vulnerability Reasoning (Phase 9, Phase 10)

Provides contextual explanations, impact analysis, and remediation
guidance for rule-based findings. LLM is an assistant, not an authority.

All outputs are clearly labeled as "Suggested / Advisory".

Phase 10: LLM suggestions are integrated safely without modifying
final_severity - analyst authority is preserved.
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
    Legacy function for backward compatibility.
    
    Use explain_single_finding() for Phase 9 structured outputs.
    """
    return generate(model_id, prompt, temperature=0.2)


def explain_single_finding(
    model_id: str,
    finding: dict,
    temperature: float = 0.2,
) -> tuple[bool, dict | str]:
    """
    Generate structured LLM reasoning for a single finding.
    
    Args:
        model_id: Ollama model identifier
        finding: Single finding dictionary from rule engine
        temperature: Sampling temperature (default 0.2 for low randomness)
    
    Returns:
        Tuple of (success: bool, output: dict | error_message: str)
        On success, returns structured output dictionary.
        On failure, returns error message string.
    """
    # Validate finding has required fields
    if "finding_id" not in finding:
        return False, "Finding missing finding_id"
    
    if "evidence" not in finding or not finding["evidence"]:
        return False, "Finding missing evidence"
    
    finding_id = finding["finding_id"]
    rule_id = finding.get("rule_id", "UNKNOWN")
    
    # Build context for this finding only (one-to-one mapping)
    context = build_single_finding_context(finding)
    
    # Build structured output prompt
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
    
    # Generate LLM response
    success, raw_output = generate(model_id, structured_prompt, temperature=temperature)
    
    if not success:
        return False, raw_output  # Error message
    
    # Try to extract JSON from response (may have extra text)
    try:
        # Find JSON object in response
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return False, "No JSON object found in LLM response"
        
        json_str = raw_output[start_idx:end_idx]
        output_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"Failed to parse LLM output as JSON: {e}"
    
    # Sanitize output
    output_dict = sanitize_llm_output(output_dict)
    
    # Get allowed file names from evidence
    allowed_file_names = {
        evidence.get("file", "")
        for evidence in finding.get("evidence", [])
        if evidence.get("file")
    }
    
    # Validate output against safety constraints
    is_valid, error_msg = validate_llm_reasoning_output(
        output_dict,
        expected_finding_id=finding_id,
        allowed_file_names=allowed_file_names,
    )
    
    if not is_valid:
        return False, f"Output validation failed: {error_msg}"
    
    # Additional validation: check for invented vulnerabilities
    is_safe, safety_error = validate_output_does_not_invent_vulnerabilities(
        output_dict,
        expected_rule_id=rule_id,
    )
    
    if not is_safe:
        return False, f"Safety validation failed: {safety_error}"
    
    # Phase 10: Integrate LLM suggestion safely without allowing override
    # LLM can suggest severity, but cannot set final_severity
    # Initialize severity fields if not already present
    if "suggested_severity" not in finding:
        finding = initialize_severity_fields(
            finding,
            rule_suggested_severity=finding.get("severity_suggested"),
            llm_suggested_severity=output_dict.get("suggested_severity"),
        )
    
    # Ensure LLM cannot override final_severity (analyst authority preserved)
    protected_finding = ensure_llm_cannot_override_severity(finding, output_dict)
    
    # Return LLM output (which only contains suggested_severity, not final_severity)
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
