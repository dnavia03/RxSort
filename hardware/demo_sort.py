import time
import cv2

from picamera2 import Picamera2
from libcamera import controls
from edge_impulse_linux.image import ImageImpulseRunner

from hardware.carousel import (
    initialize_carousel,
    rotate_to_bin,
    shutdown_carousel
)

from hardware.pusher import (
    initialize_pusher,
    push_cycle,
    shutdown_pusher
)

# ==========================================================
# DEMO HARDWARE OPTIONS
# ==========================================================

USE_PUSHER = False

# ==========================================================
# RXSORT DEMO CONFIGURATION
# ==========================================================

TOP_CAMERA_ID = 0
BOTTOM_CAMERA_ID = 1

# ----------------------------------------------------------
# CHANGE THESE TO YOUR EXACT CURRENT MODEL FILENAMES
# ----------------------------------------------------------

TOP_MODEL_PATH = (
    "models/"
    "rxsort-pill-identification-(top)-linux-aarch64-"
    "v14-impulse-#1.eim"
)

BOTTOM_MODEL_PATH = (
    "models/"
    "rxsort-pill-identification-(bottom)-linux-aarch64-"
    "v7-impulse-#1.eim"
)

# ----------------------------------------------------------
# CAMERA FOCUS
# Put your calibrated focus values here.
# Leave as None if you do not want to set manual focus yet.
# ----------------------------------------------------------

TOP_FOCUS = None
BOTTOM_FOCUS = None

TOP_IMAGE = "top_demo.jpg"
BOTTOM_IMAGE = "bottom_demo.jpg"

CONFIDENCE_THRESHOLD = 0.80


# ==========================================================
# EDGE IMPULSE LABEL → DATABASE PILL ID
# IMPORTANT:
# Labels must match your Edge Impulse class names.
# ==========================================================

LABEL_TO_PILL_ID = {

    "Ibuprofen": 3,

    "Simvastatin": 4,

    "Mucinex": 7,

    "Labetalol Hydrochloride": 15,

    "Acetaminophen (Tylenol)": 16,

    "Benadryl Allergy Ultratab Diphenhydramine": 13,

    "Nothing": 18,
}


# ==========================================================
# PILL ID → CAROUSEL BIN
#
# CHANGE THESE HOWEVER YOU WANT FOR THE DEMO.
#
# You have 10 bins available.
# ==========================================================

# ==========================================================
# CAROUSEL BIN MANAGEMENT
# ==========================================================

TOTAL_BINS = 10

# Keeps track of which pill owns which bin.
#
# Example:
# {
#     3: 1,     # Ibuprofen -> Bin 1
#     16: 2     # Tylenol -> Bin 2
# }
pill_bin_assignments = {}


def get_bin_for_pill(pill_id):
    """
    Returns a carousel bin for the identified pill.

    If this medication already has a bin assigned,
    reuse that bin.

    If it is a new medication, assign the first
    available empty bin.

    Different medications are never assigned
    to the same bin.
    """

    # ------------------------------------------------------
    # Pill already has a bin
    # ------------------------------------------------------

    if pill_id in pill_bin_assignments:

        assigned_bin = pill_bin_assignments[pill_id]

        print(
            f"Pill ID {pill_id} already assigned "
            f"to Bin {assigned_bin}."
        )

        return assigned_bin

    # ------------------------------------------------------
    # Find bins already occupied
    # ------------------------------------------------------

    occupied_bins = set(
        pill_bin_assignments.values()
    )

    # ------------------------------------------------------
    # Find first empty bin
    # ------------------------------------------------------

    for bin_number in range(
        1,
        TOTAL_BINS + 1
    ):

        if bin_number not in occupied_bins:

            pill_bin_assignments[
                pill_id
            ] = bin_number

            print(
                f"New medication detected."
            )

            print(
                f"Pill ID {pill_id} assigned "
                f"to empty Bin {bin_number}."
            )

            return bin_number

    # ------------------------------------------------------
    # No bins available
    # ------------------------------------------------------

    return None


# ==========================================================
# CAMERA SETUP
# ==========================================================

def setup_camera(camera_id, focus_value=None):

    camera = Picamera2(camera_num=camera_id)

    config = camera.create_still_configuration(
        main={
            "size": (1280, 720)
        }
    )

    camera.configure(config)

    camera.start()

    time.sleep(1)

    if focus_value is not None:

        camera.set_controls({
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": focus_value
        })

        time.sleep(0.5)

    return camera


# ==========================================================
# CAPTURE IMAGE
# ==========================================================

def capture_images(top_camera, bottom_camera):

    print("\nCapturing TOP image...")

    top_camera.capture_file(
        TOP_IMAGE
    )

    time.sleep(0.2)

    print("Capturing BOTTOM image...")

    bottom_camera.capture_file(
        BOTTOM_IMAGE
    )

    print("Images captured.")


# ==========================================================
# RUN EDGE IMPULSE MODEL
# ==========================================================

