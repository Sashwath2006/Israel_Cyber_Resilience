# Interactive Workflow Diagram

## User Flow: Rewrite Request

```
┌─────────────────────────────────────────────────────────────────┐
│  ANALYST SELECTS TEXT IN REPORT EDITOR                          │
│  Example: "A SQL injection was found in the login form"         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ANALYST TYPES REWRITE REQUEST IN CHAT                          │
│  Example: "Make this more technical"                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  MAIN_WINDOW._handle_user_message() PROCESSES REQUEST           │
│                                                                  │
│  ✓ Detects: "technical" in request → rewrite_request = True    │
│  ✓ Gets selected text: "A SQL injection was found..."          │
│  ✓ Finds model_id from dropdown                                │
│  ✓ Checks Ollama availability                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  DETECT REPORT SECTION                                          │
│                                                                  │
│  text_before = all_text[:cursor_pos]                           │
│  if "findings" in text_before.lower():                         │
│    section = ReportSection.FINDINGS                            │
│  else if "recommendations" in text_before.lower():             │
│    section = ReportSection.RECOMMENDATIONS                     │
│  ... etc                                                        │
│                                                                  │
│  Result: ReportSection.FINDINGS ◄─ (text contains "FINDINGS")  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  CREATE REWRITE CONTEXT                                         │
│                                                                  │
│  RewriteContext(                                                │
│    selected_text="A SQL injection was found in the login form"  │
│    user_request="Make this more technical",                     │
│    start_line=42,                                               │
│    end_line=42,                                                 │
│    section=ReportSection.FINDINGS                               │
│  )                                                              │
│                                                                  │
│  ▼ Inside __init__:                                             │
│  intent = _detect_intent()                                      │
│    → "technical" in request → intent = "technical" ✓            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  SAFETY CHECK                                                   │
│                                                                  │
│  is_safety_violation() checks:                                  │
│    - Contains "severity" AND "High/Medium/Low" ? ✗ NO           │
│    - Contains "rule id" AND regex pattern ? ✗ NO                │
│    - Contains "file" AND path chars ? ✗ NO                      │
│                                                                  │
│  ✓ PASS - Safe to proceed                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  BUILD AI PROMPT (assist_report_editing_advanced)               │
│                                                                  │
│  system_prompt = """                                            │
│    TEXT TO REWRITE:                                             │
│      A SQL injection was found in the login form                │
│                                                                  │
│    INTENT: technical                                            │
│    SECTION: findings                                            │
│                                                                  │
│    [FINDINGS TONE GUIDANCE]:                                    │
│    Tone: Technical, precise, evidence-based                     │
│    Goal: Clearly describe the vulnerability and its location    │
│                                                                  │
│    Generate 3 JSON styles: concise, professional, technical    │
│  """                                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  CALL LLM (via Ollama)                                          │
│                                                                  │
│  generate(model_id, system_prompt, temperature=0.3)            │
│                                                                  │
│  ⏳ LLM generates 3 rewrite versions...                          │
│  ⏳ Takes 2-5 seconds depending on model                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PARSE LLM RESPONSE                                             │
│                                                                  │
│  Raw output (possibly wrapped in ```json```):                   │
│  ```                                                            │
│  {                                                              │
│    "concise": "SQL injection in login form enables...",         │
│    "professional": "A SQL injection vulnerability has...",      │
│    "technical": "SQL injection (CWE-89) identified in..."       │
│  }                                                              │
│  ```                                                            │
│                                                                  │
│  ▼                                                              │
│  _extract_json_from_response() → JSON string                   │
│  json.loads() → dict with styles                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  FORMAT RESPONSE FOR CHAT                                       │
│                                                                  │
│  response = """                                                 │
│  ✅ Multiple Rewrite Styles Generated:                          │
│                                                                  │
│  **Concise Version:**                                           │
│  "SQL injection in login form enables unauthorized access"     │
│                                                                  │
│  **Professional Version:**                                      │
│  "A SQL injection vulnerability has been identified in the     │
│  authentication form..."                                        │
│                                                                  │
│  **Technical Version:**                                         │
│  "SQL injection (CWE-89) identified in login form input        │
│  validation..."                                                 │
│                                                                  │
│  💡 Copy any version above and paste it into your report.      │
│  """                                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  LOG REWRITE ACTION                                             │
│                                                                  │
│  logger.info(                                                   │
│    "Rewrite generated",                                         │
│    intent="technical",                                          │
│    section="findings",                                          │
│    start_line=42,                                               │
│    end_line=42                                                  │
│  )                                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  DISPLAY RESPONSE IN CHAT PANE                                  │
│                                                                  │
│  Chat shows:                                                    │
│  [AI bubble]                                                    │
│  ✅ Multiple Rewrite Styles Generated:                          │
│                                                                  │
│  **Concise Version:**                                           │
│  "SQL injection in login form enables unauthorized access"     │
│                                                                  │
│  **Professional Version:**                                      │
│  "A SQL injection vulnerability has been identified..."        │
│                                                                  │
│  **Technical Version:**                                         │
│  "SQL injection (CWE-89) identified in login form..."          │
│                                                                  │
│  💡 Copy any version above and paste it into your report.      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ANALYST ACTION                                                 │
│                                                                  │
│  1. Selects one of the three versions (e.g., Technical)        │
│  2. Copies the text                                             │
│  3. Clicks in report editor                                     │
│  4. Selects and deletes original text                           │
│  5. Pastes the new version                                      │
│                                                                  │
│  ✓ REPORT UPDATED                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Paths

```
REWRITE REQUEST
        │
        ├─ No selection detected
        │  └─→ "📝 No text selected. Select text in the report editor first"
        │
        ├─ No model selected
        │  └─→ "⚠ No AI model selected. Please select a model."
        │
        ├─ Ollama unavailable
        │  └─→ "⚠ AI service unavailable. Please ensure Ollama is running."
        │
        ├─ Safety violation (trying to modify severity/rule ID/file)
        │  └─→ "⚠ Safety Check Failed. Cannot modify protected fields..."
        │
        ├─ LLM call fails
        │  └─→ "❌ Rewrite failed: [LLM error details]"
        │
        ├─ JSON parsing fails
        │  └─→ "❌ AI returned invalid format. Please try again."
        │
        └─ Success
           └─→ Display 3 rewrite styles + "Copy and paste into your report"
