from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont
import sys

# Simulated global theme config (could be loaded from your DB in Bluecard_v2)
theme = {
    "title_color": "#FF6F61",     # A strong coral red - good contrast
    "background_color": "#2E3440", # Dark bluish-gray background
    "font_family": "Segoe UI",
    "font_size": 18
}

class TitleForm(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Bluecardv2 Title Test")
        self.setStyleSheet(f"background-color: {theme['background_color']};")

        layout = QVBoxLayout()

        title = QLabel("Student Attendance Summary")
        title.setFont(QFont(theme["font_family"], theme["font_size"], weight=QFont.Bold))
        title.setStyleSheet(f"color: {theme['title_color']}; padding: 12px;")

        layout.addWidget(title)
        self.setLayout(layout)
        self.resize(400, 200)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = TitleForm()
    form.show()
    sys.exit(app.exec_())
