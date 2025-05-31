"""
ui_display.py (now logic/display.py)

Utility functions for handling window display behavior in Bluecard,
including centering, scaling, and enforcing size policies.

Call from any QWidget/QDialog after UI setup.
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt

def scale_and_center(widget: QWidget, width_ratio: float = 0.6, height_ratio: float = 0.6):
    screen = widget.screen().availableGeometry()
    width = int(screen.width() * width_ratio)
    height = int(screen.height() * height_ratio)
    widget.resize(width, height)
    widget.move(
        (screen.width() - width) // 2,
        (screen.height() - height) // 2
    )

def center_widget(widget: QWidget):
    screen = widget.screen().availableGeometry()
    widget.move(
        (screen.width() - widget.width()) // 2,
        (screen.height() - widget.height()) // 2
    )

def apply_window_flags(widget: QWidget, show_minimize: bool = True, show_maximize: bool = True):
    flags = widget.windowFlags()
    if not show_minimize:
        flags &= ~Qt.WindowMinimizeButtonHint
    if not show_maximize:
        flags &= ~Qt.WindowMaximizeButtonHint
    widget.setWindowFlags(flags)
    widget.show()
