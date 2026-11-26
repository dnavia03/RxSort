from picamera2 import Picamera2
from libcamera import controls
from time import sleep

from hardware.lighting import lights_on, lights_off
from ai_interface.edge_impulse_interface import (
    identify_top_pill,
    identify_bottom_pill,
)
from database.database_manager import get_pill_by_id

import cv2

from vision.crop_settings import (
    crop_top_image,
    crop_bottom_image,
)


# ==========================================================
# RXSORT DUAL CAMERA CONFIGURATION
# ==========================================================

TOP_CAMERA_ID = 0
BOTTOM_CAMERA_ID = 1

TOP_FOCUS = 8.00
BOTTOM_FOCUS = 9.00

TOP_IMAGE = "top_live.jpg"
BOTTOM_IMAGE = "bottom_live.jpg"

TOP_CROPPED_IMAGE = "top_live_cropped.jpg"
BOTTOM_CROPPED_IMAGE = "bottom_live_cropped.jpg"

CONFIDENCE_THRESHOLD = 0.80
NOTHING_PILL_ID = 18
LIGHT_STABILIZATION_DELAY = 3.0


# ==========================================================
# CAMERA SETUP
# ==========================================================

def setup_camera(camera_id, focus_value):
    camera = Picamera2(camera_num=camera_id)

    config = camera.create_still_configuration(
        main={"size": (1280, 720)}
    )

    camera.configure(config)
    camera.start()
    sleep(0.5)

    camera.set_controls({
        "AfMode": controls.AfModeEnum.Manual,
        "LensPosition": focus_value,
    })

    sleep(0.5)
    return camera


# ==========================================================
# PRINT INDIVIDUAL AI RESULT
# ==========================================================

def print_result(camera_name, result):
    if result is None:
        print(f"{camera_name}: No valid AI result")
        return

    print(
        f"{camera_name}: "
        f"{result['label']} "
        f"({result['confidence'] * 100:.2f}%)"
    )


# ==========================================================
# EVALUATE BOTH CAMERA RESULTS
# ==========================================================

def evaluate_two_cameras(top_result, bottom_result):
    if top_result is None or bottom_result is None:
        return {
            "decision": "REJECT",
            "reason": "One or both AI results were invalid.",
        }

    top_id = top_result["pill_id"]
    bottom_id = bottom_result["pill_id"]
    top_confidence = top_result["confidence"]
    bottom_confidence = bottom_result["confidence"]

    if top_id == NOTHING_PILL_ID and bottom_id == NOTHING_PILL_ID:
        return {"decision": "EMPTY"}

    if top_id == NOTHING_PILL_ID or bottom_id == NOTHING_PILL_ID:
        return {
            "decision": "REJECT",
            "reason": "Only one camera detected a pill.",
        }

    if top_id != bottom_id:
        return {
            "decision": "REJECT",
            "reason": "Top and bottom AI models disagree.",
        }

    if (
        top_confidence < CONFIDENCE_THRESHOLD
        or bottom_confidence < CONFIDENCE_THRESHOLD
    ):
        return {
            "decision": "REJECT",
            "reason": "One or both confidence scores are below threshold.",
        }

    average_confidence = (top_confidence + bottom_confidence) / 2

    return {
        "decision": "SORT",
        "pill_id": top_id,
        "label": top_result["label"],
        "confidence": average_confidence,
    }


# ==========================================================
# CAPTURE ONE TOP + BOTTOM IMAGE PAIR
# ==========================================================

