import os
import sqlite3
import json

# Sample Thai public holidays (can extend or replace later)
thai_holidays = [
    ("2025-01-01", "New Year's Day"),
    ("2025-04-13", "Songkran Festival Start"),
    ("2025-04-14", "Songkran Festival"),
    ("2025-04-15", "Songkran Festival End"),
    ("2025-05-01", "Labour Day"),
    ("2025-12-05", "King's Birthday"),
    ("2025-12-10", "Constitution Day"),
]

# Get folder of current script (logic)
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

# Go up two levels to Bluecard_v2 root folder
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# Data folder is at Bluecard_v2/data
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Ensure data folder exists
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILENAME = "001attendance.db"
DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)

JSON_FILENAME = "001attendance_data.json"
JSON_PATH = os.path.join(DATA_DIR, JSON_FILENAME)

def recreate_db(db_path=DB_PATH):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted existing database {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE classes (
        class_no TEXT PRIMARY KEY,
        company TEXT,
        consultant TEXT,
        teacher TEXT,
        teacher_no TEXT,
        room TEXT,
        course_book TEXT,
        start_date TEXT,
        finish_date TEXT,
        time TEXT,
        notes TEXT,
        rate INTEGER,
        ccp INTEGER,
        travel INTEGER,
        bonus INTEGER,
        course_hours INTEGER,
        class_time INTEGER,
        max_classes TEXT,
        days TEXT,
        cod_cia TEXT,
        archive TEXT,
        show_nickname TEXT DEFAULT 'Yes',
        show_company_no TEXT DEFAULT 'Yes',
        show_score TEXT DEFAULT 'Yes',
        show_prestest TEXT DEFAULT 'Yes',
        show_posttest TEXT DEFAULT 'Yes',
        show_attn TEXT DEFAULT 'Yes',
        show_p TEXT DEFAULT 'Yes',
        show_a TEXT DEFAULT 'Yes',
        show_l TEXT DEFAULT 'Yes'
    );
    CREATE TABLE students (
        student_id TEXT PRIMARY KEY,
        class_no TEXT,
        name TEXT,
        nickname TEXT,
        company_no TEXT,
        gender TEXT,
        score TEXT,
        pre_test TEXT,
        post_test TEXT,
        note TEXT,
        active TEXT
    );
    CREATE TABLE class_students (
        class_no TEXT,
        student_id TEXT,
        PRIMARY KEY (class_no, student_id),
        FOREIGN KEY (class_no) REFERENCES classes(class_no),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    CREATE TABLE attendance (
        class_no TEXT,
        student_id TEXT,
        date TEXT,
        status TEXT,
        PRIMARY KEY (class_no, student_id, date),
        FOREIGN KEY (class_no) REFERENCES classes(class_no),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    CREATE TABLE dates (
        class_no TEXT,
        date TEXT,
        note TEXT,
        PRIMARY KEY (class_no, date),
        FOREIGN KEY (class_no) REFERENCES classes(class_no)
    );
    CREATE TABLE holidays (
        date TEXT PRIMARY KEY,
        name TEXT
    );
    CREATE TABLE defaults (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    print("Created tables")

    cursor.executemany("INSERT INTO holidays VALUES (?, ?)", thai_holidays)
    print("Inserted Thai holidays")

    conn.commit()
    return conn

def import_data(conn, data):
    cursor = conn.cursor()
    for class_no, class_data in data["classes"].items():
        meta = class_data["metadata"]

        cursor.execute("""
            INSERT OR REPLACE INTO classes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            meta["class_no"], meta["company"], meta["consultant"], meta["teacher"], meta["teacher_no"],
            meta["room"], meta["course_book"], meta["start_date"], meta["finish_date"], meta["time"],
            meta.get("notes", ""), int(meta.get("rate", 0)), int(meta.get("ccp", 0)), int(meta.get("travel", 0)),
            int(meta.get("bonus", 0)), int(meta.get("course_hours", 0)), int(meta.get("class_time", 0)),
            meta.get("max_classes", ""), meta.get("days", ""), meta.get("cod_cia", ""), class_data.get("archive", "No"),
            meta.get("show_nickname", "Yes"),
            meta.get("show_company_no", "Yes"),
            meta.get("show_score", "Yes"),
            meta.get("show_prestest", "Yes"),
            meta.get("show_posttest", "Yes"),
            meta.get("show_attn", "Yes"),
            meta.get("show_p", "Yes"),
            meta.get("show_a", "Yes"),
            meta.get("show_l", "Yes")
        ))

        for date in meta.get("dates", []):
            cursor.execute("""
                INSERT OR IGNORE INTO dates VALUES (?, ?, ?)
            """, (class_no, date, None))

        for student_id, student in class_data["students"].items():
            cursor.execute("""
                INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id,
                class_no,  # <-- PATCH: Add class_no here
                student["name"],
                student.get("nickname", ""),
                student.get("company_no", ""),
                student.get("gender", ""),
                student.get("score", ""),
                student.get("pre_test", ""),
                student.get("post_test", ""),
                student.get("note", ""),
                student.get("active", "Yes")
            ))
            cursor.execute("""
                INSERT OR IGNORE INTO class_students VALUES (?, ?)
            """, (class_no, student_id))

            for date, status in student.get("attendance", {}).items():
                cursor.execute("""
                    INSERT OR REPLACE INTO attendance VALUES (?, ?, ?, ?)
                """, (class_no, student_id, date, status))

    conn.commit()
    print("Imported class data")

def import_defaults(conn, defaults_path=os.path.join(DATA_DIR, "default.json")):
    if not os.path.exists(defaults_path):
        print(f"No default.json found at {defaults_path}")
        return
    with open(defaults_path, "r", encoding="utf-8") as f:
        defaults = json.load(f)
    # --- PATCH: Map def_teacherno to def_teacher_no ---
    if "def_teacherno" in defaults:
        defaults["def_teacher_no"] = defaults.pop("def_teacherno")
    cursor = conn.cursor()
    for key, value in defaults.items():
        cursor.execute("INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    print("Imported defaults from default.json")

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Error: Dataset file not found: {JSON_PATH}")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = recreate_db()
    import_data(conn, data)
    import_defaults(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holidays ORDER BY date")
    holidays = cursor.fetchall()
    print("Holidays in DB:")
    for h in holidays:
        print(h)

    conn.close()

if __name__ == "__main__":
    main()
