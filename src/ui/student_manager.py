from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from src.logic.db_interface import update_student, insert_student, get_students_by_class, delete_student
from src.ui.student_form import StudentForm
from logic.db_interface import get_form_settings, get_all_defaults, get_message_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

def validate_student_data(student_data: dict) -> bool:
    """Validate the student data before adding."""
    required_fields = ["name", "gender", "active"]
    for field in required_fields:
        if field not in student_data or not student_data[field]:
            QMessageBox.warning(None, "Invalid Data", f"Field '{field}' is required.")
            return False

    # Ensure the attendance field is initialized if missing
    if "attendance" not in student_data:
        student_data["attendance"] = {}

    return True

def show_message_dialog(parent, message, timeout=2000):
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
    from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
    from PyQt5.QtCore import Qt
    msg_dialog = QDialog(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
    msg_dialog.setModal(False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(message)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    msg_dialog.adjustSize()
    # Center the dialog on the parent
    parent_geo = parent.geometry()
    msg_dialog.move(parent.mapToGlobal(parent_geo.center()) - msg_dialog.rect().center())
    msg_dialog.show()
    QTimer.singleShot(timeout, msg_dialog.accept)

class StudentManager(QDialog):
    def __init__(self, parent, data, class_id, refresh_callback):
        super().__init__(parent)
        self.data = data
        self.class_id = class_id
        self.refresh_callback = refresh_callback

        # --- PATCH: Load students from DB ---
        self.students = {row["student_id"]: row for row in get_students_by_class(self.class_id)}
        self.row_to_student_id = []

        self.setWindowTitle("Student Manager")
        form_settings = get_form_settings("StudentManager") or {}
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.resize(800, 600)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        else:
            self.setMinimumSize(300, 200)
        # Remove legacy max_width and max_height logic
        # --- FONT SIZE PATCH: Set default font size from per-form or global settings ---
        default_settings = get_all_defaults()
        font_size = int(form_settings.get("font_size") or default_settings.get("form_font_size", default_settings.get("button_font_size", 12)))
        font_family = form_settings.get("font_family", "Segoe UI")
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont(font_family, font_size))
        self.form_font = QFont(font_family, font_size)
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            display_settings = get_all_defaults()
            scale = str(display_settings.get("scale_windows", "1")) == "1"
            center = str(display_settings.get("center_windows", "1")) == "1"
            width_ratio = float(display_settings.get("window_width_ratio", 0.6))
            height_ratio = float(display_settings.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        # --- PATCH END ---

        # Main layout
        layout = QVBoxLayout(self)

        # Table for students
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Nickname", "Company No", "Note", "Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # --- PATCH: Table style from DB ---
        table_bg = form_settings.get("table_bg_color", default_settings.get("table_bg_color", "#ffffff"))
        table_fg = form_settings.get("table_fg_color", default_settings.get("table_fg_color", "#222222"))
        table_header_bg = form_settings.get("table_header_bg_color", default_settings.get("table_header_bg_color", "#1976d2"))
        table_header_fg = form_settings.get("table_header_fg_color", default_settings.get("table_header_fg_color", "#ffffff"))
        self.table.setStyleSheet(f"background: {table_bg}; color: {table_fg}; font-family: {font_family}; font-size: {font_size}pt;")
        self.table.horizontalHeader().setStyleSheet(f"background: {table_header_bg}; color: {table_header_fg}; font-family: {font_family}; font-size: {font_size+2}pt; font-weight: bold;")
        self.populate_table()
        layout.addWidget(self.table)

        # Buttons (horizontal layout)
        button_layout = QHBoxLayout()
        # --- PATCH: Button style from DB ---
        button_bg = form_settings.get("button_bg_color", default_settings.get("button_bg_color", "#1976d2"))
        button_fg = form_settings.get("button_fg_color", default_settings.get("button_fg_color", "#ffffff"))
        button_font_size = int(form_settings.get("button_font_size", default_settings.get("button_font_size", 12)))
        button_font_bold = str(form_settings.get("button_font_bold", default_settings.get("button_font_bold", "no"))).lower() in ("yes", "true", "1")
        button_hover_bg = form_settings.get("button_hover_bg_color", default_settings.get("button_hover_bg_color", "#1565c0"))
        button_active_bg = form_settings.get("button_active_bg_color", default_settings.get("button_active_bg_color", "#0d47a1"))
        button_border = form_settings.get("button_border_color", default_settings.get("button_border_color", "#1976d2"))
        button_style = (
            f"QPushButton {{background: {button_bg}; color: {button_fg}; border: 2px solid {button_border}; font-size: {button_font_size}pt; font-weight: {'bold' if button_font_bold else 'normal'};}}"
            f"QPushButton:hover {{background: {button_hover_bg};}}"
            f"QPushButton:pressed {{background: {button_active_bg};}}"
        )

        toggle_active_button = QPushButton("Toggle Active Status")
        toggle_active_button.setFont(self.form_font)
        toggle_active_button.setStyleSheet(button_style)
        toggle_active_button.clicked.connect(self.toggle_active_status)
        button_layout.addWidget(toggle_active_button)

        delete_button = QPushButton("Delete Student")
        delete_button.setFont(self.form_font)
        delete_button.setStyleSheet(button_style)
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(delete_button)

        edit_button = QPushButton("Edit Student")
        edit_button.setFont(self.form_font)
        edit_button.setStyleSheet(button_style)
        edit_button.clicked.connect(self.edit_student)
        button_layout.addWidget(edit_button)

        close_button = QPushButton("Close")
        close_button.setFont(self.form_font)
        close_button.setStyleSheet(button_style)
        close_button.clicked.connect(self.close_manager)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def populate_table(self):
        # --- PATCH: Reload students from DB ---
        self.students = {row["student_id"]: row for row in get_students_by_class(self.class_id)}
        self.table.setRowCount(0)
        self.row_to_student_id = []
        for student_id, student_data in self.students.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.row_to_student_id.append(student_id)
            # Name
            item_name = QTableWidgetItem(student_data.get("name", "Unknown"))
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 0, item_name)
            # Nickname
            item_nick = QTableWidgetItem(student_data.get("nickname", ""))
            item_nick.setFlags(item_nick.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 1, item_nick)
            # Company No
            item_company = QTableWidgetItem(student_data.get("company_no", ""))
            item_company.setFlags(item_company.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 2, item_company)
            # Note
            item_note = QTableWidgetItem(student_data.get("note", ""))
            item_note.setFlags(item_note.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 3, item_note)
            # Active
            item_active = QTableWidgetItem(student_data.get("active", "No"))
            item_active.setFlags(item_active.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_position, 4, item_active)

    def toggle_active_status(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            show_message_dialog(self, "Please select a student to toggle status.")
            return
        for idx in selected_rows:
            row = idx.row()
            student_id = self.row_to_student_id[row]
            current_status = self.students[student_id].get("active", "No")
            new_status = "No" if current_status == "Yes" else "Yes"
            self.students[student_id]["active"] = new_status
            # --- PATCH: Update in DB ---
            update_student(student_id, self.students[student_id])
        self.populate_table()
        self.refresh_callback()

    def delete_student(self):
        """Delete the selected student(s) if they are inactive."""
        selected_rows = set(idx.row() for idx in self.table.selectionModel().selectedRows())
        if not selected_rows:
            show_message_dialog(self, "Please select one or more students to delete.")
            return

        # Gather student IDs to delete, but only if Active == "No"
        deletable_ids = []
        undeletable_names = []
        for row in selected_rows:
            student_id = self.row_to_student_id[row]
            student = self.students[student_id]
            if student.get("active", "No") == "No":
                deletable_ids.append(student_id)
            else:
                undeletable_names.append(student.get("name", student_id))

        if not deletable_ids:
            show_message_dialog(self, "Only students with Active = No can be deleted.\nToggle Student Active Status = No then delete.")
            return

        # Confirm deletion
        confirm = QMessageBox.warning(
            self,
            "Delete Student(s)",
            f"Deleting these students will remove all data and is unrecoverable.\nAre you sure you want to delete {len(deletable_ids)} student(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            for student_id in deletable_ids:
                # --- PATCH: Delete from DB ---
                delete_student(student_id)
            self.populate_table()
            self.refresh_callback()

            if undeletable_names:
                show_message_dialog(self, "The following students were not deleted because they are still active:\n" + "\n".join(undeletable_names))

    def edit_student(self):
        """Edit the selected student using StudentForm."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) != 1:
            show_message_dialog(self, "Please select a single student to edit.")
            return
        row = selected_rows[0].row()
        student_id = self.row_to_student_id[row]
        student_data = self.students[student_id]
        form = StudentForm(self, self.class_id, self.data, self.refresh_callback, student_id=student_id, student_data=student_data)
        form.exec_()
        self.populate_table()

    def close_manager(self):
        """Close the StudentManager."""
        self.refresh_callback()
        self.accept()

    def closeEvent(self, event):
        """Restore the initial size when the StudentManager is reopened."""
        self.resize(500, 300)
        super().closeEvent(event)
