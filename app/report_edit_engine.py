"""
Report Edit Engine (Phase 14 - AI-Powered Report Editing)

Implements safe, traceable, reversible AI-powered report editing with:
- Edit intent parsing (rewrite, summarize, expand, formalize, etc.)
- Context-aware LLM rewriting
- Patch generation and validation
- Diff preview support
- User approval workflow
- Version management and undo

All edits are:
✓ Traceable - Every change logged
✓ Previewable - Diff shown before apply
✓ Reversible - Snapshots saved before edits
✓ Safe - No hallucinated content, no severity changes, no evidence modification
"""

from typing import Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime
from copy import deepcopy

from app.ollama_client import generate
from app.logging_config import get_logger

logger = get_logger("ReportEditEngine")


class EditIntentType(Enum):
    """User edit intent types."""
    REWRITE = "REWRITE"
    SUMMARIZE = "SUMMARIZE"
    COMPRESS = "COMPRESS"
    EXPAND = "EXPAND"
    FORMAL = "FORMAL"
    SIMPLIFY = "SIMPLIFY"
    PROOFREAD = "PROOFREAD"
    CUSTOM = "CUSTOM"


class ScopeType(Enum):
    """Edit scope (what part of report to edit)."""
    SELECTION = "SELECTION"
    PARAGRAPH = "PARAGRAPH"
    SECTION = "SECTION"
    EXEC_SUMMARY = "EXEC_SUMMARY"
    FINDINGS = "FINDINGS"
    RISK_OVERVIEW = "RISK_OVERVIEW"
    FULL_REPORT = "FULL_REPORT"


@dataclass
class EditIntent:
    """Parsed user edit intent."""
    intent_type: EditIntentType
    scope: ScopeType
    tone: Optional[str] = None
    length: Optional[str] = None
    constraints: list[str] = field(default_factory=list)
    raw_request: str = ""

    def to_dict(self) -> dict:
        return {
            "intent_type": self.intent_type.value,
            "scope": self.scope.value,
            "tone": self.tone,
            "length": self.length,
            "constraints": self.constraints,
            "raw_request": self.raw_request,
        }


@dataclass
class EditPatch:
    """Structured edit patch."""
    section: str
    old_text: str
    new_text: str
    justification: str
    intent: EditIntent
    changes: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return {
            "section": self.section,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "justification": self.justification,
            "intent": self.intent.to_dict(),
            "changes": self.changes,
            "timestamp": self.timestamp,
        }


