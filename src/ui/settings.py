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
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setHorizontalSpacing(16)
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

        # --- Column 2 & 3: Stylesheet (Colors/Fonts) split into two columns ---
        style_col2 = QVBoxLayout()
        style_col2.setContentsMargins(24, 0, 0, 0)
        style_col3 = QVBoxLayout()
        style_col3.setContentsMargins(0, 0, 0, 0)
        style_heading = QLabel("Stylesheet")
        style_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        style_col2.addWidget(style_heading)

        # Helper to add a blank label for alignment
        def blank_label():
            lbl = QLabel("")
            lbl.setFixedHeight(8)
            return lbl

        # --- Stylesheet helpers ---
        from PyQt5.QtWidgets import QColorDialog, QMenu
        def color_picker_row(label_text, entry, pick_btn):
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            row.addWidget(entry)
            row.addWidget(pick_btn)
            return row
        def pick_color(entry):
            color = QColorDialog.getColor()
            if color.isValid():
                entry.setText(color.name())
        font_sizes = ["6", "8", "10", "11", "12", "13", "14", "15", "16", "18", "20", "22", "24"]
        def font_size_picker_row(label_text, entry, pick_btn):
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            row.addWidget(entry)
            row.addWidget(pick_btn)
            return row
        def pick_font_size(entry):
            menu = QMenu()
            for size in font_sizes:
                action = menu.addAction(size)
                action.triggered.connect(lambda checked, s=size: entry.setText(s))
            menu.exec_(entry.mapToGlobal(entry.rect().bottomRight()))

        # --- Column 2 & 3: Stylesheet (Colors/Fonts) split into two columns ---
        style_col2 = QVBoxLayout()
        style_col2.setContentsMargins(24, 0, 0, 0)
        style_col3 = QVBoxLayout()
        style_col3.setContentsMargins(0, 0, 0, 0)
        style_heading = QLabel("Stylesheet")
        style_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        style_col2.addWidget(style_heading)

        # Redefine add_style_row to allow for single color fields (border/title)
        def add_style_row_v2(layout, label_text, area, bg_key, fg_key, font_key, default_bg, default_fg, default_font):
            if fg_key and font_key:
                # Normal area: bg, fg, font
                bg_entry = QLineEdit(self.default_settings.get(bg_key, default_bg))
                bg_btn = QPushButton("…")
                bg_btn.setFixedWidth(28)
                bg_btn.clicked.connect(lambda: pick_color(bg_entry))
                fg_entry = QLineEdit(self.default_settings.get(fg_key, default_fg))
                fg_btn = QPushButton("…")
                fg_btn.setFixedWidth(28)
                fg_btn.clicked.connect(lambda: pick_color(fg_entry))
                font_entry = QLineEdit(str(self.default_settings.get(font_key, default_font)))
                font_btn = QPushButton("…")
                font_btn.setFixedWidth(28)
                font_btn.clicked.connect(lambda: pick_font_size(font_entry))
                setattr(self, f"{area}_bg_entry", bg_entry)
                setattr(self, f"{area}_fg_entry", fg_entry)
                setattr(self, f"{area}_font_entry", font_entry)
                layout.addLayout(color_picker_row(f"{label_text.split(' ')[0]} BG Color:", bg_entry, bg_btn))
                layout.addLayout(color_picker_row(f"{label_text.split(' ')[0]} Text Color:", fg_entry, fg_btn))
                layout.addLayout(font_size_picker_row(f"{label_text.split(' ')[0]} Font Size:", font_entry, font_btn))
            else:
                # Single color field (border/title)
                entry = QLineEdit(self.default_settings.get(bg_key, default_bg))
                btn = QPushButton("…")
                btn.setFixedWidth(28)
                btn.clicked.connect(lambda: pick_color(entry))
                setattr(self, f"{area}_entry", entry)
                layout.addLayout(color_picker_row(label_text + ":", entry, btn))

        # List of all style rows (label, area, label_prefix, bg_key, fg_key, font_key, default_bg, default_fg, default_font)
        style_rows = [
            ("Form BG Color", "form", "Form", "form_bg_color", "form_fg_color", "form_font_size", "#e3f2fd", "#222222", "12"),
            ("Form Text Color", "form", "Form", "form_bg_color", "form_fg_color", "form_font_size", "#e3f2fd", "#222222", "12"),
            ("Form Font Size", "form", "Form", "form_bg_color", "form_fg_color", "form_font_size", "#e3f2fd", "#222222", "12"),
            ("Button BG Color", "button", "Button", "button_bg_color", "button_fg_color", "button_font_size", "#1976d2", "#ffffff", "12"),
            ("Button Text Color", "button", "Button", "button_bg_color", "button_fg_color", "button_font_size", "#1976d2", "#ffffff", "12"),
            ("Button Font Size", "button", "Button", "button_bg_color", "button_fg_color", "button_font_size", "#1976d2", "#ffffff", "12"),
            ("Table BG Color", "table", "Table", "table_bg_color", "table_fg_color", "table_font_size", "#ffffff", "#222222", "12"),
            ("Table Text Color", "table", "Table", "table_bg_color", "table_fg_color", "table_font_size", "#ffffff", "#222222", "12"),
            ("Table Font Size", "table", "Table", "table_bg_color", "table_fg_color", "table_font_size", "#ffffff", "#222222", "12"),
            ("Table Header BG Color", "table_header", "Table Header", "table_header_bg_color", "table_header_fg_color", "table_header_font_size", "#1976d2", "#ffffff", "12"),
            ("Table Header Text Color", "table_header", "Table Header", "table_header_bg_color", "table_header_fg_color", "table_header_font_size", "#1976d2", "#ffffff", "12"),
            ("Table Header Font Size", "table_header", "Table Header", "table_header_bg_color", "table_header_fg_color", "table_header_font_size", "#1976d2", "#ffffff", "12"),
            ("Metadata BG Color", "metadata", "Metadata", "metadata_bg_color", "metadata_fg_color", "metadata_font_size", "#e3f2fd", "#222222", "12"),
            ("Metadata Text Color", "metadata", "Metadata", "metadata_bg_color", "metadata_fg_color", "metadata_font_size", "#e3f2fd", "#222222", "12"),
            ("Metadata Font Size", "metadata", "Metadata", "metadata_bg_color", "metadata_fg_color", "metadata_font_size", "#e3f2fd", "#222222", "12"),
            ("Form Border Color", "form_border", "Form Border", "form_border_color", None, None, "#1976d2", None, None),
            ("Form Title Color", "form_title", "Form Title", "form_title_color", None, None, "#222222", None, None),
        ]
        # For this example, we have 17 rows, so col2: 9 rows (0-8), col3: 8 rows (9-16)

        # Add rows to col2 (rows 0-8)
        for i in range(9):
            label_text, area, label_prefix, bg_key, fg_key, font_key, default_bg, default_fg, default_font = style_rows[i]
            add_style_row_v2(style_col2, label_text, area, bg_key, fg_key, font_key, default_bg, default_fg, default_font)
        # Add rows to col3 (rows 9-16)
        for i in range(9, len(style_rows)):
            label_text, area, label_prefix, bg_key, fg_key, font_key, default_bg, default_fg, default_font = style_rows[i]
            add_style_row_v2(style_col3, label_text, area, bg_key, fg_key, font_key, default_bg, default_fg, default_font)

        # --- Layout: Add columns to main layout ---
        style_cols_layout = QHBoxLayout()
        style_cols_layout.addLayout(style_col2, 1)
        style_cols_layout.addLayout(style_col3, 1)
        style_cols_layout.setContentsMargins(0, 0, 0, 0)

        # Add columns to main layout, each with 50% stretch and padding
        columns_layout.addLayout(metadata_col, 1)
        columns_layout.addLayout(style_cols_layout, 1)
        columns_layout.setContentsMargins(0, 10, 0, 10)
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
        for i in range(style_col2.count()):
            layout_item = style_col2.itemAt(i)
            if isinstance(layout_item, QHBoxLayout):
                for j in range(layout_item.count()):
                    widget = layout_item.itemAt(j).widget()
                    if isinstance(widget, (QLineEdit, QComboBox)):
                        widget.setMinimumWidth(min_entry_width)
        for i in range(style_col3.count()):
            layout_item = style_col3.itemAt(i)
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
        updated_settings = {key: entry.text() for key, entry in self.entries.items()}
        updated_settings["theme"] = self.theme_dropdown.currentText()
        updated_settings["form_bg_color"] = self.form_bg_entry.text()
        updated_settings["form_fg_color"] = self.form_fg_entry.text()
        updated_settings["form_font_size"] = self.form_font_entry.text()
        updated_settings["button_bg_color"] = self.button_bg_entry.text()
        updated_settings["button_fg_color"] = self.button_fg_entry.text()
        updated_settings["button_font_size"] = self.button_font_entry.text()
        updated_settings["table_bg_color"] = self.table_bg_entry.text()
        updated_settings["table_fg_color"] = self.table_fg_entry.text()
        updated_settings["table_font_size"] = self.table_font_entry.text()
        updated_settings["table_header_bg_color"] = self.table_header_bg_entry.text()
        updated_settings["table_header_fg_color"] = self.table_header_fg_entry.text()
        updated_settings["table_header_font_size"] = self.table_header_font_entry.text()
        updated_settings["metadata_bg_color"] = self.metadata_bg_entry.text()
        updated_settings["metadata_fg_color"] = self.metadata_fg_entry.text()
        updated_settings["metadata_font_size"] = self.metadata_font_entry.text()
        updated_settings["form_border_color"] = self.form_border_color_entry.text()
        updated_settings["form_title_color"] = self.form_title_color_entry.text()
        from logic.db_interface import set_all_defaults
        try:
            set_all_defaults(updated_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default settings: {e}")
            return
        if self.on_theme_change:
            self.on_theme_change(self.theme_dropdown.currentText())
        self.accept()

    def restore_all_colors_fonts(self):
        FACTORY_DEFAULTS = {
            "form_bg_color": "#e3f2fd",
            "form_fg_color": "#222222",
            "form_font_size": "12",
            "button_bg_color": "#1976d2",
            "button_fg_color": "#ffffff",
            "button_font_size": "12",
            "table_bg_color": "#ffffff",
            "table_fg_color": "#222222",
            "table_font_size": "12",
            "table_header_bg_color": "#1976d2",
            "table_header_fg_color": "#ffffff",
            "table_header_font_size": "12",
            "metadata_bg_color": "#e3f2fd",
            "metadata_fg_color": "#222222",
            "metadata_font_size": "12",
            "form_border_color": "#1976d2",
            "form_title_color": "#222222",
        }
        self.form_bg_entry.setText(FACTORY_DEFAULTS["form_bg_color"])
        self.form_fg_entry.setText(FACTORY_DEFAULTS["form_fg_color"])
        self.form_font_entry.setText(FACTORY_DEFAULTS["form_font_size"])
        self.button_bg_entry.setText(FACTORY_DEFAULTS["button_bg_color"])
        self.button_fg_entry.setText(FACTORY_DEFAULTS["button_fg_color"])
        self.button_font_entry.setText(FACTORY_DEFAULTS["button_font_size"])
        self.table_bg_entry.setText(FACTORY_DEFAULTS["table_bg_color"])
        self.table_fg_entry.setText(FACTORY_DEFAULTS["table_fg_color"])
        self.table_font_entry.setText(FACTORY_DEFAULTS["table_font_size"])
        self.table_header_bg_entry.setText(FACTORY_DEFAULTS["table_header_bg_color"])
        self.table_header_fg_entry.setText(FACTORY_DEFAULTS["table_header_fg_color"])
        self.table_header_font_entry.setText(FACTORY_DEFAULTS["table_header_font_size"])
        self.metadata_bg_entry.setText(FACTORY_DEFAULTS["metadata_bg_color"])
        self.metadata_fg_entry.setText(FACTORY_DEFAULTS["metadata_fg_color"])
        self.metadata_font_entry.setText(FACTORY_DEFAULTS["metadata_font_size"])
        self.form_border_color_entry.setText(FACTORY_DEFAULTS["form_border_color"])
        self.form_title_color_entry.setText(FACTORY_DEFAULTS["form_title_color"])
