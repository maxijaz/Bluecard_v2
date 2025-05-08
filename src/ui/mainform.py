import tkinter as tk
from tkinter import ttk, messagebox
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel,
    QHBoxLayout, QFrame, QGridLayout, QPushButton, QMessageBox, QStyledItemDelegate  # Added QMessageBox
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime, timedelta
import PyQt5.sip  # Import PyQt5.sip to bridge PyQt5 and Tkinter
from .archive_manager import ArchiveManager
import json  # Import json for reading and writing JSON files
import subprocess  # Import subprocess to run external scripts
import sys
import os # Import sys and os for path manipulation

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

DEFAULT_PATH = "data/default.json"  # Define the path to the default settings file


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
            header = self.headers[section]
            # Check if the header is a date in the format "DD/MM/YYYY"
            if len(header) == 10 and header[2] == "/" and header[5] == "/":
                return header[:5]  # Return only "DD/MM"
            return header
        return None


class AttendanceDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        value = index.data()
        if value == "P":
            option.backgroundBrush = QColor("#c8e6c9")  # Light green for Present
        elif value == "A":
            option.backgroundBrush = QColor("#ffcdd2")  # Light red for Absent
        elif value == "L":
            option.backgroundBrush = QColor("#fff9c4")  # Light yellow for Late


class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter  # Center-align the content


class FrozenTableDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Center-align all columns except the "Name" column (column index 1)
        if index.column() == 1:  # "Name" column
            option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
        else:
            option.displayAlignment = Qt.AlignCenter