class EditIntentParser:
    """Parse user commands to detect edit intent."""

    @staticmethod
    def parse(user_message: str, selected_text: str = "") -> EditIntent:
        """
        Parse user message to extract edit intent.

        Args:
            user_message: User's natural language request
            selected_text: Selected text (optional context)

        Returns:
            EditIntent object with parsed intent details
        """
        msg_lower = user_message.lower()

        # Detect intent type
        intent_type = EditIntentParser._detect_intent_type(msg_lower)
        scope = EditIntentParser._detect_scope(msg_lower, selected_text)
        tone = EditIntentParser._detect_tone(msg_lower)
        length = EditIntentParser._detect_length(msg_lower)

        # Build constraints
        constraints = [
            "Do not add new vulnerabilities or findings",
            "Do not change severity ratings",
            "Do not modify evidence or file references",
            "Keep all facts unchanged",
            "Preserve all technical details",
        ]

        return EditIntent(
            intent_type=intent_type,
            scope=scope,
            tone=tone,
            length=length,
            constraints=constraints,
            raw_request=user_message,
        )

    @staticmethod
    def _detect_intent_type(msg_lower: str) -> EditIntentType:
        """Detect the intent type from message."""
        if any(word in msg_lower for word in ["compress", "shorten", "condense", "tighten"]):
            return EditIntentType.COMPRESS

        if any(word in msg_lower for word in ["rewrite", "rephrase", "reword"]):
            return EditIntentType.REWRITE

        if any(word in msg_lower for word in ["summarize", "summary", "brief"]):
            return EditIntentType.SUMMARIZE

        if any(word in msg_lower for word in ["expand", "extend", "elaborate", "detail"]):
            return EditIntentType.EXPAND

        if any(word in msg_lower for word in ["formal", "professional", "formal tone"]):
            return EditIntentType.FORMAL

        if any(word in msg_lower for word in ["simplify", "simple", "easy", "plain"]):
            return EditIntentType.SIMPLIFY

        if any(word in msg_lower for word in ["grammar", "spelling", "typo", "proofread"]):
            return EditIntentType.PROOFREAD

        return EditIntentType.CUSTOM

    @staticmethod
    def _detect_scope(msg_lower: str, selected_text: str) -> ScopeType:
        """Detect the scope (what to edit)."""
        if any(word in msg_lower for word in ["summary", "executive"]):
            return ScopeType.EXEC_SUMMARY

        if any(word in msg_lower for word in ["finding", "vulnerability"]):
            return ScopeType.FINDINGS

        if any(word in msg_lower for word in ["risk overview"]):
            return ScopeType.RISK_OVERVIEW

        if any(word in msg_lower for word in ["this", "selection", "text"]) or selected_text:
            return ScopeType.SELECTION

        if any(word in msg_lower for word in ["paragraph"]):
            return ScopeType.PARAGRAPH

        if any(word in msg_lower for word in ["section"]):
            return ScopeType.SECTION

        if any(word in msg_lower for word in ["report", "entire", "whole"]):
            return ScopeType.FULL_REPORT

        return ScopeType.SELECTION

    @staticmethod
    def _detect_tone(msg_lower: str) -> Optional[str]:
        """Detect desired tone."""
        if any(word in msg_lower for word in ["professional", "formal", "business"]):
            return "professional"
        if any(word in msg_lower for word in ["technical", "cve", "cvss"]):
            return "technical"
        if any(word in msg_lower for word in ["simple", "plain", "easy"]):
            return "simple"
        if any(word in msg_lower for word in ["executive", "high-level"]):
            return "executive"
        return None

    @staticmethod
    def _detect_length(msg_lower: str) -> Optional[str]:
        """Detect desired length change."""
        if any(word in msg_lower for word in ["short", "brief", "one line", "compress"]):
            return "shorter"
        if any(word in msg_lower for word in ["long", "expand", "detail", "more"]):
            return "longer"
        return None


class ContextBuilder:
    """Build grounded context for LLM rewriting."""

    @staticmethod
    def build_context(
        section_name: str,
        text_to_edit: str,
        full_report_text: str = "",
        findings_summary: Optional[dict] = None,
        intent: Optional[EditIntent] = None,
    ) -> dict:
        """
        Build comprehensive context for LLM editing.

        Args:
            section_name: Name of report section being edited
            text_to_edit: The text to be rewritten
            full_report_text: Full report text for context
            findings_summary: Summary of report findings
            intent: Parsed edit intent

        Returns:
            Context dict with all relevant information
        """
        return {
            "section": section_name,
            "original_text": text_to_edit,
            "context_length": len(full_report_text),
            "findings_summary": findings_summary or {},
            "constraints": [
                "Do not add new vulnerabilities or findings",
                "Do not change severity levels",
                "Do not modify evidence references or file paths",
                "Keep all facts and technical details unchanged",
                "Preserve all CVE IDs, rule IDs, and technical specifics",
                "Only rewrite the given text for clarity/style",
            ],
            "intent": intent.to_dict() if intent else None,
            "editing_rules": {
                "can_improve_clarity": True,
                "can_improve_grammar": True,
                "can_reorganize_sentences": True,
                "can_change_tone": True,
                "cannot_change_facts": True,
                "cannot_change_severity": True,
                "cannot_change_evidence": True,
                "cannot_invent_findings": True,
            },
        }


class LLMPromptTemplate:
    """LLM prompt templates for different edit intents."""

    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for report editing."""
        return """You are a professional editor for cybersecurity audit reports.

CRITICAL RULES:
- Do NOT add new vulnerabilities or findings.
- Do NOT change severity ratings (High, Medium, Low, Critical).
- Do NOT modify evidence references or file paths.
- Do NOT invent or hallucinate technical details.
- Only rewrite the given text for clarity, grammar, or style.
- Keep all facts, numbers, and technical details unchanged.
- Preserve CVE IDs, rule IDs, and other identifiers exactly.

