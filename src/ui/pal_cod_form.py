from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt


class PALCODForm(QDialog):
    def __init__(self, parent, column_index, update_column_callback, current_value, date, student_name=None, show_cod_cia=True, show_student_name=False):
        super().__init__(parent)
        self.setWindowTitle("Update Attendance")
        self.setFixedSize(300, 300)

        self.column_index = column_index
        self.update_column_callback = update_column_callback
        self.current_value = current_value
        self.date = date
        self.student_name = student_name
        self.selected_value = None  # Initialize the selected_value attribute

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
            self.selected_value = value  # Set the selected value
            self.accept()  # Close the form

    def select_value(self, value):
        self.selected_value = value
        self.accept()
