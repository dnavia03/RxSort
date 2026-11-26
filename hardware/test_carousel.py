from gpiozero import OutputDevice
from time import sleep


# ==========================================================
# CAROUSEL MOTOR TEST
# Change these to your actual GPIO pins
# ==========================================================

STEP_PIN = 3
DIR_PIN = 2
ENABLE_PIN = 4

STEPS = 62

# Slower = larger number
STEP_DELAY = 0.002


# ==========================================================
# GPIO SETUP
# ==========================================================

step_pin = OutputDevice(
    STEP_PIN,
    initial_value=False
)

dir_pin = OutputDevice(
    DIR_PIN,
    initial_value=False
)

# DRV8825 ENABLE is active LOW
enable_pin = OutputDevice(
    ENABLE_PIN,
    active_high=False,
    initial_value=False
)


# ==========================================================
# MOTOR MOVEMENT
# ==========================================================

def move_motor(steps, direction):

    dir_pin.value = direction

    sleep(0.02)

    for _ in range(steps):

        step_pin.on()
        sleep(STEP_DELAY)

        step_pin.off()
        sleep(STEP_DELAY)


# ==========================================================
# TEST
# ==========================================================

try:

    print("Enabling carousel motor...")
    enable_pin.on()

    sleep(0.5)

    print("Spinning carousel forward...")

    move_motor(
        STEPS,
        direction=1
    )

    sleep(1)

    print("Spinning carousel backward...")

    move_motor(
        STEPS,
        direction=0
    )

    print("Carousel test complete.")

finally:

    print("Disabling carousel motor...")

    enable_pin.off()

    step_pin.close()
    dir_pin.close()
    enable_pin.close()
