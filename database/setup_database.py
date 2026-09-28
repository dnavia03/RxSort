import sqlite3


connection = sqlite3.connect("database/rxsort.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pills (
    pill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_name TEXT NOT NULL,
    brand_name TEXT,
    strength TEXT NOT NULL,
    imprint TEXT, 
    color TEXT,
    shape TEXT, 
    dosage_form TEXT, 
    length_mm REAL,
    width_mm REAL
    )
""")

connection.commit()
connection.close()

print("RXSort database created successfully.")
