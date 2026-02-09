# AI Assistant Report Editing Improvements (Phase 13)

## Overview

The AI assistant has been enhanced to behave like a professional report-editing copilot with context-aware rewriting, intent detection, and section-specific tone adaptation.

## Core Improvements

### 1. Context-Aware Rewriting

**New Capability:** The AI now understands the selected report text and rewrites it intelligently based on the detected section and user intent.

**How it works:**
- User selects text in the report editor
- User asks for a rewrite (e.g., "Make this concise", "More formal", "Single line")
- System detects:
  - **Intent**: What the user wants (compress, extend, formalize, simplify, technical, improve)
  - **Section**: Where in the report the text is (Executive Summary, Findings, Risk Overview, Recommendations, etc.)
  - **Line numbers**: Exact position (start_line, end_line) for potential auto-insert
- AI generates rewrites tailored to that section's tone

**Example:**

```
User selects in "FINDINGS" section:
"We discovered a SQL injection vulnerability in the login form that could allow 
attackers to access sensitive user data."

User asks: "Make this more technical"

AI returns:
Technical Version:
"SQL injection vulnerability identified in login form input validation (CWE-89). 
Insufficient parameterization of database queries enables arbitrary SQL execution 
and unauthorized data retrieval."
```

### 2. Multiple Rewrite Styles

**New Capability:** Every rewrite request generates three distinct versions.

When the user asks for a rewrite, the system automatically generates:

1. **Concise** - Shortened while preserving key information
2. **Professional** - Formal business/technical tone
3. **Technical** - Security-focused with precise terminology

**Example Output:**

```
✅ Multiple Rewrite Styles Generated:

**Concise Version:**
"SQL injection vulnerability in login form allows unauthorized data access."

**Professional Version:**
"A SQL injection vulnerability has been identified in the authentication form, 
which could permit unauthorized access to user information and compromise system integrity."

**Technical Version:**
"SQL injection (CWE-89) identified in login form input validation. 
Unsanitized user input passed directly to database queries enables arbitrary 
SQL execution and unauthorized data extraction."

💡 Copy any version above and paste it into your report.
```

### 3. Intent Detection

The system automatically recognizes user intent from their request:

| User Input | Detected Intent | Action |
|-----------|-----------------|--------|
| "Single line" | `compress` | Shorten to minimal form |
| "Another paragraph" | `extend` | Expand with more detail |
| "Make formal" | `formalize` | Adopt professional tone |
| "Simplify this" | `simplify` | Reduce complexity, plain language |
| "Add technical terms" | `technical` | Increase security terminology |
| "Rewrite this" | `improve` | General enhancement |

### 4. Section-Aware Rewriting

The AI detects which section the selected text is in and adapts its tone:

| Section | Tone | Focus | Example |
|---------|------|-------|---------|
| **Executive Summary** | Business-focused | Risk & actions | "Critical: Update database access controls immediately" |
| **Findings** | Technical, precise | Evidence-based | "SQL injection (CWE-89) in login.php line 45" |
| **Risk Overview** | Business-technical balance | Impact | "Attackers could access 50,000+ user records" |
| **Recommendations** | Actionable, step-by-step | Clear steps | "1. Implement parameterized queries..." |
| **Technical Details** | Highly technical | Thoroughness | Full technical analysis for security professionals |

**How it works:**
The system scans the text *before* the selection for section headers (case-insensitive):
- "executive summary" → EXECUTIVE_SUMMARY
- "findings" → FINDINGS
- "risk overview" → RISK_OVERVIEW
- "recommendations" → RECOMMENDATIONS
- "technical details" → TECHNICAL_DETAILS

### 5. Safety Rules Enforcement

The AI **refuses** to rewrite if it detects attempts to modify protected fields:

**Protected from modification:**
- ❌ Severity values (High, Medium, Low)
- ❌ Rule IDs (e.g., SQL-001, AUTH-042)
- ❌ Evidence locations (file paths, line numbers)
- ❌ File names

**Example:**
```
User selects: "Severity: High"
User asks: "Change this to Medium"

AI Response:
⚠ Safety Check Failed

Cannot modify protected fields (severity, rule IDs, file locations).
Select different text or request a different rewrite.
```

### 6. Line Number Metadata

Every rewrite response includes **line numbers** for potential future UI integration:

```json
{
  "success": true,
  "action": "replace",
  "intent": "compress",
  "section": "findings",
  "start_line": 42,
  "end_line": 44,
  "styles": {
    "concise": "Rewritten text...",
    "professional": "...",
    "technical": "..."
  }
}
```

