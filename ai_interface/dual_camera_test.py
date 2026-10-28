from picamera2 import Picamera2
from libcamera import controls
from time import sleep

from ai_interface.edge_impulse_interface import identify_top_pill, identify_bottom_pill
from database.database_manager import get_pill_by_id

TOP_CAMERA_ID = 0
BOTTOM_CAMERA_ID = 1

TOP_FOCUS = 8.00
BOTTOM_FOCUS = 9.00

TOP_IMAGE = "top_live.jpg"
BOTTOM_IMAGE = "bottom_live.jpg"

CONFIDENCE_THRESHOLD = 0.80


def print_result(title, result):
    print(f"\n{title}")
    print("----------------------------")
    print("Medication:", result["label"])
    print("Confidence:", f"{result['confidence'] * 100:.2f}%")
    print("Database Pill ID:", result["pill_id"])


def evaluate_two_cameras(top_result, bottom_result):
    top_id = top_result["pill_id"]
    bottom_id = bottom_result["pill_id"]

    top_confidence = top_result["confidence"]
    bottom_confidence = bottom_result["confidence"]

    if top_id is None or bottom_id is None:
        return {
            "decision": "REJECT",
            "reason": "Medication is not mapped to the database"
        }

    if top_id != bottom_id:
        return {
            "decision": "REJECT",
            "reason": "Top and bottom cameras disagree"
        }

    if top_confidence < CONFIDENCE_THRESHOLD:
        return {
            "decision": "REJECT",
            "reason": "Top camera confidence is too low"
        }

    if bottom_confidence < CONFIDENCE_THRESHOLD:
        return {
            "decision": "REJECT",
            "reason": "Bottom camera confidence is too low"
        }

    average_confidence = (top_confidence + bottom_confidence) / 2

    return {
        "decision": "SORT",
        "pill_id": top_id,
        "label": top_result["label"],
        "confidence": average_confidence
    }


top_camera = Picamera2(camera_num=TOP_CAMERA_ID)
bottom_camera = Picamera2(camera_num=BOTTOM_CAMERA_ID)

top_config = top_camera.create_still_configuration(
    main={"size": (1280, 720)}
)

bottom_config = bottom_camera.create_still_configuration(
    main={"size": (1280, 720)}
)

top_camera.configure(top_config)
bottom_camera.configure(bottom_config)

top_camera.start()
bottom_camera.start()

top_camera.set_controls({
    "AfMode": controls.AfModeEnum.Manual,
    "LensPosition": TOP_FOCUS
})

bottom_camera.set_controls({
    "AfMode": controls.AfModeEnum.Manual,
    "LensPosition": BOTTOM_FOCUS
})

sleep(2)

print("\nRxSort Dual Camera Identification")
print("--------------------------------")

try:
    while True:
        input("\nPlace one pill in the chamber and press ENTER...")

        print("\nCapturing top image...")
        top_camera.capture_file(TOP_IMAGE)

        sleep(0.5)

        print("Capturing bottom image...")
        bottom_camera.capture_file(BOTTOM_IMAGE)

        print("\nRunning Edge Impulse model...")

        top_result = identify_top_pill(TOP_IMAGE)
        bottom_result = identify_bottom_pill(BOTTOM_IMAGE)

        print_result("TOP CAMERA", top_result)
        print_result("BOTTOM CAMERA", bottom_result)

        final_result = evaluate_two_cameras(
            top_result,
            bottom_result
        )

        print("\nFINAL RESULT")
        print("----------------------------")
        print("Decision:", final_result["decision"])

        if final_result["decision"] == "SORT":
            print("Medication:", final_result["label"])
            print(
                "Combined Confidence:",
                f"{final_result['confidence'] * 100:.2f}%"
            )

            pill = get_pill_by_id(final_result["pill_id"])

            print("Database Match:", pill)

            print(
                f"\nYES - Both cameras identify this pill as "
                f"{final_result['label']}."
            )

        else:
            print("Reason:", final_result["reason"])

        again = input("\nTest another pill? (y/n): ").strip().lower()

        if again != "y":
            break

finally:
    top_camera.stop()
    bottom_camera.stop()

    top_camera.close()
    bottom_camera.close()

    print("\nCameras released.")
