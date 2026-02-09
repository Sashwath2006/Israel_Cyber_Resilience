"""
AI Assistant for Report Editing & Vulnerability Discussion (Phase 13)

Provides safe, context-aware AI assistance for:
1. Report text editing with multiple rewrite styles (concise, professional, technical)
2. Intent detection (rewrite, simplify, extend, formalize, etc.)
3. Auto-insert metadata with line numbers for UI integration
4. Section-aware rewriting (executive summary, findings, recommendations)
5. Interactive vulnerability discussion (Q&A about findings)

All AI suggestions are advisory only. Analyst has final authority.
AI cannot change evidence, severity, or invent new vulnerabilities.
"""

from typing import Optional, Literal
import json
import re
from enum import Enum

from app.ollama_client import generate
from app.logging_config import get_logger

logger = get_logger("AIAssistant")


class RewriteStyle(Enum):
    """Rewrite style options."""
    CONCISE = "concise"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"


class ReportSection(Enum):
    """Report section types for tone adaptation."""
    EXECUTIVE_SUMMARY = "executive_summary"
    FINDINGS = "findings"
    RISK_OVERVIEW = "risk_overview"
    RECOMMENDATIONS = "recommendations"
    TECHNICAL_DETAILS = "technical_details"
    OTHER = "other"


class RewriteContext:
    """
    Context object for rewrite requests.
    
    Encapsulates selected text, intent, section type, and line information
    for accurate, context-aware rewrites.
    """
    
    def __init__(
        self,
        selected_text: str,
        user_request: str,
        start_line: int,
        end_line: int,
        section: ReportSection = ReportSection.OTHER,
    ):
        self.selected_text = selected_text
        self.user_request = user_request
        self.start_line = start_line
        self.end_line = end_line
        self.section = section
        self.intent = self._detect_intent()
    
    def _detect_intent(self) -> str:
        """
        Automatically detect user's rewrite intent from request.
        
        Returns:
            Intent string: 'compress', 'extend', 'formalize', 'simplify', 
                          'technical', 'custom', etc.
        """
        request_lower = self.user_request.lower()
        
        # Intent detection patterns
        if any(word in request_lower for word in ["single line", "one line", "compress", "shorten", "condense"]):
            return "compress"
        
        if any(word in request_lower for word in ["another paragraph", "expand", "extend", "more detail", "elaborate"]):
            return "extend"
        
        if any(word in request_lower for word in ["formal", "professional", "formal tone", "professional tone"]):
            return "formalize"
        
        if any(word in request_lower for word in ["simplif", "simple", "non-technical", "plain language", "easy"]):
            return "simplify"
        
        if any(word in request_lower for word in ["technical", "cve", "cvss", "exploit", "mitigate", "vulnerability"]):
            return "technical"
        
        if any(word in request_lower for word in ["rewrite", "improve", "better", "revise", "enhance"]):
            return "improve"
        
        return "custom"
    
    def is_safety_violation(self) -> bool:
        """
        Check if rewrite request violates safety rules.
        
        Prevents modifications to:
        - Severity values
        - Rule IDs
        - Evidence locations
        - File names
        
        Returns:
            True if violation detected
        """
        request_lower = self.user_request.lower()
        text_lower = self.selected_text.lower()
        
        # Don't allow explicit changes to protected fields
        if any(word in request_lower for word in ["severity", "change severity", "set high", "set medium", "set low"]):
            if any(sev in text_lower for sev in ["high", "medium", "low", "critical"]):
                return True
        
        if any(word in request_lower for word in ["rule id", "change rule", "modify rule"]):
            if re.search(r"[A-Z]{3,}-\d{3,}", text_lower):  # Common rule ID pattern
                return True
        
        if any(word in request_lower for word in ["file name", "change file", "modify location"]):
            if any(char in text_lower for char in [".", "\\", "/"]):
                return True
        
        return False


