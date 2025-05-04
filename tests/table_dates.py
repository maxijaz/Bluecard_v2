from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
import sys

class AttendanceTable(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compact Attendance Table with Tooltips")
        layout = QVBoxLayout(self)

        # Full & short date formats
        full_dates = ["2025-05-01", "2025-05-02", "2025-05-03"]
        short_dates = [d[5:].replace('-', '/') for d in full_dates]  # e.g. "05/01"
        students = ["Alice", "Bob", "Charlie"]
        values = {
            "Alice": ["P", "A", "P"],
            "Bob":   ["A", "P", "P"],
            "Charlie": ["P", "P", "A"]
        }

        table = QTableWidget(len(students), len(full_dates))
        table.setVerticalHeaderLabels(students)

        # Set headers with tooltips
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
    window.resize(300, 200)
    window.show()
    sys.exit(app.exec_())
