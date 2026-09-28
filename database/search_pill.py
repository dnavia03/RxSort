import sqlite3


connection = sqlite3.connect("database/rxsort.db")
cursor = connection.cursor()

pill_id = int(input("Enter pill ID: "))

cursor.execute(
    "SELECT * FROM pills WHERE pill_id = ?",
    (pill_id,)
)

pill = cursor.fetchone()

if pill:
    print("\nPill found!")
    print("ID:", pill[0])
    print("Medication:", pill[1])
    print("Brand:", pill[2])
    print("Strength:", pill[3])
    print("Imprint:", pill[4])
    print("Color:", pill[5])
    print("Shape:", pill[6])
    print("Dosage Form:", pill[7])
    print("Length:", pill[8], "mm")
    print("Width:", pill[9], "mm")
else:
    print("\nPill not found.")

connection.close()
