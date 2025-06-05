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

# JSON_FILENAME = "001attendance_data.json"
# JSON_PATH = os.path.join(DATA_DIR, JSON_FILENAME)

# --- BEGIN: Embedded attendance data (formerly from 001attendance_data.json) ---
ATTENDANCE_DATA = {
    "classes": {
        "OLO123": {
            "metadata": {
                "class_no": "OLO123",
                "company": "Acer",
                "consultant": "James",
                "teacher": "Paul R",
                "teacher_no": "A20049",
                "room": "Small building 2nd Floor",
                "course_book": "IEX Pre Inter",
                "start_date": "01/05/2025",
                "finish_date": "01/05/2026",
                "time": "17:00 - 19:00",
                "notes": "Nice Group",
                "rate": "520",
                "ccp": "120",
                "travel": "200",
                "bonus": "1000",
                "course_hours": "40",
                "class_time": "2",
                "max_classes": "20 x 2 = 40.0",
                "days": "Monday, Tuesday",
                "dates": [
                    "01/05/2025", "05/05/2025", "06/05/2025", "12/05/2025", "13/05/2025", "14/05/2025", "15/05/2025", "16/05/2025", "17/05/2025", "18/05/2025", "19/05/2025", "20/05/2025", "21/05/2025", "22/05/2025", "23/05/2025", "26/05/2025", "27/05/2025", "02/06/2025", "03/06/2025", "09/06/2025", "10/06/2025", "16/06/2025", "17/06/2025"
                ],
                "cod_cia": "0 COD 0 CIA 0 HOL"
            },
            "students": {
                "S001": {
                    "name": "Paul",
                    "nickname": "Monkey King",
                    "company_no": "A123456",
                    "gender": "Male",
                    "score": "65% B",
                    "pre_test": "58%",
                    "post_test": "98%",
                    "note": "Good Student",
                    "active": "Yes",
                    "attendance": {
                        "14/05/2025": "P", "15/05/2025": "A", "16/05/2025": "P", "17/05/2025": "P", "18/05/2025": "P", "19/05/2025": "P", "20/05/2025": "P", "21/05/2025": "P", "22/05/2025": "P", "23/05/2025": "P", "10/06/2025": "-", "16/06/2025": "-", "27/05/2025": "P", "26/05/2025": "A", "17/06/2025": "-"
                    }
                },
                "S002": {
                    "name": "Jeerapha Suadee",
                    "nickname": "Small Monkey",
                    "company_no": "A321564s",
                    "gender": "Female",
                    "score": "55% D",
                    "pre_test": "55%",
                    "post_test": "85%",
                    "note": "Pain in Butt",
                    "active": "Yes",
                    "attendance": {
                        "01/05/2025": "-", "05/05/2025": "-", "06/05/2025": "-", "12/05/2025": "-", "13/05/2025": "-", "14/05/2025": "-", "15/05/2025": "-", "16/05/2025": "-", "17/05/2025": "-", "18/05/2025": "-", "19/05/2025": "A", "20/05/2025": "P", "21/05/2025": "-", "22/05/2025": "-", "23/05/2025": "P", "26/05/2025": "A", "27/05/2025": "-", "02/06/2025": "-", "03/06/2025": "-", "09/06/2025": "-", "10/06/2025": "-", "16/06/2025": "-", "17/06/2025": "-"
                    }
                }
            },
            "archive": "No"
        }
    }
}
# --- END: Embedded attendance data ---

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
        show_pretest TEXT DEFAULT 'Yes',
        show_posttest TEXT DEFAULT 'Yes',
        show_attn TEXT DEFAULT 'Yes',
        show_p TEXT DEFAULT 'Yes',
        show_a TEXT DEFAULT 'Yes',
        show_l TEXT DEFAULT 'Yes',
        show_note TEXT DEFAULT 'Yes',
        show_dates TEXT DEFAULT 'Yes',  -- NEW: show_dates column
        width_row_number INTEGER DEFAULT 30,
        width_name INTEGER DEFAULT 150,
        width_nickname INTEGER DEFAULT 100,
        width_company_no INTEGER DEFAULT 100,
        width_score INTEGER DEFAULT 65,
        width_pretest INTEGER DEFAULT 65,
        width_posttest INTEGER DEFAULT 65,
        width_attn INTEGER DEFAULT 50,
        width_p INTEGER DEFAULT 30,
        width_a INTEGER DEFAULT 30,
        width_l INTEGER DEFAULT 30,
        width_note INTEGER DEFAULT 150,
        width_date INTEGER DEFAULT 50,
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
    -- --- NEW: Per-form settings table for full customization ---
    CREATE TABLE form_settings (
        form_name TEXT PRIMARY KEY, -- e.g. 'MetadataForm', 'StudentForm', etc.
        window_width INTEGER,
        window_height INTEGER,
        min_width INTEGER,
        min_height INTEGER,
        max_width INTEGER,
        max_height INTEGER,
        resizable TEXT DEFAULT 'yes', -- 'yes' or 'no'
        font_family TEXT,
        font_size INTEGER,
        font_bold TEXT, -- 'yes' or 'no'
        font_italic TEXT, -- 'yes' or 'no'
        fg_color TEXT, -- main text color
        bg_color TEXT, -- main background color
        border_color TEXT,
        title_color TEXT,
        button_bg_color TEXT,
        button_fg_color TEXT,
        button_font_size INTEGER,
        button_border_color TEXT,
        table_bg_color TEXT,
        table_fg_color TEXT,
        table_font_size INTEGER,
        table_header_bg_color TEXT,
        table_header_fg_color TEXT,
        table_header_font_size INTEGER,
        icon_path TEXT,
        extra_json TEXT, -- for future extensibility (JSON-encoded dict)
        last_modified TEXT -- ISO timestamp
    );
    CREATE TABLE factory_defaults (
        scope TEXT,           -- 'global' or 'form'
        form_name TEXT,       -- NULL for global, form name for form
        key TEXT,
        value TEXT,
        PRIMARY KEY (scope, form_name, key)
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
            INSERT OR REPLACE INTO classes (
                class_no, company, consultant, teacher, teacher_no, room, course_book, start_date, finish_date, time, notes, rate, ccp, travel, bonus, course_hours, class_time, max_classes, days, cod_cia, archive,
                show_nickname, show_company_no, show_score, show_pretest, show_posttest, show_attn, show_p, show_a, show_l, show_note,
                show_dates,  -- NEW: show_dates column
                width_row_number, width_name, width_nickname, width_company_no, width_score, width_pretest, width_posttest, width_attn, width_p, width_a, width_l, width_note, width_date,
                bgcolor_p, bgcolor_a, bgcolor_l, bgcolor_cod, bgcolor_cia, bgcolor_hol
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            meta["class_no"], meta["company"], meta["consultant"], meta["teacher"], meta["teacher_no"],
            meta["room"], meta["course_book"], meta["start_date"], meta["finish_date"], meta["time"],
            meta.get("notes", ""), int(meta.get("rate", 0)), int(meta.get("ccp", 0)), int(meta.get("travel", 0)),
            int(meta.get("bonus", 0)), int(meta.get("course_hours", 0)), int(meta.get("class_time", 0)),
            meta.get("max_classes", ""), meta.get("days", ""), meta.get("cod_cia", ""), class_data.get("archive", "No"),
            meta.get("show_nickname", "Yes"), meta.get("show_company_no", "Yes"), meta.get("show_score", "Yes"), meta.get("show_pretest", "Yes"), meta.get("show_posttest", "Yes"), meta.get("show_attn", "Yes"), meta.get("show_p", "Yes"), meta.get("show_a", "Yes"), meta.get("show_l", "Yes"), meta.get("show_note", "Yes"),
            "Yes",  # show_dates default to Yes
            int(meta.get("width_row_number", 30)), int(meta.get("width_name", 150)), int(meta.get("width_nickname", 100)), int(meta.get("width_company_no", 100)), int(meta.get("width_score", 65)), int(meta.get("width_pretest", 65)), int(meta.get("width_posttest", 65)), int(meta.get("width_attn", 50)), int(meta.get("width_p", 30)), int(meta.get("width_a", 30)), int(meta.get("width_l", 30)), int(meta.get("width_note", 150)), int(meta.get("width_date", 50)),
            meta.get("bgcolor_p", "#c8e6c9"), meta.get("bgcolor_a", "#ffcdd2"), meta.get("bgcolor_l", "#fff9c4"), meta.get("bgcolor_cod", "#c8e6c9"), meta.get("bgcolor_cia", "#ffcdd2"), meta.get("bgcolor_hol", "#ffcdd2")
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
        items.insert(idx, ("cod_cia_hol", "0 COD 0 CIA 0 HOL"))
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
    # PATCH: Add color_toggle default if not present
    if "color_toggle" not in defaults:
        defaults["color_toggle"] = "yes"
    # Remove theme from defaults if present
    if "theme" in defaults:
        del defaults["theme"]
    # --- Add display management defaults for window centering/scaling ---
    if "center_windows" not in defaults:
        defaults["center_windows"] = "1"
    if "scale_windows" not in defaults:
        defaults["scale_windows"] = "1"
    if "window_width_ratio" not in defaults:
        defaults["window_width_ratio"] = "0.6"
    if "window_height_ratio" not in defaults:
        defaults["window_height_ratio"] = "0.6"
    cursor = conn.cursor()
    for key, value in defaults.items():
        cursor.execute("INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    print("Imported defaults from default.json")

def import_factory_defaults_table(conn, factory_defaults):
    """Populate factory_defaults table with all global and per-form defaults from factory_defaults.json."""
    cursor = conn.cursor()
    # Global defaults
    for key, value in factory_defaults.get("global", {}).items():
        cursor.execute("INSERT OR REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("global", None, key, str(value)))
    # Per-form defaults
    for form_name, settings in factory_defaults.get("forms", {}).items():
        for key, value in settings.items():
            cursor.execute("INSERT OR REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("form", form_name, key, str(value)))
    conn.commit()
    print("Populated factory_defaults table from factory_defaults.json")

def import_defaults_from_factory(conn, factory_defaults):
    """Import global defaults from factory_defaults.json into defaults table."""
    global_defaults = factory_defaults.get("global", {})
    cursor = conn.cursor()
    for key, value in global_defaults.items():
        cursor.execute("INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    print("Imported global defaults from factory_defaults.json")

def import_form_settings_from_factory(conn, factory_defaults):
    """Import per-form settings from factory_defaults.json into form_settings table, ensuring all fields are present for all forms."""
    forms = factory_defaults.get("forms", {})
    # Get the union of all keys used in any form
    all_fields = set()
    for settings in forms.values():
        all_fields.update(settings.keys())
    all_fields = sorted(all_fields)
    cursor = conn.cursor()
    for form_name, settings in forms.items():
        # For each form, ensure all fields are present (fill missing with None or "")
        values = [settings.get(field, None) for field in all_fields]
        placeholders = ["?"] * len(all_fields)
        sql = f"INSERT OR REPLACE INTO form_settings (form_name, {', '.join(all_fields)}) VALUES (?, {', '.join(placeholders)})"
        cursor.execute(sql, [form_name] + values)
    conn.commit()
    print("Imported per-form settings from factory_defaults.json (all fields ensured)")

def check_factory_defaults_vs_db(conn, factory_defaults, strict=False):
    """
    Compare the DB's defaults and form_settings to those in factory_defaults.json.
    Print warnings or raise error if mismatches are found.
    If strict=True, raise an error on any mismatch.
    Also warn if any field is missing in either direction.
    """
    cursor = conn.cursor()
    # Check global defaults
    db_defaults = dict(cursor.execute("SELECT key, value FROM defaults").fetchall())
    factory_global = factory_defaults.get("global", {})
    mismatches = []
    for key, value in factory_global.items():
        db_val = db_defaults.get(key)
        if str(db_val) != str(value):
            mismatches.append(f"Global default mismatch: {key}: DB='{db_val}' vs Factory='{value}'")
    for key in db_defaults:
        if key not in factory_global:
            mismatches.append(f"Global default in DB but missing in factory_defaults.json: {key}")
    # Check per-form settings
    db_forms = cursor.execute("SELECT form_name FROM form_settings").fetchall()
    db_forms = [row[0] for row in db_forms]
    factory_forms = factory_defaults.get("forms", {})
    # Get the union of all fields in factory
    all_fields = set()
    for settings in factory_forms.values():
        all_fields.update(settings.keys())
    all_fields = sorted(all_fields)
    for form_name, settings in factory_forms.items():
        if form_name not in db_forms:
            mismatches.append(f"Form '{form_name}' missing in DB form_settings table.")
            continue
        db_row = cursor.execute(f"SELECT * FROM form_settings WHERE form_name=?", (form_name,)).fetchone()
        db_columns = [desc[0] for desc in cursor.description]
        db_dict = dict(zip(db_columns, db_row))
        # Check all fields in factory
        for k in all_fields:
            v = settings.get(k, None)
            db_val = db_dict.get(k)
            if str(db_val) != str(v):
                mismatches.append(f"Form '{form_name}' setting mismatch: {k}: DB='{db_val}' vs Factory='{v}'")
        # Check for extra fields in DB not in factory
        for k in db_dict:
            if k not in all_fields and k != "form_name":
                mismatches.append(f"Form '{form_name}' has extra field in DB not in factory_defaults.json: {k}")
    # Warn for forms in DB but not in factory
    for db_form in db_forms:
        if db_form not in factory_forms:
            mismatches.append(f"Form '{db_form}' in DB but missing in factory_defaults.json")
    if mismatches:
        print("\nFactory defaults mismatches found:")
        for m in mismatches:
            print(m)
        if strict:
            raise RuntimeError("Factory defaults do not match DB. See above.")
    else:
        print("Factory defaults match DB.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Bluecard DB and check against factory defaults.")
    parser.add_argument('--strict-factory-check', action='store_true', help='Fail if DB and factory defaults mismatch')
    parser.add_argument('--check-only', action='store_true', help='Only check for mismatches, do not rebuild DB')
    args = parser.parse_args()
    # ...existing code...
    factory_defaults_path = os.path.join(DATA_DIR, "factory_defaults.json")
    with open(factory_defaults_path, "r", encoding="utf-8") as f:
        factory_defaults = json.load(f)
    if args.check_only:
        # Connect to existing DB and check
        if not os.path.exists(DB_PATH):
            print(f"No database found at {DB_PATH} to check.")
            return
        conn = sqlite3.connect(DB_PATH)
        check_factory_defaults_vs_db(conn, factory_defaults, strict=args.strict_factory_check)
        conn.close()
        return
    # ...existing code for full rebuild...
    conn = recreate_db()
    import_data(conn, ATTENDANCE_DATA)
    # Load factory_defaults.json
    factory_defaults_path = os.path.join(DATA_DIR, "factory_defaults.json")
    with open(factory_defaults_path, "r", encoding="utf-8") as f:
        factory_defaults = json.load(f)
    # Use factory_defaults for import_defaults and import_form_settings
    import_defaults_from_factory(conn, factory_defaults)
    import_form_settings_from_factory(conn, factory_defaults)
    import_factory_defaults_table(conn, factory_defaults)
    # Check for mismatches
    check_factory_defaults_vs_db(conn, factory_defaults, strict=args.strict_factory_check)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holidays ORDER BY date")
    holidays = cursor.fetchall()
    print("Holidays in DB:")
    for h in holidays:
        print(h)
    conn.close()

if __name__ == "__main__":
    main()
