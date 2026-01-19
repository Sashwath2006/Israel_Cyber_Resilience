# Guided Workflow Implementation Summary

## Overview
Implemented a page-by-page guided workflow for the offline hybrid vulnerability analysis application. The workflow guides users through document upload, scanning, draft review, editing, and final export.

## Workflow Changes

### Page Structure
The application now uses a 5-page workflow:

1. **Page 1: Document Upload**
   - User uploads files (ZIP/folder/multiple)
   - Uploaded paths stored in ReportState
   - No scan yet
   - Shows success summary
   - "Next" button enabled after upload

2. **Page 2: Automated Scan**
   - Runs rule-based scan automatically when page is entered
   - Shows progress indicator
   - Displays scan status and results
   - "Next" button disabled until scan completes

3. **Page 3: Sample PDF Report (Draft)**
   - Automatically generates draft PDF report
   - Labeled as "Sample Report - Draft"
   - PDF is preview-only (shows markdown preview)
   - No export buttons enabled

4. **Page 4: Review & Edit Mode**
   - Top: Scrollable editable report preview (markdown format)
   - Bottom: Chat/Edit assistant
   - User can:
     - Edit report manually
     - Ask AI to rewrite sections, clarify findings, explain vulnerabilities
   - AI suggestions:
     - Previewed before application
     - Require explicit acceptance
   - AI can answer questions about findings and locations

5. **Page 5: Final Confirmation & Export**
   - User must explicitly confirm: "Mark this report as final"
   - Only after confirmation:
     - Export buttons enabled (PDF / MD / JSON)
   - Final exported PDF:
     - Removes "Draft" labeling
     - Reflects all accepted edits

## New UI/Page Components

### Navigation Bar
- Previous/Next buttons
- Page indicator showing current page and name
- Buttons enabled/disabled based on page state

### Page Widgets
- `_build_page_1_upload()`: Document upload interface
- `_build_page_2_scan()`: Scan progress and results
- `_build_page_3_draft()`: Draft PDF preview
- `_build_page_4_review()`: Review & edit with splitter (preview + chat)
- `_build_page_5_export()`: Final confirmation and export

### Report State Structure

**New File: `app/report_state.py`**
- `ReportState` class: Central state management
- `ReportStatus` enum: Tracks workflow status
- Tracks:
  - Uploaded document paths
  - Scan results (chunks, findings)
  - Report workspace
  - Draft PDF path
  - Final confirmation status
  - All edits and AI suggestions

**Key Methods:**
- `set_uploaded()`: Store uploaded paths
- `set_scanned()`: Store scan results
- `set_draft_generated()`: Store draft PDF path
- `set_in_review()`: Enter review mode
- `confirm_final()`: Mark as final
- `can_export()`: Check if export allowed

## AI Safety Enforcement

### Preserved Constraints
- ✅ Rule-based scanning remains deterministic
- ✅ LLM does not parse raw documents
- ✅ LLM does not discover vulnerabilities
- ✅ LLM does not auto-edit reports (requires explicit acceptance)
- ✅ Export only after user confirmation
- ✅ No cloud APIs
- ✅ No auto-persist of final reports

### AI Interaction Safety
- All AI suggestions are previewed
- User must explicitly accept AI edits
- AI edits modify report state, not files directly
- AI cannot override severity (enforced by existing validation)
- AI responses grounded in findings data only

## Files Modified/Added

### New Files
1. **`app/report_state.py`**
   - Central report state management
   - ReportStatus enum
   - ReportState class

### Modified Files
1. **`app/main_window.py`**
   - Complete restructure to page-based workflow
   - Added QStackedWidget for pages
   - Added navigation bar
   - Added 5 page widgets
   - Updated chat interface to work with Page 4
   - Updated report preview regeneration
   - Legacy code preserved but not used in new workflow

2. **`app/report_exporter.py`**
   - Added draft label support
   - Markdown export includes draft label in title
   - PDF export includes draft label in title
   - Final exports remove draft label

