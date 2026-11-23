"""
database.py
------------
SQLite storage for the RxSort medication database and sort-event log, per
the schema described in the RxSort README (pill ID, medication name, brand
name, strength, imprint, color, shape, dosage form, physical dimensions).

This module adds two fields that the UI needs but the original README did
not enumerate: ``bin_number`` (which carousel compartment the medication is
assigned to) and ``description`` (a short, plain-language identity blurb
shown on the results screen).

NOTE ON SEED DATA: The sixteen medications below are real, commonly
prescribed/OTC drugs used so the interface has realistic-looking data to
demonstrate against. Strength, imprint, color, shape and form are
representative examples for demonstration purposes only -- exactly like the
project's own README states, RxSort is an academic prototype and this seed
data has not been verified against an authoritative source (e.g. the FDA
NDC directory). Replace it with verified entries before any real-world use.
"""

import sqlite3
import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict

import config


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Pill:
    pill_id: int
    class_id: int
    name: str
    brand: str
    description: str
    strength: str
    imprint: str
    color: str
    shape: str
    form: str
    dimensions: str
    bin_number: int
    image_top: Optional[str] = None     # filename under config.PILL_IMAGES_DIR, or None
    image_bottom: Optional[str] = None  # filename under config.PILL_IMAGES_DIR, or None


# class_id must match the index/label the AI classifier returns.
# bin_number must be unique and within 1..NUM_CAROUSEL_BINS-1 (bin 17 is reserved).
_SEED_PILLS = [
    # class_id, name,            brand,            description,
    #   strength,   imprint,     color,    shape,     form,       dimensions, bin,
    #   image_top,            image_bottom
    (0, "Ibuprofen", "Advil", "Nonsteroidal anti-inflammatory drug (NSAID) used to relieve pain, "
     "reduce fever, and reduce inflammation.", "200 mg", "44-527", "Brown", "Round", "Tablet",
     "9.6 mm x 9.6", 1, "ibuprofen_top.jpg", "ibuprofen_bottom.jpg"),
    (1, "Simvastatin", "Zocor", "Statin medication used to lower cholesterol and triglycerides and "
     "reduce the risk of cardiovascular disease.", "20 mg", "LL C03", "Tan", "Oval", "Tablet",
     "10 mm x 5.3 mm", 2, "Simvastatin_top.jpg", "Simvastatin_bottom.jpg"),
    (2, "Amlodipine", "Norvasc", "Calcium channel blocker used to treat high blood pressure and "
     "coronary artery disease.", "5 mg / 40 mg", "J 01", "Blue", "Capsule / Oblong", "Capsule",
     "19.8 mm x 7.1 mm", 3, "Amlodipine_top.jpg", "Amlodipine_bottom.jpg"),
    (3, "Acetaminophen", "Tylenol", "Relieves mild to moderate pain and temporarily reduce fever.", "500 mg", "TYLENOL", "Red", "Oblong/Oval", "Caplet",
     "18 mm x 8 mm", 4, "Acetaminophen_top.jpg", "Acetaminophen_bottom.jpg"),
    (4, "Fexofenadine Hydrochloride", "Allegra", "Relieves symptoms of seasonal allergies and chronic hives. It also blocks histamine in the body with minimal drowsiness compared to older antihistamines.",
     "180 mg", "L847", "Pink", "Oval", "Tablet", "7.8 x 17.8", 5, "Fexofenadine Hydrochloride_top.jpg", "Fexofenadine Hydrochloride_bottom.jpg"),
    (5, "Mucinex", "Guaifenesin", "Relieves chest congestion and loosens thick mucus or phlegm so it is easier to cough up during a cold, flu, or respiratory illness.",
     "30 mg/600 mg", "Mucinex 600", "Yellow/White", "Oval", "Tablet", "15.2 mm x 9.5 mm", 6, "Mucinex_top.jpg", "Mucinex_bottom.jpg"),
    (6, "Hydrochlorothiazide & Losartan Potassium", "Hyzaar", "Statin medication used to lower LDL cholesterol and reduce "
     "cardiovascular risk.", "12.5 mg/100 mg", "F 74", "White", "Oval", "Tablet", "16 mm x 7.1 mm", 7,
     "Hydrochlorothiazide & Losartan Potassium_top.jpg", "Hydrochlorothiazide & Losartan Potassium_bottom.jpg"),
    (7, "Prazosin Hydrochloride", "Minipress", "Treats high blood pressure (hypertension) and, off-label, PTSD-related nightmares. It works by relaxing blood vessels so blood flows more easily, lowering blood pressure and reducing adrenaline-driven vascular and sleep arousal.", "2 mg", "020 novitium", "Brown/Tan", "Capsule", "Capsule",
     "16.2 mm x 5.3 mm", 8, "Prazosin Hydrochloride_top.jpg", "Prazosin Hydrochloride_bottom.jpg"),
    (8, "Propranolol Hydrochloride", "Propranolol Hydrochloride ER", "Proton pump inhibitor used to reduce stomach acid and treat "
     "acid reflux and ulcers.", "60 mg", "60/RD203", "White", "Capsule", "Extended-Release(ER) capsule",
     "12.6 mm x 4.5 mm", 9, "Propranolol Hydrochloride_top.jpg", "Propranolol Hydrochloride_bottom.jpg"),
    (9, "Acetaminophen Guaifenesin", "Generic medication", "A combination medication used to temporarily relieve cold and flu symptoms, specifically pain, fever, and chest congestion. Sold in local pharmacies without the need of a prescription.",
     "325mg / 200 mg / 5 mg", "44-527", "White", "Oblong", "Tablet", "19.1 mm x 8.9 mm", 10, "Acetaminophen Guaifenesin_top.jpg", "Acetaminophen Guaifenesin_bottom.jpg"),
    (10, "Dexamethasone", "Decadron", "Reduces inflammation and calms an overactive immune system across many medical conditions. It is available by prescription in tablets, oral liquids, injections, eye drops, and topical forms.", "4 mg", "54-892", "Green", "Round", "Tablet",
     "5.2 mm x 5.2 mm", 11, "Dexamethasone_top.jpg", "Dexamethasone_bottom.jpg"),
    (11, "Benadryl Allergy Ultratab Diphenhydramine", "Benadryl", "Temporarily relieves allergy and common cold symptoms.", "25 mg", "B / WL25", "Pink", "Oblong", "Tablet", "10.1 mm x 4.7 mm", 12,
     "Benadryl Allergy Ultratab Diphenhydramine_top.jpg", "Benadryl Allergy Ultratab Diphenhydramine_bottom.jpg"),
    (12, "Labetalol Hydrochloride", "Generic medication", "A beta-blocker that is used to treat hypertension (high blood pressure). Labetalol oral is sometimes given with other blood pressure medications.", "300 mg", "AC372", "White", "Round", "Tablet",
     "10.2 mm x 10.2 mm", 13, "Labetalol Hydrochloride_top.jpg", "Labetalol Hydrochloride_bottom.jpg"),
    (13, "Famotidine", "Pepcid", "Reduces stomach acid and treat acid-related conditions.", "10 mg", "L141", "Pink", "Round", "Tablet", "8.2 mm x 8.2 mm", 14,
     "Famotidine_top.jpg", "Famotidine_bottom.jpg"),
]


