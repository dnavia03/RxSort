import vision.crop_settings as crop_settings
from hardware.lighting import lights_on, lights_off
from database.database_manager import get_pill_by_id
from libcamera import controls
from picamera2 import Picamera2, Preview
import os
from pathlib import Path
from time import sleep

import cv2

# Prevent OpenCV Qt settings from interfering with Picamera2 preview
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
os.environ.pop("QT_QPA_FONTDIR", None)


# ==========================================================
# RXSORT DATASET CONFIGURATION
# ==========================================================

DATASET_PATH = Path("dataset")

TOP_CAMERA_ID = 1
BOTTOM_CAMERA_ID = 0

TOP_FOCUS = 8.00
BOTTOM_FOCUS = 9.00

IMAGE_SIZE = (1280, 720)


# ==========================================================
# GET NEXT IMAGE NUMBER
# ==========================================================

def get_next_image_number(folder):

    images = list(
        folder.glob("image_*.jpg")
    )

    if not images:
        return 1

    numbers = []

    for image in images:

        try:
            number = int(
                image.stem.split("_")[1]
            )

            numbers.append(number)

        except (IndexError, ValueError):
            pass

    if not numbers:
        return 1

    return max(numbers) + 1


# ==========================================================
# MANUAL CROP FUNCTION
# ==========================================================

def crop_image(
    image,
    x,
    y,
    width,
    height
):

    image_height, image_width = image.shape[:2]

    x = max(
        0,
        min(x, image_width - 1)
    )

    y = max(
        0,
        min(y, image_height - 1)
    )

    width = min(
        width,
        image_width - x
    )

    height = min(
        height,
        image_height - y
    )

    return image[
        y:y + height,
        x:x + width
    ]


# ==========================================================
# CAPTURE MATCHED IMAGE PAIR
# ==========================================================

def capture_image_pair(
    top_camera,
    bottom_camera,
    top_folder,
    bottom_folder
):

    top_number = get_next_image_number(
        top_folder
    )

    bottom_number = get_next_image_number(
        bottom_folder
    )

    image_number = max(
        top_number,
        bottom_number
    )

    top_image_path = (
        top_folder
        / f"image_{image_number:03d}.jpg"
    )

    bottom_image_path = (
        bottom_folder
        / f"image_{image_number:03d}.jpg"
    )

    # Temporary FULL camera captures
    temp_top_path = Path(
        "temp_top_full.jpg"
    )

    temp_bottom_path = Path(
        "temp_bottom_full.jpg"
    )

    print(
        "\nPosition or rotate the pill."
    )

    input(
        "Press ENTER when ready to capture both images..."
    )

    # ======================================================
    # CAPTURE FULL IMAGES
    # ======================================================

    print(
        "\nCapturing full TOP image..."
    )

    top_camera.capture_file(
        str(temp_top_path)
    )

    sleep(0.2)

    print(
        "Capturing full BOTTOM image..."
    )

    bottom_camera.capture_file(
        str(temp_bottom_path)
    )

    # ======================================================
    # LOAD FULL IMAGES
    # ======================================================

    top_image = cv2.imread(
        str(temp_top_path)
    )

    bottom_image = cv2.imread(
        str(temp_bottom_path)
    )

    if top_image is None:

        print(
            "ERROR: Could not load top image."
        )

        return

    if bottom_image is None:

        print(
            "ERROR: Could not load bottom image."
        )

        return

    print(
        "\nOriginal TOP size:",
        top_image.shape[1],
        "x",
        top_image.shape[0]
    )

    print(
        "Original BOTTOM size:",
        bottom_image.shape[1],
        "x",
        bottom_image.shape[0]
    )

    # ======================================================
    # SHOW CURRENT CROP SETTINGS
    # ======================================================

    print(
        "\nTOP CROP SETTINGS:"
    )

    print(
        "X =",
        crop_settings.TOP_CROP_X
    )

    print(
        "Y =",
        crop_settings.TOP_CROP_Y
    )

    print(
        "WIDTH =",
        crop_settings.TOP_CROP_WIDTH
    )

    print(
        "HEIGHT =",
        crop_settings.TOP_CROP_HEIGHT
    )

    print(
        "\nBOTTOM CROP SETTINGS:"
    )

    print(
        "X =",
        crop_settings.BOTTOM_CROP_X
    )

    print(
        "Y =",
        crop_settings.BOTTOM_CROP_Y
    )

    print(
        "WIDTH =",
        crop_settings.BOTTOM_CROP_WIDTH
    )

    print(
        "HEIGHT =",
        crop_settings.BOTTOM_CROP_HEIGHT
    )

    # ======================================================
    # CROP TOP IMAGE
    # ======================================================

    top_cropped = crop_image(
        top_image,

        crop_settings.TOP_CROP_X,
        crop_settings.TOP_CROP_Y,

        crop_settings.TOP_CROP_WIDTH,
        crop_settings.TOP_CROP_HEIGHT
    )

    # ======================================================
    # CROP BOTTOM IMAGE
    # ======================================================

    bottom_cropped = crop_image(
        bottom_image,

        crop_settings.BOTTOM_CROP_X,
        crop_settings.BOTTOM_CROP_Y,

        crop_settings.BOTTOM_CROP_WIDTH,
        crop_settings.BOTTOM_CROP_HEIGHT
    )

    # ======================================================
    # VERIFY CROPPED SIZE
    # ======================================================

    print(
        "\nCropped TOP size:",
        top_cropped.shape[1],
        "x",
        top_cropped.shape[0]
    )

    print(
        "Cropped BOTTOM size:",
        bottom_cropped.shape[1],
        "x",
        bottom_cropped.shape[0]
    )

    # ======================================================
    # SAVE CROPPED IMAGES
    # ======================================================

    top_success = cv2.imwrite(
        str(top_image_path),
        top_cropped
    )

    bottom_success = cv2.imwrite(
        str(bottom_image_path),
        bottom_cropped
    )

    if not top_success:

        print(
            "ERROR: Top cropped image failed to save."
        )

        return

    if not bottom_success:

        print(
            "ERROR: Bottom cropped image failed to save."
        )

        return

    print(
        "\nCROPPED IMAGE PAIR SAVED"
    )

    print(
        f"TOP:    {top_image_path}"
    )

    print(
        f"BOTTOM: {bottom_image_path}"
    )

    # ======================================================
    # REMOVE TEMP FULL IMAGES
    # ======================================================

    try:
        temp_top_path.unlink()
    except Exception:
        pass

    try:
        temp_bottom_path.unlink()
    except Exception:
        pass


