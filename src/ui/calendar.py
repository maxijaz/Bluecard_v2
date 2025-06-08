from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QTextCharFormat, QColor, QFont
from logic.display import center_widget, scale_and_center, apply_window_flags
from logic.db_interface import get_all_defaults


class CalendarView(QDialog):
    def __init__(self, parent=None, scheduled_dates=None, on_save_callback=None, max_dates=20, protected_dates=None):
        super().__init__(parent)
        self.setWindowTitle("Class Schedule Calendar")

        # --- PATCH: Use DB-driven sizing, font, and button styles ---
        defaults = get_all_defaults()
        font_family = defaults.get("form_font_family", "Segoe UI")
        font_size = int(defaults.get("form_font_size", 12))
        self.form_font = QFont(font_family, font_size)
        self.setFont(self.form_font)
        win_w = int(defaults.get("window_width", 400))
        win_h = int(defaults.get("window_height", 400))
        self.resize(win_w, win_h)

        self.max_dates = max_dates
        self.on_save_callback = on_save_callback

        # Convert incoming date strings to QDate objects
        self.scheduled_dates = [
            qd for qd in (QDate.fromString(d, "dd/MM/yyyy") for d in (scheduled_dates or []))
            if qd.isValid()
        ]
        self.selected_dates = set(self.scheduled_dates)  # Only scheduled dates are selected

        # Convert protected dates to QDate objects
        self.protected_dates = [QDate.fromString(d, "dd/MM/yyyy") for d in (protected_dates or [])]

        # Layout
        layout = QVBoxLayout(self)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.toggle_date_selection)
        layout.addWidget(self.calendar)

        # Highlight already scheduled dates
        self.highlight_dates(self.selected_dates)

        # Remove blue highlight from today if today is not in scheduled_dates
        today = QDate.currentDate()
        if today not in self.selected_dates:
            self.clear_highlight(today)
        self.highlight_today()  # Always highlight today in red

        # Highlight protected dates in gray
        self.highlight_protected_dates(self.protected_dates)

        # Save and Close buttons in a row
        button_row = QVBoxLayout()
        button_layout = QHBoxLayout()
        # --- PATCH: Button style from DB ---
        button_bg = defaults.get("button_bg_color", "#1976d2")
        button_fg = defaults.get("button_fg_color", "#ffffff")
        button_font_size = int(defaults.get("button_font_size", 12))
        button_font_bold = str(defaults.get("button_font_bold", "no")).lower() in ("yes", "true", "1")
        button_hover_bg = defaults.get("button_hover_bg_color", "#1565c0")
        button_active_bg = defaults.get("button_active_bg_color", "#0d47a1")
        button_border = defaults.get("button_border_color", "#1976d2")
        button_style = (
            f"QPushButton {{background: {button_bg}; color: {button_fg}; border: 2px solid {button_border}; font-size: {button_font_size}pt; font-weight: {'bold' if button_font_bold else 'normal'};}}"
            f"QPushButton:hover {{background: {button_hover_bg};}}"
            f"QPushButton:pressed {{background: {button_active_bg};}}"
        )
        save_button = QPushButton("Save Changes")
        save_button.setFont(self.form_font)
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)
        close_button = QPushButton("Close")
        close_button.setFont(self.form_font)
        close_button.setStyleSheet(button_style)
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        button_row.addLayout(button_layout)
        layout.addLayout(button_row)

    def highlight_today(self):
        """Highlight today's date in red without showing the blue selection box."""
        today = QDate.currentDate()
        format = QTextCharFormat()
        format.setBackground(QColor(255, 102, 102))  # Light red background
        format.setForeground(QColor("black"))  # Ensure the text is visible
        self.calendar.setDateTextFormat(today, format)

    def highlight_dates(self, dates):
        """Highlight selected dates in light blue."""
        format = QTextCharFormat()
        format.setBackground(QColor("lightblue"))
        for date in dates:
            if date.isValid():
                self.calendar.setDateTextFormat(date, format)

    def highlight_protected_dates(self, dates):
        """Highlight protected dates in gray."""
        format = QTextCharFormat()
        format.setBackground(QColor("gray"))
        format.setForeground(QColor("white"))  # Ensure the text is visible
        for date in dates:
            if date.isValid():
                self.calendar.setDateTextFormat(date, format)

    def clear_highlight(self, date):
        """Clear the highlight for a specific date."""
        if date.isValid():
            self.calendar.setDateTextFormat(date, QTextCharFormat())

    def toggle_date_selection(self, date):
        """Toggle the selection of a date."""
        print("Before toggle:", [d.toString("dd/MM/yyyy") for d in self.selected_dates])
        if date in self.protected_dates:
            QMessageBox.warning(
                self,
                "Protected Date",
                "This date cannot be changed because it has attendance data.\n"
                "Click column header date on the Bluecard table and clear data to be able to change the date of a grey protected field on the calendar."
            )
            return

        if date in self.selected_dates:
            self.selected_dates.remove(date)
            self.clear_highlight(date)
        else:
            if len(self.selected_dates) == self.max_dates:
                QMessageBox.warning(self, "Limit Reached", f"You can only select up to {self.max_dates} dates.")
                return  # Only block when trying to add one more than allowed
            self.selected_dates.add(date)
            self.highlight_dates([date])
        print("After toggle:", [d.toString("dd/MM/yyyy") for d in self.selected_dates])

    def save_changes(self):
        """Save the selected dates."""
        print("Saving selected dates:", [d.toString("dd/MM/yyyy") for d in self.selected_dates])
        if len(self.selected_dates) > self.max_dates:
            QMessageBox.warning(self, "Too Many Dates", f"Please select up to {self.max_dates} dates.")
            return

        if not self.selected_dates:
            QMessageBox.warning(self, "No Dates Selected", "Please select at least one date.")
            return

        # Sort and filter out invalid dates
        sorted_dates = sorted(self.selected_dates)
        formatted_dates = [d.toString("dd/MM/yyyy") for d in sorted_dates if d.isValid()]
        print(f"Formatted dates to save: {formatted_dates}")  # Debugging: Check formatted dates

        # Fill up to max_dates with placeholders if needed
        num_dates = len(formatted_dates)
        if num_dates < self.max_dates:
            placeholders = [f"Date{i+1}" for i in range(num_dates, self.max_dates)]
            formatted_dates += placeholders
        elif num_dates > self.max_dates:
            formatted_dates = formatted_dates[:self.max_dates]

        if self.on_save_callback:
            self.on_save_callback(formatted_dates)

        self.accept()


def launch_calendar(parent, scheduled_dates, students, max_classes, on_save_callback):
    """
    Shared function to open the CalendarView with correct protected dates and max_classes.
    """
    # Collect protected dates: any date with P, A, L, CIA, COD, or HOL for any student
    protected_dates = set()
    for student in students.values():
        attendance = student.get("attendance", {})
        for date, value in attendance.items():
            if value in ["P", "A", "L", "CIA", "COD", "HOL"]:
                protected_dates.add(date)

    calendar_view = CalendarView(
        parent,
        scheduled_dates=scheduled_dates,
        on_save_callback=on_save_callback,
        max_dates=max_classes,
        protected_dates=list(protected_dates)
    )
    calendar_view.exec_()
