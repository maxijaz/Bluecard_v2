from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QApplication, QInputDialog, QMenu, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt
from logic.parser import save_data

class StudentForm(QDialog):
    def __init__(self, parent, class_id, data, refresh_callback, student_id=None, student_data=None):
        super().__init__(parent)
        self.class_id = class_id
        self.data = data
        self.refresh_callback = refresh_callback
        self.student_id = student_id
        self.student_data = student_data

        self.setWindowTitle("Edit Student" if student_id else "Add Student")
        self.setFixedSize(300, 350)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)

        # Row 0
        grid.addWidget(self.bold_label("Name:"), 0, 0, alignment=Qt.AlignTop)
        self.name_entry = QLineEdit(student_data.get("name", "") if student_data else "")
        grid.addWidget(self.name_entry, 0, 1, alignment=Qt.AlignTop)

        # Row 1
        grid.addWidget(self.bold_label("Nickname:"), 1, 0, alignment=Qt.AlignTop)
        self.nickname_entry = QLineEdit(student_data.get("nickname", "") if student_data else "")
        grid.addWidget(self.nickname_entry, 1, 1, alignment=Qt.AlignTop)

        # Row 2
        grid.addWidget(self.bold_label("Company No:"), 2, 0, alignment=Qt.AlignTop)
        self.company_no_entry = QLineEdit(student_data.get("company_no", "") if student_data else "")
        grid.addWidget(self.company_no_entry, 2, 1, alignment=Qt.AlignTop)

        # Row 3
        grid.addWidget(self.bold_label("Gender:"), 3, 0, alignment=Qt.AlignVCenter)
        gender_layout = QHBoxLayout()
        self.male_radio = QRadioButton("Male")
        self.female_radio = QRadioButton("Female")
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
        grid.addWidget(self.score_entry, 4, 1, alignment=Qt.AlignTop)

        # Row 5
        grid.addWidget(self.bold_label("Pre-Test:"), 5, 0, alignment=Qt.AlignTop)
        self.pre_test_entry = QLineEdit(student_data.get("pre_test", "") if student_data else "")
        grid.addWidget(self.pre_test_entry, 5, 1, alignment=Qt.AlignTop)

        # Row 6
        grid.addWidget(self.bold_label("Post-Test:"), 6, 0, alignment=Qt.AlignTop)
        self.post_test_entry = QLineEdit(student_data.get("post_test", "") if student_data else "")
        grid.addWidget(self.post_test_entry, 6, 1, alignment=Qt.AlignTop)

        # Row 7
        grid.addWidget(self.bold_label("Note:"), 7, 0, alignment=Qt.AlignTop)
        self.note_entry = QLineEdit(student_data.get("note", "") if student_data else "")
        grid.addWidget(self.note_entry, 7, 1, alignment=Qt.AlignTop)

        # Row 8
        grid.addWidget(self.bold_label("Active:"), 8, 0, alignment=Qt.AlignVCenter)
        active_layout = QHBoxLayout()
        self.active_yes = QRadioButton("Yes")
        self.active_no = QRadioButton("No")
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
        save_button.clicked.connect(self.save_student)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        bulk_import_button = QPushButton("Bulk Import")
        bulk_import_button.clicked.connect(self.open_bulk_import_dialog)
        button_layout.addWidget(bulk_import_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setSizeGripEnabled(False)

    def bold_label(self, text):
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def save_student(self):
        """Save the student data."""
        name = self.capitalize_words(self.name_entry.text().strip())
        nickname = self.capitalize_words(self.nickname_entry.text().strip())
        gender = "Male" if self.male_radio.isChecked() else "Female"
        score = self.score_entry.text().strip()
        pre_test = self.pre_test_entry.text().strip()
        post_test = self.post_test_entry.text().strip()
        note = self.note_entry.text().strip()
        active = "Yes" if self.active_yes.isChecked() else "No"

        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        if self.student_id:
            # Edit existing student
            self.data["classes"][self.class_id]["students"][self.student_id] = {
                "name": name,
                "nickname": nickname,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                "attendance": self.student_data.get("attendance", {}),
            }
        else:
            # Add new student
            student_id = self.generate_unique_student_id()
            self.data["classes"][self.class_id]["students"][student_id] = {
                "name": name,
                "nickname": nickname,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": active,
                "attendance": {},
            }

        save_data(self.data)  # Save changes to the file
        self.refresh_callback()  # Refresh the table
        self.accept()  # Close the dialog

    def generate_unique_student_id(self):
        """Generate a unique Student ID."""
        existing_ids = self.data["classes"][self.class_id]["students"].keys()
        idx = 1
        while True:
            student_id = f"S{str(idx).zfill(3)}"
            if student_id not in existing_ids:
                return student_id
            idx += 1

    def open_bulk_import_dialog(self):
        class BulkImportTable(QTableWidget):
            def __init__(self, parent, paste_callback, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.parent = parent
                self.paste_callback = paste_callback
                self.setContextMenuPolicy(Qt.CustomContextMenu)
                self.customContextMenuRequested.connect(self.open_context_menu)

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

        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Import Students")
        dialog.resize(1000, 600)
        layout = QVBoxLayout(dialog)

        info_label = QLabel("Paste up to 150 students data from Excel below (columns: Name, Nickname, Company No, Gender, Score, Pre-Test, Post-Test, Note).")
        layout.addWidget(info_label)

        table = BulkImportTable(self, self.paste_from_clipboard, 25, 8)
        table.setHorizontalHeaderLabels([
            "Name", "Nickname", "Company No", "Gender", "Score", "Pre-Test", "Post-Test", "Note"
        ])
        layout.addWidget(table)

        add_rows_button = QPushButton("Add Rows")
        layout.addWidget(add_rows_button)

        def add_more_rows():
            current_rows = table.rowCount()
            if current_rows >= 150:
                QMessageBox.warning(dialog, "Limit Reached", "Maximum of 150 rows allowed.")
                return
            rows_to_add, ok = QInputDialog.getInt(dialog, "Add Rows", "How many rows to add?", 10, 1, 150 - current_rows)
            if ok:
                table.setRowCount(min(150, current_rows + rows_to_add))

        add_rows_button.clicked.connect(add_more_rows)

        paste_button = QPushButton("Paste from Clipboard (Ctrl+V)")
        paste_button.clicked.connect(lambda: self.paste_from_clipboard(table))
        layout.addWidget(paste_button)

        clear_button = QPushButton("Clear All")
        layout.addWidget(clear_button)

        def clear_all():
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    table.setItem(row, col, QTableWidgetItem(""))

        clear_button.clicked.connect(clear_all)

        save_button = QPushButton("Save Imported Students")
        save_button.clicked.connect(lambda: self.save_bulk_import(table, dialog))
        layout.addWidget(save_button)

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
        students = self.data["classes"][self.class_id]["students"]
        from logic.parser import generate_next_student_id, save_data

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

            student_id = generate_next_student_id(students)
            students[student_id] = {
                "name": name,
                "nickname": nickname,
                "company_no": company_no,
                "gender": gender,
                "score": score,
                "pre_test": pre_test,
                "post_test": post_test,
                "note": note,
                "active": "Yes",  # Always set to Yes
                "attendance": {},
            }
        save_data(self.data)
        self.refresh_callback()
        QMessageBox.information(self, "Bulk Import", "Students imported successfully!")
        dialog.accept()

    def capitalize_words(self, s):
        return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split())