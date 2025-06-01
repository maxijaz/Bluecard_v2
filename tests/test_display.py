"""
A standalone GUI for testing and editing per-form settings for Bluecard forms.
- Dropdown to select form (populated from DB or 001form_settings.json)
- Loads current settings for the selected form
- Allows editing all fields
- [Save to DB] and [Update 001form_settings.json] buttons
- Does NOT require main.py or launcher to be running
- No button added to any main form
"""
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt
from src.logic.db_interface import get_form_settings, set_form_settings

SETTINGS_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/001form_settings.json'))

# Utility to load all form names and settings from JSON

def load_all_form_settings():
    with open(SETTINGS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {entry['form_name']: entry for entry in data}

def save_all_form_settings(all_settings):
    with open(SETTINGS_JSON, 'w', encoding='utf-8') as f:
        json.dump(list(all_settings.values()), f, indent=2, ensure_ascii=False)

class FormSettingsEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Form Settings Editor (Bluecard)")
        self.resize(600, 700)
        self.all_settings = load_all_form_settings()
        self.form_names = sorted(self.all_settings.keys())
        self.current_form = None
        self.fields = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(QLabel("Form:"))
        self.form_combo = QComboBox()
        self.form_combo.addItems(self.form_names)
        self.form_combo.currentTextChanged.connect(self.on_form_changed)
        top.addWidget(self.form_combo)
        layout.addLayout(top)

        # Scrollable area for settings fields
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.form_widget = QWidget()
        self.form_layout = QFormLayout()
        self.form_widget.setLayout(self.form_layout)
        self.scroll.setWidget(self.form_widget)
        layout.addWidget(self.scroll)

        # Buttons
        btns = QHBoxLayout()
        self.save_db_btn = QPushButton("Save to DB")
        self.save_db_btn.clicked.connect(self.save_to_db)
        self.save_json_btn = QPushButton("Update 001form_settings.json")
        self.save_json_btn.clicked.connect(self.save_to_json)
        self.open_form_btn = QPushButton("Open Form")
        self.open_form_btn.clicked.connect(self.open_selected_form)
        btns.addWidget(self.save_db_btn)
        btns.addWidget(self.save_json_btn)
        btns.addWidget(self.open_form_btn)
        layout.addLayout(btns)

        self.setLayout(layout)
        self.on_form_changed(self.form_combo.currentText())

    def on_form_changed(self, form_name):
        self.current_form = form_name
        # Clear old fields
        for i in reversed(range(self.form_layout.count())):
            self.form_layout.itemAt(i).widget().setParent(None)
        self.fields.clear()
        # Load settings (prefer DB, fallback to JSON)
        db_settings = get_form_settings(form_name) or {}
        json_settings = self.all_settings.get(form_name, {})
        merged = dict(json_settings)
        merged.update({k: v for k, v in db_settings.items() if v not in (None, "")})
        # Show all fields
        for key in sorted(json_settings.keys()):
            val = merged.get(key, "")
            le = QLineEdit(str(val))
            self.form_layout.addRow(QLabel(key), le)
            self.fields[key] = le

    def save_to_db(self):
        if not self.current_form:
            return
        settings = {k: self.fields[k].text() for k in self.fields}
        set_form_settings(self.current_form, settings)
        QMessageBox.information(self, "Saved", f"Settings for '{self.current_form}' saved to DB.")

    def save_to_json(self):
        if not self.current_form:
            return
        # Update in-memory
        self.all_settings[self.current_form] = {k: self.fields[k].text() for k in self.fields}
        save_all_form_settings(self.all_settings)
        QMessageBox.information(self, "Saved", f"Settings for '{self.current_form}' updated in 001form_settings.json.")

    def open_selected_form(self):
        """Open the selected form for visual testing, using dummy or real data."""
        import importlib
        import sys
        import os
        from PyQt5.QtWidgets import QDialog, QMainWindow
        # Ensure src/ is in sys.path for imports
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        # Also ensure src/logic is in sys.path for direct logic.* imports
        logic_dir = os.path.join(base_dir, 'logic')
        if logic_dir not in sys.path:
            sys.path.insert(0, logic_dir)
        form_name = self.form_combo.currentText()
        form_map = {
            "Mainform": ("ui.mainform", "Mainform", True),
            "MetadataForm": ("ui.metadata_form", "MetadataForm", False),
            "StudentForm": ("ui.student_form", "StudentForm", False),
            "PALCODForm": ("ui.pal_cod_form", "PALCODForm", False),
            "ShowHideForm": ("ui.show_hide_form", "ShowHideForm", False),
            "Launcher": ("ui.launcher", "Launcher", False),
            "SettingsForm": ("ui.settings", "SettingsForm", False),
            "CalendarView": ("ui.calendar", "CalendarView", False),
            "ArchiveManager": ("ui.archive_manager", "ArchiveManager", False),
            "StudentManager": ("ui.student_manager", "StudentManager", False),
            "MonthlySummary": ("ui.monthly_summary", "MonthlySummary", False),
            "StylesheetForm": ("ui.stylesheet", "StylesheetForm", False),
        }
        if form_name not in form_map:
            QMessageBox.warning(self, "Not Supported", f"No test harness for {form_name}.")
            return
        mod_name, class_name, is_mainform = form_map[form_name]
        try:
            mod = importlib.import_module(mod_name)
            FormClass = getattr(mod, class_name)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import {form_name}: {e}")
            return
        # --- Dummy/test data for each form ---
        if is_mainform:
            try:
                dbi = importlib.import_module("logic.db_interface")
                class_ids = dbi.get_all_class_ids()
                class_id = class_ids[0] if class_ids else "OLO123"
                class_data = dbi.get_class_by_id(class_id)
                students = {s["student_id"]: s for s in dbi.get_students_by_class(class_id)}
                for s in students.values():
                    attn = dbi.get_attendance_by_student(s["student_id"])
                    s["attendance"] = {a["date"]: a["status"] for a in attn}
                data = {"classes": {class_id: {"metadata": class_data, "students": students}}}
            except Exception:
                data = {"classes": {"OLO123": {"metadata": {"company": "Test Co", "teacher": "Jane"}, "students": {}}}}
                class_id = "OLO123"
            theme = "default"
            win = FormClass(class_id, data, theme)
        elif form_name == "MetadataForm":
            try:
                dbi = importlib.import_module("logic.db_interface")
                class_ids = dbi.get_all_class_ids()
                class_id = class_ids[0] if class_ids else "OLO123"
                class_data = dbi.get_class_by_id(class_id)
                data = {"classes": {class_id: {"metadata": class_data, "students": {}}}}
            except Exception:
                class_id = "OLO123"
                data = {"classes": {class_id: {"metadata": {"company": "Test Co", "teacher": "Jane"}, "students": {}}}}
            theme = "default"
            win = FormClass(None, class_id, data, theme, lambda: None, {}, is_read_only=True)
        elif form_name == "StudentForm":
            try:
                dbi = importlib.import_module("logic.db_interface")
                class_ids = dbi.get_all_class_ids()
                class_id = class_ids[0] if class_ids else "OLO123"
                students = dbi.get_students_by_class(class_id)
                student = students[0] if students else {"name": "Test Student", "student_id": "S1"}
                data = {"classes": {class_id: {"metadata": dbi.get_class_by_id(class_id), "students": {student["student_id"]: student}}}}
            except Exception:
                class_id = "OLO123"
                student = {"name": "Test Student", "student_id": "S1"}
                data = {"classes": {class_id: {"metadata": {"company": "Test Co", "teacher": "Jane"}, "students": {student["student_id"]: student}}}}
            win = FormClass(None, class_id, data, lambda: None, student_id=student["student_id"], student_data=student)
        elif form_name == "PALCODForm":
            win = FormClass(None, 0, lambda v: None, None, "01/01/2025", student_name="Test Student")
        elif form_name == "ShowHideForm":
            try:
                dbi = importlib.import_module("logic.db_interface")
                class_ids = dbi.get_all_class_ids()
                class_id = class_ids[0] if class_ids else "OLO123"
            except Exception:
                class_id = "OLO123"
            win = FormClass(None, class_id)
        elif form_name == "Launcher":
            win = FormClass()
        elif form_name == "SettingsForm":
            win = FormClass(None)
        elif form_name == "CalendarView":
            win = FormClass(None)
        elif form_name == "ArchiveManager":
            try:
                dbi = importlib.import_module("logic.db_interface")
                all_classes = dbi.get_all_classes()
                archived_classes = {row["class_no"]: row for row in all_classes if row.get("archive", "No") == "Yes"}
                data = {"classes": archived_classes}
                if not archived_classes:
                    # Add a dummy archived class for testing
                    archived_classes = {
                        "ARCH123": {
                            "class_no": "ARCH123",
                            "company": "Test Archived Co",
                            "archive": "Yes"
                        }
                    }
                    data = {"classes": archived_classes}
            except Exception:
                archived_classes = {
                    "ARCH123": {
                        "class_no": "ARCH123",
                        "company": "Test Archived Co",
                        "archive": "Yes"
                    }
                }
                data = {"classes": archived_classes}
            win = FormClass(None, data, archived_classes)
        elif form_name == "StudentManager":
            win = FormClass(None, "OLO123")
        elif form_name == "MonthlySummary":
            win = FormClass(None)
        elif form_name == "StylesheetForm":
            win = FormClass(None)
        else:
            QMessageBox.warning(self, "Not Supported", f"No test harness for {form_name}.")
            return
        # Show the form/dialog as a top-level window, bring to front and focus
        # Keep a reference to prevent garbage collection
        if not hasattr(self, '_open_forms'):
            self._open_forms = []
        if isinstance(win, (QDialog, QMainWindow)):
            win.setParent(None)
            win.setWindowModality(Qt.NonModal)
            win.show()
            win.raise_()
            win.activateWindow()
            self._open_forms.append(win)
            # Remove reference when closed
            def cleanup():
                try:
                    self._open_forms.remove(win)
                except Exception:
                    pass
            win.destroyed.connect(cleanup)
        else:
            QMessageBox.warning(self, "Not Supported", f"Cannot show {form_name} (not a QWidget).")

    def showEvent(self, event):
        super().showEvent(event)
        self.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FormSettingsEditor()
    w.show()
    sys.exit(app.exec_())
