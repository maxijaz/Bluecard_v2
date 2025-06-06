from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFormLayout, QMessageBox, QSpacerItem, QSizePolicy, QWidget, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
import json
import os

from logic.db_interface import get_form_settings, get_all_defaults, set_all_defaults, get_teacher_defaults, set_teacher_defaults, get_message_defaults
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
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        default_settings = get_all_defaults()
        font_size = int(form_settings.get("font_size") or default_settings.get("form_font_size", default_settings.get("button_font_size", 12)))
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont(form_settings.get("font_family", "Segoe UI"), font_size))
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
        # --- PATCH: Load teacher defaults from DB ---
        self.teacher_defaults = get_teacher_defaults()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        metadata_col = QVBoxLayout()
        metadata_heading = QLabel("Default Metadata (Teacher Defaults)")
        metadata_heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        metadata_col.addWidget(metadata_heading)
        # Separator 1: under heading
        heading_sep = QWidget()
        heading_sep.setFixedHeight(4)
        heading_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        metadata_col.addWidget(heading_sep)
        # Info text
        info_label = QLabel("Set default values here for all new classes. All values can be changed by editing metadata.")
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
            value = self.teacher_defaults.get(key, "")
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
        # Buttons (Save, Cancel, Check Factory Defaults) in one row
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        save_button = QPushButton("Save and Close")
        save_button.setMinimumWidth(90)
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumWidth(90)
        cancel_button.clicked.connect(self.reject)
        check_defaults_btn = QPushButton("Check Factory Defaults")
        check_defaults_btn.setMinimumWidth(180)
        check_defaults_btn.clicked.connect(self.check_factory_defaults)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(check_defaults_btn)
        button_layout.addStretch(1)
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

    def check_factory_defaults(self):
        """Check DB defaults vs factory_defaults.json and show differences."""
        try:
            from logic.build_sqlite_db import check_factory_defaults_vs_db
            from logic.db_interface import get_connection
            # Get DB connection
            conn = get_connection()
            # Load factory defaults from JSON
            factory_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'factory_defaults.json')
            with open(factory_path, 'r', encoding='utf-8') as f:
                factory_defaults = json.load(f)
            result = check_factory_defaults_vs_db(conn, factory_defaults)
            conn.close()
            if not result or (isinstance(result, str) and result.strip() == "OK"):
                QMessageBox.information(self, "Factory Defaults Check", "All settings match factory defaults.")
            else:
                # Show differences in a scrollable dialog
                dlg = QDialog(self)
                dlg.setWindowTitle("Factory Defaults Differences")
                dlg.resize(700, 500)
                vbox = QVBoxLayout(dlg)
                label = QLabel("Differences between DB and factory_defaults.json:")
                vbox.addWidget(label)
                from PyQt5.QtWidgets import QTextEdit
                text = QTextEdit()
                text.setReadOnly(True)
                text.setText(str(result))
                vbox.addWidget(text)
                btn = QPushButton("Close")
                btn.clicked.connect(dlg.accept)
                vbox.addWidget(btn)
                dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check factory defaults:\n{e}")

    def save_settings(self):
        """Save teacher defaults to the DB."""
        new_defaults = {key: entry.text().strip() for key, entry in self.entries.items()}
        set_teacher_defaults(new_defaults)
        # Use message style defaults from DB
        msg_defaults = get_message_defaults()
        bg = msg_defaults.get("message_bg_color", "#2980f0")
        fg = msg_defaults.get("message_fg_color", "#fff")
        border = msg_defaults.get("message_border_color", "#1565c0")
        border_width = msg_defaults.get("message_border_width", "3")
        border_radius = msg_defaults.get("message_border_radius", "12")
        padding = msg_defaults.get("message_padding", "18px 32px")
        font_size = msg_defaults.get("message_font_size", "13")
        font_bold = msg_defaults.get("message_font_bold", "true")
        font_weight = "bold" if str(font_bold).lower() in ("1", "true", "yes") else "normal"
        style = f"background: {bg}; color: {fg}; border: {border_width}px solid {border}; padding: {padding}; font-size: {font_size}pt; font-weight: {font_weight}; border-radius: {border_radius}px;"
        from PyQt5.QtCore import QTimer, Qt
        from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
        msg_dialog = QDialog(self, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
        msg_dialog.setModal(False)
        layout = QVBoxLayout(msg_dialog)
        label = QLabel("Teacher defaults have been updated.")
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        msg_dialog.adjustSize()
        # Center the dialog on the screen
        screen = self.window().screen() if hasattr(self.window(), 'screen') else None
        if screen:
            scr_geo = screen.geometry()
            x = scr_geo.x() + (scr_geo.width() - msg_dialog.width()) // 2
            y = scr_geo.y() + (scr_geo.height() - msg_dialog.height()) // 2
        else:
            x = 400
            y = 300
        msg_dialog.move(x, y)
        msg_dialog.show()
        self._msg_dialog = msg_dialog  # Keep reference to prevent GC
        QTimer.singleShot(2000, msg_dialog.close)
        QTimer.singleShot(2050, self.accept)

    def showEvent(self, event):
        super().showEvent(event)
        print(f"[DEBUG] SettingsForm shown: width={self.width()}, height={self.height()}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        print(f"[DEBUG] SettingsForm resized: width={self.width()}, height={self.height()}")

