import sqlite3
from pathlib import Path

def query_schema():
    db_path = Path(__file__).resolve().parents[2] / "data" / "001attendance.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(defaults);")
    schema = cursor.fetchall()
    conn.close()
    return schema

if __name__ == "__main__":
    schema = query_schema()
    for column in schema:
        print(column)
