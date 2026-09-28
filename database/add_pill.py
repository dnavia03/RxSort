import sqlite3

connection = sqlite3.connect("database/rxsort.db")
cursor = connection.cursor()

print("=== Add New Pill to RxSort ===")

medication_name = input("Enter medication name: ")
brand_name = input("Enter brand name: ")
strength = input("Enter strength (e.g., 500 mg): ")
imprint = input("Enter imprint: ")
color = input("Enter color: ")
shape = input("Enter shape: ")
dosage_form = input("Enter dosage form (e.g., Tablet, Capsule): ")
length_mm = float(input("Enter length in mm: "))
width_mm = float(input("Enter width in mm: "))

cursor.execute("""
INSERT INTO pills (
    medication_name,
    brand_name,
    strength,
    imprint,
    color,
    shape,
    dosage_form,
    length_mm,
    width_mm
) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    medication_name,
    brand_name,
    strength,
    imprint,
    color,
    shape,
    dosage_form,
    length_mm,
    width_mm
))

connection.commit()
connection.close()

print("Test pill added successfully.")
