from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QGridLayout, QLineEdit, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from logic.db_interface import update_class, get_class_by_id, get_form_settings, get_all_defaults, get_message_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

SHOW_HIDE_FIELDS = [
    ("show_nickname", "Nickname"),
    ("show_company_no", "Company No"),
    ("show_score", "Score"),
    ("show_pre_test", "Pre-test"),
    ("show_post_test", "Post-test"),
    ("show_attn", "Attn"),
    ("show_p", "P"),
    ("show_a", "A"),
    ("show_l", "L"),
    ("show_note", "Note"),
    ("show_dates", "Dates"),  # <-- Add Dates (scrollable table)
]

# Map from label to DB width key
WIDTH_DB_KEYS = {
    "Nickname": "width_nickname",
    "Company No": "width_company_no",
    "Score": "width_score",
    "Pre-test": "width_pre_test",  # <-- FIXED
    "Post-test": "width_post_test",  # <-- FIXED
    "Attn": "width_attn",
    "P": "width_p",
    "A": "width_a",
    "L": "width_l",
    "Note": "width_note",
    "Dates": "width_date",  # <-- Add width_date for Dates
}

COLOR_FIELDS = [
    ("bgcolor_p", "P", "#c8e6c9"),
    ("bgcolor_a", "A", "#ffcdd2"),
    ("bgcolor_l", "L", "#fff9c4"),
    ("bgcolor_cod", "CIA", "#c8e6c9"),
    ("bgcolor_cia", "CIA", "#ffcdd2"),
    ("bgcolor_hol", "HOL", "#ffcdd2"),
]

