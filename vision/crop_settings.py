import cv2

# ==========================================================
# RXSORT CROP SETTINGS
# ==========================================================
#
# Original camera image:
# 1280 x 720
#
# These values can be adjusted while testing.
#
# x = left/right
# y = up/down
# width = crop width
# height = crop height
#
# ==========================================================


# ---------------- TOP CAMERA ----------------

TOP_CROP_X = 390
TOP_CROP_Y = 200

TOP_CROP_WIDTH = 500
TOP_CROP_HEIGHT = 500


# ---------------- BOTTOM CAMERA ----------------

BOTTOM_CROP_X = 340
BOTTOM_CROP_Y = 220

BOTTOM_CROP_WIDTH = 500
BOTTOM_CROP_HEIGHT = 500


# ==========================================================
# CROP FUNCTION
# ==========================================================

def crop_image(image, x, y, width, height):

    image_height, image_width = image.shape[:2]

    # Prevent crop from going outside image
    x = max(0, min(x, image_width - 1))
    y = max(0, min(y, image_height - 1))

    width = min(width, image_width - x)
    height = min(height, image_height - y)

    cropped = image[
        y:y + height,
        x:x + width
    ]

    return cropped


# ==========================================================
# TOP CAMERA CROP
# ==========================================================

def crop_top_image(image):

    print("\nUSING TOP CROP SETTINGS:")
    print("X =", TOP_CROP_X)
    print("Y =", TOP_CROP_Y)
    print("WIDTH =", TOP_CROP_WIDTH)
    print("HEIGHT =", TOP_CROP_HEIGHT)

    return crop_image(
        image,
        TOP_CROP_X,
        TOP_CROP_Y,
        TOP_CROP_WIDTH,
        TOP_CROP_HEIGHT
    )


# ==========================================================
# BOTTOM CAMERA CROP
# ==========================================================

def crop_bottom_image(image):

    return crop_image(
        image,
        BOTTOM_CROP_X,
        BOTTOM_CROP_Y,
        BOTTOM_CROP_WIDTH,
        BOTTOM_CROP_HEIGHT
    )


# ==========================================================
# DRAW CROP BOX FOR PREVIEW
# ==========================================================

def draw_crop_box(
    image,
    x,
    y,
    width,
    height
):

    preview = image.copy()

    cv2.rectangle(
        preview,
        (x, y),
        (x + width, y + height),
        (0, 255, 0),
        3
    )

    return preview
