import tkinter as tk
from tkinter import ttk, messagebox
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel, QHBoxLayout, QFrame, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor, QFont
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime, timedelta
import PyQt5.sip  # Import PyQt5.sip to bridge PyQt5 and Tkinter


class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self.data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.data[0]) if self.data else 0

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.data[index.row()][index.column()]
        elif role == Qt.BackgroundRole:
            # Alternate row coloring for better readability
            if index.row() % 2 == 0:
                return QColor("#f0f0f0")
        return None


class Mainform(QMainWindow):
    def __init__(self, class_id, data, theme):
        super().__init__()
        self.setWindowTitle(f"Class Information - {class_id}")

        # Open maximized and set topmost
        self.showMaximized()
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.metadata = self.data["classes"][self.class_id]["metadata"]

        # Main container widget
        container = QWidget()
        layout = QVBoxLayout(container)

        # Metadata Section
        metadata_layout = QGridLayout()
        metadata_layout.setHorizontalSpacing(5)  # Reduced horizontal spacing for tighter alignment
        metadata_layout.setVerticalSpacing(5)  # Reduced vertical spacing for tighter alignment

        # Metadata fields
        metadata_fields = [
            ("Company:", self.metadata.get("Company", ""), "Course Hours:", self.metadata.get("CourseHours", "")),
            ("Room:", self.metadata.get("Room", ""), "Start Date:", self.metadata.get("StartDate", "")),
            ("Consultant:", self.metadata.get("Consultant", ""), "Finish Date:", self.metadata.get("FinishDate", "")),
            ("Teacher:", self.metadata.get("Teacher", ""), "Days:", self.metadata.get("Days", "")),
            ("CourseBook:", self.metadata.get("CourseBook", ""), "Time:", self.metadata.get("Time", "")),
            ("Notes:", self.metadata.get("Notes", ""), "", ""),
        ]

        # Add metadata to the grid layout
        for row, (label1, value1, label2, value2) in enumerate(metadata_fields):
            # Column 1: Label
            label1_widget = QLabel(label1)
            label1_widget.setStyleSheet("font-weight: bold; text-align: left; border: 1px groove black;")
            label1_widget.setFixedWidth(150)
            metadata_layout.addWidget(label1_widget, row, 0)

            # Column 2: Metadata
            value1_widget = QLabel(value1)
            value1_widget.setStyleSheet("text-align: center; border: 1px groove black;")
            value1_widget.setFixedWidth(150)
            metadata_layout.addWidget(value1_widget, row, 1)

            # Column 3: Label
            if label2:  # Only add if label2 is not empty
                label2_widget = QLabel(label2)
                label2_widget.setStyleSheet("font-weight: bold; text-align: left; border: 1px groove black;")
                label2_widget.setFixedWidth(150)
                metadata_layout.addWidget(label2_widget, row, 2)

            # Column 4: Metadata
            if value2:  # Only add if value2 is not empty
                value2_widget = QLabel(value2)
                value2_widget.setStyleSheet("text-align: center; border: 1px groove black;")
                value2_widget.setFixedWidth(150)
                metadata_layout.addWidget(value2_widget, row, 3)

        layout.addLayout(metadata_layout)

        # Buttons Section
        buttons_layout = QHBoxLayout()
        buttons = [
            QPushButton("Add Student"),
            QPushButton("Edit Student"),
            QPushButton("Remove Student"),
            QPushButton("Manage Students"),
        ]
        for button in buttons:
            buttons_layout.addWidget(button)
        layout.addLayout(buttons_layout)

        # Table Section
        table_layout = QHBoxLayout()

        # Sample data
        data = [[f"Row {row} Col {col}" for col in range(1, 21)] for row in range(1, 31)]

        # Frozen Table
        frozen_table = QTableView()
        frozen_table.setModel(TableModel([row[:4] for row in data]))
        frozen_table.verticalHeader().hide()
        frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frozen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Add horizontal scrollbar
        frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Scrollable Table
        scrollable_table = QTableView()
        scrollable_table.setModel(TableModel([row[4:] for row in data]))
        scrollable_table.verticalHeader().hide()
        scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Synchronize scrolling
        frozen_table.verticalScrollBar().valueChanged.connect(
            scrollable_table.verticalScrollBar().setValue
        )
        scrollable_table.verticalScrollBar().valueChanged.connect(
            frozen_table.verticalScrollBar().setValue
        )

        # Add tables to the layout
        table_layout.addWidget(frozen_table)
        table_layout.addWidget(scrollable_table)
        layout.addLayout(table_layout)

        # Set the main layout
        self.setCentralWidget(container)


if __name__ == "__main__":
    import sys

    # Example data
    example_data = {
        "classes": {
            "OLO123": {
                "metadata": {
                    "Company": "Example Company",
                    "Consultant": "John Doe",
                    "Teacher": "Jane Smith",
                    "Room": "101",
                    "CourseBook": "Advanced Python",
                },
                "students": {},
            }
        }
    }

    app = QApplication(sys.argv)
    window = Mainform("OLO123", example_data, "default")
    window.show()
    sys.exit(app.exec_())