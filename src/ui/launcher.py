from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QWidget, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from logic.parser import load_data, save_data
from ui.mainform import Mainform
import sys


class Launcher(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("Bluecard Launcher")
        self.setGeometry(100, 100, 450, 450)
        self.setFixedSize(450, 450)

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Main container widget
        container = QWidget()
        self.setCentralWidget(container)
        self.layout = QVBoxLayout(container)

        # Create UI components
        self.create_widgets()

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

        # Populate the table
        self.populate_table()

        # Buttons
        button_layout = QHBoxLayout()
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_class)
        button_layout.addWidget(open_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_class)
        button_layout.addWidget(edit_button)

        add_button = QPushButton("Add Class")
        add_button.clicked.connect(self.add_new_class)
        button_layout.addWidget(add_button)

        archive_button = QPushButton("Archive")
        archive_button.clicked.connect(self.archive_class)
        button_layout.addWidget(archive_button)

        self.layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with class data where archive = 'No', sorted by Company (A-Z)."""
        sorted_classes = sorted(
            self.classes.items(),
            key=lambda item: item[1].get("metadata", {}).get("Company", "Unknown")
        )
        self.table.setRowCount(len(sorted_classes))
        for row, (class_id, class_data) in enumerate(sorted_classes):
            metadata = class_data.get("metadata", {})
            if metadata.get("archive", "No") == "No":
                self.table.setItem(row, 0, QTableWidgetItem(class_id))
                self.table.setItem(row, 1, QTableWidgetItem(metadata.get("Company", "Unknown")))
                self.table.setItem(row, 2, QTableWidgetItem(metadata.get("archive", "No")))

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
        self.mainform.show()

    def edit_class(self):
        """Edit the selected class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to edit.")
            return
        class_id = self.table.item(selected_row, 0).text()
        print(f"Editing class ID: {class_id}")
        # Logic to open the MetadataForm for editing goes here

    def add_new_class(self):
        """Add a new class."""
        print("Adding a new class...")
        # Logic to open the MetadataForm for adding a new class goes here

    def archive_class(self):
        """Archive the selected class."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to archive.")
            return
        class_id = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.question(
            self, "Archive Class", f"Are you sure you want to archive class {class_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.classes[class_id]["metadata"]["archive"] = "Yes"
            save_data(self.data)
            self.populate_table()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher(theme="default")
    launcher.show()
    sys.exit(app.exec_())