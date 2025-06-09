from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sys

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sidebar Navigation Example")
        self.resize(800, 600)

        # Define default values
        self.default_font = QFont("Arial", 11)
        self.sidebar_width = 200
        self.bg_color = "#f0f0f0"
        self.active_color = "#d0d0ff"

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        sidebar = QListWidget()
        sidebar.setFixedWidth(self.sidebar_width)
        sidebar.setFont(self.default_font)
        sidebar.setStyleSheet(f"background-color: {self.bg_color};")

        # Add navigation items
        for name in ["Home", "Settings", "About"]:
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignCenter)
            sidebar.addItem(item)

        # Stack for main content
        self.stack = QStackedWidget(self)
        self.stack.setFont(self.default_font)

        # Add pages to the stack
        self.stack.addWidget(self.make_page("Welcome to the Home Page"))
        self.stack.addWidget(self.make_page("Settings Page: Change your preferences here."))
        self.stack.addWidget(self.make_page("About Page: Version 1.0"))

        # Connect navigation
        sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        sidebar.setCurrentRow(0)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

    def make_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setFont(self.default_font)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
