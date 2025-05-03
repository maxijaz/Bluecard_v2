from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

class StudentForm(QDialog):
    def __init__(self, parent, class_id, data, refresh_callback):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.refresh_callback = refresh_callback

        self.setWindowTitle("Add Student")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Student Name:"))
        self.name_entry = QLineEdit()
        layout.addWidget(self.name_entry)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_student)
        layout.addWidget(add_button)

        self.setLayout(layout)

    def add_student(self):
        name = self.name_entry.text()
        if name:
            # Add student logic
            self.refresh_callback()
            self.accept()  # Close the dialog