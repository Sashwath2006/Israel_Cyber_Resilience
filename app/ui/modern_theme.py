"""
Minimalist Brutalism Theme - Ollama/Vercel Inspired Design System
Clean, high-contrast UI for Vulnerability Analysis Workbench
"""

from enum import Enum


class MinimalistColors:
    """Minimalist monochrome color palette"""
    # Primary colors
    BLACK = "#000000"            # Pure black
    WHITE = "#FFFFFF"            # Pure white
    GREY_LIGHT = "#F5F5F5"       # Light grey for subtle backgrounds
    GREY_MEDIUM = "#E5E5E5"      # Medium grey for borders
    GREY_DARK = "#333333"        # Dark grey for text on light backgrounds
    
    # Backgrounds
    BG_PRIMARY = "#FFFFFF"       # Primary background (white)
    BG_SECONDARY = "#F5F5F5"     # Secondary background (light grey)
    BG_DARK = "#000000"          # Dark areas (for inverted sections)
    
    # Text colors
    TEXT_PRIMARY = "#000000"     # Primary text (black on white)
    TEXT_SECONDARY = "#666666"   # Secondary text (grey)
    TEXT_MUTED = "#999999"       # Muted text (lighter grey)
    TEXT_LIGHT = "#FFFFFF"       # Light text (white on dark)
    
    # Borders and dividers
    BORDER = "#E5E5E5"           # Standard border
    BORDER_DARK = "#333333"      # Dark border for emphasis
    DIVIDER = "#E5E5E5"          # Divider line
    
    # Status colors (restrained palette)
    SUCCESS = "#2E7D32"          # Dark green
    WARNING = "#F57C00"          # Dark orange
    DANGER = "#C62828"           # Dark red
    INFO = "#1565C0"             # Dark blue
    
    # Accents
    ACCENT_BLACK = "#000000"     # High-contrast accent
    ACCENT_DARK = "#333333"      # Secondary accent


# Backward compatibility aliases for existing code
class DeepSpaceColors(MinimalistColors):
    """Legacy color class - maps to MinimalistColors for compatibility"""
    BG_DARKEST = MinimalistColors.WHITE
    BG_DARK = MinimalistColors.WHITE
    BG_DARK_ALT = MinimalistColors.GREY_LIGHT
    BG_SECONDARY = MinimalistColors.GREY_LIGHT
    ACCENT_BLUE = MinimalistColors.ACCENT_BLACK
    ACCENT_BLUE_DIM = MinimalistColors.GREY_DARK
    ACCENT_LIME = MinimalistColors.ACCENT_BLACK
    ACCENT_LIME_DIM = MinimalistColors.GREY_DARK
    BORDER_SUBTLE = MinimalistColors.BORDER
    BORDER_LIGHT = MinimalistColors.BORDER
    GLASS_LIGHT = "transparent"
    GLASS_LIGHTER = MinimalistColors.GREY_LIGHT
    GLASS_LIGHTEST = MinimalistColors.GREY_LIGHT
    GLOW_BLUE = "transparent"
    GLOW_LIME = "transparent"


class ModernTypography:
    """Modern typography system - High-end sans-serif and monospace"""
    # Font families - prioritizing premium typefaces
    PRIMARY_FONT = "Geist, Inter, 'Segoe UI', Roboto, -apple-system, BlinkMacSystemFont, sans-serif"
    MONO_FONT = "'JetBrains Mono', 'Roboto Mono', 'Courier New', monospace"
    
    # Font sizes (in pixels)
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_BASE = 13
    SIZE_MD = 14
    SIZE_LG = 16
    SIZE_XL = 18
    SIZE_XXL = 22
    SIZE_XXXL = 28
    
    # Font weights
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


class ModernSpacing:
    """Modern spacing scale"""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 48


class ModernBorderRadius:
    """Modern border radius system - Minimalist engineered look"""
    NONE = 0       # Sharp corners for primary elements
    SM = 2         # Minimal radius
    MD = 4         # Small radius for accents
    LG = 4         # Standard radius (same as MD)
    XL = 4         # Extra (same as standard)
    FULL = 9999    # Full pill shape (rare use)


class TransitionTiming:
    """Transition timings for animations"""
    FAST = "150ms"
    BASE = "200ms"
    SLOW = "350ms"
    
    EASING = "cubic-bezier(0.4, 0, 0.2, 1)"  # Material Design easing


# Backward compatibility - ModernShadow no longer used (no shadows in minimalist design)
class ModernShadow:
    """Legacy shadow class - not used in minimalist design"""
    SM = "none"
    MD = "none"
    LG = "none"
    XL = "none"
    GLOW_BLUE = "none"
    GLOW_LIME = "none"
    GLOW_BLUE_STRONG = "none"


