#!/usr/bin/env python3
"""
diagnose_photos.py
---------------------
A standalone troubleshooting script for the pill-photo feature. Run it from
inside the rxsort_ui project folder (same place as main.py), using the exact
same Python interpreter PyCharm (or your terminal) uses to run the app:

    python3 diagnose_photos.py

It checks, in order:
  1. Whether THIS interpreter can actually import Pillow/ImageTk.
  2. What image files really exist in assets/pills/ on disk.
  3. What filenames the database has stored for each pill, and whether each
     one resolves to a real file -- flagging any mismatch by name.

This file isn't used by the app itself -- delete it whenever you're done
troubleshooting.
"""

import os
import sys

print("=" * 70)
print("Python executable:", sys.executable)
print("Python version:", sys.version.split()[0])
print("=" * 70)

print("\n--- Step 1: Can THIS interpreter load Pillow/ImageTk? ---")
pillow_ok = False
try:
    from PIL import Image, ImageTk  # noqa: F401
    pillow_ok = True
    print("OK -- Pillow and ImageTk imported successfully.")
except ImportError as e:
    print("FAILED:", e)
    print("Fix: run  pip install pillow  using this exact interpreter")
    print(f"     ({sys.executable})")

import config
import database
import pill_photos

print("\n--- Step 2: What's actually inside assets/pills/ ? ---")
print("Expected folder:", config.PILL_IMAGES_DIR)
if os.path.isdir(config.PILL_IMAGES_DIR):
    files_on_disk = sorted(os.listdir(config.PILL_IMAGES_DIR))
    if files_on_disk:
        for f in files_on_disk:
            print("  -", f)
    else:
        print("  (the folder exists but has no files in it)")
else:
    print("  FOLDER DOES NOT EXIST -- it should sit at that exact path.")
    files_on_disk = []

print("\n--- Step 3: What does the database expect, and does it match disk? ---")
database.initialize_database()
problems = 0
checked = 0
for pill in database.get_all_pills():
    for label, filename in [("top", pill.image_top), ("bottom", pill.image_bottom)]:
        if filename is None:
            print(f"  {pill.name:20s} {label:7s}: (no photo assigned yet)")
            continue
        checked += 1
        resolved = pill_photos.resolve_path(filename)
        if resolved:
            print(f"  {pill.name:20s} {label:7s}: '{filename}'  ->  FOUND ({resolved})")
        else:
            problems += 1
            print(f"  {pill.name:20s} {label:7s}: '{filename}'  ->  MISSING "
                  f"(expected at {os.path.join(config.PILL_IMAGES_DIR, filename)})")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
if not pillow_ok:
    print("-> Pillow is not importable in this interpreter. This alone will make")
    print("   every photo fall back to the drawn icon, even ones listed correctly.")
if checked and problems:
    print(f"-> {problems} of {checked} photo reference(s) point to files that don't")
    print("   exist on disk under that exact name. Double-check for typos, extra")
    print("   spaces, or a different extension (.jpeg vs .jpg, etc.) between what's")
    print("   in database.py and what the file is actually named in assets/pills/.")
if pillow_ok and checked and not problems:
    print("-> Pillow imports fine and every referenced file was found on disk.")
    print("   Photos should display. If they still don't, delete rxsort.db, rerun")
    print("   main.py, and check this script's output again for anything new.")
if checked == 0:
    print("-> No pill currently has any image_top/image_bottom set in the database.")