def detect_report_section(text_before_selection: str) -> ReportSection:
    """
    Detect which section of the report the selected text is in.
    
    Uses heuristics based on surrounding content and section markers.
    
    Args:
        text_before_selection: Text that appears before the selection
    
    Returns:
        ReportSection enum value
    """
    text_lower = text_before_selection.lower()
    
    # Look for section headers in the preceding text
    if any(marker in text_lower for marker in ["executive summary", "executive overview", "summary"]):
        return ReportSection.EXECUTIVE_SUMMARY
    
    if any(marker in text_lower for marker in ["findings", "vulnerabilities", "vulnerability details"]):
        return ReportSection.FINDINGS
    
    if any(marker in text_lower for marker in ["risk overview", "risk assessment", "risk analysis"]):
        return ReportSection.RISK_OVERVIEW
    
    if any(marker in text_lower for marker in ["recommendations", "remediation", "mitigation", "fixes"]):
        return ReportSection.RECOMMENDATIONS
    
    if any(marker in text_lower for marker in ["technical details", "technical analysis", "code"]):
        return ReportSection.TECHNICAL_DETAILS
    
    return ReportSection.OTHER


def assist_report_editing_advanced(
    model_id: str,
    rewrite_context: RewriteContext,
    temperature: float = 0.3,
) -> tuple[bool, str | dict]:
    """
    Advanced report editing assistant with context awareness.
    
    Generates multiple rewrite styles for the selected text based on:
    - Detected intent
    - Report section
    - Current text characteristics
    
    Args:
        model_id: Ollama model ID
        rewrite_context: RewriteContext object with selection and intent info
        temperature: LLM temperature (lower = more focused)
    
    Returns:
        Tuple of (success: bool, result: str | dict)
        
        On success: Returns a dict with:
        {
            "success": true,
            "action": "replace",
            "intent": "compress",
            "section": "findings",
            "start_line": 42,
            "end_line": 44,
            "styles": {
                "concise": "Rewritten text...",
                "professional": "Rewritten text...",
                "technical": "Rewritten text..."
            },
            "feedback": "You can paste any version into your report or click Insert."
        }
        
        On failure: Returns error string
    """
    
    # Safety check
    if rewrite_context.is_safety_violation():
        logger.warning(
            "Rewrite safety violation detected",
            intent=rewrite_context.intent,
            section=rewrite_context.section.value
        )
        return False, (
            "⚠ Safety Check Failed\n\n"
            "Cannot modify protected fields (severity, rule IDs, file locations).\n"
            "Select different text or request a different rewrite."
        )
    
    # Build section-aware system prompt
    section_guidance = _get_section_guidance(rewrite_context.section)
    
    system_prompt = f"""You are a professional report editor helping refine security analysis documentation.

TEXT TO REWRITE:
{rewrite_context.selected_text}

USER REQUEST:
{rewrite_context.user_request}

DETECTED INTENT: {rewrite_context.intent}
REPORT SECTION: {rewrite_context.section.value}

{section_guidance}

Your task: Generate 3 rewrite variations in JSON format ONLY:
1. **Concise**: Shorten while preserving key information
2. **Professional**: Formal business/technical tone
3. **Technical**: Security-focused terminology and precision

CRITICAL RULES:
- Do NOT change factual information (file names, line numbers, severity levels)
- Do NOT invent vulnerabilities or file locations
- Preserve all technical accuracy
- Maintain security context
- Do NOT add qualifiers like "allegedly" or "may indicate" if original was definitive
- Each variation should be complete and standalone

Return ONLY valid JSON (no markdown, no extra text):
{{
  "concise": "Shortened version here",
  "professional": "Formal version here",
  "technical": "Security-focused version here"
}}
"""
    
    try:
        success, raw_output = generate(model_id, system_prompt, temperature=temperature)
        
        if not success:
            logger.error("LLM call failed for report editing", error=raw_output)
            return False, f"AI rewrite failed: {raw_output}"
        
        # Extract JSON from response
        json_str = _extract_json_from_response(raw_output)
        
        if not json_str:
            logger.error("No valid JSON in LLM response", response=raw_output)
            return False, "AI returned invalid format. Please try again."
        
        styles = json.loads(json_str)
        
        # Validate all styles present
        required_keys = ["concise", "professional", "technical"]
        missing = [k for k in required_keys if k not in styles or not styles[k]]
        if missing:
            logger.warning("Missing rewrite styles", missing=missing)
            # Fill in missing with original text if necessary
            for key in missing:
                styles[key] = rewrite_context.selected_text
        
        result = {
            "success": True,
            "action": "replace",
            "intent": rewrite_context.intent,
            "section": rewrite_context.section.value,
            "start_line": rewrite_context.start_line,
            "end_line": rewrite_context.end_line,
            "styles": styles,
            "feedback": "✓ Here are suggested rewrites. You can paste any into your report or click Insert."
        }
        
        # Log the rewrite request
        logger.info(
            "Report rewrite suggested",
            intent=rewrite_context.intent,
            section=rewrite_context.section.value,
            char_count=len(rewrite_context.selected_text)
        )
        
        return True, result
        
    except json.JSONDecodeError as e:
        logger.error("JSON parsing failed", error=str(e))
        return False, f"Failed to parse AI response: {str(e)}"
    except Exception as e:
        logger.error("Report editing failed", error=str(e))
        return False, f"AI editing failed: {str(e)}"


