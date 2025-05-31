from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QSpacerItem, QSizePolicy, QFrame, QWidget
)

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Spacer & Stylish Lines Demo")
        self.setGeometry(100, 100, 300, 300)

        layout = QVBoxLayout()

        # First button
        layout.addWidget(QPushButton("Top Button"))

        # Spacer using QSpacerItem (fixed vertical space)
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        # Separator Option 1: QFrame with sunken shadow
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("color: #888;")
        line1.setFixedHeight(3)
        layout.addWidget(line1)

        # Second button
        layout.addWidget(QPushButton("Middle Button"))

        # Separator Option 2: QWidget with rounded rectangle
        line2 = QWidget()
        line2.setFixedHeight(4)
        line2.setStyleSheet("background-color: #666; border-radius: 2px;")
        layout.addWidget(line2)

        # Spacer using addStretch() (stretchable space)
        layout.addStretch()

        # Separator Option 3: QWidget with gradient
        line3 = QWidget()
        line3.setFixedHeight(5)
        line3.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #aaa, stop:0.5 #666, stop:1 #aaa);
            border-radius: 2px;
        """)
        layout.addWidget(line3)

        # Third button
        layout.addWidget(QPushButton("Bottom Button"))

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])
    window = MyWindow()
    window.show()
    app.exec_()