def classify_image(
    runner,
    image_path
):

    image = cv2.imread(
        image_path
    )

    if image is None:

        raise ValueError(
            f"Could not open image: {image_path}"
        )

    # OpenCV loads BGR.
    # Convert to RGB for the model.
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    features, cropped = (
        runner.get_features_from_image(
            image
        )
    )

    result = runner.classify(
        features
    )

    predictions = (
        result["result"]["classification"]
    )

    # Clean labels just in case Edge Impulse
    # contains accidental spaces.
    cleaned_predictions = {}

    for label, confidence in predictions.items():

        cleaned_label = label.strip()

        cleaned_predictions[
            cleaned_label
        ] = confidence

    best_label = max(
        cleaned_predictions,
        key=cleaned_predictions.get
    )

    confidence = (
        cleaned_predictions[
            best_label
        ]
    )

    pill_id = (
        LABEL_TO_PILL_ID.get(
            best_label
        )
    )

    return {
        "label": best_label,
        "pill_id": pill_id,
        "confidence": confidence,
        "all_predictions": cleaned_predictions
    }


# ==========================================================
# PRINT AI RESULTS
# ==========================================================

def print_prediction(
    camera_name,
    result
):

    print(
        f"\n{camera_name} CAMERA"
    )

    print(
        "-------------------------"
    )

    print(
        f"Prediction: "
        f"{result['label']}"
    )

    print(
        f"Confidence: "
        f"{result['confidence'] * 100:.1f}%"
    )

    print(
        f"Pill ID: "
        f"{result['pill_id']}"
    )


# ==========================================================
# TOP + BOTTOM AGREEMENT LOGIC
# ==========================================================

def make_sorting_decision(
    top_result,
    bottom_result
):

    top_id = (
        top_result["pill_id"]
    )

    bottom_id = (
        bottom_result["pill_id"]
    )

    top_confidence = (
        top_result["confidence"]
    )

    bottom_confidence = (
        bottom_result["confidence"]
    )

    # ------------------------------------------------------
    # UNKNOWN LABEL
    # ------------------------------------------------------

    if (
        top_id is None
        or bottom_id is None
    ):

        return {
            "decision": "REJECT",
            "reason": (
                "Medication is not mapped "
                "to the RxSort database."
            )
        }

    # ------------------------------------------------------
    # BOTH CAMERAS SEE NOTHING
    # ------------------------------------------------------

    if (
        top_id == 18
        and bottom_id == 18
    ):

        return {
            "decision": "EMPTY",
            "reason": "No pill detected."
        }

    # ------------------------------------------------------
    # ONE CAMERA SEES NOTHING
    # ------------------------------------------------------

    if (
        top_id == 18
        or bottom_id == 18
    ):

        return {
            "decision": "REJECT",
            "reason": (
                "One camera detected a pill "
                "while the other detected Nothing."
            )
        }

    # ------------------------------------------------------
    # CAMERAS DISAGREE
    # ------------------------------------------------------

    if top_id != bottom_id:

        return {
            "decision": "REJECT",
            "reason": (
                "Top and bottom AI models "
                "identified different pills."
            )
        }

    # ------------------------------------------------------
    # CONFIDENCE TOO LOW
    # ------------------------------------------------------

    if (
        top_confidence
        < CONFIDENCE_THRESHOLD
        or
        bottom_confidence
        < CONFIDENCE_THRESHOLD
    ):

        return {
            "decision": "REJECT",
            "reason": (
                "AI confidence is below "
                "the required threshold."
            )
        }

    # ------------------------------------------------------
    # BOTH CAMERAS AGREE
    # ------------------------------------------------------

    average_confidence = (
        top_confidence
        + bottom_confidence
    ) / 2

    return {
        "decision": "SORT",
        "pill_id": top_id,
        "label": top_result["label"],
        "confidence": average_confidence
    }


# ==========================================================
# PHYSICAL SORTING
# ==========================================================

def physically_sort_pill(decision):

    pill_id = decision["pill_id"]
    label = decision["label"]

    # Get an existing bin for this pill,
    # or assign the first empty bin.
    bin_number = 3

    if bin_number is None:

        print(
            "\nERROR: All 10 carousel bins are assigned."
        )

        print(
            "Pill will not be sorted."
        )

        return

    print(
        "\n================================"
    )

    print(
        "       PHYSICAL SORT"
    )

    print(
        "================================"
    )

    print(
        f"Medication: {label}"
    )

    print(
        f"Pill ID: {pill_id}"
    )

    print(
        f"Destination: Bin {bin_number}"
    )

    # ------------------------------------------------------
    # ROTATE CAROUSEL
    # ------------------------------------------------------

    print(
        "\nRotating carousel..."
    )

    rotate_to_bin(
        bin_number
    )

    time.sleep(0.5)

    print(
        "Carousel positioned."
    )

    # ------------------------------------------------------
    # PUSHER
    # ------------------------------------------------------

    if USE_PUSHER:

        print(
            "Activating pusher..."
        )

        time.sleep(0.5)

        push_cycle()

        print(
            f"\n{label} successfully "
            f"sorted into Bin {bin_number}."
        )

    else:

        print(
            "\nPusher disabled."
        )

        print(
            f"Manually push {label} "
            f"into Bin {bin_number}."
        )

    # ------------------------------------------------------
    # DEBUGGING
    # ------------------------------------------------------

    print(
        "\nCurrent bin assignments:"
    )

    for assigned_pill, assigned_bin in pill_bin_assignments.items():

        print(
            f"Pill ID {assigned_pill} "
            f"-> Bin {assigned_bin}"
        )

