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
import logging
from logic import parser
from ui.launcher import Launcher

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SETTINGS_PATH = "data/settings.json"
DEFAULT_THEME = "normal"

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Set to ERROR to suppress DEBUG and WARNING messages
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
    parser.backup_data()
    sys.exit(0)

def start_launcher():
    """Start the Launcher form."""
    theme = load_theme()
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
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
