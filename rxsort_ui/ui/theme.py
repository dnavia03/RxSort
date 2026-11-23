"""
ui/theme.py
------------
Design tokens for the RxSort touchscreen interface: a clinical, high-contrast
palette (deep teal + amber accent, echoing the project's own logo) and a
single type family used consistently across the app, sized for finger-touch
use on a small display.
"""

import tkinter as tk
from tkinter import ttk

# Color palette -----------------------------------------------------------
BG = "#F4F7F8"            # app background
SURFACE = "#FFFFFF"       # cards / panels
TEAL = "#0F7173"          # primary brand color
TEAL_DARK = "#0A4F50"     # pressed / header
BLUE = "#2E86AB"          # secondary accent
AMBER = "#F2A541"         # highlight (active bin, selected tab)
GREEN = "#2E7D32"         # success / sorted
RED = "#C62828"           # reject / alert
TEXT = "#1B2A2F"          # primary text
TEXT_MUTED = "#5A6B70"    # secondary text
BORDER = "#D7DEE0"        # dividers, outlines
NAV_BG = "#123B3D"        # bottom navigation bar

# Typography ----------------------------------------------------------------
FONT_FAMILY = "Helvetica"

FONT_H1 = (FONT_FAMILY, 26, "bold")
FONT_H2 = (FONT_FAMILY, 18, "bold")
FONT_H3 = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 10)
FONT_BUTTON = (FONT_FAMILY, 14, "bold")
FONT_NAV = (FONT_FAMILY, 11, "bold")
FONT_MONO_LOG = ("Courier", 10)


def configure_styles(root: tk.Tk) -> None:
    """Configure ttk styles used for the Treeview (history) and scrollbars."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("RxSort.Treeview", background=SURFACE, fieldbackground=SURFACE,
                     foreground=TEXT, rowheight=32, font=FONT_BODY, borderwidth=0)
    style.configure("RxSort.Treeview.Heading", background=TEAL, foreground="white",
                     font=FONT_BODY_BOLD, relief="flat")
    style.map("RxSort.Treeview.Heading", background=[("active", TEAL_DARK)])
    style.configure("RxSort.Vertical.TScrollbar", background=BORDER, troughcolor=BG)
