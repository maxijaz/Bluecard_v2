from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QButtonGroup, QLabel
)
import sys

class GenderSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.gender = "female"

        self.label = QLabel("Selected: Female")

        # Create buttons
        self.female_btn = QPushButton("Female")
        self.male_btn = QPushButton("Male")
        self.clear_btn = QPushButton("Not Set")

        for btn in (self.female_btn, self.male_btn, self.clear_btn):
            btn.setCheckable(True)
            btn.setFixedWidth(110)  # Equal width for all buttons

        # Group for exclusive selection
        self.gender_group = QButtonGroup()
        self.gender_group.setExclusive(True)
        self.gender_group.addButton(self.female_btn)
        self.gender_group.addButton(self.male_btn)
        self.gender_group.addButton(self.clear_btn)

        # Set default
        self.female_btn.setChecked(True)

        # Connect logic
        self.female_btn.clicked.connect(lambda: self.set_gender("female"))
        self.male_btn.clicked.connect(lambda: self.set_gender("male"))
        self.clear_btn.clicked.connect(lambda: self.set_gender(""))

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.female_btn)
        layout.addWidget(self.male_btn)
        layout.addWidget(self.clear_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(self.label)
        self.setLayout(main_layout)

        # Style
        self.setStyleSheet(self.custom_style())

    def set_gender(self, value):
        self.gender = value  # store exact value
        if value == "":
            self.label.setText("Selected: Not Set")
        else:
            self.label.setText(f"Selected: {value.capitalize()}")

    def custom_style(self):
        return """
        QPushButton {
            border: 3px solid #1565c0;
            border-radius: 12px;
            padding: 5px 10px;
            background-color: #ffffff;
            color: #1565c0;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e0f0ff;
        }
        QPushButton:pressed {
            background-color: #c0e0ff;
        }
        QPushButton:checked {
            background-color: #2980f0;
            color: #ffffff;
            border: 3px solid #1565c0;
        }
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GenderSelector()
    window.setWindowTitle("Gender Toggle")
    window.show()
    sys.exit(app.exec_())
