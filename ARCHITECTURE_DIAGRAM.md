# RICH-TEXT EDITOR ARCHITECTURE DIAGRAM

## 📐 System Architecture

```
╔════════════════════════════════════════════════════════════════════════╗
║                         MAIN WINDOW                                    ║
║                    (app/main_window.py)                                ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────────────────────────────────────────────────────┐    ║
║  │               TOP TOOLBAR                                    │    ║
║  │  [Model Selector] [Finalize] [Export ▼]                    │    ║
║  └──────────────────────────────────────────────────────────────┘    ║
║                                                                        ║
║  ┌────────────────────────────────────┬─────────────────────────┐    ║
║  │     LEFT PANE: REPORT EDITOR       │   RIGHT PANE:          │    ║
║  │                                     │    CHAT ASSISTANT      │    ║
║  │  ┌──────────────────────────────┐  │                        │    ║
║  │  │   Editor Toolbar             │  │  ┌─────────────────┐   │    ║
║  │  │   (app/ui/editor_toolbar.py) │  │  │ Chat Messages   │   │    ║
║  │  │                              │  │  │                 │   │    ║
║  │  │ [B][I][U] [Font▼] [Size▼]  │  │  │ • Message 1     │   │    ║
║  │  │ [Color] [Highlight]         │  │  │ • Message 2     │   │    ║
║  │  │ [≣⬅] [≣↔] [≣⬈] [≡]         │  │  │                 │   │    ║
║  │  │ [• List] [1. List] [➘][➙]  │  │  ├─────────────────┤   │    ║
║  │  │ [📊] [―――] [📷] [🔍+][🔍−] │  │  │ [Input Box]     │   │    ║
║  │  └──────────────────────────────┘  │  │ [Send Button]   │   │    ║
║  │                                     │  └─────────────────┘   │    ║
║  │  ┌──────────────────────────────┐  │                        │    ║
║  │  │    Report Editor Widget      │  │                        │    ║
║  │  │  (app/ui/report_editor.py)   │  │                        │    ║
║  │  │                              │  │                        │    ║
║  │  │  ┌──────────────────────┐   │  │                        │    ║
║  │  │  │                      │   │  │                        │    ║
║  │  │  │  Rich Text Content   │   │  │                        │    ║
║  │  │  │  • Bold text         │   │  │                        │    ║
║  │  │  │  • Italic text       │   │  │                        │    ║
║  │  │  │  • Formatted lists   │   │  │                        │    ║
║  │  │  │  • Aligned text      │   │  │                        │    ║
║  │  │  │                      │   │  │                        │    ║
║  │  │  └──────────────────────┘   │  │                        │    ║
║  │  └──────────────────────────────┘  │                        │    ║
║  └────────────────────────────────────┴─────────────────────────┘    ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

## 🏗️ Component Hierarchy

```
ReportEditor (QTextEdit subclass)
├── get_toolbar()
│   └── EditorToolbar (QToolBar subclass)
│       ├── Font Section
│       │   ├── font_family (QComboBox)
│       │   ├── font_size (QSpinBox)
│       │   ├── bold_action (QAction, checkable)
│       │   ├── italic_action (QAction, checkable)
│       │   ├── underline_action (QAction, checkable)
│       │   ├── strikethrough_action (QAction, checkable)
│       │   ├── superscript_action (QAction, checkable)
│       │   └── subscript_action (QAction, checkable)
│       │
│       ├── Color Section
│       │   ├── text_color_action (Color picker)
│       │   └── highlight_color_action (Color picker)
│       │
│       ├── Alignment Section
│       │   ├── align_left_action (QAction, checkable)
│       │   ├── align_center_action (QAction, checkable)
│       │   ├── align_right_action (QAction, checkable)
│       │   ├── align_justify_action (QAction, checkable)
│       │   └── alignment_group (QButtonGroup - mutually exclusive)
│       │
│       ├── List Section
│       │   ├── bullet_list_action (QAction, checkable)
│       │   ├── numbered_list_action (QAction, checkable)
│       │   ├── indent_increase_action (QAction)
│       │   ├── indent_decrease_action (QAction)
│       │   └── line_spacing (QComboBox)
│       │
│       ├── Advanced Section
│       │   ├── insert_table_action (QAction)
│       │   ├── insert_line_action (QAction)
│       │   └── insert_image_action (QAction)
│       │
│       ├── View Section
│       │   ├── zoom_in_action (QAction)
│       │   └── zoom_out_action (QAction)
│       │
│       └── Editing Section
│           ├── undo_action (QAction)
│           ├── redo_action (QAction)
│           ├── clear_fmt_action (QAction)
│           └── select_all_action (QAction)
│
└── Formatting Logic
    ├── _toggle_bold()
    ├── _toggle_italic()
    ├── _toggle_underline()
    ├── _toggle_strikethrough()
    ├── _toggle_superscript()
    ├── _toggle_subscript()
    ├── _apply_font_family()
    ├── _apply_font_size()
    ├── _apply_text_color()
    ├── _apply_highlight_color()
    ├── _clear_all_formatting()
    ├── _apply_alignment()
    ├── _toggle_bullet_list()
    ├── _toggle_numbered_list()
    ├── _increase_indent()
    ├── _decrease_indent()
    ├── _apply_line_spacing()
    ├── _insert_table()
    ├── _insert_horizontal_line()
    ├── _insert_image()
    ├── _zoom_in()
    ├── _zoom_out()
    └── State Management
        ├── _on_text_changed()
        ├── _on_cursor_changed()
        └── set_finalized()
