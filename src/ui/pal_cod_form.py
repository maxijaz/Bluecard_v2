from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt


class PALCODForm(QDialog):
    def __init__(self, parent, column_index, update_column_callback, current_value, date):
        super().__init__(parent)
        self.setWindowTitle("Update Attendance")
        self.setFixedSize(300, 300)

        self.column_index = column_index
        self.update_column_callback = update_column_callback
        self.current_value = current_value
        self.date = date

        # Layout
        layout = QVBoxLayout(self)

        # Display the selected date
        date_label = QLabel(f"Selected Date: {self.date}")
        date_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(date_label)

        # Buttons
        buttons = {
            "P = Present": "P",
            "A = Absent": "A",
            "L = Late": "L",
            "COD = Cancel": "COD",
            "CIA = Postpone": "CIA",
            "Clear": "-",
        }

        for label, value in buttons.items():
            button = QPushButton(label)
            if value == self.current_value:  # Highlight the current value
                button.setStyleSheet("background-color: lightblue; font-weight: bold;")
            button.clicked.connect(lambda _, v=value: self.update_column(v))
            layout.addWidget(button)

    def update_column(self, value):
        """Update the selected column with the given value."""
        confirm = QMessageBox.question(
            self,
            "Confirm Update",
            f"Are you sure you want to set all values in this column to '{value}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.update_column_callback(self.column_index, value)
            self.accept()  # Close the form
