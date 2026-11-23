"""
pill_photos.py
----------------
Loads real top-camera / bottom-camera reference photos for pills that have
them on file (see config.PILL_IMAGES_DIR and the image_top / image_bottom
columns added to the pill database), for the results screen's visual
verification panel.

Plain Tkinter's PhotoImage can only decode GIF/PGM/PPM, so JPEG/PNG photos
need Pillow (``pip install pillow``) to load. If Pillow isn't installed, or
a pill simply doesn't have a photo on file yet, ``load_thumbnail`` returns
None and the caller (ui/screens.py) falls back to pill_graphic's drawn icon
instead, so the app never crashes for medications that haven't been
photographed yet.
"""

import os
from typing import Optional

import config

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def resolve_path(filename: Optional[str]) -> Optional[str]:
    """Turn a filename stored in the database into a full path, or None if
    there is no filename or the file isn't actually on disk."""
    if not filename:
        return None
    path = os.path.join(config.PILL_IMAGES_DIR, filename)
    return path if os.path.isfile(path) else None


def load_thumbnail(filename: Optional[str], max_size=(170, 120)):
    """Return a Tkinter-displayable image for the given filename, resized to
    fit within ``max_size`` while preserving aspect ratio, or None if the
    photo can't be loaded (missing file, missing Pillow, or a decode error).

    IMPORTANT: Tkinter does not keep its own reference to the returned
    object, so the caller must hold onto it (e.g. ``self._photo = img``)
    for as long as it's displayed, or it will be garbage-collected and the
    image will vanish from the screen.
    """
    if not _HAS_PIL:
        return None
    path = resolve_path(filename)
    if path is None:
        return None
    try:
        img = Image.open(path)
        img = img.convert("RGB")
        img.thumbnail(max_size)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def pillow_available() -> bool:
    return _HAS_PIL
