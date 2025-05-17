from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from logic.parser import save_data


class ArchiveManager(QDialog):
    def __init__(self, parent, data, archived_classes, refresh_callback=None):
        super().__init__(parent)
        self.data = data
        self.archived_classes = archived_classes  # Dictionary of archived classes
        self.refresh_callback = refresh_callback  # Store the callback

        self.setWindowTitle("Archived Classes")
        self.resize(395, 300)  # Set the initial size without fixing it
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        # Main layout
        layout = QVBoxLayout(self)

        # Table for archived classes
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Class ID", "Company", "Archived"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Stretch columns to fill width
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # Populate the table
        self.populate_table()

        # Buttons
        button_layout = QHBoxLayout()
        restore_button = QPushButton("Restore")
        restore_button.clicked.connect(self.restore_class)
        button_layout.addWidget(restore_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_class)
        button_layout.addWidget(delete_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close_with_refresh)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with archived class data."""
        self.table.setRowCount(0)  # Clear existing rows
        for class_id, class_data in self.archived_classes.items():
            metadata = class_data.get("metadata", {})
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(class_id))
            self.table.setItem(row_position, 1, QTableWidgetItem(metadata.get("Company", "Unknown")))
            self.table.setItem(row_position, 2, QTableWidgetItem(metadata.get("archive", "Yes")))

    def restore_class(self):
        """Restore the selected archived class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to restore.")
            return

        class_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.question(
            self, "Restore Class",
            f"Are you sure you want to restore class {class_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.data["classes"][class_id]["metadata"]["archive"] = "No"  # Restore the class
            save_data(self.data)  # Save changes to file
            self.refresh_data()  # Refresh the table and launcher

    def delete_class(self):
        """Delete the selected archived class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to delete.")
            return

        class_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.warning(
            self, "Delete Class",
            f"Are you sure you want to delete class {class_id}? This action will delete all associated data and cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.data["classes"][class_id]  # Delete the class and its data
            save_data(self.data)  # Save changes to file
            self.refresh_data()  # Refresh the table and launcher

    def refresh_data(self):
        """Refresh the table and trigger the refresh callback."""
        # Refresh the archived classes
        self.archived_classes = {
            class_id: class_data
            for class_id, class_data in self.data["classes"].items()
            if class_data.get("metadata", {}).get("archive", "No") == "Yes"
        }
        self.populate_table()  # Refresh the table

        # Trigger the callback to refresh the launcher
        if self.refresh_callback:
            self.refresh_callback()

    def close_with_refresh(self):
        """Close the dialog and trigger the refresh callback."""
        if self.refresh_callback:
            self.refresh_callback()  # Trigger the callback
        self.accept()  # Close the dialog

    def closeEvent(self, event):
        """Restore the initial size when the archive manager is reopened."""
        self.resize(395, 300)
        super().closeEvent(event)