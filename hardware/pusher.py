from time import sleep


# ==========================================================
# RXSORT PUSHER CONFIGURATION
# Fill these in later during hardware integration
# ==========================================================

STEP_PIN = 9
DIR_PIN = 10
ENABLE_PIN = 11

PUSH_STEPS = 3500
RETRACT_STEPS = 3500

STEP_DELAY = 0.001

PUSH_DIRECTION = 0
RETRACT_DIRECTION = 1


# ==========================================================
# HARDWARE INITIALIZATION
# ==========================================================

step_output = None
dir_output = None
enable_output = None


def initialize_pusher():
    """
    Initializes Raspberry Pi GPIO communication with the DRV8825.

    GPIO pin numbers can be assigned later once final wiring is known.
    """

    global step_output
    global dir_output
    global enable_output

    if STEP_PIN is None or DIR_PIN is None:
        print("Pusher hardware pins have not been configured yet.")
        return False

    from gpiozero import OutputDevice

    step_output = OutputDevice(
        STEP_PIN,
        initial_value=False
    )

    dir_output = OutputDevice(
        DIR_PIN,
        initial_value=False
    )

    if ENABLE_PIN is not None:
        enable_output = OutputDevice(
            ENABLE_PIN,
            active_high=False,
            initial_value=False
        )

    print("Pusher initialized successfully.")

    return True


# ==========================================================
# ENABLE / DISABLE
# ==========================================================

def enable_motor():

    if enable_output is not None:
        enable_output.on()


def disable_motor():

    if enable_output is not None:
        enable_output.off()


# ==========================================================
# LOW-LEVEL MOTOR CONTROL
# ==========================================================

def move_steps(steps, direction, delay=None):
    """
    Sends STEP pulses to the DRV8825.

    steps:
        Number of motor steps/microsteps.

    direction:
        1 or 0 depending on desired motor direction.

    delay:
        Delay between pulses.
    """

    if step_output is None or dir_output is None:
        raise RuntimeError(
            "Pusher has not been initialized."
        )

    if steps is None:
        raise ValueError(
            "Motor step count has not been calibrated."
        )

    if delay is None:
        delay = STEP_DELAY

    dir_output.value = direction

    sleep(0.01)

    for _ in range(steps):

        step_output.on()
        sleep(delay)

        step_output.off()
        sleep(delay)


# ==========================================================
# HIGH-LEVEL PUSHER COMMANDS
# ==========================================================

def extend_pusher():

    if PUSH_STEPS is None:
        raise ValueError(
            "PUSH_STEPS has not been calibrated."
        )

    print("Extending pusher...")

    enable_motor()

    move_steps(
        PUSH_STEPS,
        PUSH_DIRECTION
    )

    print("Pusher extended.")


def retract_pusher():

    if RETRACT_STEPS is None:
        raise ValueError(
            "RETRACT_STEPS has not been calibrated."
        )

    print("Retracting pusher...")

    enable_motor()

    move_steps(
        RETRACT_STEPS,
        RETRACT_DIRECTION
    )

    print("Pusher retracted.")


def push_cycle():
    """
    Complete RxSort pill pushing sequence.
    """

    print("\nStarting pusher cycle...")

    extend_pusher()

    sleep(0.5)

    retract_pusher()

    disable_motor()

    print("Pusher cycle complete.\n")


# ==========================================================
# SHUTDOWN
# ==========================================================

def shutdown_pusher():

    disable_motor()

    if step_output is not None:
        step_output.close()

    if dir_output is not None:
        dir_output.close()

    if enable_output is not None:
        enable_output.close()

    print("Pusher hardware shut down.")

# ==========================================================
# TEST MODE
# ==========================================================


if __name__ == "__main__":

    print("Starting RxSort pusher test...")

    if initialize_pusher():

        try:
            push_cycle()

        except KeyboardInterrupt:
            print("\nTest stopped.")

        finally:
            shutdown_pusher()

    else:
        print("Pusher could not be initialized.")
