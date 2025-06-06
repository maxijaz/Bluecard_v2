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
from logic.db_interface import get_form_settings, get_all_defaults
from ui.launcher import Launcher

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DEFAULT_THEME = "normal"
TEST_MODE = os.getenv("BLUECARD_TEST_MODE") == "1"  # optional environment toggle

def get_theme():
    """Get UI theme from DB defaults, fallback to DEFAULT_THEME."""
    try:
        defaults = get_all_defaults()
        return defaults.get("theme", DEFAULT_THEME)
    except Exception:
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
    theme = get_theme()
    app = QApplication(sys.argv)
    # --- PATCH: Load per-form settings for Launcher ---
    try:
        form_settings = get_form_settings("Launcher") or {}
        from PyQt5.QtGui import QFont
        default_settings = get_all_defaults()
        def get_setting(key, fallback):
            val = form_settings.get(key)
            if val is not None and str(val).strip() != "":
                return val
            return default_settings.get(key, fallback)
        form_font_size = int(get_setting("font_size", 12))
        font_family = get_setting("font_family", "Segoe UI")
        app.setFont(QFont(font_family, form_font_size))
    except Exception as e:
        print(f"[WARN] Could not apply per-form settings for Launcher: {e}")
    try:
        launcher = Launcher(theme)
    except Exception as e:
        print(f"[ERROR] Failed to create Launcher: {e}")
        from PyQt5.QtWidgets import QMainWindow, QLabel
        class FallbackWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Bluecard Fallback Window")
                label = QLabel("Launcher failed to load.\nError: {}".format(e), self)
                label.setStyleSheet("color: red; font-size: 16px;")
                self.setCentralWidget(label)
        launcher = FallbackWindow()
    global _launcher_ref
    _launcher_ref = launcher  # Prevent garbage collection
    launcher.show()
    print("[INFO] Launcher (or fallback) window shown.")
    exit_code = app.exec_()
    print(f"[INFO] QApplication exited with code {exit_code}")
    sys.exit(exit_code)

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
