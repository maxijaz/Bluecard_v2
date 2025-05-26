"""
Project: Bluecard_v2
Author: Teacher Paul
Version: 2.0

Overview:
Bluecard_v2 is a local-first classroom manager for ESL teachers.
This script loads the app theme, opens the launcher window, and ensures data is backed up on close.

Features:
- Theme loading from settings.json
- Launcher entry point
- Auto-backup of data to /data/backup/ on close
- Clean test run environment (optional)
"""

import os
import json
import signal
import shutil
import sys
import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from logic import parser
from ui.launcher import Launcher

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SETTINGS_PATH = "data/settings.json"
DEFAULT_THEME = "normal"
TEST_MODE = os.getenv("BLUECARD_TEST_MODE") == "1"  # optional environment toggle

DB_PATH = os.path.join("data", "001attendance.db")
BACKUP_DIR = os.path.join("data", "backup")

def load_theme():
    """Loads UI theme from settings.json, fallback to default."""
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_THEME
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
            return settings.get("theme", DEFAULT_THEME)
    except json.JSONDecodeError:
        return DEFAULT_THEME

def clean_environment():
    """Clean temp/test files and folders before a run."""
    temp_paths = ["data/temp", "data/.cache", "__pycache__", "data/test_output"]
    for path in temp_paths:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"✅ Cleaned: {path}")
            except Exception as e:
                parser.log_error(f"Failed to clean {path}: {e}")

def backup_sqlite_db():
    """Backup the SQLite DB to /data/backup/ with a timestamp."""
    if not os.path.exists(DB_PATH):
        print("No database file found to backup.")
        return
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"001attendance_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Database backed up to {backup_path}")

def on_close():
    """Handles cleanup and backup on app close."""
    try:
        app = QApplication.instance()
        if app is not None:
            reply = QMessageBox.question(
                None,
                "Backup Database",
                "Would you like to backup the database before exiting?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                backup_sqlite_db()
        print("✅ Backup prompt completed.")
    except Exception as e:
        parser.log_error(f"Backup failed: {e}")
    finally:
        sys.exit(0)

def start_launcher():
    """Start the Launcher form."""
    theme = load_theme()
    app = QApplication(sys.argv)
    launcher = Launcher(theme)
    launcher.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        # Optional: clean up environment for testing
        if TEST_MODE:
            print("🔄 Running in TEST MODE: Cleaning environment...")
            clean_environment()

        # Register shutdown signals
        signal.signal(signal.SIGINT, lambda sig, frame: on_close())
        signal.signal(signal.SIGTERM, lambda sig, frame: on_close())

        start_launcher()
    except Exception as e:
        parser.log_error(f"An unexpected error occurred: {e}")
        sys.exit(1)