def capture_both(top_camera, bottom_camera):
    print("\nTurning imaging lights ON...")
    lights_on()
    print("Imaging lights ON.")

    print(
        f"\nWaiting {LIGHT_STABILIZATION_DELAY:.0f} seconds "
        "for lighting and camera exposure to stabilize..."
    )
    sleep(LIGHT_STABILIZATION_DELAY)

    print("\nCapturing TOP image...")
    top_camera.capture_file(TOP_IMAGE)
    print("TOP image captured.")

    sleep(0.2)

    print("\nCapturing BOTTOM image...")
    bottom_camera.capture_file(BOTTOM_IMAGE)
    print("BOTTOM image captured.")

    top_image = cv2.imread(TOP_IMAGE)
    bottom_image = cv2.imread(BOTTOM_IMAGE)

    if top_image is None:
        raise RuntimeError("Could not load TOP image.")

    if bottom_image is None:
        raise RuntimeError("Could not load BOTTOM image.")

    top_cropped = crop_top_image(top_image)
    bottom_cropped = crop_bottom_image(bottom_image)

    if top_cropped is None or top_cropped.size == 0:
        raise RuntimeError("TOP crop is empty.")

    if bottom_cropped is None or bottom_cropped.size == 0:
        raise RuntimeError("BOTTOM crop is empty.")

    if not cv2.imwrite(TOP_CROPPED_IMAGE, top_cropped):
        raise RuntimeError("Could not save TOP cropped image.")

    if not cv2.imwrite(BOTTOM_CROPPED_IMAGE, bottom_cropped):
        raise RuntimeError("Could not save BOTTOM cropped image.")

    print("\nCropped live images created.")
    print(f"TOP cropped: {TOP_CROPPED_IMAGE}")
    print(f"BOTTOM cropped: {BOTTOM_CROPPED_IMAGE}")


# ==========================================================
# RUN ONE COMPLETE TEST
# ==========================================================

def run_test(top_camera, bottom_camera):
    print("\n================================")
    print("          STARTING TEST")
    print("================================")

    capture_both(top_camera, bottom_camera)

    print("\nRunning TOP AI model...")
    top_result = identify_top_pill(TOP_CROPPED_IMAGE)

    print("Running BOTTOM AI model...")
    bottom_result = identify_bottom_pill(BOTTOM_CROPPED_IMAGE)

    print("\n================================")
    print("           AI RESULTS")
    print("================================")

    print_result("TOP", top_result)
    print_result("BOTTOM", bottom_result)

    decision = evaluate_two_cameras(top_result, bottom_result)

    print("\n================================")
    print("         FINAL DECISION")
    print("================================")

    if decision["decision"] == "EMPTY":
        print("\nEMPTY")
        print("Both cameras detected an empty chamber.")

    elif decision["decision"] == "SORT":
        pill_id = decision["pill_id"]
        pill = get_pill_by_id(pill_id)

        print("\nSORT")
        print(f"Pill ID: {pill_id}")
        print(f"Medication: {decision['label']}")
        print(
            f"Average Confidence: "
            f"{decision['confidence'] * 100:.2f}%"
        )

        if pill:
            print(f"Database Match: {pill[1]}")

    else:
        print("\nREJECT")
        print(
            f"Reason: "
            f"{decision.get('reason', 'Unknown reason')}"
        )

    print("\nTest complete.")
    print("Turning imaging lights OFF...")
    lights_off()

    return {
        "top": top_result,
        "bottom": bottom_result,
        "decision": decision,
        "top_image": TOP_CROPPED_IMAGE,
        "bottom_image": BOTTOM_CROPPED_IMAGE,
    }


# ==========================================================
# MAIN
# ==========================================================

def main():
    top_camera = None
    bottom_camera = None

    try:
        print("\n================================")
        print("     RxSort Dual Camera Test")
        print("================================")

        print("\nStarting TOP camera...")
        top_camera = setup_camera(TOP_CAMERA_ID, TOP_FOCUS)

        print("Starting BOTTOM camera...")
        bottom_camera = setup_camera(BOTTOM_CAMERA_ID, BOTTOM_FOCUS)

        print("\nBoth cameras are ready.")

        while True:
            print("\n================================")
            print("Place the pill in the chamber.")
            print("\nPress ENTER to run ONE test.")
            print("Type Q and press ENTER to quit.")

            user_input = input("\n> ").strip().lower()

            if user_input == "q":
                break

            run_test(top_camera, bottom_camera)

            print("\n================================")
            print("Ready for another test.")
            print("Change or reposition the pill if needed.")

    finally:
        print("\nShutting down...")

        try:
            lights_off()
        except Exception as error:
            print(f"Lighting shutdown error: {error}")

        if top_camera is not None:
            try:
                top_camera.stop()
            except Exception:
                pass
            try:
                top_camera.close()
            except Exception:
                pass

        if bottom_camera is not None:
            try:
                bottom_camera.stop()
            except Exception:
                pass
            try:
                bottom_camera.close()
            except Exception:
                pass

        print("Cameras released.")
        print("RxSort dual camera test closed.")


if __name__ == "__main__":
    main()
