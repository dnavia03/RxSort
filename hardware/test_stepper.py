from gpiozero import OutputDevice
from time import sleep


# ==========================================================
# CONFIGURATION
# Change these pins to match wiring
# ==========================================================

STEP_PIN = 19
DIR_PIN = 26
ENABLE_PIN = 13

# Test movement
STEPS = 400

# Speed settings
START_DELAY = 0.004     # Slow starting speed
RUN_DELAY = 0.001       # Faster normal speed

# Number of steps used to accelerate/decelerate
RAMP_STEPS = 75

# DRV8825 ENABLE is active LOW
step_pin = OutputDevice(STEP_PIN, initial_value=False)
dir_pin = OutputDevice(DIR_PIN, initial_value=False)

enable_pin = OutputDevice(
    ENABLE_PIN,
    active_high=False,
    initial_value=False
)


def enable_motor():
    enable_pin.on()


def disable_motor():
    enable_pin.off()


def step_motor(steps, direction):
    """
    Move the stepper motor with acceleration and deceleration.
    """

    dir_pin.value = direction

    # Small delay so DIR settles before STEP pulses begin
    sleep(0.01)

    for step_number in range(steps):

        # ---------------- ACCELERATION ----------------
        if step_number < RAMP_STEPS:

            progress = step_number / RAMP_STEPS

            delay = START_DELAY - (
                (START_DELAY - RUN_DELAY) * progress
            )

        # ---------------- DECELERATION ----------------
        elif step_number > steps - RAMP_STEPS:

            remaining = steps - step_number

            progress = remaining / RAMP_STEPS

            delay = START_DELAY - (
                (START_DELAY - RUN_DELAY) * progress
            )

        # ---------------- NORMAL SPEED ----------------
        else:
            delay = RUN_DELAY

        step_pin.on()
        sleep(delay)

        step_pin.off()
        sleep(delay)


try:

    print("Enabling motor...")
    enable_motor()

    sleep(0.5)

    print("Rotating forward...")

    step_motor(
        STEPS,
        direction=1
    )

    sleep(1)

    print("Rotating backward...")

    step_motor(
        STEPS,
        direction=0
    )

    sleep(0.5)

    print("Test complete.")


finally:

    print("Disabling motor...")

    disable_motor()

    step_pin.close()
    dir_pin.close()
    enable_pin.close()
