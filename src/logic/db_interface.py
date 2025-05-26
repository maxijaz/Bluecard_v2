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
