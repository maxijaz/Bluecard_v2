import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from logic.parser import save_data


class MetadataForm(QDialog):
    class_saved = pyqtSignal(str)  # Signal to notify when a class is saved

    def __init__(self, parent, class_id, data, theme, on_metadata_save, defaults=None, is_read_only=False):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.on_metadata_save = on_metadata_save
        self.is_edit = class_id is not None
        self.is_read_only = is_read_only  # New parameter to control read-only behavior

        # Load defaults from default.json
        if not self.is_edit:
            defaults_path = "data/default.json"
            if os.path.exists(defaults_path):
                with open(defaults_path, "r") as f:
                    defaults = json.load(f)
            else:
                defaults = {}
        self.defaults = defaults or {}

        self.setWindowTitle("Edit Metadata" if self.is_edit else "Add New Class")
        self.setFixedSize(300, 560)  # Adjusted size for additional fields
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
        metadata = self.data["classes"][self.class_id]["metadata"] if self.is_edit else {}
        for label, key in [
            ("Class No*", "class_no"),
            ("Company*", "Company"),
            ("Consultant", "Consultant"),
            ("Teacher", "Teacher"),
            ("Teacher No", "TeacherNo"),
            ("Room", "Room"),
            ("CourseBook", "CourseBook"),
            ("Start Date", "StartDate"),
            ("Finish Date", "FinishDate"),
            ("Days", "Days"),
            ("Time", "Time"),
            ("Notes", "Notes"),
            ("Rate", "rate"),
            ("CCP", "ccp"),
            ("Travel", "travel"),
            ("Bonus", "bonus"),
        ]:
            field_label = QLabel(label)
            field_input = QLineEdit()

            # Use default value if adding a new class, otherwise use existing metadata
            if not self.is_edit:
                default_key = f"def_{key.lower()}"
                field_input.setText(self.defaults.get(default_key, ""))
            else:
                field_input.setText(metadata.get(key, ""))

            # Make class_no read-only if is_read_only is True
            if key == "class_no" and self.is_read_only:
                field_input.setReadOnly(True)

            self.fields[key] = field_input
            scroll_layout.addRow(field_label, field_input)

        # CourseHours
        self.class_hours_label = QLabel("Course Hours:")
        self.class_hours_input = QLineEdit()
        self.class_hours_input.setText(self.defaults.get("def_coursehours", "40"))
        scroll_layout.addRow(self.class_hours_label, self.class_hours_input)

        # ClassTime
        self.class_time_label = QLabel("Class Time:")
        self.class_time_input = QLineEdit()
        self.class_time_input.setText(self.defaults.get("def_classtime", "2"))
        scroll_layout.addRow(self.class_time_label, self.class_time_input)

        # MaxClasses
        self.max_classes_label = QLabel("Max Classes:")
        self.max_classes_input = QLineEdit()
        self.max_classes_input.setReadOnly(True)
        scroll_layout.addRow(self.max_classes_label, self.max_classes_input)

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

        # Connect signals
        self.class_hours_input.textChanged.connect(self.update_max_classes)
        self.class_time_input.textChanged.connect(self.update_max_classes)

        # Initialize MaxClasses
        self.update_max_classes()

    def update_max_classes(self):
        """Recalculate MaxClasses based on CourseHours and ClassTime, supporting decimals."""
        try:
            course_hours = float(self.class_hours_input.text())
            class_time = float(self.class_time_input.text())

            if class_time > 0:
                max_classes = int(course_hours // class_time)  # Whole number of classes
                total_time_used = max_classes * class_time
                remainder = course_hours - total_time_used  # Remaining hours

                if remainder > 0:
                    self.max_classes_input.setText(f"{max_classes} x {class_time} = {total_time_used:.1f} ({remainder:.1f} hour remains)")
                else:
                    self.max_classes_input.setText(f"{max_classes} x {class_time} = {total_time_used:.1f}")
            else:
                self.max_classes_input.setText("0")
        except ValueError:
            self.max_classes_input.setText("Invalid input")

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
        metadata["CourseHours"] = self.class_hours_input.text()
        metadata["ClassTime"] = self.class_time_input.text()
        metadata["MaxClasses"] = self.max_classes_input.text()

        if not self.is_edit:
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            self.data["classes"][self.class_id]["metadata"] = metadata

        save_data(self.data)
        self.on_metadata_save()

        # Emit the signal with the new class ID
        self.class_saved.emit(class_no)

        self.accept()  # Close the dialog