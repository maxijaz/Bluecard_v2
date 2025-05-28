from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel,
    QHBoxLayout, QFrame, QGridLayout, QPushButton, QMessageBox, QStyledItemDelegate, QDialog  # Added QDialog
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QColor, QFont
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime, timedelta
import PyQt5.sip  # Import PyQt5.sip to bridge PyQt5 and Tkinter
from .archive_manager import ArchiveManager
import subprocess  # Import subprocess to run external scripts
import sys
import re
import os # Import sys and os for path manipulation
from .calendar import CalendarView, launch_calendar  # Make sure to import the new function
from logic.update_dates import update_dates, add_date, remove_date, modify_date  # Import the new functions
from PyQt5.QtCore import QItemSelection, QItemSelectionModel
from .pal_cod_form import PALCODForm
from ui.settings import SettingsForm  # Make sure this import is at the top
from logic.db_interface import (
    get_class_by_id,
    get_students_by_class,
    get_attendance_by_student,
    update_class,
    update_student,
    get_all_defaults,
    set_attendance,
)

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

class TableModel(QAbstractTableModel):
    def __init__(self, students, attendance_dates, class_time=2):
        super().__init__()
        self.students = students  # dict of student_id: student_data
        self.attendance_dates = attendance_dates
        self.student_keys = list(students.keys())
        self.class_time = class_time

        # Precompute running total row
        self.running_total = [self.class_time * (i + 1) for i in range(len(self.attendance_dates))]

    def rowCount(self, parent=QModelIndex()):
        # +1 for the running total row
        return 1 + len(self.student_keys)

    def columnCount(self, parent=QModelIndex()):
        return len(self.attendance_dates)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row == 0:
            # Running total row
            if role == Qt.DisplayRole:
                return self.running_total[col]
            return None
        student_id = self.student_keys[row - 1]
        date = self.attendance_dates[col]
        value = self.students[student_id]["attendance"].get(date, "-")
        if role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole:
            if value == "P":
                return QColor("#c8e6c9")
            elif value == "A":
                return QColor("#ffcdd2")
            elif value == "L":
                return QColor("#fff9c4")
        return None

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        col = index.column()
        if role == Qt.EditRole and row > 0:
            student_id = self.student_keys[row - 1]
            date = self.attendance_dates[col]
            self.students[student_id]["attendance"][date] = value
            self.dataChanged.emit(index, index)
            return True
        return False

        def flags(self, index):
            if index.row() == 0:
                return Qt.ItemIsEnabled  # Running total row is not editable/selectable
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled  # Remove Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.attendance_dates[section]
        return None


class AttendanceDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        value = index.data()
        option.displayAlignment = Qt.AlignCenter
        option.palette.setColor(option.palette.Text, Qt.black)  # Normal text
        option.palette.setColor(option.palette.HighlightedText, Qt.black)  # Selected text
        if value == "P":
            option.backgroundBrush = QColor("#c8e6c9")
        elif value == "A":
            option.backgroundBrush = QColor("#ffcdd2")
        elif value == "L":
            option.backgroundBrush = QColor("#fff9c4")


class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.palette.setColor(option.palette.Text, Qt.black)
        option.palette.setColor(option.palette.HighlightedText, Qt.black)
        option.displayAlignment = Qt.AlignCenter


class FrozenTableDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() == 1:
            option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
        else:
            option.displayAlignment = Qt.AlignCenter
        option.palette.setColor(option.palette.Text, Qt.black)
        option.palette.setColor(option.palette.HighlightedText, Qt.black)


class DebugTableView(QTableView):
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            mainform = self.parent()
            while mainform and not hasattr(mainform, "select_row_in_both_tables"):
                mainform = mainform.parent()
            if (mainform):
                mainform.select_row_in_both_tables(index.row())
        super().mousePressEvent(event)


