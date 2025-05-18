import tkinter as tk
from tkinter import ttk, messagebox
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel,
    QHBoxLayout, QFrame, QGridLayout, QPushButton, QMessageBox, QStyledItemDelegate, QDialog  # Added QDialog
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
from .calendar import CalendarView
from logic.update_dates import update_dates, add_date, remove_date, modify_date  # Import the new functions
from PyQt5.QtCore import QItemSelection, QItemSelectionModel
from .pal_cod_form import PALCODForm
from ui.settings import SettingsForm  # Make sure this import is at the top

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
            try:
                return self.data[index.row()][index.column()]
            except IndexError:
                return ""
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
        self.setWindowTitle(f"Class Information - {class_id}")
        self.resize(1280, 720)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.metadata = self.data["classes"][self.class_id]["metadata"]
        self.students = self.data["classes"][self.class_id]["students"]

        self.default_settings = self.load_default_settings()
        self.column_visibility = {
            "Nickname": self.default_settings.get("show_nickname", "Yes") == "Yes",
            "CompanyNo": self.default_settings.get("show_company_no", "Yes") == "Yes",
            "Score": self.default_settings.get("show_score", "Yes") == "Yes",
            "PreTest": self.default_settings.get("show_prestest", "Yes") == "Yes",
            "PostTest": self.default_settings.get("show_posttest", "Yes") == "Yes",
            "Attn": self.default_settings.get("show_attn", "Yes") == "Yes",
            "P": self.default_settings.get("show_p", "Yes") == "Yes",   # <-- Add
            "A": self.default_settings.get("show_a", "Yes") == "Yes",   # <-- Add
            "L": self.default_settings.get("show_l", "Yes") == "Yes"    # <-- Add
        }
        self.scrollable_column_visibility = {
            "Dates": self.default_settings.get("show_dates", "Yes") == "Yes"
        }

        self.frozen_table_width = 0
        self.init_ui()

    def reset_scrollable_column_widths(self):
        """Reset the column widths of the scrollable table to their default values."""
        # Fixed widths for the date columns
        for col in range(self.scrollable_table.model().columnCount()):  # All columns are now date columns
            self.scrollable_table.setColumnWidth(col, 50)  # Default width for date columns

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
            ("Notes:", self.metadata.get("Notes", ""), "COD/CIA:", self.metadata.get("COD_CIA", "")),  # Combine Notes and COD/CIA
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
        remove_student_btn = QPushButton("Manage/Remove Students")
        pal_cod_btn = QPushButton("PAL/COD")
        html_button = QPushButton("Run HTML Output")
        metadata_form_btn = QPushButton("Manage Metadata")
        manage_dates_btn = QPushButton("Manage Dates")  # Placeholder button
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)

        # Connect buttons to their respective methods
        add_edit_student_btn.clicked.connect(self.add_edit_student)
        remove_student_btn.clicked.connect(self.remove_student)
        pal_cod_btn.clicked.connect(self.open_pal_cod_form)  # Connect to the new form
        html_button.clicked.connect(self.run_html_output)
        metadata_form_btn.clicked.connect(self.open_metadata_form)
        manage_dates_btn.clicked.connect(self.open_calendar_view)

        # Add buttons to the layout
        buttons = [
            add_edit_student_btn, remove_student_btn, pal_cod_btn,
            html_button, metadata_form_btn, manage_dates_btn, settings_btn  # Add settings_btn here
        ]
        for button in buttons:
            buttons_layout.addWidget(button)
        self.layout.addLayout(buttons_layout)

        # Table Section
        self.table_layout = QHBoxLayout()
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        # Frozen Table
        frozen_headers = ["#","Name"]
        if self.column_visibility.get("Nickname", True):
            frozen_headers.append("Nickname")
        if self.column_visibility.get("CompanyNo", True):
            frozen_headers.append("Company No")
        if self.column_visibility.get("Score", True):
            frozen_headers.append("Score")
        if self.column_visibility.get("PreTest", True):
            frozen_headers.append("PreTest")
        if self.column_visibility.get("PostTest", True):
            frozen_headers.append("PostTest")
        if self.column_visibility.get("Attn", True):
            frozen_headers.append("Attn")
        frozen_data = [
            [
                idx + 1,
                student.get("name", ""),
                student.get("nickname", ""),
                student.get("company_no", ""),
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

        self.frozen_table.horizontalHeader().setStyleSheet("font-weight: bold;")

        # Connect double-click signal to edit_student method
        self.frozen_table.doubleClicked.connect(self.edit_student)

        self.frozen_table.horizontalHeader().sectionResized.connect(self.adjust_frozen_table_width)

        # Scrollable Table
        attendance_dates = self.get_attendance_dates()
        scrollable_headers = attendance_dates  # Only include date columns
        scrollable_data = [
            [student.get("attendance", {}).get(date, "-") for date in attendance_dates]
            for student in self.students.values()
        ]

        self.scrollable_table = QTableView()
        self.scrollable_table.setModel(TableModel(scrollable_data, scrollable_headers))
        self.scrollable_table.verticalHeader().hide()
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Enable dynamic resizing
        self.scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Connect the sectionClicked signal to highlight the column
        self.scrollable_table.horizontalHeader().sectionClicked.connect(self.highlight_column)

        # **Connect the sectionDoubleClicked signal to open_pal_cod_form**
        self.scrollable_table.horizontalHeader().sectionDoubleClicked.connect(self.open_pal_cod_form)

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

        # Synchronize vertical scrollbars
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.scrollable_table.verticalScrollBar().setValue
        )
        self.scrollable_table.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue
        )

        # Set the main layout
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.refresh_student_table()  # Populate the tables during initialization
        self.reset_column_widths()
        self.reset_scrollable_column_widths()

        self.scrollable_table.doubleClicked.connect(self.edit_attendance_field)

    # Button Methods
    def add_edit_student(self):
        """Handle adding or editing a student."""
        selected_row = self.frozen_table.currentIndex().row()

        # Adjust for the "Running Total" row
        adjusted_row = selected_row - 1  # Subtract 1 to skip the "Running Total" row

        if adjusted_row < 0:
            # No valid student row selected, add a new student
            print("Add Student button clicked")
            def refresh_callback():
                print("Refreshing student table after adding a student...")
                self.refresh_student_table()
                self.frozen_table.selectionModel().clearSelection()  # Clear selection after adding

            student_form = StudentForm(self, self.class_id, self.data, refresh_callback)
            student_form.exec_()
        else:
            # A valid student row is selected, edit the student
            print("Edit Student button clicked")
            try:
                student_id = list(self.students.keys())[adjusted_row]
                student_data = self.students[student_id]

                def refresh_callback():
                    print("Refreshing student table after editing a student...")
                    self.refresh_student_table()
                    self.frozen_table.selectionModel().clearSelection()  # Clear selection after editing

                student_form = StudentForm(self, self.class_id, self.data, refresh_callback, student_id, student_data)
                student_form.exec_()
            except IndexError:
                QMessageBox.warning(self, "Error", "Invalid row selected. Please try again.")

    def remove_student(self):
        """Handle removing or managing students."""
        # Check if a row is selected
        if not self.frozen_table.selectionModel().hasSelection():
            # No row selected, open the StudentManager
            print("No student selected. Opening Student Manager...")
            student_manager = StudentManager(self, self.data, self.class_id, self.refresh_student_table)
            student_manager.exec_()  # Open the StudentManager as a modal dialog
            return

        # A row is selected, confirm removal
        selected_row = self.frozen_table.currentIndex().row()
        adjusted_row = selected_row - 1  # Adjust for the "Running Total" row
        if adjusted_row < 0:
            QMessageBox.warning(self, "Invalid Selection", "Cannot remove the 'Running Total' row.")
            return

        # Get the student ID and data for the selected row
        student_id = list(self.students.keys())[adjusted_row]
        student_data = self.students[student_id]

        # Confirm removal of the student
        confirm = QMessageBox.question(
            self,
            "Remove Student",
            f"Are you sure you want to mark the student '{student_data['name']}' as inactive?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            # Mark the student as inactive
            self.students[student_id]["active"] = "No"
            save_data(self.data)  # Save the updated data
            print(f"Student '{student_data['name']}' marked as inactive.")

            # Refresh the Mainform
            self.refresh_student_table()
        else:
            # Clear the selection if the user clicks "No"
            self.frozen_table.selectionModel().clearSelection()

    def open_metadata_form(self):
        """Open the Metadata Form."""
        print("Manage Metadata button clicked")

        # Pass the Dates metadata to the MetadataForm
        metadata_form = MetadataForm(
            self,
            self.class_id,
            self.data,
            self.theme,  # Pass the theme argument
            self.refresh_student_table,  # Pass the on_metadata_save callback
            is_read_only=True  # Make class_no read-only
        )

        # Connect the class_saved signal to refresh the metadata and student table
        metadata_form.class_saved.connect(self.refresh_metadata)
        metadata_form.class_saved.connect(self.refresh_student_table)

        # Open the form as a modal dialog
        metadata_form.exec_()

    def resizeEvent(self, event):
        """Adjust the width and position of the scrollable table dynamically."""
        if hasattr(self, "frozen_table") and self.frozen_table.width() > 0:
            QTimer.singleShot(0, self.update_scrollable_table_position)  # Delay the update
        super().resizeEvent(event)  # Call the base class implementation

    def get_attendance_dates(self):
        """Get all unique attendance dates dynamically based on StartDate, Days, and MaxClasses."""
        if "Dates" in self.metadata:
            return self.metadata["Dates"]

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
        active_students = {
            key: student
            for key, student in self.students.items()
            if student.get("active", "Yes") == "Yes"
        }

        # Initialize totals for all fields
        total_cia = 0
        total_cod = 0

        # Calculate CIA and COD totals by searching scrollable_data
        attendance_dates = self.metadata.get("Dates", [])
        scrollable_data = [
            [student.get("attendance", {}).get(date, "-") for date in attendance_dates]
            for student in self.students.values()
        ]

        for col_index in range(len(attendance_dates)):
            column_values = [row[col_index] for row in scrollable_data]
            if "CIA" in column_values:
                total_cia += 1
            if "COD" in column_values:
                total_cod += 1

        # Update the metadata with COD/CIA totals
        self.metadata["COD_CIA"] = f"{total_cod} COD / {total_cia} CIA"

        # Rebuild the frozen table data
        frozen_headers = ["#", "Name"]
        if self.column_visibility.get("Nickname", True):
            frozen_headers.append("Nickname")
        if self.column_visibility.get("CompanyNo", True):
            frozen_headers.append("Company No")
        if self.column_visibility.get("Score", True):
            frozen_headers.append("Score")
        if self.column_visibility.get("PreTest", True):
            frozen_headers.append("PreTest")
        if self.column_visibility.get("PostTest", True):
            frozen_headers.append("PostTest")
        if self.column_visibility.get("Attn", True):
            frozen_headers.append("Attn")
        if self.column_visibility.get("P", True):
            frozen_headers.append("P")
        if self.column_visibility.get("A", True):
            frozen_headers.append("A")
        if self.column_visibility.get("L", True):
            frozen_headers.append("L")

        frozen_data = []

        # Add "Running Total" row to the frozen table
        class_time = int(self.metadata.get("ClassTime", "2"))  # Default to 2 if not provided
        running_total = []
        cumulative_total = 0

        for date in attendance_dates:
            # Check if any student has "CIA" or "HOL" for this date (COD now counts as a class)
            has_cia_hol = any(
                student.get("attendance", {}).get(date) in ["CIA", "HOL"]
                for student in self.students.values()
            )
            if has_cia_hol:
                running_total.append("-")  # Exclude this date from the running total
            else:
                cumulative_total += class_time
                running_total.append(cumulative_total)

        # Add "-" for columns that don't need a count in the "Running Total" row
        # Build the running total row to match the visible frozen headers
        running_total_row = []
        # header_iter = iter(frozen_headers)
        for header in frozen_headers:
            if header == "#":
                running_total_row.append("")
            elif header == "Name":
                running_total_row.append("Running Total")
            else:
                running_total_row.append("-")
        # Do NOT append running_total here, as frozen table should only have as many columns as headers
        frozen_data.append(running_total_row)

        # Add student rows
        for idx, student in enumerate(active_students.values()):
            row = [idx + 1, student.get("name", "")]
            if self.column_visibility.get("Nickname", True):
                row.append(student.get("nickname", ""))
            if self.column_visibility.get("CompanyNo", True):
                row.append(student.get("company_no", ""))
            if self.column_visibility.get("Score", True):
                row.append(student.get("score", ""))
            if self.column_visibility.get("PreTest", True):
                row.append(student.get("pre_test", ""))
            if self.column_visibility.get("PostTest", True):
                row.append(student.get("post_test", ""))
            if self.column_visibility.get("Attn", True):
                row.append(len(student.get("attendance", {})))
            if self.column_visibility.get("P", True):
                row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "P"))
            if self.column_visibility.get("A", True):
                row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "A"))
            if self.column_visibility.get("L", True):
                row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "L"))
            frozen_data.append(row)

        # Debugging: Check frozen_data dimensions
        print("Frozen Data Dimensions:", len(frozen_data), len(frozen_headers))
        for row in frozen_data:
            print("Row Length:", len(row))

        self.frozen_table.setModel(TableModel(frozen_data, frozen_headers))

        # Center-align all headers in the frozen table
        header = self.frozen_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        # Rebuild the scrollable table data
        scrollable_headers = attendance_dates
        scrollable_data = []

        # Add "Running Total" row
        scrollable_data.append(running_total)

        # Add student attendance rows
        for student in active_students.values():
            row_data = [student.get("attendance", {}).get(date, "-") for date in attendance_dates]
            scrollable_data.append(row_data)

        # Debugging: Check scrollable_data dimensions
        print("Scrollable Data Dimensions:", len(scrollable_data), len(scrollable_headers))
        for row in scrollable_data:
            print("Row Length:", len(row))

        self.scrollable_table.setModel(TableModel(scrollable_data, scrollable_headers))

        # Adjust column widths
        self.reset_column_widths()
        self.reset_scrollable_column_widths()

        print("Frozen Data:", frozen_data)
        print("Scrollable Data:", scrollable_data)

        # Refresh the metadata section to include COD/CIA totals
        self.refresh_metadata()

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

    FROZEN_COLUMN_WIDTHS = {
        "#": 30,
        "Name": 150,
        "Nickname": 100,
        "Company No": 100,
        "Score": 65,
        "PreTest": 65,
        "PostTest": 65,
        "Attn": 50,
        "P": 30,
        "A": 30,
        "L": 30,
    }

    def reset_column_widths(self):
        """Reset the column widths of the frozen table to their fixed values based on header name."""
        model = self.frozen_table.model()
        if not model:
            return
        for col in range(model.columnCount()):
            header = model.headers[col]
            width = self.FROZEN_COLUMN_WIDTHS.get(header, 50)  # Default to 50 if not found
            self.frozen_table.setColumnWidth(col, width)
        self.adjust_frozen_table_width()
        self.update_scrollable_table_position()

    def adjust_frozen_table_width(self):
        """Adjust the frozen table's frame width to match the total column widths."""
        total_width = sum(self.frozen_table.columnWidth(col) for col in range(self.frozen_table.model().columnCount()))
        self.frozen_table.setFixedWidth(total_width)
        self.frozen_table_width = total_width  # Update the frozen table width
        self.update_scrollable_table_position()  # Ensure the scrollable table is updated

    def update_scrollable_table_position(self):
        """Update the position and width of the scrollable table."""
        # Get the right edge of the frozen table using geometry for accurate positioning
        frozen_table_right = self.frozen_table.geometry().right()

        # Calculate the available width for the scrollable table
        available_width = self.width() - frozen_table_right

        # Ensure the scrollable table takes up the remaining space
        if (available_width > 0):
            self.scrollable_table.setFixedWidth(available_width)
        else:
            self.scrollable_table.setFixedWidth(0)  # Fallback to 0 if no space is available

        # Align the scrollable table to the right of the frozen table and match its y-coordinate
        self.scrollable_table.move(frozen_table_right, self.frozen_table.geometry().top())

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
            # Write data to a temporary JSON file
            temp_data_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "temp_data.json"))
            with open(temp_data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)

            # Run htmlbluecard.py in a separate process
            subprocess.Popen(
                ["python", "src/ui/htmlbluecard.py"],
                shell=True,
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),  # Set working directory
            )
            QMessageBox.information(self, "HTML Output", "HTML output is running in your browser.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run HTML output: {e}")

    def refresh_metadata(self):
        """Refresh the metadata section with updated data."""
        print("Refreshing metadata...")  # Debugging: Method entry

        # Update the metadata dictionary
        self.metadata = self.data["classes"][self.class_id]["metadata"]

        # Clear the existing metadata layout
        metadata_widget = self.layout.itemAt(0).widget()
        metadata_layout = metadata_widget.layout()
        while metadata_layout.count():
            item = metadata_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild the metadata fields
        metadata_fields = [
            ("Company:", self.metadata.get("Company", ""), "Course Hours:", 
             f"{self.metadata.get('CourseHours', '')} / {self.metadata.get('ClassTime', '')} / {self.metadata.get('MaxClasses', '')}"),
            ("Room:", self.metadata.get("Room", ""), "Start Date:", self.metadata.get("StartDate", "")),
            ("Consultant:", self.metadata.get("Consultant", ""), "Finish Date:", self.metadata.get("FinishDate", "")),
            ("Teacher:", self.metadata.get("Teacher", ""), "Days:", self.metadata.get("Days", "")),
            ("CourseBook:", self.metadata.get("CourseBook", ""), "Time:", self.metadata.get("Time", "")),
            ("Notes:", self.metadata.get("Notes", ""), "COD/CIA:", self.metadata.get("COD_CIA", "")),  # Combine Notes and COD/CIA
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

    def open_calendar_view(self):
        """Open the calendar view to display and manage the schedule."""
        print("Opening Calendar View...")  # Debugging: Method entry

        # Get the current attendance dates
        scheduled_dates = self.get_attendance_dates()
        print(f"Scheduled dates before calendar: {scheduled_dates}")  # Debugging: Check current dates

        # Identify protected dates (dates with attendance values like "P", "A", "L", "CIA", "COD", "HOL")
        protected_dates = set()
        for student in self.students.values():
            attendance = student.get("attendance", {})
            for date, value in attendance.items():
                if value in ["P", "A", "L", "CIA", "COD", "HOL"]:
                    protected_dates.add(date)

        print(f"Protected dates: {protected_dates}")  # Debugging: Check protected dates

        # Define a callback to handle saving changes from the calendar
        def on_save_callback(selected_dates):
            print(f"Selected dates from calendar: {selected_dates}")  # Debugging: Check selected dates

            # Update metadata and students using update_dates
            self.metadata["Dates"] = selected_dates
            self.metadata, self.students = update_dates(self.metadata, self.students)

            # Save the updated data
            save_data(self.data)

            # Refresh the metadata and table to reflect the changes
            self.refresh_metadata()
            self.refresh_student_table()

        # Open the CalendarView
        max_classes = int(self.metadata.get("MaxClasses", "20").split()[0])  # Extract the numeric part of MaxClasses
        print(f"Max classes allowed: {max_classes}")  # Debugging: Check max classes
        calendar_view = CalendarView(self, scheduled_dates, on_save_callback, max_dates=max_classes, protected_dates=protected_dates)
        calendar_view.exec_()

    def highlight_column(self, column_index):
        """Highlight the entire column when a header is clicked."""
        self.scrollable_table.selectionModel().clearSelection()
        model = self.scrollable_table.model()
        row_count = model.rowCount()
        top_left = model.index(0, column_index)
        bottom_right = model.index(row_count - 1, column_index)
        selection = QItemSelection(top_left, bottom_right)
        self.scrollable_table.selectionModel().select(selection, QItemSelectionModel.Select | QItemSelectionModel.Columns)

    def open_pal_cod_form(self):
        """Open the PALCODForm to update attendance."""
        # Get the selected column index
        selected_columns = self.scrollable_table.selectionModel().selectedColumns()
        if not selected_columns:
            QMessageBox.warning(self, "No Column Selected", "Please select a column header to update.")
            return

        column_index = selected_columns[0].column()  # Get the first selected column

        # Validate the column index
        attendance_dates = self.metadata.get("Dates", [])
        if column_index < 0 or column_index >= len(attendance_dates):
            QMessageBox.warning(self, "Invalid Column", "Please select a valid date column.")
            return

        date = attendance_dates[column_index]

        # --- Block if the header is not a real date (e.g., "Date1", "date2", "Empty-1") ---
        if not (len(date) == 10 and date[2] == "/" and date[5] == "/" and date.replace("/", "").isdigit()):
            QMessageBox.warning(
                self,
                "Invalid Date",
                "Cannot set P/A/L for this column. Please add real dates first before attempting to change attendance."
            )
            return

        # Open the PALCODForm with COD and CIA options, without student name
        pal_cod_form = PALCODForm(self, column_index, self.update_column_values, None, date, show_cod_cia=True, show_student_name=False)
        if pal_cod_form.exec_() == QDialog.Accepted:
            # Get the selected value from the form
            new_value = pal_cod_form.selected_value

            # Update the attendance data for all students in the selected column
            self.update_column_values(column_index, new_value)

    def update_column_values(self, column_index, value):
        """Update the selected column with the given value for all students."""
        attendance_dates = self.metadata.get("Dates", [])

        # Validate the column index
        if (column_index < 0 or column_index >= len(attendance_dates)):
            QMessageBox.warning(self, "Invalid Column", "The selected column is out of range.")
            return

        date = attendance_dates[column_index]  # Get the corresponding date

        # Update the attendance value for all students (skip the "Running Total" row)
        for student in self.students.values():
            student["attendance"][date] = value

        # --- Ensure there are always MaxClasses teaching dates (excluding CIA/HOL) ---
        max_classes = int(self.metadata.get("MaxClasses", "20").split()[0])

        def is_teaching_date(d):
            return not any(
                student.get("attendance", {}).get(d) in ["CIA", "HOL"]
                for student in self.students.values()
            )

        attendance_dates = self.metadata["Dates"]  # Make sure to use the updated list
        teaching_dates = [d for d in attendance_dates if is_teaching_date(d)]

        # Add new dates if needed
        while len(teaching_dates) < max_classes:
            if attendance_dates:
                last_date = datetime.strptime(attendance_dates[-1], "%d/%m/%Y")
                days_str = self.metadata.get("Days", "")
                weekdays = []
                if days_str:
                    day_map = {
                        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
                    }
                    weekdays = [day_map[day.strip()] for day in days_str.split(",") if day.strip() in day_map]
                next_date = last_date
                while True:
                    next_date += timedelta(days=1)
                    if not weekdays or next_date.weekday() in weekdays:
                        break
                new_date_str = next_date.strftime("%d/%m/%Y")
            else:
                new_date_str = f"Extra-{len(attendance_dates)+1}"
            attendance_dates.append(new_date_str)
            for student in self.students.values():
                student["attendance"][new_date_str] = "-"
            teaching_dates.append(new_date_str)

        # --- Remove extra dates if there are too many teaching dates ---
        while len(teaching_dates) > max_classes:
            # Remove the last date in attendance_dates that is a teaching date
            for i in range(len(attendance_dates) - 1, -1, -1):
                d = attendance_dates[i]
                if is_teaching_date(d):
                    # Remove this date from attendance_dates and all students' attendance
                    del attendance_dates[i]
                    for student in self.students.values():
                        if d in student["attendance"]:
                            del student["attendance"][d]
                    teaching_dates.remove(d)
                    break  # Remove one at a time

        # Save the updated dates and data
        self.metadata["Dates"] = attendance_dates
        save_data(self.data)

        # Refresh the frozen table and scrollable table
        self.refresh_student_table()

    def refresh_scrollable_table_column(self, column_index):
        """Refresh a specific column in the scrollable table."""
        model = self.scrollable_table.model()
        if not model:
            return

        # Notify the view that the data in the column has changed
        row_count = model.rowCount()
        if row_count > 0:
            top_left = model.index(0, column_index)
            bottom_right = model.index(row_count - 1, column_index)
            model.dataChanged.emit(top_left, bottom_right)

    def refresh_scrollable_table(self):
        """Rebuild the scrollable table model to reflect updated data."""
        attendance_dates = self.metadata.get("Dates", [])
        scrollable_headers = attendance_dates  # Only include date columns
        scrollable_data = []

        # Add "Running Total" row
        class_time = int(self.metadata.get("ClassTime", "2"))  # Default to 2 if not provided
        running_total = [class_time * (i + 1) for i in range(len(attendance_dates))]
        scrollable_data.append(running_total)  # Add the "Running Total" row as the first row

        # Add student attendance rows
        for student in self.students.values():
            attendance = student.get("attendance", {})
            row_data = [attendance.get(date, "-") for date in attendance_dates]
            scrollable_data.append(row_data)

        # Update the model
        self.scrollable_table.setModel(TableModel(scrollable_data, scrollable_headers))

        # Reset column widths
        self.reset_scrollable_column_widths()

    def edit_attendance_field(self, index):
        """Open a dialog to edit the selected attendance field."""
        row = index.row()
        column = index.column()

        # Skip the "Running Total" row
        if row == 0:
            QMessageBox.warning(self, "Invalid Selection", "Cannot edit the 'Running Total' row.")
            return

        # Get the corresponding date and column data
        attendance_dates = self.metadata.get("Dates", [])
        if column < 0 or column >= len(attendance_dates):
            QMessageBox.warning(self, "Invalid Selection", "Please select a valid date column.")
            return

        date = attendance_dates[column]

        # --- Only allow editing if the header is a valid date ---
        # Check if the header is a real date (e.g., "20/05/2025")
        if not (len(date) == 10 and date[2] == "/" and date[5] == "/"):
            QMessageBox.warning(
                self,
                "Invalid Date",
                "Please add dates first before attempting to change attendance."
            )
            return

        # row - 1 because row 0 is running total, row 1 is first student, etc.
        student_keys = list(self.students.keys())
        if (row - 1) < 0 or (row - 1) >= len(student_keys):
            QMessageBox.warning(self, "Invalid Selection", "Student row out of range.")
            return

        student_id = student_keys[row - 1]
        student_name = self.students[student_id].get("name", "Unknown")
        current_value = self.students[student_id]["attendance"].get(date, "-")

        # Check if the column contains "CIA" or "COD"
        column_values = [self.students[sid]["attendance"].get(date, "-") for sid in self.students]
        if "CIA" in column_values or "COD" in column_values or "HOL" in column_values:
            QMessageBox.warning(
                self,
                "Edit Blocked",
                "Press header [date] to clear CIA, COD, or HOL before \nchanging any individual attendance data (P,A,L)....",
                QMessageBox.Cancel,
            )
            return  # Do not proceed with editing

        # Open the PALCODForm without COD and CIA options, with student name
        dialog = PALCODForm(self, column, None, current_value, date, student_name, show_cod_cia=False, show_student_name=True)
        if dialog.exec_() == QDialog.Accepted:
            new_value = dialog.selected_value

            # Update the attendance data for the specific student and date
            self.students[student_id]["attendance"][date] = new_value

            # Save the updated data
            save_data(self.data)

            # Refresh the tables
            self.refresh_student_table()

    def open_settings(self):
        """Open the Settings dialog."""
        settings_form = SettingsForm(self, self.theme, self.apply_theme_and_refresh)
        settings_form.exec_()

    def apply_theme_and_refresh(self, selected_theme):
        # Reload settings and refresh UI as needed
        self.default_settings = self.load_default_settings()
        self.theme = selected_theme

        # Rebuild column visibility dictionaries from updated settings
        self.column_visibility = {
            "Nickname": self.default_settings.get("show_nickname", "Yes") == "Yes",
            "CompanyNo": self.default_settings.get("show_company_no", "Yes") == "Yes",
            "Score": self.default_settings.get("show_score", "Yes") == "Yes",
            "PreTest": self.default_settings.get("show_prestest", "Yes") == "Yes",
            "PostTest": self.default_settings.get("show_posttest", "Yes") == "Yes",
            "Attn": self.default_settings.get("show_attn", "Yes") == "Yes",
            "P": self.default_settings.get("show_p", "Yes") == "Yes",
            "A": self.default_settings.get("show_a", "Yes") == "Yes",
            "L": self.default_settings.get("show_l", "Yes") == "Yes"
        }
        self.scrollable_column_visibility = {
            "show_dates": self.default_settings.get("show_dates", "Yes") == "Yes"
        }

        self.refresh_student_table()
        # Optionally, refresh other UI elements if needed


class EditAttendanceDialog(QDialog):
    def __init__(self, parent, current_value):
        super().__init__(parent)
        self.setWindowTitle("Edit Attendance")
        self.setFixedSize(300, 200)

        self.selected_value = current_value

        # Layout
        layout = QVBoxLayout(self)

        # Buttons
        buttons = {
            "P = Present": "P",
            "A = Absent": "A",
            "L = Late": "L",
            "Clear": "-",
        }

        for label, value in buttons.items():
            button = QPushButton(label)
            if value == current_value:  # Highlight the current value
                button.setStyleSheet("background-color: lightblue; font-weight: bold;")
            button.clicked.connect(lambda _, v=value: self.select_value(v))
            layout.addWidget(button)

    def select_value(self, value):
        """Set the selected value and close the dialog."""
        self.selected_value = value
        self.accept()  # Close the dialog


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