def generate_button_stylesheet(
    primary: bool = False,
    rounded: int = 0,
    padding: str = "8px 16px"
) -> str:
    """Generate button stylesheet with minimalist styling"""
    
    if primary:
        # Primary action button: Solid black with white text
        return f"""
            QPushButton {{
                background-color: {MinimalistColors.BLACK};
                color: {MinimalistColors.WHITE};
                border: 1px solid {MinimalistColors.BLACK};
                border-radius: {rounded}px;
                padding: {padding};
                font-weight: {ModernTypography.WEIGHT_SEMIBOLD};
                font-size: {ModernTypography.SIZE_BASE}px;
                font-family: {ModernTypography.PRIMARY_FONT};
            }}
            QPushButton:hover {{
                background-color: {MinimalistColors.GREY_DARK};
                border: 1px solid {MinimalistColors.GREY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {MinimalistColors.BLACK};
            }}
            QPushButton:disabled {{
                background-color: {MinimalistColors.GREY_LIGHT};
                color: {MinimalistColors.TEXT_MUTED};
                border: 1px solid {MinimalistColors.GREY_LIGHT};
            }}
        """
    else:
        # Secondary/Ghost button: Transparent with border, shows on hover
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {MinimalistColors.TEXT_PRIMARY};
                border: 1px solid transparent;
                border-radius: {rounded}px;
                padding: {padding};
                font-size: {ModernTypography.SIZE_BASE}px;
                font-family: {ModernTypography.PRIMARY_FONT};
            }}
            QPushButton:hover {{
                background-color: {MinimalistColors.GREY_LIGHT};
                border: 1px solid {MinimalistColors.BORDER};
            }}
            QPushButton:pressed {{
                background-color: transparent;
                border: 1px solid {MinimalistColors.BORDER_DARK};
            }}
            QPushButton:disabled {{
                color: {MinimalistColors.TEXT_MUTED};
                border: 1px solid transparent;
            }}
        """


def generate_global_stylesheet() -> str:
    """Generate global application stylesheet - Minimalist Brutalism"""
    return f"""
    /* Global Styling */
    QMainWindow, QDialog, QWidget {{
        background-color: {MinimalistColors.BG_PRIMARY};
        color: {MinimalistColors.TEXT_PRIMARY};
        font-family: {ModernTypography.PRIMARY_FONT};
        font-size: {ModernTypography.SIZE_BASE}px;
    }}
    
    QFrame {{
        background-color: transparent;
        border: none;
    }}
    
    /* Text Edit - Clean editor style */
    QTextEdit, QPlainTextEdit {{
        background-color: {MinimalistColors.WHITE};
        color: {MinimalistColors.TEXT_PRIMARY};
        border: 1px solid {MinimalistColors.BORDER};
        border-radius: {ModernBorderRadius.MD}px;
        padding: {ModernSpacing.MD}px;
        font-family: {ModernTypography.MONO_FONT};
        font-size: {ModernTypography.SIZE_BASE}px;
        selection-background-color: {MinimalistColors.GREY_LIGHT};
        selection-color: {MinimalistColors.TEXT_PRIMARY};
    }}
    
    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {MinimalistColors.BORDER_DARK};
        background-color: {MinimalistColors.WHITE};
    }}
    
    /* Combo Box - Clean Model Selector */
    QComboBox {{
        background-color: {MinimalistColors.WHITE};
        color: {MinimalistColors.TEXT_PRIMARY};
        border: 1px solid {MinimalistColors.BORDER};
        border-radius: {ModernBorderRadius.MD}px;
        padding: 6px 10px;
        font-family: {ModernTypography.PRIMARY_FONT};
        font-size: {ModernTypography.SIZE_BASE}px;
        min-height: 32px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {MinimalistColors.BORDER_DARK};
        background-color: {MinimalistColors.GREY_LIGHT};
    }}
    
    QComboBox:focus {{
        border: 1px solid {MinimalistColors.BORDER_DARK};
        background-color: {MinimalistColors.WHITE};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        color: {MinimalistColors.GREY_DARK};
    }}
    
    /* Label - Typography */
    QLabel {{
        color: {MinimalistColors.TEXT_PRIMARY};
        font-family: {ModernTypography.PRIMARY_FONT};
    }}
    
    /* Scroll Bar - Minimal Style */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {MinimalistColors.GREY_MEDIUM};
        border-radius: 4px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {MinimalistColors.GREY_DARK};
    }}
    
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
        border: none;
        background: none;
    }}
    
    /* Splitter Handle */
    QSplitter::handle {{
        background-color: {MinimalistColors.BORDER};
    }}
    
    QSplitter::handle:hover {{
        background-color: {MinimalistColors.GREY_MEDIUM};
    }}
    """
