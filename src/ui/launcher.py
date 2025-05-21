from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QWidget, QMessageBox, QApplication, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from logic.parser import load_data, save_data
from ui.mainform import Mainform
from ui.metadata_form import MetadataForm
from ui.archive_manager import ArchiveManager
from ui.settings import SettingsForm
from .calendar import CalendarView
from logic.update_dates import update_dates, add_date, remove_date, modify_date
from logic.date_utils import warn_if_start_date_not_in_days
import sys
import json
import os
from datetime import datetime, timedelta


class Launcher(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Bluecard Launcher")
        self.resize(395, 300)  # Set the initial size without fixing it
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Main container widget
        container = QWidget()
        self.setCentralWidget(container)
        self.layout = QVBoxLayout(container)

        # Create UI components
        self.create_widgets()

        # Center the window on startup
        self.center_window()

    def create_widgets(self):
        """Create the table and buttons."""
        # Table for class data
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Class No", "Company", "Archived"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.layout.addWidget(self.table)

        # Set column widths
        self.table.setColumnWidth(0, 150)  # Class No
        self.table.setColumnWidth(1, 150)  # Company
        self.table.setColumnWidth(2, 75)   # Archived

        # Connect double-click event to open_class
        self.table.doubleClicked.connect(self.open_class)

        # Populate the table
        self.populate_table()

        # Buttons - Row 1
        button_layout_row1 = QHBoxLayout()

        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_class)
        button_layout_row1.addWidget(open_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_class)
        button_layout_row1.addWidget(edit_button)

        add_button = QPushButton("Add New Class")
        add_button.clicked.connect(self.add_new_class)
        button_layout_row1.addWidget(add_button)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        button_layout_row1.addWidget(settings_button)

        self.layout.addLayout(button_layout_row1)

        # Buttons - Row 2
        button_layout_row2 = QHBoxLayout()

        archive_button = QPushButton("Archive")
        archive_button.clicked.connect(self.archive_class)
        button_layout_row2.addWidget(archive_button)

        archive_manager_button = QPushButton("Archive Manager")
        archive_manager_button.clicked.connect(self.open_archive_manager)
        button_layout_row2.addWidget(archive_manager_button)

        ttr_button = QPushButton("TTR")
        ttr_button.clicked.connect(self.open_ttr)
        button_layout_row2.addWidget(ttr_button)

        self.layout.addLayout(button_layout_row2)

    def populate_table(self):
        """Populate the table with class data where archive = 'No', sorted by Company (A-Z)."""
        self.table.setRowCount(0)  # Clear the table before repopulating
        sorted_classes = sorted(
            self.classes.items(),
            key=lambda item: item[1].get("metadata", {}).get("Company", "Unknown")
        )
        for class_id, class_data in sorted_classes:
            metadata = class_data.get("metadata", {})
            if metadata.get("archive", "No") == "No":
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(class_id))
                self.table.setItem(row_position, 1, QTableWidgetItem(metadata.get("Company", "Unknown")))
                self.table.setItem(row_position, 2, QTableWidgetItem(metadata.get("archive", "No")))

    def open_class(self):
        """Open the selected class in the Mainform."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to open.")
            return

        class_id = self.table.item(selected_row, 0).text()

        # Open the Mainform window with the correct data
        self.mainform = Mainform(class_id, self.data, self.theme)
        self.mainform.showMaximized()  # Open the Mainform maximized
        self.mainform.closed.connect(self.show_launcher)  # Reopen Launcher when Mainform is closed
        self.close()  # Close the Launcher

    def show_launcher(self):
        """Reopen the Launcher and refresh its data."""
        self.refresh_data()  # Refresh the data and table
        self.show()
        self.center_window()

    def edit_class(self):
        """Edit the selected class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to edit.")
            return

        class_id = self.table.item(selected_row, 0).text()

        # Open the MetadataForm for editing
        metadata_form = MetadataForm(self, class_id, self.data, self.theme, self.refresh_table)
        metadata_form.exec_()  # Open the form as a modal dialog

    def add_new_class(self):
        """Add a new class with default values."""
        # Load default values
        defaults = self.load_defaults()
        if not defaults:
            return  # Exit if defaults could not be loaded

        # Open the MetadataForm with single-date mode enabled
        metadata_form = MetadataForm(self, None, self.data, self.theme, self.refresh_table, defaults, single_date_mode=True)

        def handle_class_saved(class_id):
            metadata = self.data["classes"][class_id]["metadata"]
            start_date = metadata.get("StartDate", "").strip()
            days = metadata.get("Days", "").strip()
            max_classes = int(metadata.get("MaxClasses", "20").split()[0])  # Extract numeric part of MaxClasses

            # Generate dates and update metadata
            metadata["Dates"] = generate_dates(start_date, days, max_classes)

            # Save the updated data
            save_data(self.data)

            # Open the Mainform window with the correct data
            self.open_mainform_after_save(class_id)

        metadata_form.class_saved.connect(handle_class_saved)  # Connect the signal

        metadata_form.exec_()  # Open the form as a modal dialog

    def archive_class(self):
        """Archive the selected class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to archive.")
            return

        class_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.question(
            self,
            "Archive Class",
            f"Are you sure you want to archive class {class_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Set the archive field to "Yes"
            self.classes[class_id]["metadata"]["archive"] = "Yes"
            save_data(self.data)  # Save changes to 001attendance_data.json
            self.populate_table()  # Refresh the table to show only non-archived classes
            QMessageBox.information(self, "Archived", f"Class {class_id} has been archived.")

    def open_archive_manager(self):
        """Open the Archive Manager for all archived classes."""
        archived_classes = {
            class_id: class_data
            for class_id, class_data in self.classes.items()
            if class_data.get("metadata", {}).get("archive", "Yes") == "Yes"
        }

        if not archived_classes:
            QMessageBox.information(self, "No Archived Classes", "There are no archived classes to manage.")
            return

        archive_manager = ArchiveManager(self, self.data, archived_classes, self.refresh_table)
        archive_manager.exec_()  # Open the Archive Manager as a modal dialog

    def open_ttr(self):
        """Open the TTR."""
        pass  # Logic to open the TTR goes here

    def open_settings(self):
        """Open the Settings dialog."""
        settings_form = SettingsForm(self, self.theme, self.refresh_theme)
        if settings_form.exec_() == QDialog.Accepted:
            pass  # Handle settings update

    def refresh_theme(self, new_theme):
        """Refresh the theme in the Launcher."""
        self.theme = new_theme

    def refresh_table(self):
        """Refresh the table with updated class data."""
        self.populate_table()

    def load_defaults(self):
        """Load default values from default.json."""
        defaults_path = "data/default.json"
        if not os.path.exists(defaults_path):
            QMessageBox.warning(self, "Error", "Default settings file (default.json) not found.")
            return {}
        try:
            with open(defaults_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Error", "Failed to parse default.json.")
            return {}

    def center_window(self):
        """Center the Launcher window on the screen."""
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def open_mainform_after_save(self, class_id):
        """Open the Mainform after saving a new class."""
        metadata = self.data["classes"][class_id]["metadata"]
        start_date = metadata.get("StartDate", "").strip()
        days = metadata.get("Days", "").strip()
        max_classes = int(metadata.get("MaxClasses", "20").split()[0])  # Extract numeric part of MaxClasses

        # Generate dates if not already present
        if not metadata.get("Dates"):
            metadata["Dates"] = generate_dates(start_date, days, max_classes)

        # Save the updated data
        save_data(self.data)

        # Open the Mainform window with the correct data
        self.mainform = Mainform(class_id, self.data, self.theme)
        self.mainform.showMaximized()  # Open the Mainform maximized
        self.mainform.closed.connect(self.show_launcher)  # Reopen Launcher when Mainform is closed
        self.close()  # Close the Launcher

    def refresh_data(self):
        """Refresh the data and table in the Launcher."""
        self.data = load_data()  # Reload the data from the source
        self.classes = self.data.get("classes", {})  # Update the classes dictionary
        self.populate_table()  # Refresh the table with the updated data

    def closeEvent(self, event):
        """Restore the initial size when the launcher is reopened."""
        self.resize(395, 300)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher(theme="default")
    launcher.show()
    sys.exit(app.exec_())