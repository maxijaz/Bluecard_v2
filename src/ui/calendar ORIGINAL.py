from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget, QPushButton, QMessageBox
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QTextCharFormat, QColor


class CalendarView(QDialog):
    def __init__(self, parent=None, scheduled_dates=None, on_save_callback=None, max_dates=20):
        """
        A reusable calendar view for managing and visualizing dates.

        :param parent: The parent widget.
        :param scheduled_dates: A list of dates (in "dd/MM/yyyy" format) to highlight.
        :param on_save_callback: A callback function to handle saving changes.
        :param max_dates: The maximum number of dates the user can select.
        """
        super().__init__(parent)
        self.setWindowTitle("Class Schedule Calendar")
        self.setFixedSize(400, 400)

        self.scheduled_dates = scheduled_dates or []
        self.on_save_callback = on_save_callback
        self.max_dates = max_dates
        self.selected_dates = set(self.scheduled_dates)  # Initialize with existing dates

        # Main layout
        layout = QVBoxLayout(self)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.toggle_date_selection)
        layout.addWidget(self.calendar)

        # Highlight scheduled dates
        self.highlight_dates(self.scheduled_dates)

        # Save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

    def highlight_dates(self, dates):
        """Highlight the scheduled dates on the calendar."""
        format = QTextCharFormat()
        format.setBackground(QColor("lightblue"))
        for date_str in dates:
            date = QDate.fromString(date_str, "dd/MM/yyyy")
            if date.isValid():
                self.calendar.setDateTextFormat(date, format)

    def clear_highlight(self, date_str):
        """Clear the highlight for a specific date."""
        date = QDate.fromString(date_str, "dd/MM/yyyy")
        if date.isValid():
            self.calendar.setDateTextFormat(date, QTextCharFormat())

    def toggle_date_selection(self, date):
        """Toggle the selection of a date."""
        date_str = date.toString("dd/MM/yyyy")
        if date_str in self.selected_dates:
            self.selected_dates.remove(date_str)
            self.clear_highlight(date_str)  # Remove highlight
        else:
            if len(self.selected_dates) < self.max_dates:
                self.selected_dates.add(date_str)
                self.highlight_dates([date_str])  # Add highlight
            else:
                QMessageBox.warning(self, "Limit Reached", f"You can only select up to {self.max_dates} dates.")

    def save_changes(self):
        """Save the selected dates."""
        if len(self.selected_dates) > self.max_dates:
            QMessageBox.warning(self, "Too Many Dates", f"Please select up to {self.max_dates} dates.")
            return

        if not self.selected_dates:
            QMessageBox.warning(self, "No Dates Selected", "Please select at least one date.")
            return

        # Sort the selected dates and pass them to the callback
        sorted_dates = sorted(self.selected_dates, key=lambda d: QDate.fromString(d, "dd/MM/yyyy"))
        if self.on_save_callback:
            self.on_save_callback(sorted_dates)
        self.accept()  # Close the dialog