import os
import shutil
from datetime import datetime
from typing import Any, Dict

from logic.db_interface import (
    get_all_classes,
    get_class_by_id,
    get_students_by_class,
    get_attendance_by_student,
    get_holidays,
)

# DATA_FILE and BACKUP_DIR are now obsolete for DB usage

def load_data() -> Dict[str, Any]:
    """Fetch all classes and their students from the database."""
    classes = {}
    show_hide_fields = [
        "show_nickname", "show_company_no", "show_score", "show_pre_test",
        "show_post_test", "show_attn", "show_p", "show_a", "show_l"
    ]
    for class_row in get_all_classes():
        class_no = class_row["class_no"]
        students = {}
        for student_row in get_students_by_class(class_no):
            student_id = student_row["student_id"]
            attendance_records = get_attendance_by_student(student_id)
            attendance = {rec["date"]: rec["status"] for rec in attendance_records}
            student_row["attendance"] = attendance
            students[student_id] = student_row
        class_row["students"] = students

        # Ensure show/hide fields are present (default to "Yes" if missing)
        for field in show_hide_fields:
            class_row[field] = class_row.get(field, "Yes")

        classes[class_no] = class_row
    return {"classes": classes}

def save_data(data: dict, filepath: str = None) -> None:
    """Saving is now handled by db_interface insert/update functions. This is a no-op."""
    print("[INFO] save_data is now handled by db_interface. No action taken.")

def log_error(message: str) -> None:
    """Logs errors to a file."""
    with open("data/bluecard_errors.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

def validate_class_format(data: dict) -> bool:
    """Enhanced schema validation for class and student data."""
    if "classes" not in data or not isinstance(data["classes"], dict) or not data["classes"]:
        return False  # Ensure "classes" exists, is a dictionary, and is not empty

    for class_id, class_data in data["classes"].items():
        # Validate metadata (now top-level fields)
        required_metadata_fields = [
            "class_no", "company", "consultant", "teacher", "teacher_no", "room", "course_book",
            "start_date", "finish_date", "time", "notes", "rate", "ccp", "travel", "bonus",
            "course_hours", "class_time", "max_classes", "days", "dates", "cod_cia",
            "show_nickname", "show_company_no", "show_score", "show_pre_test",
            "show_post_test", "show_attn", "show_p", "show_a", "show_l"
        ]
        if not all(field in class_data for field in required_metadata_fields):
            return False

        # Validate students
        students = class_data.get("students", {})
        if not isinstance(students, dict):
            return False
        for student_id, student_data in students.items():
            required_student_fields = [
                "name", "nickname", "gender", "score", "pre_test", "post_test",
                "note", "active", "attendance"
            ]
            if not all(field in student_data for field in required_student_fields):
                return False

    return True

def backup_data() -> None:
    """Backups are not needed for the SQLite DB in this function. Use DB backup tools if needed."""
    print("[INFO] backup_data is not implemented for SQLite DB. Use external backup tools.")

def cleanup_old_backups(days: int = 90) -> None:
    """No-op for SQLite DB."""
    pass

def generate_next_student_id(students: dict) -> str:
    """Generate the next unique student ID."""
    if not students:
        return "S001"  # Start with S001 if no students exist
    existing_ids = [int(sid[1:]) for sid in students.keys() if sid.startswith("S")]
    next_id = max(existing_ids, default=0) + 1
    return f"S{next_id:03d}"  # Format as S001, S002, etc.