# ==========================================================
# CAMERA SETUP
# ==========================================================

def setup_camera(
    camera_id,
    focus_value
):

    camera = Picamera2(
        camera_num=camera_id
    )

    config = (
        camera.create_preview_configuration(
            main={
                "size": IMAGE_SIZE
            }
        )
    )

    camera.configure(
        config
    )

    camera.start_preview(
        Preview.QTGL
    )

    camera.start()

    sleep(0.5)

    camera.set_controls({

        "AfMode":
            controls.AfModeEnum.Manual,

        "LensPosition":
            focus_value

    })

    sleep(0.5)

    return camera


# ==========================================================
# MAIN
# ==========================================================

def main():

    print(
        "\n================================"
    )

    print(
        "       RxSort Image Capture"
    )

    print(
        "================================"
    )

    # ======================================================
    # PILL ID
    # ======================================================

    pill_id = input(
        "\nEnter the pill ID: "
    ).strip()

    try:

        pill_id_number = int(
            pill_id
        )

    except ValueError:

        print(
            "Invalid pill ID."
        )

        return

    pill = get_pill_by_id(
        pill_id_number
    )

    if not pill:

        print(
            "Pill ID not found in database."
        )

        return

    print(
        "\nMedication:",
        pill[1]
    )

    # ======================================================
    # DATASET FOLDERS
    # ======================================================

    pill_folder = (
        DATASET_PATH
        / f"pill_{pill_id_number:03d}"
    )

    top_folder = (
        pill_folder
        / "top"
    )

    bottom_folder = (
        pill_folder
        / "bottom"
    )

    top_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    bottom_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    print(
        "\nTop:",
        top_folder
    )

    print(
        "Bottom:",
        bottom_folder
    )

    top_camera = None
    bottom_camera = None

    try:

        # ==================================================
        # LIGHTS
        # ==================================================

        print(
            "\nTurning imaging lights ON..."
        )

        lights_on()

        sleep(1)

        # ==================================================
        # CAMERAS
        # ==================================================

        print(
            "\nStarting TOP camera..."
        )

        top_camera = setup_camera(
            TOP_CAMERA_ID,
            TOP_FOCUS
        )

        print(
            "Starting BOTTOM camera..."
        )

        bottom_camera = setup_camera(
            BOTTOM_CAMERA_ID,
            BOTTOM_FOCUS
        )

        print(
            "\nBoth cameras ready."
        )

        sleep(2)

        # ==================================================
        # CAPTURE LOOP
        # ==================================================

        while True:

            next_number = max(

                get_next_image_number(
                    top_folder
                ),

                get_next_image_number(
                    bottom_folder
                )

            )

            print(
                "\n================================"
            )

            print(
                f"Next image pair: "
                f"image_{next_number:03d}.jpg"
            )

            print(
                "\nC = Capture"
            )

            print(
                "Q = Quit"
            )

            choice = input(
                "\nChoice: "
            ).strip().lower()

            if choice == "c":

                capture_image_pair(
                    top_camera,
                    bottom_camera,
                    top_folder,
                    bottom_folder
                )

            elif choice == "q":

                break

            else:

                print(
                    "Enter C or Q."
                )

    finally:

        print(
            "\nShutting down..."
        )

        try:

            lights_off()

        except Exception:

            pass

        if top_camera is not None:

            try:
                top_camera.stop()
            except Exception:
                pass

            try:
                top_camera.stop_preview()
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
                bottom_camera.stop_preview()
            except Exception:
                pass

            try:
                bottom_camera.close()
            except Exception:
                pass

        print(
            "Capture session complete."
        )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()
