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
import sys
import json
import os


class Launcher(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Bluecard Launcher")
        self.setGeometry(100, 100, 450, 450)
        self.setFixedSize(395, 300)

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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)  # Use fixed column widths
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
        print(f"Selected class ID: {class_id}")
        print("Opening Mainform...")

        # Open the Mainform window with the correct data
        self.mainform = Mainform(class_id, self.data, self.theme)
        self.mainform.showMaximized()  # Open the Mainform maximized
        self.mainform.closed.connect(self.show_launcher)  # Reopen Launcher when Mainform is closed
        self.close()  # Close the Launcher

    def show_launcher(self):
        """Reopen the Launcher and center it on the screen."""
        self.show()
        self.center_window()

    def edit_class(self):
        """Edit the selected class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to edit.")
            return

        class_id = self.table.item(selected_row, 0).text()
        print(f"Editing class ID: {class_id}")

        # Open the MetadataForm for editing
        metadata_form = MetadataForm(self, class_id, self.data, self.theme, self.refresh_table)
        metadata_form.exec_()  # Open the form as a modal dialog

    def add_new_class(self):
        """Add a new class with default values."""
        print("Adding a new class...")

        # Load default values
        defaults = self.load_defaults()
        if not defaults:
            return  # Exit if defaults could not be loaded

        # Open the MetadataForm with default values
        metadata_form = MetadataForm(self, None, self.data, self.theme, self.refresh_table, defaults)
        metadata_form.class_saved.connect(self.open_mainform_after_save)  # Connect the signal
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
            if class_data.get("metadata", {}).get("archive", "No") == "Yes"
        }

        if not archived_classes:
            QMessageBox.information(self, "No Archived Classes", "There are no archived classes to manage.")
            return

        print(f"Opening Archive Manager for archived classes: {list(archived_classes.keys())}")
        archive_manager = ArchiveManager(self, self.data, archived_classes, self.refresh_table)
        archive_manager.exec_()  # Open the Archive Manager as a modal dialog

    def open_ttr(self):
        """Open the TTR."""
        print("Opening TTR...")
        # Logic to open the TTR goes here

    def open_settings(self):
        """Open the Settings dialog."""
        print("Opening Settings...")
        settings_form = SettingsForm(self, self.theme, self.refresh_theme)
        if settings_form.exec_() == QDialog.Accepted:
            print("Settings updated.")

    def refresh_theme(self, new_theme):
        """Refresh the theme in the Launcher."""
        self.theme = new_theme
        print(f"Theme updated to: {new_theme}")

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

    def save_metadata(self):
        """Save metadata for the class."""
        class_no = self.fields["class_no"].text().strip().upper()
        if not class_no:
            QMessageBox.warning(self, "Validation Error", "Class No is required.")
            return

        if class_no in self.data["classes"] and not self.is_edit:
            QMessageBox.warning(self, "Duplicate Class ID", f"Class ID '{class_no}' already exists.")
            return

        metadata = {key: field.text().strip() for key, field in self.fields.items()}
        metadata["CourseHours"] = self.class_hours_input.text()
        metadata["ClassTime"] = self.class_time_input.text()
        metadata["MaxClasses"] = self.max_classes_input.text()

        if not self.is_edit:
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            self.data["classes"][self.class_id]["metadata"] = metadata

        save_data(self.data)
        self.on_metadata_save()

        # Emit the signal with the new class ID
        self.class_saved.emit(class_no)

        self.accept()  # Close the dialog

    def open_mainform_after_save(self, class_id):
        """Open the Mainform after saving a new class."""
        print(f"Opening Mainform for new class ID: {class_id}")

        # Open the Mainform window with the correct data
        self.mainform = Mainform(class_id, self.data, self.theme)
        self.mainform.showMaximized()  # Open the Mainform maximized
        self.mainform.closed.connect(self.show_launcher)  # Reopen Launcher when Mainform is closed
        self.close()  # Close the Launcher


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher(theme="default")
    launcher.show()
    sys.exit(app.exec_())