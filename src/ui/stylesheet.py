from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QSizePolicy, QColorDialog, QMenu
)
from PyQt5.QtCore import Qt
from logic.db_interface import get_all_defaults, set_all_defaults

class StylesheetForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stylesheet Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.default_settings = self.load_default_settings()
        self.init_ui()

    def load_default_settings(self):
        return get_all_defaults()

    def init_ui(self):
        layout = QVBoxLayout(self)
        style_heading = QLabel("Stylesheet")
        style_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(style_heading)
        style_grid = QGridLayout()
        style_grid.setHorizontalSpacing(16)
        style_grid.setVerticalSpacing(6)
        style_grid.setContentsMargins(0, 0, 0, 0)
        def bold_right_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold;")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return lbl
        style_fields = [
            ("Form Title Color", "form_title", "form_title_color", "color", "#222222"),
            ("Form BG Color", "form_bg", "form_bg_color", "color", "#e3f2fd"),
            ("Form Text Color", "form_fg", "form_fg_color", "color", "#222222"),
            ("Form Border Color", "form_border", "form_border_color", "color", "#1976d2"),
            ("Form Font Size", "form_font", "form_font_size", "font", "12"),
            ("Metadata BG Color", "metadata_bg", "metadata_bg_color", "color", "#e3f2fd"),
            ("Metadata Text Color", "metadata_fg", "metadata_fg_color", "color", "#222222"),
            ("Metadata Font Size", "metadata_font", "metadata_font_size", "font", "12"),
            ("Table BG Color", "table_bg", "table_bg_color", "color", "#ffffff"),
            ("Button BG Color", "button_bg", "button_bg_color", "color", "#1976d2"),
            ("Button Text Color", "button_fg", "button_fg_color", "color", "#ffffff"),
            ("Button Border Color", "button_border", "button_border_color", "color", "#1976d2"),
            ("Button Font Size", "button_font", "button_font_size", "font", "12"),
            ("Table Header BG Color", "table_header_bg", "table_header_bg_color", "color", "#1976d2"),
            ("Table Header Text Color", "table_header_fg", "table_header_fg_color", "color", "#ffffff"),
            ("Table Header Font Size", "table_header_font", "table_header_font_size", "font", "12"),
            ("Table Text Color", "table_fg", "table_fg_color", "color", "#222222"),
            ("Table Font Size", "table_font", "table_font_size", "font", "12"),
        ]
        def pick_color(entry):
            color = QColorDialog.getColor()
            if color.isValid():
                entry.setText(color.name())
        font_sizes = ["6", "8", "10", "11", "12", "13", "14", "15", "16", "18", "20", "22", "24", "26", "28", "30"]
        def pick_font_size(entry):
            menu = QMenu()
            for size in font_sizes:
                action = menu.addAction(size)
                action.triggered.connect(lambda checked, s=size: entry.setText(s))
            menu.exec_(entry.mapToGlobal(entry.rect().bottomRight()))
        for i in range(9):
            if i < len(style_fields):
                label_text, area, key, typ, default = style_fields[i]
                label = bold_right_label(label_text + ":")
                if typ == "color":
                    entry = QLineEdit(self.default_settings.get(key, default))
                    btn = QPushButton("…")
                    btn.setFixedWidth(28)
                    btn.clicked.connect(lambda _, e=entry: pick_color(e))
                elif typ == "font":
                    entry = QLineEdit(str(self.default_settings.get(key, default)))
                    btn = QPushButton("…")
                    btn.setFixedWidth(28)
                    btn.clicked.connect(lambda _, e=entry: pick_font_size(e))
                entry.setMinimumWidth(140)
                entry.setMaximumWidth(300)
                entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                setattr(self, f"{area}_entry", entry)
                style_grid.addWidget(label, i, 0)
                style_grid.addWidget(entry, i, 1)
                style_grid.addWidget(btn, i, 2)
        for i in range(9, 18):
            if i < len(style_fields):
                label_text, area, key, typ, default = style_fields[i]
                label = bold_right_label(label_text + ":")
                if typ == "color":
                    entry = QLineEdit(self.default_settings.get(key, default))
                    btn = QPushButton("…")
                    btn.setFixedWidth(28)
                    btn.clicked.connect(lambda _, e=entry: pick_color(e))
                elif typ == "font":
                    entry = QLineEdit(str(self.default_settings.get(key, default)))
                    btn = QPushButton("…")
                    btn.setFixedWidth(28)
                    btn.clicked.connect(lambda _, e=entry: pick_font_size(e))
                entry.setMinimumWidth(140)
                entry.setMaximumWidth(300)
                entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                setattr(self, f"{area}_entry", entry)
                style_grid.addWidget(label, i-9, 3)
                style_grid.addWidget(entry, i-9, 4)
                style_grid.addWidget(btn, i-9, 5)
        layout.addLayout(style_grid)
        layout.addStretch(1)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        save_button = QPushButton("Save")
        save_button.setMinimumWidth(90)
        save_button.clicked.connect(self.save_settings)
        restore_defaults_button = QPushButton("Restore All Colors/Fonts")
        restore_defaults_button.setMinimumWidth(150)
        restore_defaults_button.clicked.connect(self.restore_all_colors_fonts)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(90)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(restore_defaults_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        layout.addSpacing(16)

    def save_settings(self):
        updated_settings = {}
        style_fields = [
            ("form_title_color", self.form_title_entry),
            ("form_bg_color", self.form_bg_entry),
            ("form_fg_color", self.form_fg_entry),
            ("form_border_color", self.form_border_entry),
            ("form_font_size", self.form_font_entry),
            ("metadata_bg_color", self.metadata_bg_entry),
            ("metadata_fg_color", self.metadata_fg_entry),
            ("metadata_font_size", self.metadata_font_entry),
            ("table_bg_color", self.table_bg_entry),
            ("button_bg_color", self.button_bg_entry),
            ("button_fg_color", self.button_fg_entry),
            ("button_border_color", self.button_border_entry),
            ("button_font_size", self.button_font_entry),
            ("table_header_bg_color", self.table_header_bg_entry),
            ("table_header_fg_color", self.table_header_fg_entry),
            ("table_header_font_size", self.table_header_font_entry),
            ("table_fg_color", self.table_fg_entry),
            ("table_font_size", self.table_font_entry),
        ]
        for key, entry in style_fields:
            updated_settings[key] = entry.text()
        try:
            set_all_defaults(updated_settings)
            # --- Instant update: reapply global stylesheet and font size ---
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtGui import QFont
            form_font_size = int(updated_settings.get("form_font_size") or 12)
            button_font_size = int(updated_settings.get("button_font_size") or form_font_size)
            table_font_size = int(updated_settings.get("table_font_size") or form_font_size)
            table_header_font_size = int(updated_settings.get("table_header_font_size") or form_font_size)
            form_bg_color = updated_settings.get("form_bg_color", "#e3f2fd")
            button_bg_color = updated_settings.get("button_bg_color", "#1976d2")
            button_fg_color = updated_settings.get("button_fg_color", "#ffffff")
            table_bg_color = updated_settings.get("table_bg_color", "#ffffff")
            table_fg_color = updated_settings.get("table_fg_color", "#222222")
            table_header_bg_color = updated_settings.get("table_header_bg_color", "#1976d2")
            table_header_fg_color = updated_settings.get("table_header_fg_color", "#ffffff")
            # Set the default font for general UI (form/metadata)
            QApplication.instance().setFont(QFont("Segoe UI", form_font_size))
            style = f"""
                QWidget {{ background-color: {form_bg_color}; }}
                QLabel, QLineEdit {{ font-size: {form_font_size}pt; }}
                QPushButton {{ background-color: {button_bg_color}; color: {button_fg_color}; font-size: {button_font_size}pt; }}
                QTableView, QTableWidget {{ background-color: {table_bg_color}; }}
                QHeaderView::section {{ background-color: {table_header_bg_color}; color: {table_header_fg_color}; font-size: {table_header_font_size}pt; }}
                QTableWidget::item {{ color: {table_fg_color}; font-size: {table_font_size}pt; }}
            """
            QApplication.instance().setStyleSheet(style)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save stylesheet settings: {e}")
            return
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
        for key, value in FACTORY_DEFAULTS.items():
            attr = key.replace('_color', '_entry').replace('_size', '_entry').replace('_font', '_font_entry')
            entry = getattr(self, attr, None)
            if entry:
                entry.setText(value)
