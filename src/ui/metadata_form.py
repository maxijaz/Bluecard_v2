from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from logic.parser import save_data


class MetadataForm(QDialog):
    def __init__(self, parent, class_id, data, theme, on_metadata_save, defaults=None):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.on_metadata_save = on_metadata_save
        self.is_edit = class_id is not None

        self.setWindowTitle("Edit Metadata" if self.is_edit else "Add New Class")
        self.setFixedSize(600, 700)  # Adjusted size for additional fields
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout(self)

        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)

        # Fields
        self.fields = {}
        metadata = self.data["classes"][self.class_id]["metadata"] if self.is_edit else (defaults or {})
        for label, key in [
            ("Class No*", "class_no"),
            ("Company*", "Company"),
            ("Consultant", "Consultant"),
            ("Teacher", "Teacher"),
            ("Teacher No", "TeacherNo"),
            ("Room", "Room"),
            ("CourseBook", "CourseBook"),
            ("Course Hours", "CourseHours"),
            ("Class Time", "ClassTime"),
            ("Start Date", "StartDate"),
            ("Finish Date", "FinishDate"),
            ("Days", "Days"),
            ("Time", "Time"),
            ("Notes", "Notes"),
            ("Rate", "rate"),
            ("CCP", "ccp"),
            ("Travel", "travel"),
            ("Bonus", "bonus"),
            ("Max Classes", "MaxClasses"),
        ]:
            field_label = QLabel(label)
            field_input = QLineEdit()
            field_input.setText(metadata.get(key, ""))  # Use default or existing value
            self.fields[key] = field_input
            scroll_layout.addRow(field_label, field_input)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_metadata)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def save_metadata(self):
        """Save metadata for the class."""
        class_no = self.fields["class_no"].text().strip().upper()
        if not class_no:
            QMessageBox.warning(self, "Validation Error", "Class No is required.")
            return

        if class_no in self.data["classes"] and not self.is_edit:
            QMessageBox.warning(self, "Duplicate Class ID", f"Class ID '{class_no}' already exists.")
            return

        metadata = {key: field.text().strip() for key, field in self.fields.items()}
        if not self.is_edit:
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            self.data["classes"][self.class_id]["metadata"] = metadata

        save_data(self.data)
        self.on_metadata_save()
        self.accept()  # Close the dialog