from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QGridLayout, QVBoxLayout, QApplication
)
import sys

class StyleSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Style Settings")
        self.setGeometry(100, 100, 400, 500)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Grid for labels + entries
        grid = QGridLayout()

        # Define your label/text entry pairs
        fields = [
            ("Form Title Color", QLineEdit()),
            ("Form BG Color", QLineEdit()),
            ("Form Text Color", QLineEdit()),
            ("Form Border Color", QLineEdit()),
            ("Form Font Size", QLineEdit()),
            ("Metadata BG Color", QLineEdit()),
            ("Metadata Text Color", QLineEdit()),
            ("Metadata Font Size", QLineEdit()),
            ("Button BG Color", QLineEdit()),
            ("Button Text Color", QLineEdit()),
            ("Button Border Color", QLineEdit()),
            ("Button Font Size", QLineEdit()),
            ("Table Header BG Color", QLineEdit()),
            ("Table Header Text Color", QLineEdit()),
            ("Table Header Font Size", QLineEdit()),
            ("Table BG Color", QLineEdit()),
            ("Table Text Color", QLineEdit()),
            ("Table Font Size", QLineEdit()),
        ]

        # Add to grid layout (2 columns of fields)
        for index, (label_text, widget) in enumerate(fields):
            row = index % 9
            col = 0 if index < 9 else 2  # start new column
            grid.addWidget(QLabel(label_text), row, col)
            grid.addWidget(widget, row, col + 1)

        layout.addLayout(grid)

        # Add buttons at the bottom
        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_restore = QPushButton("Restore")

        button_layout = QGridLayout()
        button_layout.addWidget(btn_save, 0, 0)
        button_layout.addWidget(btn_cancel, 0, 1)
        button_layout.addWidget(btn_restore, 0, 2)

        layout.addLayout(button_layout)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StyleSettingsWidget()
    window.show()
    sys.exit(app.exec_())
