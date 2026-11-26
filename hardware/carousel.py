from gpiozero import OutputDevice
from time import sleep


# ==========================================================
# RXSORT CAROUSEL CONFIGURATION
# ==========================================================

STEP_PIN = 3
DIR_PIN = 2
ENABLE_PIN = 4

TOTAL_BINS = 10

# Measured during testingq
STEPS_PER_BIN = 152

# Working motor speed from test_carousel.py
STEP_DELAY = 0.004

CLOCKWISE_DIRECTION = 1
COUNTERCLOCKWISE_DIRECTION = 0

# Assume bin 1 is aligned at startup for now
HOME_BIN = 1


# ==========================================================
# CURRENT STATE
# ==========================================================

current_bin = HOME_BIN

step_output = None
dir_output = None
enable_output = None


# ==========================================================
# INITIALIZATION
# ==========================================================

def initialize_carousel():

    global step_output
    global dir_output
    global enable_output

    step_output = OutputDevice(
        STEP_PIN,
        initial_value=False
    )

    dir_output = OutputDevice(
        DIR_PIN,
        initial_value=False
    )

    enable_output = OutputDevice(
        ENABLE_PIN,
        active_high=False,
        initial_value=False
    )

    print("Carousel initialized successfully.")

    return True


# ==========================================================
# MOTOR ENABLE / DISABLE
# ==========================================================

def enable_motor():
    enable_output.on()


def disable_motor():
    enable_output.off()


# ==========================================================
# LOW LEVEL MOVEMENT
# ==========================================================

def move_steps(steps, direction):

    dir_output.value = direction

    sleep(0.02)

    for _ in range(steps):

        step_output.on()
        sleep(STEP_DELAY)

        step_output.off()
        sleep(STEP_DELAY)


# ==========================================================
# BIN MOVEMENT CALCULATION
# ==========================================================

def calculate_bin_movement(target_bin):

    global current_bin

    if target_bin < 1 or target_bin > TOTAL_BINS:
        raise ValueError(
            f"Bin must be between 1 and {TOTAL_BINS}"
        )

    clockwise_distance = (
        target_bin - current_bin
    ) % TOTAL_BINS

    counterclockwise_distance = (
        current_bin - target_bin
    ) % TOTAL_BINS

    if clockwise_distance <= counterclockwise_distance:

        return (
            CLOCKWISE_DIRECTION,
            clockwise_distance
        )

    else:

        return (
            COUNTERCLOCKWISE_DIRECTION,
            counterclockwise_distance
        )


# ==========================================================
# MAIN CAROUSEL FUNCTION
# ==========================================================

def rotate_to_bin(target_bin):

    global current_bin

    if step_output is None:
        raise RuntimeError(
            "Carousel has not been initialized."
        )

    direction, bins_to_move = calculate_bin_movement(
        target_bin
    )

    if bins_to_move == 0:

        print(
            f"Carousel already at bin {target_bin}."
        )

        return

    total_steps = bins_to_move * STEPS_PER_BIN

    print(
        f"\nMoving carousel:"
        f"\nCurrent bin: {current_bin}"
        f"\nTarget bin: {target_bin}"
        f"\nBins to move: {bins_to_move}"
        f"\nMotor steps: {total_steps}"
    )

    enable_motor()

    move_steps(
        total_steps,
        direction
    )

    disable_motor()

    current_bin = target_bin

    print(
        f"Carousel now positioned at bin {current_bin}."
    )


# ==========================================================
# HOME FUNCTION
# ==========================================================

def home_carousel():

    global current_bin

    # For now, physically place carousel at bin 1
    # before starting the program.

    current_bin = HOME_BIN

    print(
        f"Carousel position set to home bin {HOME_BIN}."
    )


# ==========================================================
# SHUTDOWN
# ==========================================================

def shutdown_carousel():

    if enable_output is not None:
        disable_motor()
        enable_output.close()

    if step_output is not None:
        step_output.close()

    if dir_output is not None:
        dir_output.close()

    print("Carousel shut down.")


# ==========================================================
# TEST MODE
# ==========================================================

if __name__ == "__main__":

    initialize_carousel()

    try:

        print("\nRxSort Carousel Test")

        while True:

            print(
                "\nEnter a bin number from 1-10"
            )

            print(
                "Enter Q to quit"
            )

            choice = input(
                "\nTarget bin: "
            ).strip().lower()

            if choice == "q":
                break

            try:

                target_bin = int(choice)

                rotate_to_bin(
                    target_bin
                )

            except ValueError as error:

                print(
                    f"Error: {error}"
                )

    finally:

        shutdown_carousel()
