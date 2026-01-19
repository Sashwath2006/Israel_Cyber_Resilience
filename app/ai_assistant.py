"""
AI Assistant for Report Editing & Vulnerability Discussion (Phase 12)

Provides safe AI assistance for:
1. Report text editing (rewrite, clarify, improve wording)
2. Interactive vulnerability discussion (Q&A about findings)

All AI suggestions are advisory only. Analyst has final authority.
AI cannot change evidence, severity, or invent new vulnerabilities.
"""

from typing import Optional
import json

from app.ollama_client import generate


def assist_report_editing(
    model_id: str,
    current_text: str,
    user_request: str,
    temperature: float = 0.3,
) -> tuple[bool, str]:
    """
    Assist analyst in editing report text.
    
    Examples:
    - "Rewrite this executive summary to be more formal"
    - "Clarify this finding for a non-technical audience"
    - "Improve remediation wording"
    
    Args:
        model_id: Ollama model ID
        current_text: Current text to be edited
        user_request: User's editing request
        temperature: LLM temperature (lower = more focused)
    
    Returns:
        Tuple of (success: bool, suggested_text: str | error_message: str)
    
    Note:
        This function only suggests text changes. The analyst must explicitly
        accept the suggestion to apply it.
    """
    system_prompt = """You are an AI writing assistant helping a security analyst edit a security report.

Your role:
- Suggest text improvements based on user requests
- Maintain accuracy and technical correctness
- Do NOT change factual information (file names, line numbers, severity, etc.)
- Do NOT invent new vulnerabilities or locations
- Do NOT change severity levels

User Request: {user_request}

Current Text:
{current_text}

Provide ONLY the revised text. Do not include explanations or metadata.
Return just the improved text that addresses the user's request."""

    user_prompt = f"Please revise the text according to: {user_request}"

    try:
        # Query LLM
        full_prompt = (
            f"{system_prompt.format(user_request=user_request, current_text=current_text)}\n\n"
            f"{user_prompt}"
        )
        success, raw_output = generate(model_id, full_prompt, temperature=temperature)
        
        if not success:
            return False, raw_output
        
        # Return cleaned output (remove any JSON wrapping if present)
        suggested_text = raw_output.strip()
        
        # Remove markdown code blocks if present
        if suggested_text.startswith("```"):
            lines = suggested_text.split('\n')
            # Remove first line (```) and last line (```)
            if len(lines) > 2:
                suggested_text = '\n'.join(lines[1:-1])
            else:
                suggested_text = ""
        
        return True, suggested_text
        
    except Exception as e:
        return False, f"AI editing failed: {str(e)}"


def discuss_vulnerability(
    model_id: str,
    finding: dict,
    user_question: str,
    temperature: float = 0.3,
) -> tuple[bool, str]:
    """
    Discuss a specific vulnerability finding with the analyst.
    
    Examples:
    - "Why is this vulnerability risky?"
    - "What could happen if this is exploited?"
    - "Is this a false positive?"
    
    Args:
        model_id: Ollama model ID
        finding: Finding dictionary with evidence and metadata
        user_question: Analyst's question about the finding
        temperature: LLM temperature
    
    Returns:
        Tuple of (success: bool, answer: str | error_message: str)
    
    Note:
        Responses are grounded ONLY in:
        - Rule metadata
        - Evidence from the finding
        - Confidence score
        
        AI must NOT invent:
        - New vulnerabilities
        - New file names
        - New locations
    """
    # Extract finding information
    rule_id = finding.get("rule_id", "unknown")
    title = finding.get("title", "Unknown")
    category = finding.get("category", "Unknown")
    confidence = finding.get("confidence_score", finding.get("confidence", 0.0))
    final_severity = finding.get("final_severity", finding.get("severity_suggested", "Unknown"))
    
    # Extract evidence (file, lines, snippet)
    evidence_list = finding.get("evidence", [])
    evidence_summary = []
    for evidence in evidence_list:
        file_path = evidence.get("file", "unknown")
        line_start = evidence.get("line_start")
        snippet = evidence.get("snippet", "")[:100]  # Truncate long snippets
        
        location = file_path
        if line_start is not None:
            location += f" (line {line_start})"
        
        evidence_summary.append(f"- File: {location}")
        if snippet:
            evidence_summary.append(f"  Snippet: {snippet[:80]}...")
    
    evidence_text = "\n".join(evidence_summary) if evidence_summary else "No evidence available."
    
    system_prompt = """You are an AI security analyst assistant helping explain vulnerability findings.

CRITICAL CONSTRAINTS:
- Answer questions based ONLY on the provided finding information
- Do NOT invent new vulnerabilities, files, or locations
- Do NOT claim certainty beyond what the evidence supports
- Do NOT change or suggest changes to severity (analyst authority)
- Reference only the evidence, rule metadata, and confidence score provided

Finding Information:
- Rule ID: {rule_id}
- Title: {title}
- Category: {category}
- Final Severity: {final_severity} (set by analyst)
- Confidence Score: {confidence:.2f}

Evidence:
{evidence_text}

User Question: {user_question}

Provide a helpful answer grounded ONLY in the information above.
If the question asks about information not in the finding, state that clearly."""

    user_prompt = user_question

    try:
        # Query LLM
        full_prompt = (
            f"{system_prompt.format(rule_id=rule_id, title=title, category=category, final_severity=final_severity, confidence=confidence, evidence_text=evidence_text, user_question=user_question)}\n\n"
            f"{user_prompt}"
        )
        success, raw_output = generate(model_id, full_prompt, temperature=temperature)
        
        if not success:
            return False, raw_output
        
        # Return cleaned output
        answer = raw_output.strip()
        return True, answer
        
    except Exception as e:
        return False, f"Discussion failed: {str(e)}"