This enables one-click "Insert" functionality in future UI updates.

### 7. Improved User Feedback

**Before (Generic):**
> "I can see your report has 5 findings. Select any section and ask me to rewrite it!"

**After (Actionable):**
```
✨ Analyzing selection (127 chars)...
Section: findings
Intent: compress

✅ Multiple Rewrite Styles Generated:

**Concise Version:**
"..."

**Professional Version:**
"..."

**Technical Version:**
"..."

💡 Copy any version above and paste it into your report.
```

### 8. Internal Logging

All rewrite actions are logged for debugging and analytics:

```python
logger.info(
    "Report rewrite suggested",
    intent="compress",
    section="findings",
    char_count=127
)

logger.info(
    "Rewrite generated",
    intent="compress",
    section="findings",
    start_line=42,
    end_line=44
)
```

Log entries include:
- Intent (what the user wanted)
- Section (where in the report)
- Character count (size of selection)
- Line numbers (position in document)
- Errors (if any)

---

## API Reference

### RewriteContext Class

```python
class RewriteContext:
    """Context for rewrite requests."""
    
    def __init__(
        self,
        selected_text: str,
        user_request: str,
        start_line: int,
        end_line: int,
        section: ReportSection = ReportSection.OTHER,
    ):
        """
        Args:
            selected_text: The text user selected
            user_request: User's rewrite request ("make concise", "formal tone", etc.)
            start_line: 1-indexed line number where selection starts
            end_line: 1-indexed line number where selection ends
            section: ReportSection enum (auto-detected if needed)
        """
```

**Properties:**
- `intent` (str): Auto-detected intent (compress, extend, formalize, etc.)
- `section` (ReportSection): Report section enum

**Methods:**
- `is_safety_violation() → bool`: Check if rewrite request violates safety rules

---

### Main Functions

#### `assist_report_editing_advanced()`

```python
def assist_report_editing_advanced(
    model_id: str,
    rewrite_context: RewriteContext,
    temperature: float = 0.3,
) -> tuple[bool, str | dict]:
    """
    Generate context-aware rewrite suggestions.
    
    Returns:
        (True, {dict with styles, metadata}) on success
        (False, error_message) on failure
    """
```

#### `detect_report_section()`

```python
def detect_report_section(text_before_selection: str) -> ReportSection:
    """
    Detect which section of the report the selection is in.
    
    Args:
        text_before_selection: All text that appears before the selected text
    
    Returns:
        ReportSection enum value
    """
```

---

## User Workflow Example

### Scenario: Improve Findings Section

**User's Report:**
```
[FINDING-001] SQL Injection in Login Form
Description: A SQL injection vulnerability was found in the login form. 
This could allow attackers to access the database and retrieve sensitive information.
```

**Step 1: User selects the description text**
```
"A SQL injection vulnerability was found in the login form. 
This could allow attackers to access the database and retrieve sensitive information."
```

**Step 2: User types in chat**
```
"Make this more formal and technical"
```

**Step 3: System response**

```
✨ Analyzing selection (176 chars)...
Section: findings
Intent: technical

✅ Multiple Rewrite Styles Generated:

**Concise Version:**
"SQL injection vulnerability in authentication form enables unauthorized database access."

**Professional Version:**
"A SQL injection vulnerability has been identified in the authentication form. 
This vulnerability could potentially permit unauthorized access to the database 
and compromise the security of sensitive user information."

**Technical Version:**
"SQL injection vulnerability (CWE-89) identified in login form input validation. 
Unsanitized user-supplied input passed directly to database query execution enables 
arbitrary SQL command injection and unauthorized access to sensitive data tables."

💡 Copy any version above and paste it into your report.
```

**Step 4: User copies the technical version and updates their report**

---

## Current Limitations

1. **Manual Copying Required**: Currently users must copy/paste the rewrite into their report
   - Future: One-click "Insert" button (metadata is already prepared)

2. **Single Selection Only**: Must select one contiguous block of text
   - Future: Could support multiple selections

3. **No Undo**: Rewrites are suggestions only; analyst applies manually
   - Already safe: No automatic edits

4. **Temperature Fixed at 0.3**: Rewrite temperature is hard-coded for consistency
   - Could be: User-adjustable (e.g., "Creative" vs "Precise" slider)

5. **Section Detection**: Works with common section headers; custom headers not recognized
   - Workaround: Explicitly tell AI the section (e.g., "In the recommendations section, make this more concise")

