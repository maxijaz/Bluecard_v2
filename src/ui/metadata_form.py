import json
import os
from datetime import datetime  # Import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QWidget, QFormLayout, QMessageBox, QCheckBox, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from logic.parser import save_data
from .calendar import CalendarView  # Import CalendarView
from logic.update_dates import update_dates, add_date, remove_date, modify_date  # Import the new functions
from datetime import datetime, timedelta
from ui.calendar import launch_calendar  # Import the shared function
from logic.date_utils import warn_if_start_date_not_in_days
from logic.db_interface import insert_class, update_class, get_all_defaults, get_class_by_id, get_form_settings, get_teacher_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

class MetadataForm(QDialog):
    class_saved = pyqtSignal(str)  # Signal to notify when a class is saved

    def __init__(self, parent, class_id, data, theme, on_metadata_save, defaults=None, is_read_only=False, single_date_mode=False):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.on_metadata_save = on_metadata_save
        self.is_edit = class_id is not None
        self.is_read_only = is_read_only
        self.single_date_mode = single_date_mode

        self.defaults = defaults or {}
        self.cod_cia_hol_default = self.defaults.get("def_cod_cia_hol", "0 COD 0 CIA 0 HOL")

        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("MetadataForm") or {}
        win_w = form_settings.get("window_width")
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
        # --- FONT SIZE PATCH: Set default font size from per-form or global settings ---
        default_settings = get_all_defaults()
        font_size = int(form_settings.get("font_size") or default_settings.get("form_font_size", default_settings.get("button_font_size", 12)))
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        self.form_font = QFont(form_settings.get("font_family", "Segoe UI"), font_size)
        QApplication.instance().setFont(self.form_font)
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
        # --- PATCH END ---

        # --- PATCH: Load teacher defaults for new class creation ---
        self.teacher_defaults = get_teacher_defaults() if not self.is_edit else {}
        # Fallbacks for course_hours, class_time, max_classes
        self.fallback_course_hours = 40
        self.fallback_class_time = 2
        self.fallback_max_classes = 20

        # Main layout
        layout = QVBoxLayout(self)

        # Add heading and info text to match StylesheetForm
        heading = QLabel("Add New Class")
        heading.setObjectName("formTitle")
        heading.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(heading)
        heading_sep = QWidget()
        heading_sep.setFixedHeight(4)
        heading_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        layout.addWidget(heading_sep)
        info_label = QLabel("Text blah blah blah\nblah blah blah")
        info_label.setStyleSheet("font-size: 9.5pt; color: #444444;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        info_sep = QWidget()
        info_sep.setFixedHeight(4)
        info_sep.setStyleSheet("background-color: #444444; border-radius: 2px;")
        layout.addWidget(info_sep)
        layout.addSpacing(12)

        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setHorizontalSpacing(24)
        grid_layout.setVerticalSpacing(10)

        # --- Data entry fields ---
        self.fields = {}
        metadata = self.data["classes"][self.class_id]["metadata"] if self.is_edit else {}
        field_defs = [
            ("Class No: *", "class_no"),
            ("Company: *", "company"),
            ("Room:", "room"),
            ("Course Book:", "course_book"),
            ("Course Hours:", "course_hours"),
            ("Time:", "time"),
            ("Start Date:", "start_date"),
            ("Finish Date:", "finish_date"),
            ("Notes:", "notes"),
            ("Consultant:", "consultant"),
            ("Teacher:", "teacher"),
            ("Teacher No:", "teacher_no"),
            ("Rate:", "rate"),
            ("CCP:", "ccp"),
            ("Travel:", "travel"),
            ("Bonus:", "bonus"),
            ("Class Time:", "class_time"),
            ("Max Classes:", "max_classes"),
        ]
        # Place fields in 2 columns, 9 rows, in the order given (lines 77-94)
        num_fields = len(field_defs)
        num_rows = (num_fields + 1) // 2
        for idx, (label, key) in enumerate(field_defs):
            # --- PATCH: Use teacher_defaults for new class, fallback for course_hours/class_time/max_classes ---
            if self.is_edit:
                value = metadata.get(key, "")
            else:
                if key == "course_hours":
                    value = self.teacher_defaults.get("def_coursehours", str(self.fallback_course_hours))
                elif key == "class_time":
                    value = self.teacher_defaults.get("def_classtime", str(self.fallback_class_time))
                elif key == "max_classes":
                    value = str(self.fallback_max_classes)
                else:
                    # For other fields, use teacher_defaults if present, else blank
                    value = self.teacher_defaults.get(f"def_{key}", "")
            field = QLineEdit(value)
            field.setFont(self.form_font)
            self.fields[key] = field
            # --- PATCH: Assign special fields to instance variables ---
            if key == "course_hours":
                self.class_hours_input = field
            elif key == "class_time":
                self.class_time_input = field
            elif key == "max_classes":
                self.max_classes_input = field
            row = idx % num_rows
            col = idx // num_rows
            grid_layout.addWidget(QLabel(label), row, col * 2)
            grid_layout.addWidget(field, row, col * 2 + 1)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        # --- Tickboxes (Days) at bottom ---
        bottom_row = QHBoxLayout()
        # Days toggle buttons
        self.days_label = QLabel("Days:")
        self.days_label.setFont(self.form_font)
        self.days_buttons = {}
        days_layout = QHBoxLayout()
        day_map = [
            ("Mon", "Monday"), ("Tue", "Tuesday"), ("Wed", "Wednesday"),
            ("Thu", "Thursday"), ("Fri", "Friday"), ("Sat", "Saturday"), ("Sun", "Sunday")
        ]
        # --- PATCH: Load toggle button style defaults from DB ---
        toggle_defaults = get_all_defaults()
        toggle_bg = toggle_defaults.get("toggle_bg_color", "#ffffff")
        toggle_fg = toggle_defaults.get("toggle_fg_color", "#1565c0")
        toggle_border = toggle_defaults.get("toggle_border_color", "#1565c0")
        toggle_border_width = int(toggle_defaults.get("toggle_border_width", 3))
        toggle_border_radius = int(toggle_defaults.get("toggle_border_radius", 12))
        toggle_padding = toggle_defaults.get("toggle_padding", "5px 10px")
        toggle_font_size = int(toggle_defaults.get("toggle_font_size", 12))
        toggle_font_bold = str(toggle_defaults.get("toggle_font_bold", "true")).lower() == "true"
        toggle_hover_bg = toggle_defaults.get("toggle_hover_bg_color", "#e0f0ff")
        toggle_pressed_bg = toggle_defaults.get("toggle_pressed_bg_color", "#c0e0ff")
        toggle_checked_bg = toggle_defaults.get("toggle_checked_bg_color", "#2980f0")
        toggle_checked_fg = toggle_defaults.get("toggle_checked_fg_color", "#ffffff")
        font_weight = "bold" if toggle_font_bold else "normal"
        toggle_stylesheet = f"""
            QPushButton {{
                border-radius: {toggle_border_radius}px;
                padding: {toggle_padding};
                background: {toggle_bg};
                color: {toggle_fg};
                border: {toggle_border_width}px solid {toggle_border};
                font-size: {toggle_font_size}pt;
                font-weight: {font_weight};
            }}
            QPushButton:checked {{
                background: {toggle_checked_bg};
                color: {toggle_checked_fg};
                border: {toggle_border_width + 1}px solid {toggle_border};
            }}
            QPushButton:hover {{
                background: {toggle_hover_bg};
            }}
            QPushButton:pressed {{
                background: {toggle_pressed_bg};
            }}
        """
        for short, full in day_map:
            btn = QPushButton(short)
            btn.setCheckable(True)
            btn.setFont(self.form_font)
            btn.setMinimumWidth(44)
            btn.setMaximumWidth(80)
            btn.setFixedWidth(64)  # Fixed width of Mon, Tue, Wed etc. for consistency
            btn.setStyleSheet(toggle_stylesheet)
            self.days_buttons[full] = btn
            days_layout.addWidget(btn)
        # Prepopulate toggles if editing
        if self.is_edit:
            selected_days = metadata.get("days", "").split(", ")
            for day in selected_days:
                if day in self.days_buttons:
                    self.days_buttons[day].setChecked(True)
        days_widget = QWidget()
        days_widget.setLayout(days_layout)
        bottom_row.addWidget(self.days_label)
        bottom_row.addWidget(days_widget)
        # Add a stretch to push toggle to the right
        bottom_row.addStretch()
        # Add a styled frame for bottom row
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.StyledPanel)
        bottom_frame.setLayout(bottom_row)
        layout.addWidget(bottom_frame)
        # --- Buttons ---
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setFont(self.form_font)
        save_button.clicked.connect(self.save_metadata)
        button_layout.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(self.form_font)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect signals for live max_classes update
        self.fields["course_hours"].textChanged.connect(self.update_max_classes)
        self.fields["class_time"].textChanged.connect(self.update_max_classes)
        self.fields["start_date"].editingFinished.connect(self.validate_start_date)
        # Initialize MaxClasses
        self.update_max_classes()

    def update_max_classes(self):
        """Recalculate Max Classes based on Course Hours and Class Time. Always fallback to safe defaults. Add note if remainder exists."""
        try:
            course_hours = float(self.fields["course_hours"].text())
        except Exception:
            course_hours = 40.0
        try:
            class_time = float(self.fields["class_time"].text())
        except Exception:
            class_time = 2.0
        if class_time <= 0:
            class_time = 2.0
        max_classes = int(course_hours // class_time)
        remainder = course_hours - (max_classes * class_time)
        if max_classes <= 0:
            max_classes = 20
        if remainder > 0:
            self.fields["max_classes"].setText(f"{max_classes} classes ({remainder:g} hour remains)")
        else:
            self.fields["max_classes"].setText(f"{max_classes} classes")

    def save_metadata(self):
        """Save metadata for the class."""

        # --- Warn if start date does not match selected days ---
        if not self.warn_if_start_date_not_in_days():
            return

        class_no = self.fields["class_no"].text().strip().upper()
        if not class_no:
            QMessageBox.warning(self, "Validation Error", "Class No is required.")
            return

        # --- PATCH: Check for duplicate class_no in the database ---
        if not self.is_edit:
            if get_class_by_id(class_no):
                QMessageBox.warning(
                    self,
                    "Duplicate Class ID",
                    f"Class ID '{class_no}' already exists in the database.\n"
                    "Please enter a different Class ID."
                )
                self.fields["class_no"].setFocus()
                self.fields["class_no"].selectAll()
                return

        # Gather metadata from fields and ensure all keys are lowercase
        metadata = {key: field.text().strip() for key, field in self.fields.items()}

        # --- Block save if Start Date is invalid ---
        start_date = metadata.get("start_date", "")
        if not start_date:
            QMessageBox.warning(
                self,
                "Missing Start Date",
                "Start Date is required. Please enter a valid date or click [Pick] to select from the calendar."
            )
            self.fields["start_date"].setFocus()
            return
        try:
            datetime.strptime(start_date, "%d/%m/%Y")
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Start Date",
                "Start Date must be in DD/MM/YYYY format and be a real date.\n"
                "Please enter a valid date or click [Pick] to select from the calendar."
            )
            self.fields["start_date"].setFocus()
            self.fields["start_date"].selectAll()
            return

        # --- Apply formatting rules ---
        metadata["class_no"] = class_no  # Always uppercase

        # Company: Capitalize first letter of each word, but preserve existing uppercase letters
        def smart_title(s):
            return " ".join(
                w if (len(w) > 1 and w.isupper()) else w[:1].upper() + w[1:]
                for w in s.split()
            )
        company = metadata.get("company", "")
        metadata["company"] = smart_title(company)

        metadata["course_hours"] = self.class_hours_input.text()
        metadata["class_time"] = self.class_time_input.text()
        metadata["max_classes"] = self.max_classes_input.text()

        # Combine selected days into a comma-separated string (from toggled buttons)
        selected_days = [day for day, btn in self.days_buttons.items() if btn.isChecked()]
        metadata["days"] = ", ".join(selected_days)

        # --- PATCH: Set default COD/CIA/HOL for new class ---
        if not self.is_edit:
            metadata["cod_cia"] = self.cod_cia_hol_default

        # --- PROTECT EXISTING DATES AND ATTENDANCE ---
        students = self.data["classes"][self.class_id].get("students", {}) if self.is_edit else {}

        old_dates = []
        if self.is_edit:
            old_dates = self.data["classes"][self.class_id]["metadata"].get("dates", [])
        else:
            old_dates = []

        try:
            max_classes = int(metadata["max_classes"].split()[0])
        except Exception:
            max_classes = 20

        start_date_str = metadata.get("start_date", "")
        days_str = metadata.get("days", "")

        def is_real_date(d):
            return len(d) == 10 and d[2] == "/" and d[5] == "/"

        protected_dates = set()
        for student in students.values():
            attendance = student.get("attendance", {})
            for date, value in attendance.items():
                if value in ["P", "A", "L", "CIA", "COD", "HOL"] and is_real_date(date):
                    protected_dates.add(date)

        protected_dates = sorted(protected_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))

        generated_dates = generate_dates(start_date_str, days_str, max_classes * 2)
        generated_dates = [d for d in generated_dates if d not in protected_dates]
        final_dates = sorted(
            list(protected_dates) + generated_dates[:max_classes - len(protected_dates)],
            key=lambda d: datetime.strptime(d, "%d/%m/%Y") if is_real_date(d) else datetime(9999, 12, 31)
        )

        num_dates = len(final_dates)
        if num_dates < max_classes:
            placeholders = [f"Date{i+1}" for i in range(num_dates, max_classes)]
            final_dates += placeholders
        elif num_dates > max_classes:
            final_dates = final_dates[:max_classes]

        metadata["dates"] = final_dates
        metadata["max_classes"] = f"{max_classes} x {metadata['class_time']} = {max_classes * float(metadata['class_time']):.1f}"

        # Update metadata and students using update_dates
        metadata, students = update_dates(metadata, students)

        # --- PATCH: Save to DB instead of JSON ---
        class_record = dict(metadata)
        class_record["archive"] = "No" if not self.is_edit else self.data["classes"][self.class_id].get("archive", "No")

        # --- PATCH: Remove 'dates' before inserting/updating class record ---
        if "dates" in class_record:
            del class_record["dates"]

        if not self.is_edit:
            insert_class(class_record)
            # Optionally, insert students here as well
        else:
            update_class(self.class_id, class_record)
            # Optionally, update students here as well

        # --- PATCH: Save dates to the dates table ---
        from logic.db_interface import insert_date
        for date in metadata.get("dates", []):
            if date and len(date) == 10 and date[2] == "/" and date[5] == "/":
                insert_date(class_record["class_no"], date, "")

        self.on_metadata_save()
        self.class_saved.emit(class_no)
        self.accept()

    def pick_start_date(self):
        if self.is_edit and self.class_id:
            class_data = self.data["classes"][self.class_id]
            scheduled_dates = class_data["metadata"].get("dates", [])
            students = class_data.get("students", {})
            max_classes_str = class_data["metadata"].get("max_classes", "1")
            try:
                max_dates = int(str(max_classes_str).split()[0])
            except Exception:
                max_dates = 1

            def on_save_callback(selected_dates):
                if selected_dates:
                    self.fields["start_date"].setText(selected_dates[0])
                    self.data["classes"][self.class_id]["metadata"]["dates"] = selected_dates
            launch_calendar(self, scheduled_dates, students, max_dates, on_save_callback)
        else:
            scheduled_dates = []
            students = {}
            try:
                max_dates = int(self.max_classes_input.text().split()[0])
            except Exception:
                max_dates = 1

            def on_save_callback(selected_dates):
                if selected_dates:
                    self.fields["start_date"].setText(selected_dates[0])
            launch_calendar(self, scheduled_dates, students, max_dates, on_save_callback)

    def closeEvent(self, event):
        self.resize(500, 600)
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        print(f"[DEBUG] MetadataForm shown: width={self.width()}, height={self.height()}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        print(f"[DEBUG] MetadataForm resized: width={self.width()}, height={self.height()}")

    def validate_start_date(self):
        start_date = self.fields["start_date"].text().strip()
        if not start_date:
            return
        try:
            datetime.strptime(start_date, "%d/%m/%Y")
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Start Date",
                "Start Date must be in DD/MM/YYYY format and be a real date.\n"
                "Please enter a valid date or click [Pick] to select from the calendar."
            )
            self.fields["start_date"].setFocus()
            self.fields["start_date"].selectAll()

    def warn_if_start_date_not_in_days(self):
        start_date_str = self.fields["start_date"].text().strip()
        days_str = ", ".join([day for day, cb in self.days_buttons.items() if cb.isChecked()])
        return warn_if_start_date_not_in_days(self, start_date_str, days_str)

def generate_dates(start_date_str, days_str, max_classes):
    """Generate a list of dates based on StartDate, Days, and MaxClasses.
    The first date is always StartDate, even if it doesn't match the selected days.
    """
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

    dates = []
    if start_date:
        # Always add the start date as the first date
        dates.append(start_date.strftime("%d/%m/%Y"))
        current_date = start_date + timedelta(days=1)
        while len(dates) < max_classes and weekdays:
            if current_date.weekday() in weekdays:
                dates.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)

    # Fallback to placeholders if no valid dates are generated
    if not dates:
        dates = [f"Date{i + 1}" for i in range(max_classes)]

    # Ensure the list is exactly max_classes long
    if len(dates) < max_classes:
        dates += [f"Date{i + 1}" for i in range(len(dates), max_classes)]
    elif len(dates) > max_classes:
        dates = dates[:max_classes]

    return dates