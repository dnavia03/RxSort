from time import sleep

from hardware.carousel import (
    initialize_carousel,
    rotate_to_bin,
    shutdown_carousel
)

from hardware.pusher import (
    initialize_pusher,
    push_cycle,
    shutdown_pusher
)


def initialize_hardware():

    print("\nInitializing RxSort hardware...")

    carousel_ready = initialize_carousel()
    pusher_ready = initialize_pusher()

    if carousel_ready:
        print("Carousel ready.")
    else:
        print("Carousel configuration incomplete.")

    if pusher_ready:
        print("Pusher ready.")
    else:
        print("Pusher configuration incomplete.")

    return carousel_ready and pusher_ready


def sort_pill(bin_number):
    """
    Complete physical sorting sequence.

    1. Rotate carousel
    2. Wait for carousel to settle
    3. Push pill
    4. Retract pusher
    """

    print(
        f"\nBeginning RxSort sorting sequence "
        f"for bin {bin_number}."
    )

    rotate_to_bin(bin_number)

    # Small settling delay.
    # Can be adjusted later.
    sleep(0.25)

    push_cycle()

    print(
        f"Pill successfully routed to bin {bin_number}.\n"
    )


def shutdown_hardware():

    shutdown_pusher()
    shutdown_carousel()

    print("RxSort hardware shut down.")
