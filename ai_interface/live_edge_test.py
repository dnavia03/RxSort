from picamera2 import Picamera2, Preview
from libcamera import controls
from time import sleep

from ai_interface.edge_impulse_interface import identify_pill, evaluate_prediction
from database.database_manager import get_pill_by_id

FOCUS_VALUE = 8.00
IMAGE_PATH = "live_pill.jpg"

camera = Picamera2()

config = camera.create_preview_configuration(
    main={"size": (1280, 720)}
)

camera.configure(config)

camera.start()

camera.set_controls({
    "AfMode": controls.AfModeEnum.Manual,
    "LensPosition": FOCUS_VALUE
})

sleep(2)

print("\nRxSort Live AI Test")
print("----------------------------")

try:
    while True:
        input("\nPlace one pill in the chamber and press ENTER...")

        camera.capture_file(IMAGE_PATH)

        print("\nPicture captured.")
        print("Running Edge Impulse identification...")

        result = identify_pill(IMAGE_PATH)
        decision = evaluate_prediction(result)

        print("\nIDENTIFICATION RESULT")
        print("----------------------------")
        print("Medication:", result["label"])
        print("Confidence:", f"{result['confidence'] * 100:.2f}%")
        print("Database Pill ID:", result["pill_id"])

        if result["pill_id"] is not None:
            pill = get_pill_by_id(result["pill_id"])

            print("\nDatabase Match:")
            print(pill)

        print("\nDecision:", decision["decision"])

        if decision["decision"] == "SORT":
            print(
                f"YES - this pill is identified as {result['label']}."
            )
        else:
            print(
                "NO - identification is not confident enough to accept."
            )

        again = input("\nTest another pill? (y/n): ").strip().lower()

        if again != "y":
            break

finally:
    camera.stop()
    camera.close()

    print("\nCamera released.")
