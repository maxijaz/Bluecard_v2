import sqlite3
from pathlib import Path

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
    conn = get_connection()
    cursor = conn.cursor()
    assignments = ', '.join([f"{k}=?" for k in class_data.keys()])
    cursor.execute(
        f"UPDATE classes SET {assignments} WHERE class_no = ?",
        tuple(class_data.values()) + (class_no,)
    )
    conn.commit()
    conn.close()

def insert_student(student_data):
    """Insert a new student into the database."""
    conn = get_connection()
    cursor = conn.cursor()
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
    """Set or update a default value in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()
    conn.close()

def set_all_defaults(defaults_dict):
    """Set or update multiple defaults in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in defaults_dict.items():
        cursor.execute(
            "INSERT OR REPLACE INTO defaults (key, value) VALUES (?, ?)",
            (key, str(value))
        )
    conn.commit()
    conn.close()
