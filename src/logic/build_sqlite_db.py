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
    conn.execute("PRAGMA foreign_keys = ON")
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
        show_l TEXT DEFAULT 'Yes',
        -- PATCH: Add color columns for attendance types
        bgcolor_p TEXT DEFAULT '#c8e6c9',
        bgcolor_a TEXT DEFAULT '#ffcdd2',
        bgcolor_l TEXT DEFAULT '#fff9c4',
        bgcolor_cod TEXT DEFAULT '#c8e6c9',
        bgcolor_cia TEXT DEFAULT '#ffcdd2',
        bgcolor_hol TEXT DEFAULT '#ffcdd2'
    );
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            INSERT OR REPLACE INTO classes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
            meta.get("show_l", "Yes"),
            meta.get("bgcolor_p", "#c8e6c9"),
            meta.get("bgcolor_a", "#ffcdd2"),
            meta.get("bgcolor_l", "#fff9c4"),
            meta.get("bgcolor_cod", "#c8e6c9"),
            meta.get("bgcolor_cia", "#ffcdd2"),
            meta.get("bgcolor_hol", "#ffcdd2"),
        ))

        for date in meta.get("dates", []):
            cursor.execute("""
                INSERT OR IGNORE INTO dates VALUES (?, ?, ?)
            """, (class_no, date, None))

        for student_id, student in class_data["students"].items():
            # Let SQLite auto-assign student_id by passing None
            sid = None
            try:
                cursor.execute("""
                    INSERT INTO students (
                        student_id, class_no, name, nickname, company_no, gender,
                        score, pre_test, post_test, note, active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    None,  # Let SQLite auto-increment student_id
                    class_no,
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
                sid = cursor.lastrowid  # Get the DB-generated student_id
            except Exception as e:
                print(f"Error inserting student {student.get('name', '')}: {e}")
                continue

            # Insert into class_students (future-proof)
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO class_students VALUES (?, ?)
                """, (class_no, sid))
            except Exception as e:
                print(f"Error inserting into class_students for {student.get('name', '')}: {e}")

            # Insert attendance records for this student
            for date, status in student.get("attendance", {}).items():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO attendance VALUES (?, ?, ?, ?)
                    """, (class_no, sid, date, status))
                except Exception as e:
                    print(f"Error inserting attendance for {student.get('name', '')}, date {date}: {e}")

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
    # --- PATCH: Add cod_cia_hol default if not present ---
    if "cod_cia_hol" not in defaults:
        # Insert between columns_before_today and show_nickname if you care about order
        keys = list(defaults.keys())
        idx = keys.index("columns_before_today") + 1 if "columns_before_today" in keys else len(keys)
        items = list(defaults.items())
        items.insert(idx, ("cod_cia_hol", "0 COD / 0 CIA / 0 HOL"))
        defaults = dict(items)
    # PATCH: Add default colors if not present
    for color_key, color_val in [
        ("bgcolor_p", "#c8e6c9"),
        ("bgcolor_a", "#ffcdd2"),
        ("bgcolor_l", "#fff9c4"),
        ("bgcolor_cod", "#c8e6c9"),
        ("bgcolor_cia", "#ffcdd2"),
        ("bgcolor_hol", "#ffcdd2"),
    ]:
        if color_key not in defaults:
            defaults[color_key] = color_val
    # PATCH: Add font size and global color defaults if not present
    # Remove font_size (global) from defaults, only use specific font sizes
    # Ensure all settings fields used in the UI are present in defaults
    if "form_bg_color" not in defaults:
        defaults["form_bg_color"] = "#e3f2fd"  # Light blue
    if "form_fg_color" not in defaults:
        defaults["form_fg_color"] = "#222222"  # Main text color
    if "button_bg_color" not in defaults:
        defaults["button_bg_color"] = "#1976d2"  # Blue
    if "button_fg_color" not in defaults:
        defaults["button_fg_color"] = "#ffffff"  # White
    if "button_font_size" not in defaults:
        defaults["button_font_size"] = "12"
    if "table_bg_color" not in defaults:
        defaults["table_bg_color"] = "#ffffff"  # White
    if "table_fg_color" not in defaults:
        defaults["table_fg_color"] = "#222222"  # Table text color
    if "table_header_bg_color" not in defaults:
        defaults["table_header_bg_color"] = "#1976d2"  # Table header bg
    if "table_header_fg_color" not in defaults:
        defaults["table_header_fg_color"] = "#ffffff"  # Table header fg
    if "metadata_font_size" not in defaults:
        defaults["metadata_font_size"] = "12"
    if "metadata_fg_color" not in defaults:
        defaults["metadata_fg_color"] = "#222222"
    if "table_font_size" not in defaults:
        defaults["table_font_size"] = "12"
    if "form_font_size" not in defaults:
        defaults["form_font_size"] = "12"
    # --- Add any new settings fields from settings.py ---
    # These are the metadata fields (default values can be blank)
    for meta_key in [
        "def_teacher", "def_teacher_no", "def_coursehours", "def_classtime", "def_rate", "def_ccp", "def_travel", "def_bonus"
    ]:
        if meta_key not in defaults:
            defaults[meta_key] = ""
    # Add any new color/font fields from settings.py if missing
    for k, v in [
        ("table_header_font_size", "12"),
    ]:
        if k not in defaults:
            defaults[k] = v
    # Remove any old global font_size if present
    if "font_size" in defaults:
        del defaults["font_size"]
    # Metadata section
    if "metadata_bg_color" not in defaults:
        defaults["metadata_bg_color"] = "#e3f2fd"  # or your preferred color

    # (Optional) Button hover/border color
    if "button_border_color" not in defaults:
        defaults["button_border_color"] = "#1976d2"  # or your preferred color

    # (Optional) Form border/title color
    if "form_border_color" not in defaults:
        defaults["form_border_color"] = "#1976d2"
    if "form_title_color" not in defaults:
        defaults["form_title_color"] = "#222222"
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
