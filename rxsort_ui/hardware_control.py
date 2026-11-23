"""
hardware_control.py
---------------------
Carousel and pusher control, matching the mechanical design described in
the RxSort report: a NEMA 17 stepper motor driving the rotating carousel,
a lead-screw pusher also driven by a NEMA 17, and both controlled through
individual DRV8825 drivers (STEP/DIR signals) after the original stepper
motor HAT proved unreliable (report section F-5).

Call sequence used by the UI, matching the block diagram's "Mechanical
Control" box:

    carousel.rotate_to_bin(bin_number)   # 1. Rotate to assigned bin
    pusher.activate()                    # 2. Activate pusher (dispense pill)

In DEMO_MODE, both classes simulate motion instantly and simply report what
*would* happen, which is enough to drive the UI's status log and carousel
map widget. On real hardware (DEMO_MODE = False with RPi.GPIO installed),
steps are pulsed on the STEP pin with direction set by the DIR pin.

Because pulsing GPIO pins for real motor motion is blocking, any call into
the real implementation should be made from a background thread (see
ui/screens.py ScanningScreen) so the Tkinter main loop -- and therefore the
touchscreen -- stays responsive while the carousel turns.
"""

import time
import config

try:
    import RPi.GPIO as GPIO
    _HAS_GPIO = True
except ImportError:
    _HAS_GPIO = False


class CarouselController:
    def __init__(self):
        self.current_bin = 1
        self._use_real_hw = (not config.DEMO_MODE) and _HAS_GPIO
        if self._use_real_hw:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.CAROUSEL_STEP_PIN, GPIO.OUT)
            GPIO.setup(config.CAROUSEL_DIR_PIN, GPIO.OUT)
            GPIO.setup(config.CAROUSEL_ENABLE_PIN, GPIO.OUT)
            GPIO.output(config.CAROUSEL_ENABLE_PIN, GPIO.LOW)  # DRV8825 enable is active-low

    def rotate_to_bin(self, bin_number: int, log_callback=None) -> None:
        """Rotate the carousel so ``bin_number`` is aligned with the pusher."""
        bins_to_travel = (bin_number - self.current_bin) % config.NUM_CAROUSEL_BINS
        steps_per_bin = (config.CAROUSEL_STEPS_PER_REV * config.CAROUSEL_MICROSTEPPING
                          ) // config.NUM_CAROUSEL_BINS
        total_steps = bins_to_travel * steps_per_bin

        if log_callback:
            log_callback(f"Rotating carousel {bins_to_travel} position(s) "
                          f"({total_steps} steps) to bin {bin_number}...")

        if self._use_real_hw:
            GPIO.output(config.CAROUSEL_DIR_PIN, GPIO.HIGH)
            for _ in range(total_steps):
                GPIO.output(config.CAROUSEL_STEP_PIN, GPIO.HIGH)
                time.sleep(0.0007)
                GPIO.output(config.CAROUSEL_STEP_PIN, GPIO.LOW)
                time.sleep(0.0007)
        else:
            # Demo: nothing to physically move.
            time.sleep(0.05)

        self.current_bin = bin_number
        if log_callback:
            log_callback(f"Carousel aligned on bin {bin_number}.")

    def cleanup(self) -> None:
        if self._use_real_hw:
            GPIO.cleanup()


class PusherController:
    def __init__(self):
        self._use_real_hw = (not config.DEMO_MODE) and _HAS_GPIO
        if self._use_real_hw:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(config.PUSHER_STEP_PIN, GPIO.OUT)
            GPIO.setup(config.PUSHER_DIR_PIN, GPIO.OUT)
            GPIO.setup(config.PUSHER_ENABLE_PIN, GPIO.OUT)
            GPIO.output(config.PUSHER_ENABLE_PIN, GPIO.LOW)

    def activate(self, log_callback=None) -> None:
        """Extend the pusher to move the pill out of the imaging chamber and
        then retract it back to the home position."""
        if log_callback:
            log_callback("Activating pusher: moving pill toward carousel...")

        if self._use_real_hw:
            GPIO.output(config.PUSHER_DIR_PIN, GPIO.HIGH)  # extend
            for _ in range(config.PUSHER_EXTEND_STEPS):
                GPIO.output(config.PUSHER_STEP_PIN, GPIO.HIGH)
                time.sleep(0.0005)
                GPIO.output(config.PUSHER_STEP_PIN, GPIO.LOW)
                time.sleep(0.0005)
            GPIO.output(config.PUSHER_DIR_PIN, GPIO.LOW)   # retract
            for _ in range(config.PUSHER_EXTEND_STEPS):
                GPIO.output(config.PUSHER_STEP_PIN, GPIO.HIGH)
                time.sleep(0.0005)
                GPIO.output(config.PUSHER_STEP_PIN, GPIO.LOW)
                time.sleep(0.0005)
        else:
            time.sleep(0.05)

        if log_callback:
            log_callback("Pusher cycle complete.")

    def cleanup(self) -> None:
        if self._use_real_hw:
            GPIO.cleanup()
