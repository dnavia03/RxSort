import sqlite3

DATABASE_PATH = "database/rxsort.db"


def get_pill_by_id(pill_id):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM pills WHERE pill_id = ?",
        (pill_id,)
    )

    pill = cursor.fetchone()

    connection.close()

    return pill