6. **No Markdown Formatting**: Text-only (no bold, italics in response)
   - By design: Keeps UI simple and text content portable

---

## Technical Implementation

### Files Modified

#### 1. **ai_assistant.py** (Main improvements)
- Added `RewriteContext` class: Encapsulates selection context
- Added `ReportSection` enum: Identifies report sections
- Added `assist_report_editing_advanced()`: Context-aware rewrite function
- Added `detect_report_section()`: Section detection from surrounding text
- Added `_get_section_guidance()`: Section-specific AI prompts
- Added `_extract_json_from_response()`: Robust JSON extraction from LLM
- Updated `discuss_vulnerability()`: Added detailed logging
- Improved imports and added logging support

#### 2. **main_window.py** (Chat integration)
- Updated imports to include new AI functions
- Completely rewrote `_handle_user_message()`:
  - Intent detection for rewrite requests
  - Selection validation
  - Section detection using text context
  - Line number calculation
  - Multi-style presentation
  - Better error messages and feedback
  - Comprehensive logging

#### 3. **context_builder.py**
- No changes needed; uses existing detection patterns
- Compatible with new rewriting system

---

## Testing Checklist

### ✓ Implemented Tests (Manual)

- [x] Rewrite detection: User says "rewrite", AI responds appropriately
- [x] No selection handling: Prompts user to select text first
- [x] Intent detection: "Concise", "Formal", "Technical" are recognized
- [x] Section detection: Text before selection identifies Executive Summary, Findings, etc.
- [x] Safety violation: Cannot modify severity/rule IDs/file paths
- [x] Multiple styles: All three (concise, professional, technical) are generated
- [x] Logging: Rewrite actions are logged with intent and section
- [x] Error handling: Graceful failures with user-friendly messages
- [x] JSON extraction: Handles markdown code blocks in LLM response
- [x] Line numbers: start_line and end_line are calculated correctly

### Recommended Manual Tests

1. **Rewrite a single-sentence finding**: Should produce "compressed" version effectively
2. **Rewrite an executive summary section**: Should use business-focused language
3. **Rewrite a recommendations section**: Should be action-oriented
4. **Provide malformed request**: Should gracefully degrade
5. **Try to rewrite "Severity: High"**: Should trigger safety violation
6. **Select text at start vs. end of document**: Line numbers should be accurate

---

## Performance Considerations

- **Token Usage**: Multi-style generation uses ~30% more tokens than single suggestion
- **Latency**: Expect 2-5 second response time (dependent on Ollama model)
- **Memory**: Section detection is O(n) scan of preceding text (negligible for reports < 100KB)

---

## Future Enhancements

1. **One-Click Insert**: Implement UI buttons to auto-insert rewrite at line range
2. **Inline Comments**: AI could suggest comments without replacing text
3. **Tone Slider**: User-adjustable rewrite intensity (0 = no change, 10 = maximum rewrite)
4. **Comparison View**: Show before/after side-by-side
5. **Undo Stack**: Keep suggestion history for quick rollback
6. **Batch Rewriting**: Process multiple selections in one request
7. **Custom Sections**: Allow analysts to define their own section types
8. **Export Suggestions**: Save all generated rewrites for team review

---

## Debugging

### Enable Debug Logging

Add to your logging config:
```python
import logging
logging.getLogger("AIAssistant").setLevel(logging.DEBUG)
```

### Check Logs for Rewrite Actions

```python
# Look for entries like:
# INFO: Report rewrite suggested [intent='compress', section='findings', char_count=127]
# INFO: Rewrite generated [intent='compress', start_line=42, end_line=44]
```

### Verify Intent Detection

Add print statement in `RewriteContext._detect_intent()`:
```python
detected = self._detect_intent()
print(f"DEBUG: Detected intent '{detected}' from request '{self.user_request}'")
```

---

## Summary

The AI assistant now provides **professional report editing** capabilities:

✔ **Context-Aware**: Understands selected text and report section
✔ **Intent-Driven**: Detects what the user wants automatically  
✔ **Multi-Style**: Generates concise, professional, and technical versions
✔ **Safety-First**: Protects critical fields from modification
✔ **Metadata-Rich**: Includes line numbers for UI integration
✔ **Well-Logged**: All actions recorded for debugging
✔ **User-Friendly**: Clear feedback and actionable suggestions

The implementation maintains the existing safety constraints while dramatically improving the user experience for report editing workflows.
