import sqlite3


connection = sqlite3.connect("database/rxsort.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM pills")

pills = cursor.fetchall()

for pill in pills:
    print(pill)

connection.close()
