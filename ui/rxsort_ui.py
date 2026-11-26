from system_controller import RxSortController, RxSortHardwareError
import random
import threading
import time
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

# Allow this file to be launched directly with:
#     python ui/rxsort_ui.py
# while system_controller.py remains in the project root.
_PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT_FOR_IMPORTS))


# ==========================================================
# RXSORT TOUCHSCREEN CONFIGURATION
# ==========================================================

# Waveshare 7" HDMI LCD (C) native resolution
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 600

# Scale the original 800x480 UI proportions for 1024x600.
UI_SCALE = 1.20

# True = kiosk-style fullscreen on the touchscreen.
FULLSCREEN = True

REJECT_BIN = 10

# Keep True while testing the UI without the real AI/hardware workflow.
DEMO_MODE = False


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILL_IMAGE_FOLDER = PROJECT_ROOT / "assets" / "pill_images"
LOGO_PATH = PROJECT_ROOT / "assets" / "rxsort_logo.png"


# ==========================================================
# COLORS
# ==========================================================

BACKGROUND = "#EDF4F8"
NAVY = "#12324A"
DARK_NAVY = "#0B2235"
BLUE = "#169BD5"
LIGHT_BLUE = "#DDF3FC"
TEAL = "#16B3A3"
LIGHT_TEAL = "#DCF7F3"
GREEN = "#22A55A"
LIGHT_GREEN = "#E2F7EA"
RED = "#D94A4A"
LIGHT_RED = "#FCE7E7"
WHITE = "#FFFFFF"
TEXT = "#182B3A"
MUTED = "#687A88"
CARD_BORDER = "#D8E3EA"


# ==========================================================
# DEMO PILL INFORMATION
# ==========================================================

DEMO_PILLS = {
    6: {
        "name": "Fexofenadine Hydrochloride",
        "strength": "180 mg",
        "imprint": "L847",
        "color": "Light Pink",
        "shape": "Oblong",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Fexofenadine.png",
        "description": (
            "Fexofenadine is an antihistamine used to help relieve allergy "
            "symptoms such as sneezing, runny nose, and itchy or watery eyes."
        ),
    },
    7: {
        "name": "Mucinex",
        "strength": "600 mg",
        "imprint": "Mucinex / 600",
        "color": "Light Green / White",
        "shape": "Oblong",
        "dosage_form": "Extended-Release Tablet",
        "image": PILL_IMAGE_FOLDER / "Mucinex.png",
        "description": (
            "Mucinex contains guaifenesin, an expectorant that helps loosen "
            "mucus and relieve chest congestion."
        ),
    },
    8: {
        "name": "Hydrochlorothiazide & Losartan Potassium",
        "strength": "",
        "imprint": "F / 74",
        "color": "White",
        "shape": "Oval",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Hydrochlorothiazide.png",
        "description": (
            "This combination medication is used to help lower high blood "
            "pressure by combining an angiotensin receptor blocker with a diuretic."
        ),
    },
    13: {
        "name": "Benadryl Allergy Ultratab Diphenhydramine",
        "strength": "25 mg",
        "imprint": "B / WL25",
        "color": "Pink",
        "shape": "Oblong",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Benadryl.png",
        "description": (
            "Diphenhydramine is an antihistamine commonly used for temporary "
            "relief of allergy symptoms."
        ),
    },
    15: {
        "name": "Labetalol Hydrochloride",
        "strength": "200 mg",
        "imprint": "AC / 372",
        "color": "White",
        "shape": "Round",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Labetalol Hydrochloride.png",
        "description": (
            "Labetalol is a prescription medication used to help lower high "
            "blood pressure by blocking certain effects of adrenaline on the "
            "heart and blood vessels."
        ),
    },
    16: {
        "name": "Acetaminophen (Tylenol)",
        "strength": "500 mg",
        "imprint": "TYLENOL / 500",
        "color": "Red",
        "shape": "Oblong",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Tylenol.png",
        "description": (
            "Acetaminophen is commonly used to temporarily reduce fever and "
            "relieve minor aches and pain."
        ),
    },
    19: {
        "name": "Advil",
        "strength": "200 mg",
        "imprint": "Advil",
        "color": "Orange / Red",
        "shape": "Round",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Advil.png",
        "description": (
            "Advil contains ibuprofen, a nonsteroidal anti-inflammatory drug "
            "commonly used for temporary pain, inflammation, and fever relief."
        ),
    },
    20: {
        "name": "Loperamide HCl",
        "strength": "2 mg",
        "imprint": "44375",
        "color": "Light Green",
        "shape": "Oblong",
        "dosage_form": "Tablet",
        "image": PILL_IMAGE_FOLDER / "Loperamide HCl.png",
        "description": (
            "Loperamide is an anti-diarrheal medication used to slow intestinal "
            "movement and help control symptoms of diarrhea."
        ),
    },
}


# ==========================================================
# BIN TRACKING
# ==========================================================

pill_bin_assignments = {}
bin_contents = {}


def add_pill_to_bin(bin_number, pill_id, pill):
    if bin_number in bin_contents:
        bin_contents[bin_number]["count"] += 1
    else:
        bin_contents[bin_number] = {
            "pill_id": pill_id,
            "pill": pill,
            "count": 1,
        }


def get_bin_for_pill(pill_id):
    if pill_id in pill_bin_assignments:
        return pill_bin_assignments[pill_id]

    used_bins = set(pill_bin_assignments.values())

    for bin_number in range(1, REJECT_BIN):
        if bin_number not in used_bins:
            pill_bin_assignments[pill_id] = bin_number
            return bin_number

    return None


