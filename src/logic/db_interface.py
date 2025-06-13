import sqlite3
from pathlib import Path
import logging

# Dynamically resolve the path to the database
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "001attendance.db"

def get_connection():
    """Return a SQLite connection with rows as dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_classes():
    """Fetch all class records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classes")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_class_by_id(class_no):
    """Fetch a specific class by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classes WHERE class_no = ?", (class_no,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_students_by_class(class_no):
    """Fetch all students belonging to a class."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE class_no = ?", (class_no,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_attendance_by_student(student_id):
    """Fetch attendance records for a specific student."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance WHERE student_id = ?", (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_holidays():
    """Fetch the list of Thai holidays."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM holidays ORDER BY date")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def set_class_archived(class_no, archived=True):
    """Set the archive status of a class."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE classes SET archive = ? WHERE class_no = ?",
        ("Yes" if archived else "No", class_no)
    )
    conn.commit()
    conn.close()

def insert_class(class_data):
    """Insert a new class into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = ', '.join(class_data.keys())
    placeholders = ', '.join(['?'] * len(class_data))
    cursor.execute(
        f"INSERT INTO classes ({fields}) VALUES ({placeholders})",
        tuple(class_data.values())
    )
    conn.commit()
    conn.close()

def update_class(class_no, class_data):
    """Update an existing class in the database."""
    # print(f"[DEBUG] update_class: Attempting to update {class_no} with: {class_data}")
    conn = get_connection()
    cursor = conn.cursor()
    # Print current values before update
    cursor.execute("SELECT * FROM classes WHERE class_no = ?", (class_no,))
    before = cursor.fetchone()
    # print(f"[DEBUG] update_class: Before update: {before}")
    assignments = ', '.join([f"{k}=?" for k in class_data.keys()])
    cursor.execute(
        f"UPDATE classes SET {assignments} WHERE class_no = ?",
        tuple(class_data.values()) + (class_no,)
    )
    conn.commit()
    # Print values after update
    cursor.execute("SELECT * FROM classes WHERE class_no = ?", (class_no,))
    after = cursor.fetchone()
    # print(f"[DEBUG] update_class: After update: {after}")
    conn.close()

def insert_student(student_data):
    """Insert a new student into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    student_data = dict(student_data)
    student_data.pop("student_id", None)  # Let SQLite auto-assign
    fields = ', '.join(student_data.keys())
    placeholders = ', '.join(['?'] * len(student_data))
    cursor.execute(
        f"INSERT INTO students ({fields}) VALUES ({placeholders})",
        tuple(student_data.values())
    )
    conn.commit()
    conn.close()

def update_student(student_id, student_data):
    """Update an existing student in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    assignments = ', '.join([f"{k}=?" for k in student_data.keys()])
    cursor.execute(
        f"UPDATE students SET {assignments} WHERE student_id = ?",
        tuple(student_data.values()) + (student_id,)
    )
    conn.commit()
    conn.close()

def delete_student(student_id):
    """Delete a student from the database by student_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    # Optionally, also delete attendance records for this student:
    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

def delete_class(class_no):
    """Delete a class and all associated students and attendance from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE class_no = ?", (class_no,))
    cursor.execute("DELETE FROM students WHERE class_no = ?", (class_no,))
    cursor.execute("DELETE FROM attendance WHERE class_no = ?", (class_no,))
    conn.commit()
    conn.close()

def get_default(key):
    """Fetch a single default value by key."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM defaults WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None

def get_all_defaults():
    """Fetch all defaults as a dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM defaults")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_default(key, value):
    """Set or update a default value in the database (including color_toggle)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def set_all_defaults(defaults_dict):
    """Set or update multiple defaults in the database (including color_toggle)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Add logging for defaults_dict
    logging.debug(f"Defaults dictionary passed: {defaults_dict}")
    for key, value in defaults_dict.items():
        # Add logging to debug database operations
        logging.debug(f"Setting default: {key} = {value}")
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)",
                (key, str(value))
            )
        except Exception as e:
            logging.error(f"Error inserting default {key}: {e}")
    # Add logging to confirm transaction success
    try:
        conn.commit()
        logging.debug("Transaction committed successfully.")
    except Exception as e:
        logging.error(f"Error committing transaction: {e}")
    finally:
        conn.close()

def insert_date(class_no, date, note=""):
    """Insert a date for a class into the dates table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO dates (class_no, date, note) VALUES (?, ?, ?)",
        (class_no, date, note)
    )
    conn.commit()
    conn.close()

def delete_date(class_no, date):
    """Delete a date for a class from the dates table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM dates WHERE class_no = ? AND date = ?",
        (class_no, date)
    )
    conn.commit()
    conn.close()

def set_attendance(class_no, student_id, date, status):
    """Set or update attendance for a student on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO attendance (class_no, student_id, date, status) VALUES (?, ?, ?, ?)",
        (class_no, student_id, date, status)
    )
    conn.commit()
    conn.close()

def get_form_settings(form_name):
    """Fetch per-form settings as a dict for the given form_name (e.g., 'MetadataForm')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM form_settings WHERE form_name = ?", (form_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_form_settings(form_name, settings_dict):
    """Insert or update per-form settings for the given form_name. settings_dict keys must match table columns (except form_name)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Remove form_name if present in dict
    settings = dict(settings_dict)
    settings.pop("form_name", None)
    columns = ["form_name"] + list(settings.keys())
    placeholders = ["?"] * len(columns)
    values = [form_name] + [settings[k] for k in settings.keys()]
    assignments = ', '.join([f"{k}=?" for k in settings.keys()])
    # Try update first, then insert if not exists
    cursor.execute(f"UPDATE form_settings SET {assignments} WHERE form_name = ?", values[1:] + [form_name])
    if cursor.rowcount == 0:
        cursor.execute(f"INSERT INTO form_settings ({', '.join(columns)}) VALUES ({', '.join(placeholders)})", values)
    conn.commit()
    conn.close()

def get_teacher_defaults():
    """Fetch all teacher defaults as a dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM teacher_defaults")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_teacher_defaults(new_defaults):
    """Set or update multiple teacher defaults in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in new_defaults.items():
        cursor.execute("INSERT OR REPLACE INTO teacher_defaults (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_message_defaults():
    """Fetch message style defaults as a dict from the defaults table."""
    conn = get_connection()
    cursor = conn.cursor()
    keys = [
        "message_bg_color", "message_fg_color", "message_border_color", "message_border_width",
        "message_border_radius", "message_padding", "message_font_size", "message_font_bold"
    ]
    d = {}
    for key in keys:
        cursor.execute("SELECT value FROM defaults WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            d[key] = row["value"]
    conn.close()
    return d

def get_dates_by_class(class_no):
    """Fetch all dates for a class from the dates table, sorted chronologically."""
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM dates WHERE class_no = ?", (class_no,))
    rows = cursor.fetchall()
    conn.close()
    # Return as a list of date strings, sorted chronologically if possible
    date_list = [row[0] for row in rows]
    def date_key(d):
        try:
            return datetime.strptime(d, "%d/%m/%Y")
        except Exception:
            return d  # fallback for placeholders or invalid dates
    return sorted(date_list, key=date_key)

def get_factory_defaults():
    """Fetch all factory defaults as a nested dict (mirroring factory_defaults.json structure)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Get class defaults (scope = 'class', form_name IS NULL)
    cursor.execute("SELECT key, value FROM factory_defaults WHERE scope = 'class' AND form_name IS NULL")
    classes_default = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return {"classes": {"default": classes_default}}