Your job is to improve the text while maintaining complete accuracy.

Return ONLY valid JSON with this structure:
{
  "edited_text": "The improved text here",
  "justification": "Brief explanation of changes made",
  "changes": ["Change 1", "Change 2", ...]
}"""

    @staticmethod
    def get_rewrite_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for rewriting."""
        tone_instruction = ""
        if intent.tone:
            tone_instruction = f"\nAdjust tone to be: {intent.tone}"

        length_instruction = ""
        if intent.length:
            length_instruction = f"\nMake the text: {intent.length}"

        return f"""Rewrite this text for the {context.get('section', 'report')} section:

ORIGINAL TEXT:
{text}

INTENT: {intent.intent_type.value}
{tone_instruction}
{length_instruction}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Improve the clarity, grammar, and flow while preserving all facts and technical details."""

    @staticmethod
    def get_summarize_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for summarization."""
        return f"""Summarize this text concisely for the {context.get('section', 'report')} section:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Create a brief summary that captures the key points without losing essential details."""

    @staticmethod
    def get_compress_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for compression."""
        return f"""Compress this text into a single paragraph for the {context.get('section', 'report')} section:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Remove redundancy and condense without losing important information."""

    @staticmethod
    def get_expand_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for expansion."""
        return f"""Expand this text with more detail for the {context.get('section', 'report')} section:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Add more context and detail to make it clearer, but don't invent new information."""

    @staticmethod
    def get_formal_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for formalization."""
        return f"""Rewrite this text in a more formal, professional tone:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Use formal language suitable for a security audit report."""

    @staticmethod
    def get_simplify_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for simplification."""
        return f"""Rewrite this text in simpler, clearer language:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Make it easy to understand while preserving technical accuracy."""

    @staticmethod
    def get_proofread_prompt(text: str, intent: EditIntent, context: dict) -> str:
        """Generate prompt for proofreading."""
        return f"""Proofread and fix grammar/spelling in this text:

ORIGINAL TEXT:
{text}

CONSTRAINTS:
{chr(10).join('- ' + c for c in intent.constraints)}

Fix any grammar, spelling, or punctuation errors. Don't change meaning."""

    @staticmethod
    def get_prompt_for_intent(text: str, intent: EditIntent, context: dict) -> str:
        """Get the appropriate prompt for the detected intent."""
        intent_map = {
            EditIntentType.REWRITE: LLMPromptTemplate.get_rewrite_prompt,
            EditIntentType.SUMMARIZE: LLMPromptTemplate.get_summarize_prompt,
            EditIntentType.COMPRESS: LLMPromptTemplate.get_compress_prompt,
            EditIntentType.EXPAND: LLMPromptTemplate.get_expand_prompt,
            EditIntentType.FORMAL: LLMPromptTemplate.get_formal_prompt,
            EditIntentType.SIMPLIFY: LLMPromptTemplate.get_simplify_prompt,
            EditIntentType.PROOFREAD: LLMPromptTemplate.get_proofread_prompt,
            EditIntentType.CUSTOM: LLMPromptTemplate.get_rewrite_prompt,
        }

        prompt_fn = intent_map.get(intent.intent_type, LLMPromptTemplate.get_rewrite_prompt)
        return prompt_fn(text, intent, context)


