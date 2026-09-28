from pathlib import Path
from picamera2 import Picamera2, Preview
from time import sleep
from database.database_manager import get_pill_by_id
from libcamera import controls


DATASET_PATH = Path("dataset")


def get_next_image_number(folder):
    images = list(folder.glob("image_*.jpg"))

    if not images:
        return 1

    numbers = []

    for image in images:
        number = int(image.stem.split("_")[1])
        numbers.append(number)

    return max(numbers) + 1


def capture_image(camera, folder):
    image_number = get_next_image_number(folder)
    image_path = folder / f"image_{image_number:03d}.jpg"

    print("\nLive preview is ready.")
    input("Position the pill, then press ENTER to focus...")

    print("Focusing...")
    success = camera.autofocus_cycle()

    if success:
        print("Focus locked.")

    else:
        print("Autofocus could not lock")

    camera.capture_file(str(image_path))

    print(f"Picture saved: {image_path}")

print("=== RxSort Image Capture ===")

pill_id = input("Enter the pill ID: ")

pill = get_pill_by_id(pill_id)

if pill:
    print("\nPill found!")
    print("Medication:", pill[1])
    print("Strength:", pill[3])
    print("Color:", pill[5])
    print("Shape:", pill[6])

    pill_folder = DATASET_PATH / f"pill_{int(pill_id):03d}"
    pill_folder.mkdir(parents=True, exist_ok=True)

    top_folder = pill_folder / "top"
    bottom_folder = pill_folder / "bottom"

    top_folder.mkdir(parents=True, exist_ok=True)
    bottom_folder.mkdir(parents=True, exist_ok=True)

    print("\nImage folder ready:")
    print("Top images:", top_folder)
    print("Bottom images:", bottom_folder)

    top_number = get_next_image_number(top_folder)
    bottom_number = get_next_image_number(bottom_folder)

    print("\nNext available image numbers:")
    print(f"Top: image_{top_number:03d}.jpg")
    print(f"Bottom: image_{bottom_number:03d}.jpg")

    camera = Picamera2()

    try:
        camera.start_preview(Preview.QTGL)
        camera.start()

        print("\nCamera starting...")
        sleep(2)

        while True:
            print("\nWhich side are you photographing?")
            print("T = Top")
            print("B = Bottom")
            print("Q = Quit")

            choice = input("Choice: ").strip().lower()

            if choice == "t":
                capture_image(camera, top_folder)

            elif choice == "b":
                capture_image(camera, bottom_folder)

            elif choice == "q":
                break

        else:
            print("Invalid choice. Enter T, B, or Q.")

    finally:
        camera.stop()
        camera.stop_preview()
        camera.close()

        print("\nCamera released.")

else:
    print("\nPill ID not found in database.")