```

## 🔄 Signal/Slot Connection Flow

```
TOOLBAR SIGNALS                    EDITOR SLOTS
═════════════════════════════════════════════════════════════

bold_toggled(bool)        ────→   _toggle_bold(bool)
italic_toggled(bool)      ────→   _toggle_italic(bool)
underline_toggled(bool)   ────→   _toggle_underline(bool)
strikethrough_toggled()   ────→   _toggle_strikethrough()
superscript_toggled()     ────→   _toggle_superscript()
subscript_toggled()       ────→   _toggle_subscript()

font_family_changed(str)  ────→   _apply_font_family(str)
font_size_changed(int)    ────→   _apply_font_size(int)

text_color_selected()     ────→   _apply_text_color()
highlight_color_selected()────→   _apply_highlight_color()

alignment_changed()       ────→   _apply_alignment()
bullet_list_triggered()   ────→   _toggle_bullet_list()
numbered_list_triggered() ────→   _toggle_numbered_list()
indent_increased()        ────→   _increase_indent()
indent_decreased()        ────→   _decrease_indent()
line_spacing_changed()    ────→   _apply_line_spacing()

undo_triggered()          ────→   undo()
redo_triggered()          ────→   redo()
clear_formatting_triggered────→   _clear_all_formatting()
select_all_triggered()    ────→   selectAll()

insert_table_triggered()  ────→   _insert_table()
insert_line_triggered()   ────→   _insert_horizontal_line()
insert_image_triggered()  ────→   _insert_image()

zoom_in_triggered()       ────→   _zoom_in()
zoom_out_triggered()      ────→   _zoom_out()


EDITOR SIGNALS                     TOOLBAR/MAIN WINDOW SLOTS
═══════════════════════════════════════════════════════════════

cursorPositionChanged()   ────→   toolbar.update_formatting_state()
textChanged()             ────→   content_changed signal
```

## 📊 Class Diagram

```
┌──────────────────────────────────────────────────┐
│         FormattingActions (Utility Class)         │
├──────────────────────────────────────────────────┤
│ Static Methods:                                  │
│ + get_char_format()                              │
│ + get_block_format()                             │
│ + set_bold()                                     │
│ + set_italic()                                   │
│ + set_underline()                                │
│ + set_strikethrough()                            │
│ + set_superscript()                              │
│ + set_subscript()                                │
│ + set_font_family()                              │
│ + set_font_size()                                │
│ + set_text_color()                               │
│ + set_highlight_color()                          │
│ + clear_formatting()                             │
│ + set_alignment()                                │
│ + set_line_spacing()                             │
│ + set_indentation()                              │
│ + is_bold()                                      │
│ + is_italic()                                    │
│ + is_underline()                                 │
│ + is_strikethrough()                             │
│ + get_alignment()                                │
└──────────────────────────────────────────────────┘
                       ▲
                       │ uses
                       │
┌──────────────────────────────────────────────────┐
│      EditorToolbar(QToolBar)                     │
├──────────────────────────────────────────────────┤
│ Widgets:                      Actions:           │
│ • font_family (QComboBox)     • bold_action     │
│ • font_size (QSpinBox)        • italic_action   │
│ • line_spacing (QComboBox)    • underline_action│
│                                • ... etc        │
│ Signals:                                         │
│ + bold_toggled(bool)                             │
│ + italic_toggled(bool)                           │
│ + font_family_changed(str)                       │
│ + alignment_changed(Qt.Alignment)                │
│ + ... 20+ signals total                          │
│                                                  │
│ Methods:                                         │
│ + update_formatting_state()                      │
│ + set_undo_enabled()                             │
│ + set_redo_enabled()                             │
└──────────────────────────────────────────────────┘
                       ▲
                       │ uses
                       │
