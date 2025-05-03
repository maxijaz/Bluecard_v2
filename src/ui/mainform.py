import tkinter as tk
from tkinter import ttk, messagebox
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel, QHBoxLayout, QFrame, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime, timedelta
import PyQt5.sip  # Import PyQt5.sip to bridge PyQt5 and Tkinter


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self.data = data
        self.headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self.data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.data[index.row()][index.column()]
        elif role == Qt.BackgroundRole:
            # Alternate row coloring for better readability
            if index.row() % 2 == 0:
                return QColor("#f0f0f0")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None


class Mainform(QMainWindow):
    closed = pyqtSignal()  # Signal to notify when the Mainform is closed

    def __init__(self, class_id, data, theme):
        super().__init__()
        self.setWindowTitle(f"Class Information - {class_id}")

        # Set default size and constraints
        self.resize(1280, 720)  # Default size
        self.setMinimumSize(800, 600)  # Minimum size
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.metadata = self.data["classes"][self.class_id]["metadata"]
        self.students = self.data["classes"][self.class_id]["students"]

        # Initialize frozen_table_width
        self.frozen_table_width = 0  # Ensure it is always defined

        # Main container widget
        container = QWidget()
        self.layout = QVBoxLayout(container)

        # Metadata Section (unchanged)
        metadata_layout = QGridLayout()
        metadata_layout.setHorizontalSpacing(5)
        metadata_layout.setVerticalSpacing(5)

        metadata_fields = [
            ("Company:", self.metadata.get("Company", ""), "Course Hours:", 
             f"{self.metadata.get('CourseHours', '')} / {self.metadata.get('ClassTime', '')} / {self.metadata.get('MaxClasses', '')}"),
            ("Room:", self.metadata.get("Room", ""), "Start Date:", self.metadata.get("StartDate", "")),
            ("Consultant:", self.metadata.get("Consultant", ""), "Finish Date:", self.metadata.get("FinishDate", "")),
            ("Teacher:", self.metadata.get("Teacher", ""), "Days:", self.metadata.get("Days", "")),
            ("CourseBook:", self.metadata.get("CourseBook", ""), "Time:", self.metadata.get("Time", "")),
            ("Notes:", self.metadata.get("Notes", ""), "", ""),
        ]

        for row, (label1, value1, label2, value2) in enumerate(metadata_fields):
            label1_widget = QLabel(label1)
            label1_widget.setStyleSheet("font-weight: bold; text-align: left; border: 1px groove black;")
            label1_widget.setFixedWidth(150)
            metadata_layout.addWidget(label1_widget, row, 0)

            value1_widget = QLabel(value1)
            value1_widget.setStyleSheet("text-align: center; border: 1px groove black;")
            value1_widget.setFixedWidth(150)
            metadata_layout.addWidget(value1_widget, row, 1)

            if label2:
                label2_widget = QLabel(label2)
                label2_widget.setStyleSheet("font-weight: bold; text-align: left; border: 1px groove black;")
                label2_widget.setFixedWidth(150)
                metadata_layout.addWidget(label2_widget, row, 2)

            if value2:
                value2_widget = QLabel(value2)
                value2_widget.setStyleSheet("text-align: center; border: 1px groove black;")
                value2_widget.setFixedWidth(150)
                metadata_layout.addWidget(value2_widget, row, 3)

        self.layout.addLayout(metadata_layout)

        # Buttons Section
        buttons_layout = QHBoxLayout()
        add_student_btn = QPushButton("Add Student")
        edit_student_btn = QPushButton("Edit Student")
        remove_student_btn = QPushButton("Remove Student")
        metadata_form_btn = QPushButton("Manage Metadata")

        # Connect buttons to their respective methods
        add_student_btn.clicked.connect(self.add_student)
        edit_student_btn.clicked.connect(self.edit_student)
        remove_student_btn.clicked.connect(self.remove_student)
        metadata_form_btn.clicked.connect(self.open_metadata_form)

        buttons = [add_student_btn, edit_student_btn, remove_student_btn, metadata_form_btn]
        for button in buttons:
            buttons_layout.addWidget(button)
        self.layout.addLayout(buttons_layout)

        # Table Section
        self.table_layout = QHBoxLayout()
        self.table_layout.setSpacing(0)  # Remove gap between tables

        # Frozen Table
        frozen_headers = ["#", "Name", "Nickname", "Score", "PreTest", "PostTest", "Attn"]
        frozen_data = [
            [
                idx + 1,
                student.get("name", ""),
                student.get("nickname", ""),
                student.get("score", ""),
                student.get("pre_test", ""),
                student.get("post_test", ""),
                len(student.get("attendance", {})),  # Attendance count
            ]
            for idx, student in enumerate(self.students.values())
        ]

        self.frozen_table = QTableView()
        self.frozen_table.setModel(TableModel(frozen_data, frozen_headers))
        self.frozen_table.verticalHeader().hide()
        self.frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.frozen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set column widths
        self.frozen_table.setColumnWidth(0, 10)  # #
        self.frozen_table.setColumnWidth(1, 150)  # Name
        self.frozen_table.setColumnWidth(2, 100)  # Nickname
        self.frozen_table.setColumnWidth(3, 60)  # Score
        self.frozen_table.setColumnWidth(4, 60)  # PreTest
        self.frozen_table.setColumnWidth(5, 60)  # PostTest
        self.frozen_table.setColumnWidth(6, 25)  # Attn

        # Calculate total width of frozen table
        self.frozen_table_width = 10 + 150 + 100 + 60 + 60 + 60 + 90
        self.frozen_table.setFixedWidth(self.frozen_table_width)

        self.frozen_table.horizontalHeader().setStyleSheet("font-weight: bold; text-align: center;")

        # Scrollable Table
        attendance_dates = self.get_attendance_dates()
        scrollable_headers = ["P", "A", "L"] + attendance_dates
        scrollable_data = [
            ["-", "-", "-"] + [student.get("attendance", {}).get(date, "-") for date in attendance_dates]
            for student in self.students.values()
        ]

        self.scrollable_table = QTableView()
        self.scrollable_table.setModel(TableModel(scrollable_data, scrollable_headers))
        self.scrollable_table.verticalHeader().hide()
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.scrollable_table.horizontalHeader().setStyleSheet("font-weight: bold; text-align: center;")

        # Add tables to the layout
        self.table_layout.addWidget(self.frozen_table)
        self.table_layout.addWidget(self.scrollable_table)
        self.layout.addLayout(self.table_layout)

        # Set the main layout
        self.setCentralWidget(container)

    # Button Methods
    def add_student(self):
        """Open the Add Student form."""
        print("Add Student button clicked")

        # Define a callback to refresh the student table after adding a student
        def refresh_callback():
            print("Refreshing student table...")
            self.refresh_student_table()

        # Pass the refresh_callback to the StudentForm
        student_form = StudentForm(self, self.class_id, self.data, refresh_callback)
        student_form.exec_()  # Open the form as a modal dialog

    def edit_student(self):
        """Open the Edit Student form."""
        print("Edit Student button clicked")
        # Logic to open the Edit Student form goes here

    def remove_student(self):
        """Remove the selected student."""
        print("Remove Student button clicked")
        # Logic to remove the selected student goes here

    def open_metadata_form(self):
        """Open the Metadata Form."""
        print("Manage Metadata button clicked")
        metadata_form = MetadataForm(self, self.class_id, self.data)
        metadata_form.exec_()  # Open the form as a modal dialog

    def resizeEvent(self, event):
        """Adjust the width of the scrollable table dynamically."""
        if hasattr(self, "frozen_table_width") and self.frozen_table_width > 0:
            available_width = self.width() - self.frozen_table_width
            if available_width > 0:
                self.scrollable_table.setFixedWidth(available_width)
        super().resizeEvent(event)

    def get_attendance_dates(self):
        """Get all unique attendance dates dynamically based on StartDate, Days, and MaxClasses."""
        max_classes_str = self.metadata.get("MaxClasses", "10")
        max_classes = int(max_classes_str.split()[0])  # Extract the numeric part (e.g., "10" from "10 (1 hour remains)")

        start_date_str = self.metadata.get("StartDate", "")
        days_str = self.metadata.get("Days", "")

        # Parse StartDate
        try:
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        except ValueError:
            start_date = None  # If StartDate is invalid or missing, fallback to placeholders

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
            dates = [f"Empty-{i + 1}" for i in range(max_classes)]

        return dates

    def closeEvent(self, event):
        """Handle the close event to reopen the Launcher."""
        self.closed.emit()  # Emit the closed signal
        event.accept()  # Accept the close event


if __name__ == "__main__":
    import sys

    # Example data
    example_data = {
        "classes": {
            "OLO123": {
                "metadata": {
                    "Company": "Example Company",
                    "Consultant": "John Doe",
                    "Teacher": "Jane Smith",
                    "Room": "101",
                    "CourseBook": "Advanced Python",
                },
                "students": {},
            }
        }
    }

    app = QApplication(sys.argv)
    window = Mainform("OLO123", example_data, "default")
    window.show()
    sys.exit(app.exec_())