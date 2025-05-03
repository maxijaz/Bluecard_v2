from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor, QFont


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


class TestScrollbar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Split Table Example with Zoom")
        self.setGeometry(100, 100, 1200, 600)

        # Sample data
        data = [[f"Row {row} Col {col}" for col in range(1, 21)] for row in range(1, 31)]

        # Create the main layout
        main_layout = QVBoxLayout()

        # Add a label for displaying scroll information
        self.output_label = QLabel("Scroll Value: 0.0")
        self.output_label.setStyleSheet("background-color: lightgray; padding: 5px;")
        main_layout.addWidget(self.output_label)

        # Create a horizontal layout for the tables
        table_layout = QHBoxLayout()
        table_layout.setSpacing(0)  # Remove spacing between tables

        # Create the frozen table
        self.frozen_table = QTableView()
        self.frozen_table.setModel(TableModel([row[:4] for row in data]))
        self.frozen_table.verticalHeader().hide()
        self.frozen_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.frozen_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.frozen_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.frozen_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide vertical scrollbar
        self.frozen_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Add horizontal scrollbar

        # Create the scrollable table
        self.scrollable_table = QTableView()
        self.scrollable_table.setModel(TableModel([row[4:] for row in data]))
        self.scrollable_table.verticalHeader().hide()
        self.scrollable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scrollable_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.scrollable_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Synchronize scrolling
        self.frozen_table.verticalScrollBar().valueChanged.connect(
            self.scrollable_table.verticalScrollBar().setValue
        )
        self.scrollable_table.verticalScrollBar().valueChanged.connect(
            self.frozen_table.verticalScrollBar().setValue
        )

        # Synchronize row selection
        self.frozen_table.selectionModel().selectionChanged.connect(self.sync_selection)
        self.scrollable_table.selectionModel().selectionChanged.connect(self.sync_selection)

        # Add tables to the layout
        table_layout.addWidget(self.frozen_table)
        table_layout.addWidget(self.scrollable_table)

        # Add the table layout to the main layout
        main_layout.addLayout(table_layout)

        # Set the central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Initialize zoom level
        self.zoom_level = 1.0

    def keyPressEvent(self, event):
        """Handle zoom in/out with keyboard shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus:  # Ctrl + Zoom In
                self.zoom(1.1)
            elif event.key() == Qt.Key_Minus:  # Ctrl - Zoom Out
                self.zoom(0.9)

    def zoom(self, factor):
        """Adjust the zoom level by changing font size and row height."""
        self.zoom_level *= factor

        # Adjust font size
        font = QFont()
        font.setPointSizeF(10 * self.zoom_level)  # Base font size is 10
        self.frozen_table.setFont(font)
        self.scrollable_table.setFont(font)

        # Adjust row height
        for table in [self.frozen_table, self.scrollable_table]:
            for row in range(table.model().rowCount()):
                table.setRowHeight(row, int(25 * self.zoom_level))  # Base row height is 25

        # Adjust column width
        for table in [self.frozen_table, self.scrollable_table]:
            for col in range(table.model().columnCount()):
                table.setColumnWidth(col, int(100 * self.zoom_level))  # Base column width is 100

    def sync_selection(self, selected, deselected):
        # Synchronize row selection between the two tables
        sender = self.sender()
        if sender == self.frozen_table.selectionModel():
            target_table = self.scrollable_table
        else:
            target_table = self.frozen_table

        selected_rows = sender.selectedRows()
        target_selection_model = target_table.selectionModel()
        target_selection_model.clearSelection()

        for index in selected_rows:
            target_selection_model.select(
                target_table.model().index(index.row(), 0),
                target_selection_model.Select | target_selection_model.Rows,
            )


if __name__ == "__main__":
    app = QApplication([])
    window = TestScrollbar()
    window.show()
    app.exec_()