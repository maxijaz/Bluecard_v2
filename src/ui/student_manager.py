from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from src.logic.parser import save_data, generate_next_student_id
from src.ui.student_form import StudentForm

def validate_student_data(student_data: dict) -> bool:
    """Validate the student data before adding."""
    required_fields = ["name", "gender", "active"]
    for field in required_fields:
        if field not in student_data or not student_data[field]:
            QMessageBox.warning(None, "Invalid Data", f"Field '{field}' is required.")
            return False

    # Ensure the attendance field is initialized if missing
    if "attendance" not in student_data:
        student_data["attendance"] = {}

    return True

class StudentManager(QDialog):
    def __init__(self, parent, data, class_id, refresh_callback):
        super().__init__(parent)
        self.data = data
        self.class_id = class_id
        self.refresh_callback = refresh_callback
        self.students = self.data["classes"][self.class_id]["students"]

        self.setWindowTitle("Student Manager")
        self.resize(400, 300)  # Set the initial size
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for students
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # Add a third column for "Active"
        self.table.setHorizontalHeaderLabels(["Student ID", "Name", "Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.populate_table()
        layout.addWidget(self.table)

        # Buttons
        button_layout = QVBoxLayout()
        toggle_active_button = QPushButton("Toggle Active Status")
        toggle_active_button.clicked.connect(self.toggle_active_status)
        button_layout.addWidget(toggle_active_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_manager)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with student data."""
        self.table.setRowCount(0)
        for student_id, student_data in self.students.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(student_id))
            self.table.setItem(row_position, 1, QTableWidgetItem(student_data.get("name", "Unknown")))
            self.table.setItem(row_position, 2, QTableWidgetItem(student_data.get("active", "No")))  # Add "Active" field

    def toggle_active_status(self):
        """Toggle the active status of the selected student."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a student to toggle their active status.")
            return

        student_id = self.table.item(selected_row, 0).text()
        current_status = self.students[student_id].get("active", "No")
        new_status = "Yes" if current_status == "No" else "No"

        # Confirm the action
        confirm = QMessageBox.question(
            self,
            "Toggle Active Status",
            f"Are you sure you want to change the active status of student {student_id} to '{new_status}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.students[student_id]["active"] = new_status
            save_data(self.data)  # Save the updated data
            self.populate_table()  # Refresh the table
            self.refresh_callback()  # Refresh the main form

    def close_manager(self):
        """Close the StudentManager."""
        self.refresh_callback()
        self.accept()

    def closeEvent(self, event):
        """Restore the initial size when the StudentManager is reopened."""
        self.resize(400, 300)
        super().closeEvent(event)