# ---------------------------------------------------------------------------
# Connection / schema
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    """Create tables if they don't exist and seed the pill table if empty."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pills (
            pill_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id    INTEGER UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            brand       TEXT,
            description TEXT,
            strength    TEXT,
            imprint     TEXT,
            color       TEXT,
            shape       TEXT,
            form        TEXT,
            dimensions  TEXT,
            bin_number  INTEGER UNIQUE NOT NULL,
            image_top     TEXT,
            image_bottom  TEXT
        )
    """)

    # Migration path for databases created by an earlier version of this
    # project that predates the image_top/image_bottom columns.
    existing_columns = {row["name"] for row in cur.execute("PRAGMA table_info(pills)").fetchall()}
    if "image_top" not in existing_columns:
        cur.execute("ALTER TABLE pills ADD COLUMN image_top TEXT")
    if "image_bottom" not in existing_columns:
        cur.execute("ALTER TABLE pills ADD COLUMN image_bottom TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sort_log (
            log_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp        TEXT NOT NULL,
            pill_name        TEXT NOT NULL,
            bin_number       INTEGER NOT NULL,
            confidence_top   REAL,
            confidence_bottom REAL,
            status           TEXT NOT NULL  -- 'SORTED' or 'REJECTED'
        )
    """)

    cur.execute("SELECT COUNT(*) FROM pills")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            """INSERT INTO pills
               (class_id, name, brand, description, strength, imprint, color,
                shape, form, dimensions, bin_number, image_top, image_bottom)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            _SEED_PILLS,
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def get_pill_by_class_id(class_id: int) -> Optional[Pill]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM pills WHERE class_id = ?", (class_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return Pill(**{k: row[k] for k in row.keys()})


def get_all_pills() -> List[Pill]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM pills ORDER BY bin_number").fetchall()
    conn.close()
    return [Pill(**{k: r[k] for k in r.keys()}) for r in rows]


def get_bin_map() -> Dict[int, str]:
    """Return {bin_number: label} for every bin, including the reject bin."""
    bin_map: Dict[int, str] = {b: "Empty" for b in config.MEDICATION_BINS}
    for pill in get_all_pills():
        bin_map[pill.bin_number] = pill.name
    bin_map[config.REJECT_BIN] = "REJECT / DISCARD"
    return bin_map


def log_sort_event(pill_name: str, bin_number: int, confidence_top: Optional[float],
                    confidence_bottom: Optional[float], status: str) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO sort_log
           (timestamp, pill_name, bin_number, confidence_top, confidence_bottom, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (datetime.datetime.now().isoformat(timespec="seconds"), pill_name, bin_number,
         confidence_top, confidence_bottom, status),
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 50) -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sort_log ORDER BY log_id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows
