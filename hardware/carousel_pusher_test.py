from time import sleep

from hardware import carousel
from hardware import pusher


# ==========================================================
# RXSORT CAROUSEL + PUSHER INTEGRATION TEST
# ==========================================================

PAUSE_BEFORE_PUSH = 0.5
PAUSE_AFTER_PUSH = 0.5


def run_sort_test(target_bin):
    """
    Simulates the mechanical portion of an RxSort sorting cycle.

    1. Move carousel to selected bin
    2. Wait for carousel to settle
    3. Run pusher cycle
    """

    print("\n====================================")
    print("Starting mechanical sorting test")
    print("====================================")

    print(f"\nTarget bin: {target_bin}")

    # ------------------------------------------------------
    # STEP 1: MOVE CAROUSEL
    # ------------------------------------------------------

    print("\n[1/2] Positioning carousel...")

    carousel.rotate_to_bin(target_bin)

    print("Carousel movement complete.")

    sleep(PAUSE_BEFORE_PUSH)

    # ------------------------------------------------------
    # STEP 2: PUSH PILL
    # ------------------------------------------------------

    print("\n[2/2] Running pusher...")

    pusher.push_cycle()

    sleep(PAUSE_AFTER_PUSH)

    print("\n====================================")
    print("Mechanical sorting test complete.")
    print("====================================\n")


def main():

    print("\nRxSort Carousel + Pusher Test")
    print("=============================")

    carousel_initialized = False
    pusher_initialized = False

    try:

        # --------------------------------------------------
        # INITIALIZE CAROUSEL
        # --------------------------------------------------

        print("\nInitializing carousel...")

        carousel_initialized = carousel.initialize_carousel()

        if not carousel_initialized:
            print("Carousel initialization failed.")
            return

        # --------------------------------------------------
        # INITIALIZE PUSHER
        # --------------------------------------------------

        print("Initializing pusher...")

        pusher_initialized = pusher.initialize_pusher()

        if not pusher_initialized:
            print("Pusher initialization failed.")
            return

        # --------------------------------------------------
        # SET CAROUSEL HOME POSITION
        # --------------------------------------------------

        carousel.home_carousel()

        print("\nIMPORTANT:")
        print("Physically align BIN 1 before testing.")

        # --------------------------------------------------
        # TEST LOOP
        # --------------------------------------------------

        while True:

            print("\n------------------------------------")
            print("Enter target bin (1-10)")
            print("Enter Q to quit")
            print("------------------------------------")

            choice = input("\nTarget bin: ").strip().lower()

            if choice == "q":
                break

            try:

                target_bin = int(choice)

                if target_bin < 1 or target_bin > carousel.TOTAL_BINS:
                    print(
                        f"Bin must be between 1 and "
                        f"{carousel.TOTAL_BINS}."
                    )
                    continue

                run_sort_test(target_bin)

            except ValueError:

                print("Please enter a valid bin number.")

    except KeyboardInterrupt:

        print("\n\nTest stopped by user.")

    finally:

        print("\nShutting down mechanical systems...")

        if pusher_initialized:
            pusher.shutdown_pusher()

        if carousel_initialized:
            carousel.shutdown_carousel()

        print("RxSort mechanical test closed.")


if __name__ == "__main__":
    main()
