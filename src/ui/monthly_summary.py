import json
import os
from datetime import datetime
from collections import defaultdict
from logic.db_interface import get_all_classes, get_students_by_class, get_attendance_by_student, get_all_defaults, get_message_defaults, get_form_settings
from logic.display import center_widget, scale_and_center, apply_window_flags
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QDialog
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer

def is_attended(value):
    """Check if an attendance value counts as a class held."""
    return value in ("P", "COD", "CIA")  # Add others if needed

def generate_monthly_summary(teacher_name="Paul R"):
    """
    Build a monthly summary across all classes taught by a given teacher.

    Returns:
        Dict of the form:
        {
            "2025-05": {
                "total_hours": 20,
                "total_travel": 4000,
                "total_bonus": 1000,
                "total_pay": 15400,
                "notes": "1 class"
            },
            ...
        }
    """
    summary = defaultdict(lambda: {
        "total_hours": 0,
        "total_travel": 0,
        "total_bonus": 0,
        "total_pay": 0,
        "notes": set()
    })

    for class_row in get_all_classes():
        if class_row.get("teacher") != teacher_name:
            continue

        class_time = float(class_row.get("class_time", "2"))
        rate = float(class_row.get("rate", "0"))
        travel_rate = float(class_row.get("travel", "0"))
        bonus_amount = float(class_row.get("bonus", "0"))
        dates = class_row.get("dates", [])
        class_name = class_row.get("company", class_row.get("class_no", ""))

        # Get all students for this class
        students = get_students_by_class(class_row["class_no"])

        # Count actual held sessions per date
        class_dates_by_month = defaultdict(int)
        for date_str in dates:
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                month_key = dt.strftime("%Y-%m")

                # Check if at least one student attended
                any_attended = False
                for student in students:
                    attendance_records = get_attendance_by_student(student["student_id"])
                    attendance = {rec["date"]: rec["status"] for rec in attendance_records}
                    if is_attended(attendance.get(date_str, "")):
                        any_attended = True
                        break

                if any_attended:
                    class_dates_by_month[month_key] += 1
            except ValueError:
                continue

        # Now summarize for each month where this class had sessions
        for month, count in class_dates_by_month.items():
            hours = count * class_time
            travel = count * travel_rate
            # If you have a lowercase "bonus_claimed" field, use that; otherwise, remove this logic or adapt as needed
            bonus = bonus_amount if class_row.get("bonus_claimed", "") == month else 0
            pay = hours * rate + travel + bonus

            summary[month]["total_hours"] += hours
            summary[month]["total_travel"] += travel
            summary[month]["total_bonus"] += bonus
            summary[month]["total_pay"] += pay
            summary[month]["notes"].add(class_name)

    # Final formatting
    for month in summary:
        summary[month]["notes"] = f"{len(summary[month]['notes'])} class(es)"

    return summary

def get_summary_text(teacher_name="Paul R"):
    summary = generate_monthly_summary(teacher_name)
    lines = []
    lines.append(f"{'Month':<10} {'Hours':<6} {'Travel':<8} {'Bonus':<7} {'Total Pay':<10} {'Notes'}")
    lines.append("-" * 60)
    for month in sorted(summary):
        row = summary[month]
        lines.append(f"{month:<10} {row['total_hours']:<6} {row['total_travel']:<8} {row['total_bonus']:<7} {row['total_pay']:<10} {row['notes']}")
    return "\n".join(lines)

