from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel,
    QHBoxLayout, QFrame, QGridLayout, QPushButton, QMessageBox, QStyledItemDelegate, QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QColor, QFont
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from ui.metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime, timedelta
import PyQt5.sip  # Import PyQt5.sip to bridge PyQt5 and Tkinter
from .archive_manager import ArchiveManager
import subprocess  # Import subprocess to run external scripts
import sys
import re
import time  # Import time for profiling
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
    get_form_settings,
    get_message_defaults,
)

from logic.display import center_widget, scale_and_center, apply_window_flags

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def show_message_dialog(parent, message, timeout=2000):
    msg_defaults = get_message_defaults()
    bg = msg_defaults.get("message_bg_color", "#2980f0")
    fg = msg_defaults.get("message_fg_color", "#fff")
    border = msg_defaults.get("message_border_color", "#1565c0")
    border_width = msg_defaults.get("message_border_width", "3")
    border_radius = msg_defaults.get("message_border_radius", "12")
    padding = msg_defaults.get("message_padding", "18px 32px")
    font_size = msg_defaults.get("message_font_size", "13")
    font_bold = msg_defaults.get("message_font_bold", "true")
    font_weight = "bold" if str(font_bold).lower() in ("1", "true", "yes") else "normal"
    style = f"background: {bg}; color: {fg}; border: {border_width}px solid {border}; padding: {padding}; font-size: {font_size}pt; font-weight: {font_weight}; border-radius: {border_radius}px;"
    from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
    from PyQt5.QtCore import Qt
    msg_dialog = QDialog(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
    msg_dialog.setModal(False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(message)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    msg_dialog.adjustSize()
    parent_geo = parent.geometry() if parent else None
    if parent_geo:
        msg_dialog.move(parent.mapToGlobal(parent_geo.center()) - msg_dialog.rect().center())
    msg_dialog.show()
    QTimer.singleShot(timeout, msg_dialog.accept)

SHOW_HIDE_FIELDS = [
    ("show_nickname", "Nickname"),
    ("show_company_no", "Company No"),
    ("show_score", "Score"),
    ("show_pre_test", "Pre-test"),
    ("show_post_test", "Post-test"),
    ("show_attn", "Attn"),
    ("show_p", "P"),
    ("show_a", "A"),
    ("show_l", "L"),
]

class TableModel(QAbstractTableModel):
    def __init__(self, students, attendance_dates, class_time=2, mainform=None, parent=None):
        super().__init__(parent)
        self.students = students  # dict of student_id: student_data
        self.attendance_dates = attendance_dates
        self.student_keys = list(students.keys())
        self.class_time = class_time
        self.mainform = mainform

        # PATCH: Running total skips columns with CIA or HOL
        self.running_total = []
        cumulative_total = 0
        for date in self.attendance_dates:
            # If any student has CIA or HOL for this date, skip counting this class
            has_cia_hol = any(
                self.students[student_id]["attendance"].get(date) in ["CIA", "HOL"]
                for student_id in self.student_keys
            )
            if has_cia_hol:
                self.running_total.append("-")
            else:
                cumulative_total += self.class_time
                self.running_total.append(cumulative_total)

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
            if role == Qt.DisplayRole:
                return self.running_total[col]
            return None
        student_id = self.student_keys[row - 1]
        date = self.attendance_dates[col]
        value = self.students[student_id]["attendance"].get(date, "-")
        if role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole:
            mainform = self.mainform
            if mainform and hasattr(mainform, "metadata"):
                color_map = {
                    "P": mainform.metadata.get("bgcolor_p", "#c8e6c9"),
                    "COD": mainform.metadata.get("bgcolor_cod", "#c8e6c9"),
                    "A": mainform.metadata.get("bgcolor_a", "#ffcdd2"),
                    "CIA": mainform.metadata.get("bgcolor_cia", "#ffcdd2"),
                    "HOL": mainform.metadata.get("bgcolor_hol", "#ffcdd2"),
                    "L": mainform.metadata.get("bgcolor_l", "#fff9c4"),
                }
                color = color_map.get(value, "")
                if isinstance(color, str) and color.startswith("#") and len(color) in (4, 7):
                    return QColor(color)
                else:
                    return None
            return None
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
        option.displayAlignment = Qt.AlignCenter
        option.palette.setColor(option.palette.Text, Qt.black)  # Normal text
        option.palette.setColor(option.palette.HighlightedText, Qt.black)  # Selected text
        # Do NOT set option.backgroundBrush here; let the model's BackgroundRole handle all coloring


class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.palette.setColor(option.palette.Text, Qt.black)
        option.palette.setColor(option.palette.HighlightedText, Qt.black)
        option.displayAlignment = Qt.AlignCenter


class FrozenTableDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Center all columns except 'Name' and 'Note', which are left-aligned
        model = index.model()
        if hasattr(model, 'headers') and index.column() < len(model.headers):
            header = model.headers[index.column()]
            if header in ("Name", "Note"):
                option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
            else:
                option.displayAlignment = Qt.AlignCenter
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


class FrozenTableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self._data = data  # List of lists (rows)
        self.headers = headers  # List of column headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            try:
                return self._data[row][col]
            except IndexError:
                return ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            try:
                return self.headers[section]
            except IndexError:
                return ""
        return None


class Mainform(QMainWindow):
    closed = pyqtSignal()  # Signal to notify when the Mainform is closed

    def __init__(self, class_id, data, theme):
        super().__init__()
        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("Mainform") or {}        
        # self.setWindowTitle(f"Class Information - {class_id}")
        win_w = form_settings.get("window_width")
        # Remove duplicate super().__init__() call below (should only be called once at the top)

        win_h = form_settings.get("window_height")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.resize(800, 600)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        else:
            self.setMinimumSize(300, 200)
        # REMOVED: max_width and max_height logic

        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # --- PATCH: Set company name in window title from data or class metadata ---
        company = data.get("company")
        if not company and "classes" in data and class_id in data["classes"]:
            company = data["classes"][class_id].get("company")
        self.setWindowTitle(f"Bluecard Attendance - {class_id} - {company or 'Unknown Company'}")
        # --- FONT SIZE PATCH: Set default font size from per-form or global settings ---
        from logic.db_interface import get_all_defaults
        self.default_settings = get_all_defaults()
        font_size = int(form_settings.get("font_size") or self.default_settings.get("form_font_size", self.default_settings.get("button_font_size", 12)))
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont(form_settings.get("font_family", "Segoe UI"), font_size))
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            display_settings = get_all_defaults()
            scale = str(display_settings.get("scale_windows", "1")) == "1"
            center = str(display_settings.get("center_windows", "1")) == "1"
            width_ratio = float(display_settings.get("window_width_ratio", 0.6))
            height_ratio = float(display_settings.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        self.class_id = class_id
        self.theme = theme
        # --- PATCH: Load from DB ---
        self.class_data = get_class_by_id(self.class_id)
        show_dates_db = self.class_data.get("show_dates", "Yes")
        print(f"[DATES DEBUG INIT] show_dates from DB: {show_dates_db}")
        print(f"[DATES DEBUG INIT] Will show scrollable table: {show_dates_db == 'Yes'}")
        # --- PATCH: Update FROZEN_COLUMN_WIDTHS from DB if present ---
        width_map = {
            "#": "width_row_number",
            "Name": "width_name",
            "Note": "width_note",
            "Nickname": "width_nickname",
            "Company No": "width_company_no",
            "Score": "width_score",
            "Pre-test": "width_pre_test",
            "Post-test": "width_post_test",
            "Attn": "width_attn",
            "P": "width_p",
            "A": "width_a",
            "L": "width_l",
        }
        for col, db_key in width_map.items():
            db_val = self.class_data.get(db_key)
            if db_val is not None:
                try:
                    self.FROZEN_COLUMN_WIDTHS[col] = int(db_val)
                except (ValueError, TypeError):
                    pass

        self.students = {}
        for student_row in get_students_by_class(self.class_id):
            student_id = student_row["student_id"]
            attendance_records = get_attendance_by_student(student_id)
            attendance = {rec["date"]: rec["status"] for rec in attendance_records}
            student_row["attendance"] = attendance
            self.students[student_id] = student_row
        self.metadata = self.class_data  # All fields are now top-level

        # --- PATCH: Get metadata font size from settings ---
        self.metadata_font_size = int(self.default_settings.get("metadata_font_size", 12))
        self.metadata_font = QFont("Segoe UI", self.metadata_font_size)

        # Ensure self.metadata["dates"] is set
        if "dates" not in self.metadata or not self.metadata["dates"]:
            # Generate dates if missing
            max_classes_str = self.metadata.get("max_classes", "10")
            max_classes = parse_max_classes(max_classes_str)
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
                dates = ["--/--/--" for _ in range(max_classes)]
            self.metadata["dates"] = dates

        # --- PATCH: Load per-class show/hide state from DB, fallback to defaults ---
        self.default_settings = self.load_default_settings()
        self.column_visibility = {
            "Nickname": (self.class_data.get("show_nickname") or self.default_settings.get("show_nickname", "Yes")) == "Yes",
            "Company No": (self.class_data.get("show_company_no") or self.default_settings.get("show_company_no", "Yes")) == "Yes",
            "Score": (self.class_data.get("show_score") or self.default_settings.get("show_score", "Yes")) == "Yes",
            "Pre-test": (self.class_data.get("show_pre_test") or self.default_settings.get("show_pre_test", "Yes")) == "Yes",
            "Post-test": (self.class_data.get("show_post_test") or self.default_settings.get("show_post_test", "Yes")) == "Yes",
            "Attn": (self.class_data.get("show_attn") or self.default_settings.get("show_attn", "Yes")) == "Yes",
            "P": (self.class_data.get("show_p") or self.default_settings.get("show_p", "Yes")) == "Yes",
            "A": (self.class_data.get("show_a") or self.default_settings.get("show_a", "Yes")) == "Yes",
            "L": (self.class_data.get("show_l") or self.default_settings.get("show_l", "Yes")) == "Yes",
            "Note": (self.class_data.get("show_note") or self.default_settings.get("show_note", "Yes")) == "Yes",
        }
        self.scrollable_column_visibility = {
            "Dates": (self.class_data.get("show_dates") or self.default_settings.get("show_dates", "Yes")) == "Yes"
        }

        self.frozen_table_width = 0
        self._syncing_selection = False  # <-- Add this line
        self.init_ui()

        self.installEventFilter(self)  # <-- Add this line

        # --- FONT SIZE PATCH: Add zoom in/out shortcuts ---
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)  # For some keyboards
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.reset_zoom)

        # --- Apply display preferences ---
        from logic.db_interface import get_all_defaults
        display_settings = get_all_defaults()
        from logic.display import center_widget, scale_and_center, apply_window_flags
        scale = str(display_settings.get("scale_windows", "1")) == "1"
        center = str(display_settings.get("center_windows", "1")) == "1"
        width_ratio = float(display_settings.get("window_width_ratio", 0.6))
        height_ratio = float(display_settings.get("window_height_ratio", 0.6))
        if scale:
            scale_and_center(self, width_ratio, height_ratio)
        elif center:
            center_widget(self)
        # Optionally, apply_window_flags(self, show_minimize=True, show_maximize=True)

    def zoom_in(self):
        self.font_size = min(self.font_size + 1, 32)
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont("Segoe UI", self.font_size))

    def zoom_out(self):
        self.font_size = max(self.font_size - 1, 8)
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont("Segoe UI", self.font_size))

    def reset_zoom(self):
        self.font_size = int(self.default_settings.get("font_size", 12))
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont("Segoe UI", self.font_size))

    def reset_scrollable_column_widths(self):
        """Reset the column widths of the scrollable table to their default or DB values, and prevent stretching."""
        # Use width_date from DB if present, else fallback to 50
        width = 50
        if self.class_data.get("width_date"):
            try:
                width = int(self.class_data["width_date"])
            except Exception:
                width = 50
        for col in range(self.scrollable_table.model().columnCount()):
            self.scrollable_table.setColumnWidth(col, width)
            # Prevent stretching: always set to Interactive
            self.scrollable_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Interactive)

    def init_ui(self):
        """Initialize the UI components."""
        # Main container widget
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(5, 5, 5, 0)

        # Metadata Section (updated)
        metadata_widget = QWidget()  # Create a widget to contain the metadata layout
        metadata_layout = QGridLayout(metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        # metadata_layout.setHorizontalSpacing(10)  # Reduce horizontal spacing
        metadata_layout.setVerticalSpacing(0)  # Reduce vertical spacing
        from PyQt5.QtWidgets import QSizePolicy
        from PyQt5.QtGui import QFontMetrics

        # Define metadata_fields before using it
        metadata_fields = [
            ("Company:", self.metadata.get("company", ""), "Course Hours:", f"{self.metadata.get('course_hours', '')} / {self.metadata.get('class_time', '')} / {self.metadata.get('max_classes', '')}"),
            ("Room:", self.metadata.get("room", ""), "Start Date:", self.metadata.get("start_date", "")),
            ("Consultant:", self.metadata.get("consultant", ""), "Finish Date:", self.metadata.get("finish_date", "")),
            ("Teacher:", self.metadata.get("teacher", ""), "Days:", self.metadata.get("days", "")),
            ("CourseBook:", self.metadata.get("course_book", ""), "Time:", self.metadata.get("time", "")),
            ("Notes:", self.metadata.get("notes", ""), "COD/CIA/HOL:", self.metadata.get("cod_cia", "")),
        ]

        # --- Calculate dynamic min widths for metadata labels and values ---
        # Collect all label1, label2, value1, value2
        label1_list = [label1 for (label1, _, _, _) in metadata_fields]
        label2_list = [label2 for (_, _, label2, _) in metadata_fields if label2]
        value1_list = [value1 for (_, value1, _, _) in metadata_fields]
        value2_list = [value2 for (_, _, _, value2) in metadata_fields if value2]

        metrics = QFontMetrics(self.metadata_font)
        label1_min = max([metrics.width(text) for text in label1_list]) + 26  # +padding
        label2_min = max([metrics.width(text) for text in label2_list]) + 26 if label2_list else label1_min
        value1_min = max(200, max([metrics.width(str(text)) for text in value1_list]) + 34)  # min 300px
        value2_min = max(200, max([metrics.width(str(text)) for text in value2_list]) + 34) if value2_list else value1_min

        # Set fixed width for metadata widget based on calculated min widths
        metadata_widget.setFixedWidth(label1_min + value1_min + label2_min + value2_min + 24)
        metadata_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # --- Metadata Section - Add metadata fields ---
        for row, (label1, value1, label2, value2) in enumerate(metadata_fields):
            # Label 1
            label1_widget = QLabel(label1)
            label1_widget.setStyleSheet("font-weight: bold; text-align: left; border: none; padding-left: 5px; padding-right: 5px;")
            label1_widget.setMinimumWidth(label1_min)
            label1_widget.setFont(self.metadata_font)
            label1_widget.setFixedHeight(metrics.height() + 4)
            metadata_layout.addWidget(label1_widget, row, 0)
            # Value 1 (always show border, even if blank)
            v1 = value1 if value1.strip() else " "
            value1_widget = QLabel(v1)
            value1_widget.setStyleSheet("text-align: left; border: 1px solid gray; padding-left: 5px; padding-right: 5px;")
            value1_widget.setMinimumWidth(value1_min)
            value1_widget.setFont(self.metadata_font)
            value1_widget.setFixedHeight(metrics.height() + 4)
            metadata_layout.addWidget(value1_widget, row, 1)
            if label2:
                label2_widget = QLabel(label2)
                label2_widget.setStyleSheet("font-weight: bold; text-align: left; border: none; padding-left: 5px; padding-right: 5px;")
                label2_widget.setMinimumWidth(label2_min)
                label2_widget.setFont(self.metadata_font)
                label2_widget.setFixedHeight(metrics.height() + 4)
                metadata_layout.addWidget(label2_widget, row, 2)
            # Value 2 (always show border, even if blank)
            v2 = value2 if value2.strip() else " "
            value2_widget = QLabel(v2)
            value2_widget.setStyleSheet("text-align: left; border: 1px solid gray; padding-left: 5px; padding-right: 5px;")
            value2_widget.setMinimumWidth(value2_min)
            value2_widget.setFont(self.metadata_font)
            value2_widget.setFixedHeight(metrics.height() + 4)
            metadata_layout.addWidget(value2_widget, row, 3)
        # Add the metadata widget to the main layout
        self.layout.addWidget(metadata_widget)

        # Add a 5px vertical spacer below metadata before buttons
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        self.layout.addItem(QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Buttons Section
        buttons_layout = QHBoxLayout()
        self.add_edit_student_btn = QPushButton("Add/Edit Student")
        self.remove_student_btn = QPushButton("Manage/Remove Students")
        self.pal_cod_btn = QPushButton("PAL/COD")
        self.html_button = QPushButton("Run HTML Output")
        self.metadata_form_btn = QPushButton("Manage Metadata")
        self.manage_dates_btn = QPushButton("Manage Dates")  # Placeholder button
        self.show_hide_btn = QPushButton("Show/Hide")
        # Only connect if method exists
        if hasattr(self, 'open_show_hide'):
            self.show_hide_btn.clicked.connect(self.open_show_hide)
        # Connect buttons to their respective methods
        self.add_edit_student_btn.clicked.connect(self.add_edit_student)
        self.remove_student_btn.clicked.connect(self.remove_student)
        self.pal_cod_btn.clicked.connect(lambda: self.debug_pal_cod_button_click())
        self.html_button.clicked.connect(self.run_html_output)
        self.metadata_form_btn.clicked.connect(self.open_metadata_form)
        self.manage_dates_btn.clicked.connect(self.open_calendar_view)
        # Add buttons to the layout
        self._mainform_buttons = [
            self.add_edit_student_btn, self.remove_student_btn, self.pal_cod_btn,
            self.html_button, self.metadata_form_btn, self.manage_dates_btn, self.show_hide_btn
        ]
        for button in self._mainform_buttons:
            buttons_layout.addWidget(button)
        self.layout.addLayout(buttons_layout)

        # Add a 5px vertical spacer below buttons before table
        # from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        self.layout.addItem(QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))


        # Table Section (manual overlay for perfect join)
        # Create both tables before referencing them
        self.frozen_table = QTableView()
        self.scrollable_table = QTableView()
        # Set minimum section size for both tables to allow very narrow columns
        self.frozen_table.horizontalHeader().setMinimumSectionSize(10)
        self.scrollable_table.horizontalHeader().setMinimumSectionSize(10)
        self.frozen_table.verticalHeader().setVisible(False)
        self.scrollable_table.verticalHeader().setVisible(False)

        # Only create the container and set parents after both tables are created
        self.table_container = QWidget()
        self.table_container.setContentsMargins(0, 0, 0, 0)
        self.table_container.setStyleSheet("background: transparent;")
        self.table_container.setMinimumHeight(300)  # Adjust as needed

        self.frozen_table.setParent(self.table_container)
        self.scrollable_table.setParent(self.table_container)

        def position_tables():
            frozen_width = self.frozen_table.width()
            height = self.table_container.height()
            self.frozen_table.setGeometry(0, 0, frozen_width, height)
            # Move scrollable_table left by 1px for a perfect join
            self.scrollable_table.setGeometry(frozen_width - 1, 0, self.table_container.width() - frozen_width + 1, height)
            # Debug output for geometry
            print("[DEBUG] table_container:", self.table_container.geometry())
            print("[DEBUG] frozen_table:", self.frozen_table.geometry())
            print("[DEBUG] scrollable_table:", self.scrollable_table.geometry())
        
        # Remove debug borders for production
        # self.frozen_table.setStyleSheet(self.frozen_table.styleSheet() + "QTableView { border: 2px solid red !important; }")
        # self.scrollable_table.setStyleSheet(self.scrollable_table.styleSheet() + "QTableView { border: 2px solid blue !important; }")
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.position_tables)

        self.layout.addWidget(self.table_container)

        # Remove frame and padding from both tables to eliminate gaps
        # Make frozen_table 1px wider for a perfect join
        self.frozen_table.setFrameStyle(QFrame.NoFrame)
        self.scrollable_table.setFrameStyle(QFrame.NoFrame)
        self.frozen_table.setStyleSheet("QTableView { border: none; border-top: none; border-bottom: none; border-left: none; margin: 0px; padding: 0px; }")
        self.scrollable_table.setStyleSheet("QTableView { border: none; border-top: none; border-bottom: none; border-right: none; border-left: none; margin: 0px; padding: 0px; }")
        # Make frozen_table 1px wider
        self.frozen_table.resize(self.frozen_table.width() + 1, self.frozen_table.height())
        # Remove the vertical line (border-left) under the scrollable table
        self.scrollable_table.setStyleSheet(self.scrollable_table.styleSheet() + " QTableView::item { border-left: none; }")
        # Ensure the table_layout has no spacing or margins
        # self.table_layout.setSpacing(0)
        # self.table_layout.setContentsMargins(0, 0, 0, 0)

        # Add tables to the layout
        # self.table_layout.addWidget(self.frozen_table)
        # self.table_layout.addWidget(self.scrollable_table)
        # Now set header and corner button styles (after both tables exist)
        self.frozen_table.horizontalHeader().setStyleSheet("font-weight: bold; border: none;")
        self.scrollable_table.horizontalHeader().setStyleSheet("border: none;")
        corner_style = "QTableCornerButton::section { background: transparent; border: none; }"
        self.frozen_table.setStyleSheet(self.frozen_table.styleSheet() + corner_style)
        self.scrollable_table.setStyleSheet(self.scrollable_table.styleSheet() + corner_style)

        # Connect double-click signal to edit_student method
        self.frozen_table.doubleClicked.connect(self.edit_student)

        # Connect the double-click event of the header to the `header_double_click` method
        header = self.scrollable_table.horizontalHeader()
        header.sectionDoubleClicked.connect(self.header_double_click)
        print("[DEBUG] Connected header double-click event to header_double_click method.")

        self.frozen_table.horizontalHeader().sectionResized.connect(self.adjust_frozen_table_width)
        self.frozen_table.horizontalHeader().sectionResized.connect(self.on_frozen_header_resized)
        self.scrollable_table.horizontalHeader().sectionResized.connect(self.on_scrollable_header_resized)

        # Set size policies and stretch factors for proper alignment
        from PyQt5.QtWidgets import QSizePolicy
        self.frozen_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.scrollable_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.table_layout.setStretch(0, 0)  # Frozen table: fixed
        # self.table_layout.setStretch(1, 1)  # Scrollable table: expands

        # Add the table_layout to the main layout
        # self.layout.addLayout(self.table_layout)
        # print("[DEBUG] Added table_layout to main layout.")
        # print(f"[DEBUG] layout count: {self.layout.count()}")
        # print(f"[DEBUG] container children: {[child.objectName() for child in self.findChildren(QWidget)]}")

        # Remove any setFixedWidth and move calls for both tables (handled by layout)
        # Remove adjust_frozen_table_width and update_scrollable_table_position logic that sets widths/moves
        # Remove setFixedWidth for frozen_table
        # Remove setFixedWidth for scrollable_table (if any)
        # ...existing code...
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

        # self.frozen_table.selectionModel().selectionChanged.connect(self.debug_frozen_selection)
        # self.scrollable_table.selectionModel().selectionChanged.connect(self.debug_scrollable_selection)

        # Force a style update and geometry refresh to ensure the left border is visible on startup
        self.frozen_table.setStyleSheet(
            self.frozen_table.styleSheet() +
            "QTableView { border-left: none; } "
            "QTableView::item { border-left: 1px solid #000; } "
            "QHeaderView::section { border-left: 1px solid #000 !important; }"
        )
        self.frozen_table.viewport().update()
        self.frozen_table.horizontalHeader().repaint()
        self.frozen_table.repaint()
        # Also trigger a geometry/layout update for the table container
        self.table_container.updateGeometry()
        self.table_container.repaint()
        QTimer.singleShot(0, lambda: self.frozen_table.updateGeometry())
        QTimer.singleShot(0, lambda: self.frozen_table.viewport().update())
        QTimer.singleShot(0, lambda: self.frozen_table.horizontalHeader().repaint())

    def on_frozen_header_resized(self, logicalIndex, oldSize, newSize):
        """Live-sync: Save frozen/scrollable column width to DB and update ShowHideForm if open. Also realign tables."""
        try:
            model = self.frozen_table.model()
            if not hasattr(model, 'headers'):
                return
            header = model.headers[logicalIndex]
            width_db_map = {
                "#": "width_row_number",
                "Name": "width_name",
                "Nickname": "width_nickname",
                "Company No": "width_company_no",
                "Score": "width_score",
                "Pre-test": "width_pre_test",
                "Post-test": "width_post_test",
                "Attn": "width_attn",
                "P": "width_p",
                "A": "width_a",
                "L": "width_l",
                "Note": "width_note",
            }
            db_key = width_db_map.get(header)
            if db_key:
                from logic.db_interface import update_class, get_class_by_id
                update_class(self.class_id, {db_key: newSize})
                self.class_data = get_class_by_id(self.class_id)
                from PyQt5.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, "width_edits") and db_key in widget.width_edits:
                        widget.width_edits[db_key].blockSignals(True)
                        widget.width_edits[db_key].setText(str(newSize))
                        widget.width_edits[db_key].blockSignals(False)
        except Exception as e:
            print(f"[ERROR] on_frozen_header_resized: {e}")
        # --- Ensure robust alignment after any width change ---
        self.adjust_frozen_table_width()
        self.position_tables()

    def on_scrollable_header_resized(self, logicalIndex, oldSize, newSize):
        """Live-sync: Save scrollable (dates) column width to DB and update ShowHideForm if open."""
        try:
            # All date columns use width_date
            db_key = "width_date"
            from logic.db_interface import update_class, get_class_by_id
            update_class(self.class_id, {db_key: newSize})
            self.class_data = get_class_by_id(self.class_id)
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, "width_edits") and db_key in widget.width_edits:
                    widget.width_edits[db_key].blockSignals(True)
                    widget.width_edits[db_key].setText(str(newSize))
                    widget.width_edits[db_key].blockSignals(False)
        except Exception as e:
            print(f"[ERROR] on_scrollable_header_resized: {e}")

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
        # Only include active students for row mapping
        active_students = [sid for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"]
        if adjusted_row < 0:
            print("Add Student button clicked")
            def refresh_callback():
                print("Refreshing student table after adding a student...")
                self.refresh_student_table()
                self.frozen_table.selectionModel().clearSelection()  # Clear selection after adding
            default_attendance = self.get_default_attendance_for_new_student()
            student_form = StudentForm(self, self.class_id, {}, refresh_callback, default_attendance=default_attendance)
            student_form.exec_()
            if getattr(student_form, "bulk_import_requested", False):
                student_form.open_bulk_import_dialog()
        else:
            print("Edit Student button clicked")
            try:
                student_id = active_students[adjusted_row]
                student_data = self.students[student_id]
                def refresh_callback():
                    print("Refreshing student table after editing a student...")
                    self.refresh_student_table()
                    self.frozen_table.selectionModel().clearSelection()  # Clear selection after editing
                student_form = StudentForm(self, self.class_id, {}, refresh_callback, student_id, student_data)
                student_form.exec_()
                if getattr(student_form, "bulk_import_requested", False):
                    student_form.open_bulk_import_dialog()
            except IndexError:
                show_message_dialog(self, "Invalid row selected. Please try again.")

    def remove_student(self):
        """Handle removing or managing students."""
        if not self.frozen_table.selectionModel().hasSelection():
            print("No student selected. Opening Student Manager...")
            student_manager = StudentManager(self, {}, self.class_id, self.refresh_student_table)
            student_manager.exec_()
            return
        selected_row = self.frozen_table.currentIndex().row()
        adjusted_row = selected_row - 1
        # Only include active students for row mapping
        active_students = [sid for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"]
        if adjusted_row < 0:
            show_message_dialog(self, "Cannot remove the 'Running Total' row.")
            return
        try:
            student_id = active_students[adjusted_row]
            student_data = self.students[student_id]
        except IndexError:
            show_message_dialog(self, "Invalid row selected. Please try again.")
            return
        # Floating Yes/No dialog for confirmation
        def confirm_remove():
            self.students[student_id]["active"] = "No"
            # Remove attendance before DB update
            update_data = dict(self.students[student_id])
            update_data.pop("attendance", None)
            update_student(student_id, update_data)
            self.refresh_student_table()
        def cancel_remove():
            self.frozen_table.selectionModel().clearSelection()
        dialog = QDialog(self, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        label = QLabel(f"Are you sure you want to mark the student '{student_data['name']}' as inactive?")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        btn_row = QHBoxLayout()
        btn_yes = QPushButton("Yes")
        btn_no = QPushButton("No")
        btn_yes.clicked.connect(lambda: (dialog.accept(), confirm_remove()))
        btn_no.clicked.connect(lambda: (dialog.reject(), cancel_remove()))
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dialog.adjustSize()
        dialog.move(self.mapToGlobal(self.geometry().center()) - dialog.rect().center())
        dialog.exec_()

    def open_metadata_form(self):
        """Open the Metadata Form."""
        print("Manage Metadata button clicked")
        defaults = self.load_default_settings()
        metadata_form = MetadataForm(
            self,
            self.class_id,
            {"classes": {self.class_id: {"metadata": self.metadata, "students": self.students}}},
            self.theme,
            self.refresh_student_table,
            defaults,
            is_read_only=True
        )
        # metadata_form.class_saved.connect(self.refresh_metadata)
        def deferred_refresh():
            QTimer.singleShot(0, self.refresh_student_table)

        metadata_form.class_saved.connect(deferred_refresh)
        metadata_form.exec_()

    def showEvent(self, event):
        super().showEvent(event)
        print(f"[DEBUG] Mainform shown: width={self.width()}, height={self.height()}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        print(f"[DEBUG] Mainform resized: width={self.width()}, height={self.height()}")

    def resizeEvent(self, event):
        """Adjust the width and position of the scrollable table dynamically."""
        if hasattr(self, "frozen_table") and self.frozen_table.width() > 0:
            QTimer.singleShot(0, self.update_scrollable_table_position)  # Delay the update
        super().resizeEvent(event)  # Call the base class implementation

    def get_attendance_dates(self):
        """Get all unique attendance dates dynamically based on start_date, days, and max_classes, always returning max_classes dates."""
        if "dates" in self.metadata:
            attendance_dates = list(self.metadata["dates"])
        else:
            attendance_dates = []

        # --- PATCH: Remove dates marked as CIA/HOL/COD in date_status ---
        date_status = self.metadata.get("date_status", {})
        attendance_dates = [d for d in attendance_dates if date_status.get(d, "") not in ("CIA", "HOL", "COD")]

        max_classes_str = self.metadata.get("max_classes", "10")
        try:
            max_classes = int(str(max_classes_str).split()[0])
        except Exception:
            max_classes = 10
        start_date_str = self.metadata.get("start_date", "")
        days_str = self.metadata.get("days", "")

        # Parse StartDate
        try:
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
        except ValueError:
            start_date = None

        # Parse Days into weekday indices (0=Monday, 1=Tuesday, ..., 6=Sunday)
        weekdays = []
        if days_str:
            day_map = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            weekdays = [day_map[day.strip()] for day in days_str.split(",") if day.strip() in day_map]

        # Remove placeholders and duplicates
        print("[DEBUG] Original attendance_dates before patch:", attendance_dates)
        attendance_dates = [d for d in attendance_dates if d != "--/--/--"]
        attendance_dates = list(dict.fromkeys(attendance_dates))

        # Remove all CIA/HOL/COD dates from attendance_dates before generating new ones (already done above)
        def is_real_class_date(date_str):
            for student in self.students.values():
                att = student.get("attendance", {})
                if att.get(date_str, "-") in ["CIA", "HOL", "COD"]:
                    return False
            return True
        # attendance_dates = [d for d in attendance_dates if is_real_class_date(d)]
        print("[DEBUG] attendance_dates after removing CIA/HOL/COD:", attendance_dates)
        print(f"[DEBUG] max_classes: {max_classes}, weekdays: {weekdays}, start_date: {start_date}")
        if attendance_dates:
            print(f"[DEBUG] last_date for extension: {attendance_dates[-1]}")
        else:
            print("[DEBUG] No real class dates, using start_date for extension.")

        # Now generate new dates if needed
        if len(attendance_dates) < max_classes:
            if attendance_dates:
                last_date = datetime.strptime(attendance_dates[-1], "%d/%m/%Y")
            else:
                last_date = start_date

            new_dates = []
            current_date = last_date + timedelta(days=1) if last_date else datetime.now()
            while len(attendance_dates) + len(new_dates) < max_classes and weekdays and current_date:
                if current_date.weekday() in weekdays:
                    new_date_str = current_date.strftime("%d/%m/%Y")
                    # Don't add if already in attendance_dates or marked as CIA/HOL/COD
                    if new_date_str not in attendance_dates and date_status.get(new_date_str, "") not in ("CIA", "HOL", "COD"):
                        new_dates.append(new_date_str)
                current_date += timedelta(days=1)
            print("[DEBUG] new_dates generated:", new_dates)
            attendance_dates += new_dates
        if len(attendance_dates) < max_classes:
            print(f"[DEBUG] Adding {max_classes - len(attendance_dates)} placeholders.")
            attendance_dates += ["--/--/--"] * (max_classes - len(attendance_dates))
        print("[DEBUG] Final attendance_dates returned:", attendance_dates)
        return attendance_dates
    

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
        # Focused debug for 'Dates' column and scrollable table visibility
        self.class_data = get_class_by_id(self.class_id)
        self.metadata = self.class_data
        show_dates_db = self.class_data.get("show_dates", "Yes")
        self.column_visibility = {
            "Nickname": (self.class_data.get("show_nickname") or self.default_settings.get("show_nickname", "Yes")) == "Yes",
            "Company No": (self.class_data.get("show_company_no") or self.default_settings.get("show_company_no", "Yes")) == "Yes",
            "Score": (self.class_data.get("show_score") or self.default_settings.get("show_score", "Yes")) == "Yes",
            "Pre-test": (self.class_data.get("show_pre_test") or self.default_settings.get("show_pre_test", "Yes")) == "Yes",
            "Post-test": (self.class_data.get("show_post_test") or self.default_settings.get("show_post_test", "Yes")) == "Yes",
            "Attn": (self.class_data.get("show_attn") or self.default_settings.get("show_attn", "Yes")) == "Yes",
            "P": (self.class_data.get("show_p") or self.default_settings.get("show_p", "Yes")) == "Yes",
            "A": (self.class_data.get("show_a") or self.default_settings.get("show_a", "Yes")) == "Yes",
            "L": (self.class_data.get("show_l") or self.default_settings.get("show_l", "Yes")) == "Yes",
            "Note": (self.class_data.get("show_note") or self.default_settings.get("show_note", "Yes")) == "Yes",
        }
        self.scrollable_column_visibility = {
            "Dates": (show_dates_db or self.default_settings.get("show_dates", "Yes")) == "Yes"
        }
        print(f"[DATES DEBUG] show_dates from DB: {show_dates_db}")
        print(f"[DATES DEBUG] scrollable_column_visibility['Dates']: {self.scrollable_column_visibility['Dates']}")
        # ...existing code for rebuilding tables...
        # Build attendance_dates and set model
        attendance_dates = self.get_attendance_dates()  # <-- Use robust method
        print(f"[DATES DEBUG] attendance_dates used for model: {attendance_dates}")
        active_students = {sid: s for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"}
        self.scrollable_table.setModel(TableModel(active_students, attendance_dates, mainform=self))
        self.scrollable_table.setItemDelegate(AttendanceDelegate(self.scrollable_table))  # Always set delegate after model
        print(f"[UI DEBUG] scrollable_table columnCount: {self.scrollable_table.model().columnCount() if self.scrollable_table.model() else 'No model'}")
        # Hide scrollable table if Dates is off or no columns
        if not self.scrollable_column_visibility["Dates"] or self.scrollable_table.model().columnCount() == 0:
            print("[DATES DEBUG] Hiding scrollable table (attendance dates table)")
            self.scrollable_table.hide()
        else:
            print("[DATES DEBUG] Showing scrollable table (attendance dates table)")
            self.scrollable_table.show()
        # Force layout update after show/hide
        self.scrollable_table.parentWidget().update()
        self.scrollable_table.parentWidget().adjustSize()
        self.scrollable_table.updateGeometry()
        self.scrollable_table.repaint()
        self.scrollable_table.update()
        print(f"[UI DEBUG] scrollable_table.isVisible(): {self.scrollable_table.isVisible()}")
        # ...rest of method unchanged...

        self.ensure_max_teaching_dates()
        t1 = time.time()
        # print(f"[PROFILE] ensure_max_teaching_dates: {t1 - start:.3f}s")

        self.students = {}
        for student_row in get_students_by_class(self.class_id):
            student_id = student_row["student_id"]
            attendance_records = get_attendance_by_student(student_id)
            attendance = {rec["date"]: rec["status"] for rec in attendance_records}
            student_row["attendance"] = attendance
            self.students[student_id] = student_row
        t2 = time.time()
        # print(f"[PROFILE] Reload students/attendance: {t2 - t1:.3f}s")

        # Only include students who are active
        active_students = {sid: s for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"}

        # --- PATCH: Always reload metadata from DB before using dates ---
        self.class_data = get_class_by_id(self.class_id)
        self.metadata = self.class_data
        # --- PATCH: Ensure metadata['dates'] is always set after DB reload ---
        from logic.db_interface import get_dates_by_class
        self.metadata["dates"] = get_dates_by_class(self.class_id)

        self.refresh_metadata()  # Only call once here!

        # Rebuild the frozen table data
        frozen_headers = ["#", "Name"]
        if self.column_visibility.get("Nickname", True):
            frozen_headers.append("Nickname")
        if self.column_visibility.get("Company No", True):
            frozen_headers.append("Company No")
        if self.column_visibility.get("Score", True):
            frozen_headers.append("Score")
        if self.column_visibility.get("Pre-test", True):
            frozen_headers.append("Pre-test")
        if self.column_visibility.get("Post-test", True):
            frozen_headers.append("Post-test")
        if self.column_visibility.get("Attn", True):
            frozen_headers.append("Attn")
        if self.column_visibility.get("P", True):
            frozen_headers.append("P")
        if self.column_visibility.get("A", True):
            frozen_headers.append("A")
        if self.column_visibility.get("L", True):
            frozen_headers.append("L")
        if self.column_visibility.get("Note", True):
            frozen_headers.append("Note")
        self.frozen_headers = frozen_headers  # <-- Assign to self
        frozen_data = []
        # Add "Running Total" row
        running_total_row = []
        for header in self.frozen_headers:
            if header == "#":
                running_total_row.append("")
            elif header == "Name":
                running_total_row.append("Running Total")
            else:
                running_total_row.append("-")
        frozen_data.append(running_total_row)
        # --- Use DB-driven attendance_dates for all attendance columns ---
        attendance_dates = self.metadata.get("dates", [])
        # Add student rows
        for idx, student in enumerate(active_students.values()):
            row = []
            for header in self.frozen_headers:
                if header == "#":
                    row.append(idx + 1)
                elif header == "Name":
                    row.append(student.get("name", ""))
                elif header == "Nickname":
                    row.append(student.get("nickname", ""))
                elif header == "Company No":
                    row.append(student.get("company_no", ""))
                elif header == "Score":
                    row.append(student.get("score", ""))
                elif header == "Pre-test":
                    row.append(student.get("pre_test", ""))
                elif header == "Post-test":
                    row.append(student.get("post_test", ""))
                elif header == "Attn":
                    row.append(len(student.get("attendance", {})))
                elif header == "P":
                    row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "P"))
                elif header == "A":
                    row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "A"))
                elif header == "L":
                    row.append(sum(1 for date in attendance_dates if student.get("attendance", {}).get(date) == "L"))
                elif header == "Note":
                    row.append(student.get("note", ""))  # Handle Note column
                else:
                    row.append("")
            frozen_data.append(row)
        self.frozen_table.setModel(FrozenTableModel(frozen_data, frozen_headers))
        self.frozen_table.setItemDelegate(FrozenTableDelegate(self.frozen_table))
        t3 = time.time()
        # print(f"[PROFILE] Set frozen table model: {t3 - t2:.3f}s")
        # print(f"[DEBUG] After setModel: frozen_table visible: {self.frozen_table.isVisible()}, geometry: {self.frozen_table.geometry()}")

        self.scrollable_table.setModel(TableModel(active_students, attendance_dates, mainform=self))
        self.scrollable_table.setItemDelegate(AttendanceDelegate(self.scrollable_table))
        self.scrollable_table.show()
        self.scrollable_table.viewport().update()  # Force repaint after setting the model
        t4 = time.time()
        # print(f"[PROFILE] Set scrollable table model: {t4 - t3:.3f}s")
        # print(f"[DEBUG] After setModel: scrollable_table visible: {self.scrollable_table.isVisible()}, geometry: {self.scrollable_table.geometry()}")

        self.reset_column_widths()
        self.reset_scrollable_column_widths()
        t5 = time.time()
        # print(f"[PROFILE] Reset column widths: {t5 - t4:.3f}s")

        scrollable_headers = attendance_dates
        today_str = datetime.now().strftime("%d/%m/%Y")
        QTimer.singleShot(0, lambda: self.scroll_to_today(scrollable_headers, today_str))
        t6 = time.time()
        # print(f"[PROFILE] Scroll to today: {t6 - t5:.3f}s")

        t7 = time.time()
        # print(f"[PROFILE] Refresh metadata: {t7 - t6:.3f}s")

        # self.debug_table_positions("after refresh_student_table")
        # print(f"[PROFILE] TOTAL refresh_student_table: {t7 - start:.3f}s")

    def edit_student(self, index):
        """Open the StudentForm in Edit mode for the selected student."""
        selected_row = index.row()
        if selected_row == 0:
            show_message_dialog(self, "Cannot edit the 'Running Total' row.")
            return
        adjusted_row = selected_row - 1  # Subtract 1 to skip the "Running Total" row
        # Only include active students for row mapping
        active_students = [sid for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"]
        try:
            student_id = active_students[adjusted_row]
            student_data = self.students[student_id]
        except IndexError:
            show_message_dialog(self, "Invalid row selected. Please try again.")
            return
        def refresh_callback():
            print("Callback triggered: Refreshing student table...")
            self.refresh_student_table()
        student_form = StudentForm(self, self.class_id, {}, refresh_callback, student_id, student_data)
        student_form.move(
            self.geometry().center().x() - student_form.width() // 2,
            self.geometry().center().y() - student_form.height() // 2
        )
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

    # Add a variable to track the last clicked header section index
    last_clicked_header_index = None

    FROZEN_COLUMN_WIDTHS = {
        "#": 30, # mapped to db width_row_number = 30
        "Name": 150, # mapped to db width_name = 150
        "Note": 200,  # mapped to db width_note = 150
        "Nickname": 100, # mapped to db width_nickname = 100
        "Company No": 100, # mapped to db width_company_no = 100
        "Score": 65, # mapped to db to width_score = 65
        "Pre-test": 65, # mapped to db to width_pre_test = 65
        "Post-test": 65, # mapped to db to width_post_test = 65
        "Attn": 50, # mapped to db to width_attn = 50
        "P": 30, # mapped to db to width_p = 30
        "A": 30, # mapped to db to width_a = 30
        "L": 30, # mapped to db to width_l = 30
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

    def position_tables(self):
        """Position frozen and scrollable tables so scrollable always sticks to the right of frozen."""
        frozen_width = self.frozen_table.width()
        height = self.table_container.height()
        self.frozen_table.setGeometry(0, 0, frozen_width, height)
        # Move scrollable_table left by 1px for a perfect join
        self.scrollable_table.setGeometry(frozen_width - 1, 0, self.table_container.width() - frozen_width + 1, height)

    def adjust_frozen_table_width(self):
        # Calculate the width of the frozen table as the sum of visible columns
        total_width = 0
        for col, header in enumerate(self.frozen_headers):
            if self.column_visibility.get(header, True):
                total_width += self.frozen_table.columnWidth(col)
        self.frozen_table.setFixedWidth(total_width + self.frozen_table.verticalHeader().width() + 2)
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozen_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.frozen_table.updateGeometry()

    def update_scrollable_table_position(self):
        """Update the position and width of the scrollable table (DISABLED: handled by layout)."""
        pass

    def load_default_settings(self):
        """Load default settings from the database."""
        return get_all_defaults()

    def refresh_metadata(self):
        """Refresh the metadata section with updated data from the DB."""
        # This should update the metadata display if needed
        pass

    def track_header_click(self, section_index):
        """Track the last clicked header section index."""
        print(f"[DEBUG] Header clicked section index: {section_index}")
        self.last_clicked_header_index = section_index

    def open_pal_cod_form(self, column_index=None):
        """Open the PALCODForm to update attendance."""
        from .pal_cod_form import PALCODForm, show_message_dialog
        import re
        print(f"[DEBUG] open_pal_cod_form: self.metadata = {self.metadata}")  # Print full metadata for debugging
        attendance_dates = self.metadata.get("dates", [])
        # --- CRITICAL: Only use DB-driven attendance_dates, never fallback/generate here ---
        if not attendance_dates:
            show_message_dialog(self, "No attendance dates available. Please check your class schedule.")
            print("[DEBUG] No dates in metadata. Aborting PALCODForm.")
            return
        if column_index is None:
            print("[DEBUG] open_pal_cod_form called with column_index=None")
            return
        if column_index < 0 or column_index >= len(attendance_dates):
            print(f"[DEBUG] Invalid column_index: {column_index} for attendance_dates length {len(attendance_dates)}")
            return
        # Header index N always maps to attendance_dates[N]
        date = attendance_dates[column_index]
        print(f"[DEBUG] open_pal_cod_form: column_index={column_index}, date='{date}'")
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", date):
            print(f"[DEBUG] Skipping PALCODForm: date '{date}' does not match dd/MM/yyyy")
            return
        pal_cod_form = PALCODForm(
            self,
            column_index,
            self.update_column_values,
            None,
            date,
            show_cod_cia=True,
            show_student_name=False
        )
        if pal_cod_form.exec_() == QDialog.Accepted:
            pass

    def header_double_click(self, section_index):
        """Handle double-click on a header to open PALCODForm."""
        print(f"[DEBUG] Double-clicked header section index: {section_index}")
        self.open_pal_cod_form(section_index)

    def edit_attendance_field(self, index):
        """Edit the attendance field for the selected cell (cell workflow)."""
        from .pal_cod_form import PALCODForm, show_message_dialog
        row = index.row()
        col = index.column()
        # Row 0 is running total, not editable
        if row == 0:
            return
        attendance_dates = self.metadata.get("dates", [])
        if not attendance_dates:
            attendance_dates = self.get_attendance_dates()
        if col < 0 or col >= len(attendance_dates):
            show_message_dialog(self, "Invalid date column selected.")
            return
        date = attendance_dates[col]
        # Only include active students for row mapping
        active_students = [sid for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"]
        student_index = row - 1
        if student_index < 0 or student_index >= len(active_students):
            show_message_dialog(self, "Invalid student row selected.")
            return
        student_id = active_students[student_index]
        student_data = self.students[student_id]
        student_name = student_data.get("name", "")
        # PALCODForm: cell workflow (single student/date)
        pal_cod_form = PALCODForm(
            self,
            col,  # column_index
            None,  # update_column_callback (not used for single cell)
            student_data["attendance"].get(date, "-"),  # current_value
            date,
            student_name=student_name,
            show_cod_cia=True,
            show_student_name=True,
            refresh_cell_callback=None,
            row=row
        )
        if hasattr(pal_cod_form, '_blocked') and pal_cod_form._blocked:
            return
        if pal_cod_form.exec_() == QDialog.Accepted:
            new_value = pal_cod_form.selected_value
            # Update the student's attendance for this date
            self.students[student_id]["attendance"][date] = new_value
            # Save to DB
            from logic.db_interface import set_attendance
            set_attendance(self.class_id, student_id, date, new_value)
            self.refresh_student_table()

    def highlight_column(self, column_index):
        """Highlight the entire column when a header is clicked. (Stub)"""
        # You can implement column highlighting logic here if needed
        pass

    def ensure_max_teaching_dates(self):
        """Ensure the number of teaching dates matches max_classes. (Stub)"""
        # Implement logic if needed, or leave as a stub for now
        pass

    def scroll_to_today(self, headers, today_str):
        """Scroll the table to today's date column. (Stub)"""
        pass

    def open_show_hide(self):
        """Open the Show/Hide columns dialog and update the frozen and scrollable tables accordingly."""
        # Prevent multiple instances
        if hasattr(self, 'show_hide_form') and self.show_hide_form is not None and self.show_hide_form.isVisible():
            self.show_hide_form.raise_()
            self.show_hide_form.activateWindow()
            return
        try:
            from ui.show_hide_form import ShowHideForm
        except ImportError:
            return
        columns = [col for col in self.FROZEN_COLUMN_WIDTHS.keys() if col not in ("#", "Name")]
        current = {col: self.column_visibility.get(col, True) for col in columns}
        # --- PATCH: Pass a live update callback to ShowHideForm ---
        def on_show_hide_saved(live_update=False):
            self.refresh_student_table()
        self.show_hide_form = ShowHideForm(self, self.class_id, on_save_callback=on_show_hide_saved)
        # Disable only mainform buttons while dialog is open
        for btn in getattr(self, '_mainform_buttons', []):
            btn.setEnabled(False)
        self.show_hide_form.finished.connect(lambda _: self._on_show_hide_closed())
        self.show_hide_form.show()

        # Overlap scrollable_table over frozen_table by setting a negative left margin
        self.scrollable_table.setStyleSheet(
            self.scrollable_table.styleSheet() +
            "QTableView { margin-left: 20px; }"
        )

        # Add back the left border only for the actual table rows (not header)
        corner_style = "QTableCornerButton::section { background: transparent; border: none; }"
        highlight_style = """
QTableView::item:selected {
    background: #b3d7ff;  /* Light blue highlight */
}
"""
        self.scrollable_table.setStyleSheet(
            "QTableView { border: none; border-top: none; border-bottom: none; border-right: none; border-left: none; margin: 0px; padding: 0px; }"
            + corner_style + highlight_style
        )

        # Only add a left border to the frozen table header and rows (not the whole table)
        self.frozen_table.setStyleSheet(
            self.frozen_table.styleSheet() +
            "QTableView { border-left: none; } "
            "QTableView::item { border-left: 1px solid #000; } "
            "QHeaderView::section { border-left: 1px solid #000 !important; }"
        )
        self.frozen_table.viewport().update()
        self.frozen_table.horizontalHeader().repaint()
        self.frozen_table.repaint()
        # Also trigger a geometry/layout update for the table container
        self.table_container.updateGeometry()
        self.table_container.repaint()
        QTimer.singleShot(0, lambda: self.frozen_table.updateGeometry())
        QTimer.singleShot(0, lambda: self.frozen_table.viewport().update())
        QTimer.singleShot(0, lambda: self.frozen_table.horizontalHeader().repaint())

        # Show or hide the scrollable table based on show_dates value
        # (REMOVED: self.scrollable_table.setVisible(show_dates == "Yes"))
        # Let refresh_student_table handle visibility logic

    def _on_show_hide_closed(self):
        # Re-enable only mainform buttons when dialog is closed
        for btn in getattr(self, '_mainform_buttons', []):
            btn.setEnabled(True)
        self.show_hide_form = None

    def get_default_attendance_for_new_student(self):
        """Return a default attendance dictionary for a new student, with all dates set to '-'."""
        # Use self.metadata to get the list of attendance dates
        attendance_dates = []
        if hasattr(self, 'metadata') and self.metadata:
            attendance_dates = self.metadata.get('dates', [])
        # If not available, fallback to get_attendance_dates()
        if not attendance_dates and hasattr(self, 'get_attendance_dates'):
            attendance_dates = self.get_attendance_dates()
        # Return a dict with all dates set to '-'
        return {date: '-' for date in attendance_dates}

    def open_calendar_view(self):
        """Open the calendar dialog for managing class dates."""
        from .calendar import launch_calendar
        scheduled_dates = self.metadata.get("dates", [])
        students = self.students
        # PATCH: Robustly parse max_classes as int, even if string is like '20 x 2 = 40.0'
        max_classes_raw = self.metadata.get("max_classes", 10)
        try:
            if isinstance(max_classes_raw, int):
                max_classes = max_classes_raw
            else:
                max_classes = int(str(max_classes_raw).split()[0])
        except Exception:
            max_classes = 10
        def on_save_callback(new_dates):
            # Save the new dates to metadata and refresh UI as needed
            self.metadata["dates"] = new_dates
            # Optionally, refresh the table or UI here
            self.refresh_table() if hasattr(self, "refresh_table") else None
        launch_calendar(self, scheduled_dates, students, max_classes, on_save_callback)

    def update_column_values(self, column_index, new_value):
        print(f"[DEBUG] update_column_values called: column_index={column_index}, new_value={new_value}")
        attendance_dates = self.metadata.get("dates", [])
        if not attendance_dates:
            attendance_dates = self.get_attendance_dates()
        if column_index < 0 or column_index >= len(attendance_dates):
            show_message_dialog(self, "Invalid column index.")
            return

        date = attendance_dates[column_index]
        active_students = [sid for sid, s in self.students.items() if s.get("active", "Yes") == "Yes"]
        for student_id in active_students:
            self.students[student_id]["attendance"][date] = new_value
            # Save to DB
            from logic.db_interface import set_attendance, insert_date
            set_attendance(self.class_id, student_id, date, new_value)

        # --- PATCH: Mark date as CIA/HOL/COD in the dates table if needed ---
        if new_value in ("CIA", "HOL", "COD"):
            # Save to DB (dates table) and in-memory metadata if needed
            try:
                insert_date(self.class_id, date, new_value)
            except Exception as e:
                print(f"[DEBUG] Failed to insert date status for {date}: {e}")
            # Optionally, keep a parallel structure in metadata
            if "date_status" not in self.metadata:
                self.metadata["date_status"] = {}
            self.metadata["date_status"][date] = new_value
        else:
            # If clearing CIA/HOL/COD, remove from date_status
            if "date_status" in self.metadata and date in self.metadata["date_status"]:
                del self.metadata["date_status"][date]

        self.refresh_student_table()

    def debug_pal_cod_button_click(self):
        print("[DEBUG] PAL/COD button clicked.")
        # Retrieve the selected column index from the table
        selected_columns = self.scrollable_table.selectionModel().selectedColumns()
        if not selected_columns:

            print("[DEBUG] No column selected, defaulting to column index 0.")
            column_index = 0
        else:
            column_index = selected_columns[0].column()
           

            print(f"[DEBUG] Selected column index: {column_index}")
        self.open_pal_cod_form(column_index=column_index)

def parse_max_classes(val, default=10):
    """Safely extract the leading integer from max_classes, even if it's a display string."""
    try:
        if isinstance(val, int):
            return val
        return int(str(val).split()[0])
    except Exception:
        return default

