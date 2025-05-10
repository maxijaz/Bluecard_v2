from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget, QPushButton, QMessageBox
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QTextCharFormat, QColor


class CalendarView(QDialog):
    def __init__(self, parent=None, scheduled_dates=None, on_save_callback=None, max_dates=20):
        super().__init__(parent)
        self.setWindowTitle("Class Schedule Calendar")
        self.setFixedSize(400, 400)

        self.max_dates = max_dates
        self.on_save_callback = on_save_callback

        # Convert incoming date strings to QDate objects
        self.scheduled_dates = [QDate.fromString(d, "dd/MM/yyyy") for d in (scheduled_dates or [])]
        self.selected_dates = set(self.scheduled_dates)

        # Layout
        layout = QVBoxLayout(self)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.toggle_date_selection)
        layout.addWidget(self.calendar)

        # Highlight already scheduled dates
        self.highlight_dates(self.selected_dates)

        # Highlight today's date in red
        self.highlight_today()

        # Save button
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

    def highlight_today(self):
        """Highlight today's date in red without showing the blue selection box."""
        today = QDate.currentDate()
        format = QTextCharFormat()
        format.setBackground(QColor(255, 102, 102))  # Light red background
        format.setForeground(QColor("black"))  # Ensure the text is visible
        self.calendar.setDateTextFormat(today, format)

        # Clear the blue selection box
        self.calendar.setSelectedDate(QDate())  # Set to an invalid date to clear selection

    def highlight_dates(self, dates):
        """Highlight selected dates in light blue."""
        format = QTextCharFormat()
        format.setBackground(QColor("lightblue"))
        for date in dates:
            if date.isValid():
                self.calendar.setDateTextFormat(date, format)

    def clear_highlight(self, date):
        """Clear the highlight for a specific date."""
        if date.isValid():
            self.calendar.setDateTextFormat(date, QTextCharFormat())

    def toggle_date_selection(self, date):
        """Toggle the selection of a date."""
        if self.max_dates == 1:
            # Single-date mode: Clear the previous selection and select the new date
            if self.selected_dates:
                # Clear the previously selected date
                for selected_date in self.selected_dates:
                    self.clear_highlight(selected_date)
                self.selected_dates.clear()

            # Add the new date
            self.selected_dates.add(date)
            self.highlight_dates([date])
        else:
            # Multi-date mode: Toggle the selection of the clicked date
            if date in self.selected_dates:
                self.selected_dates.remove(date)
                self.clear_highlight(date)
            else:
                if len(self.selected_dates) < self.max_dates:
                    self.selected_dates.add(date)
                    self.highlight_dates([date])
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

        # Sort and filter out invalid dates
        sorted_dates = sorted(self.selected_dates)
        formatted_dates = [d.toString("dd/MM/yyyy") for d in sorted_dates if d.isValid()]
        print(f"Formatted dates to save: {formatted_dates}")  # Debugging: Check formatted dates

        if self.on_save_callback:
            self.on_save_callback(formatted_dates)

        self.accept()
