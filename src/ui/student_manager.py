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
        self.resize(500, 300)  # Adjusted size to accommodate the new column
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for students
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Add a fourth column for "Nickname"
        self.table.setHorizontalHeaderLabels(["Student ID", "Name", "Nickname", "Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # Highlight the whole row on click
        self.populate_table()
        layout.addWidget(self.table)

        # Buttons
        button_layout = QVBoxLayout()

        toggle_active_button = QPushButton("Toggle Active Status")
        toggle_active_button.clicked.connect(self.toggle_active_status)
        button_layout.addWidget(toggle_active_button)

        delete_button = QPushButton("Delete Student")
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(delete_button)

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
            self.table.setItem(row_position, 2, QTableWidgetItem(student_data.get("nickname", "")))  # Add "Nickname" field
            self.table.setItem(row_position, 3, QTableWidgetItem(student_data.get("active", "No")))  # Add "Active" field

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

    def delete_student(self):
        """Delete the selected student(s)."""
        selected_rows = set(idx.row() for idx in self.table.selectionModel().selectedRows())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more students to delete.")
            return

        # Gather student IDs to delete
        student_ids = [self.table.item(row, 0).text() for row in selected_rows]

        # Confirm deletion
        confirm = QMessageBox.warning(
            self,
            "Delete Student(s)",
            f"Deleting these students will remove all data and is unrecoverable.\nAre you sure you want to delete {len(student_ids)} student(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            for student_id in student_ids:
                if student_id in self.students:
                    del self.students[student_id]
            save_data(self.data)  # Save the updated data
            self.populate_table()  # Refresh the table
            self.refresh_callback()  # Refresh the main form

    def close_manager(self):
        """Close the StudentManager."""
        self.refresh_callback()
        self.accept()

    def closeEvent(self, event):
        """Restore the initial size when the StudentManager is reopened."""
        self.resize(500, 300)
        super().closeEvent(event)
