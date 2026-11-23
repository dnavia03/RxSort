#!/usr/bin/env python3
"""
main.py
--------
Entry point for the RxSort touchscreen interface.

Usage:
    python3 main.py              # windowed, for development on a desktop
    python3 main.py --kiosk      # fullscreen, for the real touchscreen unit

See config.py to adjust the carousel bin count, confidence threshold, demo
mode, and GPIO pin assignments.
"""

import sys

import config
from ui.app import RxSortApp


def main():
    if "--kiosk" in sys.argv:
        config.FULLSCREEN_ON_START = True

    app = RxSortApp()
    app.mainloop()


if __name__ == "__main__":
    main()
