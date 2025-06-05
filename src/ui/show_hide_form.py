from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QGridLayout, QMessageBox, QLineEdit, QWidget
)
from PyQt5.QtCore import Qt
from logic.db_interface import update_class, get_class_by_id, get_form_settings, get_all_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

SHOW_HIDE_FIELDS = [
    ("show_nickname", "Nickname"),
    ("show_company_no", "Company No"),
    ("show_score", "Score"),
    ("show_pretest", "PreTest"),
    ("show_posttest", "PostTest"),
    ("show_attn", "Attn"),
    ("show_p", "P"),
    ("show_a", "A"),
    ("show_l", "L"),
    ("show_note", "Note"),
    ("show_dates", "Dates"),  # <-- Add Dates (scrollable table)
]

# Map from label to DB width key
WIDTH_DB_KEYS = {
    "Nickname": "width_nickname",
    "Company No": "width_company_no",
    "Score": "width_score",
    "PreTest": "width_pretest",
    "PostTest": "width_posttest",
    "Attn": "width_attn",
    "P": "width_p",
    "A": "width_a",
    "L": "width_l",
    "Note": "width_note",
    "Dates": "width_date",  # <-- Add width_date for Dates
}

COLOR_FIELDS = [
    ("bgcolor_p", "P", "#c8e6c9"),
    ("bgcolor_a", "A", "#ffcdd2"),
    ("bgcolor_l", "L", "#fff9c4"),
    ("bgcolor_cod", "COD", "#c8e6c9"),
    ("bgcolor_cia", "CIA", "#ffcdd2"),
    ("bgcolor_hol", "HOL", "#ffcdd2"),
]

