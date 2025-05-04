from PyQt5.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QVBoxLayout, QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import sys

class AttendanceDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        value = index.data()
        if value == "P":
            option.backgroundBrush = QColor("#c8e6c9")  # light green
        elif value == "A":
            option.backgroundBrush = QColor("#ffcdd2")  # light red
        elif value == "L":
            option.backgroundBrush = QColor("#fff9c4")  # light yellow

class AttendanceTable(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance Table with Color Delegate")
        layout = QVBoxLayout(self)

        full_dates = ["2025-05-01", "2025-05-02", "2025-05-03"]
        short_dates = [d[5:].replace('-', '/') for d in full_dates]
        students = ["Alice", "Bob", "Charlie"]
        values = {
            "Alice":   ["P", "A", "L"],
            "Bob":     ["A", "P", "P"],
            "Charlie": ["P", "L", "A"]
        }

        table = QTableWidget(len(students), len(full_dates))
        table.setVerticalHeaderLabels(students)

        # Set horizontal headers with short text and tooltips
        for col, (short, full) in enumerate(zip(short_dates, full_dates)):
            item = QTableWidgetItem(short)
            item.setToolTip(full)
            table.setHorizontalHeaderItem(col, item)

        # Fill values
        for row, student in enumerate(students):
            for col, letter in enumerate(values[student]):
                item = QTableWidgetItem(letter)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

        # Delegate for coloring
        table.setItemDelegate(AttendanceDelegate(table))

        # Narrow columns
        for col in range(len(full_dates)):
            table.setColumnWidth(col, 45)

        table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(table)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AttendanceTable()
    window.resize(300, 250)
    window.show()
    sys.exit(app.exec_())
