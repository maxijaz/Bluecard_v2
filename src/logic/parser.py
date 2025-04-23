
import os
import json
import shutil
from datetime import datetime, timedelta

DATA_FILE = "data/001attendance_data.json"
BACKUP_DIR = "data/backup"

def load_data(filepath=DATA_FILE):
    """Loads and returns the class and student data from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data, filepath=DATA_FILE):
    """Saves the provided dictionary back into the JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def validate_class_format(data):
    """Simple schema check to ensure data has expected keys."""
    return "classes" in data and isinstance(data["classes"], dict)

def backup_data():
    """Creates a timestamped backup of the JSON data file."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"001attendance_data_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    shutil.copy(DATA_FILE, backup_path)
    print("Auto backing up 001attendance_data.JSON to /data/backup")  # Flash message equivalent
    cleanup_old_backups()

def cleanup_old_backups(days=90):
    """Deletes backup files older than the specified number of days."""
    now = datetime.now()
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith("001attendance_data_") and filename.endswith(".json"):
            filepath = os.path.join(BACKUP_DIR, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (now - file_time) > timedelta(days=days):
                os.remove(filepath)
