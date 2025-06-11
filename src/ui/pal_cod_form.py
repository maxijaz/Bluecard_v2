from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from logic.db_interface import get_form_settings, get_all_defaults, get_message_defaults
from PyQt5.QtGui import QFont


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
    msg_dialog = QDialog(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
    msg_dialog.setModal(True if buttons else False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(message)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    if buttons:
        btn_row = QVBoxLayout() if len(buttons) < 3 else QHBoxLayout()
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


class PALCODForm(QDialog):
    def __init__(self, parent, column_index, update_column_callback, current_value, date, student_name=None, show_cod_cia=True, show_student_name=False, refresh_cell_callback=None, row=None):
        super().__init__(parent)
        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("PALCODForm") or {}
        defaults = get_all_defaults()
        self.form_font_size = int(form_settings.get("font_size") or defaults.get("form_font_size", 12))
        font_family = form_settings.get("font_family", defaults.get("form_font_family", "Segoe UI"))
        self.form_font = QFont(font_family, self.form_font_size)
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        resizable = str(form_settings.get("resizable", "yes")).lower() in ("yes", "true", "1")
        window_controls = form_settings.get("window_controls", "standard")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.setFixedSize(300, 300)
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
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            from logic.display import center_widget, scale_and_center, apply_window_flags
            scale = str(defaults.get("scale_windows", "1")) == "1"
            center = str(defaults.get("center_windows", "1")) == "1"
            width_ratio = float(defaults.get("window_width_ratio", 0.6))
            height_ratio = float(defaults.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        # --- PATCH END ---

        self._blocked = False
        # --- Prevent single-cell edit if column contains CIA/COD/HOL ---
        if row is not None:
            mainform = parent
            try:
                model = mainform.scrollable_table.model()
                col = column_index
                for r in range(1, model.rowCount()):
                    idx = model.index(r, col)
                    val = model.data(idx, role=Qt.DisplayRole)
                    if val in ("CIA", "COD", "HOL"):
                        show_message_dialog(
                            mainform,
                            "You cannot change a single attendance value in this column because it contains CIA, COD, or HOL.\n\nPlease click the column header and clear the special value for all students before retrying to edit a single cell."
                        )
                        self._blocked = True
                        self.close()
                        return
            except Exception as e:
                print(f"[DEBUG] PALCODForm: Exception during CIA/COD/HOL check: {e}")

        self.setWindowTitle("Update Attendance")

        self.column_index = column_index
        self.update_column_callback = update_column_callback
        self.current_value = current_value
        self.date = date
        self.student_name = student_name
        self.selected_value = None  # Initialize the selected_value attribute
        self.refresh_cell_callback = refresh_cell_callback
        self.row = row

        # Layout
        layout = QVBoxLayout(self)

        # Display the date
        date_label = QLabel(f"Date: {self.date}")
        date_label.setFont(self.form_font)
        date_label.setStyleSheet(f"font-weight: bold; font-size: {self.form_font_size+2}px; margin-bottom: 10px; color: {defaults.get('title_color', '#1976d2')};")
        layout.addWidget(date_label)

        # Optionally display the student name
        if show_student_name and self.student_name:
            student_label = QLabel(f"Student: {self.student_name}")
            student_label.setFont(self.form_font)
            student_label.setStyleSheet(f"font-weight: bold; font-size: {self.form_font_size+1}px; margin-bottom: 5px; color: {defaults.get('form_fg_color', '#222222')};")
            layout.addWidget(student_label)

        # --- PATCH: Button style from DB ---
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

        # Buttons
        buttons = {
            "P = Present": "P",
            "A = Absent": "A",
            "L = Late": "L",
            "Clear": "-",
        }

        if show_cod_cia:  # Include COD, CIA, HOL options only if show_cod_cia is True
            buttons.update({
                "COD = Cancel": "COD",
                "CIA = Postpone": "CIA",
                "HOL = Holiday": "HOL",
            })

        for label, value in buttons.items():
            button = QPushButton(label)
            button.setFont(self.form_font)
            button.setStyleSheet(button_style if value != self.current_value else button_style + "background: lightblue; font-weight: bold;")
            button.clicked.connect(lambda _, v=value: self.update_column(v))
            layout.addWidget(button)

    def update_column(self, value):
        def on_confirm():
            self.selected_value = value
            if self.update_column_callback:
                print(f"[DEBUG] PALCODForm: Calling update_column_callback({self.column_index}, {value})")
                self.update_column_callback(self.column_index, value)
            self.accept()
            # Refresh the cell if callback is provided
            if self.refresh_cell_callback and self.row is not None:
                self.refresh_cell_callback(self.row, self.column_index)
        def on_cancel():
            pass
        show_message_dialog(
            self,
            f"Are you sure you want to set this field to '{value}'?",
            buttons=[("Yes", on_confirm), ("No", on_cancel)]
        )

    def select_value(self, value):
        self.selected_value = value
        if self.update_column_callback:
            print(f"[DEBUG] PALCODForm: Calling update_column_callback({self.column_index}, {value})")
            self.update_column_callback(self.column_index, value)
        self.accept()
        # Refresh the cell if callback is provided
        if self.refresh_cell_callback and self.row is not None:
            self.refresh_cell_callback(self.row, self.column_index)


def open_pal_cod_form(self, column_index=None):
    """Open the PALCODForm to update attendance."""
    attendance_dates = self.metadata.get("dates", [])

    # If called from header double-click, column_index is provided
    if column_index is not None:
        if column_index < 0 or column_index >= len(attendance_dates):
            show_message_dialog(
                self,
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return
    else:
        # Called from button/menu, get selected column
        selected_columns = self.scrollable_table.selectionModel().selectedColumns()
        if not selected_columns:
            show_message_dialog(
                self,
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return
        column_index = selected_columns[0].column()
        if column_index < 0 or column_index >= len(attendance_dates):
            show_message_dialog(
                self,
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return

    date = attendance_dates[column_index]

    # --- Block if the header is not a real date (e.g., "Date1", "date2", "Empty-1") ---
    if not (len(date) == 10 and date[2] == "/" and date[5] == "/" and date.replace("/", "").isdigit()):
        show_message_dialog(
            self,
            "Cannot set P/A/L for this column. Please add real dates first before attempting to change attendance."
        )
        return

    pal_cod_form = PALCODForm(self, column_index, self.update_column_values, None, date, show_cod_cia=False, show_student_name=True)
    if hasattr(pal_cod_form, '_blocked') and pal_cod_form._blocked:
        print("[DEBUG] PALCODForm: Dialog was blocked, not calling exec_()")
        return
    if pal_cod_form.exec_() == QDialog.Accepted:
        new_value = pal_cod_form.selected_value
        self.update_column_values(column_index, new_value)
