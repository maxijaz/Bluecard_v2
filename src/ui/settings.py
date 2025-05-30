from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import json
import os

from logic.db_interface import get_all_defaults, set_all_defaults  # <-- PATCH: Use DB for defaults

SETTINGS_PATH = "data/settings.json"
THEMES_PATH = "data/themes.json"


class SettingsForm(QDialog):
    def __init__(self, parent, current_theme, on_theme_change):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(350, 400)  # Set the initial size without fixing it
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowModality(Qt.ApplicationModal)

        self.current_theme = current_theme
        self.on_theme_change = on_theme_change  # Callback to refresh Launcher
        self.themes = self.load_themes()
        self.default_settings = self.load_default_settings()

        # Create UI components
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
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Select Theme:")
        theme_label.setFixedWidth(100)
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(self.themes)
        self.theme_dropdown.setCurrentText(self.current_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        layout.addLayout(theme_layout)

        # Font size selection
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_label.setFixedWidth(100)
        self.font_size_dropdown = QComboBox()
        self.font_size_dropdown.addItems(["10", "12", "14", "16", "18", "20", "22", "24"])
        current_font_size = str(self.default_settings.get("font_size", "12"))
        self.font_size_dropdown.setCurrentText(current_font_size)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_dropdown)
        layout.addLayout(font_size_layout)

        # Form background color
        form_bg_layout = QHBoxLayout()
        form_bg_label = QLabel("Form Background Color:")
        form_bg_label.setFixedWidth(150)
        self.form_bg_entry = QLineEdit(self.default_settings.get("form_bg_color", "#e3f2fd"))
        form_bg_layout.addWidget(form_bg_label)
        form_bg_layout.addWidget(self.form_bg_entry)
        layout.addLayout(form_bg_layout)

        # Button background color
        button_bg_layout = QHBoxLayout()
        button_bg_label = QLabel("Button Background Color:")
        button_bg_label.setFixedWidth(150)
        self.button_bg_entry = QLineEdit(self.default_settings.get("button_bg_color", "#1976d2"))
        button_bg_layout.addWidget(button_bg_label)
        button_bg_layout.addWidget(self.button_bg_entry)
        layout.addLayout(button_bg_layout)

        # Button foreground color
        button_fg_layout = QHBoxLayout()
        button_fg_label = QLabel("Button Text Color:")
        button_fg_label.setFixedWidth(150)
        self.button_fg_entry = QLineEdit(self.default_settings.get("button_fg_color", "#ffffff"))
        button_fg_layout.addWidget(button_fg_label)
        button_fg_layout.addWidget(self.button_fg_entry)
        layout.addLayout(button_fg_layout)

        # Table background color
        table_bg_layout = QHBoxLayout()
        table_bg_label = QLabel("Table Background Color:")
        table_bg_label.setFixedWidth(150)
        self.table_bg_entry = QLineEdit(self.default_settings.get("table_bg_color", "#ffffff"))
        table_bg_layout.addWidget(table_bg_label)
        table_bg_layout.addWidget(self.table_bg_entry)
        layout.addLayout(table_bg_layout)

        # Default settings fields
        self.entries = {}
        form_layout = QFormLayout()
        fields_to_include = [
            "def_teacher",
            "def_teacher_no",
            "def_coursehours",
            "def_classtime",
            "def_rate",
            "def_ccp",
            "def_travel",
            "def_bonus"
        ]
        for key in fields_to_include:
            value = self.default_settings.get(key, "")
            entry = QLineEdit(value)
            self.entries[key] = entry
            form_layout.addRow(key.replace("def_", "").capitalize() + ":", entry)

        layout.addLayout(form_layout, stretch=0)

        # Add a vertical expanding spacer so the form stays at the top
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def save_settings(self):
        """Save the selected theme and default settings."""
        # Save theme to settings.json
        selected_theme = self.theme_dropdown.currentText()
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"theme": selected_theme}, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save theme: {e}")
            return

        # Save default settings to the database
        updated_settings = {key: entry.text() for key, entry in self.entries.items()}
        updated_settings["font_size"] = self.font_size_dropdown.currentText()
        updated_settings["form_bg_color"] = self.form_bg_entry.text()
        updated_settings["button_bg_color"] = self.button_bg_entry.text()
        updated_settings["button_fg_color"] = self.button_fg_entry.text()
        updated_settings["table_bg_color"] = self.table_bg_entry.text()
        try:
            set_all_defaults(updated_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return

        # Refresh Launcher with the new theme
        if self.on_theme_change:
            self.on_theme_change(self.theme_dropdown.currentText())
        self.accept()  # Close the dialog

    def closeEvent(self, event):
        """Restore the initial size when the settings form is reopened."""
        self.resize(450, 700)
        super().closeEvent(event)

    def open_settings(self):
        """Open the Settings dialog."""
        settings_form = SettingsForm(self, self.theme, self.apply_theme_and_refresh)
        settings_form.exec_()