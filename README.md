
# Project Bluecard_v2

## Overview
Bluecard_v2 is a local-first Python application for managing ESL class data.  
It supports editable class metadata, student attendance tracking, archive handling, and student activity control.  
Built to be portable, offline, and eventually packaged as a standalone `.exe` for fellow teachers.

## Setup
- Requires: Python 3.13+
- Install dependencies:
  ```
  pip install -r requirements.txt
  ```
- Run the app:
  ```
  python src/main.py
  ```

## Features
- Add/edit class metadata (company, room, schedule, etc.)
- Add/edit students with attendance and performance tracking
- Mark students active/inactive
- Archive and restore whole classes
- Settings: Theme selector (normal, dark, clam, etc.)
- Launch from a single `.exe` (via PyInstaller)

## Startup Flow
```text
1. main.py → loads theme
2. Launcher window opens:
   - [ Open ] → Mainform
   - [ Edit ] → Metadata Form
   - [ Add New Class ] → Blank Metadata Form
   - [ Archive ] → set archive = "Yes"
   - [ Archive Manager ] → manage archived classes
   - [ TTR ] → placeholder (future feature)
   - [ Settings ] → Theme picker
3. On Close → prompt to back up data (JSON)
```

# Update the existing README.md file with a reference to parser.py and the /data/backup directory.

readme_update = """
## Data Management & Backup

All class and student data is stored in `data/001attendance_data.json`. The parser module handles:
- Loading and saving JSON (`parser.load_data()` / `parser.save_data()`)
- Validating data format (`parser.validate_class_format()`)
- Auto-backups to `data/backup/` with timestamped copies upon app closure
- Automatic cleanup of backups older than 90 days

## Updated Project Structure
```plaintext
📁 Bluecard_v2/
├── data/
│   ├── 001attendance_data.json
│   ├── 001attendance_data_YYYYMMDD_HHMMSS.json ← (backup with TimeStamp)
│   ├── themes.json ← (from old bluecard)
│   ├── settings.json
│   ├── default.json
│   ├── Project_Outline.txt ← (keep for documentation/reference)
│   └── backup/
│   └── (timestamped .json backups)

├── src/
│   ├── 
│   ├── logic/
│   │   └── parser.py
│   │   
│   └── ui/
│   ├── launcher.py (GUI or interactive launcher in progress)
│   ├── archive_manager.py
│   ├── mainform.py
│   ├── metadata_form.py
│   ├── settings.py
│   └── student_manager.py
│
├── tests/
│   └── test_attendance.py
│
├── .gitignore ← (from old bluecard)
├── main.py
├── requirements.txt
└── README.md 

## Notes
- All errors are logged to: `data/bluecard_errors.log`
- Data is stored locally for portability
- UI will support `-topmost = True` on forms
- Buttons marked `(Unused)` are planned for future versions
- Built with teachers' workflows and class structures in mind
