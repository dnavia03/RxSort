"""
pill_graphic.py
-----------------
Draws a simple, stylized representation of a pill on a Tkinter Canvas based
on its database ``color`` and ``shape`` fields, for the results screen's
"visual verification" panel.

RxSort does not keep photographic reference images bundled with this code,
so this module generates an illustrative icon instead -- enough for a user
to sanity-check "does this look like what I expect" without pretending to
be an actual photo of the pill.
"""

from typing import Tuple

_COLOR_MAP = {
    "white": "#FFFFFF", "yellow": "#F4D35E", "pink": "#F4A6B8", "blue": "#5E8FD1",
    "orange": "#F0974B", "green": "#6FAE6E", "peach": "#F3B888", "tan": "#D8C49B",
    "red": "#D9534F", "lavender": "#C6B6E2", "brown": "#9B6B43", "gray": "#BFC2C6",
}


def _resolve_colors(color_field: str) -> Tuple[str, str]:
    """RxSort stores some pills as a single color ('White') and others as a
    two-tone capsule ('Pink/Yellow'). Return (primary, secondary) hex colors."""
    parts = [p.strip().lower() for p in color_field.split("/")]
    primary = _COLOR_MAP.get(parts[0], "#D7DEE0")
    secondary = _COLOR_MAP.get(parts[1], primary) if len(parts) > 1 else primary
    return primary, secondary


def draw_pill(canvas, cx: int, cy: int, shape: str, color_field: str,
              width: int = 140, height: int = 70, outline: str = "#1B2A2F",
              caption: str = "Visual verification (illustrative)") -> None:
    """Draw a pill icon centered at (cx, cy) on the given canvas.

    ``shape`` should roughly match the database's ``shape`` field (Round,
    Oval, Diamond, Capsule, Capsule-shaped, etc.) and is matched loosely
    (case-insensitive substring) so new shapes degrade gracefully to an oval.

    ``caption`` is drawn in small italic text below the icon; pass None (or
    an empty string) to omit it, e.g. when space is tight in a small
    top/bottom camera thumbnail.
    """
    canvas.delete("pill_graphic")
    primary, secondary = _resolve_colors(color_field)
    shape_l = shape.lower()

    x0, y0, x1, y1 = cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2

    if "round" in shape_l:
        d = min(width, height)
        canvas.create_oval(cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2,
                            fill=primary, outline=outline, width=2, tags="pill_graphic")

    elif "diamond" in shape_l:
        d = min(width, height)
        canvas.create_polygon(cx, cy - d / 2, cx + d / 2, cy, cx, cy + d / 2, cx - d / 2, cy,
                               fill=primary, outline=outline, width=2, tags="pill_graphic")

    elif "capsule" in shape_l:
        # Two-tone capsule: left half + right half, with a dividing line.
        canvas.create_oval(x0, y0, x0 + height, y1, fill=primary, outline=outline,
                            width=2, tags="pill_graphic")
        canvas.create_rectangle(x0 + height / 2, y0, x1 - height / 2, y1, fill=secondary,
                                 outline=secondary, tags="pill_graphic")
        canvas.create_oval(x1 - height, y0, x1, y1, fill=secondary, outline=outline,
                            width=2, tags="pill_graphic")
        canvas.create_line(cx, y0, cx, y1, fill=outline, width=2, tags="pill_graphic")

    else:  # oval / oblong / default
        canvas.create_oval(x0, y0, x1, y1, fill=primary, outline=outline, width=2,
                            tags="pill_graphic")

    if caption:
        canvas.create_text(cx, cy + height / 2 + 16, text=caption,
                            fill="#5A6B70", font=("Helvetica", 9, "italic"), tags="pill_graphic")
