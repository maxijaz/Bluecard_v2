from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QApplication, QInputDialog, QMenu, QWidget, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QItemSelectionModel
from PyQt5.QtGui import QFont, QColor
from logic.parser import save_data
from logic.db_interface import insert_student, update_student, get_students_by_class, get_all_defaults, get_form_settings, get_message_defaults
from logic.display import center_widget, scale_and_center, apply_window_flags

class StudentForm(QDialog):
    def __init__(self, parent, class_id, data, refresh_callback, student_id=None, student_data=None, default_attendance=None):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.refresh_callback = refresh_callback
        self.student_id = student_id
        self.student_data = student_data or {}
        self.default_attendance = default_attendance

        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("StudentForm") or {}
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
        max_w = form_settings.get("max_width")
        max_h = form_settings.get("max_height")
        if max_w and max_h:
            self.setMaximumSize(int(max_w), int(max_h))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # --- FONT SIZE PATCH: Set default font size from per-form or global settings ---
        default_settings = get_all_defaults()
        font_size = int(form_settings.get("window_width") or default_settings.get("form_font_size", default_settings.get("button_font_size", 12)))
        font_family = form_settings.get("font_family", "Segoe UI")
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont
        QApplication.instance().setFont(QFont(font_family, font_size))
        # Set form font attributes for use in widgets
        self.form_font_size = font_size
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

        # --- Layouts ---
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)

        # Row 0
        grid.addWidget(self.bold_label("Name:"), 0, 0, alignment=Qt.AlignTop)
        self.name_entry = QLineEdit(student_data.get("name", "") if student_data else "")
        self.name_entry.setFont(self.form_font)
        grid.addWidget(self.name_entry, 0, 1, alignment=Qt.AlignTop)

        # Row 1
        grid.addWidget(self.bold_label("Nickname:"), 1, 0, alignment=Qt.AlignTop)
        self.nickname_entry = QLineEdit(student_data.get("nickname", "") if student_data else "")
        self.nickname_entry.setFont(self.form_font)
        grid.addWidget(self.nickname_entry, 1, 1, alignment=Qt.AlignTop)

        # Row 2
        grid.addWidget(self.bold_label("Company No:"), 2, 0, alignment=Qt.AlignTop)
        self.company_no_entry = QLineEdit(student_data.get("company_no", "") if student_data else "")
        self.company_no_entry.setFont(self.form_font)
        grid.addWidget(self.company_no_entry, 2, 1, alignment=Qt.AlignTop)

        # Row 3
        grid.addWidget(self.bold_label("Gender:"), 3, 0, alignment=Qt.AlignVCenter)
        gender_layout = QHBoxLayout()
        self.male_radio = QRadioButton("Male")
        self.male_radio.setFont(self.form_font)
        self.female_radio = QRadioButton("Female")
        self.female_radio.setFont(self.form_font)
        if student_data:
            if student_data.get("gender", "Female") == "Male":
                self.male_radio.setChecked(True)
            else:
                self.female_radio.setChecked(True)
        else:
            self.female_radio.setChecked(True)
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        gender_widget = QWidget()
        gender_widget.setLayout(gender_layout)
        gender_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grid.addWidget(gender_widget, 3, 1, alignment=Qt.AlignVCenter)

        # Row 4
        grid.addWidget(self.bold_label("Score:"), 4, 0, alignment=Qt.AlignTop)
        self.score_entry = QLineEdit(student_data.get("score", "") if student_data else "")
        self.score_entry.setFont(self.form_font)
        grid.addWidget(self.score_entry, 4, 1, alignment=Qt.AlignTop)

        # Row 5
        grid.addWidget(self.bold_label("Pre-Test:"), 5, 0, alignment=Qt.AlignTop)
        self.pre_test_entry = QLineEdit(student_data.get("pre_test", "") if student_data else "")
        self.pre_test_entry.setFont(self.form_font)
        grid.addWidget(self.pre_test_entry, 5, 1, alignment=Qt.AlignTop)

        # Row 6
        grid.addWidget(self.bold_label("Post-Test:"), 6, 0, alignment=Qt.AlignTop)
        self.post_test_entry = QLineEdit(student_data.get("post_test", "") if student_data else "")
        self.post_test_entry.setFont(self.form_font)
        grid.addWidget(self.post_test_entry, 6, 1, alignment=Qt.AlignTop)

        # Row 7
        grid.addWidget(self.bold_label("Note:"), 7, 0, alignment=Qt.AlignTop)
        self.note_entry = QLineEdit(student_data.get("note", "") if student_data else "")
        self.note_entry.setFont(self.form_font)
        grid.addWidget(self.note_entry, 7, 1, alignment=Qt.AlignTop)

        # Row 8
        grid.addWidget(self.bold_label("Active:"), 8, 0, alignment=Qt.AlignVCenter)
        active_layout = QHBoxLayout()
        self.active_yes = QRadioButton("Yes")
        self.active_yes.setFont(self.form_font)
        self.active_no = QRadioButton("No")
        self.active_no.setFont(self.form_font)
        if student_data:
            if student_data.get("active", "Yes") == "Yes":
                self.active_yes.setChecked(True)
            else:
                self.active_no.setChecked(True)
        else:
            self.active_yes.setChecked(True)
        active_layout.addWidget(self.active_yes)
        active_layout.addWidget(self.active_no)
        active_widget = QWidget()
        active_widget.setLayout(active_layout)
        active_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grid.addWidget(active_widget, 8, 1, alignment=Qt.AlignVCenter)

        main_layout.addLayout(grid)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setFont(self.form_font)
        save_button.clicked.connect(self.save_student)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(self.form_font)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        cancel_button.setDefault(True)  # Set Cancel as the default button
        save_button.setAutoDefault(False)
        save_button.setDefault(False)

        bulk_import_button = QPushButton("Bulk Import")
        bulk_import_button.setFont(self.form_font)
        bulk_import_button.clicked.connect(self.open_bulk_import_and_close)
        button_layout.addWidget(bulk_import_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setSizeGripEnabled(False)

        # If adding a new student and default_attendance is provided, set it
        if self.student_id is None and self.default_attendance is not None:
            self.student_data["attendance"] = dict(self.default_attendance)

        # Flag to track if bulk import was requested
        self.bulk_import_requested = False

    def bold_label(self, text):
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        font.setPointSize(self.form_font_size)
        label.setFont(font)
        return label

    def show_message_dialog(self, message, timeout=2000):
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
        msg_dialog = QDialog(self, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        msg_dialog.setAttribute(Qt.WA_TranslucentBackground)
        msg_dialog.setModal(False)
        layout = QVBoxLayout(msg_dialog)
        label = QLabel(message)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        msg_dialog.adjustSize()
        # Center the dialog on the parent
        parent_geo = self.geometry()
        msg_dialog.move(self.mapToGlobal(parent_geo.center()) - msg_dialog.rect().center())
        msg_dialog.show()
        QTimer.singleShot(timeout, msg_dialog.accept)

    def save_student(self):
        """Save the student data."""
        name = self.capitalize_words(self.name_entry.text().strip())
        nickname = self.capitalize_words(self.nickname_entry.text().strip())
        company_no = self.company_no_entry.text().strip()
        gender = "Male" if self.male_radio.isChecked() else "Female"
        score = self.score_entry.text().strip()
        pre_test = self.pre_test_entry.text().strip()
        post_test = self.post_test_entry.text().strip()
        note = self.note_entry.text().strip()
        active = "Yes" if self.active_yes.isChecked() else "No"

        if not name:
            self.show_message_dialog("Name is required.")
            return

        if self.student_id:
            # Edit existing student
            student_record = {
                "student_id": self.student_id,
                "class_no": self.class_id,
                "name": name,
                "nickname": nickname,
                "company_no": company_no,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                # Attendance is handled in a separate table; update if needed
            }
            update_student(self.student_id, student_record)
        else:
            # Add new student
            student_id = self.generate_unique_student_id()
            student_record = {
                "student_id": student_id,
                "class_no": self.class_id,
                "name": name,
                "nickname": nickname,
                "company_no": company_no,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                # Attendance is handled in a separate table; insert if needed
            }
            insert_student(student_record)

        self.refresh_callback()
        self.accept()

    def generate_unique_student_id(self):
        """Generate a unique Student ID."""
        existing_ids = [row["student_id"] for row in get_students_by_class(self.class_id)]
        idx = 1
        while True:
            student_id = f"S{str(idx).zfill(3)}"
            if student_id not in existing_ids:
                return student_id
            idx += 1

    def open_bulk_import_dialog(self):
        # --- Load per-form settings for BulkImportStudents ---
        form_settings = get_form_settings("BulkImportStudents") or {}
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        resizable = str(form_settings.get("resizable", "yes")).lower() in ("yes", "true", "1")
        window_controls = form_settings.get("window_controls", "standard")
        font_family = form_settings.get("form_font_family", "Segoe UI")
        font_size = int(form_settings.get("form_font_size", 12))
        bg_color = form_settings.get("form_bg_color", "#e3f2fd")
        fg_color = form_settings.get("form_fg_color", "#222222")
        border_color = form_settings.get("form_border_color", "#1976d2")
        table_header_bg = form_settings.get("table_header_bg_color", "#1976d2")
        table_header_fg = form_settings.get("table_header_fg_color", "#ffffff")
        table_bg = form_settings.get("table_bg_color", "#ffffff")
        table_fg = form_settings.get("table_fg_color", "#222222")
        button_bg = form_settings.get("button_bg_color", "#1976d2")
        button_fg = form_settings.get("button_fg_color", "#ffffff")
        button_font_size = int(form_settings.get("button_font_size", 12))
        button_font_bold = str(form_settings.get("button_font_bold", "no")).lower() in ("yes", "true", "1")
        button_hover_bg = form_settings.get("button_hover_bg_color", "#1565c0")
        button_active_bg = form_settings.get("button_active_bg_color", "#0d47a1")
        button_border = form_settings.get("button_border_color", "#1976d2")
        button_style = (
            f"QPushButton {{background: {button_bg}; color: {button_fg}; border: 2px solid {button_border};}}"
            f"QPushButton:hover {{background: {button_hover_bg};}}"
            f"QPushButton:pressed {{background: {button_active_bg};}}"
        )

        class BulkImportTable(QTableWidget):
            def __init__(self, parent, paste_callback, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.parent = parent
                self.paste_callback = paste_callback
                self.setContextMenuPolicy(Qt.CustomContextMenu)
                self.customContextMenuRequested.connect(self.open_context_menu)
                # Table style
                self.setStyleSheet(f"background: {table_bg}; color: {table_fg}; font-family: {font_family}; font-size: {font_size}pt;")
                self.horizontalHeader().setStyleSheet(f"background: {table_header_bg}; color: {table_header_fg}; font-family: {font_family}; font-size: {font_size+2}pt; font-weight: bold;")
                # Don't delete this comment or next 4 lines, they are important
                # click cell highlight row automatically - next 3 lines changes behaviour
                # self.setSelectionBehavior(QTableWidget.SelectRows) # 1. Select entire rows
                self.setSelectionBehavior(QTableWidget.SelectItems) # 2. Select individual items
                self.setSelectionMode(QTableWidget.SingleSelection)  # choose 1 or 2 inlcude: ExtendedSelection for multi-select
                self.setAlternatingRowColors(True)
                self.setEditTriggers(QTableWidget.NoEditTriggers)
                self.setShowGrid(True)
                self.setWordWrap(False)
                self.horizontalHeader().setStretchLastSection(True)
                self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                # Pre-populate all cells with empty QTableWidgetItems (no highlight)
                for r in range(self.rowCount()):
                    for c in range(self.columnCount()):
                        if not self.item(r, c):
                            item = QTableWidgetItem("")
                            item.setBackground(Qt.white)
                            self.setItem(r, c, item)
                # --- Add double-click delete row/column logic ---
                self.verticalHeader().sectionDoubleClicked.connect(self.confirm_delete_row)
                self.horizontalHeader().sectionDoubleClicked.connect(self.confirm_delete_column)
                self.horizontalHeader().sectionClicked.connect(self.highlight_column)
                self.verticalHeader().sectionClicked.connect(self.highlight_row)
                # Set a fixed minimum row height for all rows
                min_row_height = 28  # or fetch from settings if desired
                for r in range(self.rowCount()):
                    self.setRowHeight(r, min_row_height)

            def keyPressEvent(self, event):
                if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
                    self.paste_callback(self)
                else:
                    super().keyPressEvent(event)

            def open_context_menu(self, position):
                menu = QMenu(self)
                paste_action = menu.addAction("Paste")
                paste_action.triggered.connect(lambda: self.paste_callback(self))
                menu.exec_(self.viewport().mapToGlobal(position))

            def confirm_delete_row(self, row):
                from PyQt5.QtWidgets import QMessageBox
                # Set default button to No for safety
                reply = QMessageBox.question(
                    self, "Delete Row", f"Delete row {row+1}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.removeRow(row)

            def confirm_delete_column(self, col):
                from PyQt5.QtWidgets import QMessageBox
                header = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else f"Column {col+1}"
                # Set default button to No for safety
                reply = QMessageBox.question(
                    self, "Clear Column", f"Clear all data in column '{header}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    for row in range(self.rowCount()):
                        self.setItem(row, col, QTableWidgetItem(""))

            def highlight_column(self, col):
                # If already highlighted, remove highlight and return
                already_highlighted = all(
                    self.item(row, col) and self.item(row, col).background().color().name() == '#2196f3'
                    for row in range(self.rowCount())
                )
                if already_highlighted:
                    for row in range(self.rowCount()):
                        item = self.item(row, col)
                        if item:
                            item.setBackground(Qt.white)
                        else:
                            new_item = QTableWidgetItem("")
                            new_item.setBackground(Qt.white)
                            self.setItem(row, col, new_item)
                    return
                # Remove previous highlights
                for c in range(self.columnCount()):
                    for r in range(self.rowCount()):
                        item = self.item(r, c)
                        if item:
                            item.setBackground(Qt.white)
                        else:
                            new_item = QTableWidgetItem("")
                            new_item.setBackground(Qt.white)
                            self.setItem(r, c, new_item)
                # Highlight selected column (blue)
                for row in range(self.rowCount()):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(QColor('#2196f3'))
                    else:
                        new_item = QTableWidgetItem("")
                        new_item.setBackground(QColor('#2196f3'))
                        self.setItem(row, col, new_item)

            def highlight_row(self, row):
                # If already highlighted, remove highlight and return
                is_highlighted = all(
                    self.item(row, col) and self.item(row, col).background().color().name() == '#2196f3'
                    for col in range(self.columnCount())
                )
                if is_highlighted:
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item:
                            item.setBackground(Qt.white)
                        else:
                            new_item = QTableWidgetItem("")
                            new_item.setBackground(Qt.white)
                            self.setItem(row, col, new_item)
                    self.selectionModel().select(self.model().index(row, 0), QItemSelectionModel.Deselect | QItemSelectionModel.Rows)
                    return
                # Remove previous highlights
                self.clear_row_highlights()
                self.clear_column_highlights()
                # Highlight selected row (blue)
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        item.setBackground(QColor('#2196f3'))
                    else:
                        new_item = QTableWidgetItem("")
                        new_item.setBackground(QColor('#2196f3'))
                        self.setItem(row, col, new_item)
                self.selectRow(row)

            def mousePressEvent(self, event):
                index = self.indexAt(event.pos())
                row = index.row()
                col = index.column()

                # Row header click
                if event.button() == Qt.LeftButton and col == -1 and row >= 0:
                    self.clear_column_highlights()
                    # Toggle row highlight: if already highlighted, clear; else, highlight
                    is_highlighted = all(
                        self.item(row, c) and self.item(row, c).background().color().name() == '#2196f3'
                        for c in range(self.columnCount())
                    )
                    if is_highlighted:
                        self.clear_row_highlights()
                    else:
                        self.clear_row_highlights()
                        self.highlight_row(row)
                    return

                # Column header click
                if event.button() == Qt.LeftButton and row == -1 and col >= 0:
                    self.clear_row_highlights()
                    # Toggle column highlight: if already highlighted, clear; else, highlight
                    is_highlighted = all(
                        self.item(r, col) and self.item(r, col).background().color().name() == '#2196f3'
                        for r in range(self.rowCount())
                    )
                    if is_highlighted:
                        self.clear_column_highlights()
                    else:
                        self.clear_column_highlights()
                        self.highlight_column(col)
                    return

                # Table cell click: just move the focus (dotted box), do not clear or set any highlight
                if event.button() == Qt.LeftButton and index.isValid():
                    self.setCurrentIndex(index)
                    # Do NOT clear or set any row/column highlight here!
                    return

                super().mousePressEvent(event)

            def clear_row_highlights(self):
                for row in range(self.rowCount()):
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item and item.background().color().name() == '#2196f3':
                            item.setBackground(Qt.white)

            def clear_column_highlights(self):
                for col in range(self.columnCount()):
                    for row in range(self.rowCount()):
                        item = self.item(row, col)
                        if item and item.background().color().name() == '#2196f3':
                            item.setBackground(Qt.white)

            def mouseDoubleClickEvent(self, event):
                # Double click row header: offer to clear row
                if event.button() == Qt.LeftButton and self.indexAt(event.pos()).column() == -1:
                    row = self.indexAt(event.pos()).row()
                    if row >= 0:
                        from PyQt5.QtWidgets import QMessageBox
                        reply = QMessageBox.question(
                            self, "Clear Row", f"Clear all data in row {row+1}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            for col in range(self.columnCount()):
                                self.setItem(row, col, QTableWidgetItem(""))
                            # Keep row highlighted after clear
                            for col in range(self.columnCount()):
                                item = self.item(row, col)
                                if item:
                                    item.setBackground(QColor('#2196f3'))
                                else:
                                    new_item = QTableWidgetItem("")
                                    new_item.setBackground(QColor('#2196f3'))
                                    self.setItem(row, col, new_item)
                    return
                # Only allow edit on double click in table cells
                if event.button() == Qt.LeftButton and self.indexAt(event.pos()).isValid() and self.indexAt(event.pos()).column() != -1:
                    self.setEditTriggers(QTableWidget.AllEditTriggers)
                    self.edit(self.indexAt(event.pos()))
                    self.setEditTriggers(QTableWidget.NoEditTriggers)
                    return
                super().mouseDoubleClickEvent(event)

        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Import Students")
        if win_w and win_h:
            dialog.resize(int(win_w), int(win_h))
        if min_w and min_h:
            dialog.setMinimumSize(int(min_w), int(min_h))
        dialog.setStyleSheet(f"background: {bg_color}; color: {fg_color}; border: 2px solid {border_color}; font-family: {font_family}; font-size: {font_size}pt;")
        if resizable:
            dialog.setSizeGripEnabled(True)
        else:
            dialog.setSizeGripEnabled(False)
        if window_controls == "standard":
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        else:
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(dialog)

        info_label = QLabel("Paste up to 150 students data from Excel below (columns: Name, Nickname, Company No, Gender, Score, Pre-Test, Post-Test, Note).")
        info_label.setFont(QFont(font_family, font_size))
        layout.addWidget(info_label)

        table = BulkImportTable(self, self.paste_from_clipboard, 25, 8)
        table.setHorizontalHeaderLabels([
            "Name", "Nickname", "Company No", "Gender", "Score", "Pre-Test", "Post-Test", "Note"
        ])
        layout.addWidget(table)

        # --- Buttons in a row, consistent order ---
        button_row = QHBoxLayout()
        save_button = QPushButton("Save Imported Students")
        save_button.setFont(QFont(font_family, button_font_size, QFont.Bold if button_font_bold else QFont.Normal))
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(lambda: self.save_bulk_import(table, dialog))
        button_row.addWidget(save_button)

        paste_button = QPushButton("Paste from Clipboard (Ctrl+V)")
        paste_button.setFont(QFont(font_family, button_font_size, QFont.Bold if button_font_bold else QFont.Normal))
        paste_button.setStyleSheet(button_style)
        paste_button.clicked.connect(lambda: self.paste_from_clipboard(table))
        button_row.addWidget(paste_button)

        clear_button = QPushButton("Clear All")
        clear_button.setFont(QFont(font_family, button_font_size, QFont.Bold if button_font_bold else QFont.Normal))
        clear_button.setStyleSheet(button_style)
        def clear_all():
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    table.setItem(row, col, QTableWidgetItem(""))
        clear_button.clicked.connect(clear_all)
        button_row.addWidget(clear_button)

        add_rows_button = QPushButton("Add Rows")
        add_rows_button.setFont(QFont(font_family, button_font_size, QFont.Bold if button_font_bold else QFont.Normal))
        add_rows_button.setStyleSheet(button_style)
        def add_more_rows():
            current_rows = table.rowCount()
            if current_rows >= 150:
                QMessageBox.warning(dialog, "Limit Reached", "Maximum of 150 rows allowed.")
                return
            rows_to_add, ok = QInputDialog.getInt(dialog, "Add Rows", "How many rows to add?", 10, 1, 150 - current_rows)
            if ok:
                table.setRowCount(min(150, current_rows + rows_to_add))
        add_rows_button.clicked.connect(add_more_rows)
        button_row.addWidget(add_rows_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(QFont(font_family, button_font_size, QFont.Bold if button_font_bold else QFont.Normal))
        cancel_button.setStyleSheet(button_style)
        cancel_button.clicked.connect(dialog.reject)
        button_row.addWidget(cancel_button)

        layout.addLayout(button_row)
        dialog.setLayout(layout)
        dialog.exec_()

    def paste_from_clipboard(self, table):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        rows = text.strip().split('\n')

        selected_ranges = table.selectedRanges()
        if selected_ranges and selected_ranges[0].columnCount() == 1:
            # Paste into the selected column
            col = selected_ranges[0].leftColumn()
            start_row = selected_ranges[0].topRow()
            for i, row_data in enumerate(rows):
                value = row_data.strip()
                if start_row + i < table.rowCount():
                    table.setItem(start_row + i, col, QTableWidgetItem(value))
        else:
            # Default: paste as a block
            for row_idx, row_data in enumerate(rows):
                columns = row_data.split('\t')
                for col_idx, value in enumerate(columns):
                    if row_idx < table.rowCount() and col_idx < table.columnCount():
                        table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def save_bulk_import(self, table, dialog):
        from logic.db_interface import insert_student

        headers = ["Name", "Nickname", "Company No", "Gender", "Score", "Pre-Test", "Post-Test", "Note"]

        for row in range(table.rowCount()):
            name_item = table.item(row, 0)
            if not name_item or not name_item.text().strip():
                continue  # Skip empty rows

            # --- Skip header row if pasted ---
            if name_item.text().strip().lower() == "name":
                continue
            if all(
                table.item(row, col) and table.item(row, col).text().strip().lower() == headers[col].lower()
                for col in range(table.columnCount())
            ):
                continue

            name = self.capitalize_words(name_item.text().strip())
            nickname = self.capitalize_words(table.item(row, 1).text().strip()) if table.item(row, 1) else ""
            company_no = table.item(row, 2).text().strip() if table.item(row, 2) else ""
            gender = table.item(row, 3).text().strip() if table.item(row, 3) else "Female"
            score = table.item(row, 4).text().strip() if table.item(row, 4) else ""
            pre_test = table.item(row, 5).text().strip() if table.item(row, 5) else ""
            post_test = table.item(row, 6).text().strip() if table.item(row, 6) else ""
            note = table.item(row, 7).text().strip() if table.item(row, 7) else ""

            student_id = self.generate_unique_student_id()
            student_record = {
                "student_id": student_id,
                "class_no": self.class_id,
                "name": name,
                "nickname": nickname,
                "company_no": company_no,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": "Yes",
                # Attendance is handled in a separate table; insert if needed
            }
            insert_student(student_record)

        self.refresh_callback()
        self.show_message_dialog("Students imported successfully!")
        dialog.accept()

    def capitalize_words(self, s):
        return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split())

    def open_bulk_import_and_close(self):
        self.bulk_import_requested = True
        self.reject()
        # Do NOT call QTimer or open_bulk_import_dialog here