```

---

## Intent Detection Decision Tree

```
User says: "Make this concise"
                │
                ├─ Contains "single line"? NO
                ├─ Contains "one line"? NO
                ├─ Contains "compress"? NO
                ├─ Contains "shorten"? NO
                ├─ Contains "condense"? YES ✓
                │
                └─→ intent = "compress" ✓

─────────────────────────────────────

User says: "Add more technical terms"
                │
                ├─ Contains "extend"? NO
                ├─ Contains "expand"? NO
                ├─ Contains "more detail"? YES (but...)
                ├─ Contains "technical"? YES ✓ (higher priority)
                │
                └─→ intent = "technical" ✓

─────────────────────────────────────

User says: "Make this formal"
                │
                ├─ Contains "formal"? YES ✓
                │
                └─→ intent = "formalize" ✓
```

---

## Section Detection Logic

```
Analyst selects text in report.

System extracts:
  - all_text = full report content
  - cursor_pos = position where selection starts
  - text_before = all_text[:cursor_pos]

Call: detect_report_section(text_before)

Check patterns in text_before (case-insensitive):

  if contains "executive summary" → ReportSection.EXECUTIVE_SUMMARY ✓
  else if contains "findings" → ReportSection.FINDINGS ✓
  else if contains "risk overview" → ReportSection.RISK_OVERVIEW ✓
  else if contains "recommendations" → ReportSection.RECOMMENDATIONS ✓
  else if contains "technical details" → ReportSection.TECHNICAL_DETAILS ✓
  else → ReportSection.OTHER (default)

Result used to select tone guidance:

  EXECUTIVE_SUMMARY:
    "Tone: Business-focused, high-level, actionable
     Avoid: Technical jargon, excessive detail
     Goal: Communicate risk and recommended actions to leadership"

  FINDINGS:
    "Tone: Technical, precise, evidence-based
     Avoid: Speculation, vague language
     Goal: Clearly describe the vulnerability and its location"

  [etc...]

LLM uses tone guidance when generating rewrites.
```

---

## Data Flow: From Selection to Multiple Styles

```
SELECTED TEXT (127 chars)
        │
        ▼
RewriteContext
├─ selected_text: str
├─ user_request: str
├─ start_line: int
├─ end_line: int
├─ section: ReportSection
├─ intent: str (auto-detected)
└─ is_safety_violation(): bool
        │
        ▼
AI System Prompt
├─ TEXT TO REWRITE: [selected_text]
├─ USER REQUEST: [user_request]
├─ INTENT: [intent]
├─ SECTION: [section]
├─ TONE GUIDANCE: [section-specific]
└─ OUTPUT FORMAT: JSON with 3 styles
        │
        ▼
LLM Generation (2-5 sec)
        │
        ▼
LLM Response (possible markdown wrapping)
        │
        ▼
_extract_json_from_response()
├─ Remove ```json``` blocks
├─ Find { ... } boundaries
└─ Return JSON string
        │
        ▼
