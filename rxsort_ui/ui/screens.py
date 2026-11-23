"""
ui/screens.py
--------------
Every screen in the RxSort touchscreen interface. Screens are plain
tk.Frame subclasses that the app controller (ui/app.py) raises with
tkraise(); each implements an optional on_show() hook the controller calls
every time that screen becomes visible.
"""

import tkinter as tk
from tkinter import ttk

import config
import database
import ai_classifier
from ui import theme
from ui.widgets import TouchButton, HeaderBar, CarouselMapCanvas
from pill_graphic import draw_pill
import pill_photos


# ---------------------------------------------------------------------------
# Base screen
# ---------------------------------------------------------------------------
class BaseScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller

    def on_show(self):
        """Called by the controller every time this screen is raised."""
        pass


def nav_bar(parent, controller, active: str) -> tk.Frame:
    """Persistent bottom navigation shown on the non-full-attention screens."""
    bar = tk.Frame(parent, bg=theme.NAV_BG, height=56)
    bar.pack_propagate(False)

    tabs = [("home", "Home"), ("history", "History"),
            ("manual", "Manual Control"), ("settings", "Settings")]
    for key, label in tabs:
        is_active = key == active
        btn = tk.Button(
            bar, text=label, command=lambda k=key: controller.show_screen(k),
            bg=theme.NAV_BG if not is_active else theme.TEAL,
            fg="white", font=theme.FONT_NAV, relief="flat", bd=0,
            activebackground=theme.TEAL_DARK, activeforeground="white", cursor="hand2",
        )
        btn.pack(side="left", expand=True, fill="both", padx=1, pady=1)
    return bar


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
class HomeScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        HeaderBar(self, "RxSort", "Automated Pill Identification & Sorting").pack(
            side="top", fill="x")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(side="top", fill="both", expand=True)

        center = tk.Frame(body, bg=theme.BG)
        center.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(center, text="Please place one pill at a time into the imaging chamber, then",
                  bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.FONT_BODY).pack()
        tk.Label(center, text="press Scan to identify and sort.",
                  bg=theme.BG, fg=theme.TEXT_MUTED, font=theme.FONT_BODY).pack(pady=(0, 18))

        TouchButton(center, "\u25B6  SCAN PILL", width=24, height=3,
                    font=theme.FONT_H3,
                    command=lambda: controller.show_screen("scanning")).pack()

        self._stats_label = tk.Label(body, bg=theme.BG, fg=theme.TEXT_MUTED,
                                      font=theme.FONT_SMALL)
        self._stats_label.place(relx=0.5, rely=0.78, anchor="center")

        nav_bar(self, controller, active="home").pack(side="bottom", fill="x")

    def on_show(self):
        rows = database.get_recent_history(limit=500)
        sorted_count = sum(1 for r in rows if r["status"] == "SORTED")
        rejected_count = sum(1 for r in rows if r["status"] == "REJECTED")
        self._stats_label.configure(
            text=f"Session totals \u2014 Sorted: {sorted_count}    Rejected: {rejected_count}")