# ==========================================================
# MAIN APPLICATION
# ==========================================================

class RxSortUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RxSort")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+0+0")
        self.configure(fg_color=BACKGROUND)
        self.resizable(False, False)

        if FULLSCREEN:
            self.attributes("-fullscreen", True)

        # Development / kiosk controls
        self.bind("<Escape>", self.exit_fullscreen)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Control-q>", self.on_close)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.current_pill = None
        self.current_pill_id = None
        self.current_bin = None
        self.current_pill_image = None

        self.scan_animation_running = False
        self.scan_dot_count = 0
        self.bin_detail_panel = None
        self.sort_destination_label = None

        # The controller is only initialized in REAL mode. Demo mode remains
        # fully usable without Raspberry Pi hardware connected.
        self.controller = None

        # Load the RxSort logo once and reuse it throughout the UI.
        self.load_brand_assets()

        if DEMO_MODE:
            self.show_home_screen()
        else:
            self.show_initializing_screen()
            self.after(100, self.start_real_system_initialization)

    # ======================================================
    # FULLSCREEN CONTROLS
    # ======================================================

    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+0+0")

    def toggle_fullscreen(self, event=None):
        current = bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", not current)

    # ======================================================
    # REAL SYSTEM INITIALIZATION / SHUTDOWN
    # ======================================================

    def show_initializing_screen(self):
        self.clear_screen()
        self.create_header(
            "System Startup",
            "INITIALIZING",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        title = ctk.CTkLabel(
            card,
            text="Preparing RxSort",
            font=("Arial", 26, "bold"),
            text_color=TEXT,
        )
        title.pack(pady=(72, 12))

        self.system_status_label = ctk.CTkLabel(
            card,
            text="Loading hardware...",
            font=("Arial", 14),
            text_color=MUTED,
        )
        self.system_status_label.pack(pady=(0, 18))

        self.system_progress = ctk.CTkProgressBar(
            card,
            width=400,
            height=12,
            corner_radius=6,
            progress_color=TEAL,
            fg_color="#DCE7ED",
        )
        self.system_progress.pack()
        self.system_progress.set(0)

    def start_real_system_initialization(self):
        worker = threading.Thread(
            target=self.initialize_real_system,
            daemon=True,
        )
        worker.start()

    def initialize_real_system(self):
        try:
            self.controller = RxSortController()
            self.controller.initialize(self.controller_startup_progress)
            self.after(0, self.show_home_screen)

        except Exception as error:
            self.after(
                0,
                lambda e=error: self.show_system_error_screen(
                    "RxSort could not initialize.",
                    str(e),
                ),
            )

    def controller_startup_progress(self, value, message):
        self.after(
            0,
            lambda v=value, m=message: self.update_startup_progress(v, m),
        )

    def update_startup_progress(self, value, message):
        try:
            self.system_progress.set(value)
            self.system_status_label.configure(text=message)
        except Exception:
            pass

    def show_system_error_screen(self, title_text, message_text):
        self.scan_animation_running = False
        self.clear_screen()
        self.create_header(
            "System Error",
            "ATTENTION",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        title = ctk.CTkLabel(
            card,
            text=title_text,
            font=("Arial", 24, "bold"),
            text_color=RED,
        )
        title.pack(pady=(55, 12))

        message = ctk.CTkLabel(
            card,
            text=message_text,
            font=("Arial", 13),
            text_color=MUTED,
            wraplength=580,
            justify="center",
        )
        message.pack(pady=(0, 20))

        retry = ctk.CTkButton(
            card,
            text="RETRY STARTUP",
            width=170,
            height=42,
            corner_radius=10,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.retry_real_system,
        )
        retry.pack()

    def retry_real_system(self):
        if self.controller is not None:
            try:
                self.controller.shutdown(suppress_errors=True)
            except Exception:
                pass

        self.controller = None
        self.show_initializing_screen()
        self.after(100, self.start_real_system_initialization)

    def on_close(self, event=None):
        try:
            if self.controller is not None:
                self.controller.shutdown(suppress_errors=True)
        finally:
            self.destroy()

    # ======================================================
    # BRAND ASSETS
    # ======================================================

    def load_brand_assets(self):
        self.header_logo_image = None
        self.home_logo_image = None

        if not LOGO_PATH.exists():
            print(f"RxSort logo not found: {LOGO_PATH}")
            return

        try:
            logo_image = Image.open(LOGO_PATH).convert("RGBA")

            # Small logo displayed in the header on every screen.
            self.header_logo_image = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(38, 38),
            )

            # Larger transparent logo displayed on the home screen.
            self.home_logo_image = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(120, 120),
            )

            print("RxSort logo loaded successfully.")

        except Exception as error:
            print(f"Could not load RxSort logo: {error}")

    # ======================================================
    # HELPERS
    # ======================================================

    def clear_screen(self):
        self.scan_animation_running = False
        self.current_pill_image = None
        self.bin_detail_panel = None
        self.sort_destination_label = None

        for widget in self.winfo_children():
            widget.destroy()

    def create_header(self, title, subtitle=""):
        header = ctk.CTkFrame(
            self,
            height=78,
            corner_radius=0,
            fg_color=NAVY,
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        # Small RxSort logo stays visible on every screen.
        if self.header_logo_image is not None:
            logo_icon = ctk.CTkLabel(
                header,
                image=self.header_logo_image,
                text="",
                fg_color="transparent",
            )
            logo_icon.place(x=20, y=19)
            brand_x = 64
        else:
            brand_x = 28

        logo = ctk.CTkLabel(
            header,
            text="RxSort",
            font=("Arial", 27, "bold"),
            text_color=WHITE,
        )
        logo.place(x=brand_x, y=13)

        page_title = ctk.CTkLabel(
            header,
            text=title,
            font=("Arial", 15, "bold"),
            text_color="#CDEAF7",
        )
        page_title.place(x=brand_x + 1, y=47)

        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header,
                text=subtitle,
                font=("Arial", 12, "bold"),
                text_color="#A9C2D2",
            )
            subtitle_label.place(relx=0.96, rely=0.50, anchor="e")

    # ======================================================
    # HOME SCREEN
    # ======================================================

    def show_home_screen(self):
        self.clear_screen()
        self.create_header(
            "Medication Identification & Sorting",
            "SYSTEM READY",
        )

        hero = ctk.CTkFrame(
            self,
            width=710,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        hero.pack(expand=True, pady=(15, 20))
        hero.pack_propagate(False)

        # Main RxSort logo. The source PNG has transparency, so place it
        # directly on the white hero card with no colored frame behind it.
        if self.home_logo_image is not None:
            home_logo = ctk.CTkLabel(
                hero,
                image=self.home_logo_image,
                text="",
                fg_color="transparent",
            )
            home_logo.pack(pady=(18, 4))
        else:
            home_logo = ctk.CTkLabel(
                hero,
                text="RxSort",
                font=("Arial", 34, "bold"),
                text_color=BLUE,
                fg_color="transparent",
            )
            home_logo.pack(pady=(30, 12))

        title = ctk.CTkLabel(
            hero,
            text="Smart Medication Sorting",
            font=("Arial", 25, "bold"),
            text_color=TEXT,
        )
        title.pack(pady=(4, 4))

        message = ctk.CTkLabel(
            hero,
            text=(
                "Identify and sort medications using "
                "dual-camera AI recognition."
            ),
            font=("Arial", 15),
            text_color=MUTED,
        )
        message.pack(pady=(0, 22))

        start_button = ctk.CTkButton(
            hero,
            text="START SORTING",
            width=260,
            height=53,
            corner_radius=12,
            font=("Arial", 17, "bold"),
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.show_insert_screen,
        )
        start_button.pack()

    # ======================================================
    # INSERT SCREEN
    # ======================================================

    def show_insert_screen(self):
        self.clear_screen()
        self.create_header(
            "Ready for Medication",
            "WAITING FOR PILL",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        status = ctk.CTkLabel(
            card,
            text="●  CHAMBER READY",
            font=("Arial", 13, "bold"),
            text_color=TEAL,
            fg_color=LIGHT_TEAL,
            corner_radius=12,
            width=160,
            height=30,
        )
        status.pack(pady=(30, 20))

        title = ctk.CTkLabel(
            card,
            text="Insert One Pill",
            font=("Arial", 27, "bold"),
            text_color=TEXT,
        )
        title.pack()

        instructions = ctk.CTkLabel(
            card,
            text=(
                "Place a single pill inside the imaging chamber.\n"
                "Make sure the pill is fully visible before scanning."
            ),
            font=("Arial", 15),
            text_color=MUTED,
            justify="center",
        )
        instructions.pack(pady=(8, 25))

        scan_button = ctk.CTkButton(
            card,
            text="SCAN PILL",
            width=230,
            height=50,
            corner_radius=12,
            font=("Arial", 17, "bold"),
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.start_scan,
        )
        scan_button.pack()

        done_button = ctk.CTkButton(
            card,
            text="Return Home",
            width=120,
            height=32,
            fg_color="transparent",
            text_color=MUTED,
            hover_color="#E7EFF4",
            command=self.show_home_screen,
        )
        done_button.pack(pady=(12, 0))

    # ======================================================
    # SCANNING
    # ======================================================

    def start_scan(self):
        self.show_scanning_screen()
        worker = threading.Thread(
            target=self.run_scan_process,
            daemon=True,
        )
        worker.start()

    def show_scanning_screen(self):
        self.clear_screen()
        self.create_header(
            "Analyzing Medication",
            "AI ACTIVE",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        scan_circle = ctk.CTkFrame(
            card,
            width=92,
            height=92,
            corner_radius=46,
            fg_color=LIGHT_BLUE,
        )
        scan_circle.pack(pady=(30, 15))
        scan_circle.pack_propagate(False)

        scan_icon = ctk.CTkLabel(
            scan_circle,
            text="◎",
            font=("Arial", 46, "bold"),
            text_color=BLUE,
        )
        scan_icon.place(relx=0.5, rely=0.5, anchor="center")

        self.scan_status_label = ctk.CTkLabel(
            card,
            text="Scanning pill",
            font=("Arial", 24, "bold"),
            text_color=TEXT,
        )
        self.scan_status_label.pack()

        self.scan_subtitle_label = ctk.CTkLabel(
            card,
            text="Activating imaging system...",
            font=("Arial", 14),
            text_color=MUTED,
        )
        self.scan_subtitle_label.pack(pady=(5, 17))

        self.scan_progress = ctk.CTkProgressBar(
            card,
            width=400,
            height=12,
            corner_radius=6,
            progress_color=TEAL,
            fg_color="#DCE7ED",
        )
        self.scan_progress.pack()
        self.scan_progress.set(0)

        self.scan_animation_running = True
        self.scan_dot_count = 0
        self.animate_scanning_dots()

        # Demo mode uses the original smooth timed animation. In real mode
        # the controller moves this bar only when each physical stage finishes.
        if DEMO_MODE:
            self.animate_progress()

    def animate_scanning_dots(self):
        if not self.scan_animation_running:
            return

        self.scan_dot_count = (self.scan_dot_count + 1) % 4
        dots = "." * self.scan_dot_count

        try:
            self.scan_status_label.configure(text=f"Scanning pill{dots}")
        except Exception:
            return

        self.after(400, self.animate_scanning_dots)

    def animate_progress(self):
        if not self.scan_animation_running:
            return

        try:
            current = self.scan_progress.get()
        except Exception:
            return

        if current < 0.25:
            status_text = "Activating imaging lights..."
        elif current < 0.50:
            status_text = "Capturing top and bottom images..."
        elif current < 0.75:
            status_text = "Running AI identification..."
        else:
            status_text = "Comparing medication results..."

        try:
            self.scan_subtitle_label.configure(text=status_text)
            self.scan_progress.set(min(current + 0.025, 0.95))
        except Exception:
            return

        self.after(100, self.animate_progress)

    # ======================================================
    # DEMO / REAL SCAN PROCESS
    # ======================================================

    def run_scan_process(self):
        if DEMO_MODE:
            time.sleep(4)

            successful = random.random() < 0.90

            if successful:
                pill_id = random.choice(list(DEMO_PILLS.keys()))
                pill = DEMO_PILLS[pill_id]
                bin_number = get_bin_for_pill(pill_id)

                if bin_number is None:
                    self.after(0, self.show_carousel_full_screen)
                    return

                self.current_pill_id = pill_id
                self.current_pill = pill
                self.current_bin = bin_number

                add_pill_to_bin(
                    bin_number,
                    pill_id,
                    pill,
                )

                self.after(
                    0,
                    lambda: self.show_sorting_screen(
                        pill,
                        bin_number,
                    ),
                )
            else:
                self.after(0, self.show_reject_sorting_screen)

            return

        # ==================================================
        # REAL RXSORT WORKFLOW
        # ==================================================
        if self.controller is None or not self.controller.initialized:
            self.after(
                0,
                lambda: self.show_system_error_screen(
                    "RxSort is not ready.",
                    "The hardware controller has not finished initializing.",
                ),
            )
            return

        try:
            result = self.controller.scan_and_identify(
                self.real_scan_progress,
            )

            decision = result.get("decision")

            if decision == "EMPTY":
                self.after(0, self.show_no_pill_screen)
                return

            if decision == "REJECT":
                self.after(
                    0,
                    lambda: self.show_reject_sorting_screen(
                        auto_complete=False
                    ),
                )

                # Give Tk time to render the reject screen before the motor work.
                time.sleep(0.10)

                self.controller.reject_pill(
                    self.real_sort_progress,
                )

                self.after(0, self.show_reject_screen)
                return

            if decision != "IDENTIFIED":
                raise RxSortHardwareError(
                    f"Unexpected identification decision: {decision}"
                )

            pill_id = result["pill_id"]
            pill = self.controller.get_pill_info(
                pill_id,
                result.get("label", ""),
            )

            # If this pill exists in the demo display dictionary, retain the
            # richer description/image information already used by the UI.
            if pill_id in DEMO_PILLS:
                demo_pill = DEMO_PILLS[pill_id].copy()
                for key, value in pill.items():
                    if value not in (None, "", "Unknown", "Medication"):
                        demo_pill[key] = value
                pill = demo_pill

            bin_number = get_bin_for_pill(pill_id)

            if bin_number is None:
                self.after(0, self.show_carousel_full_screen)
                return

            self.current_pill_id = pill_id
            self.current_pill = pill
            self.current_bin = bin_number

            # Immediately show the real identification result and pill image.
            self.after(
                0,
                lambda: self.show_sorting_screen(
                    pill,
                    bin_number,
                    auto_complete=False,
                ),
            )

            time.sleep(0.10)

            # These calls block this worker thread until the REAL carousel and
            # pusher have physically completed their work.
            self.controller.sort_to_bin(
                bin_number,
                self.real_sort_progress,
            )

            # Only count the pill after the mechanical cycle succeeds.
            add_pill_to_bin(
                bin_number,
                pill_id,
                pill,
            )

            self.after(
                0,
                lambda: self.show_success_screen(
                    pill,
                    bin_number,
                ),
            )

        except Exception as error:
            self.after(
                0,
                lambda e=error: self.show_system_error_screen(
                    "Sorting cycle stopped.",
                    str(e),
                ),
            )

    def real_scan_progress(self, value, message):
        self.after(
            0,
            lambda v=value, m=message: self.update_real_scan_progress(v, m),
        )

    def update_real_scan_progress(self, value, message):
        try:
            self.scan_progress.set(value)
            self.scan_subtitle_label.configure(text=message)
        except Exception:
            pass

    def real_sort_progress(self, value, message):
        self.after(
            0,
            lambda m=message: self.update_real_sort_status(m),
        )

    def update_real_sort_status(self, message):
        try:
            if self.sort_destination_label is not None:
                self.sort_destination_label.configure(text=message)
        except Exception:
            pass

    def show_no_pill_screen(self):
        self.scan_animation_running = False
        self.clear_screen()
        self.create_header(
            "No Pill Detected",
            "WAITING",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        title = ctk.CTkLabel(
            card,
            text="No Pill Detected",
            font=("Arial", 25, "bold"),
            text_color=TEXT,
        )
        title.pack(pady=(65, 10))

        message = ctk.CTkLabel(
            card,
            text=(
                "Place one pill in the imaging chamber, then try the scan again."
            ),
            font=("Arial", 15),
            text_color=MUTED,
            wraplength=560,
            justify="center",
        )
        message.pack(pady=(0, 22))

        retry = ctk.CTkButton(
            card,
            text="TRY AGAIN",
            width=160,
            height=44,
            corner_radius=10,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.show_insert_screen,
        )
        retry.pack()

    # ======================================================
    # SORTING SCREEN
    # ======================================================

    def show_sorting_screen(self, pill, bin_number, auto_complete=True):
        self.scan_animation_running = False
        self.clear_screen()
        self.create_header(
            "Medication Identified",
            "SORTING",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        badge = ctk.CTkLabel(
            card,
            text="✓  IDENTIFIED",
            width=130,
            height=30,
            corner_radius=12,
            fg_color=LIGHT_GREEN,
            text_color=GREEN,
            font=("Arial", 13, "bold"),
        )
        badge.pack(pady=(22, 9))

        name = ctk.CTkLabel(
            card,
            text=pill["name"],
            font=("Arial", 24, "bold"),
            text_color=TEXT,
            wraplength=600,
        )
        name.pack()

        if pill.get("strength"):
            strength = ctk.CTkLabel(
                card,
                text=pill["strength"],
                font=("Arial", 14),
                text_color=MUTED,
            )
            strength.pack(pady=(2, 4))

        # Quick pill preview shown immediately after identification.
        # The image keeps its original proportions and is never stretched.
        image_value = pill.get("image")

        if image_value:
            image_path = Path(image_value)

            if image_path.exists():
                try:
                    pil_image = Image.open(image_path).convert("RGBA")

                    original_width = pil_image.width
                    original_height = pil_image.height

                    max_width = 92
                    max_height = 82

                    scale = min(
                        max_width / original_width,
                        max_height / original_height,
                        1.0,
                    )

                    display_width = max(1, int(original_width * scale))
                    display_height = max(1, int(original_height * scale))

                    pil_image = pil_image.resize(
                        (display_width, display_height),
                        Image.Resampling.LANCZOS,
                    )

                    self.current_pill_image = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(display_width, display_height),
                    )

                    pill_preview = ctk.CTkLabel(
                        card,
                        image=self.current_pill_image,
                        text="",
                        fg_color="transparent",
                    )
                    pill_preview.pack(pady=(1, 4))

                except Exception as error:
                    print("Quick pill image load error:", error)

        self.sort_destination_label = ctk.CTkLabel(
            card,
            text=f"Routing medication to Carousel Bin {bin_number}",
            font=("Arial", 15),
            text_color=MUTED,
        )
        self.sort_destination_label.pack(pady=(3, 0))

        # Demo mode keeps the original timed transition. Real mode waits for
        # the actual carousel + pusher cycle before showing Sort Complete.
        if auto_complete:
            self.after(
                1600,
                lambda: self.show_success_screen(pill, bin_number),
            )

    # ======================================================
    # SUCCESS SCREEN
    # ======================================================

    def show_success_screen(self, pill, bin_number):
        self.current_pill = pill
        self.current_bin = bin_number

        self.clear_screen()
        self.create_header(
            "Sort Complete",
            "READY",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        badge = ctk.CTkLabel(
            card,
            text="✓  SORT COMPLETE",
            width=155,
            height=30,
            corner_radius=13,
            fg_color=LIGHT_GREEN,
            text_color=GREEN,
            font=("Arial", 13, "bold"),
        )
        badge.pack(pady=(24, 13))

        name = ctk.CTkLabel(
            card,
            text=pill["name"],
            font=("Arial", 22, "bold"),
            text_color=TEXT,
            wraplength=600,
        )
        name.pack()

        detail_parts = []
        if pill.get("strength"):
            detail_parts.append(pill["strength"])
        detail_parts.append(pill["color"])
        detail_parts.append(pill["shape"])

        details = ctk.CTkLabel(
            card,
            text="  •  ".join(detail_parts),
            font=("Arial", 14),
            text_color=MUTED,
        )
        details.pack(pady=(7, 7))

        bin_label = ctk.CTkLabel(
            card,
            text=f"CAROUSEL BIN {bin_number}",
            width=150,
            height=34,
            corner_radius=10,
            fg_color=LIGHT_BLUE,
            text_color=BLUE,
            font=("Arial", 14, "bold"),
        )
        bin_label.pack(pady=(0, 15))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack()

        more_info = ctk.CTkButton(
            buttons,
            text="MORE INFO",
            width=120,
            height=42,
            corner_radius=10,
            fg_color=DARK_NAVY,
            hover_color=NAVY,
            command=self.show_more_info_screen,
        )
        more_info.grid(row=0, column=0, padx=4)

        view_bins = ctk.CTkButton(
            buttons,
            text="VIEW BINS",
            width=120,
            height=42,
            corner_radius=10,
            fg_color=TEAL,
            hover_color="#119D90",
            command=self.show_bin_map_screen,
        )
        view_bins.grid(row=0, column=1, padx=4)

        next_button = ctk.CTkButton(
            buttons,
            text="SCAN NEXT",
            width=120,
            height=42,
            corner_radius=10,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.show_insert_screen,
        )
        next_button.grid(row=0, column=2, padx=4)

        done = ctk.CTkButton(
            buttons,
            text="DONE",
            width=90,
            height=42,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color="#B8C7D1",
            text_color=TEXT,
            hover_color="#EDF3F6",
            command=self.show_home_screen,
        )
        done.grid(row=0, column=3, padx=4)

    # ======================================================
    # MORE INFO SCREEN
    # ======================================================

    def show_more_info_screen(self):
        if self.current_pill is None:
            self.show_home_screen()
            return

        pill = self.current_pill

        self.clear_screen()
        self.create_header(
            "Medication Information",
            f"BIN {self.current_bin}",
        )

        card = ctk.CTkFrame(
            self,
            width=750,
            height=360,
            corner_radius=22,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(10, 14))
        card.pack_propagate(False)

        # ---------------- LEFT IMAGE PANEL ----------------
        image_card = ctk.CTkFrame(
            card,
            width=285,
            height=315,
            corner_radius=18,
            fg_color="#F4F8FA",
        )
        image_card.place(x=20, y=22)
        image_card.pack_propagate(False)

        image_value = pill.get("image")

        if image_value:
            image_path = Path(image_value)
            print("\nTrying pill image:")
            print(image_path)

            if image_path.exists():
                try:
                    pil_image = Image.open(image_path).convert("RGBA")

                    original_width = pil_image.width
                    original_height = pil_image.height

                    max_width = 255
                    max_height = 285

                    # Preserve aspect ratio and never enlarge low-res images.
                    scale = min(
                        max_width / original_width,
                        max_height / original_height,
                        1.0,
                    )

                    display_width = max(
                        1,
                        int(original_width * scale),
                    )
                    display_height = max(
                        1,
                        int(original_height * scale),
                    )

                    # High-quality image resize.
                    pil_image = pil_image.resize(
                        (display_width, display_height),
                        Image.Resampling.LANCZOS,
                    )

                    self.current_pill_image = ctk.CTkImage(
                        light_image=pil_image,
                        dark_image=pil_image,
                        size=(display_width, display_height),
                    )

                    image_label = ctk.CTkLabel(
                        image_card,
                        image=self.current_pill_image,
                        text="",
                    )
                    image_label.place(
                        relx=0.5,
                        rely=0.5,
                        anchor="center",
                    )

                    print("IMAGE LOADED SUCCESSFULLY")

                except Exception as error:
                    print("IMAGE LOAD ERROR:", error)
                    self.show_image_placeholder(image_card)
            else:
                print("IMAGE FILE NOT FOUND")
                self.show_image_placeholder(image_card)
        else:
            self.show_image_placeholder(image_card)

        # ---------------- RIGHT INFO PANEL ----------------
        info_panel = ctk.CTkFrame(
            card,
            width=410,
            height=315,
            corner_radius=0,
            fg_color="transparent",
        )
        info_panel.place(x=325, y=16)
        info_panel.pack_propagate(False)

        name_label = ctk.CTkLabel(
            info_panel,
            text=pill["name"],
            font=("Arial", 19, "bold"),
            text_color=TEXT,
            wraplength=395,
            justify="left",
            anchor="w",
        )
        name_label.pack(fill="x", pady=(0, 8))

        details_frame = ctk.CTkFrame(
            info_panel,
            fg_color="transparent",
        )
        details_frame.pack(fill="x")
        details_frame.grid_columnconfigure(0, minsize=92)
        details_frame.grid_columnconfigure(1, weight=1)

        detail_rows = []

        if pill.get("strength"):
            detail_rows.append(("Strength", pill["strength"]))

        detail_rows.extend(
            [
                ("Imprint", pill["imprint"]),
                ("Color", pill["color"]),
                ("Shape", pill["shape"]),
                ("Form", pill["dosage_form"]),
                ("Bin", str(self.current_bin)),
            ]
        )

        for row_number, (label_text, value_text) in enumerate(detail_rows):
            label = ctk.CTkLabel(
                details_frame,
                text=label_text,
                font=("Arial", 12, "bold"),
                text_color=MUTED,
                anchor="w",
                justify="left",
            )
            label.grid(
                row=row_number,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=1,
            )

            value = ctk.CTkLabel(
                details_frame,
                text=value_text,
                font=("Arial", 12),
                text_color=TEXT,
                anchor="w",
                justify="left",
                wraplength=285,
            )
            value.grid(
                row=row_number,
                column=1,
                sticky="w",
                pady=1,
            )

        description_title = ctk.CTkLabel(
            info_panel,
            text="What this medication does",
            font=("Arial", 14, "bold"),
            text_color=TEXT,
            anchor="w",
        )
        description_title.pack(fill="x", pady=(10, 2))

        description_label = ctk.CTkLabel(
            info_panel,
            text=pill["description"],
            font=("Arial", 11),
            text_color=MUTED,
            wraplength=390,
            justify="left",
            anchor="w",
        )
        description_label.pack(fill="x", pady=(0, 6))

        back_button = ctk.CTkButton(
            info_panel,
            text="←  BACK",
            width=105,
            height=30,
            corner_radius=8,
            fg_color=BLUE,
            hover_color="#1189BC",
            font=("Arial", 11, "bold"),
            command=lambda: self.show_success_screen(
                self.current_pill,
                self.current_bin,
            ),
        )
        back_button.pack(anchor="e", pady=(0, 0))

    def show_image_placeholder(self, parent):
        label = ctk.CTkLabel(
            parent,
            text="Medication image\nnot available",
            font=("Arial", 14),
            text_color=MUTED,
            justify="center",
        )
        label.place(relx=0.5, rely=0.5, anchor="center")

    # ======================================================
    # INTERACTIVE BIN MAP
    # ======================================================

    def show_bin_map_screen(self):
        self.clear_screen()
        self.create_header(
            "Carousel Bin Map",
            "TAP A BIN",
        )

        card = ctk.CTkFrame(
            self,
            width=750,
            height=360,
            corner_radius=22,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(10, 14))
        card.pack_propagate(False)

        # ---------------- LEFT: CAROUSEL ----------------
        carousel_frame = ctk.CTkFrame(
            card,
            width=370,
            height=315,
            corner_radius=18,
            fg_color="#F4F8FA",
        )
        carousel_frame.place(x=18, y=20)
        carousel_frame.pack_propagate(False)

        carousel_title = ctk.CTkLabel(
            carousel_frame,
            text="CAROUSEL",
            font=("Arial", 12, "bold"),
            text_color=MUTED,
        )
        carousel_title.place(relx=0.5, y=20, anchor="center")

        center = ctk.CTkFrame(
            carousel_frame,
            width=120,
            height=120,
            corner_radius=60,
            fg_color=NAVY,
        )
        center.place(x=125, y=100)
        center.pack_propagate(False)

        center_text = ctk.CTkLabel(
            center,
            text="RxSort\nBins",
            font=("Arial", 18, "bold"),
            text_color=WHITE,
            justify="center",
        )
        center_text.place(relx=0.5, rely=0.5, anchor="center")

        bin_positions = {
            1: (163, 42),
            2: (236, 65),
            3: (278, 125),
            4: (275, 195),
            5: (230, 245),
            6: (163, 260),
            7: (95, 245),
            8: (50, 195),
            9: (47, 125),
            10: (90, 65),
        }

        for bin_number in range(1, 11):
            if bin_number == REJECT_BIN:
                bin_color = LIGHT_RED
                text_color = RED
            elif bin_number in bin_contents:
                bin_color = LIGHT_GREEN
                text_color = GREEN
            else:
                bin_color = "#E5EDF2"
                text_color = MUTED

            x, y = bin_positions[bin_number]

            button = ctk.CTkButton(
                carousel_frame,
                text=str(bin_number),
                width=52,
                height=52,
                corner_radius=26,
                fg_color=bin_color,
                hover_color=LIGHT_BLUE,
                text_color=text_color,
                font=("Arial", 16, "bold"),
                command=lambda b=bin_number: self.show_bin_details(b),
            )
            button.place(x=x, y=y)

        # ---------------- RIGHT: DETAILS ----------------
        self.bin_detail_panel = ctk.CTkFrame(
            card,
            width=325,
            height=315,
            corner_radius=18,
            fg_color="#F8FAFB",
        )
        self.bin_detail_panel.place(x=405, y=20)
        self.bin_detail_panel.pack_propagate(False)

        title = ctk.CTkLabel(
            self.bin_detail_panel,
            text="Select a Bin",
            font=("Arial", 22, "bold"),
            text_color=TEXT,
        )
        title.pack(pady=(70, 8))

        instructions = ctk.CTkLabel(
            self.bin_detail_panel,
            text=(
                "Tap any numbered bin on the\n"
                "carousel to see its contents."
            ),
            font=("Arial", 13),
            text_color=MUTED,
            justify="center",
        )
        instructions.pack()

        back = ctk.CTkButton(
            self.bin_detail_panel,
            text="←  BACK",
            width=110,
            height=34,
            corner_radius=9,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.return_from_bin_map,
        )
        back.pack(side="bottom", pady=18)

    def show_bin_details(self, bin_number):
        if self.bin_detail_panel is None:
            return

        for widget in self.bin_detail_panel.winfo_children():
            widget.destroy()

        bin_label = ctk.CTkLabel(
            self.bin_detail_panel,
            text=f"BIN {bin_number}",
            font=("Arial", 13, "bold"),
            text_color=BLUE,
        )
        bin_label.pack(pady=(25, 5))

        if bin_number == REJECT_BIN:
            title = ctk.CTkLabel(
                self.bin_detail_panel,
                text="Reject Bin",
                font=("Arial", 22, "bold"),
                text_color=RED,
            )
            title.pack(pady=(5, 8))

            description = ctk.CTkLabel(
                self.bin_detail_panel,
                text=(
                    "Bin 10 is permanently reserved\n"
                    "for unidentified medications."
                ),
                font=("Arial", 13),
                text_color=MUTED,
                justify="center",
            )
            description.pack()

        elif bin_number in bin_contents:
            content = bin_contents[bin_number]
            pill = content["pill"]
            count = content["count"]

            medication_name = ctk.CTkLabel(
                self.bin_detail_panel,
                text=pill["name"],
                font=("Arial", 19, "bold"),
                text_color=TEXT,
                wraplength=275,
                justify="center",
            )
            medication_name.pack(pady=(5, 6))

            if pill.get("strength"):
                strength = ctk.CTkLabel(
                    self.bin_detail_panel,
                    text=pill["strength"],
                    font=("Arial", 13),
                    text_color=MUTED,
                )
                strength.pack()

            count_text = f"{count} pill" if count == 1 else f"{count} pills"

            quantity = ctk.CTkLabel(
                self.bin_detail_panel,
                text=count_text,
                width=100,
                height=30,
                corner_radius=10,
                fg_color=LIGHT_GREEN,
                text_color=GREEN,
                font=("Arial", 13, "bold"),
            )
            quantity.pack(pady=(12, 5))

            imprint = ctk.CTkLabel(
                self.bin_detail_panel,
                text=f"Imprint: {pill['imprint']}",
                font=("Arial", 12),
                text_color=MUTED,
            )
            imprint.pack(pady=(4, 0))

        else:
            empty_title = ctk.CTkLabel(
                self.bin_detail_panel,
                text="Empty Bin",
                font=("Arial", 22, "bold"),
                text_color=TEXT,
            )
            empty_title.pack(pady=(15, 8))

            empty_text = ctk.CTkLabel(
                self.bin_detail_panel,
                text=(
                    "No medication has been\n"
                    "assigned to this bin yet."
                ),
                font=("Arial", 13),
                text_color=MUTED,
                justify="center",
            )
            empty_text.pack()

        back = ctk.CTkButton(
            self.bin_detail_panel,
            text="←  BACK",
            width=110,
            height=34,
            corner_radius=9,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.return_from_bin_map,
        )
        back.pack(side="bottom", pady=18)

    def return_from_bin_map(self):
        if self.current_pill is not None and self.current_bin is not None:
            self.show_success_screen(
                self.current_pill,
                self.current_bin,
            )
        else:
            self.show_home_screen()

    # ======================================================
    # REJECT FLOW
    # ======================================================

    def show_reject_sorting_screen(self, auto_complete=True):
        self.scan_animation_running = False
        self.clear_screen()
        self.create_header(
            "Medication Not Identified",
            "REJECT",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        badge = ctk.CTkLabel(
            card,
            text="!  UNRECOGNIZED",
            width=150,
            height=30,
            corner_radius=12,
            fg_color=LIGHT_RED,
            text_color=RED,
            font=("Arial", 13, "bold"),
        )
        badge.pack(pady=(50, 18))

        title = ctk.CTkLabel(
            card,
            text="Moving Pill to Reject Bin",
            font=("Arial", 24, "bold"),
            text_color=TEXT,
        )
        title.pack()

        self.sort_destination_label = ctk.CTkLabel(
            card,
            text=f"The medication will be routed to Bin {REJECT_BIN}.",
            font=("Arial", 15),
            text_color=MUTED,
        )
        self.sort_destination_label.pack(pady=(8, 0))

        if auto_complete:
            self.after(1600, self.show_reject_screen)

    def show_reject_screen(self):
        self.clear_screen()
        self.create_header(
            "Medication Rejected",
            "BIN 10",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        badge = ctk.CTkLabel(
            card,
            text="✕  NOT IDENTIFIED",
            width=160,
            height=30,
            corner_radius=12,
            fg_color=LIGHT_RED,
            text_color=RED,
            font=("Arial", 13, "bold"),
        )
        badge.pack(pady=(38, 15))

        message = ctk.CTkLabel(
            card,
            text=(
                f"The pill has been moved to Reject Bin {REJECT_BIN}.\n"
                "Retrieve the medication and try scanning it again."
            ),
            font=("Arial", 16),
            text_color=TEXT,
            justify="center",
        )
        message.pack(pady=(0, 24))

        button_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        button_frame.pack()

        retry = ctk.CTkButton(
            button_frame,
            text="TRY AGAIN",
            width=150,
            height=42,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.show_insert_screen,
        )
        retry.grid(row=0, column=0, padx=7)

        done = ctk.CTkButton(
            button_frame,
            text="DONE",
            width=110,
            height=42,
            fg_color="transparent",
            border_width=1,
            border_color="#B8C7D1",
            text_color=TEXT,
            hover_color="#EDF3F6",
            command=self.show_home_screen,
        )
        done.grid(row=0, column=1, padx=7)

    # ======================================================
    # CAROUSEL FULL
    # ======================================================

    def show_carousel_full_screen(self):
        self.clear_screen()
        self.create_header(
            "Carousel Full",
            "ATTENTION",
        )

        card = ctk.CTkFrame(
            self,
            width=700,
            height=325,
            corner_radius=24,
            fg_color=WHITE,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(expand=True, pady=(15, 20))
        card.pack_propagate(False)

        warning = ctk.CTkLabel(
            card,
            text="No Medication Bins Available",
            font=("Arial", 24, "bold"),
            text_color=RED,
        )
        warning.pack(pady=(65, 10))

        message = ctk.CTkLabel(
            card,
            text=(
                "Bins 1 through 9 are currently assigned.\n"
                "Bin 10 remains reserved for rejected pills."
            ),
            font=("Arial", 15),
            text_color=MUTED,
            justify="center",
        )
        message.pack(pady=(0, 20))

        done = ctk.CTkButton(
            card,
            text="RETURN HOME",
            width=160,
            height=42,
            fg_color=BLUE,
            hover_color="#1189BC",
            command=self.show_home_screen,
        )
        done.pack()


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Scale widgets for the 1024x600 Waveshare screen while keeping
    # the actual application window at the panel's native resolution.
    ctk.set_widget_scaling(UI_SCALE)
    ctk.set_window_scaling(1.0)

    app = RxSortUI()
    app.mainloop()
