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

# --- BEGIN: Load attendance data from external JSON file ---
FACTORY_STUDENTS_JSON = os.path.join(DATA_DIR, "factory_students.json")

def load_factory_students():
    if not os.path.exists(FACTORY_STUDENTS_JSON):
        print(f"Sample data file not found: {FACTORY_STUDENTS_JSON}")
        return None
    with open(FACTORY_STUDENTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
# --- END: Load attendance data from external JSON file ---

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
        teacher TEXT,  -- def_teacher from teacher_defaults.json
        teacher_no TEXT,  -- def_teacher_no from teacher_defaults.json
        room TEXT,
        course_book TEXT,
        start_date TEXT,
        finish_date TEXT,
        time TEXT,
        notes TEXT,
        rate INTEGER,  -- def_rate from teacher_defaults.json
        ccp INTEGER,  -- def_ccp from teacher_defaults.json
        travel INTEGER,  -- def_travel from teacher_defaults.json
        bonus INTEGER,  -- def_bonus from teacher_defaults.json
        course_hours INTEGER,  -- def_coursehours from teacher_defaults.json
        class_time INTEGER,  -- def_classtime from teacher_defaults.json
        max_classes TEXT,
        days TEXT,
        cod_cia TEXT,
        archive TEXT,
        show_nickname TEXT,
        show_company_no TEXT,
        show_score TEXT,
        show_pretest TEXT,
        show_posttest TEXT,
        show_attn TEXT,
        show_p TEXT,
        show_a TEXT,
        show_l TEXT,
        show_note TEXT,
        show_dates TEXT,
        width_row_number INTEGER,
        width_name INTEGER,
        width_nickname INTEGER,
        width_company_no INTEGER,
        width_score INTEGER,
        width_pretest INTEGER,
        width_posttest INTEGER,
        width_attn INTEGER,
        width_p INTEGER,
        width_a INTEGER,
        width_l INTEGER,
        width_note INTEGER,
        width_date INTEGER,
        bgcolor_p TEXT,
        bgcolor_a TEXT,
        bgcolor_l TEXT,
        bgcolor_cod TEXT,
        bgcolor_cia TEXT,
        bgcolor_hol TEXT
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
    CREATE TABLE teacher_defaults (
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
        resizable TEXT DEFAULT 'yes', -- 'yes' or 'no'
        window_controls TEXT,
        form_font_family TEXT,
        title_color TEXT,
        title_font_size INTEGER,
        title_font_bold TEXT, -- 'yes' or 'no'
        title_alignment TEXT,
        subtitle_color TEXT,
        subtitle_font_size INTEGER,
        subtitle_font_bold TEXT, -- 'yes' or 'no'
        subtitle_alignment TEXT,
        form_bg_color TEXT,
        form_fg_color TEXT,
        form_border_color TEXT,
        form_font_size INTEGER,
        form_label_bold TEXT, -- 'yes' or 'no'
        form_label_alignment TEXT,
        form_input_bg_color TEXT,
        form_input_alignment TEXT,
        form_input_field_bold TEXT, -- 'yes' or 'no'
        form_input_placeholder_color TEXT,
        form_input_focus_border_color TEXT,
        form_input_disabled_bg_color TEXT,
        form_error_border_color TEXT,
        metadata_bg_color TEXT,
        metadata_fg_color TEXT,
        metadata_border_color TEXT,
        metadata_font_size INTEGER,
        metadata_label_bold TEXT, -- 'yes' or 'no'
        metadata_input_field_bold TEXT, -- 'yes' or 'no'
        metadata_input_bg_color TEXT,
        metadata_input_placeholder_color TEXT,
        metadata_input_focus_border_color TEXT,
        metadata_input_disabled_bg_color TEXT,
        metadata_error_border_color TEXT,
        table_header_bg_color TEXT,
        table_header_fg_color TEXT,
        table_header_border_color TEXT,
        table_header_font_size INTEGER,
        table_header_bold TEXT, -- 'yes' or 'no'
        table_bg_color TEXT,
        table_fg_color TEXT,
        table_border_color TEXT,
        table_font_size INTEGER,
        table_input_field_bold TEXT, -- 'yes' or 'no'
        table_error_border_color TEXT,
        button_bg_color TEXT,
        button_fg_color TEXT,
        button_border_color TEXT,
        button_font_size INTEGER,
        button_font_bold TEXT, -- 'yes' or 'no'
        button_hover_bg_color TEXT,
        button_active_bg_color TEXT,
        button_error_border_color TEXT
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

    # Ensure defaults are loaded from teacher_defaults.json
    defaults_path = os.path.join(DATA_DIR, "teacher_defaults.json")
    if not os.path.exists(defaults_path):
        print(f"No teacher_defaults.json found at {defaults_path}")
        return
    with open(defaults_path, "r", encoding="utf-8") as f:
        defaults = json.load(f)

    # --- PATCH: Insert teacher_defaults into teacher_defaults table ---
    teacher_defaults = {
        "def_teacher": defaults.get("def_teacher", "Paul R"),
        "def_teacher_no": defaults.get("def_teacher_no", "A20049"),
        "def_coursehours": defaults.get("def_coursehours", "40"),
        "def_classtime": defaults.get("def_classtime", "2"),
        "def_rate": defaults.get("def_rate", "520"),
        "def_ccp": defaults.get("def_ccp", "120"),
        "def_travel": defaults.get("def_travel", "200"),
        "def_bonus": defaults.get("def_bonus", "1000")
    }
    cursor.executemany("INSERT OR REPLACE INTO teacher_defaults (key, value) VALUES (?, ?)", teacher_defaults.items())
    print("Inserted teacher defaults")

    cursor.executemany("INSERT INTO holidays VALUES (?, ?)", thai_holidays)
    print("Inserted Thai holidays")

    conn.commit()
    return conn

def merge_metadata_with_defaults(meta, class_defaults):
    """Merge class metadata with defaults. Precedence: meta > class_defaults > fallback."""
    fallback = {
        "company": "",
        "consultant": "",
        "teacher": "",
        "teacher_no": "",
        "room": "",
        "course_book": "",
        "start_date": "",
        "finish_date": "",
        "time": "",
        "notes": "",
        "rate": "0",
        "ccp": "0",
        "travel": "0",
        "bonus": "0",
        "course_hours": "0",
        "class_time": "0",
        "days": "",
        "cod_cia": "",
        "dates": []
    }
    merged = dict(fallback)
    merged.update({k: v for k, v in class_defaults.items() if v not in (None, "")})
    merged.update({k: v for k, v in meta.items() if v not in (None, "")})
    return merged

def import_data(conn, data, factory_defaults=None):
    cursor = conn.cursor()
    class_defaults = factory_defaults.get("classes", {}).get("default", {}) if factory_defaults else {}
    for class_no, class_data in data["classes"].items():
        meta = class_data["metadata"]
        meta = merge_metadata_with_defaults(meta, class_defaults)
        cursor.execute("""
            INSERT OR REPLACE INTO classes (
                class_no, company, consultant, teacher, teacher_no, room, course_book, start_date, finish_date, time, notes, rate, ccp, travel, bonus, course_hours, class_time, max_classes, days, cod_cia, archive,
                show_nickname, show_company_no, show_score, show_pretest, show_posttest, show_attn, show_p, show_a, show_l, show_note,
                show_dates,
                width_row_number, width_name, width_nickname, width_company_no, width_score, width_pretest, width_posttest, width_attn, width_p, width_a, width_l, width_note, width_date,
                bgcolor_p, bgcolor_a, bgcolor_l, bgcolor_cod, bgcolor_cia, bgcolor_hol
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            meta["class_no"], meta["company"], meta["consultant"], meta["teacher"], meta["teacher_no"],
            meta["room"], meta["course_book"], meta["start_date"], meta["finish_date"], meta["time"],
            meta.get("notes", ""), int(meta.get("rate", 0)), int(meta.get("ccp", 0)), int(meta.get("travel", 0)),
            int(meta.get("bonus", 0)), int(meta.get("course_hours", 0)), int(meta.get("class_time", 0)),
            meta["max_classes"], meta.get("days", ""), meta.get("cod_cia", ""), meta["archive"],
            meta["show_nickname"], meta["show_company_no"], meta["show_score"], meta["show_pretest"], meta["show_posttest"], meta["show_attn"], meta["show_p"], meta["show_a"], meta["show_l"], meta["show_note"],
            meta["show_dates"],
            int(meta["width_row_number"]), int(meta["width_name"]), int(meta["width_nickname"]), int(meta["width_company_no"]), int(meta["width_score"]), int(meta["width_pretest"]), int(meta["width_posttest"]), int(meta["width_attn"]), int(meta["width_p"]), int(meta["width_a"]), int(meta["width_l"]), int(meta["width_note"]), int(meta["width_date"]),
            meta["bgcolor_p"], meta["bgcolor_a"], meta["bgcolor_l"], meta["bgcolor_cod"], meta["bgcolor_cia"], meta["bgcolor_hol"]
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

def import_defaults_from_factory(conn, factory_defaults):
    """
    Import global defaults from factory_defaults.json into the defaults table.
    """
    cursor = conn.cursor()
    global_defaults = factory_defaults.get("global", {})
    def normalize_value(val):
        if isinstance(val, bool):
            return "True" if val else "False"
        return str(val)
    for key, value in global_defaults.items():
        cursor.execute("REPLACE INTO defaults (key, value) VALUES (?, ?)", (key, normalize_value(value)))
    conn.commit()

def import_form_settings_from_factory(conn, factory_defaults):
    """
    Import per-form settings from factory_defaults.json into the form_settings table.
    """
    cursor = conn.cursor()
    forms = factory_defaults.get("forms", {})
    for form_name, form_settings in forms.items():
        columns = [
            "form_name", "window_width", "window_height", "min_width", "min_height",
            "resizable", "window_controls", "form_font_family", "title_color", "title_font_size", "title_font_bold", "title_alignment",
            "subtitle_color", "subtitle_font_size", "subtitle_font_bold", "subtitle_alignment", "form_bg_color", "form_fg_color", "form_border_color",
            "form_font_size", "form_label_bold", "form_label_alignment", "form_input_bg_color", "form_input_alignment", "form_input_field_bold",
            "form_input_placeholder_color", "form_input_focus_border_color", "form_input_disabled_bg_color", "form_error_border_color",
            "metadata_bg_color", "metadata_fg_color", "metadata_border_color", "metadata_font_size", "metadata_label_bold", "metadata_input_field_bold",
            "metadata_input_bg_color", "metadata_input_placeholder_color", "metadata_input_focus_border_color", "metadata_input_disabled_bg_color",
            "metadata_error_border_color", "table_header_bg_color", "table_header_fg_color", "table_header_border_color", "table_header_font_size",
            "table_header_bold", "table_bg_color", "table_fg_color", "table_border_color", "table_font_size", "table_input_field_bold",
            "table_error_border_color", "button_bg_color", "button_fg_color", "button_border_color", "button_font_size", "button_font_bold",
            "button_hover_bg_color", "button_active_bg_color", "button_error_border_color"
        ]
        def normalize_value(val):
            if isinstance(val, bool):
                return "True" if val else "False"
            return str(val)
        values = [form_name] + [normalize_value(form_settings.get(col, None)) for col in columns[1:]]
        placeholders = ','.join(['?'] * len(columns))
        cursor.execute(f"REPLACE INTO form_settings ({','.join(columns)}) VALUES ({placeholders})", values)
    conn.commit()

def import_class_defaults_from_factory(conn, factory_defaults):
    """
    Import per-class defaults from factory_defaults.json into the classes table as templates (for new classes).
    """
    cursor = conn.cursor()
    class_defaults = factory_defaults.get("classes", {}).get("default", {})
    # This function can be expanded to insert into a class_templates table if needed
    # For now, just store in factory_defaults table for reference
    for key, value in class_defaults.items():
        cursor.execute("REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("class", None, key, json.dumps(value)))
    conn.commit()

def import_factory_defaults_table(conn, factory_defaults):
    """
    Import all factory defaults into the factory_defaults table for reference and reset.
    """
    cursor = conn.cursor()
    def normalize_bool(val):
        if isinstance(val, bool):
            return "True" if val else "False"
        if isinstance(val, int):
            return str(val)
        if str(val).lower() in ("true", "yes"): return "True"
        if str(val).lower() in ("false", "no"): return "False"
        return val
    # Global
    for key, value in factory_defaults.get("global", {}).items():
        cursor.execute("REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("global", None, key, str(normalize_bool(value))))
    # Forms
    for form_name, form_settings in factory_defaults.get("forms", {}).items():
        for key, value in form_settings.items():
            cursor.execute("REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("form", form_name, key, str(normalize_bool(value))))
    # Classes
    for key, value in factory_defaults.get("classes", {}).get("default", {}).items():
        cursor.execute("REPLACE INTO factory_defaults (scope, form_name, key, value) VALUES (?, ?, ?, ?)", ("class", None, key, str(normalize_bool(value))))
    conn.commit()

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

    # --- FULL REBUILD ---
    conn = recreate_db()
    # Import all settings from factory_defaults.json
    import_defaults_from_factory(conn, factory_defaults)
    import_form_settings_from_factory(conn, factory_defaults)
    import_class_defaults_from_factory(conn, factory_defaults)
    import_factory_defaults_table(conn, factory_defaults)

    # Load sample attendance/class/student data from factory_students.json
    sample_data = load_factory_students()
    if sample_data:
        import_data(conn, sample_data)
    else:
        print("No sample attendance/class/student data loaded.")

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