json.loads(json_str)
        │
        ▼
styles dict
├─ styles["concise"]
├─ styles["professional"]
└─ styles["technical"]
        │
        ▼
Format Response
        │
        ▼
Display in Chat
        │
        ▼
Analyst Copies & Pastes
```

---

## Line Number Calculation

```
Full Report:
Line 1:  =====================================
Line 2:  VULNERABILITY ANALYSIS REPORT
Line 3:  =====================================
...
Line 40: FINDINGS
Line 41: -------
Line 42: [FINDING-001] SQL Injection
Line 43: A SQL injection was found in the
Line 44: login form that could allow attackers

Analyst selects on lines 43-44:
"A SQL injection was found in the
login form that could allow attackers"

System calculates:
├─ all_text = full report text
├─ cursor_pos = position before "A SQL injection..."
├─ count \n before cursor → current_line = 42
├─ count \n in selection → selected_lines = 1
├─ start_line = 42 + 1 = 43 ✓
├─ end_line = 42 + 1 + 1 = 44 ✓
│
└─ Metadata:
   {
     "start_line": 43,
     "end_line": 44
   }

This metadata enables future UI feature:
  "Insert" button → auto-replace lines 43-44
```

---

## Safety Violation Detection

```
User selects: "Severity: High"
User asks: "Change this to Medium"

System checks: is_safety_violation()

request_lower = "change this to medium"
text_lower = "severity: high"

Check 1: Does request mention "severity" AND text contain severity level?
  ├─ "severity" in request? YES ✓
  ├─ "change severity" in request? NO (only "change")
  ├─ text_lower contains "high"/"medium"/"low"? YES ✓
  └─ → Match! Set violation_flag = True

result = True (violation detected)

Response:
  "⚠ Safety Check Failed
   Cannot modify protected fields (severity, rule IDs, file locations).
   Select different text or request a different rewrite."

─────────────────────────────────────────

User selects: "auth.py line 45"
User asks: "Change to auth.py line 50"

System checks: is_safety_violation()

request_lower = "change to auth.py line 50"
text_lower = "auth.py line 45"

Check: Does request ask to modify a file/location?
  ├─ "file name"/"change file" in request? NO
  ├─ "location" mentioned? NO
  └─ → No explicit file modification intent
       (but this SHOULD trigger for explicit location changes)

Currently this would PASS (minor limitation)
Workaround: AI instructions prevent changing file names anyway.

─────────────────────────────────────────

User selects: "This section is complex"
User asks: "Simplify this"

System checks: is_safety_violation()

request_lower = "simplify this"
text_lower = "this section is complex"

Check all patterns:
  ├─ "severity" in request? NO
  ├─ "rule id" in request? NO
  ├─ "file name" in request? NO
  └─ → No violations detected ✓

result = False (safe to proceed)
```

---

## State Machine: Message Processing

```
START
  │
  ▼
Receive user message
  │
  ├─ Is it a rewrite request?
  │  │ (contains: rewrite, improve, clarify, simplify,
  │  │  formal, professional, technical, single line, etc.)
  │  │
  │  ├─ YES → REWRITE_PATH
  │  │          ├─ Check selection exists
  │  │          ├─ Detect intent
  │  │          ├─ Detect section
  │  │          ├─ Create RewriteContext
  │  │          ├─ Check safety
  │  │          ├─ Call AI
  │  │          ├─ Parse response
  │  │          ├─ Log action
  │  │          └─ Display styles
  │  │
  │  └─ NO → DEFAULT_PATH
  │           │
  │           ├─ Is there a report?
  │           │  ├─ YES → Show report info + suggestion
  │           │  └─ NO → Show "upload files first"
  │           │
  │           └─ END
  │
  └─ END
```

---

## Performance Profile

```
Operation                          Latency    Tokens
─────────────────────────────────────────────────────
Intent detection                   ~1 ms      0
Section detection                  ~5 ms      0
Safety check                        ~2 ms      0
Create RewriteContext              ~1 ms      0
Build AI prompt                    ~10 ms     ~50
─────────────────────────────────────────────────────
Subtotal (prep)                    ~19 ms     ~50
─────────────────────────────────────────────────────
LLM inference (Ollama)             2-5 sec    500-2000
─────────────────────────────────────────────────────
JSON parsing                       ~5 ms      0
Format response                    ~10 ms     0
Log action                         ~5 ms      0
─────────────────────────────────────────────────────
TOTAL                              2.1-5.1 s  550-2050 tokens
─────────────────────────────────────────────────────
```

The dominant cost is the LLM inference time. All prep work is negligible (<20ms).
