"""
ui/app.py
----------
The RxSort application window: a simple screen-manager pattern where every
screen is a tk.Frame stacked in the same container, and only the active one
is raised with tkraise(). Shared resources (database connection helpers,
the AI classifier, and the carousel/pusher controllers) live here on the
controller so every screen can reach them through ``self.controller``.
"""

import tkinter as tk

import config
import database
import ai_classifier
import hardware_control
from ui import theme
from ui.screens import (
    HomeScreen, ScanningScreen, ResultsScreen, RejectScreen,
    HistoryScreen, SettingsScreen, ManualControlScreen,
)


class RxSortApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.configure(bg=theme.BG)
        self.minsize(720, 440)

        theme.configure_styles(self)

        if config.FULLSCREEN_ON_START:
            self.attributes("-fullscreen", True)
        # Escape always exits fullscreen / kiosk mode so the unit isn't
        # stuck full-screen during development or servicing.
        self.bind("<Escape>", lambda _e: self.attributes("-fullscreen", False))
        self.bind("<F11>", lambda _e: self.attributes(
            "-fullscreen", not self.attributes("-fullscreen")))

        database.initialize_database()

        # Shared hardware/AI resources, available to every screen.
        self.classifier = ai_classifier.get_classifier()
        self.carousel = hardware_control.CarouselController()
        self.pusher = hardware_control.PusherController()
        self.last_result = None  # most recent ai_classifier.ClassificationResult

        container = tk.Frame(self, bg=theme.BG)
        container.pack(side="top", fill="both", expand=True)

        self._screens = {}
        screen_classes = {
            "home": HomeScreen,
            "scanning": ScanningScreen,
            "results": ResultsScreen,
            "reject": RejectScreen,
            "history": HistoryScreen,
            "settings": SettingsScreen,
            "manual": ManualControlScreen,
        }
        for name, screen_cls in screen_classes.items():
            frame = screen_cls(container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self._screens[name] = frame
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_screen("home")

    def show_screen(self, name: str) -> None:
        screen = self._screens[name]
        screen.tkraise()
        screen.on_show()

    def _on_close(self):
        self.carousel.cleanup()
        self.pusher.cleanup()
        self.destroy()
