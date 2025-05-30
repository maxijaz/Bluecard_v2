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

        # Metadata font size and color
        metadata_font_size_layout = QHBoxLayout()
        metadata_font_size_label = QLabel("Metadata Font Size:")
        metadata_font_size_label.setFixedWidth(150)
        self.metadata_font_size_entry = QLineEdit(self.default_settings.get("metadata_font_size", "12"))
        metadata_font_size_layout.addWidget(metadata_font_size_label)
        metadata_font_size_layout.addWidget(self.metadata_font_size_entry)
        layout.addLayout(metadata_font_size_layout)

        metadata_fg_color_layout = QHBoxLayout()
        metadata_fg_color_label = QLabel("Metadata Text Color:")
        metadata_fg_color_label.setFixedWidth(150)
        self.metadata_fg_color_entry = QLineEdit(self.default_settings.get("metadata_fg_color", "#222222"))
        metadata_fg_color_layout.addWidget(metadata_fg_color_label)
        metadata_fg_color_layout.addWidget(self.metadata_fg_color_entry)
        layout.addLayout(metadata_fg_color_layout)

        # Button font size
        button_font_size_layout = QHBoxLayout()
        button_font_size_label = QLabel("Button Font Size:")
        button_font_size_label.setFixedWidth(150)
        self.button_font_size_entry = QLineEdit(self.default_settings.get("button_font_size", "11"))
        button_font_size_layout.addWidget(button_font_size_label)
        button_font_size_layout.addWidget(self.button_font_size_entry)
        layout.addLayout(button_font_size_layout)

        # Table header font size and color
        table_header_font_size_layout = QHBoxLayout()
        table_header_font_size_label = QLabel("Table Header Font Size:")
        table_header_font_size_label.setFixedWidth(150)
        self.table_header_font_size_entry = QLineEdit(self.default_settings.get("table_header_font_size", "12"))
        table_header_font_size_layout.addWidget(table_header_font_size_label)
        table_header_font_size_layout.addWidget(self.table_header_font_size_entry)
        layout.addLayout(table_header_font_size_layout)

        table_header_bg_color_layout = QHBoxLayout()
        table_header_bg_color_label = QLabel("Table Header BG Color:")
        table_header_bg_color_label.setFixedWidth(150)
        self.table_header_bg_color_entry = QLineEdit(self.default_settings.get("table_header_bg_color", "#1976d2"))
        table_header_bg_color_layout.addWidget(table_header_bg_color_label)
        table_header_bg_color_layout.addWidget(self.table_header_bg_color_entry)
        layout.addLayout(table_header_bg_color_layout)

        table_header_fg_color_layout = QHBoxLayout()
        table_header_fg_color_label = QLabel("Table Header Text Color:")
        table_header_fg_color_label.setFixedWidth(150)
        self.table_header_fg_color_entry = QLineEdit(self.default_settings.get("table_header_fg_color", "#ffffff"))
        table_header_fg_color_layout.addWidget(table_header_fg_color_label)
        table_header_fg_color_layout.addWidget(self.table_header_fg_color_entry)
        layout.addLayout(table_header_fg_color_layout)

        # Table data font size and color
        table_font_size_layout = QHBoxLayout()
        table_font_size_label = QLabel("Table Data Font Size:")
        table_font_size_label.setFixedWidth(150)
        self.table_font_size_entry = QLineEdit(self.default_settings.get("font_size", "12"))
        table_font_size_layout.addWidget(table_font_size_label)
        table_font_size_layout.addWidget(self.table_font_size_entry)
        layout.addLayout(table_font_size_layout)

        table_fg_color_layout = QHBoxLayout()
        table_fg_color_label = QLabel("Table Data Text Color:")
        table_fg_color_label.setFixedWidth(150)
        self.table_fg_color_entry = QLineEdit(self.default_settings.get("table_fg_color", "#222222"))
        table_fg_color_layout.addWidget(table_fg_color_label)
        table_fg_color_layout.addWidget(self.table_fg_color_entry)
        layout.addLayout(table_fg_color_layout)

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
        restore_defaults_button = QPushButton("Restore All Colors/Fonts")
        restore_defaults_button.clicked.connect(self.restore_all_colors_fonts)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(restore_defaults_button)
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
        updated_settings["metadata_font_size"] = self.metadata_font_size_entry.text()
        updated_settings["metadata_fg_color"] = self.metadata_fg_color_entry.text()
        updated_settings["button_font_size"] = self.button_font_size_entry.text()
        updated_settings["table_header_font_size"] = self.table_header_font_size_entry.text()
        updated_settings["table_header_bg_color"] = self.table_header_bg_color_entry.text()
        updated_settings["table_header_fg_color"] = self.table_header_fg_color_entry.text()
        updated_settings["table_fg_color"] = self.table_fg_color_entry.text()
        updated_settings["table_font_size"] = self.table_font_size_entry.text()
        try:
            set_all_defaults(updated_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return

        # Refresh Launcher with the new theme
        if self.on_theme_change:
            self.on_theme_change(self.theme_dropdown.currentText())
        self.accept()  # Close the dialog

    def restore_all_colors_fonts(self):
        """Restore only color and font fields to factory defaults, leave other values untouched."""
        FACTORY_DEFAULTS = {
            "font_size": "12",
            "form_bg_color": "#e3f2fd",
            "form_fg_color": "#222222",
            "button_bg_color": "#1976d2",
            "button_fg_color": "#ffffff",
            "button_font_size": "11",
            "table_bg_color": "#ffffff",
            "table_fg_color": "#222222",
            "table_header_bg_color": "#1976d2",
            "table_header_fg_color": "#ffffff",
        }
        self.font_size_dropdown.setCurrentText(FACTORY_DEFAULTS["font_size"])
        if hasattr(self, 'form_bg_entry'):
            self.form_bg_entry.setText(FACTORY_DEFAULTS["form_bg_color"])
        if hasattr(self, 'button_bg_entry'):
            self.button_bg_entry.setText(FACTORY_DEFAULTS["button_bg_color"])
        if hasattr(self, 'button_fg_entry'):
            self.button_fg_entry.setText(FACTORY_DEFAULTS["button_fg_color"])
        if hasattr(self, 'table_bg_entry'):
            self.table_bg_entry.setText(FACTORY_DEFAULTS["table_bg_color"])
        # Add more fields as you add them to the form (e.g., table header, fg, etc.)

    def closeEvent(self, event):
        """Restore the initial size when the settings form is reopened."""
        self.resize(450, 700)
        super().closeEvent(event)

    def open_settings(self):
        """Open the Settings dialog."""
        settings_form = SettingsForm(self, self.theme, self.apply_theme_and_refresh)
        settings_form.exec_()