## Manual Testing Steps

### Test Page 1: Document Upload
1. Launch application
2. Verify Page 1 is displayed
3. Click "Upload Documents"
4. Select test files (e.g., from `test_files/`)
5. Verify files appear in summary
6. Verify "Next" button is enabled

### Test Page 2: Automated Scan
1. Click "Next" from Page 1
2. Verify Page 2 is displayed
3. Verify progress indicator appears
4. Verify scan status updates
5. Verify scan results summary appears
6. Verify "Next" button enabled after scan completes

### Test Page 3: Draft PDF Preview
1. Click "Next" from Page 2
2. Verify Page 3 is displayed
3. Verify draft PDF is generated (or markdown preview shown)
4. Verify "Draft" label is visible
5. Verify "Next" button is enabled

### Test Page 4: Review & Edit
1. Click "Next" from Page 3
2. Verify Page 4 is displayed with:
   - Report preview on top
   - Chat interface on bottom
3. Test manual editing:
   - Edit report preview text
   - Verify changes are reflected
4. Test AI editing:
   - Type "rewrite the executive summary" in chat
   - Verify AI suggestion appears
   - Accept suggestion
   - Verify preview updates
5. Test AI discussion:
   - Ask "Why is this risky?" about a finding
   - Verify grounded response

### Test Page 5: Final Confirmation & Export
1. Click "Next" from Page 4
2. Verify Page 5 is displayed
3. Verify export buttons are disabled
4. Click "Mark Report as Final"
5. Confirm in dialog
6. Verify export buttons are enabled
7. Test PDF export:
   - Click "Export PDF"
   - Save to file
   - Verify PDF has no "Draft" label
8. Test Markdown export:
   - Click "Export Markdown"
   - Save to file
   - Verify markdown content
9. Test JSON export:
   - Click "Export JSON"
   - Save to file
   - Verify JSON structure

### Test Navigation
1. Test "Previous" button on each page
2. Test "Next" button validation (should prevent skipping steps)
3. Test page state persistence when navigating back/forward

## Completion Criteria

✅ **All 5 pages implemented**
- Page 1: Document Upload
- Page 2: Automated Scan
- Page 3: Draft PDF Preview
- Page 4: Review & Edit
- Page 5: Final Confirmation & Export

✅ **Navigation working**
- Previous/Next buttons functional
- Page state validation
- Button enable/disable logic

✅ **Report state management**
- Central ReportState class
- State tracking through workflow
- Export only after final confirmation

✅ **AI safety preserved**
- No auto-editing
- Explicit acceptance required
- Grounded responses only

✅ **Draft labeling**
- Draft PDFs labeled correctly
- Final PDFs have no draft label
- Markdown export respects draft status

✅ **UI requirements met**
- Black & white only
- Minimal design
- Clear page navigation
- Clear labels ("Draft Report", "AI Suggestion", "Final Report")
- Chat UI below report preview on Page 4

## Git Commit Message

```
feat: Implement guided page-by-page workflow for vulnerability analysis

- Add ReportState class for central state management
- Restructure UI to use QStackedWidget with 5 pages
- Page 1: Document Upload (store paths, no scan yet)
- Page 2: Automated Scan (progress indicator, results)
- Page 3: Draft PDF Preview (auto-generated, labeled as draft)
- Page 4: Review & Edit (editable preview + chat assistant)
- Page 5: Final Confirmation & Export (requires explicit confirmation)
- Add navigation bar with Previous/Next buttons
- Update PDF/Markdown export to handle draft labels
- Preserve all AI safety constraints
- Export only enabled after final confirmation
- Report preview regenerates on edits

All non-negotiable constraints preserved:
- Rule-based scanning remains deterministic
- LLM does not parse documents or discover vulnerabilities
- No auto-editing or auto-export
- No cloud APIs
- No auto-persist
```