# ==========================================================
# MAIN PROGRAM
# ==========================================================


def main():

    print(
        "\n================================"
    )

    print(
        "       RXSORT DEMO MODE"
    )

    print(
        "================================"
    )

    # ------------------------------------------------------
# HARDWARE INITIALIZATION
# ------------------------------------------------------


print("\nInitializing carousel...")

carousel_ready = initialize_carousel()

# Pusher is optional for this demo
if USE_PUSHER:

    print("Initializing pusher...")

    pusher_ready = initialize_pusher()

else:

    print("Pusher disabled for demo.")

    # Treat pusher as ready so it does not block the demo
    pusher_ready = True


# Make sure required hardware initialized
if not carousel_ready or not pusher_ready:

    print(
        "\nERROR: Hardware initialization failed."
    )

    raise SystemExit

    # ------------------------------------------------------
    # CAMERA INITIALIZATION
    # ------------------------------------------------------

print(
    "\nStarting cameras..."
)

top_camera = setup_camera(
    TOP_CAMERA_ID,
    TOP_FOCUS
)

bottom_camera = setup_camera(
    BOTTOM_CAMERA_ID,
    BOTTOM_FOCUS
)

# ------------------------------------------------------
# AI MODEL INITIALIZATION
# ------------------------------------------------------

print(
    "\nLoading AI models..."
)

top_runner = ImageImpulseRunner(
    TOP_MODEL_PATH
)

bottom_runner = ImageImpulseRunner(
    BOTTOM_MODEL_PATH
)

top_runner.init()
bottom_runner.init()

print(
    "\nRxSort ready."
)

try:

    while True:

        print(
            "\n================================"
        )

        print(
            "Place ONE pill "
            "inside the imaging chamber."
        )

        print(
            "Press ENTER to scan."
        )

        print(
            "Enter Q to quit."
        )

        command = input(
            "\n> "
        ).strip().lower()

        if command == "q":
            break

        # ------------------------------------------------
        # CAPTURE
        # ------------------------------------------------

        capture_images(
            top_camera,
            bottom_camera
        )

        # ------------------------------------------------
        # TOP MODEL
        # ------------------------------------------------

        print(
            "\nRunning TOP AI model..."
        )

        top_result = (
            classify_image(
                top_runner,
                TOP_IMAGE
            )
        )

        # ------------------------------------------------
        # BOTTOM MODEL
        # ------------------------------------------------

        print(
            "Running BOTTOM AI model..."
        )

        bottom_result = (
            classify_image(
                bottom_runner,
                BOTTOM_IMAGE
            )
        )

        # ------------------------------------------------
        # PRINT RESULTS
        # ------------------------------------------------

        print_prediction(
            "TOP",
            top_result
        )

        print_prediction(
            "BOTTOM",
            bottom_result
        )

        # ------------------------------------------------
        # MAKE FINAL DECISION
        # ------------------------------------------------

        decision = (
            make_sorting_decision(
                top_result,
                bottom_result
            )
        )

        print(
            "\n================================"
        )

        print(
            f"DECISION: "
            f"{decision['decision']}"
        )

        print(
            "================================"
        )

        # ------------------------------------------------
        # SORT
        # ------------------------------------------------

        if (
            decision["decision"]
            == "SORT"
        ):

            print(
                f"\nMedication identified:"
                f" {decision['label']}"
            )

            print(
                f"Average confidence:"
                f" "
                f"{decision['confidence'] * 100:.1f}%"
            )

            physically_sort_pill(
                decision
            )

        # ------------------------------------------------
        # REJECT
        # ------------------------------------------------

        elif (
            decision["decision"]
            == "REJECT"
        ):

            print(
                "\nPill rejected."
            )

            print(
                f"Reason:"
                f" {decision['reason']}"
            )

            print(
                "Pusher will NOT activate."
            )

        # ------------------------------------------------
        # EMPTY
        # ------------------------------------------------

        elif (
            decision["decision"]
            == "EMPTY"
        ):

            print(
                "\nNo pill detected."
            )

            print(
                "Waiting for a pill."
            )

except KeyboardInterrupt:

    print(
        "\nRxSort demo stopped."
    )

finally:

    # ----------------------------------------------------
    # CLEAN SHUTDOWN
    # ----------------------------------------------------

    print(
        "\nShutting down RxSort..."
    )

    try:
        top_runner.stop()
    except Exception:
        pass

    try:
        bottom_runner.stop()
    except Exception:
        pass

    try:
        top_camera.stop()
        top_camera.close()
    except Exception:
        pass

    try:
        bottom_camera.stop()
        bottom_camera.close()
    except Exception:
        pass

    if USE_PUSHER:
        try:
            shutdown_pusher()
        except Exception:
            pass
    try:
        shutdown_carousel()
    except Exception:
        pass

    print(
        "RxSort shut down successfully."
    )


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()
