from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox


class PALCODForm(QDialog):
    def __init__(self, parent, column_index, update_column_callback):
        super().__init__(parent)
        self.setWindowTitle("Update Attendance")
        self.setFixedSize(300, 300)

        self.column_index = column_index
        self.update_column_callback = update_column_callback

        # Layout
        layout = QVBoxLayout(self)

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