# Floating message dialog for future use (DB-driven style)
def show_message_dialog(parent, message, timeout=2000, buttons=None):
    msg_defaults = get_message_defaults()
    bg = msg_defaults.get("message_bg_color", "#2980f0")
    fg = msg_defaults.get("message_fg_color", "#fff")
    border = msg_defaults.get("message_border_color", "#1565c0")
    border_width = msg_defaults.get("message_border_width", "3")
    border_radius = msg_defaults.get("message_border_radius", "12")
    padding = msg_defaults.get("message_padding", "18px 32px")
    font_size = msg_defaults.get("message_font_size", "13")
    font_bold = msg_defaults.get("message_font_bold", "true")
    font_weight = "bold" if str(font_bold).lower() in ("1", "true", "yes") else "normal"
    style = f"background: {bg}; color: {fg}; border: {border_width}px solid {border}; padding: {padding}; font-size: {font_size}pt; font-weight: {font_weight}; border-radius: {border_radius}px;"
    msg_dialog = QDialog(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
    msg_dialog.setModal(True if buttons else False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(message)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    if buttons:
        btn_row = QHBoxLayout()
        for btn_text, btn_callback in buttons:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(f"background: {bg}; color: {fg}; border-radius: {border_radius}px; font-size: {font_size}pt; font-weight: {font_weight}; padding: 6px 18px;")
            btn.clicked.connect(lambda _, cb=btn_callback: (msg_dialog.accept(), cb() if cb else None))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)
    msg_dialog.adjustSize()
    parent_geo = parent.geometry() if parent else None
    if parent_geo:
        msg_dialog.move(parent.mapToGlobal(parent_geo.center()) - msg_dialog.rect().center())
    msg_dialog.show()
    if not buttons:
        QTimer.singleShot(timeout, msg_dialog.accept)
    else:
        msg_dialog.exec_()

class MonthlySummaryWindow(QWidget):
    def __init__(self, teacher_name="Paul R"):
        super().__init__()
        # --- PATCH: Set a default window icon to avoid '?' on Windows ---
        self.setWindowIcon(QIcon())  # Set your app icon here if you have one
        # --- PATCH: Load per-form and global settings from DB ---
        form_settings = get_form_settings("MonthlySummaryWindow") or get_all_defaults()
        font_family = form_settings.get("form_font_family", "Segoe UI")
        font_size = int(form_settings.get("form_font_size", 12))
        self.form_font = QFont(font_family, font_size)
        self.setFont(self.form_font)
        win_w = int(form_settings.get("window_width", 700))
        win_h = int(form_settings.get("window_height", 500))
        resizable = str(form_settings.get("resizable", "yes")).lower() in ("yes", "true", "1")
        window_controls = form_settings.get("window_controls", "standard")
        # --- PATCH: Set window flags (with Qt.Window) before any sizing ---
        flags = Qt.Window
        if window_controls == "standard":
            flags |= Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        else:
            flags |= Qt.WindowCloseButtonHint
            flags &= ~Qt.WindowMaximizeButtonHint
        # --- PATCH: Remove the '?' help button by clearing Qt.WindowContextHelpButtonHint ---
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        if resizable:
            self.setMinimumSize(300, 200)
            self.resize(win_w, win_h)
        else:
            self.setFixedSize(win_w, win_h)
        self.setWindowTitle("TTR Monthly Summary")
        # --- REMOVE FORCE MAXIMIZE ON OPEN ---
        # QTimer.singleShot(0, self.showMaximized)
        # --- PATCH: Apply display preferences ---
        scale = str(form_settings.get("scale_windows", "1")) == "1"
        center = str(form_settings.get("center_windows", "1")) == "1"
        width_ratio = float(form_settings.get("window_width_ratio", 0.6))
        height_ratio = float(form_settings.get("window_height_ratio", 0.6))
        if scale:
            scale_and_center(self, width_ratio, height_ratio)
        elif center:
            center_widget(self)
        # --- PATCH: Set background and label styles from DB ---
        bg_color = form_settings.get("form_bg_color", "#e3f2fd")
        fg_color = form_settings.get("form_fg_color", "#222222")
        self.setStyleSheet(f"background: {bg_color}; color: {fg_color};")
        # Layout
        layout = QVBoxLayout(self)
        summary_text = get_summary_text(teacher_name)
        label = QLabel(summary_text)
        label.setFont(self.form_font)
        label.setStyleSheet(f"color: {fg_color}; font-size: {font_size}pt;")
        label.setTextInteractionFlags(label.textInteractionFlags() | Qt.TextSelectableByMouse)
        layout.addWidget(label)
        close_btn = QPushButton("Close")
        close_btn.setFont(self.form_font)
        button_bg = form_settings.get("button_bg_color", "#1976d2")
        button_fg = form_settings.get("button_fg_color", "#ffffff")
        button_font_size = int(form_settings.get("button_font_size", 12))
        button_font_bold = str(form_settings.get("button_font_bold", "no")).lower() in ("yes", "true", "1")
        button_hover_bg = form_settings.get("button_hover_bg_color", "#1565c0")
        button_active_bg = form_settings.get("button_active_bg_color", "#0d47a1")
        button_border = form_settings.get("button_border_color", "#1976d2")
        button_style = (
            f"QPushButton {{background: {button_bg}; color: {button_fg}; border: 2px solid {button_border}; font-size: {button_font_size}pt; font-weight: {'bold' if button_font_bold else 'normal'};}}"
            f"QPushButton:hover {{background: {button_hover_bg};}}"
            f"QPushButton:pressed {{background: {button_active_bg};}}"
        )
        close_btn.setStyleSheet(button_style)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
