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
import shutil
import sys
from PyQt5.QtWidgets import QApplication
from logic import parser
from ui.launcher import Launcher

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SETTINGS_PATH = "data/settings.json"
DEFAULT_THEME = "normal"
TEST_MODE = os.getenv("BLUECARD_TEST_MODE") == "1"  # optional environment toggle

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

        start_launcher()
    except Exception as e:
        parser.log_error(f"An unexpected error occurred: {e}")
        sys.exit(1)