# ---------------------------------------------------------------------------
# Scanning (full attention, no nav bar)
# ---------------------------------------------------------------------------
class ScanningScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        HeaderBar(self, "RxSort", "Identifying medication...").pack(side="top", fill="x")

        center = tk.Frame(self, bg=theme.BG)
        center.pack(expand=True, fill="both")

        self._spinner = tk.Canvas(center, width=90, height=90, bg=theme.BG,
                                   highlightthickness=0)
        self._spinner.pack(pady=(30, 10))
        self._spinner_angle = 0

        self._log = tk.Text(center, width=62, height=11, font=theme.FONT_MONO_LOG,
                             bg=theme.SURFACE, fg=theme.TEXT, relief="flat",
                             state="disabled", wrap="word")
        self._log.pack(pady=10)

        self._cancel_id = None

    # -- logging helpers ----------------------------------------------------
    def _log_line(self, text: str):
        self._log.configure(state="normal")
        self._log.insert("end", f"\u2022 {text}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _spin(self):
        self._spinner.delete("all")
        self._spinner.create_arc(10, 10, 80, 80, start=self._spinner_angle, extent=100,
                                  style="arc", width=6, outline=theme.TEAL)
        self._spinner_angle = (self._spinner_angle + 18) % 360
        self._cancel_id = self.after(60, self._spin)

    # -- main sequence --------------------------------------------------------
    def on_show(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._spin()

        # Run (simulated or real) classification immediately; the result is
        # revealed to the user gradually through the scripted log below so
        # the pipeline stages from the RxSort architecture stay visible.
        result = self.controller.classifier.classify()
        self.controller.last_result = result

        steps = [
            (500, "Capturing top camera image..."),
            (500, "Capturing bottom camera image..."),
            (450, "Preprocessing images (resize, normalize)..."),
            (600, f"Top camera model prediction confidence: {result.top_confidence * 100:.1f}%"),
            (600, f"Bottom camera model prediction confidence: {result.bottom_confidence * 100:.1f}%"),
            (500, "Comparing top and bottom predictions..."),
        ]
        self._run_steps(steps, 0, result)

    def _run_steps(self, steps, index, result):
        if index < len(steps):
            delay, message = steps[index]
            self._log_line(message)
            self.after(delay, lambda: self._run_steps(steps, index + 1, result))
            return

        if result.accepted and result.pill is not None:
            self._log_line(f"Identified: {result.pill.name} ({result.pill.strength}).")
            self.after(500, lambda: self._sort_accepted(result))
        else:
            self._log_line(f"Rejected: {result.reason}")
            self.after(500, lambda: self._sort_rejected(result))

    def _sort_accepted(self, result):
        bin_number = result.pill.bin_number
        self._log_line(f"Decision: SORT \u2192 Bin {bin_number} ({result.pill.name}).")
        self.controller.carousel.rotate_to_bin(bin_number, log_callback=self._log_line)
        self.controller.pusher.activate(log_callback=self._log_line)
        database.log_sort_event(result.pill.name, bin_number, result.top_confidence,
                                 result.bottom_confidence, "SORTED")
        self._log_line("Sort complete.")
        if self._cancel_id:
            self.after_cancel(self._cancel_id)
        self.after(400, lambda: self.controller.show_screen("results"))

    def _sort_rejected(self, result):
        self._log_line(f"Decision: REJECT \u2192 Bin {config.REJECT_BIN} (discard pile).")
        self.controller.carousel.rotate_to_bin(config.REJECT_BIN, log_callback=self._log_line)
        self.controller.pusher.activate(log_callback=self._log_line)
        database.log_sort_event("Unidentified pill", config.REJECT_BIN, result.top_confidence,
                                 result.bottom_confidence, "REJECTED")
        self._log_line("Pill moved to discard pile.")
        if self._cancel_id:
            self.after_cancel(self._cancel_id)
        self.after(400, lambda: self.controller.show_screen("reject"))


# ---------------------------------------------------------------------------
# Results (full attention, no nav bar)
# ---------------------------------------------------------------------------
class ResultsScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self._header = HeaderBar(self, "RxSort", "Medication identified")
        self._header.pack(side="top", fill="x")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # Left: visual verification + carousel map
        left = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        left.pack(side="left", fill="both", expand=False, padx=(0, 10), ipadx=8, ipady=8)

        tk.Label(left, text="Visual Verification", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_H3).pack(pady=(8, 4))

        cameras_row = tk.Frame(left, bg=theme.SURFACE)
        cameras_row.pack(pady=4)

        top_cell = tk.Frame(cameras_row, bg=theme.SURFACE)
        top_cell.pack(side="left", padx=6)
        tk.Label(top_cell, text="Top Camera", bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                  font=theme.FONT_SMALL).pack()
        self._top_canvas = tk.Canvas(top_cell, width=170, height=120, bg=theme.SURFACE,
                                      highlightbackground=theme.BORDER, highlightthickness=1)
        self._top_canvas.pack()

        bottom_cell = tk.Frame(cameras_row, bg=theme.SURFACE)
        bottom_cell.pack(side="left", padx=6)
        tk.Label(bottom_cell, text="Bottom Camera", bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                  font=theme.FONT_SMALL).pack()
        self._bottom_canvas = tk.Canvas(bottom_cell, width=170, height=120, bg=theme.SURFACE,
                                         highlightbackground=theme.BORDER, highlightthickness=1)
        self._bottom_canvas.pack()

        # Tkinter garbage-collects a PhotoImage once nothing references it,
        # so the loaded photos are kept alive here for as long as they're shown.
        self._top_photo = None
        self._bottom_photo = None

        self._confidence_label = tk.Label(left, bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                                           font=theme.FONT_SMALL, justify="left")
        self._confidence_label.pack(pady=(6, 6))

        self._carousel_map = CarouselMapCanvas(left, size=170)
        self._carousel_map.pack(pady=(0, 10))

        # Right: identification details
        right = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                          highlightthickness=1)
        right.pack(side="left", fill="both", expand=True, ipadx=10, ipady=8)

        self._name_label = tk.Label(right, bg=theme.SURFACE, fg=theme.TEXT, font=theme.FONT_H1,
                                     anchor="w", justify="left")
        self._name_label.pack(fill="x", padx=16, pady=(12, 0))

        self._brand_label = tk.Label(right, bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                                      font=theme.FONT_BODY, anchor="w")
        self._brand_label.pack(fill="x", padx=16)

        self._desc_label = tk.Label(right, bg=theme.SURFACE, fg=theme.TEXT, font=theme.FONT_BODY,
                                     anchor="w", justify="left", wraplength=360)
        self._desc_label.pack(fill="x", padx=16, pady=(8, 10))

        grid = tk.Frame(right, bg=theme.SURFACE)
        grid.pack(fill="x", padx=16)
        self._field_labels = {}
        fields = ["Strength / Dosage", "Imprint", "Color", "Shape", "Form", "Dimensions"]
        for i, field in enumerate(fields):
            r, c = divmod(i, 2)
            cell = tk.Frame(grid, bg=theme.SURFACE)
            cell.grid(row=r, column=c, sticky="w", padx=(0, 24), pady=4)
            tk.Label(cell, text=field.upper(), bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                      font=theme.FONT_SMALL).pack(anchor="w")
            value_label = tk.Label(cell, bg=theme.SURFACE, fg=theme.TEXT, font=theme.FONT_BODY_BOLD)
            value_label.pack(anchor="w")
            self._field_labels[field] = value_label

        self._destination_frame = tk.Frame(right, bg=theme.TEAL)
        self._destination_frame.pack(fill="x", padx=16, pady=14)
        self._destination_label = tk.Label(self._destination_frame, bg=theme.TEAL, fg="white",
                                            font=theme.FONT_H2, pady=10)
        self._destination_label.pack()

        TouchButton(right, "Scan Next Pill", width=20,
                    command=lambda: controller.show_screen("home")).pack(
            padx=16, pady=(0, 14), anchor="w")

    def on_show(self):
        result = self.controller.last_result
        pill = result.pill

        self._name_label.configure(text=pill.name)
        self._brand_label.configure(text=f"Brand name: {pill.brand}")
        self._desc_label.configure(text=pill.description)

        self._field_labels["Strength / Dosage"].configure(text=f"{pill.name} {pill.strength}")
        self._field_labels["Imprint"].configure(text=pill.imprint)
        self._field_labels["Color"].configure(text=pill.color)
        self._field_labels["Shape"].configure(text=pill.shape)
        self._field_labels["Form"].configure(text=pill.form)
        self._field_labels["Dimensions"].configure(text=pill.dimensions)

        self._destination_label.configure(
            text=f"Sorting Destination \u2192 Carousel Bin {pill.bin_number}")

        self._top_photo = pill_photos.load_thumbnail(pill.image_top)
        self._top_canvas.delete("all")
        if self._top_photo is not None:
            self._top_canvas.create_image(85, 60, image=self._top_photo)
        else:
            draw_pill(self._top_canvas, 85, 55, pill.shape, pill.color,
                      width=110, height=55, caption="No photo on file (icon)")

        self._bottom_photo = pill_photos.load_thumbnail(pill.image_bottom)
        self._bottom_canvas.delete("all")
        if self._bottom_photo is not None:
            self._bottom_canvas.create_image(85, 60, image=self._bottom_photo)
        else:
            draw_pill(self._bottom_canvas, 85, 55, pill.shape, pill.color,
                      width=110, height=55, caption="No photo on file (icon)")

        self._confidence_label.configure(
            text=f"Top confidence: {result.top_confidence * 100:.1f}%   |   "
                 f"Bottom confidence: {result.bottom_confidence * 100:.1f}%")

        self._carousel_map.set_bin_labels(database.get_bin_map())
        self._carousel_map.highlight_bin(pill.bin_number)

        if config.RESULTS_AUTO_RETURN_MS:
            self.after(config.RESULTS_AUTO_RETURN_MS,
                       lambda: self.controller.show_screen("home"))


# ---------------------------------------------------------------------------
# Reject / unidentified alert (full attention, no nav bar)
# ---------------------------------------------------------------------------
class RejectScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.configure(bg="#FBECEC")

        banner = tk.Frame(self, bg=theme.RED)
        banner.pack(side="top", fill="x")
        tk.Label(banner, text="\u26A0  Medication Unidentified", bg=theme.RED, fg="white",
                  font=theme.FONT_H1, pady=16).pack()

        body = tk.Frame(self, bg="#FBECEC")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        left = tk.Frame(body, bg="#FBECEC")
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))

        self._reason_label = tk.Label(left, bg="#FBECEC", fg=theme.TEXT, font=theme.FONT_H3,
                                       wraplength=380, justify="left")
        self._reason_label.pack(anchor="w", pady=(10, 6))

        self._confidence_label = tk.Label(left, bg="#FBECEC", fg=theme.TEXT_MUTED,
                                           font=theme.FONT_BODY, justify="left")
        self._confidence_label.pack(anchor="w", pady=(0, 14))

        notice = tk.Frame(left, bg="white", highlightbackground=theme.RED, highlightthickness=1)
        notice.pack(fill="x", pady=10)
        tk.Label(notice, bg="white", fg=theme.TEXT, font=theme.FONT_BODY, justify="left",
                  wraplength=380, padx=12, pady=10,
                  text=f"This pill has been sorted into the discard pile "
                       f"(Carousel Bin {config.REJECT_BIN}) instead of a medication "
                       f"compartment. Please retrieve it and verify it manually before "
                       f"dispensing.").pack()

        TouchButton(left, "OK, Scan Next Pill", bg=theme.RED, width=20,
                    command=lambda: controller.show_screen("home")).pack(anchor="w", pady=16)

        right = tk.Frame(body, bg="#FBECEC")
        right.pack(side="left")
        self._carousel_map = CarouselMapCanvas(right, size=240)
        self._carousel_map.pack()

    def on_show(self):
        result = self.controller.last_result
        self._reason_label.configure(text=result.reason)
        self._confidence_label.configure(
            text=f"Top camera confidence: {result.top_confidence * 100:.1f}%\n"
                 f"Bottom camera confidence: {result.bottom_confidence * 100:.1f}%\n"
                 f"Required threshold: {config.CONFIDENCE_THRESHOLD * 100:.0f}%")
        self._carousel_map.set_bin_labels(database.get_bin_map())
        self._carousel_map.highlight_bin(config.REJECT_BIN)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
class HistoryScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        HeaderBar(self, "RxSort", "Sorting history").pack(side="top", fill="x")

        toolbar = tk.Frame(self, bg=theme.BG)
        toolbar.pack(fill="x", padx=14, pady=(10, 4))
        TouchButton(toolbar, "Refresh", width=10, height=1,
                    command=self._refresh).pack(side="right")

        table_frame = tk.Frame(self, bg=theme.BG)
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        columns = ("time", "pill", "bin", "top_conf", "bottom_conf", "status")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                   style="RxSort.Treeview", height=9)
        headings = {"time": "Time", "pill": "Medication", "bin": "Bin",
                    "top_conf": "Top Conf.", "bottom_conf": "Bottom Conf.", "status": "Status"}
        widths = {"time": 140, "pill": 180, "bin": 50, "top_conf": 90,
                  "bottom_conf": 100, "status": 90}
        for col in columns:
            self._tree.heading(col, text=headings[col])
            self._tree.column(col, width=widths[col], anchor="center")
        self._tree.column("pill", anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview,
                                   style="RxSort.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._tree.tag_configure("rejected", foreground=theme.RED)
        self._tree.tag_configure("sorted", foreground=theme.GREEN)

        nav_bar(self, controller, active="history").pack(side="bottom", fill="x")

    def on_show(self):
        self._refresh()

    def _refresh(self):
        self._tree.delete(*self._tree.get_children())
        for row in database.get_recent_history(limit=100):
            top_conf = f"{row['confidence_top'] * 100:.1f}%" if row["confidence_top"] is not None else "-"
            bottom_conf = f"{row['confidence_bottom'] * 100:.1f}%" if row["confidence_bottom"] is not None else "-"
            tag = "rejected" if row["status"] == "REJECTED" else "sorted"
            self._tree.insert("", "end", values=(
                row["timestamp"].replace("T", " "), row["pill_name"], row["bin_number"],
                top_conf, bottom_conf, row["status"]), tags=(tag,))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingsScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        HeaderBar(self, "RxSort", "Settings").pack(side="top", fill="x")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # Threshold control
        threshold_card = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                                   highlightthickness=1)
        threshold_card.pack(fill="x", pady=(0, 12), ipady=8)
        tk.Label(threshold_card, text="Confidence Threshold", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_H3).pack(anchor="w", padx=14, pady=(8, 0))
        tk.Label(threshold_card, text="Minimum top/bottom camera confidence required to "
                                       "accept an identification (RxSort default: 80%).",
                  bg=theme.SURFACE, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                  wraplength=600, justify="left").pack(anchor="w", padx=14)

        slider_row = tk.Frame(threshold_card, bg=theme.SURFACE)
        slider_row.pack(fill="x", padx=14, pady=8)
        self._threshold_var = tk.DoubleVar(value=config.CONFIDENCE_THRESHOLD * 100)
        self._threshold_value_label = tk.Label(slider_row, bg=theme.SURFACE, fg=theme.TEAL,
                                                font=theme.FONT_H3, width=6)
        self._threshold_value_label.pack(side="right")
        scale = tk.Scale(slider_row, from_=50, to=99, orient="horizontal",
                          variable=self._threshold_var, showvalue=False,
                          bg=theme.SURFACE, troughcolor=theme.BORDER, fg=theme.TEAL,
                          highlightthickness=0, command=self._on_threshold_change)
        scale.pack(side="left", fill="x", expand=True)
        self._on_threshold_change(None)

        # Mode card
        mode_card = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                              highlightthickness=1)
        mode_card.pack(fill="x", pady=(0, 12), ipady=8)
        tk.Label(mode_card, text="Operating Mode", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_H3).pack(anchor="w", padx=14, pady=(8, 0))
        self._mode_label = tk.Label(mode_card, bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                                     font=theme.FONT_BODY, justify="left", wraplength=600)
        self._mode_label.pack(anchor="w", padx=14, pady=(0, 8))
        self._update_mode_label()

        # Bin assignments
        bins_card = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                              highlightthickness=1)
        bins_card.pack(fill="both", expand=True)
        tk.Label(bins_card, text="Carousel Bin Assignments (1\u201316 medications, "
                                  f"{config.REJECT_BIN} = reject)",
                  bg=theme.SURFACE, fg=theme.TEXT, font=theme.FONT_H3).pack(
            anchor="w", padx=14, pady=(8, 4))

        columns = ("bin", "name", "strength")
        tree = ttk.Treeview(bins_card, columns=columns, show="headings",
                             style="RxSort.Treeview", height=6)
        for col, label, width in [("bin", "Bin", 60), ("name", "Medication", 220),
                                   ("strength", "Strength", 100)]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w" if col == "name" else "center")
        for pill in database.get_all_pills():
            tree.insert("", "end", values=(pill.bin_number, pill.name, pill.strength))
        tree.insert("", "end", values=(config.REJECT_BIN, "REJECT / DISCARD", "\u2014"))
        tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        nav_bar(self, controller, active="settings").pack(side="bottom", fill="x")

    def _on_threshold_change(self, _event):
        pct = self._threshold_var.get()
        config.CONFIDENCE_THRESHOLD = pct / 100.0
        self._threshold_value_label.configure(text=f"{pct:.0f}%")

    def _update_mode_label(self):
        mode = "DEMO (simulated camera, AI, and motors)" if config.DEMO_MODE else "REAL HARDWARE"
        self._mode_label.configure(
            text=f"Current mode: {mode}\n"
                 "Change config.DEMO_MODE and restart the application to switch to the "
                 "real Picamera2 + TFLite + GPIO pipeline once the hardware is wired up.")


