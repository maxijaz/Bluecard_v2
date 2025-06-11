import sqlite3
from pathlib import Path

def query_defaults():
    db_path = Path(__file__).resolve().parents[2] / "data" / "001attendance.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM defaults;")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    rows = query_defaults()
    for row in rows:
        print(row)
