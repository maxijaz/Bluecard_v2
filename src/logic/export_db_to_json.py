import os
import sqlite3
import json

# output 001attendance.db to 001attendance_data.json
# Paths
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "001attendance.db")
OUTPUT_JSON = os.path.join(DATA_DIR, "001attendance_data.json")  # Changed output filename

def export_db_to_json(db_path=DB_PATH, output_json=OUTPUT_JSON):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    data = {"classes": {}}

    # Get all classes
    cur.execute("SELECT * FROM classes")
    for class_row in cur.fetchall():
        class_no = class_row["class_no"]
        metadata = dict(class_row)
        students = {}
        # Get all students for this class
        cur.execute("SELECT * FROM students WHERE class_no = ? ORDER BY student_id", (class_no,))
        for idx, student_row in enumerate(cur.fetchall(), 1):
            # Use S001, S002, ... as keys
            student_key = f"S{idx:03d}"
            student = dict(student_row)
            student.pop("class_no", None)
            student.pop("student_id", None)
            # Stringify all fields except attendance
            for k in list(student.keys()):
                student[k] = str(student[k]) if student[k] is not None else ""
            # Attendance for this student
            attendance = {}
            cur.execute("SELECT date, status FROM attendance WHERE class_no = ? AND student_id = ?", (class_no, student_row["student_id"]))
            for attn_row in cur.fetchall():
                attendance[attn_row["date"]] = attn_row["status"]
            student["attendance"] = attendance
            students[student_key] = student
        # Dates for this class
        cur.execute("SELECT date FROM dates WHERE class_no = ? ORDER BY date", (class_no,))
        dates = [row["date"] for row in cur.fetchall()]
        metadata["dates"] = dates
        # Stringify all metadata fields except 'dates'
        for k in list(metadata.keys()):
            if k != "dates":
                metadata[k] = str(metadata[k]) if metadata[k] is not None else ""
        data["classes"][class_no] = {
            "metadata": metadata,
            "students": students
        }
    # Write to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[INFO] Exported DB to JSON: {output_json}")

if __name__ == "__main__":
    export_db_to_json()