class SafetyValidator:
    """Validate that patches don't violate safety constraints."""

    @staticmethod
    def validate_no_new_findings(old_text: str, new_text: str) -> tuple[bool, str]:
        """
        Check that no new findings/vulnerabilities were added.

        Args:
            old_text: Original text
            new_text: Rewritten text

        Returns:
            (is_valid, message)
        """
        # Count finding indicators (CVE, severity words, rule IDs)
        old_pattern = r"(CVE-\d{4}-\d+|High|Medium|Low|Critical|finding|vulnerability)"
        old_matches = len(re.findall(old_pattern, old_text, re.IGNORECASE))
        new_matches = len(re.findall(old_pattern, new_text, re.IGNORECASE))

        # Allow same count ± 1 (for natural rephrasing)
        if new_matches > old_matches + 1:
            return False, f"Detected potential new findings ({new_matches} vs {old_matches})"

        return True, "No new findings detected"

    @staticmethod
    def validate_severity_unchanged(old_text: str, new_text: str) -> tuple[bool, str]:
        """
        Check that severity ratings weren't modified.

        Args:
            old_text: Original text
            new_text: Rewritten text

        Returns:
            (is_valid, message)
        """
        # Extract severity mentions
        severity_pattern = r"\b(High|Medium|Low|Critical)\b"
        old_sevs = re.findall(severity_pattern, old_text)
        new_sevs = re.findall(severity_pattern, new_text)

        if sorted(old_sevs) != sorted(new_sevs):
            return False, f"Severity levels changed: {old_sevs} → {new_sevs}"

        return True, "Severity levels unchanged"

    @staticmethod
    def validate_evidence_preserved(old_text: str, new_text: str) -> tuple[bool, str]:
        """
        Check that evidence references weren't modified.

        Args:
            old_text: Original text
            new_text: Rewritten text

        Returns:
            (is_valid, message)
        """
        # Extract evidence patterns (CVE, CWE, rule IDs, file paths)
        evidence_pattern = r"(CVE-\d{4}-\d+|CWE-\d+|[A-Z]{3,}-\d{3,}|[\w./:\\-]+\.(?:conf|xml|json|yaml|py|js|ts))"
        old_evidence = set(re.findall(evidence_pattern, old_text))
        new_evidence = set(re.findall(evidence_pattern, new_text))

        # All old evidence should still be present
        missing = old_evidence - new_evidence
        if missing:
            return False, f"Evidence removed: {missing}"

        return True, "Evidence preserved"

    @staticmethod
    def validate_patch(patch: EditPatch) -> tuple[bool, list[str]]:
        """
        Comprehensive patch validation.

        Args:
            patch: EditPatch to validate

        Returns:
            (is_valid, messages)
        """
        messages = []
        all_valid = True

        # Check for new findings
        valid, msg = SafetyValidator.validate_no_new_findings(patch.old_text, patch.new_text)
        messages.append(("✓" if valid else "✗") + " " + msg)
        all_valid = all_valid and valid

        # Check severity unchanged
        valid, msg = SafetyValidator.validate_severity_unchanged(patch.old_text, patch.new_text)
        messages.append(("✓" if valid else "✗") + " " + msg)
        all_valid = all_valid and valid

        # Check evidence preserved
        valid, msg = SafetyValidator.validate_evidence_preserved(patch.old_text, patch.new_text)
        messages.append(("✓" if valid else "✗") + " " + msg)
        all_valid = all_valid and valid

        # Length sanity check
        old_len = len(patch.old_text)
        new_len = len(patch.new_text)
        ratio = new_len / old_len if old_len > 0 else 1

        if ratio > 3:  # More than 3x expansion
            messages.append("⚠ Large expansion detected (3x+)")
        if ratio < 0.3:  # Less than 30% compression
            messages.append("⚠ Large compression detected (70%+)")

        return all_valid, messages


class PatchGenerator:
    """Generate structured patches from LLM output."""

    @staticmethod
    def generate_patch(
        section: str,
        old_text: str,
        llm_output: str,
        intent: EditIntent,
    ) -> tuple[bool, Optional[EditPatch], str]:
        """
        Generate patch from LLM output.

        Args:
            section: Report section name
            old_text: Original text
            llm_output: LLM response (should be JSON)
            intent: Edit intent

        Returns:
            (success, patch, error_message)
        """
        try:
            # Parse LLM JSON output
            if not llm_output.strip():
                return False, None, "LLM returned empty response"

            # Find JSON in response (might be wrapped in other text)
            json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if not json_match:
                return False, None, "LLM response doesn't contain valid JSON"

            llm_data = json.loads(json_match.group())

            edited_text = llm_data.get("edited_text", "").strip()
            justification = llm_data.get("justification", "").strip()
            changes = llm_data.get("changes", [])

            if not edited_text:
                return False, None, "LLM returned empty edited text"

            # Create patch
            patch = EditPatch(
                section=section,
                old_text=old_text,
                new_text=edited_text,
                justification=justification,
                intent=intent,
                changes=changes if isinstance(changes, list) else [str(changes)],
            )

            return True, patch, ""

        except json.JSONDecodeError as e:
            return False, None, f"Failed to parse LLM response: {str(e)}"
        except Exception as e:
            return False, None, f"Error generating patch: {str(e)}"


