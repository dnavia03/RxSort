"""
config.py
----------
Central configuration for the RxSort touchscreen interface.

Edit the values in this file to match the physical build (bin count,
confidence threshold, GPIO pin assignments) without touching application
logic elsewhere in the project.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rxsort.db")

# Folder holding real reference photos taken during pill testing (top-camera
# and bottom-camera shots). See pill_photos.py and the "Adding pill photos"
# section of README.md for the naming convention.
PILL_IMAGES_DIR = os.path.join(BASE_DIR, "assets", "pills")

# ---------------------------------------------------------------------------
# Carousel layout
# ---------------------------------------------------------------------------
# RxSort's carousel has 17 total compartments. Bins 1-16 are assigned to
# known medications in the pill database. Bin 17 is permanently reserved
# as the REJECT / DISCARD compartment for any pill that cannot be
# identified with sufficient confidence.
NUM_CAROUSEL_BINS = 14
REJECT_BIN = 15
MEDICATION_BINS = list(range(1, NUM_CAROUSEL_BINS))  # bins 1-16

# ---------------------------------------------------------------------------
# Identification / decision logic
# (matches the SORT / REJECT logic described in the RxSort README and the
#  "Compare Predictions" block in the system block diagram)
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.80          # 80% minimum confidence, per project README
REQUIRE_CAMERA_AGREEMENT = True      # top-camera and bottom-camera models must agree

# ---------------------------------------------------------------------------
# Operating mode
# ---------------------------------------------------------------------------
# DEMO_MODE = True   -> uses simulated camera capture, a simulated classifier,
#                        and simulated carousel/pusher motion. Safe to run on
#                        any desktop for UI development and demonstrations.
# DEMO_MODE = False  -> attempts to use real hardware (Picamera2, a local
#                        TFLite/LiteRT model, and GPIO-driven DRV8825 stepper
#                        drivers). Only works on a Raspberry Pi wired up per
#                        the RxSort hardware design.
DEMO_MODE = True

# Paths to the exported TFLite models (see README links to the Edge Impulse
# projects). Only used when DEMO_MODE is False.
TOP_CAMERA_MODEL_PATH = os.path.join(BASE_DIR, "models", "top_camera_model.tflite")
BOTTOM_CAMERA_MODEL_PATH = os.path.join(BASE_DIR, "models", "bottom_camera_model.tflite")

# ---------------------------------------------------------------------------
# GPIO pin map (BCM numbering) for the carousel and pusher DRV8825 drivers.
# Only used when DEMO_MODE is False and RPi.GPIO is available.
# ---------------------------------------------------------------------------
CAROUSEL_STEP_PIN = 20
CAROUSEL_DIR_PIN = 21
CAROUSEL_ENABLE_PIN = 16
CAROUSEL_STEPS_PER_REV = 200          # NEMA 17, full step
CAROUSEL_MICROSTEPPING = 1            # set to 16, 32, etc. if microstepping pins are wired

PUSHER_STEP_PIN = 19
PUSHER_DIR_PIN = 26
PUSHER_ENABLE_PIN = 13
PUSHER_EXTEND_STEPS = 400             # steps to push a pill out of the chamber

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
APP_TITLE = "RxSort"
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 600
FULLSCREEN_ON_START = False           # set True for the real kiosk touchscreen

# How long the results / reject screens stay up before auto-returning home
# if the user does not interact with them (0 disables the timeout).
RESULTS_AUTO_RETURN_MS = 0
