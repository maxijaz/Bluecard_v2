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
"""

import os
import json
import signal
import sys
import tkinter as tk
from src.logic import parser
from src.ui.launcher import Launcher

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SETTINGS_PATH = "data/settings.json"
DEFAULT_THEME = "normal"

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

def on_close():
    """Handles cleanup and backup on app close."""
    print("Auto backing up 001attendance_data.JSON to /data/backup")
    parser.backup_data()
    sys.exit(0)

def start_launcher():
    """Start the Launcher form."""
    theme = load_theme()
    print(f"Launching Bluecard_v2 with theme: {theme}")
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    launcher = Launcher(root, theme)
    launcher.mainloop()

if __name__ == "__main__":
    try:
        # Handle Ctrl+C or forced exit
        signal.signal(signal.SIGINT, lambda sig, frame: on_close())
        signal.signal(signal.SIGTERM, lambda sig, frame: on_close())

        start_launcher()
    finally:
        on_close()

print(sys.path)
