from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from logic.db_interface import set_class_archived, get_all_classes, get_class_by_id, update_class, delete_class


class ArchiveManager(QDialog):
    def __init__(self, parent, data, archived_classes, refresh_callback=None):
        super().__init__(parent)
        self.data = data
        self.archived_classes = archived_classes  # Dictionary of archived classes
        self.refresh_callback = refresh_callback  # Store the callback

        self.setWindowTitle("Archived Classes")
        self.resize(395, 300)  # Set the initial size without fixing it
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

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

        cancel_button = QPushButton("Close")
        cancel_button.clicked.connect(self.close_with_refresh)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with archived class data."""
        self.table.setRowCount(0)  # Clear existing rows
        for class_id, class_data in self.archived_classes.items():
            # class_data is now a flat dict from DB
            if class_data.get("archive", "No") != "Yes":
                continue  # Only show archived classes
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(class_id))
            self.table.setItem(row_position, 1, QTableWidgetItem(class_data.get("company", "Unknown")))
            self.table.setItem(row_position, 2, QTableWidgetItem(class_data.get("archive", "Yes")))

    def restore_class(self):
        """Restore the selected archived class immediately (no Y/N confirmation, auto-closing message)."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to restore.")
            return

        class_id = self.table.item(selected_row, 0).text()
        company = self.table.item(selected_row, 1).text()
        set_class_archived(class_id, archived=False)
        self.refresh_data()
        # Show a non-blocking confirmation dialog for 2 seconds
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt5.QtGui import QFontMetrics, QFont
        dlg = QDialog(self)
        dlg.setWindowTitle("Restored")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.FramelessWindowHint | Qt.Tool)
        layout = QVBoxLayout(dlg)
        label_text = f"Class {class_id} ({company}) has been restored."
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        dlg.setLayout(layout)
        # Dynamically set dialog width based on label text
        font = label.font() if hasattr(label, 'font') else QFont()
        metrics = QFontMetrics(font)
        text_width = metrics.width(label_text)
        dlg_width = max(text_width + 60, 400)  # 60px padding, min 400px
        dlg.setFixedSize(dlg_width, 80)
        dlg.show()
        QTimer.singleShot(2000, dlg.accept)

    def delete_class(self):
        """Delete the selected archived class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to delete.")
            return

        class_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.warning(
            self, "Delete Class",
            f"Are you sure you want to delete class {class_id}? \nThis action will delete all associated data and cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # --- PATCH: Delete from DB ---
            from logic.db_interface import delete_class
            delete_class(class_id)
            self.refresh_data()

    def refresh_data(self):
        """Refresh the table and trigger the refresh callback."""
        # Refresh the archived classes from DB
        all_classes = {row["class_no"]: row for row in get_all_classes()}
        self.archived_classes = {
            class_id: class_data
            for class_id, class_data in all_classes.items()
            if class_data.get("archive", "No") == "Yes"
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