┌──────────────────────────────────────────────────┐
│      ReportEditor(QTextEdit)                     │
├──────────────────────────────────────────────────┤
│ Member Variables:                                │
│ • toolbar: EditorToolbar                        │
│ • is_finalized: bool                            │
│ • zoom_level: int                               │
│ • current_font_family: str                      │
│ • current_font_size: int                        │
│                                                  │
│ Signals:                                         │
│ + content_changed()                              │
│ + formatting_changed()                           │
│ + status_message(str)                            │
│                                                  │
│ Public Methods:                                  │
│ + get_toolbar() → EditorToolbar                 │
│ + set_finalized(bool)                            │
│ + get_html() → str                              │
│ + get_plain_text() → str                        │
│ + set_html_content(str)                         │
│ + set_plain_text_content(str)                   │
│ + get_word_count() → int                        │
│ + get_char_count() → int                        │
│ + find_and_replace() → int                      │
│                                                  │
│ Protected Methods:                               │
│ - _toggle_bold/italic/underline/etc            │
│ - _apply_font_family/size/color/highlight     │
│ - _apply_alignment()                            │
│ - _insert_table/line/image()                    │
│ - _zoom_in/out()                                │
│ - _on_text_changed()                            │
│ - _on_cursor_changed()                          │
│ - _setup_shortcuts()                            │
│ - _connect_toolbar_signals()                    │
└──────────────────────────────────────────────────┘
```

## 📁 File Organization

```
app/
├── ui/                                [NEW DIRECTORY]
│   ├── __init__.py                   [NEW - 12 lines]
│   │   └─ Exports: ReportEditor, EditorToolbar
│   │
│   ├── formatting_actions.py         [NEW - 180 lines]
│   │   └─ Class: FormattingActions
│   │      └─ 20+ static formatting methods
│   │
│   ├── editor_toolbar.py             [NEW - 380 lines]
│   │   └─ Class: EditorToolbar(QToolBar)
│   │      ├─ 7 toolbar sections
│   │      ├─ 20+ signals
│   │      ├─ Color pickers
│   │      └─ Button management
│   │
│   └── report_editor.py              [NEW - 525 lines]
│       └─ Class: ReportEditor(QTextEdit)
│           ├─ Toolbar integration
│           ├─ 20+ formatting methods
│           ├─ Advanced features
│           ├─ State management
│           └─ Export compatibility
│
├── main_window.py                   [MODIFIED - integration]
│   ├─ Import: from app.ui import ReportEditor, EditorToolbar
│   ├─ Removed: Old ReportEditor class
│   └─ Updated: _build_ui() method
│
└── [other files - unchanged]
```

## 🔌 Integration Points

```
MainWindow._build_ui()
    │
    ├─→ Creates ReportEditor() instance
    │   └─ This includes EditorToolbar
    │
    ├─→ Gets toolbar: editor.get_toolbar()
    │
    ├─→ Adds to layout:
    │   ├─ Top bar: Model selector & export buttons
    │   ├─ Toolbar: editor.get_toolbar()
    │   ├─ Editor: self.report_editor
    │   └─ Chat: self.chat_pane
    │
    └─→ Display report:
        self.report_editor.setPlainText(report_text)

Export Pipeline (unchanged)
    │
    ├─→ Uses self.report_data (structured object)
    ├─→ NOT self.report_editor.toHtml()
    └─→ Independent from editor

Finalization
    │
    └─→ self.report_editor.set_finalized(True)
        ├─ setReadOnly(True)
        ├─ Visual feedback (gray background)
        └─ Toolbar limited
```

## ✨ Data Flow: Formatting Example

```
User Action: Click Bold Button
    ↓
toolbar.bold_action.triggered() signal emitted
    ↓
toolbar.bold_toggled(True) signal emitted
    ↓
SlotsEditor._toggle_bold(True) called
    ↓
Get cursor: cursor = self.textCursor()
    ↓
Apply formatting: FA.set_bold(cursor, True)
    │   ↓
    │   Create format: fmt = cursor.charFormat()
    │   Set: fmt.setFontWeight(QFont.Bold)
    │   Merge: cursor.mergeCharFormat(fmt)
    ↓
Update editor: self.setTextCursor(cursor)
    ↓
QTextEdit emits: textChanged() signal
    ↓ (asynchronously)
QTextEdit emits: cursorPositionChanged() signal
    ↓
editor._on_cursor_changed() called
    ↓
Get formatting: char_fmt = cursor.charFormat()
                block_fmt = cursor.blockFormat()
    ↓
Update toolbar: toolbar.update_formatting_state(char_fmt, block_fmt)
    ├─ toolbar.bold_action.setChecked(True)
    ├─ toolbar.italic_action.setChecked(False)
    └─ ... other buttons
    ↓
User sees: Bold button highlighted/pressed
```

## 🎯 State Management

```
ReportEditor State Variables:
├─ is_finalized: bool
│   ├─ False (default) = editing allowed
│   └─ True = read-only, limited toolbar
│
├─ zoom_level: int (50-200)
│   └─ Affects display font size
│
├─ current_font_family: str
│   └─ Tracks last selected font
│
├─ current_font_size: int
│   └─ Tracks last selected size
│
└─ toolbar: EditorToolbar
    └─ Manages all formatting toolbar state

QTextEdit Built-in:
├─ undo/redo stack (unlimited history)
├─ document state (content)
├─ cursor position
├─ selection state
└─ formatting at cursor
```

---

**This architecture ensures:**
- ✅ Clean separation of concerns
- ✅ Modular, testable components
- ✅ Efficient signal/slot communication
- ✅ Easy to maintain and extend
- ✅ High performance (no document recreation)
- ✅ Professional UI/UX
