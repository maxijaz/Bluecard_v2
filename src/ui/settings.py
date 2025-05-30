from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
import json
import os

from logic.db_interface import get_all_defaults, set_all_defaults  # <-- PATCH: Use DB for defaults

SETTINGS_PATH = "data/settings.json"
THEMES_PATH = "data/themes.json"


class SettingsForm(QDialog):
    def __init__(self, parent, current_theme, on_theme_change, open_stylesheet_callback):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.current_theme = current_theme
        self.on_theme_change = on_theme_change
        self.open_stylesheet_callback = open_stylesheet_callback
        self.themes = self.load_themes()
        self.default_settings = self.load_default_settings()
        self.init_ui()

    def load_themes(self):
        """Load themes from themes.json."""
        if not os.path.exists(THEMES_PATH):
            return []
        try:
            with open(THEMES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [theme["name"] for theme in data["themes"]]
        except json.JSONDecodeError:
            return []

    def load_default_settings(self):
        """Load default settings from the database."""
        return get_all_defaults()

    def init_ui(self):
        layout = QVBoxLayout(self)
        metadata_col = QVBoxLayout()
        metadata_heading = QLabel("Default Metadata")
        metadata_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        metadata_col.addWidget(metadata_heading)
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
        min_entry_width = 220
        for key in fields_to_include:
            value = self.default_settings.get(key, "")
            entry = QLineEdit(value)
            entry.setMinimumWidth(min_entry_width)
            entry.setStyleSheet("padding-left: 8px; padding-right: 16px;")  # Add left padding for symmetry
            self.entries[key] = entry
            form_layout.addRow(bold_metadata_label(key.replace("def_", "").capitalize() + ":"), entry)
        # Move theme dropdown here (below Bonus)
        theme_layout = QHBoxLayout()
        theme_label = bold_metadata_label("Select Theme:")
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(self.themes)
        self.theme_dropdown.setCurrentText(self.current_theme)
        self.theme_dropdown.setMinimumWidth(min_entry_width)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        form_layout.addRow(theme_layout)
        metadata_col.addLayout(form_layout)
        metadata_col.addStretch(1)
        layout.addLayout(metadata_col)

        # Add a vertical expanding spacer so the form stays at the top
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Add stretch before buttons for spacing
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(90)
        save_button.clicked.connect(self.save_settings)
        stylesheet_button = QPushButton("Stylesheet")
        stylesheet_button.setMinimumWidth(110)
        stylesheet_button.clicked.connect(self.open_stylesheet_callback)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(90)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(stylesheet_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)  # Add stretch after buttons for spacing
        layout.addLayout(button_layout)
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
        updated_settings["theme"] = self.theme_dropdown.currentText()
        try:
            set_all_defaults(updated_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return
        if self.on_theme_change:
            self.on_theme_change(self.theme_dropdown.currentText())
        self.accept()
