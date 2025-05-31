from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt
import json
import os

from logic.db_interface import get_all_defaults, set_all_defaults  # <-- PATCH: Use DB for defaults

SETTINGS_PATH = "data/settings.json"
THEMES_PATH = "data/themes.json"


class SettingsForm(QDialog):
    def __init__(self, parent, current_theme=None, on_theme_change=None, open_stylesheet_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        # Add minimize, maximize, and close buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
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

    def save_settings(self):
        updated_settings = {key: entry.text() for key, entry in self.entries.items()}
        try:
            set_all_defaults(updated_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return
        self.accept()

