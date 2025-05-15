from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QApplication
)
from PyQt5.QtCore import Qt
from logic.parser import save_data


class StudentForm(QDialog):
    def __init__(self, parent, class_id, data, refresh_callback, student_id=None, student_data=None):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.refresh_callback = refresh_callback
        self.student_id = student_id
        self.student_data = student_data

        self.setWindowTitle("Edit Student" if student_id else "Add Student")
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_entry = QLineEdit()
        self.name_entry.setText(student_data.get("name", "") if student_data else "")
        layout.addWidget(self.name_entry)

        # Nickname
        layout.addWidget(QLabel("Nickname:"))
        self.nickname_entry = QLineEdit()
        self.nickname_entry.setText(student_data.get("nickname", "") if student_data else "")
        layout.addWidget(self.nickname_entry)

        # Gender
        layout.addWidget(QLabel("Gender:"))
        gender_layout = QHBoxLayout()
        self.male_radio = QRadioButton("Male")
        self.female_radio = QRadioButton("Female")
        if student_data:
            if student_data.get("gender", "Female") == "Male":
                self.male_radio.setChecked(True)
            else:
                self.female_radio.setChecked(True)
        else:
            self.female_radio.setChecked(True)  # Default to Female
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        layout.addLayout(gender_layout)

        # Score
        layout.addWidget(QLabel("Score:"))
        self.score_entry = QLineEdit()
        self.score_entry.setText(student_data.get("score", "") if student_data else "")
        layout.addWidget(self.score_entry)

        # Pre-Test
        layout.addWidget(QLabel("Pre-Test:"))
        self.pre_test_entry = QLineEdit()
        self.pre_test_entry.setText(student_data.get("pre_test", "") if student_data else "")
        layout.addWidget(self.pre_test_entry)

        # Post-Test
        layout.addWidget(QLabel("Post-Test:"))
        self.post_test_entry = QLineEdit()
        self.post_test_entry.setText(student_data.get("post_test", "") if student_data else "")
        layout.addWidget(self.post_test_entry)

        # Note
        layout.addWidget(QLabel("Note:"))
        self.note_entry = QLineEdit()
        self.note_entry.setText(student_data.get("note", "") if student_data else "")
        layout.addWidget(self.note_entry)

        # Active
        layout.addWidget(QLabel("Active:"))
        active_layout = QHBoxLayout()
        self.active_yes = QRadioButton("Yes")
        self.active_no = QRadioButton("No")
        if student_data:
            if student_data.get("active", "Yes") == "Yes":
                self.active_yes.setChecked(True)
            else:
                self.active_no.setChecked(True)
        else:
            self.active_yes.setChecked(True)  # Default to Yes
        active_layout.addWidget(self.active_yes)
        active_layout.addWidget(self.active_no)
        layout.addLayout(active_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_student)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        bulk_import_button = QPushButton("Bulk Import")
        bulk_import_button.clicked.connect(self.open_bulk_import_dialog)
        button_layout.addWidget(bulk_import_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_student(self):
        """Save the student data."""
        name = self.name_entry.text().strip()
        nickname = self.nickname_entry.text().strip()
        gender = "Male" if self.male_radio.isChecked() else "Female"
        score = self.score_entry.text().strip()
        pre_test = self.pre_test_entry.text().strip()
        post_test = self.post_test_entry.text().strip()
        note = self.note_entry.text().strip()
        active = "Yes" if self.active_yes.isChecked() else "No"

        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        if self.student_id:
            # Edit existing student
            self.data["classes"][self.class_id]["students"][self.student_id] = {
                "name": name,
                "nickname": nickname,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                "attendance": self.student_data.get("attendance", {}),
            }
        else:
            # Add new student
            student_id = self.generate_unique_student_id()
            self.data["classes"][self.class_id]["students"][student_id] = {
                "name": name,
                "nickname": nickname,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                "attendance": {},
            }

        save_data(self.data)  # Save changes to the file
        self.refresh_callback()  # Refresh the table
        self.accept()  # Close the dialog

    def generate_unique_student_id(self):
        """Generate a unique Student ID."""
        existing_ids = self.data["classes"][self.class_id]["students"].keys()
        idx = 1
        while True:
            student_id = f"S{str(idx).zfill(3)}"
            if student_id not in existing_ids:
                return student_id
            idx += 1

    def open_bulk_import_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Import Students")
        dialog.resize(700, 400)
        layout = QVBoxLayout(dialog)

        info_label = QLabel("Paste student data from Excel below (columns: Name, Nickname, Gender, Score, Pre-Test, Post-Test, Note, Active).")
        layout.addWidget(info_label)

        table = QTableWidget(10, 8)  # 10 rows, 8 columns as default
        table.setHorizontalHeaderLabels(["Name", "Nickname", "Gender", "Score", "Pre-Test", "Post-Test", "Note", "Active"])
        layout.addWidget(table)

        paste_button = QPushButton("Paste from Clipboard")
        paste_button.clicked.connect(lambda: self.paste_from_clipboard(table))
        layout.addWidget(paste_button)

        save_button = QPushButton("Save Imported Students")
        save_button.clicked.connect(lambda: self.save_bulk_import(table, dialog))
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def paste_from_clipboard(self, table):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        rows = text.strip().split('\n')
        for row_idx, row_data in enumerate(rows):
            columns = row_data.split('\t')
            for col_idx, value in enumerate(columns):
                if row_idx < table.rowCount() and col_idx < table.columnCount():
                    table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def save_bulk_import(self, table, dialog):
        students = self.data["classes"][self.class_id]["students"]
        from logic.parser import generate_next_student_id, save_data

        for row in range(table.rowCount()):
            name_item = table.item(row, 0)
            if not name_item or not name_item.text().strip():
                continue  # Skip empty rows
            name = name_item.text().strip()
            nickname = table.item(row, 1).text().strip() if table.item(row, 1) else ""
            gender = table.item(row, 2).text().strip() if table.item(row, 2) else "Female"
            score = table.item(row, 3).text().strip() if table.item(row, 3) else ""
            pre_test = table.item(row, 4).text().strip() if table.item(row, 4) else ""
            post_test = table.item(row, 5).text().strip() if table.item(row, 5) else ""
            note = table.item(row, 6).text().strip() if table.item(row, 6) else ""
            active = table.item(row, 7).text().strip() if table.item(row, 7) else "Yes"

            student_id = generate_next_student_id(students)
            students[student_id] = {
                "name": name,
                "nickname": nickname,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                "attendance": {},
            }
        save_data(self.data)
        self.refresh_callback()
        QMessageBox.information(self, "Bulk Import", "Students imported successfully!")
        dialog.accept()