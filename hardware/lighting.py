import board
import neopixel


# ==========================================================
# RXSORT LIGHTING CONFIGURATION
# ==========================================================

LED_PIN = board.D14

TOP_LED_COUNT = 24
BOTTOM_LED_COUNT = 24

LED_COUNT = TOP_LED_COUNT + BOTTOM_LED_COUNT


# ==========================================================
# COLOR
# ==========================================================

# Warm white / warm amber-ish scan color
SCAN_COLOR = (255, 225, 140)

OFF_COLOR = (0, 0, 0)


# ==========================================================
# SEPARATE BRIGHTNESS LEVELS
# ==========================================================

# Top already looks good
TOP_BRIGHTNESS = 0.25

# Bottom is brighter
BOTTOM_BRIGHTNESS = 0.50


# ==========================================================
# INITIALIZE 48-LED DAISY CHAIN
# ==========================================================

pixels = neopixel.NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=1.0,
    auto_write=False
)


# ==========================================================
# SCALE RGB COLOR BY BRIGHTNESS
# ==========================================================

def scale_color(color, brightness):

    red = int(color[0] * brightness)
    green = int(color[1] * brightness)
    blue = int(color[2] * brightness)

    return (
        red,
        green,
        blue
    )


# ==========================================================
# TURN BOTH LIGHTS ON
# ==========================================================

def lights_on():

    top_color = scale_color(
        SCAN_COLOR,
        TOP_BRIGHTNESS
    )

    bottom_color = scale_color(
        SCAN_COLOR,
        BOTTOM_BRIGHTNESS
    )

    # ------------------------------------------------------
    # TOP RING
    # LEDs 0 through 23
    # ------------------------------------------------------

    for i in range(
        0,
        TOP_LED_COUNT
    ):

        pixels[i] = top_color

    # ------------------------------------------------------
    # BOTTOM RING
    # LEDs 24 through 47
    # ------------------------------------------------------

    for i in range(
        TOP_LED_COUNT,
        LED_COUNT
    ):

        pixels[i] = bottom_color

    pixels.show()

    print(
        "Top and bottom imaging lights ON."
    )


# ==========================================================
# TURN BOTH LIGHTS OFF
# ==========================================================

def lights_off():

    pixels.fill(
        OFF_COLOR
    )

    pixels.show()

    print(
        "Top and bottom imaging lights OFF."
    )


# ==========================================================
# TOP LIGHT ONLY
# ==========================================================

def top_light_on():

    top_color = scale_color(
        SCAN_COLOR,
        TOP_BRIGHTNESS
    )

    for i in range(
        0,
        TOP_LED_COUNT
    ):

        pixels[i] = top_color

    pixels.show()

    print(
        "Top imaging light ON."
    )


def top_light_off():

    for i in range(
        0,
        TOP_LED_COUNT
    ):

        pixels[i] = OFF_COLOR

    pixels.show()

    print(
        "Top imaging light OFF."
    )


# ==========================================================
# BOTTOM LIGHT ONLY
# ==========================================================

def bottom_light_on():

    bottom_color = scale_color(
        SCAN_COLOR,
        BOTTOM_BRIGHTNESS
    )

    for i in range(
        TOP_LED_COUNT,
        LED_COUNT
    ):

        pixels[i] = bottom_color

    pixels.show()

    print(
        "Bottom imaging light ON."
    )


def bottom_light_off():

    for i in range(
        TOP_LED_COUNT,
        LED_COUNT
    ):

        pixels[i] = OFF_COLOR

    pixels.show()

    print(
        "Bottom imaging light OFF."
    )


# ==========================================================
# CHANGE COLOR FOR BOTH RINGS
# ==========================================================

def set_color(red, green, blue):

    global SCAN_COLOR

    SCAN_COLOR = (
        red,
        green,
        blue
    )

    lights_on()

    print(
        f"Scan color set to "
        f"RGB({red}, {green}, {blue})."
    )


# ==========================================================
# CHANGE TOP BRIGHTNESS
# ==========================================================

def set_top_brightness(value):

    global TOP_BRIGHTNESS

    if value < 0.0:
        value = 0.0

    if value > 1.0:
        value = 1.0

    TOP_BRIGHTNESS = value

    lights_on()

    print(
        f"Top brightness set to {value}."
    )


# ==========================================================
# CHANGE BOTTOM BRIGHTNESS
# ==========================================================

def set_bottom_brightness(value):

    global BOTTOM_BRIGHTNESS

    if value < 0.0:
        value = 0.0

    if value > 1.0:
        value = 1.0

    BOTTOM_BRIGHTNESS = value

    lights_on()

    print(
        f"Bottom brightness set to {value}."
    )


# ==========================================================
# TEST MODE
# ==========================================================

if __name__ == "__main__":

    print(
        "\nRxSort Lighting Test"
    )

    print(
        "--------------------"
    )

    print(
        f"Top brightness: "
        f"{TOP_BRIGHTNESS}"
    )

    print(
        f"Bottom brightness: "
        f"{BOTTOM_BRIGHTNESS}"
    )

    print(
        f"Scan color: "
        f"{SCAN_COLOR}"
    )

    lights_on()

    input(
        "\nBoth lights should now be ON. "
        "Press ENTER to turn them OFF..."
    )

    lights_off()

    print(
        "\nLighting test complete."
    )
