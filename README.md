
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

## Project Structure
```plaintext
Bluecard_v2/
├── data/
│   ├── 001attendance_data.json
│   ├── logo.png
│   └── settings.json
├── src/
│   ├── main.py
│   ├── logic/
│   │   ├── parser.py
│   │   └── attendance_utils.py
│   └── ui/
│       └── launcher.py (upcoming)
├── tests/
│   └── test_attendance.py
├── merge_bluecard.py         # Merges project assets
├── create_exe.bat            # Builds Windows .exe
├── requirements.txt
└── README.md
```

## Notes
- All errors are logged to: `data/bluecard_errors.log`
- Data is stored locally for portability
- UI will support `-topmost = True` on forms
- Buttons marked `(Unused)` are planned for future versions
- Built with teachers' workflows and class structures in mind