class ReportEditEngine:
    """Main engine for AI-powered report editing."""

    def __init__(self, model_id: str, temperature: float = 0.3):
        """
        Initialize the report edit engine.

        Args:
            model_id: Ollama model ID
            temperature: LLM temperature (lower = more focused)
        """
        self.model_id = model_id
        self.temperature = temperature
        self.intent_parser = EditIntentParser()
        self.context_builder = ContextBuilder()
        self.safety_validator = SafetyValidator()
        self.patch_generator = PatchGenerator()

    def analyze_intent(self, user_message: str, selected_text: str = "") -> EditIntent:
        """
        Analyze user message to detect edit intent.

        Args:
            user_message: User's request
            selected_text: Selected text (optional)

        Returns:
            EditIntent object
        """
        intent = self.intent_parser.parse(user_message, selected_text)
        logger.info(f"Detected intent: {intent.intent_type.value} (scope: {intent.scope.value})")
        return intent

    def build_context(
        self,
        section_name: str,
        text_to_edit: str,
        full_report_text: str = "",
        findings_summary: Optional[dict] = None,
        intent: Optional[EditIntent] = None,
    ) -> dict:
        """
        Build context for LLM rewriting.

        Args:
            section_name: Report section name
            text_to_edit: Text to be edited
            full_report_text: Full report for context
            findings_summary: Findings summary
            intent: Edit intent

        Returns:
            Context dictionary
        """
        return self.context_builder.build_context(
            section_name, text_to_edit, full_report_text, findings_summary, intent
        )

    def generate_patch(
        self,
        section: str,
        text_to_edit: str,
        intent: EditIntent,
        context: Optional[dict] = None,
    ) -> tuple[bool, Optional[EditPatch], str]:
        """
        Generate an edit patch using the LLM.

        Args:
            section: Report section name
            text_to_edit: Text to edit
            intent: Edit intent
            context: Optional context dict

        Returns:
            (success, patch, error_message)
        """
        # Ensure we have context
        if context is None:
            context = self.build_context(section, text_to_edit, intent=intent)

        # Generate prompt
        prompt = LLMPromptTemplate.get_prompt_for_intent(text_to_edit, intent, context)
        system_prompt = LLMPromptTemplate.get_system_prompt()

        # Prepare full prompt with system instruction
        full_prompt = f"{system_prompt}\n\n{prompt}"

        # Call LLM
        logger.info(f"Calling LLM for {intent.intent_type.value} ({section})")
        success, output = generate(self.model_id, full_prompt, temperature=self.temperature)

        if not success:
            logger.error(f"LLM error: {output}")
            return False, None, f"LLM error: {output}"

        # Generate patch from LLM output
        return self.patch_generator.generate_patch(section, text_to_edit, output, intent)

    def validate_patch(self, patch: EditPatch) -> tuple[bool, list[str]]:
        """
        Validate a patch for safety violations.

        Args:
            patch: EditPatch to validate

        Returns:
            (is_valid, validation_messages)
        """
        return self.safety_validator.validate_patch(patch)

    def apply_patch(self, text: str, patch: EditPatch) -> str:
        """
        Apply a patch to text with robust matching.

        Uses multiple strategies to handle whitespace variations:
        1. Exact match (fastest)
        2. Normalized whitespace match
        3. Fuzzy substring match with partial text
        4. Fallback: return text unchanged with warning

        Args:
            text: Original text
            patch: Patch to apply

        Returns:
            Modified text with patch applied, or unchanged if match fails
        """
        # Strategy 1: Exact substring match
        if patch.old_text in text:
            result = text.replace(patch.old_text, patch.new_text, 1)
            logger.info(f"Applied patch to {patch.section} (exact match)")
            return result

        # Strategy 2: Normalize whitespace and try again
        # This handles cases where LLM added/removed extra spaces or line breaks
        normalized_old = self._normalize_whitespace(patch.old_text)
        normalized_text = self._normalize_whitespace(text)
        
        if normalized_old in normalized_text:
            # Find the position in normalized text
            normalized_start = normalized_text.find(normalized_old)
            normalized_end = normalized_start + len(normalized_old)
            
            # Map back to original text positions
            char_count = 0
            original_start = 0
            original_end = 0
            
            for i, char in enumerate(text):
                if char.strip():  # Count non-whitespace characters
                    if char_count == sum(1 for c in patch.old_text if c.strip()):
                        original_end = i
                        break
                    char_count += 1
                    
                    if char_count == 0:
                        original_start = i
            
            # Try to find better boundaries by looking at actual text position
            try:
                # Find the actual position of the normalized text in original
                old_lines = patch.old_text.split('\n')
                text_lines = text.split('\n')
                
                for i in range(len(text_lines) - len(old_lines) + 1):
                    if self._normalize_whitespace('\n'.join(text_lines[i:i+len(old_lines)])) == normalized_old:
                        # Found matching lines
                        start_line = i
                        end_line = i + len(old_lines)
                        original_start = sum(len(text_lines[j]) + 1 for j in range(start_line))  # +1 for newlines
                        original_end = sum(len(text_lines[j]) + 1 for j in range(end_line))
                        
                        result = text[:original_start] + patch.new_text + text[original_end:]
                        logger.info(f"Applied patch to {patch.section} (normalized match)")
                        return result
            except Exception as e:
                logger.debug(f"Normalized line-based matching failed: {str(e)}")

        # Strategy 3: Partial text match with fuzzy logic
        # If exact match fails, try to match with first and last 50 chars
        if len(patch.old_text) > 100:
            first_part = patch.old_text[:50].strip()
            last_part = patch.old_text[-50:].strip()
            
            if first_part in text and last_part in text:
                first_idx = text.find(first_part)
                last_idx = text.rfind(last_part)
                
                if first_idx >= 0 and last_idx >= 0 and last_idx > first_idx:
                    # Found both parts, replace the text between them
                    start = first_idx
                    end = last_idx + len(last_part)
                    
                    result = text[:start] + patch.new_text + text[end:]
                    logger.warning(f"Applied patch to {patch.section} (fuzzy match - first/last parts)")
                    return result

        # Strategy 4: Try to find similar text with minor variations
        # Handle case where whitespace or punctuation slightly differs
        old_normalized_simple = ' '.join(patch.old_text.split())
        text_normalized_simple = ' '.join(text.split())
        
        if old_normalized_simple in text_normalized_simple:
            # Find position and reconstruct proper replacement
            idx = text_normalized_simple.find(old_normalized_simple)
            if idx >= 0:
                # Reconstruct actual position in original text
                try:
                    # More careful reconstruction
                    words_before = len(' '.join(text.split())[:idx].split())
                    words_in_old = len(old_normalized_simple.split())
                    
                    current_word = 0
                    original_start = 0
                    original_end = 0
                    in_match = False
                    
                    for i, char in enumerate(text):
                        if char.isspace():
                            current_word += 1
                        else:
                            if current_word == words_before and not in_match:
                                original_start = i
                                in_match = True
                            elif current_word == words_before + words_in_old and in_match:
                                original_end = i
                                break
                    
                    if original_end == 0:
                        original_end = len(text)
                    
                    result = text[:original_start] + patch.new_text + text[original_end:]
                    logger.warning(f"Applied patch to {patch.section} (normalized words match)")
                    return result
                except Exception as e:
                    logger.debug(f"Word-based matching failed: {str(e)}")

        # Fallback: Could not find text to replace
        logger.error(
            f"Could not find text to replace in {patch.section}.\n"
            f"Old text length: {len(patch.old_text)}\n"
            f"Report text length: {len(text)}\n"
            f"Old text preview: {patch.old_text[:100]!r}"
        )
        return text

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace for comparison.

        Converts:
        - Multiple spaces to single space
        - All line endings to \n
        - Trailing/leading whitespace in lines removed
        - Tab characters to spaces
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Normalize tabs to spaces
        text = text.replace('\t', '  ')
        
        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Normalize internal line spacing (multiple spaces to single)
        lines = [' '.join(line.split()) for line in lines]
        
        return '\n'.join(lines)
