from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout
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
        self.row_to_student_id = []

        self.setWindowTitle("Student Manager")
        self.resize(700, 300)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for students
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Nickname", "Company No", "Note", "Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.populate_table()
        layout.addWidget(self.table)

        # Buttons (horizontal layout)
        button_layout = QHBoxLayout()

        toggle_active_button = QPushButton("Toggle Active Status")
        toggle_active_button.clicked.connect(self.toggle_active_status)
        button_layout.addWidget(toggle_active_button)

        delete_button = QPushButton("Delete Student")
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(delete_button)

        edit_button = QPushButton("Edit Student")
        edit_button.clicked.connect(self.edit_student)
        button_layout.addWidget(edit_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_manager)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        self.table.setRowCount(0)
        self.row_to_student_id = []
        for student_id, student_data in self.students.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.row_to_student_id.append(student_id)
            # Name
            item_name = QTableWidgetItem(student_data.get("name", "Unknown"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 0, item_name)
            # Nickname
            item_nick = QTableWidgetItem(student_data.get("nickname", ""))
            item_nick.setFlags(item_nick.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 1, item_nick)
            # Company No
            item_company = QTableWidgetItem(student_data.get("company_no", ""))
            item_company.setFlags(item_company.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 2, item_company)
            # Note
            item_note = QTableWidgetItem(student_data.get("note", ""))
            item_note.setFlags(item_note.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 3, item_note)
            # Active
            item_active = QTableWidgetItem(student_data.get("active", "No"))
            item_active.setFlags(item_active.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 4, item_active)

    def toggle_active_status(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a student to toggle status.")
            return
        for idx in selected_rows:
            row = idx.row()
            student_id = self.row_to_student_id[row]
            current_status = self.students[student_id].get("active", "No")
            self.students[student_id]["active"] = "No" if current_status == "Yes" else "Yes"
        save_data(self.data)
        self.populate_table()
        self.refresh_callback()

    def delete_student(self):
        """Delete the selected student(s) if they are inactive."""
        selected_rows = set(idx.row() for idx in self.table.selectionModel().selectedRows())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more students to delete.")
            return

        # Gather student IDs to delete, but only if Active == "No"
        deletable_ids = []
        undeletable_names = []
        for row in selected_rows:
            student_id = self.row_to_student_id[row]
            student = self.students[student_id]
            if student.get("active", "No") == "No":
                deletable_ids.append(student_id)
            else:
                undeletable_names.append(student.get("name", student_id))

        if not deletable_ids:
            QMessageBox.warning(self, "Cannot Delete", "Only students with Active = No can be deleted.\nToggle Student Active Status = No then delete.")
            return

        # Confirm deletion
        confirm = QMessageBox.warning(
            self,
            "Delete Student(s)",
            f"Deleting these students will remove all data and is unrecoverable.\nAre you sure you want to delete {len(deletable_ids)} student(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            for student_id in deletable_ids:
                if student_id in self.students:
                    del self.students[student_id]
            save_data(self.data)  # Save the updated data
            self.populate_table()  # Refresh the table
            self.refresh_callback()  # Refresh the main form

            if undeletable_names:
                QMessageBox.information(
                    self,
                    "Some Students Not Deleted",
                    "The following students were not deleted because they are still active:\n" +
                    "\n".join(undeletable_names)
                )

    def edit_student(self):
        """Edit the selected student using StudentForm."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) != 1:
            QMessageBox.warning(self, "Select Student", "Please select a single student to edit.")
            return
        row = selected_rows[0].row()
        student_id = self.row_to_student_id[row]
        student_data = self.students[student_id]
        form = StudentForm(self, self.class_id, self.data, self.refresh_callback, student_id=student_id, student_data=student_data)
        form.exec_()
        self.populate_table()

    def close_manager(self):
        """Close the StudentManager."""
        self.refresh_callback()
        self.accept()

    def closeEvent(self, event):
        """Restore the initial size when the StudentManager is reopened."""
        self.resize(500, 300)
        super().closeEvent(event)
