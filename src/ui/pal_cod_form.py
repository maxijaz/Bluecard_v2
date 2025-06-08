from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from logic.db_interface import get_form_settings, get_all_defaults
from PyQt5.QtGui import QFont


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
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.setFixedSize(300, 300)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        # Remove max_width/max_height logic
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
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
                    print(f"[DEBUG] PALCODForm: row={r}, col={col}, val={val}")
                    if val in ("CIA", "COD", "HOL"):
                        print(f"[DEBUG] PALCODForm: Blocking edit, found special value '{val}' in column {col}")
                        QMessageBox.information(
                            mainform,
                            "Cannot Edit Cell",
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
        """Update the selected column with the given value."""
        confirm = QMessageBox.question(
            self,
            "Confirm Update",
            f"Are you sure you want to set this field to '{value}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.selected_value = value
            self.accept()
            # Refresh the cell if callback is provided
            if self.refresh_cell_callback and self.row is not None:
                self.refresh_cell_callback(self.row, self.column_index)

    def select_value(self, value):
        self.selected_value = value
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
            QMessageBox.warning(
                self,
                "Invalid Column",
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return
    else:
        # Called from button/menu, get selected column
        selected_columns = self.scrollable_table.selectionModel().selectedColumns()
        if not selected_columns:
            QMessageBox.warning(
                self,
                "No Column Selected",
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return
        column_index = selected_columns[0].column()
        if column_index < 0 or column_index >= len(attendance_dates):
            QMessageBox.warning(
                self,
                "Invalid Column",
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return

    date = attendance_dates[column_index]

    # --- Block if the header is not a real date (e.g., "Date1", "date2", "Empty-1") ---
    if not (len(date) == 10 and date[2] == "/" and date[5] == "/" and date.replace("/", "").isdigit()):
        QMessageBox.warning(
            self,
            "Invalid Date",
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
