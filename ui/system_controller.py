"""RxSort system controller.

IMPORTANT:
This controller deliberately reuses the SAME camera/crop pipeline from
ai_interface.dual_camera_test instead of reimplementing it.

That means the standalone dual-camera test and the UI use:
- the same camera IDs
- the same focus values
- the same 1280x720 camera configuration
- the same lighting/capture sequence
- the same crop_top_image()/crop_bottom_image() calls
- the same identify_top_pill()/identify_bottom_pill() functions

scan_and_identify() NEVER moves the carousel or pusher.
"""

from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path
from typing import Callable, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "rxsort.db"
PILL_IMAGE_FOLDER = PROJECT_ROOT / "assets" / "pill_images"

CONFIDENCE_THRESHOLD = 0.80
REJECT_BIN = 10
NO_PILL_ID = 18


class RxSortHardwareError(RuntimeError):
    pass


class RxSortController:
    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        top_model_path=None,
        bottom_model_path=None,
    ):
        # Model path arguments remain only for compatibility with older UI code.
        self.confidence_threshold = float(confidence_threshold)

        self.top_camera = None
        self.bottom_camera = None

        self.dual = None
        self.ai = None
        self.carousel = None
        self.pusher = None
        self.lighting = None

        self.initialized = False
        self.busy = False

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def initialize(self, progress_callback: Optional[Callable] = None):
        if self.initialized:
            return

        try:
            self._progress(progress_callback, 0.05,
                           "Loading RxSort modules...")

            # SOURCE OF TRUTH FOR CAMERA/CROP PIPELINE
            self.dual = importlib.import_module(
                "ai_interface.dual_camera_test"
            )

            # SOURCE OF TRUTH FOR AI PIPELINE
            self.ai = importlib.import_module(
                "ai_interface.edge_impulse_interface"
            )

            self.carousel = importlib.import_module(
                "hardware.carousel"
            )
            self.pusher = importlib.import_module(
                "hardware.pusher"
            )
            self.lighting = importlib.import_module(
                "hardware.lighting"
            )

            self._progress(progress_callback, 0.18, "Initializing carousel...")
            result = self.carousel.initialize_carousel()
            if result is False:
                raise RxSortHardwareError(
                    "Carousel failed to initialize."
                )

            self._progress(progress_callback, 0.30, "Initializing pusher...")
            result = self.pusher.initialize_pusher()
            if result is False:
                raise RxSortHardwareError(
                    "Pusher failed to initialize."
                )

            self.lighting.lights_off()

            # DO NOT create/configure cameras here ourselves.
            # Use the exact setup_camera() that the working test uses.
            self._progress(progress_callback, 0.48, "Starting TOP camera...")
            self.top_camera = self.dual.setup_camera(
                self.dual.TOP_CAMERA_ID,
                self.dual.TOP_FOCUS,
            )

            self._progress(progress_callback, 0.68,
                           "Starting BOTTOM camera...")
            self.bottom_camera = self.dual.setup_camera(
                self.dual.BOTTOM_CAMERA_ID,
                self.dual.BOTTOM_FOCUS,
            )

            self.initialized = True

            self._progress(
                progress_callback,
                1.0,
                "RxSort system ready.",
            )

            print("\n================================================")
            print("RXSORT CONTROLLER READY")
            print("Using ai_interface.dual_camera_test as")
            print("the camera/capture/crop source of truth.")
            print(f"TOP focus:    {self.dual.TOP_FOCUS}")
            print(f"BOTTOM focus: {self.dual.BOTTOM_FOCUS}")
            print("================================================\n")

        except Exception as exc:
            self.shutdown(suppress_errors=True)

            if isinstance(exc, RxSortHardwareError):
                raise

            raise RxSortHardwareError(
                f"RxSort initialization failed: {exc}"
            ) from exc

    # ======================================================
    # SCAN / IDENTIFY
    # ======================================================

    def scan_and_identify(
        self,
        progress_callback: Optional[Callable] = None,
    ):
        self._require_initialized()

        if self.busy:
            raise RxSortHardwareError(
                "RxSort is already processing a pill."
            )

        self.busy = True

        try:
            print("\n================================================")
            print("RXSORT REAL SCAN START")
            print("================================================")

            self._progress(
                progress_callback,
                0.10,
                "Capturing top and bottom images...",
            )

            # CRITICAL FIX:
            # Call the SAME capture_both() used by the known-good
            # dual_camera_test.py. This function handles lights, timing,
            # camera capture, and the exact training crops.
            self.dual.capture_both(
                self.top_camera,
                self.bottom_camera,
            )

            top_cropped_path = Path(
                self.dual.TOP_CROPPED_IMAGE
            )
            bottom_cropped_path = Path(
                self.dual.BOTTOM_CROPPED_IMAGE
            )

            # dual_camera_test uses relative filenames. Resolve them from
            # the project root because the UI is launched from ~/RxSort.
            if not top_cropped_path.is_absolute():
                top_cropped_path = PROJECT_ROOT / top_cropped_path

            if not bottom_cropped_path.is_absolute():
                bottom_cropped_path = PROJECT_ROOT / bottom_cropped_path

            if not top_cropped_path.exists():
                raise RxSortHardwareError(
                    f"TOP cropped image was not created: {top_cropped_path}"
                )

            if not bottom_cropped_path.exists():
                raise RxSortHardwareError(
                    f"BOTTOM cropped image was not created: {bottom_cropped_path}"
                )

            self._progress(
                progress_callback,
                0.52,
                "Running TOP AI identification...",
            )

            print("\n[AI] Running EXACT TOP identification function...")
            top_result = self.ai.identify_top_pill(
                str(top_cropped_path)
            )

            self._validate_ai_result(
                top_result,
                "TOP",
            )

            self._progress(
                progress_callback,
                0.72,
                "Running BOTTOM AI identification...",
            )

            print("\n[AI] Running EXACT BOTTOM identification function...")
            bottom_result = self.ai.identify_bottom_pill(
                str(bottom_cropped_path)
            )

            self._validate_ai_result(
                bottom_result,
                "BOTTOM",
            )

            print("\n================================================")
            print("AI RESULTS USED BY UI")
            print("================================================")
            self._print_result("TOP", top_result)
            self._print_result("BOTTOM", bottom_result)

            self._progress(
                progress_callback,
                0.88,
                "Comparing AI results...",
            )

            decision = self._compare_predictions(
                top_result,
                bottom_result,
            )

            decision["top_image"] = str(
                top_cropped_path
            )
            decision["bottom_image"] = str(
                bottom_cropped_path
            )

            print("\n================================================")
            print("FINAL DECISION")
            print("================================================")
            print(f"Decision: {decision['decision']}")
            print(f"Reason: {decision['reason']}")

            if decision.get("label"):
                print(f"Medication: {decision['label']}")

            if decision.get("pill_id") is not None:
                print(f"Pill ID: {decision['pill_id']}")

            if decision.get("confidence") is not None:
                print(
                    "Confidence: "
                    f"{decision['confidence'] * 100:.2f}%"
                )

            print("================================================\n")

            self._progress(
                progress_callback,
                1.0,
                decision["reason"],
            )

            return decision

        except Exception as exc:
            print(f"\nRXSORT SCAN ERROR: {exc}")

            if isinstance(exc, RxSortHardwareError):
                raise

            raise RxSortHardwareError(
                f"Scan/identification failed: {exc}"
            ) from exc

        finally:
            try:
                if self.lighting is not None:
                    self.lighting.lights_off()
            except Exception:
                pass

            self.busy = False

    def _compare_predictions(self, top, bottom):
        top_id = top["pill_id"]
        bottom_id = bottom["pill_id"]

        top_conf = float(top["confidence"])
        bottom_conf = float(bottom["confidence"])

        # Empty chamber
        if (
            top_id == NO_PILL_ID
            and bottom_id == NO_PILL_ID
        ):
            return {
                "decision": "EMPTY",
                "pill_id": NO_PILL_ID,
                "label": "Nothing",
                "confidence": min(top_conf, bottom_conf),
                "top": top,
                "bottom": bottom,
                "reason": "No pill detected. Insert one pill to continue.",
            }

        # One camera sees empty
        if (
            top_id == NO_PILL_ID
            or bottom_id == NO_PILL_ID
        ):
            return {
                "decision": "REJECT",
                "pill_id": None,
                "label": None,
                "confidence": min(top_conf, bottom_conf),
                "top": top,
                "bottom": bottom,
                "reason": "Only one camera detected a pill.",
            }

        # Models disagree
        if top_id != bottom_id:
            return {
                "decision": "REJECT",
                "pill_id": None,
                "label": None,
                "confidence": min(top_conf, bottom_conf),
                "top": top,
                "bottom": bottom,
                "reason": "Top and bottom AI models disagree on the medication.",
            }

        # Both must pass threshold
        if (
            top_conf < self.confidence_threshold
            or bottom_conf < self.confidence_threshold
        ):
            return {
                "decision": "REJECT",
                "pill_id": None,
                "label": None,
                "confidence": min(top_conf, bottom_conf),
                "top": top,
                "bottom": bottom,
                "reason": "Identification confidence is below the required threshold.",
            }

        average_confidence = (
            top_conf + bottom_conf
        ) / 2.0

        return {
            "decision": "IDENTIFIED",
            "pill_id": top_id,
            "label": top["label"],
            "confidence": average_confidence,
            "top": top,
            "bottom": bottom,
            "reason": f"Medication identified as {top['label']}.",
        }

    @staticmethod
    def _validate_ai_result(result, name):
        if result is None:
            raise RxSortHardwareError(
                f"{name} AI returned no result."
            )

        for key in (
            "label",
            "confidence",
            "pill_id",
        ):
            if key not in result:
                raise RxSortHardwareError(
                    f"{name} AI result is missing '{key}'."
                )

    @staticmethod
    def _print_result(name, result):
        print(
            f"{name}: "
            f"{result['label']} "
            f"({float(result['confidence']) * 100:.2f}%) "
            f"[pill_id={result['pill_id']}]"
        )

    # ======================================================
    # MECHANICAL SORTING
    # ======================================================

    def sort_to_bin(
        self,
        target_bin: int,
        progress_callback: Optional[Callable] = None,
    ):
        self._require_initialized()

        if self.busy:
            raise RxSortHardwareError(
                "RxSort is already processing a pill."
            )

        try:
            target_bin = int(target_bin)
        except Exception as exc:
            raise RxSortHardwareError(
                f"Invalid target bin: {target_bin}"
            ) from exc

        if not 1 <= target_bin <= 10:
            raise RxSortHardwareError(
                f"Target bin must be 1-10, got {target_bin}."
            )

        self.busy = True

        try:
            self._progress(
                progress_callback,
                0.20,
                f"Positioning carousel at Bin {target_bin}...",
            )

            self.carousel.rotate_to_bin(
                target_bin
            )

            self._progress(
                progress_callback,
                0.65,
                "Pushing medication into bin...",
            )

            self.pusher.push_cycle()

            self._progress(
                progress_callback,
                1.0,
                "Sorting complete.",
            )

        except Exception as exc:
            raise RxSortHardwareError(
                f"Mechanical sorting failed: {exc}"
            ) from exc

        finally:
            self.busy = False

    def reject_pill(
        self,
        progress_callback: Optional[Callable] = None,
    ):
        self.sort_to_bin(
            REJECT_BIN,
            progress_callback,
        )

    # ======================================================
    # DATABASE / UI INFORMATION
    # ======================================================

    def get_pill_info(
        self,
        pill_id: int,
        fallback_label: str = "",
    ):
        row = self._database_row_for_pill(
            pill_id
        ) or {}

        name = (
            row.get("medication_name")
            or row.get("name")
            or fallback_label
            or f"Pill {pill_id}"
        )

        info = {
            "name": name,
            "strength": row.get("strength") or "",
            "imprint": row.get("imprint") or "",
            "color": row.get("color") or "Unknown",
            "shape": row.get("shape") or "Unknown",
            "dosage_form": (
                row.get("dosage_form")
                or row.get("form")
                or "Medication"
            ),
            "description": (
                row.get("description")
                or "Medication identified by the RxSort dual-camera AI system."
            ),
        }

        info["image"] = self._find_pill_image(
            name,
            fallback_label,
        )

        return info

    def _database_row_for_pill(self, pill_id):
        if not DATABASE_PATH.exists():
            return None

        connection = None

        try:
            connection = sqlite3.connect(
                DATABASE_PATH
            )
            connection.row_factory = sqlite3.Row

            row = connection.execute(
                "SELECT * FROM pills WHERE pill_id = ?",
                (pill_id,),
            ).fetchone()

            return dict(row) if row else None

        except Exception as exc:
            print(
                f"Warning: database lookup failed: {exc}"
            )
            return None

        finally:
            if connection is not None:
                connection.close()

    def _find_pill_image(self, *names):
        if not PILL_IMAGE_FOLDER.exists():
            return None

        targets = [
            self._normalize_name(name)
            for name in names
            if name
        ]

        files = []

        for pattern in (
            "*.png",
            "*.jpg",
            "*.jpeg",
            "*.PNG",
            "*.JPG",
            "*.JPEG",
        ):
            files.extend(
                PILL_IMAGE_FOLDER.glob(pattern)
            )

        for path in files:
            stem = self._normalize_name(
                path.stem
            )

            if stem in targets:
                return path

        for path in files:
            stem = self._normalize_name(
                path.stem
            )

            for target in targets:
                if target and (
                    target in stem
                    or stem in target
                ):
                    return path

        return None

    # ======================================================
    # SHUTDOWN
    # ======================================================

    def shutdown(
        self,
        suppress_errors: bool = False,
    ):
        errors = []

        try:
            if self.lighting is not None:
                self.lighting.lights_off()
        except Exception as exc:
            errors.append(exc)

        for camera in (
            self.top_camera,
            self.bottom_camera,
        ):
            if camera is None:
                continue

            try:
                camera.stop()
            except Exception:
                pass

            try:
                camera.close()
            except Exception as exc:
                errors.append(exc)

        self.top_camera = None
        self.bottom_camera = None

        try:
            if self.pusher is not None:
                self.pusher.shutdown_pusher()
        except Exception as exc:
            errors.append(exc)

        try:
            if self.carousel is not None:
                self.carousel.shutdown_carousel()
        except Exception as exc:
            errors.append(exc)

        self.initialized = False
        self.busy = False

        if errors and not suppress_errors:
            raise RxSortHardwareError(
                "; ".join(str(error) for error in errors)
            )

    # ======================================================
    # HELPERS
    # ======================================================

    @staticmethod
    def _normalize_name(value):
        return "".join(
            char.lower()
            for char in str(value)
            if char.isalnum()
        )

    def _require_initialized(self):
        if not self.initialized:
            raise RxSortHardwareError(
                "RxSort hardware has not been initialized."
            )

    @staticmethod
    def _progress(callback, value, message):
        if callback is not None:
            callback(
                float(value),
                str(message),
            )


# ==========================================================
# STANDALONE TEST
# ==========================================================

if __name__ == "__main__":
    controller = RxSortController()

    def console_progress(value, message):
        print(
            f"[{value:>5.0%}] {message}"
        )

    try:
        controller.initialize(
            console_progress
        )

        print(
            "\nPlace ONE pill in the chamber, then press ENTER."
        )
        input()

        result = controller.scan_and_identify(
            console_progress
        )

        print("\nRESULT:")
        print(result)

        print(
            "\nNOTE: standalone test does NOT move carousel/pusher."
        )

    finally:
        controller.shutdown(
            suppress_errors=True
        )
