"""
Modern Design System for Security Audit UI.

Comprehensive theming system with tokens, colors, spacing, typography, and components.
"""


class Colors:
    """Monochrome color palette."""
    # Primary backgrounds
    BG_PRIMARY = "#FFFFFF"          # White background
    BG_SECONDARY = "#F7F7F7"        # Light gray background
    BG_TERTIARY = "#F0F0F0"         # Slightly darker gray for user messages
    
    # Text colors
    TEXT_PRIMARY = "#111111"        # Dark text
    TEXT_SECONDARY = "#666666"      # Medium gray text
    TEXT_INVERSE = "#FFFFFF"        # White text (for dark backgrounds)
    
    # UI elements
    BORDER = "#E5E5E5"              # Light border color
    HOVER = "#F5F5F5"               # Hover state background
    ACCENT = "#000000"              # Black accent color
    
    # Status colors (minimal)
    ERROR = "#DC2626"               # Red for errors
    WARNING = "#EA8C00"             # Orange for warnings
    SUCCESS = "#16A34A"             # Green for success
    INFO = "#0284C7"                # Blue for info


class Spacing:
    """Spacing scale in pixels."""
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


class Typography:
    """Typography constants."""
    # Fonts
    PRIMARY_FONT = "Inter, 'Segoe UI', Roboto, sans-serif"
    MONO_FONT = "'Monaco', 'Courier New', monospace"
    
    # Font sizes
    LABEL_SIZE = 11
    BODY_SIZE = 13
    BUTTON_SIZE = 13
    HEADING_SIZE = 16
    LARGE_HEADING_SIZE = 28
    
    # Font weights
    NORMAL = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700


class Shadow:
    """Shadow definitions."""
    NONE = "none"
    SMALL = "0 1px 2px rgba(0, 0, 0, 0.05)"
    MEDIUM = "0 4px 6px rgba(0, 0, 0, 0.1)"
    LARGE = "0 10px 15px rgba(0, 0, 0, 0.1)"


class BorderRadius:
    """Border radius values."""
    NONE = 0
    SM = 4
    MD = 8
    LG = 12
    XL = 16
    FULL = 9999


class Transitions:
    """Animation and transition constants."""
    FAST = "100ms"
    NORMAL = "200ms"
    SLOW = "300ms"
    
    EASING = "cubic-bezier(0.4, 0, 0.2, 1)"


class Buttons:
    """Button styling constants."""
    MIN_HEIGHT = 36
    PADDING_X = 16
    PADDING_Y = 8


class Components:
    """Component-specific constants."""
    # Navigation bar
    NAV_HEIGHT = 56
    NAV_PADDING = 12
    
    # Chat interface
    CHAT_BUBBLE_RADIUS = 16
    CHAT_BUBBLE_MAX_WIDTH = 600
    CHAT_MESSAGE_SPACING = 16
    CHAT_INPUT_MIN_HEIGHT = 44
    
    # Scrollbars
    SCROLLBAR_WIDTH = 6
    SCROLLBAR_THUMB = "#CCCCCC"
    SCROLLBAR_THUMB_HOVER = "#999999"


class Feedback:
    """Feedback and user interaction constants."""
    CONFIRMATION_DURATION = 2000  # milliseconds
    ERROR_DURATION = 4000
    
    LOADING_SPINNER_SIZE = 24
    ICON_SIZE = 16


class PathHighlighter:
    """Path highlighting for file system contexts."""
    HIGHLIGHT_COLOR = "#FFE5CC"


class Theme:
    """Unified theme container."""
    # Color palette
    colors = Colors()
    
    # Spacing
    spacing = Spacing()
    
    # Typography
    typography = Typography()
    
    # Shadows
    shadow = Shadow()
    
    # Border radius
    border_radius = BorderRadius()
    
    # Transitions
    transitions = Transitions()
    
    # Component sizes
    buttons = Buttons()
    components = Components()
    
    # Feedback
    feedback = Feedback()
    
    # Highlighting
    path_highlighter = PathHighlighter()