class Mainform(QMainWindow):
    closed = pyqtSignal()  # Signal to notify when the Mainform is closed

    def __init__(self, class_id, data, theme):
        super().__init__()
        print("Initializing Mainform...")  # Debugging: Initialization
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

        # Load column visibility settings
        self.default_settings = self.load_default_settings()
        self.column_visibility = {
            "Score": self.default_settings.get("show_score", "Yes") == "Yes",
            "PreTest": self.default_settings.get("show_prestest", "Yes") == "Yes",
            "PostTest": self.default_settings.get("show_posttest", "Yes") == "Yes",
            "Attn": self.default_settings.get("show_attn", "Yes") == "Yes"
        }
        self.scrollable_column_visibility = {
            "P": self.default_settings.get("show_p", "Yes") == "Yes",
            "A": self.default_settings.get("show_a", "Yes") == "Yes",
            "L": self.default_settings.get("show_l", "Yes") == "Yes",
            "Dates": self.default_settings.get("show_dates", "Yes") == "Yes"
        }

        # Initialize frozen_table_width
        self.frozen_table_width = 0  # Ensure it is always defined

        # Initialize UI
        self.init_ui()

    def reset_scrollable_column_widths(self):
        """Reset the column widths of the scrollable table to their default values."""
        # Fixed widths for the first three columns (P, A, L)
        columns = ["P", "A", "L"]
        widths = [35, 35, 35]
        for i, column in enumerate(columns):
            if self.scrollable_column_visibility[column]:
                self.scrollable_table.setColumnWidth(i, widths[i])
                self.scrollable_table.setColumnHidden(i, False)
            else:
                self.scrollable_table.setColumnHidden(i, True)

        # Fixed widths for the date columns
        for col in range(3, self.scrollable_table.model().columnCount()):  # Date columns start at index 3
            if self.scrollable_column_visibility["Dates"]:
                self.scrollable_table.setColumnWidth(col, 40)  # Default width for date columns
                self.scrollable_table.setColumnHidden(col, False)
            else:
                self.scrollable_table.setColumnHidden(col, True)

        # Ensure all columns are resizable
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def init_ui(self):
        """Initialize the UI components."""
        # Main container widget
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Metadata Section (updated)
        metadata_widget = QWidget()  # Create a widget to contain the metadata layout
        metadata_layout = QGridLayout(metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        metadata_layout.setHorizontalSpacing(2)  # Reduce horizontal spacing
        metadata_layout.setVerticalSpacing(2)  # Reduce vertical spacing

        # Set the fixed width for the metadata widget
        metadata_widget.setFixedWidth(600)  # Total width: 100 + 150 + 100 + 150 + spacing

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
            # Label 1
            label1_widget = QLabel(label1)
            label1_widget.setStyleSheet("font-weight: bold; text-align: left; border: none;")
            label1_widget.setFixedWidth(100)  # Set fixed width for labels
            metadata_layout.addWidget(label1_widget, row, 0)

            # Value 1
            value1_widget = QLabel(value1)
            value1_widget.setStyleSheet("text-align: left; border: 1px solid gray; border-style: sunken;")
            value1_widget.setFixedWidth(200)  # Set fixed width for fields
            metadata_layout.addWidget(value1_widget, row, 1)

            if label2:
                # Label 2
                label2_widget = QLabel(label2)
                label2_widget.setStyleSheet("font-weight: bold; text-align: left; border: none;")
                label2_widget.setFixedWidth(100)  # Set fixed width for labels
                metadata_layout.addWidget(label2_widget, row, 2)

            if value2:
                # Value 2
                value2_widget = QLabel(value2)
                value2_widget.setStyleSheet("text-align: left; border: 1px solid gray; border-style: sunken;")
                value2_widget.setFixedWidth(200)  # Set fixed width for fields
                metadata_layout.addWidget(value2_widget, row, 3)

        # Add the metadata widget to the main layout
        self.layout.addWidget(metadata_widget)

        # Buttons Section
        buttons_layout = QHBoxLayout()
        add_edit_student_btn = QPushButton("Add/Edit Student")
        remove_student_btn = QPushButton("Manage/Remove Students")  # Correct button
        metadata_form_btn = QPushButton("Manage Metadata")

        # Connect buttons to their respective methods
        add_edit_student_btn.clicked.connect(self.add_edit_student)
        remove_student_btn.clicked.connect(self.remove_student)
        metadata_form_btn.clicked.connect(self.open_metadata_form)

        buttons = [add_edit_student_btn, remove_student_btn, metadata_form_btn]
        for button in buttons:
            buttons_layout.addWidget(button)
        self.layout.addLayout(buttons_layout)

        # Add a button to run htmlbluecard.py
        html_button = QPushButton("Run HTML Output")
        html_button.clicked.connect(self.run_html_output)  # Connect button to method
        self.layout.addWidget(html_button)  # Add button to the main layout

        # Table Section
        self.table_layout = QHBoxLayout()
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        # Frozen Table
        frozen_headers = ["#", "Name", "Nickname", "Score", "Pre", "Post", "Attn"]  # Updated PreTest -> Pre, PostTest -> Post
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
        self.frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.frozen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set the minimum section size for the horizontal header
        self.frozen_table.horizontalHeader().setMinimumSectionSize(5)

        # Set column widths
        self.frozen_table.setColumnWidth(0, 20)  # #
        self.frozen_table.setColumnWidth(1, 150)  # Name
        self.frozen_table.setColumnWidth(2, 80)  # Nickname
        self.frozen_table.setColumnWidth(3, 40)  # Score
        self.frozen_table.setColumnWidth(4, 40)  # PreTest
        self.frozen_table.setColumnWidth(5, 40)  # PostTest
        self.frozen_table.setColumnWidth(6, 40)  # Attn

        # Calculate total width of frozen table
        self.frozen_table_width = 410  # Match the sum of the column widths
        self.frozen_table.setFixedWidth(self.frozen_table_width)

        # Set the FrozenTableDelegate for the frozen table
        self.frozen_table.setItemDelegate(FrozenTableDelegate(self.frozen_table))

        # Center-align all headers except the "Name" column
        for col in range(self.frozen_table.model().columnCount()):
            if col == 1:  # "Name" column
                self.frozen_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            else:
                self.frozen_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        self.frozen_table.horizontalHeader().setStyleSheet("font-weight: bold;")

        # Connect double-click signal to edit_student method
        self.frozen_table.doubleClicked.connect(self.edit_student)

        self.frozen_table.horizontalHeader().sectionResized.connect(self.adjust_frozen_table_width)

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
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Enable dynamic resizing
        self.scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Set the minimum section size for the horizontal header
        self.scrollable_table.horizontalHeader().setMinimumSectionSize(5)  # Set minimum width to 5 pixels

        # Set the AttendanceDelegate for the scrollable table
        self.scrollable_table.setItemDelegate(AttendanceDelegate(self.scrollable_table))

        # Set the CenterAlignDelegate for the scrollable table
        self.scrollable_table.setItemDelegate(CenterAlignDelegate(self.scrollable_table))

        self.scrollable_table.horizontalHeader().setStyleSheet("font-weight: bold; text-align: center;")

        # Add tables to the layout
        self.table_layout.addWidget(self.frozen_table)
        self.table_layout.addWidget(self.scrollable_table)
        self.layout.addLayout(self.table_layout)

        # Reset column widths for the scrollable table
        self.reset_scrollable_column_widths()

        # Connect selection models for synchronization
        self.frozen_table.selectionModel().selectionChanged.connect(self.sync_selection_to_scrollable)
        self.scrollable_table.selectionModel().selectionChanged.connect(self.sync_selection_to_frozen)

        # Set the main layout
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.refresh_student_table()  # Populate the tables during initialization
        self.reset_column_widths()
        self.reset_scrollable_column_widths()

    # Button Methods
    def add_edit_student(self):
        """Handle adding or editing a student."""
        selected_row = self.frozen_table.currentIndex().row()

        if selected_row == -1:
            print("Add Student button clicked")
            def refresh_callback():
                print("Refreshing student table after adding a student...")
                self.refresh_student_table()
            student_form = StudentForm(self, self.class_id, self.data, refresh_callback)
            student_form.exec_()
        else:
            print("Edit Student button clicked")
            student_id = list(self.students.keys())[selected_row]
            student_data = self.students[student_id]
            def refresh_callback():
                print("Refreshing student table after editing a student...")
                self.refresh_student_table()
            student_form = StudentForm(self, self.class_id, self.data, refresh_callback, student_id, student_data)
            student_form.exec_()

    def remove_student(self):
        """Handle removing or managing students."""
        # Check if a row is selected
        if not self.frozen_table.selectionModel().hasSelection():
            # No row selected, open the ArchiveManager
            print("No student selected. Opening Archive Manager...")
            archive_manager = ArchiveManager(self, self.data, self.class_id, self.refresh_student_table)
            archive_manager.exec_()  # Open the ArchiveManager as a modal dialog
            return

        # A row is selected, archive the student
        selected_row = self.frozen_table.currentIndex().row()
        adjusted_row = selected_row - 1  # Adjust for the "Running Total" row
        if adjusted_row < 0:
            QMessageBox.warning(self, "Invalid Selection", "Cannot archive the 'Running Total' row.")
            return

        # Get the student ID and data for the selected row
        student_id = list(self.students.keys())[adjusted_row]
        student_data = self.students[student_id]

        # Confirm archiving the student
        confirm = QMessageBox.question(
            self,
            "Archive Student",
            f"Are you sure you want to archive the student '{student_data['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            # Archive the student
            self.students[student_id]["active"] = "No"  # Set active to "No"
            save_data(self.data)  # Save the updated data
            print(f"Student '{student_data['name']}' archived successfully.")

            # Refresh the Mainform
            self.refresh_student_table()

    def open_metadata_form(self):
        """Open the Metadata Form."""
        print("Manage Metadata button clicked")
        metadata_form = MetadataForm(self, self.class_id, self.data)
        metadata_form.exec_()  # Open the form as a modal dialog

    def resizeEvent(self, event):
        """Adjust the width and position of the scrollable table dynamically."""
        if hasattr(self, "frozen_table") and self.frozen_table.width() > 0:
            QTimer.singleShot(0, self.update_scrollable_table_position)  # Delay the update
        super().resizeEvent(event)  # Call the base class implementation

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

    def sync_selection_to_scrollable(self, selected, deselected):
        """Synchronize selection from the frozen table to the scrollable table."""
        selected_rows = {index.row() for index in selected.indexes()}
        self.scrollable_table.selectionModel().blockSignals(True)  # Block signals temporarily
        self.scrollable_table.selectionModel().clearSelection()
        for row in selected_rows:
            self.scrollable_table.selectRow(row)
        self.scrollable_table.selectionModel().blockSignals(False)  # Unblock signals

    def sync_selection_to_frozen(self, selected, deselected):
        """Synchronize selection from the scrollable table to the frozen table."""
        selected_rows = {index.row() for index in selected.indexes()}
        self.frozen_table.selectionModel().blockSignals(True)  # Block signals temporarily
        self.frozen_table.selectionModel().clearSelection()
        for row in selected_rows:
            self.frozen_table.selectRow(row)
        self.frozen_table.selectionModel().blockSignals(False)  # Unblock signals

    def closeEvent(self, event):
        """Handle the close event to reopen the Launcher."""
        self.closed.emit()  # Emit the closed signal
        event.accept()  # Accept the close event

    def refresh_student_table(self):
        """Refresh the student table with updated data."""
        print("refresh_student_table called")  # Debugging: Method entry

        # Filter students where "Archive" = "No"
        active_students = {key: student for key, student in self.students.items() if student.get("active", "Yes") == "Yes"}

        # Rebuild the frozen table data
        frozen_headers = ["#", "Name", "Nickname", "Score", "Pre", "Post", "Attn"]  # Updated PreTest -> Pre, PostTest -> Post
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
            for idx, student in enumerate(active_students.values())
        ]

        # Add "Running Total" row to the frozen table
        frozen_data.insert(0, ["", "Running Total", "", "", "", "", ""])

        self.frozen_table.setModel(TableModel(frozen_data, frozen_headers))

        # Rebuild the scrollable table data
        attendance_dates = self.get_attendance_dates()
        scrollable_headers = ["P", "A", "L"] + attendance_dates
        scrollable_data = []

        for student in active_students.values():
            attendance = student.get("attendance", {})
            total_p = sum(1 for date in attendance_dates if attendance.get(date) == "P")
            total_a = sum(1 for date in attendance_dates if attendance.get(date) == "A")
            total_l = sum(1 for date in attendance_dates if attendance.get(date) == "L")
            row_data = [total_p, total_a, total_l] + [attendance.get(date, "-") for date in attendance_dates]
            scrollable_data.append(row_data)

        # Calculate the running total for the first row
        class_time = int(self.metadata.get("ClassTime", "2"))  # Default to 2 if not provided
        running_total = [class_time * (i + 1) for i in range(len(attendance_dates))]
        running_total_row = ["", "", ""] + running_total

        # Add "Running Total" row to the scrollable table
        scrollable_data.insert(0, running_total_row)

        print(f"Scrollable data: {scrollable_data}")  # Debugging: Check scrollable table data

        self.scrollable_table.setModel(TableModel(scrollable_data, scrollable_headers))

        # Style the first three columns (P, A, L)
        for col in range(3):
            self.scrollable_table.setColumnWidth(col, 35)  # Fixed width for P, A, L
            self.scrollable_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)

        # Set fixed width for date columns
        for col in range(3, len(scrollable_headers)):  # Date columns start at index 3
            self.scrollable_table.setColumnWidth(col, 40)  # Fixed width for date columns
            self.scrollable_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)

        # Center the headers for P, A, L
        self.scrollable_table.horizontalHeader().setStyleSheet(
            """
            QHeaderView::section {
                font-weight: normal;
                text-align: center;
            }
            """
        )

    def edit_student(self, index):
        """Open the StudentForm in Edit mode for the selected student."""
        selected_row = index.row()

        # Adjust for the "Running Total" row
        if selected_row == 0:
            QMessageBox.warning(self, "Invalid Selection", "Cannot edit the 'Running Total' row.")
            return

        adjusted_row = selected_row - 1  # Subtract 1 to skip the "Running Total" row

        # Get the student ID and data for the adjusted row
        student_id = list(self.students.keys())[adjusted_row]
        student_data = self.students[student_id]

        # Define a callback to refresh the student table after editing
        def refresh_callback():
            print("Callback triggered: Refreshing student table...")
            self.refresh_student_table()

        # Open the StudentForm in Edit mode
        student_form = StudentForm(self, self.class_id, self.data, refresh_callback, student_id, student_data)

        # Center the form relative to the Mainform
        student_form.move(
            self.geometry().center().x() - student_form.width() // 2,
            self.geometry().center().y() - student_form.height() // 2
        )

        # Open the form as a modal dialog
        student_form.exec_()
        print("Calling refresh_student_table from edit_student")
        self.refresh_student_table()

    def reset_column_widths(self):
        """Reset the column widths of the frozen table to their default values."""
        self.frozen_table.setColumnWidth(0, 20)  # #
        self.frozen_table.setColumnWidth(1, 150)  # Name
        self.frozen_table.setColumnWidth(2, 80)  # Nickname

        # Dynamically set visibility for the remaining columns
        columns = ["Score", "PreTest", "PostTest", "Attn"]
        widths = [40, 40, 40, 40]
        for i, column in enumerate(columns, start=3):
            if self.column_visibility[column]:
                self.frozen_table.setColumnWidth(i, widths[i - 3])
                self.frozen_table.setColumnHidden(i, False)
            else:
                self.frozen_table.setColumnHidden(i, True)

        self.adjust_frozen_table_width()  # Recalculate frozen table width
        self.update_scrollable_table_position()  # Update scrollable table position

    def adjust_frozen_table_width(self):
        """Adjust the frozen table's frame width to match the total column widths."""
        total_width = sum(self.frozen_table.columnWidth(col) for col in range(self.frozen_table.model().columnCount()))
        print(f"Calculated frozen table width: {total_width}")  # Debugging
        self.frozen_table.setFixedWidth(total_width)
        self.frozen_table_width = total_width  # Update the frozen table width
        self.update_scrollable_table_position()  # Ensure the scrollable table is updated

    def update_scrollable_table_position(self):
        """Update the position and width of the scrollable table."""
        # Get the right edge of the frozen table using geometry for accurate positioning
        frozen_table_right = self.frozen_table.geometry().right()
        print(f"Frozen table right edge (delayed): {frozen_table_right}")  # Debugging

        # Calculate the available width for the scrollable table
        available_width = self.width() - frozen_table_right
        print(f"Available width for scrollable table (delayed): {available_width}")  # Debugging

        # Ensure the scrollable table takes up the remaining space
        if available_width > 0:
            self.scrollable_table.setFixedWidth(available_width)
        else:
            self.scrollable_table.setFixedWidth(0)  # Fallback to 0 if no space is available

        # Align the scrollable table to the right of the frozen table and match its y-coordinate
        self.scrollable_table.move(frozen_table_right, self.frozen_table.geometry().top())
        print(f"Scrollable table moved to (delayed): {self.scrollable_table.geometry()}")  # Debugging
        print(f"Parent layout margins: {self.layout.contentsMargins()}")  # Debugging
        print(f"Parent layout geometry: {self.container.geometry()}")  # Debugging
        print(f"Frozen table geometry: {self.frozen_table.geometry()}")  # Debugging
        print(f"Scrollable table geometry: {self.scrollable_table.geometry()}")  # Debugging

    def load_default_settings(self):
        """Load default settings from default.json."""
        if not os.path.exists(DEFAULT_PATH):
            return {}
        try:
            with open(DEFAULT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def run_html_output(self):
        """Run htmlbluecard.py to output HTML."""
        try:
            # Run htmlbluecard.py in a separate process
            subprocess.Popen(
                ["python", "src/ui/htmlbluecard.py"],
                shell=True,
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),  # Set working directory
            )
            QMessageBox.information(self, "HTML Output", "HTML output is running in your browser.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run HTML output: {e}")


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