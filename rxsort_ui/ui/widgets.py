"""
ui/widgets.py
--------------
Reusable widgets shared across RxSort screens:

* TouchButton        - a large, flat, finger-friendly button.
* HeaderBar          - the persistent top bar (title + live clock + status dot).
* CarouselMapCanvas  - a circular diagram of all 17 carousel bins that can
                        highlight the bin a pill is currently being sorted to,
                        used as part of the "sorting destination" display.
"""

import math
import tkinter as tk
import datetime

import config
from ui import theme


class TouchButton(tk.Button):
    def __init__(self, parent, text, command=None, bg=theme.TEAL, fg="white",
                 font=theme.FONT_BUTTON, width=None, height=2, **kwargs):
        super().__init__(
            parent, text=text, command=command, bg=bg, fg=fg, font=font,
            activebackground=theme.TEAL_DARK, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", width=width, height=height,
            **kwargs,
        )
        self._bg = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        if self["state"] != "disabled":
            self.configure(bg=theme.TEAL_DARK)

    def _on_leave(self, _event):
        if self["state"] != "disabled":
            self.configure(bg=self._bg)


class HeaderBar(tk.Frame):
    def __init__(self, parent, title="RxSort", subtitle=None):
        super().__init__(parent, bg=theme.TEAL_DARK, height=60)
        self.pack_propagate(False)

        left = tk.Frame(self, bg=theme.TEAL_DARK)
        left.pack(side="left", padx=16)
        tk.Label(left, text=title, bg=theme.TEAL_DARK, fg="white",
                  font=theme.FONT_H2).pack(anchor="w")
        if subtitle:
            tk.Label(left, text=subtitle, bg=theme.TEAL_DARK, fg="#BFE3E2",
                      font=theme.FONT_SMALL).pack(anchor="w")

        right = tk.Frame(self, bg=theme.TEAL_DARK)
        right.pack(side="right", padx=16)
        self._status_dot = tk.Canvas(right, width=14, height=14, bg=theme.TEAL_DARK,
                                      highlightthickness=0)
        self._status_dot.pack(side="left", padx=(0, 6))
        self._status_dot.create_oval(2, 2, 12, 12, fill=theme.GREEN, outline="")
        self._status_label = tk.Label(right, text="Ready", bg=theme.TEAL_DARK, fg="white",
                                       font=theme.FONT_SMALL)
        self._status_label.pack(side="left", padx=(0, 16))
        self._clock_label = tk.Label(right, bg=theme.TEAL_DARK, fg="white", font=theme.FONT_SMALL)
        self._clock_label.pack(side="left")
        self._tick()

    def set_status(self, text: str, color: str = theme.GREEN) -> None:
        self._status_label.configure(text=text)
        self._status_dot.delete("all")
        self._status_dot.create_oval(2, 2, 12, 12, fill=color, outline="")

    def _tick(self):
        self._clock_label.configure(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
        self.after(1000, self._tick)


class CarouselMapCanvas(tk.Canvas):
    """A circular diagram of all NUM_CAROUSEL_BINS bins. Bin 17 (REJECT) is
    drawn in a distinct color at a fixed position; bins 1-16 are arranged
    evenly around the remainder of the circle."""

    def __init__(self, parent, size=260, bin_labels=None, **kwargs):
        super().__init__(parent, width=size, height=size, bg=theme.SURFACE,
                          highlightthickness=0, **kwargs)
        self._size = size
        self._bin_labels = bin_labels or {}
        self._active_bin = None
        self.redraw()

    def set_bin_labels(self, bin_labels: dict) -> None:
        self._bin_labels = bin_labels
        self.redraw()

    def highlight_bin(self, bin_number) -> None:
        self._active_bin = bin_number
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        size = self._size
        cx, cy = size / 2, size / 2
        radius = size * 0.38
        node_r = size * 0.075

        n = config.NUM_CAROUSEL_BINS
        for i in range(n):
            bin_number = i + 1
            angle = (2 * math.pi * i / n) - (math.pi / 2)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)

            is_reject = bin_number == config.REJECT_BIN
            is_active = bin_number == self._active_bin

            if is_active:
                fill = theme.AMBER
                outline = theme.TEAL_DARK
            elif is_reject:
                fill = "#F4CDCB"
                outline = theme.RED
            else:
                fill = "#E3EEEE"
                outline = theme.TEAL

            self.create_oval(x - node_r, y - node_r, x + node_r, y + node_r,
                              fill=fill, outline=outline, width=2)
            self.create_text(x, y, text=str(bin_number), font=(theme.FONT_FAMILY, 9, "bold"),
                              fill=theme.TEXT)

            label = self._bin_labels.get(bin_number, "")
            label_short = (label if len(label) <= 10 else label[:9] + "\u2026")
            label_x = cx + (radius + node_r + 22) * math.cos(angle)
            label_y = cy + (radius + node_r + 22) * math.sin(angle)
            self.create_text(label_x, label_y, text=label_short, font=theme.FONT_SMALL,
                              fill=theme.TEXT_MUTED)

        # Hub
        self.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill=theme.TEAL, outline="")
        self.create_text(cx, cy, text="RxSort", font=(theme.FONT_FAMILY, 8, "bold"), fill="white")
