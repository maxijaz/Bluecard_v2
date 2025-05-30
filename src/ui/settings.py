from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy, QFrame
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

        # --- Layout: Two columns for Metadata and Stylesheet ---
        columns_layout = QHBoxLayout()

        # --- Column 1: Default Metadata ---
        metadata_col = QVBoxLayout()
        metadata_heading = QLabel("Default Metadata")
        metadata_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        metadata_col.addWidget(metadata_heading)
        self.entries = {}
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)  # Right-align labels for even spacing
        form_layout.setFormAlignment(Qt.AlignLeft)    # Align form to left
        form_layout.setHorizontalSpacing(16)          # Match spacing to column 2
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
        metadata_col.addLayout(form_layout)
        metadata_col.addStretch(1)

        # --- Column 2: Stylesheet (Colors/Fonts) ---
        style_col = QVBoxLayout()
        style_col.setContentsMargins(24, 0, 0, 0)     # left margin for right column
        style_heading = QLabel("Stylesheet")
        style_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        style_col.addWidget(style_heading)

        # All style/color label texts for dynamic widths
        style_labels = [
            "Metadata Font Size:", "Metadata Text Color:", "Button Font Size:",
            "Table Header Font Size:", "Table Header BG Color:", "Table Header Text Color:",
            "Table Data Font Size:", "Table Data Text Color:", "Form Background Color:",
            "Button Background Color:", "Button Text Color:", "Table Background Color:", "Select Theme:"
        ]
        # Add extra width for bold font and padding
        max_label_width = max(QtGui.QFontMetrics(self.font()).width(lbl) for lbl in style_labels) + 40

        # Helper for right-aligned bold labels in style_col
        def right_bold_label(text):
            lbl = QLabel(text)
            lbl.setFixedWidth(max_label_width)
            lbl.setStyleSheet("font-weight: bold;")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return lbl

        # Helper for bold labels (used for theme label, etc.)
        def bold_label(text):
            lbl = QLabel(text)
            lbl.setFixedWidth(max_label_width)
            lbl.setStyleSheet("font-weight: bold;")
            return lbl

        # Theme selection at top of column 2
        theme_layout = QHBoxLayout()
        theme_label = bold_label("Select Theme:")
        theme_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Right align label
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(self.themes)
        self.theme_dropdown.setCurrentText(self.current_theme)
        self.theme_dropdown.setMinimumWidth(min_entry_width)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        style_col.addLayout(theme_layout)

        # Helper to robustly set dropdown values, always allowing the saved value
        def set_font_size_dropdown(dropdown, value):
            font_sizes = ["6", "8", "10", "11", "12", "13", "14", "15", "16", "18", "20", "22", "24"]
            dropdown.clear()
            dropdown.addItems(font_sizes)
            if str(value) not in font_sizes:
                # Insert in correct order if not present
                font_sizes_with_value = font_sizes + [str(value)]
                font_sizes_with_value = sorted(set(font_sizes_with_value), key=lambda x: int(x))
                dropdown.clear()
                dropdown.addItems(font_sizes_with_value)
            dropdown.setCurrentText(str(value))

        # Helper to robustly set dropdown values (add if missing, then select)
        def set_dropdown_value(dropdown, value, default_items):
            value = str(value)
            # Ensure default_items are sorted numerically if they are numbers
            try:
                sorted_items = sorted(set(default_items), key=lambda x: int(x))
            except Exception:
                sorted_items = list(default_items)
            items = [dropdown.itemText(i) for i in range(dropdown.count())]
            if value not in items:
                sorted_items.append(value)
                sorted_items = sorted(set(sorted_items), key=lambda x: int(x))
            dropdown.clear()
            dropdown.addItems(sorted_items)
            dropdown.setCurrentText(value)

        font_sizes = ["6", "8", "10", "11", "12", "13", "14", "15", "16", "18", "20", "22", "24"]

        # Metadata font size and color
        metadata_font_size_layout = QHBoxLayout()
        metadata_font_size_label = right_bold_label("Metadata Font Size:")
        self.metadata_font_size_dropdown = QComboBox()
        set_dropdown_value(self.metadata_font_size_dropdown, self.default_settings.get("metadata_font_size", "12"), font_sizes)
        metadata_font_size_layout.addWidget(metadata_font_size_label)
        metadata_font_size_layout.addWidget(self.metadata_font_size_dropdown)
        style_col.addLayout(metadata_font_size_layout)

        metadata_fg_color_layout = QHBoxLayout()
        metadata_fg_color_label = right_bold_label("Metadata Text Color:")
        self.metadata_fg_color_entry = QLineEdit(self.default_settings.get("metadata_fg_color", "#222222"))
        metadata_fg_color_layout.addWidget(metadata_fg_color_label)
        metadata_fg_color_layout.addWidget(self.metadata_fg_color_entry)
        style_col.addLayout(metadata_fg_color_layout)

        # Button font size
        button_font_size_layout = QHBoxLayout()
        button_font_size_label = right_bold_label("Button Font Size:")
        self.button_font_size_dropdown = QComboBox()
        set_dropdown_value(self.button_font_size_dropdown, self.default_settings.get("button_font_size", "12"), font_sizes)
        button_font_size_layout.addWidget(button_font_size_label)
        button_font_size_layout.addWidget(self.button_font_size_dropdown)
        style_col.addLayout(button_font_size_layout)

        # Table header font size and color
        table_header_font_size_layout = QHBoxLayout()
        table_header_font_size_label = right_bold_label("Table Header Font Size:")
        self.table_header_font_size_dropdown = QComboBox()
        set_dropdown_value(self.table_header_font_size_dropdown, self.default_settings.get("table_header_font_size", "12"), font_sizes)
        table_header_font_size_layout.addWidget(table_header_font_size_label)
        table_header_font_size_layout.addWidget(self.table_header_font_size_dropdown)
        style_col.addLayout(table_header_font_size_layout)

        table_header_bg_color_layout = QHBoxLayout()
        table_header_bg_color_label = right_bold_label("Table Header BG Color:")
        self.table_header_bg_color_entry = QLineEdit(self.default_settings.get("table_header_bg_color", "#1976d2"))
        table_header_bg_color_layout.addWidget(table_header_bg_color_label)
        table_header_bg_color_layout.addWidget(self.table_header_bg_color_entry)
        style_col.addLayout(table_header_bg_color_layout)

        table_header_fg_color_layout = QHBoxLayout()
        table_header_fg_color_label = right_bold_label("Table Header Text Color:")
        self.table_header_fg_color_entry = QLineEdit(self.default_settings.get("table_header_fg_color", "#ffffff"))
        table_header_fg_color_layout.addWidget(table_header_fg_color_label)
        table_header_fg_color_layout.addWidget(self.table_header_fg_color_entry)
        style_col.addLayout(table_header_fg_color_layout)

        # Table data font size and color
        table_font_size_layout = QHBoxLayout()
        table_font_size_label = right_bold_label("Table Data Font Size:")
        self.table_font_size_dropdown = QComboBox()
        set_dropdown_value(self.table_font_size_dropdown, self.default_settings.get("table_font_size", "12"), font_sizes)
        table_font_size_layout.addWidget(table_font_size_label)
        table_font_size_layout.addWidget(self.table_font_size_dropdown)
        style_col.addLayout(table_font_size_layout)

        table_fg_color_layout = QHBoxLayout()
        table_fg_color_label = right_bold_label("Table Data Text Color:")
        self.table_fg_color_entry = QLineEdit(self.default_settings.get("table_fg_color", "#222222"))
        table_fg_color_layout.addWidget(table_fg_color_label)
        table_fg_color_layout.addWidget(self.table_fg_color_entry)
        style_col.addLayout(table_fg_color_layout)

        # Form, button, table background colors
        form_bg_layout = QHBoxLayout()
        form_bg_label = right_bold_label("Form Background Color:")
        self.form_bg_entry = QLineEdit(self.default_settings.get("form_bg_color", "#e3f2fd"))
        form_bg_layout.addWidget(form_bg_label)
        form_bg_layout.addWidget(self.form_bg_entry)
        style_col.addLayout(form_bg_layout)

        button_bg_layout = QHBoxLayout()
        button_bg_label = right_bold_label("Button Background Color:")
        self.button_bg_entry = QLineEdit(self.default_settings.get("button_bg_color", "#1976d2"))
        button_bg_layout.addWidget(button_bg_label)
        button_bg_layout.addWidget(self.button_bg_entry)
        style_col.addLayout(button_bg_layout)

        button_fg_layout = QHBoxLayout()
        button_fg_label = right_bold_label("Button Text Color:")
        self.button_fg_entry = QLineEdit(self.default_settings.get("button_fg_color", "#ffffff"))
        button_fg_layout.addWidget(button_fg_label)
        button_fg_layout.addWidget(self.button_fg_entry)
        style_col.addLayout(button_fg_layout)

        table_bg_layout = QHBoxLayout()
        table_bg_label = right_bold_label("Table Background Color:")
        self.table_bg_entry = QLineEdit(self.default_settings.get("table_bg_color", "#ffffff"))
        table_bg_layout.addWidget(table_bg_label)
        table_bg_layout.addWidget(self.table_bg_entry)
        style_col.addLayout(table_bg_layout)

        # Add a vertical line between columns
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setLineWidth(2)
        divider.setStyleSheet("background: #b0b0b0;")

        # Set symmetrical margins for columns and outer layout
        layout.setContentsMargins(20, 0, 20, 0)  # 20px left/right padding for the whole form
        metadata_col.setContentsMargins(0, 0, 24, 0)  # right margin for left column
        style_col.setContentsMargins(24, 0, 0, 0)     # left margin for right column

        # Add columns to main layout, each with 50% stretch and padding
        columns_layout.addLayout(metadata_col, 1)
        columns_layout.addWidget(divider)
        columns_layout.addLayout(style_col, 1)
        columns_layout.setContentsMargins(0, 10, 0, 10)  # Remove horizontal margins
        layout.addLayout(columns_layout)

        # Add a vertical expanding spacer so the form stays at the top
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Add stretch before buttons for spacing
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(90)
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(90)
        cancel_button.clicked.connect(self.reject)
        restore_defaults_button = QPushButton("Restore All Colors/Fonts")
        restore_defaults_button.setMinimumWidth(150)
        restore_defaults_button.clicked.connect(self.restore_all_colors_fonts)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(restore_defaults_button)
        button_layout.addStretch(1)  # Add stretch after buttons for spacing
        layout.addLayout(button_layout)
        layout.addSpacing(16)  # Add bottom margin below buttons

        # For all QLineEdit and QComboBox in style_col, set minimum width
        for i in range(style_col.count()):
            layout_item = style_col.itemAt(i)
            if isinstance(layout_item, QHBoxLayout):
                for j in range(layout_item.count()):
                    widget = layout_item.itemAt(j).widget()
                    if isinstance(widget, (QLineEdit, QComboBox)):
                        widget.setMinimumWidth(min_entry_width)

        # Add right padding to data entry fields in column 1
        for i in range(form_layout.rowCount()):
            field_widget = form_layout.itemAt(i, QFormLayout.FieldRole)
            if field_widget is not None:
                widget = field_widget.widget()
                if isinstance(widget, QLineEdit):
                    widget.setStyleSheet("padding-right: 16px;")

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
        updated_settings["metadata_font_size"] = self.metadata_font_size_dropdown.currentText()
        updated_settings["button_font_size"] = self.button_font_size_dropdown.currentText()
        updated_settings["table_header_font_size"] = self.table_header_font_size_dropdown.currentText()
        updated_settings["table_font_size"] = self.table_font_size_dropdown.currentText()
        updated_settings["form_bg_color"] = self.form_bg_entry.text()
        updated_settings["button_bg_color"] = self.button_bg_entry.text()
        updated_settings["button_fg_color"] = self.button_fg_entry.text()
        updated_settings["table_bg_color"] = self.table_bg_entry.text()
        updated_settings["metadata_fg_color"] = self.metadata_fg_color_entry.text()
        updated_settings["table_header_bg_color"] = self.table_header_bg_color_entry.text()
        updated_settings["table_header_fg_color"] = self.table_header_fg_color_entry.text()
        updated_settings["table_fg_color"] = self.table_fg_color_entry.text()
        updated_settings["form_font_size"] = self.form_font_size_dropdown.currentText()
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
            "metadata_font_size": "12",
            "button_font_size": "12",
            "table_header_font_size": "12",
            "table_font_size": "12",
            "form_bg_color": "#e3f2fd",
            "form_fg_color": "#222222",
            "button_bg_color": "#1976d2",
            "button_fg_color": "#ffffff",
            "table_bg_color": "#ffffff",
            "table_fg_color": "#222222",
            "table_header_bg_color": "#1976d2",
            "table_header_fg_color": "#ffffff",
            "form_font_size": "12",
        }
        self.metadata_font_size_dropdown.setCurrentText(FACTORY_DEFAULTS["metadata_font_size"])
        self.button_font_size_dropdown.setCurrentText(FACTORY_DEFAULTS["button_font_size"])
        self.table_header_font_size_dropdown.setCurrentText(FACTORY_DEFAULTS["table_header_font_size"])
        self.table_font_size_dropdown.setCurrentText(FACTORY_DEFAULTS["table_font_size"])
        self.form_font_size_dropdown.setCurrentText(FACTORY_DEFAULTS.get("form_font_size", "12"))
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