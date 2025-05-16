import json
import os
from datetime import datetime  # Import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget, QFormLayout, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from logic.parser import save_data
from .calendar import CalendarView  # Import CalendarView
from logic.update_dates import update_dates, add_date, remove_date, modify_date  # Import the new functions
from datetime import datetime, timedelta

class MetadataForm(QDialog):
    class_saved = pyqtSignal(str)  # Signal to notify when a class is saved

    def __init__(self, parent, class_id, data, theme, on_metadata_save, defaults=None, is_read_only=False, single_date_mode=False):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.on_metadata_save = on_metadata_save
        self.is_edit = class_id is not None
        self.is_read_only = is_read_only  # New parameter to control read-only behavior
        self.single_date_mode = single_date_mode  # New parameter to differentiate modes

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
        self.resize(500, 600)  # Set the initial size without fixing it
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
            ("Start Date", "StartDate"),  # Remove mask for Start Date
            ("Finish Date", "FinishDate"),  # Remove mask for Finish Date
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

            # Add "Pick" button for StartDate
            if key == "StartDate":
                pick_button = QPushButton("Pick")
                pick_button.clicked.connect(self.pick_start_date)
                row_layout = QHBoxLayout()
                row_layout.addWidget(field_input)
                row_layout.addWidget(pick_button)
                self.fields[key] = field_input
                scroll_layout.addRow(field_label, row_layout)
            else:
                self.fields[key] = field_input
                scroll_layout.addRow(field_label, field_input)

        # Days Field (Checkboxes)
        self.days_label = QLabel("Days:")
        self.days_checkboxes = {}
        days_layout = QHBoxLayout()
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            checkbox = QCheckBox(day)
            self.days_checkboxes[day] = checkbox
            days_layout.addWidget(checkbox)

        # Prepopulate checkboxes if editing
        if self.is_edit:
            selected_days = metadata.get("Days", "").split(", ")
            for day in selected_days:
                if day in self.days_checkboxes:
                    self.days_checkboxes[day].setChecked(True)

        scroll_layout.addRow(self.days_label, days_layout)

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

        # --- Apply formatting rules ---
        metadata["class_no"] = class_no  # Always uppercase

        # Company: Capitalize first letter of each word, but preserve existing uppercase letters
        def smart_title(s):
            return " ".join(
                w if (len(w) > 1 and w.isupper()) else w[:1].upper() + w[1:]
                for w in s.split()
            )
        company = metadata.get("Company", "")
        metadata["Company"] = smart_title(company)

        metadata["CourseHours"] = self.class_hours_input.text()
        metadata["ClassTime"] = self.class_time_input.text()
        metadata["MaxClasses"] = self.max_classes_input.text()

        # Combine selected days into a comma-separated string
        selected_days = [day for day, checkbox in self.days_checkboxes.items() if checkbox.isChecked()]
        metadata["Days"] = ", ".join(selected_days)

        # Generate dates dynamically
        max_classes = int(metadata["MaxClasses"].split()[0])  # Extract the numeric part of MaxClasses
        start_date_str = metadata.get("StartDate", "")
        days_str = metadata.get("Days", "")
        metadata["Dates"] = generate_dates(start_date_str, days_str, max_classes)

        # Update metadata and students using update_dates
        students = self.data["classes"][self.class_id]["students"] if self.is_edit else {}
        metadata, students = update_dates(metadata, students)

        if not self.is_edit:
            self.data["classes"][class_no] = {"metadata": metadata, "students": students, "archive": "No"}
        else:
            self.data["classes"][self.class_id]["metadata"] = metadata
            self.data["classes"][self.class_id]["students"] = students

        save_data(self.data)
        self.on_metadata_save()

        # Emit the signal with the new class ID
        self.class_saved.emit(class_no)

        self.accept()  # Close the dialog

    def pick_start_date(self):
        """Open the calendar to pick a Start Date."""
        # Retrieve the existing dates from the metadata if editing, otherwise use an empty list
        scheduled_dates = []
        if self.is_edit and self.class_id:
            scheduled_dates = self.data["classes"][self.class_id]["metadata"].get("Dates", [])

        def on_save_callback(selected_dates):
            if self.single_date_mode:
                # Single-date mode: Set the first selected date as StartDate
                if selected_dates:
                    self.fields["StartDate"].setText(selected_dates[0])
            else:
                # Multi-date mode: Update the Dates metadata
                if selected_dates:
                    self.data["classes"][self.class_id]["metadata"]["Dates"] = selected_dates
                    self.fields["StartDate"].setText(selected_dates[0])  # Update StartDate to the earliest date

        # Open the CalendarView with the appropriate max_dates
        max_dates = 1 if self.single_date_mode else 20  # Allow only 1 date in single-date mode
        calendar_view = CalendarView(self, scheduled_dates=scheduled_dates, on_save_callback=on_save_callback, max_dates=max_dates)
        calendar_view.exec_()

    def closeEvent(self, event):
        """Restore the initial size when the form is reopened."""
        self.resize(500, 600)
        super().closeEvent(event)

def generate_dates(start_date_str, days_str, max_classes):
    """Generate a list of dates based on StartDate, Days, and MaxClasses."""
    # Parse StartDate
    try:
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    except ValueError:
        start_date = None  # If StartDate is invalid or missing

    # Parse Days into weekday indices (0=Monday, 1=Tuesday, ..., 6=Sunday)
    weekdays = []
    if days_str:
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        weekdays = [day_map[day.strip()] for day in days_str.split(",") if day.strip() in day_map]

    # Generate dates dynamically
    dates = []
    if start_date and weekdays:
        current_date = start_date
        while len(dates) < max_classes:
            if current_date.weekday() in weekdays:
                dates.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)  # Move to the next day

    # Fallback to placeholders if no valid dates are generated
    if not dates:
        dates = [f"Date{i + 1}" for i in range(max_classes)]

    return dates