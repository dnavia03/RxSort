# RxSort Touchscreen Interface

A Python/Tkinter touchscreen UI for the RxSort automated pill identification
and sorting system (Senior Design Team 6), built around the architecture in
the project's Senior Design II report: dual top/bottom camera capture ->
on-device AI classification -> SQLite medication lookup -> carousel + pusher
sorting, with a 17-bin carousel (bins 1-16 for identified medications, bin
17 reserved as the reject/discard compartment for anything that can't be
identified confidently).

## Quick start

```bash
# On a Raspberry Pi (or any desktop with Tkinter installed):
sudo apt install python3-tk      # if tkinter isn't already present
python3 main.py                  # windowed, for development
python3 main.py --kiosk          # fullscreen, for the real touchscreen
```

No extra pip packages are required for the simulated camera/AI/motor demo
mode itself. One optional package matters for the results screen: **Pillow**
(`pip install pillow`) is needed to display the real JPEG/PNG reference
photos taken during pill testing. Without it, the app still runs fine, it
just shows a drawn placeholder icon in place of any photo.

On first run, `main.py` creates `rxsort.db` (SQLite) next to the project
and seeds it with 16 example medications. Delete `rxsort.db` at any time to
reset the sort history and bin assignments back to the defaults in
`database.py`.

## What it does

* **Home** - large "Insert Pill & Scan" button plus a running sorted/rejected
  count for the session.
* **Scanning** - a live status log that mirrors the RxSort pipeline (capture
  top/bottom images, preprocess, run both camera models, compare
  predictions, decide SORT vs. REJECT, rotate the carousel, activate the
  pusher).
* **Results** - shown when a pill is identified above the confidence
  threshold and both camera models agree. Displays the medication name,
  brand, a short identity description, an illustrative visual-verification
  graphic (drawn from the stored color/shape, since no photo library is
  bundled), strength/dosage, imprint, color, shape, form, dimensions, the
  top/bottom camera confidences, and the destination carousel bin,
  highlighted live on a 17-bin carousel map.
* **Reject alert** - shown whenever confidence is below the threshold or the
  two camera models disagree. Clearly alerts the user that the medication
  was **not** identified and that the pill was routed to bin 17 (the
  discard pile) for manual review, with the reason and both confidence
  values.
* **History** - a scrollable log of every past sort/reject event.
* **Settings** - adjust the acceptance confidence threshold (80% by
  default, matching the project README), see the current operating mode,
  and view the full bin-assignment table.
* **Manual Control** - manually command the carousel to any of the 17 bins
  or trigger the pusher, useful for calibration and demos.

## Project layout

```
rxsort_ui/
├── main.py                entry point
├── config.py              bin count, confidence threshold, GPIO pins, demo/real switch
├── database.py            SQLite schema, 16-medication seed data, logging/queries
├── ai_classifier.py       DemoClassifier (simulated) + RealClassifier (documented stub)
├── hardware_control.py    CarouselController / PusherController (simulated + real GPIO)
├── pill_graphic.py        draws the fallback (no-photo) visual-verification icon
├── pill_photos.py         loads real top/bottom reference photos via Pillow
├── assets/pills/          real reference photos (jpg/png) per medication
└── ui/
    ├── app.py             screen manager / shared state
    ├── theme.py           color palette, fonts
    ├── widgets.py         TouchButton, HeaderBar, CarouselMapCanvas
    └── screens.py         Home, Scanning, Results, Reject, History, Settings, Manual
```

## Adding pill photos

The results screen shows a real top-camera and bottom-camera photo for any
medication that has them on file, falling back to a drawn placeholder icon
for the rest. Ibuprofen already has both photos wired up as an example.

To add photos for another medication:

1. Drop the two image files (jpg or png) into `assets/pills/`. Use a clear
   name, e.g. `amlodipine_top.jpg` and `amlodipine_bottom.jpg`.
2. In `database.py`, find that medication's row in `_SEED_PILLS` and set its
   last two fields (currently `None, None`) to the filenames you just added,
   e.g. `"amlodipine_top.jpg", "amlodipine_bottom.jpg"`.
3. Delete `rxsort.db` so it reseeds with the updated data (this also clears
   the sort history log), or update the row directly in the `pills` table
   with a SQLite tool if you'd rather keep your history.

This requires **Pillow** (`pip install pillow`) in addition to Tkinter,
since plain Tkinter can't decode JPEG/PNG files on its own. If Pillow isn't
installed, or a photo file is missing, the app automatically falls back to
the drawn icon instead of crashing.

## Connecting the real hardware

Everything is written so swapping simulation for hardware is a matter of
editing `config.py` and filling in two already-outlined classes, without
touching any screen code:

1. **AI pipeline** (`ai_classifier.RealClassifier`): install
   `tflite-runtime` and `picamera2`, export the two trained models from the
   Edge Impulse projects linked in the report to
   `config.TOP_CAMERA_MODEL_PATH` / `BOTTOM_CAMERA_MODEL_PATH`, then fill in
   `_capture_image()` and `_run_model()` (the structure and TODOs are
   already in place).
2. **Motor control** (`hardware_control.py`): the DRV8825 STEP/DIR GPIO
   logic is already implemented behind `config.DEMO_MODE`; it only needs
   `RPi.GPIO` installed and the pin numbers in `config.py` matched to your
   wiring. Because stepping real motors blocks, consider running
   `rotate_to_bin()` / `activate()` on a background `threading.Thread` from
   `ui/screens.py` so the touchscreen doesn't freeze mid-rotation.
3. Set `config.DEMO_MODE = False` once both are wired up.

## Notes

* The 16 seed medications (name, strength, imprint, color, shape, form,
  dimensions) are realistic example data for demonstration purposes only,
  consistent with the project's own disclaimer that RxSort is an academic
  prototype and not a certified medical device. Verify and replace this
  data with confirmed values (e.g. from the FDA NDC directory) before any
  real-world use.
* This code was developed and syntax/logic-tested in a headless sandbox
  without a Tkinter display available, so please do a quick visual pass on
  your own Raspberry Pi or desktop before the final demo.