def show_message_dialog(parent, message, timeout=2000, buttons=None):
    """
    Show a floating message dialog. If buttons is provided, it should be a list of (label, callback) tuples.
    If buttons is None, show an auto-closing info dialog.
    """
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
    from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
    from PyQt5.QtCore import Qt
    msg_dialog = QDialog(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
    msg_dialog.setModal(True if buttons else False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(message)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    if buttons:
        btn_row = QHBoxLayout()
        for btn_text, btn_callback in buttons:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(f"background: {bg}; color: {fg}; border-radius: {border_radius}px; font-size: {font_size}pt; font-weight: {font_weight}; padding: 6px 18px;")
            btn.clicked.connect(lambda _, cb=btn_callback: (msg_dialog.accept(), cb() if cb else None))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)
    msg_dialog.adjustSize()
    parent_geo = parent.geometry() if parent else None
    if parent_geo:
        msg_dialog.move(parent.mapToGlobal(parent_geo.center()) - msg_dialog.rect().center())
    msg_dialog.show()
    if not buttons:
        QTimer.singleShot(timeout, msg_dialog.accept)
    else:
        msg_dialog.exec_()

class ShowHideForm(QDialog):
    def __init__(self, parent, class_id, on_save_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Show/Hide Columns and Colors")
        self.class_id = class_id
        self.on_save_callback = on_save_callback
        self.class_data = get_class_by_id(class_id)  # <-- Load from classes table
        self.checkboxes = {}
        self.color_edits = {}
        self.width_edits = {}  # {db_key: QLineEdit}

        # --- PATCH: Make non-modal and always on top, but allow header dragging in mainform ---
        from PyQt5.QtCore import Qt
        self.setModal(False)
        # Only use WindowStaysOnTopHint (remove Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # --- END PATCH ---

        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("ShowHideForm") or {}
        defaults = get_all_defaults()
        # Font
        font_family = form_settings.get("font_family", defaults.get("form_font_family", "Segoe UI"))
        font_size = int(form_settings.get("font_size") or defaults.get("form_font_size", 12))
        from PyQt5.QtGui import QFont
        self.form_font = QFont(font_family, font_size)
        # Window sizing
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        resizable = str(form_settings.get("resizable", "yes")).lower() in ("yes", "true", "1")
        window_controls = form_settings.get("window_controls", "standard")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.setFixedSize(850, 500)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        if resizable:
            self.setSizeGripEnabled(True)
        else:
            self.setSizeGripEnabled(False)
        if window_controls == "standard":
            self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        # Display preferences
        if not win_w or not win_h:
            scale = str(defaults.get("scale_windows", "1")) == "1"
            center = str(defaults.get("center_windows", "1")) == "1"
            width_ratio = float(defaults.get("window_width_ratio", 0.6))
            height_ratio = float(defaults.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        # --- PATCH END ---

        layout = QVBoxLayout(self)

        # Header row
        header_layout = QHBoxLayout()
        header_label_style = f"color: {defaults.get('title_color', '#1976d2')}; font-size: {defaults.get('title_font_size', 14)}pt; font-weight: {'bold' if str(defaults.get('title_font_bold', True)).lower() in ('1','true','yes') else 'normal'};"
        for text in ("<b>Columns: Show/Width</b>", "<b>P/A/L colors</b>"):
            lbl = QLabel(text)
            lbl.setStyleSheet(header_label_style)
            header_layout.addWidget(lbl)
        layout.addLayout(header_layout)

        # Main grid
        grid = QGridLayout()
        max_rows = max(len(SHOW_HIDE_FIELDS), len(COLOR_FIELDS))
        label_style = f"color: {defaults.get('form_fg_color', '#222222')}; font-size: {font_size}pt; font-weight: {'bold' if str(defaults.get('form_label_bold', True)).lower() in ('1','true','yes') else 'normal'};"
        for row in range(max_rows):
            # Column 1: Show/Hide tickboxes
            if row < len(SHOW_HIDE_FIELDS):
                key, label = SHOW_HIDE_FIELDS[row]
                lbl = QLabel(label)
                lbl.setStyleSheet(label_style)
                cb = QCheckBox()
                cb.setChecked(self.class_data.get(key, "Yes") == "Yes")
                cb.setFont(self.form_font)
                self.checkboxes[key] = cb
                grid.addWidget(lbl, row, 0)
                grid.addWidget(cb, row, 1)
                # Column 2: Width QLineEdit (aligned with label/tickbox)
                width_db_key = WIDTH_DB_KEYS.get(label)
                if width_db_key:
                    width_val = self.class_data.get(width_db_key, "")
                    width_edit = QLineEdit(str(width_val) if width_val else "")
                    width_edit.setMaximumWidth(60)
                    width_edit.setFont(self.form_font)
                    self.width_edits[width_db_key] = width_edit
                    grid.addWidget(width_edit, row, 2)
                else:
                    grid.addWidget(QWidget(), row, 2)
            else:
                grid.addWidget(QWidget(), row, 0)
                grid.addWidget(QWidget(), row, 1)
                grid.addWidget(QWidget(), row, 2)
            # Column 3: Color label + QLineEdit
            if row < len(COLOR_FIELDS):
                color_key, color_label, default = COLOR_FIELDS[row]
                lbl = QLabel(color_label)
                lbl.setStyleSheet(label_style)
                edit = QLineEdit(self.class_data.get(color_key, default))
                edit.setFont(self.form_font)
                self.color_edits[color_key] = edit
                grid.addWidget(lbl, row, 3)
                grid.addWidget(edit, row, 4)
            else:
                grid.addWidget(QWidget(), row, 3)
                grid.addWidget(QWidget(), row, 4)
        layout.addLayout(grid)

        # Toggle buttons
        button_bg = form_settings.get("button_bg_color", defaults.get("button_bg_color", "#1976d2"))
        button_fg = form_settings.get("button_fg_color", defaults.get("button_fg_color", "#ffffff"))
        button_font_size = int(form_settings.get("button_font_size", defaults.get("button_font_size", 12)))
        button_font_bold = str(form_settings.get("button_font_bold", defaults.get("button_font_bold", "no"))).lower() in ("yes", "true", "1")
        button_hover_bg = form_settings.get("button_hover_bg_color", defaults.get("button_hover_bg_color", "#1565c0"))
        button_active_bg = form_settings.get("button_active_bg_color", defaults.get("button_active_bg_color", "#0d47a1"))
        button_border = form_settings.get("button_border_color", defaults.get("button_border_color", "#1976d2"))
        button_style = (
            f"QPushButton {{background: {button_bg}; color: {button_fg}; border: 2px solid {button_border}; font-size: {button_font_size}pt; font-weight: {'bold' if button_font_bold else 'normal'};}}"
            f"QPushButton:hover {{background: {button_hover_bg};}}"
            f"QPushButton:pressed {{background: {button_active_bg};}}"
        )
        toggle_layout = QHBoxLayout()
        self.toggle_columns_btn = QPushButton("Toggle show/hide columns")
        self.toggle_columns_btn.setFont(self.form_font)
        self.toggle_columns_btn.setStyleSheet(button_style)
        self.toggle_columns_btn.clicked.connect(self.toggle_columns)
        self.toggle_colors_btn = QPushButton("Toggle bgcolor on/off")
        self.toggle_colors_btn.setFont(self.form_font)
        self.toggle_colors_btn.setStyleSheet(button_style)
        self.toggle_colors_btn.clicked.connect(self.toggle_colors)
        self.reset_widths_btn = QPushButton("Reset Widths")
        self.reset_widths_btn.setFont(self.form_font)
        self.reset_widths_btn.setStyleSheet(button_style)
        self.reset_widths_btn.clicked.connect(self.reset_widths)
        toggle_layout.addWidget(self.toggle_columns_btn)
        toggle_layout.addWidget(self.toggle_colors_btn)
        toggle_layout.addWidget(self.reset_widths_btn)
        layout.addLayout(toggle_layout)

        # Save/Cancel
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setFont(self.form_font)
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(self.form_font)
        cancel_btn.setStyleSheet(button_style)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # --- LIVE WIDTH TRACKING: Connect QLineEdit edits to DB update ---
        for db_key, width_edit in self.width_edits.items():
            width_edit.textChanged.connect(lambda val, db_key=db_key: self._update_width_live(db_key, val))

    def reset_widths(self):
        # Show confirmation dialog before resetting widths
        from PyQt5.QtWidgets import QMessageBox
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Reset Column Widths")
        confirm.setText("This will reset all the column widths to their default values. Are you sure?")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        confirm.setDefaultButton(QMessageBox.Cancel)
        ret = confirm.exec_()
        if ret != QMessageBox.Yes:
            return  # User cancelled
        # Reload widths from factory_defaults (not just DB) and update QLineEdits
        from logic.db_interface import get_factory_defaults
        factory_defaults = get_factory_defaults()
        class_defaults = factory_defaults.get("classes", {}).get("default", {}) if factory_defaults else {}
        for label, db_key in WIDTH_DB_KEYS.items():
            if db_key in self.width_edits:
                default_val = class_defaults.get(db_key, "")
                if default_val is not None and str(default_val).strip() != "":
                    self.width_edits[db_key].setText(str(default_val))
                    self.class_data[db_key] = default_val
                else:
                    self.width_edits[db_key].setText("")
                    self.class_data[db_key] = None
        # --- LIVE UPDATE: Notify mainform to update widths immediately ---
        if self.on_save_callback:
            self.on_save_callback(live_update=True)

    def toggle_columns(self):
        # Toggle all checkboxes: if any unchecked, check all; else uncheck all
        check = not all(cb.isChecked() for cb in self.checkboxes.values())
        for cb in self.checkboxes.values():
            cb.setChecked(check)

    def toggle_colors(self):
        # If any color is not empty, clear all; else set to default
        any_colored = any(edit.text().strip() for edit in self.color_edits.values())
        for color_key, edit in self.color_edits.items():
            default = next((d for k, l, d in COLOR_FIELDS if k == color_key), "")
            edit.setText("" if any_colored else default)

    def save(self):
        updates = {key: "Yes" if cb.isChecked() else "No" for key, cb in self.checkboxes.items()}
        for color_key, edit in self.color_edits.items():
            updates[color_key] = edit.text().strip()
        # Save widths
        for db_key, edit in self.width_edits.items():
            val = edit.text().strip()
            if val.isdigit():
                updates[db_key] = int(val)
            else:
                updates[db_key] = None
        try:
            update_class(self.class_id, updates)
            if self.on_save_callback:
                self.on_save_callback(live_update=True)
            self.accept()
        except Exception as e:
            show_message_dialog(self, f"Failed to save: {e}")

    def get_selected_columns(self):
        # Returns a dict mapping DB key (e.g. 'show_nickname') to True/False for checked/unchecked
        result = {}
        for key, cb in self.checkboxes.items():
            result[key] = cb.isChecked()
        return result

    def _update_width_live(self, db_key, val):
        # Save the width to DB as soon as the QLineEdit changes
        try:
            from logic.db_interface import update_class
            if val.isdigit():
                update_class(self.class_id, {db_key: int(val)})
                self.class_data[db_key] = int(val)
            else:
                update_class(self.class_id, {db_key: None})
                self.class_data[db_key] = None
            if self.on_save_callback:
                self.on_save_callback(live_update=True)
        except Exception as e:
            print(f"[ERROR] Failed to update width {db_key} live: {e}")