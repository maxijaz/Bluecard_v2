from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
import json
import os

SETTINGS_PATH = "data/settings.json"
DEFAULT_PATH = "data/default.json"
THEMES_PATH = "data/themes.json"


class SettingsForm(QDialog):
    def __init__(self, parent, current_theme, on_theme_change):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(450, 600)
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
        """Load default settings from default.json."""
        if not os.path.exists(DEFAULT_PATH):
            return {}
        try:
            with open(DEFAULT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

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

        # Default settings fields
        self.entries = {}
        form_layout = QFormLayout()
        fields_to_include = [
            "def_teacher",
            "def_teacherno",
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
        layout.addLayout(form_layout)

        # Frozen table column visibility checkboxes
        self.column_visibility = {}
        column_fields = {
            "show_score": "Show Score",
            "show_prestest": "Show PreTest",
            "show_posttest": "Show PostTest",
            "show_attn": "Show Attn"
        }
        for key, label in column_fields.items():
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.default_settings.get(key, "Yes") == "Yes")
            self.column_visibility[key] = checkbox
            layout.addWidget(checkbox)

        # Scrollable table column visibility checkboxes
        self.scrollable_column_visibility = {}
        scrollable_column_fields = {
            "show_p": "Show P",
            "show_a": "Show A",
            "show_l": "Show L",
            "show_dates": "Show Dates"
        }
        for key, label in scrollable_column_fields.items():
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.default_settings.get(key, "Yes") == "Yes")
            self.scrollable_column_visibility[key] = checkbox
            layout.addWidget(checkbox)

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

        # Save default settings to default.json
        updated_settings = {key: entry.text() for key, entry in self.entries.items()}
        updated_settings.update({
            key: "Yes" if checkbox.isChecked() else "No"
            for key, checkbox in self.column_visibility.items()
        })
        updated_settings.update({
            key: "Yes" if checkbox.isChecked() else "No"
            for key, checkbox in self.scrollable_column_visibility.items()
        })
        try:
            with open(DEFAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(updated_settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return

        # Refresh Launcher with the new theme
        self.on_theme_change(selected_theme)
        self.accept()  # Close the dialog