class ShowHideForm(QDialog):
    def __init__(self, parent, class_id, on_save_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Show / Hide Columns & Colour Scheme")
        self.class_id = class_id
        self.on_save_callback = on_save_callback
        self.class_data = get_class_by_id(class_id)  # <-- Load from classes table
        self.checkboxes = {}
        self.color_edits = {}
        self.width_edits = {}  # {db_key: QLineEdit}

        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("ShowHideForm") or {}
        defaults = get_all_defaults()
        from PyQt5.QtGui import QFont
        self.form_font_size = int(form_settings.get("font_size") or defaults.get("form_font_size", 12))
        self.form_font = QFont(form_settings.get("font_family", "Segoe UI"), self.form_font_size)
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.setFixedSize(850, 500)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        max_w = form_settings.get("max_width")
        max_h = form_settings.get("max_height")
        if max_w and max_h:
            self.setMaximumSize(int(max_w), int(max_h))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            from logic.display import center_widget, scale_and_center, apply_window_flags
            scale = str(defaults.get("scale_windows", "1")) == "1"
            center = str(defaults.get("center_windows", "1")) == "1"
            width_ratio = float(defaults.get("window_width_ratio", 0.6))
            height_ratio = float(defaults.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        # --- PATCH END ---

        layout = QVBoxLayout(self)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Choose columns to show/hide</b>"))
        header_layout.addWidget(QLabel("<b>P/A/L colour scheme</b>"))
        header_layout.addWidget(QLabel("<b>Column Width</b>"))
        layout.addLayout(header_layout)

        # Main grid
        grid = QGridLayout()
        max_rows = max(len(SHOW_HIDE_FIELDS), len(COLOR_FIELDS))
        for row in range(max_rows):
            # Column 1: Show/Hide tickboxes
            if row < len(SHOW_HIDE_FIELDS):
                key, label = SHOW_HIDE_FIELDS[row]
                lbl = QLabel(label)
                cb = QCheckBox()
                cb.setChecked(self.class_data.get(key, "Yes") == "Yes")
                self.checkboxes[key] = cb
                grid.addWidget(lbl, row, 0)
                grid.addWidget(cb, row, 1)
                # Column 2: Width QLineEdit (aligned with label/tickbox)
                width_db_key = WIDTH_DB_KEYS.get(label)
                if width_db_key:
                    width_val = self.class_data.get(width_db_key, "")
                    width_edit = QLineEdit(str(width_val) if width_val else "")
                    width_edit.setMaximumWidth(60)
                    self.width_edits[width_db_key] = width_edit
                    grid.addWidget(width_edit, row, 2)
                else:
                    grid.addWidget(QWidget(), row, 2)
            else:
                grid.addWidget(QWidget(), row, 0)
                grid.addWidget(QWidget(), row, 1)
                grid.addWidget(QWidget(), row, 2)
            # Column 3: Color label + QLineEdit
            if row < len(COLOR_FIELDS):
                color_key, color_label, default = COLOR_FIELDS[row]
                lbl = QLabel(color_label)
                edit = QLineEdit(self.class_data.get(color_key, default))
                self.color_edits[color_key] = edit
                grid.addWidget(lbl, row, 3)
                grid.addWidget(edit, row, 4)
            else:
                grid.addWidget(QWidget(), row, 3)
                grid.addWidget(QWidget(), row, 4)
        layout.addLayout(grid)

        # Toggle buttons
        toggle_layout = QHBoxLayout()
        self.toggle_columns_btn = QPushButton("Toggle show/hide columns")
        self.toggle_columns_btn.clicked.connect(self.toggle_columns)
        self.toggle_colors_btn = QPushButton("Toggle bgcolor on/off")
        self.toggle_colors_btn.clicked.connect(self.toggle_colors)
        self.reset_widths_btn = QPushButton("Reset Widths")
        self.reset_widths_btn.clicked.connect(self.reset_widths)
        toggle_layout.addWidget(self.toggle_columns_btn)
        toggle_layout.addWidget(self.toggle_colors_btn)
        toggle_layout.addWidget(self.reset_widths_btn)
        layout.addLayout(toggle_layout)

        # Save/Cancel
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def reset_widths(self):
        # Reload widths from DB and update QLineEdits
        db_row = get_class_by_id(self.class_id)
        for label, db_key in WIDTH_DB_KEYS.items():
            if db_key in self.width_edits:
                val = db_row.get(db_key, "")
                self.width_edits[db_key].setText(str(val) if val else "")

    def toggle_columns(self):
        # Toggle all checkboxes: if any unchecked, check all; else uncheck all
        check = not all(cb.isChecked() for cb in self.checkboxes.values())
        for cb in self.checkboxes.values():
            cb.setChecked(check)

    def toggle_colors(self):
        # If any color is not empty, clear all; else set to default
        any_colored = any(edit.text().strip() for edit in self.color_edits.values())
        for color_key, edit in self.color_edits.items():
            default = next((d for k, l, d in COLOR_FIELDS if k == color_key), "")
            edit.setText("" if any_colored else default)

    def save(self):
        updates = {key: "Yes" if cb.isChecked() else "No" for key, cb in self.checkboxes.items()}
        for color_key, edit in self.color_edits.items():
            updates[color_key] = edit.text().strip()
        # Save widths
        for db_key, edit in self.width_edits.items():
            val = edit.text().strip()
            if val.isdigit():
                updates[db_key] = int(val)
            else:
                updates[db_key] = None
        # print(f"[DEBUG] ShowHideForm.save: updates to save for class {self.class_id}: {updates}")
        try:
            update_class(self.class_id, updates)
            # print(f"[DEBUG] update_class called for {self.class_id} with: {updates}")
            if self.on_save_callback:
                self.on_save_callback()
            self.accept()
        except Exception as e:
            # print(f"[DEBUG] ShowHideForm.save: Exception: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def get_selected_columns(self):
        # Returns a dict mapping DB key (e.g. 'show_nickname') to True/False for checked/unchecked
        result = {}
        for key, cb in self.checkboxes.items():
            result[key] = cb.isChecked()
        return result