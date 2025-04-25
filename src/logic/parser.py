import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict

DATA_FILE = "data/001attendance_data.json"
BACKUP_DIR = "data/backup"

def load_data(filepath: str = DATA_FILE) -> Dict[str, Any]:
    """Loads and returns the class and student data from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log_error(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        log_error(f"Invalid JSON format in file: {filepath}")
        return {}

def save_data(data: dict, filepath: str = DATA_FILE) -> None:
    """Saves the provided dictionary back into the JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_error(f"Failed to save data to {filepath}: {e}")

def log_error(message: str) -> None:
    """Logs errors to a file."""
    with open("data/bluecard_errors.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

def validate_class_format(data: dict) -> bool:
    """Enhanced schema validation for class and student data."""
    if "classes" not in data or not isinstance(data["classes"], dict) or not data["classes"]:
        return False  # Ensure "classes" exists, is a dictionary, and is not empty

    for class_id, class_data in data["classes"].items():
        # Validate metadata
        metadata = class_data.get("metadata", {})
        required_metadata_fields = [
            "Company", "Consultant", "Teacher", "Room", "CourseBook",
            "MaxClasses", "CourseHours", "ClassTime", "StartDate", "FinishDate",
            "Days", "Time", "Notes"
        ]
        if not all(field in metadata for field in required_metadata_fields):
            return False

        # Validate students
        students = class_data.get("students", {})
        if not isinstance(students, dict):
            return False
        for student_id, student_data in students.items():
            required_student_fields = [
                "name", "gender", "nickname", "score", "pre_test", "post_test",
                "active", "note", "attendance"
            ]
            if not all(field in student_data for field in required_student_fields):
                return False

    return True

def backup_data() -> None:
    """Creates a timestamped backup of the JSON data file."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    if os.path.exists(DATA_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"001attendance_data_{timestamp}.json"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy(DATA_FILE, backup_path)
        print("Auto backing up 001attendance_data.JSON to /data/backup")  # Flash message equivalent
        cleanup_old_backups()
    else:
        log_error(f"Backup failed. Source file not found: {DATA_FILE}")

def cleanup_old_backups(days: int = 90) -> None:
    """Deletes backup files older than the specified number of days."""
    now = datetime.now()
    if not os.path.exists(BACKUP_DIR):
        return  # If the backup directory doesn't exist, nothing to clean up

    for filename in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, filename)
        if os.path.isfile(file_path):
            # Extract the timestamp from the filename
            try:
                timestamp_str = filename.split("_")[-1].replace(".json", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                # Check if the file is older than the specified number of days
                if (now - file_date).days > days:
                    os.remove(file_path)
            except ValueError:
                # Skip files that don't match the expected timestamp format
                continue
