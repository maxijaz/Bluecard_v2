from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy, QWidget, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
import json
import os

from logic.db_interface import get_form_settings, get_all_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

SETTINGS_PATH = "data/settings.json"
THEMES_PATH = "data/themes.json"


class SettingsForm(QDialog):
    def __init__(self, parent, current_theme=None, on_theme_change=None, open_stylesheet_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        form_settings = get_form_settings("SettingsForm") or {}
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.resize(800, 600)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        else:
            self.setMinimumSize(300, 200)
        max_w = form_settings.get("max_width")
        max_h = form_settings.get("max_height")
        if max_w and max_h:
            self.setMaximumSize(int(max_w), int(max_h))
        # Add minimize, maximize, and close buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # --- FONT SIZE PATCH: Set default font size from per-form or global settings ---
        default_settings = get_all_defaults()
        font_size = int(form_settings.get("font_size") or default_settings.get("form_font_size", default_settings.get("button_font_size", 12)))
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont(form_settings.get("font_family", "Segoe UI"), font_size))
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            display_settings = get_all_defaults()
            scale = str(display_settings.get("scale_windows", "1")) == "1"
            center = str(display_settings.get("center_windows", "1")) == "1"
            width_ratio = float(display_settings.get("window_width_ratio", 0.6))
            height_ratio = float(display_settings.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)

        self.default_settings = self.load_default_settings()
        self.init_ui()

    def load_default_settings(self):
        """Load default settings from the database."""
        return get_all_defaults()

    def init_ui(self):
        layout = QVBoxLayout(self)
        metadata_col = QVBoxLayout()
        metadata_heading = QLabel("Default Metadata")
        metadata_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        metadata_col.addWidget(metadata_heading)
        # Separator 1: under heading
        heading_sep = QWidget()
        heading_sep.setFixedHeight(4)
        heading_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        metadata_col.addWidget(heading_sep)
        # Info text
        info_label = QLabel("Set default values here for all new classes.\nAll values can be changed by editing metadata.")
        info_label.setStyleSheet("font-size: 9.5pt; color: #444444;")
        info_label.setWordWrap(True)
        metadata_col.addWidget(info_label)
        # Separator 2: under info text
        info_sep = QWidget()
        info_sep.setFixedHeight(4)
        info_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        metadata_col.addWidget(info_sep)
        metadata_col.addSpacing(12)
        self.entries = {}
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setHorizontalSpacing(16)
        fields_to_include = [
            "def_teacher", "def_teacher_no", "def_coursehours", "def_classtime", "def_rate", "def_ccp", "def_travel", "def_bonus"
        ]
        # Helper for bold metadata labels
        def bold_metadata_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold;")
            return lbl
        min_entry_width = 150
        for idx, key in enumerate(fields_to_include):
            value = self.default_settings.get(key, "")
            entry = QLineEdit(value)
            entry.setMinimumWidth(min_entry_width)
            entry.setStyleSheet("padding-left: 8px; padding-right: 16px;")  # Add left padding for symmetry
            self.entries[key] = entry
            form_layout.addRow(bold_metadata_label(key.replace("def_", "").capitalize() + ":"), entry)
            # Add a 20px vertical spacer after 'Bonus'
            if key == "def_bonus":
                form_layout.addRow(QWidget())  # Add an empty row for spacing
                spacer = QWidget()
                spacer.setFixedHeight(20)
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                form_layout.addRow(spacer)
        metadata_col.addLayout(form_layout)
        metadata_col.addStretch(1)
        layout.addLayout(metadata_col)
        # Add a vertical expanding spacer so the form stays at the top
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        # Separator 3: above buttons
        above_btn_sep = QWidget()
        above_btn_sep.setFixedHeight(4)
        above_btn_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        layout.addWidget(above_btn_sep)
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Add stretch before buttons for spacing
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(90)
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(90)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)  # Add stretch after buttons for spacing
        layout.addLayout(button_layout)
        # Separator 4: below buttons
        below_btn_sep = QWidget()
        below_btn_sep.setFixedHeight(4)
        below_btn_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        layout.addWidget(below_btn_sep)
        layout.addSpacing(16)  # Add bottom margin below buttons

        # Add right padding to data entry fields in column 1
        for i in range(form_layout.rowCount()):
            field_widget = form_layout.itemAt(i, QFormLayout.FieldRole)
            if field_widget is not None:
                widget = field_widget.widget()
                if isinstance(widget, QLineEdit):
                    widget.setStyleSheet("padding-right: 16px;")

        # --- Display Management Controls ---
        display_heading = QLabel("Window Display Management")
        display_heading.setStyleSheet("font-weight: bold; font-size: 13pt; margin-top: 12px;")
        layout.addWidget(display_heading)
        display_layout = QFormLayout()
        display_layout.setLabelAlignment(Qt.AlignRight)
        display_layout.setFormAlignment(Qt.AlignLeft)
        display_layout.setHorizontalSpacing(16)
        # Center windows checkbox
        center_cb = QCheckBox("Center windows on open")
        center_cb.setChecked(str(self.default_settings.get("center_windows", "1")) == "1")
        self.entries["center_windows"] = center_cb
        display_layout.addRow(center_cb)
        # Scale windows checkbox
        scale_cb = QCheckBox("Scale windows to screen size")
        scale_cb.setChecked(str(self.default_settings.get("scale_windows", "1")) == "1")
        self.entries["scale_windows"] = scale_cb
        display_layout.addRow(scale_cb)
        # Width ratio spinbox
        width_spin = QDoubleSpinBox()
        width_spin.setRange(0.1, 1.0)
        width_spin.setSingleStep(0.05)
        width_spin.setDecimals(2)
        width_spin.setValue(float(self.default_settings.get("window_width_ratio", 0.6)))
        width_spin.setSuffix(" (width ratio)")
        self.entries["window_width_ratio"] = width_spin
        display_layout.addRow("Width ratio:", width_spin)
        # Height ratio spinbox
        height_spin = QDoubleSpinBox()
        height_spin.setRange(0.1, 1.0)
        height_spin.setSingleStep(0.05)
        height_spin.setDecimals(2)
        height_spin.setValue(float(self.default_settings.get("window_height_ratio", 0.6)))
        height_spin.setSuffix(" (height ratio)")
        self.entries["window_height_ratio"] = height_spin
        display_layout.addRow("Height ratio:", height_spin)
        layout.addLayout(display_layout)

    def save_settings(self):
        updated_settings = {}
        for key, entry in self.entries.items():
            if isinstance(entry, QLineEdit):
                updated_settings[key] = entry.text()
            elif isinstance(entry, QCheckBox):
                updated_settings[key] = "1" if entry.isChecked() else "0"
            elif isinstance(entry, QDoubleSpinBox):
                updated_settings[key] = str(entry.value())
            else:
                updated_settings[key] = str(entry.text()) if hasattr(entry, 'text') else str(entry)
        try:
            set_all_defaults(updated_settings)
            # --- Live update: apply display settings immediately if parent is a main window ---
            parent = self.parent()
            if parent is not None:
                from logic.db_interface import get_all_defaults
                from logic.display import center_widget, scale_and_center
                display_settings = get_all_defaults()
                scale = str(display_settings.get("scale_windows", "1")) == "1"
                center = str(display_settings.get("center_windows", "1")) == "1"
                width_ratio = float(display_settings.get("window_width_ratio", 0.6))
                height_ratio = float(display_settings.get("window_height_ratio", 0.6))
                if scale:
                    scale_and_center(parent, width_ratio, height_ratio)
                elif center:
                    center_widget(parent)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return
        self.accept()

