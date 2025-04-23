# Project Bluecard STR
## Overview
A Python application for managing class data with data entry, validation, and reporting.
## Setup
- Requires Python 3.13
- Install dependencies: `pip install -r requirements.txt`
- Run: `python main.py`
## Notes
- Logs errors to `data/bluecard_errors.log`.
- Executable built with PyInstaller (see `create_exe.bat`).
- Data files: `data/001attendance_data.json`, `data/logo.png`.
- `merge_bluecard.py` merges project files for build purposes.

Project: Bluecard STR
Author: Teacher Paul
Version: 1.0

Overview:
Bluecard STR is a local-first classroom manager for ESL teachers.
It supports class metadata editing, student records, attendance tracking, archiving,
and active/inactive student management. Data is saved locally in JSON format
and can be exported as a standalone `.exe`.

Startup Flow:
1. Apply theme (default: "normal"). Theme options: ["normal", "dark", "light", "clam"]
2. Open the Launcher (Form 4):
    - If [ Open ] → open Mainform (Form 6) with selected class
    - If [ Edit ] → open Metadata form (Form 7) for selected class
    - If [ Add New Class ] → open blank Metadata form (Form 7)
    - If [ Archive ] → prompt user, set archive = "Yes"
    - If [ Archive Manager ] → open Form 5 for managing archived classes
    - If [ TTR ] → placeholder for future feature
    - If [ Settings ] → open theme selector popup
3. Close button prompts user to back up JSON file (future: upload to Google Drive)

Key Modules:
- data/001attendance_data.json → all class and student info
- logic/parser.py              → handles loading/saving JSON
- logic/attendance_utils.py    → scoring and attendance logic
- ui/cli.py                    → command-line or GUI logic
- tests/test_attendance.py     → unit tests
- create_exe.bat               → builds final Windows executable
- merge_bluecard.py            → compiles assets for build

Notes:
- Topmost windows: all forms use `-topmost = True`
- Data is portable and can be merged into one JSON
- Unused buttons are placeholders for future feature expansion
- Errors logged to: `data/bluecard_errors.log`
