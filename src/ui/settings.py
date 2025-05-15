from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QCheckBox, QGridLayout, QSpacerItem, QSizePolicy, QTableView
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
        self.resize(450, 400)  # Set the initial size without fixing it
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

        # Make sure this is at the top, before any assignment to self.scrollable_column_visibility
        self.scrollable_column_visibility = {}

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
        layout.addLayout(form_layout, stretch=0)

        layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))  # 8 pixels high spacer

        # Add heading/label for tickboxes
        tickbox_heading = QLabel("Select columns to show / hide on mainform (Bluecard).")
        tickbox_heading.setAlignment(Qt.AlignLeft)
        tickbox_heading.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(tickbox_heading)

        # --- Frozen table column visibility tickboxes (first group) ---
        self.column_visibility = {}
        main_columns = [
            ("show_nickname", "Nickname"),
            ("show_company_no", "Company No"),
            ("show_score", "Score"),
            ("show_prestest", "PreTest"),
            ("show_posttest", "PostTest"),
        ]

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(12)
        main_grid.setVerticalSpacing(2)
        main_grid.setContentsMargins(0, 0, 0, 0)
        for col, (key, label) in enumerate(main_columns):
            label_widget = QLabel(label)
            label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            main_grid.addWidget(label_widget, 0, col)
            checkbox = QCheckBox()
            checkbox.setChecked(self.default_settings.get(key, "Yes") == "Yes")
            self.column_visibility[key] = checkbox
            main_grid.addWidget(checkbox, 1, col, alignment=Qt.AlignHCenter | Qt.AlignTop)

        layout.addLayout(main_grid)

        # --- Spacer between groups ---
        layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Frozen table column visibility tickboxes (second group) ---
        secondary_columns = [
            ("show_attn", "Attn"),
            ("show_p", "P"),
            ("show_a", "A"),
            ("show_l", "L"),
            ("show_dates", "Show Dates"),
        ]

        secondary_grid = QGridLayout()
        secondary_grid.setHorizontalSpacing(12)
        secondary_grid.setVerticalSpacing(2)
        secondary_grid.setContentsMargins(0, 0, 0, 0)
        for col, (key, label) in enumerate(secondary_columns):
            label_widget = QLabel(label)
            label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            secondary_grid.addWidget(label_widget, 0, col)
            checkbox = QCheckBox()
            checkbox.setChecked(self.default_settings.get(key, "Yes") == "Yes")
            if key == "show_dates":
                self.scrollable_column_visibility[key] = checkbox
            else:
                self.column_visibility[key] = checkbox
            secondary_grid.addWidget(checkbox, 1, col, alignment=Qt.AlignHCenter | Qt.AlignTop)

        layout.addLayout(secondary_grid)

        # Add a vertical expanding spacer so tickboxes stay at the top
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Table layout
        self.table_layout = QVBoxLayout()
        layout.addLayout(self.table_layout)

        # Add frozen table
        self.frozen_table = QTableView()
        self.table_layout.addWidget(self.frozen_table)

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

    def closeEvent(self, event):
        """Restore the initial size when the settings form is reopened."""
        self.resize(450, 700)
        super().closeEvent(event)