def _get_section_guidance(section: ReportSection) -> str:
    """
    Get section-specific guidance for rewriting.
    
    Args:
        section: ReportSection enum
    
    Returns:
        Guidance string for the LLM
    """
    guidance_map = {
        ReportSection.EXECUTIVE_SUMMARY: (
            "SECTION CONTEXT: Executive Summary\n"
            "Tone: Business-focused, high-level, actionable\n"
            "Avoid: Technical jargon, excessive detail\n"
            "Goal: Communicate risk and recommended actions to leadership"
        ),
        ReportSection.FINDINGS: (
            "SECTION CONTEXT: Findings / Vulnerabilities\n"
            "Tone: Technical, precise, evidence-based\n"
            "Avoid: Speculation, vague language\n"
            "Goal: Clearly describe the vulnerability and its location"
        ),
        ReportSection.RISK_OVERVIEW: (
            "SECTION CONTEXT: Risk Overview\n"
            "Tone: Business-technical balance, impact-focused\n"
            "Avoid: Excessive technical depth, marketing language\n"
            "Goal: Explain business impact and likelihood"
        ),
        ReportSection.RECOMMENDATIONS: (
            "SECTION CONTEXT: Recommendations / Remediation\n"
            "Tone: Actionable, clear, step-by-step\n"
            "Avoid: Vague or impossible-to-implement guidance\n"
            "Goal: Provide concrete remediation steps"
        ),
        ReportSection.TECHNICAL_DETAILS: (
            "SECTION CONTEXT: Technical Details\n"
            "Tone: Highly technical, precise, complete\n"
            "Avoid: Oversimplification\n"
            "Goal: Provide thorough technical analysis for security professionals"
        ),
        ReportSection.OTHER: (
            "SECTION CONTEXT: General report content\n"
            "Tone: Professional, clear\n"
            "Avoid: Ambiguity, unsupported claims\n"
            "Goal: Communicate information effectively"
        ),
    }
    
    return guidance_map.get(section, guidance_map[ReportSection.OTHER])


def _extract_json_from_response(response: str) -> Optional[str]:
    """
    Extract JSON object from LLM response.
    
    Handles cases where LLM wraps JSON in markdown code blocks or extra text.
    
    Args:
        response: Raw LLM response
    
    Returns:
        JSON string or None if not found
    """
    # Try direct JSON parsing first
    response = response.strip()
    
    # Remove markdown code blocks
    if response.startswith("```"):
        # Extract content between backticks
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
        if match:
            response = match.group(1)
    
    # Find JSON object boundaries
    start_idx = response.find('{')
    end_idx = response.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return response[start_idx:end_idx + 1]
    
    return None


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
            logger.error("Vulnerability discussion LLM call failed", rule_id=rule_id, error=raw_output)
            return False, raw_output
        
        # Return cleaned output
        answer = raw_output.strip()
        
        # Log successful discussion
        logger.info(
            "Vulnerability discussion completed",
            rule_id=rule_id,
            finding_id=finding.get("finding_id", "unknown")
        )
        
        return True, answer
        
    except Exception as e:
        logger.error("Vulnerability discussion exception", rule_id=rule_id, error=str(e))
        return False, f"Discussion failed: {str(e)}"
