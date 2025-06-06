import os
import sqlite3
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "001attendance.db"
FACTORY_DEFAULTS_PATH = DATA_DIR / "factory_defaults.json"

# Helper: Connect to DB
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_factory_defaults():
    with open(FACTORY_DEFAULTS_PATH, encoding="utf-8") as f:
        return json.load(f)

def reset_defaults_table(conn, factory_defaults):
    cur = conn.cursor()
    cur.execute("DELETE FROM defaults")
    for k, v in factory_defaults["global"].items():
        cur.execute("INSERT INTO defaults (key, value) VALUES (?, ?)", (k, str(v)))
    print("[OK] Reset global defaults table.")

def reset_form_settings_table(conn, factory_defaults):
    cur = conn.cursor()
    cur.execute("DELETE FROM form_settings")
    forms = factory_defaults.get("forms", {})
    for form_name, settings in forms.items():
        columns = ["form_name"] + list(settings.keys())
        values = [form_name] + [settings[k] for k in settings.keys()]
        placeholders = ",".join(["?"] * len(columns))
        cur.execute(f"INSERT INTO form_settings ({','.join(columns)}) VALUES ({placeholders})", values)
    print("[OK] Reset per-form settings table.")

def reset_class_settings(conn, factory_defaults):
    cur = conn.cursor()
    class_defaults = factory_defaults.get("classes", {}).get("default", {})
    if not class_defaults:
        print("[WARN] No class defaults found in factory_defaults.json.")
        return
    # Get all classes
    cur.execute("SELECT class_no FROM classes")
    class_nos = [row["class_no"] for row in cur.fetchall()]
    # Update each class with default settings
    for class_no in class_nos:
        assignments = ", ".join([f"{k}=?" for k in class_defaults.keys()])
        values = list(class_defaults.values()) + [class_no]
        cur.execute(f"UPDATE classes SET {assignments} WHERE class_no = ?", values)
    print(f"[OK] Reset per-class settings for {len(class_nos)} classes.")

def main():
    print("This will reset ALL settings to factory defaults, but keep all class/student/attendance data.")
    confirm = input("Type 'YES' to continue: ")
    if confirm != "YES":
        print("Aborted.")
        return
    conn = get_conn()
    factory_defaults = load_factory_defaults()
    reset_defaults_table(conn, factory_defaults)
    reset_form_settings_table(conn, factory_defaults)
    reset_class_settings(conn, factory_defaults)
    conn.commit()
    conn.close()
    print("[DONE] All settings reset to factory defaults.")

if __name__ == "__main__":
    main()
