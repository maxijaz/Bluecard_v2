from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QGridLayout, QMessageBox
from PyQt5.QtCore import Qt
from logic.db_interface import update_class, get_class_by_id

SHOW_HIDE_FIELDS = [
    ("show_nickname", "Nickname"),
    ("show_company_no", "Company No"),
    ("show_score", "Score"),
    ("show_prestest", "PreTest"),
    ("show_posttest", "PostTest"),
    ("show_attn", "Attn"),
    ("show_p", "P"),
    ("show_a", "A"),
    ("show_l", "L"),
]

class ShowHideForm(QDialog):
    def __init__(self, parent, class_id, on_save_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Show / Hide Columns")
        self.class_id = class_id
        self.on_save_callback = on_save_callback
        self.class_data = get_class_by_id(class_id)
        self.checkboxes = {}

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        for i, (key, label) in enumerate(SHOW_HIDE_FIELDS):
            lbl = QLabel(label)
            cb = QCheckBox()
            cb.setChecked(self.class_data.get(key, "Yes") == "Yes")
            self.checkboxes[key] = cb
            grid.addWidget(lbl, 0, i)
            grid.addWidget(cb, 1, i)
        layout.addLayout(grid)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save(self):
        updates = {key: "Yes" if cb.isChecked() else "No" for key, cb in self.checkboxes.items()}
        try:
            update_class(self.class_id, updates)
            if self.on_save_callback:
                self.on_save_callback()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")