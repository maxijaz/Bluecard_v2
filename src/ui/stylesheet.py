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
        # --- PATCH: Read color_toggle from defaults and set toggle state ---
        self.color_toggle = self.default_settings.get("color_toggle", "yes").lower() in ("yes", "on", "true", "1")
        self.init_ui()
        # --- Track initial state for change detection (after UI fields are created) ---
        self._initial_values = self._get_current_values()

    def load_default_settings(self):
        return get_all_defaults()

    def init_ui(self):
        layout = QVBoxLayout(self)
        style_heading = QLabel("Stylesheet")
        style_heading.setObjectName("formTitle")  # Set objectName for targeted styling
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
        save_button.clicked.connect(self._debug_save_settings)
        restore_defaults_button = QPushButton("Restore All Colors/Fonts")
        restore_defaults_button.setMinimumWidth(150)
        restore_defaults_button.clicked.connect(self._debug_restore_all_colors_fonts)
        close_button = QPushButton("Close")
        close_button.setMinimumWidth(90)
        close_button.clicked.connect(self._debug_close_with_prompt)

        # --- Add Toggle Color On/Off Button ---
        toggle_color_button = QPushButton()
        toggle_color_button.setMinimumWidth(150)
        toggle_color_button.setCheckable(True)
        toggle_color_button.setChecked(self.color_toggle)
        if self.color_toggle:
            toggle_color_button.setText("Toggle Color On")
        else:
            toggle_color_button.setText("Toggle Color Off")
        toggle_color_button.clicked.connect(self._debug_toggle_color_on_off)
        self.toggle_color_button = toggle_color_button

        button_layout.addWidget(save_button)
        button_layout.addWidget(restore_defaults_button)
        button_layout.addWidget(toggle_color_button)
        button_layout.addWidget(close_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        layout.addSpacing(16)

        # --- PATCH: Apply color mode at form open ---
        if not self.color_toggle:
            self.toggle_color_on_off(init=True)

    def _get_current_values(self):
        """Return a dict of all current field values, including toggle."""
        values = {}
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
            values[key] = entry.text() if entry else ""
        values["color_toggle"] = "yes" if getattr(self, "toggle_color_button", None) and self.toggle_color_button.isChecked() else "no"
        return values

    def _has_changes(self):
        """Return True if any field (including toggle) has changed since open."""
        return self._get_current_values() != self._initial_values

    def get_factory_defaults(self):
        """Return a dict of factory default color/font values."""
        return {
            "form_title_color": "#222222",
            "form_bg_color": "#e3f2fd",
            "form_fg_color": "#222222",
            "form_border_color": "#1976d2",
            "form_font_size": "12",
            "metadata_bg_color": "#e3f2fd",
            "metadata_fg_color": "#222222",
            "metadata_font_size": "12",
            "table_bg_color": "#ffffff",
            "button_bg_color": "#1976d2",
            "button_fg_color": "#ffffff",
            "button_border_color": "#1976d2",
            "button_font_size": "12",
            "table_header_bg_color": "#1976d2",
            "table_header_fg_color": "#ffffff",
            "table_header_font_size": "12",
            "table_fg_color": "#222222",
            "table_font_size": "12",
        }

    def get_toggle_on_values(self):
        """Return a dict of color/font values for toggle ON (all white/black, font 12)."""
        return {
            "form_title_color": "#000000",
            "form_bg_color": "#ffffff",
            "form_fg_color": "#000000",
            "form_border_color": "#000000",
            "form_font_size": "12",
            "metadata_bg_color": "#ffffff",
            "metadata_fg_color": "#000000",
            "metadata_font_size": "12",
            "table_bg_color": "#ffffff",
            "button_bg_color": "#ffffff",
            "button_fg_color": "#000000",
            "button_border_color": "#000000",
            "button_font_size": "12",
            "table_header_bg_color": "#ffffff",
            "table_header_fg_color": "#000000",
            "table_header_font_size": "12",
            "table_fg_color": "#000000",
            "table_font_size": "12",
        }

    def toggle_color_on_off(self, init=False):
        from logic.db_interface import set_all_defaults, get_all_defaults
        from PyQt5.QtWidgets import QApplication
        if self.toggle_color_button.isChecked():
            # Toggle ON: set all fields to white/black/font 12
            toggle_on = self.get_toggle_on_values()
            for key, value in toggle_on.items():
                attr = key.replace('_color', '_entry').replace('_size', '_entry').replace('_font', '_font_entry')
                entry = getattr(self, attr, None)
                if entry:
                    entry.setText(value)
            QApplication.processEvents()
            self.save_settings(close_dialog=False)
            self.toggle_color_button.setChecked(True)
            self.toggle_color_button.setText("Toggle Color On")
            self._apply_global_stylesheet(self._get_current_values())
            if not init:
                set_all_defaults({"color_toggle": "yes"})
        else:
            # Toggle OFF: restore factory defaults
            factory = self.get_factory_defaults()
            for key, value in factory.items():
                attr = key.replace('_color', '_entry').replace('_size', '_entry').replace('_font', '_font_entry')
                entry = getattr(self, attr, None)
                if entry:
                    entry.setText(value)
            QApplication.processEvents()
            self.save_settings(close_dialog=False)
            self.toggle_color_button.setChecked(False)
            self.toggle_color_button.setText("Toggle Color Off")
            self._apply_global_stylesheet(self._get_current_values())
            if not init:
                set_all_defaults({"color_toggle": "no"})

    def _apply_global_stylesheet(self, updated_settings=None):
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        if updated_settings is None:
            updated_settings = self._get_current_values()
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
        form_title_color = updated_settings.get("form_title_color", "#222222")
        form_border_color = updated_settings.get("form_border_color", "#1976d2")
        style = f"""
            QWidget {{ background-color: {form_bg_color}; }}
            QLabel, QLineEdit {{ font-size: {form_font_size}pt; }}
            QLabel#formTitle {{ color: {form_title_color}; }}
            QLineEdit, QComboBox {{ border: 1px solid {form_border_color}; }}
            QPushButton {{ background-color: {button_bg_color}; color: {button_fg_color}; font-size: {button_font_size}pt; }}
            QTableView, QTableWidget {{ background-color: {table_bg_color}; }}
            QHeaderView::section {{ background-color: {table_header_bg_color}; color: {table_header_fg_color}; font-size: {table_header_font_size}pt; }}
            QTableWidget::item {{ color: {table_fg_color}; font-size: {table_font_size}pt; }}
        """
        QApplication.instance().setStyleSheet(style)
        QApplication.instance().setStyle(QApplication.instance().style())

    def save_settings(self, close_dialog=True):
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
        # Always save the current toggle state
        updated_settings["color_toggle"] = "yes" if self.toggle_color_button.isChecked() else "no"
        try:
            from PyQt5.QtWidgets import QApplication, QLabel
            from PyQt5.QtGui import QFont
            from PyQt5.QtCore import QTimer
            set_all_defaults(updated_settings)
            # --- Instant update: reapply global stylesheet and font size ---
            QApplication.instance().setFont(QFont("Segoe UI", int(updated_settings.get("form_font_size") or 12)))
            self._apply_global_stylesheet(updated_settings)
            if close_dialog:
                self._show_flash_message("Stylesheet settings saved!", duration=1800)
                QTimer.singleShot(1800, self.accept)
            self._initial_values = self._get_current_values()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save stylesheet settings: {e}")
            return
        if close_dialog:
            return  # Do not call self.accept() here, handled by QTimer above

    def _show_flash_message(self, text, duration=1800):
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QLabel
        flash = QLabel(text, self)
        flash.setStyleSheet("background: #1976d2; color: white; font-weight: bold; border-radius: 8px; padding: 8px; font-size: 13pt;")
        flash.setAlignment(Qt.AlignCenter)
        flash.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        flash.adjustSize()
        # Center on screen (not just dialog)
        screen = self.screen().geometry() if hasattr(self, 'screen') and self.screen() else self.geometry()
        x = screen.x() + (screen.width() - flash.width()) // 2
        y = screen.y() + (screen.height() - flash.height()) // 2
        flash.move(x, y)
        flash.show()
        QTimer.singleShot(duration, flash.close)

    def restore_all_colors_fonts(self):
        factory = self.get_factory_defaults()
        for key, value in factory.items():
            attr = key.replace('_color', '_entry').replace('_size', '_entry').replace('_font', '_font_entry')
            entry = getattr(self, attr, None)
            if entry:
                entry.setText(value)
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        self.save_settings(close_dialog=False)
        self._apply_global_stylesheet()

    def close_with_prompt(self):
        if not self._has_changes():
            self.reject()
            return
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Save Changes?", "Save changes before closing?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_settings()
        else:
            self.reject()

    def closeEvent(self, event):
        # If user clicks [X], treat as cancel (no save)
        event.accept()

    def _debug_save_settings(self, *args, **kwargs):
        print("[DEBUG] Save button clicked. Current values:", self._get_current_values())
        self.save_settings(*args, **kwargs)

    def _debug_restore_all_colors_fonts(self, *args, **kwargs):
        print("[DEBUG] Restore All Colors/Fonts button clicked.")
        self.restore_all_colors_fonts()  # Call with no arguments
        print("[DEBUG] After restore, current values:", self._get_current_values())

    def _debug_toggle_color_on_off(self, *args, **kwargs):
        print(f"[DEBUG] Toggle Color button clicked. Checked: {self.toggle_color_button.isChecked()}")
        self.toggle_color_on_off()  # Call with no arguments
        print("[DEBUG] After toggle, current values:", self._get_current_values())

    def _debug_close_with_prompt(self, *args, **kwargs):
        print("[DEBUG] Close button clicked. Has changes:", self._has_changes())
        self.close_with_prompt()  # Call with no arguments
