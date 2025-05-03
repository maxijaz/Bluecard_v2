from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.parser import save_data


class StudentForm(QDialog):
    def __init__(self, parent, class_id, data, refresh_callback):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.refresh_callback = refresh_callback

        self.setWindowTitle("Add Student")
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_entry = QLineEdit()
        layout.addWidget(self.name_entry)

        # Nickname
        layout.addWidget(QLabel("Nickname:"))
        self.nickname_entry = QLineEdit()
        layout.addWidget(self.nickname_entry)

        # Gender
        layout.addWidget(QLabel("Gender:"))
        gender_layout = QHBoxLayout()
        self.male_radio = QRadioButton("Male")
        self.female_radio = QRadioButton("Female")
        self.female_radio.setChecked(True)  # Default to Female
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        layout.addLayout(gender_layout)

        # Score
        layout.addWidget(QLabel("Score:"))
        self.score_entry = QLineEdit()
        layout.addWidget(self.score_entry)

        # Pre-Test
        layout.addWidget(QLabel("Pre-Test:"))
        self.pre_test_entry = QLineEdit()
        layout.addWidget(self.pre_test_entry)

        # Post-Test
        layout.addWidget(QLabel("Post-Test:"))
        self.post_test_entry = QLineEdit()
        layout.addWidget(self.post_test_entry)

        # Note
        layout.addWidget(QLabel("Note:"))
        self.note_entry = QLineEdit()
        layout.addWidget(self.note_entry)

        # Active
        layout.addWidget(QLabel("Active:"))
        active_layout = QHBoxLayout()
        self.active_yes = QRadioButton("Yes")
        self.active_no = QRadioButton("No")
        self.active_yes.setChecked(True)  # Default to Yes
        active_layout.addWidget(self.active_yes)
        active_layout.addWidget(self.active_no)
        layout.addLayout(active_layout)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_student)
        button_layout.addWidget(add_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_student(self):
        """Add a new student to the class."""
        name = self.name_entry.text().strip()
        nickname = self.nickname_entry.text().strip()
        gender = "Male" if self.male_radio.isChecked() else "Female"
        score = self.score_entry.text().strip()
        pre_test = self.pre_test_entry.text().strip()
        post_test = self.post_test_entry.text().strip()
        note = self.note_entry.text().strip()
        active = "Yes" if self.active_yes.isChecked() else "No"

        if not name:
            # Ensure required fields are filled
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        # Generate a unique Student ID
        student_id = self.generate_unique_student_id()

        # Add the student to the data
        self.data["classes"][self.class_id]["students"][student_id] = {
            "name": name,
            "nickname": nickname,
            "gender": gender,
            "score": score,
            "pre_test": pre_test,
            "post_test": post_test,
            "note": note,
            "active": active,
            "attendance": {},  # Initialize with empty attendance
        }

        # Save the updated data to the file
        save_data(self.data)

        # Trigger the refresh callback
        self.refresh_callback()
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