# ---------------------------------------------------------------------------
# Manual control
# ---------------------------------------------------------------------------
class ManualControlScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        HeaderBar(self, "RxSort", "Manual control").pack(side="top", fill="x")

        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        left = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10), ipady=10)

        tk.Label(left, text="Carousel", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_H3).pack(anchor="w", padx=14, pady=(8, 4))

        row = tk.Frame(left, bg=theme.SURFACE)
        row.pack(fill="x", padx=14, pady=4)
        tk.Label(row, text="Target bin:", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_BODY).pack(side="left")
        self._bin_var = tk.IntVar(value=1)
        bin_menu = tk.OptionMenu(row, self._bin_var, *range(1, config.NUM_CAROUSEL_BINS + 1))
        bin_menu.configure(font=theme.FONT_BODY, bg="white")
        bin_menu.pack(side="left", padx=8)

        TouchButton(left, "Rotate Carousel", width=20,
                    command=self._rotate).pack(padx=14, pady=8, anchor="w")
        TouchButton(left, "Activate Pusher", bg=theme.BLUE, width=20,
                    command=self._push).pack(padx=14, pady=(0, 8), anchor="w")

        self._log = tk.Text(left, height=8, font=theme.FONT_MONO_LOG, bg=theme.BG, fg=theme.TEXT,
                             relief="flat", state="disabled", wrap="word")
        self._log.pack(fill="both", expand=True, padx=14, pady=(8, 10))

        right = tk.Frame(body, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                          highlightthickness=1)
        right.pack(side="left", padx=(10, 0), ipady=10)
        tk.Label(right, text="Current carousel position", bg=theme.SURFACE, fg=theme.TEXT,
                  font=theme.FONT_H3).pack(pady=(8, 0))
        self._carousel_map = CarouselMapCanvas(right, size=200)
        self._carousel_map.pack(padx=14, pady=10)

        self._is_demo = isinstance(controller.classifier, ai_classifier.DemoClassifier)
        if self._is_demo:
            tk.Frame(right, bg=theme.BORDER, height=1).pack(fill="x", padx=14, pady=(0, 10))
            tk.Label(right, text="Scan Simulator (Demo Mode)", bg=theme.SURFACE, fg=theme.TEXT,
                      font=theme.FONT_H3).pack(pady=(0, 2))
            tk.Label(right, text="Jump straight to a specific medication's result screen "
                                  "instead of waiting on a random scan outcome \u2014 handy for "
                                  "checking whether its reference photos display correctly.",
                      bg=theme.SURFACE, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                      wraplength=230, justify="left").pack(padx=14, pady=(0, 8))

            self._sim_name_to_class = {p.name: p.class_id for p in database.get_all_pills()}
            sim_options = ["Random outcome", "Force reject / unidentified"] + list(
                self._sim_name_to_class.keys())
            self._sim_var = tk.StringVar(value="Random outcome")
            sim_menu = tk.OptionMenu(right, self._sim_var, *sim_options)
            sim_menu.configure(font=theme.FONT_BODY, bg="white")
            sim_menu.pack(padx=14, pady=4, fill="x")

            TouchButton(right, "Run Simulated Scan", bg=theme.AMBER, fg=theme.TEXT,
                        width=20, command=self._run_simulated_scan).pack(padx=14, pady=(6, 10))
        else:
            tk.Label(right, text="Scan simulator is unavailable in real hardware mode.",
                      bg=theme.SURFACE, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                      wraplength=200).pack(padx=14, pady=10)

        nav_bar(self, controller, active="manual").pack(side="bottom", fill="x")

    def on_show(self):
        self._carousel_map.set_bin_labels(database.get_bin_map())
        self._carousel_map.highlight_bin(self.controller.carousel.current_bin)

    def _log_line(self, text):
        self._log.configure(state="normal")
        self._log.insert("end", f"\u2022 {text}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _rotate(self):
        bin_number = self._bin_var.get()
        self.controller.carousel.rotate_to_bin(bin_number, log_callback=self._log_line)
        self._carousel_map.highlight_bin(bin_number)

    def _push(self):
        self.controller.pusher.activate(log_callback=self._log_line)

    def _run_simulated_scan(self):
        selection = self._sim_var.get()
        if selection == "Random outcome":
            self.controller.classifier.force_next(None)
        elif selection == "Force reject / unidentified":
            self.controller.classifier.force_next("reject")
        else:
            self.controller.classifier.force_next(self._sim_name_to_class[selection])
        self.controller.show_screen("scanning")
