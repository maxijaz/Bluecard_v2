from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.parser import save_data


class ArchiveManager(QDialog):
    def __init__(self, parent, data, class_id, refresh_callback=None):
        super().__init__(parent)
        self.data = data
        self.class_id = class_id
        self.students = self.data["classes"][self.class_id].get("students", {})
        self.refresh_callback = refresh_callback  # Store the callback

        self.setWindowTitle("Archived Students")
        self.setFixedSize(600, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for archived students
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Student ID", "Name", "Archived"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # Populate the table
        self.populate_table()

        # Buttons
        button_layout = QHBoxLayout()
        restore_button = QPushButton("Restore")
        restore_button.clicked.connect(self.restore_student)
        button_layout.addWidget(restore_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(delete_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close_with_refresh)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with archived student data."""
        self.table.setRowCount(0)  # Clear existing rows
        for student_id, student_data in self.students.items():
            if student_data.get("active", "Yes") == "No":  # Filter archived students
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(student_id))
                self.table.setItem(row_position, 1, QTableWidgetItem(student_data.get("name", "Unknown")))
                self.table.setItem(row_position, 2, QTableWidgetItem(student_data.get("active", "No")))

    def restore_student(self):
        """Restore the selected archived student."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a student to restore.")
            return

        student_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.question(
            self, "Restore Student", f"Are you sure you want to restore student {student_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.students[student_id]["active"] = "Yes"  # Restore the student
            save_data(self.data)  # Save changes to file
            self.populate_table()  # Refresh the table

    def delete_student(self):
        """Delete the selected archived student."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a student to delete.")
            return

        student_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.warning(
            self, "Delete Student",
            f"Are you sure you want to delete student {student_id}? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.students[student_id]  # Delete the student
            save_data(self.data)  # Save changes to file
            self.populate_table()  # Refresh the table

    def close_with_refresh(self):
        """Close the dialog and trigger the refresh callback."""
        if self.refresh_callback:
            self.refresh_callback()  # Trigger the callback
        self.accept()  # Close the dialog