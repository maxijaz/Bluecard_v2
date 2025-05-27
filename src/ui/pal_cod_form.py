from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt


class PALCODForm(QDialog):
    def __init__(self, parent, column_index, update_column_callback, current_value, date, student_name=None, show_cod_cia=True, show_student_name=False, refresh_cell_callback=None, row=None):
        super().__init__(parent)
        self.setWindowTitle("Update Attendance")
        self.setFixedSize(300, 300)

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
        date_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(date_label)

        # Optionally display the student name
        if show_student_name and self.student_name:
            student_label = QLabel(f"Student: {self.student_name}")
            student_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
            layout.addWidget(student_label)

        # Buttons
        buttons = {
            "P = Present": "P",
            "A = Absent": "A",
            "L = Late": "L",
            "Clear": "-",
        }

        if show_cod_cia:  # Include COD and CIA options only if show_cod_cia is True
            buttons.update({
                "COD = Cancel": "COD",
                "CIA = Postpone": "CIA",
            })

        for label, value in buttons.items():
            button = QPushButton(label)
            if value == self.current_value:  # Highlight the current value
                button.setStyleSheet("background-color: lightblue; font-weight: bold;")
            button.clicked.connect(lambda _, v=value: self.update_column(v))
            layout.addWidget(button)

        if show_cod_cia:
            cod_button = QPushButton("COD")
            cod_button.clicked.connect(lambda: self.select_value("COD"))
            layout.addWidget(cod_button)

            cia_button = QPushButton("CIA")
            cia_button.clicked.connect(lambda: self.select_value("CIA"))
            layout.addWidget(cia_button)

            hol_button = QPushButton("HOL")  # <-- Add this
            hol_button.clicked.connect(lambda: self.select_value("HOL"))
            layout.addWidget(hol_button)

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

    # Open the PALCODForm with COD and CIA options, without student name
    pal_cod_form = PALCODForm(self, column_index, self.update_column_values, None, date, show_cod_cia=False, show_student_name=True)
    if pal_cod_form.exec_() == QDialog.Accepted:
        new_value = pal_cod_form.selected_value
        self.update_column_values(column_index, new_value)