class Mainform(QMainWindow):
    closed = pyqtSignal()  # Signal to notify when the Mainform is closed

    def __init__(self, class_id, data, theme):
        super().__init__()
        self.setWindowTitle(f"Class Information - {class_id}")
        self.resize(1280, 720)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        self.class_id = class_id
        self.theme = theme

        # --- PATCH: Load from DB ---
        self.class_data = get_class_by_id(self.class_id)
        self.students = {}
        for student_row in get_students_by_class(self.class_id):
            student_id = student_row["student_id"]
            attendance_records = get_attendance_by_student(student_id)
            attendance = {rec["date"]: rec["status"] for rec in attendance_records}
            student_row["attendance"] = attendance
            self.students[student_id] = student_row
        self.metadata = self.class_data  # All fields are now top-level

        # Ensure self.metadata["dates"] is set
        if "dates" not in self.metadata or not self.metadata["dates"]:
            # Generate dates if missing
            max_classes_str = self.metadata.get("max_classes", "10")
            max_classes = int(max_classes_str.split()[0])
            start_date_str = self.metadata.get("start_date", "")
            days_str = self.metadata.get("days", "")
            try:
                start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
            except ValueError:
                start_date = None
            weekdays = []
            if days_str:
                day_map = {
                    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
                }
                weekdays = [day_map[day.strip()] for day in days_str.split(",") if day.strip() in day_map]
            dates = []
            if start_date and weekdays:
                current_date = start_date
                while len(dates) < max_classes:
                    if current_date.weekday() in weekdays:
                        dates.append(current_date.strftime("%d/%m/%Y"))
                    current_date += timedelta(days=1)
            if not dates:
                dates = [f"Empty-{i + 1}" for i in range(max_classes)]
            self.metadata["dates"] = dates

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
        self.columns_before_today = int(self.default_settings.get("columns_before_today", 3))

        self.frozen_table_width = 0
        self._syncing_selection = False  # <-- Add this line
        self.init_ui()

        self.installEventFilter(self)  # <-- Add this line

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
            ("Company:", self.metadata.get("company", ""), "Course Hours:", 
             f"{self.metadata.get('course_hours', '')} / {self.metadata.get('class_time', '')} / {self.metadata.get('max_classes', '')}"),
            ("Room:", self.metadata.get("room", ""), "Start Date:", self.metadata.get("start_date", "")),
            ("Consultant:", self.metadata.get("consultant", ""), "Finish Date:", self.metadata.get("finish_date", "")),
            ("Teacher:", self.metadata.get("teacher", ""), "Days:", self.metadata.get("days", "")),
            ("CourseBook:", self.metadata.get("course_book", ""), "Time:", self.metadata.get("time", "")),
            ("Notes:", self.metadata.get("notes", ""), "COD/CIA:", self.metadata.get("cod_cia", "")),  # Combine Notes and COD/CIA
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
        show_hide_btn = QPushButton("Show/Hide")
        show_hide_btn.clicked.connect(self.open_show_hide)

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
            html_button, metadata_form_btn, manage_dates_btn, show_hide_btn  # Add settings_btn here
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

        self.frozen_table = DebugTableView()
        self.frozen_table.setObjectName("FROZEN")
        self.frozen_table.setModel(FrozenTableModel(frozen_data, frozen_headers))
        self.frozen_table.verticalHeader().hide()
        self.frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.frozen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setSelectionMode(QAbstractItemView.SingleSelection)

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

        self.scrollable_table = DebugTableView()
        self.scrollable_table.setObjectName("SCROLLABLE")
        self.scrollable_table.setModel(TableModel(self.students, attendance_dates))
        self.scrollable_table.verticalHeader().hide()
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # Enable dynamic resizing
        self.scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.scrollable_table.setSelectionMode(QAbstractItemView.SingleSelection)

        # Connect the sectionClicked signal to highlight the column
        self.scrollable_table.horizontalHeader().sectionClicked.connect(self.highlight_column)

        # **Connect the sectionDoubleClicked signal to open_pal_cod_form**
        self.scrollable_table.horizontalHeader().sectionDoubleClicked.connect(
        lambda col: self.open_pal_cod_form(col)
        )

        # Set a 1px solid right border for the frozen table
        self.frozen_table.setStyleSheet("""
            QTableView {
                border-right: 1px solid #ccc;
                border-top: none;
                border-bottom: none;
                border-left: none;
            }
        """)

        # Set a 1px solid left border for the scrollable table (optional, for contrast)
        self.scrollable_table.setStyleSheet("""
            QTableView {
                border-left: 0px solid #ccc;
                border-top: none;
                border-bottom: none;
                border-right: none;
            }
        """)

        # Set the minimum section size for the horizontal header
        self.scrollable_table.horizontalHeader().setMinimumSectionSize(5)  # Set minimum width to 5 pixels

        # Set the AttendanceDelegate for the scrollable table
        self.scrollable_table.setItemDelegate(AttendanceDelegate(self.scrollable_table))

        # Set the CenterAlignDelegate for the scrollable table
        # self.scrollable_table.setItemDelegate(CenterAlignDelegate(self.scrollable_table))

        self.scrollable_table.horizontalHeader().setStyleSheet("font-weight: bold; text-align: center;")

        # Add tables to the layout
        self.table_layout.addWidget(self.frozen_table)
        self.table_layout.addWidget(self.scrollable_table)
        self.layout.addLayout(self.table_layout)

        # Reset column widths for the scrollable table
        self.reset_scrollable_column_widths()

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

        highlight_style = """
QTableView::item:selected {
    background: #b3d7ff;  /* Light blue highlight */
}
"""
        self.frozen_table.setStyleSheet(self.frozen_table.styleSheet() + highlight_style)
        self.scrollable_table.setStyleSheet(self.scrollable_table.styleSheet() + highlight_style)

        self.frozen_table.selectionModel().selectionChanged.connect(self.debug_frozen_selection)
        self.scrollable_table.selectionModel().selectionChanged.connect(self.debug_scrollable_selection)

    # Button Methods
    def run_html_output(self):
        """Run htmlbluecard.py to output HTML."""
        try:
            # --- PATCH: No need to write temp_data.json, just launch htmlbluecard.py ---
            subprocess.Popen(
                ["python", "src/ui/htmlbluecard.py"],
                shell=True,
                cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),  # Set working directory
            )
            QMessageBox.information(self, "HTML Output", "HTML output is running in your browser.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run HTML output: {e}")

    def add_edit_student(self):
        """Handle adding or editing a student."""
        selected_row = self.frozen_table.currentIndex().row()
        adjusted_row = selected_row - 1  # Subtract 1 to skip the "Running Total" row

        if adjusted_row < 0:
            print("Add Student button clicked")
            def refresh_callback():
                print("Refreshing student table after adding a student...")
                self.refresh_student_table()
                self.frozen_table.selectionModel().clearSelection()  # Clear selection after adding

            default_attendance = self.get_default_attendance_for_new_student()
            student_form = StudentForm(self, self.class_id, {}, refresh_callback, default_attendance=default_attendance)
            student_form.exec_()
        else:
            print("Edit Student button clicked")
            try:
                student_id = list(self.students.keys())[adjusted_row]
                student_data = self.students[student_id]

                def refresh_callback():
                    print("Refreshing student table after editing a student...")
                    self.refresh_student_table()
                    self.frozen_table.selectionModel().clearSelection()  # Clear selection after editing

                student_form = StudentForm(self, self.class_id, {}, refresh_callback, student_id, student_data)
                student_form.exec_()
            except IndexError:
                QMessageBox.warning(self, "Error", "Invalid row selected. Please try again.")

    def remove_student(self):
        """Handle removing or managing students."""
        if not self.frozen_table.selectionModel().hasSelection():
            print("No student selected. Opening Student Manager...")
            student_manager = StudentManager(self, {}, self.class_id, self.refresh_student_table)
            student_manager.exec_()
            return

        selected_row = self.frozen_table.currentIndex().row()
        adjusted_row = selected_row - 1
        if adjusted_row < 0:
            QMessageBox.warning(self, "Invalid Selection", "Cannot remove the 'Running Total' row.")
            return

        student_id = list(self.students.keys())[adjusted_row]
        student_data = self.students[student_id]

        confirm = QMessageBox.question(
            self,
            "Remove Student",
            f"Are you sure you want to mark the student '{student_data['name']}' as inactive?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.students[student_id]["active"] = "No"
            update_student(student_id, self.students[student_id])
            print(f"Student '{student_data['name']}' marked as inactive.")
            self.refresh_student_table()
        else:
            self.frozen_table.selectionModel().clearSelection()

    def open_metadata_form(self):
        """Open the Metadata Form."""
        print("Manage Metadata button clicked")
        defaults = self.load_default_settings()
        metadata_form = MetadataForm(
            self,
            self.class_id,
            {},  # No need to pass self.data
            self.theme,
            self.refresh_student_table,
            defaults,
            is_read_only=True
        )
        metadata_form.class_saved.connect(self.refresh_metadata)
        metadata_form.class_saved.connect(self.refresh_student_table)
        metadata_form.exec_()

    def resizeEvent(self, event):
        """Adjust the width and position of the scrollable table dynamically."""
        if hasattr(self, "frozen_table") and self.frozen_table.width() > 0:
            QTimer.singleShot(0, self.update_scrollable_table_position)  # Delay the update
        super().resizeEvent(event)  # Call the base class implementation

    def get_attendance_dates(self):
        """Get all unique attendance dates dynamically based on start_date, days, and max_classes."""
        if "dates" in self.metadata:
            return self.metadata["dates"]

        max_classes_str = self.metadata.get("max_classes", "10")
        max_classes = int(max_classes_str.split()[0])  # Extract the numeric part

        start_date_str = self.metadata.get("start_date", "")
        days_str = self.metadata.get("days", "")

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
    
    def select_row_in_both_tables(self, row):
        self._syncing_selection = True
        try:
            self.frozen_table.selectionModel().clearSelection()
            self.scrollable_table.selectionModel().clearSelection()
            if row is not None and row >= 0:
                self.frozen_table.selectRow(row)
                self.scrollable_table.selectRow(row)
        finally:
            self._syncing_selection = False

    def closeEvent(self, event):
        """Handle the close event to reopen the Launcher."""
        self.closed.emit()  # Emit the closed signal
        event.accept()  # Accept the close event

    def refresh_student_table(self):
        """Refresh the student table with updated data from the DB."""
        # --- PATCH: Reload students from DB ---
        self.students = {}
        for student_row in get_students_by_class(self.class_id):
            student_id = student_row["student_id"]
            attendance_records = get_attendance_by_student(student_id)
            attendance = {rec["date"]: rec["status"] for rec in attendance_records}
            student_row["attendance"] = attendance
            self.students[student_id] = student_row

        # Only include students who are active
        active_students = {sid: s for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"}

        # --- PATCH: Ensure attendance_dates is always valid ---
        attendance_dates = self.metadata.get("dates", [])
        if not attendance_dates:
            attendance_dates = self.get_attendance_dates()
            self.metadata["dates"] = attendance_dates

        # Initialize totals for all fields
        total_cia = 0
        total_cod = 0

        # Calculate CIA and COD totals by searching scrollable_data
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
        self.metadata["cod_cia"] = f"{total_cod} COD / {total_cia} CIA"

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
        class_time = int(self.metadata.get("class_time", "2"))  # Default to 2 if not provided
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
        # print("Frozen Data Dimensions:", len(frozen_data), len(frozen_headers))
        # for row in frozen_data:
          #  print("Row Length:", len(row))

        self.frozen_table.setModel(FrozenTableModel(frozen_data, frozen_headers))
        # Reconnect selection sync after setModel (Qt gotcha)
        # self.frozen_table.selectionModel().selectionChanged.connect(self.sync_selection_to_scrollable)

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
        # print("Scrollable Data Dimensions:", len(scrollable_data), len(scrollable_headers))
        # for row in scrollable_data:
          #  print("Row Length:", len(row))

        self.scrollable_table.setModel(TableModel(self.students, attendance_dates))
        # Reconnect selection sync after setModel (Qt gotcha)
        # self.scrollable_table.selectionModel().selectionChanged.connect(self.sync_selection_to_frozen)

        # Adjust column widths
        self.reset_column_widths()
        self.reset_scrollable_column_widths()

        # --- Scroll to today's date if present ---
        today_str = datetime.now().strftime("%d/%m/%Y")
        print("DEBUG: scrollable_headers =", scrollable_headers)
        print("DEBUG: today_str =", today_str)

        QTimer.singleShot(0, lambda: self.scroll_to_today(scrollable_headers, today_str))

        # print("Frozen Data:", frozen_data)
        # print("Scrollable Data:", scrollable_data)

        # Refresh the metadata section to include COD/CIA totals
        self.refresh_metadata()
        self.debug_table_positions("after refresh_student_table")

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
        student_form = StudentForm(self, self.class_id, {}, refresh_callback, student_id, student_data)

        # Center the form relative to the Mainform
        student_form.move(
            self.geometry().center().x() - student_form.width() // 2,
            self.geometry().center().y() - student_form.height() // 2
        )

        # Open the form as a modal dialog
        student_form.exec_()
        print("Calling refresh_student_table from edit_student")
        self.refresh_student_table()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            # Get the widget under the mouse
            widget = self.childAt(event.pos())
            # If not clicking inside either table, clear selection
            if widget not in (self.frozen_table, self.scrollable_table):
                self.frozen_table.selectionModel().clearSelection()
                self.scrollable_table.selectionModel().clearSelection()
                # Clear the current cell (removes dotted box)
                self.frozen_table.setCurrentIndex(QModelIndex())
                self.scrollable_table.setCurrentIndex(QModelIndex())
        return super().eventFilter(obj, event)

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
        print("Frozen Table column widths:", [self.frozen_table.columnWidth(col) for col in range(self.frozen_table.model().columnCount())])
        total_width = sum(self.frozen_table.columnWidth(col) for col in range(self.frozen_table.model().columnCount()))
        print("Calculated total frozen table width:", total_width)
        self.frozen_table.setFixedWidth(total_width)
        self.frozen_table_width = total_width  # Update the frozen table width
        self.update_scrollable_table_position()  # Ensure the scrollable table is updated

    def update_scrollable_table_position(self):
        """Update the position and width of the scrollable table."""
        # Get the right edge of the frozen table using geometry for accurate positioning
        frozen_table_right = self.frozen_table.geometry().right() + 1  # <-- Fix: add +1

        # Calculate the available width for the scrollable table
        available_width = self.width() - frozen_table_right

        # Ensure the scrollable table takes up the remaining space
        if (available_width > 0):
            self.scrollable_table.setFixedWidth(available_width)
        else:
            self.scrollable_table.setFixedWidth(0)  # Fallback to 0 if no space is available

        # Align the scrollable table to the right of the frozen table and match its y-coordinate
        self.scrollable_table.move(frozen_table_right, self.frozen_table.geometry().top())
        self.debug_table_positions("after update_scrollable_table_position")

    def load_default_settings(self):
        """Load default settings from the database."""
        return get_all_defaults()

    def refresh_metadata(self):
        """Refresh the metadata section with updated data from the DB."""
        print("Refreshing metadata...")  # Debugging: Method entry

        # --- PATCH: Reload class metadata from DB ---
        self.class_data = get_class_by_id(self.class_id)
        self.metadata = self.class_data  # All fields are now top-level

        # Clear the existing metadata layout
        metadata_widget = self.layout.itemAt(0).widget()
        metadata_layout = metadata_widget.layout()
        while metadata_layout.count():
            item = metadata_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild the metadata fields
        metadata_fields = [
            ("Company:", self.metadata.get("company", ""), "Course Hours:", 
             f"{self.metadata.get('course_hours', '')} / {self.metadata.get('class_time', '')} / {self.metadata.get('max_classes', '')}"),
            ("Room:", self.metadata.get("room", ""), "Start Date:", self.metadata.get("start_date", "")),
            ("Consultant:", self.metadata.get("consultant", ""), "Finish Date:", self.metadata.get("finish_date", "")),
            ("Teacher:", self.metadata.get("teacher", ""), "Days:", self.metadata.get("days", "")),
            ("CourseBook:", self.metadata.get("course_book", ""), "Time:", self.metadata.get("time", "")),
            ("Notes:", self.metadata.get("notes", ""), "COD/CIA:", self.metadata.get("cod_cia", "")),  # Combine Notes and COD/CIA
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
        print("Opening Calendar View...")  # Debugging: Method entry

        scheduled_dates = self.get_attendance_dates()
        print(f"Scheduled dates before calendar: {scheduled_dates}")  # Debugging: Check current dates

        max_classes = int(self.metadata.get("max_classes", "20").split()[0])
        students = self.students

        def on_save_callback(selected_dates):
            print(f"Selected dates from calendar: {selected_dates}")  # Debugging: Check selected dates
            self.metadata["dates"] = selected_dates
            self.metadata, self.students = update_dates(self.metadata, self.students)
            # --- PATCH: Save to DB if needed ---
            update_class(self.class_id, self.metadata)
            self.refresh_metadata()
            self.refresh_student_table()

        launch_calendar(self, scheduled_dates, students, max_classes, on_save_callback)

    def highlight_column(self, column_index):
        """Highlight the entire column when a header is clicked."""
        self.scrollable_table.selectionModel().clearSelection()
        model = self.scrollable_table.model()
        row_count = model.rowCount()
        top_left = model.index(0, column_index)
        bottom_right = model.index(row_count - 1, column_index)
        selection = QItemSelection(top_left, bottom_right)
        self.scrollable_table.selectionModel().select(selection, QItemSelectionModel.Select | QItemSelectionModel.Columns)

    def open_pal_cod_form(self, column_index=None):
        print("DEBUG: open_pal_cod_form called, column_index =", column_index)
        attendance_dates = self.metadata.get("dates", [])
        if not attendance_dates:
            attendance_dates = self.get_attendance_dates()
            self.metadata["dates"] = attendance_dates
        print(f"DEBUG: attendance_dates={attendance_dates}, column_index={column_index}, len={len(attendance_dates)}")
        if column_index < 0 or column_index >= len(attendance_dates):
            QMessageBox.warning(
                self,
                "Invalid Column",
                "Please select a valid date column header in the attendance table before using PAL/COD."
            )
            return

        attendance_dates = self.metadata.get("dates", [])

        # If called from header double-click, column_index is provided
        if column_index is not None:
            if column_index < 0 or column_index >= len(attendance_dates):
                QMessageBox.warning(
                    self,
                    "Invalid Column",
                    "Please select a valid date column header in the attendance table before using PAL/COD."
                )
                return
        else:
            # Called from button/menu, get selected column
            selected_columns = self.scrollable_table.selectionModel().selectedColumns()
            if not selected_columns:
                QMessageBox.warning(
                    self,
                    "No Column Selected",
                    "Please select a valid date column header in the attendance table before using PAL/COD."
                )
                return
            column_index = selected_columns[0].column()
            if column_index < 0 or column_index >= len(attendance_dates):
                QMessageBox.warning(
                    self,
                    "Invalid Column",
                    "Please select a valid date column header in the attendance table before using PAL/COD."
                )
                return

        print(f"DEBUG: column_index={column_index}, attendance_dates={attendance_dates}")
        date = re.sub(r'\s+', '', attendance_dates[column_index])
        print(f"DEBUG: selected date header for PAL/COD: {date!r}")

        if not (len(date) == 10 and date[2] == "/" and date[5] == "/" and date.replace("/", "").isdigit()):
            print("DEBUG: Not a real date, but allowing for placeholder columns.")
            # Remove or comment out the QMessageBox and return if you want to allow
            # QMessageBox.warning(
            #     self,
            #     "Invalid Date",
            #     "Cannot set P/A/L for this column. Please add real dates first before attempting to change attendance."
            # )
            # return

        # Open the PALCODForm with COD and CIA options, without student name
        pal_cod_form = PALCODForm(self, column_index, self.update_column_values, None, date, show_cod_cia=True, show_student_name=False)
        if pal_cod_form.exec_() == QDialog.Accepted:
            new_value = pal_cod_form.selected_value
            self.update_column_values(column_index, new_value)

    def update_column_values(self, column_index, value):
        """Update the selected column with the given value for all students."""
        attendance_dates = self.metadata.get("dates", [])

        # Validate the column index
        if (column_index < 0 or column_index >= len(attendance_dates)):
            QMessageBox.warning(self, "Invalid Column", "The selected column is out of range.")
            return

        date = attendance_dates[column_index]  # Get the corresponding date

        # Update the attendance value for all students (skip the "Running Total" row)
        for student in self.students.values():
            student["attendance"][date] = value
            set_attendance(self.class_id, student["student_id"], date, value)

        # --- Ensure there are always MaxClasses teaching dates (excluding CIA/HOL) ---
        max_classes = int(self.metadata.get("max_classes", "20").split()[0])

        def is_teaching_date(d):
            return not any(
                student.get("attendance", {}).get(d) in ["CIA", "HOL"]
                for student in self.students.values()
            )

        attendance_dates = self.metadata["dates"]  # Make sure to use the updated list
        teaching_dates = [d for d in attendance_dates if is_teaching_date(d)]

        # Add new dates if needed
        while len(teaching_dates) < max_classes:
            if attendance_dates:
                last_date = datetime.strptime(attendance_dates[-1], "%d/%m/%Y")
                days_str = self.metadata.get("days", "")
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
        self.metadata["dates"] = attendance_dates
        # Only update DB columns, not 'dates'
        db_metadata = {k: v for k, v in self.metadata.items() if k != "dates"}
        update_class(self.class_id, db_metadata)
        # If you want to update the dates table, do it here with your insert_date/update_dates logic
        self.refresh_student_table()

    def refresh_scrollable_table_column(self, column_index):
        """Refresh a specific column in the scrollable table."""
        model = self.scrollable_table.model()
        if not model:
            return
        row_count = model.rowCount()
        if row_count > 0:
            top_left = model.index(0, column_index)
            bottom_right = model.index(row_count - 1, column_index)
            model.dataChanged.emit(top_left, bottom_right)

    def refresh_scrollable_table(self):
        """Rebuild the scrollable table model to reflect updated data."""
        attendance_dates = self.metadata.get("dates", [])
        scrollable_headers = attendance_dates  # Only include date columns
        scrollable_data = []

        # Add "Running Total" row
        class_time = int(self.metadata.get("class_time", "2"))  # Default to 2 if not provided
        running_total = [class_time * (i + 1) for i in range(len(attendance_dates))]
        scrollable_data.append(running_total)  # Add the "Running Total" row as the first row

        # Add student attendance rows
        for student in self.students.values():
            attendance = student.get("attendance", {})
            row_data = [attendance.get(date, "-") for date in attendance_dates]
            scrollable_data.append(row_data)

        # Update the model
        self.scrollable_table.setModel(TableModel(self.students, attendance_dates))

        # Reset column widths
        self.reset_scrollable_column_widths()

    def edit_attendance_field(self, index):
        """Open a dialog to edit the selected attendance field."""
        row = index.row()
        column = index.column()
        print(f"[DEBUG] edit_attendance_field: row={row}, column={column}")

        attendance_dates = self.metadata.get("dates", [])
        if not attendance_dates:
            attendance_dates = self.get_attendance_dates()
            self.metadata["dates"] = attendance_dates
        print(f"[DEBUG] attendance_dates={attendance_dates}, len={len(attendance_dates)}")

        # Skip the "Running Total" row
        if row == 0:
            print("[DEBUG] Attempted to edit Running Total row")
            QMessageBox.warning(self, "Invalid Selection", "Cannot edit the 'Running Total' row.")
            return

        if column < 0 or column >= len(attendance_dates):
            print(f"[DEBUG] Invalid column: {column}, attendance_dates length: {len(attendance_dates)}")
            QMessageBox.warning(self, "Invalid Selection", "Please select a valid date column.")
            return

        date = attendance_dates[column]
        print(f"[DEBUG] Editing date: {date}")

        student_keys = list(self.students.keys())
        if (row - 1) < 0 or (row - 1) >= len(student_keys):
            print(f"[DEBUG] Invalid student row: {row-1}, student_keys: {student_keys}")
            QMessageBox.warning(self, "Invalid Selection", "Student row out of range.")
            return

        student_id = student_keys[row - 1]
        student_name = self.students[student_id].get("name", "Unknown")
        current_value = self.students[student_id]["attendance"].get(date, "-")
        print(f"[DEBUG] Editing student_id={student_id}, name={student_name}, current_value={current_value}")

        column_values = [self.students[sid]["attendance"].get(date, "-") for sid in self.students]
        print(f"[DEBUG] column_values for date {date}: {column_values}")

        if "CIA" in column_values or "COD" in column_values or "HOL" in column_values:
            print("[DEBUG] Edit blocked due to CIA/COD/HOL in column")
            QMessageBox.warning(
                self,
                "Edit Blocked",
                "Press header [date] to clear CIA, COD, or HOL before \nchanging any individual attendance data (P,A,L)....",
                QMessageBox.Cancel,
            )
            return

        dialog = PALCODForm(
            self,
            column,
            None,
            current_value,
            date,
            student_name,
            show_cod_cia=False,
            show_student_name=True,
            refresh_cell_callback=lambda r, c: print(f"[DEBUG] refresh_cell_callback called for row={r}, col={c}"),
            row=row
        )
        if dialog.exec_() == QDialog.Accepted:
            new_value = dialog.selected_value
            print(f"[DEBUG] Dialog accepted, new_value={new_value}")
            self.students[student_id]["attendance"][date] = new_value
            set_attendance(self.class_id, student_id, date, new_value)

            # No need to reload all attendance or refresh the whole table!
            model = self.scrollable_table.model()
            model.setData(model.index(row, column), new_value, Qt.EditRole)

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

    def debug_table_positions(self, context=""):
        print(f"\n--- DEBUG [{context}] ---")
        # print("Frozen Table geometry:", self.frozen_table.geometry())
        # print("Frozen Table pos:", self.frozen_table.pos())
        # print("Frozen Table width:", self.frozen_table.width())
        # print("Scrollable Table geometry:", self.scrollable_table.geometry())
        # print("Scrollable Table pos:", self.scrollable_table.pos())
        # print("Scrollable Table width:", self.scrollable_table.width())
        # print("Scrollable Table vertical scrollbar visible:", self.scrollable_table.verticalScrollBar().isVisible())
        # print("Scrollable Table horizontal scrollbar visible:", self.scrollable_table.horizontalScrollBar().isVisible())
        print("Scrollable table visible:", self.scrollable_table.isVisible())
        print("Scrollable table geometry:", self.scrollable_table.geometry())
        print("Scrollable table width:", self.scrollable_table.width())
        print("--- END DEBUG ---\n")

    def debug_frozen_selection(self, selected, deselected):
        print(f"[DEBUG] FROZEN selection changed: {[i.row() for i in self.frozen_table.selectionModel().selectedRows()]}")

    def debug_scrollable_selection(self, selected, deselected):
        print(f"[DEBUG] SCROLLABLE selection changed: {[i.row() for i in self.scrollable_table.selectionModel().selectedRows()]}")

    def scroll_to_today(self, scrollable_headers, today_str):
        today_index = None
        for i, date_str in enumerate(scrollable_headers):
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                today_obj = datetime.strptime(today_str, "%d/%m/%Y")
                if date_obj >= today_obj:
                    today_index = i
                    break
            except Exception:
                continue

        if today_index is not None:
            print(f"Auto-scroll to column: {today_index} (Centering today)")
            self.scrollable_table.scrollTo(
                self.scrollable_table.model().index(0, today_index),
                QTableView.PositionAtCenter
            )
        else:
            last_col = len(scrollable_headers) - 1
            print(f"Auto-scroll to column: {last_col} (End of table)")
            self.scrollable_table.scrollTo(
                self.scrollable_table.model().index(0, last_col),
                QTableView.PositionAtCenter
            )

    def get_default_attendance_for_new_student(self):
        """Return a dict of {date: value} for a new student, matching CIA/COD/HOL if all others have it."""
        attendance_dates = self.metadata.get("dates", [])
        special_values = {"CIA", "COD", "HOL"}
        attendance = {}
        for date in attendance_dates:
            values = [student.get("attendance", {}).get(date, "-") for student in self.students.values()]
            unique_specials = set(v for v in values if v in special_values)
            # If all students have the same special value (and no other values), use it
            if len(values) > 0 and len(unique_specials) == 1 and all(v in unique_specials or v == "-" for v in values):
                attendance[date] = unique_specials.pop()
            else:
                attendance[date] = "-"
        return attendance

    def open_show_hide(self):
        from ui.show_hide_form import ShowHideForm
        dlg = ShowHideForm(self, self.class_id, self.refresh_student_table)
        dlg.exec_()


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


class FrozenTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self.data_matrix = data  # List of lists
        self.headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self.data_matrix)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self.data_matrix[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return value
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


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
