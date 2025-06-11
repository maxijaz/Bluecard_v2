from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QSizePolicy, QColorDialog, QMenu, QWidget,
    QListWidget, QListWidgetItem, QStackedWidget, QFormLayout, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from logic.db_interface import get_all_defaults, set_all_defaults, get_form_settings, get_teacher_defaults

# --- Floating message dialog helper ---
def show_floating_message(parent, message, duration=2500, style_overrides=None):
    defaults = get_all_defaults()
    bg = defaults.get("message_bg_color", "#323232")
    fg = defaults.get("message_fg_color", "#fff")
    border = defaults.get("message_border_color", "#2980f0")
    border_width = int(defaults.get("message_border_width", 2))
    border_radius = int(defaults.get("message_border_radius", 12))
    font_size = int(defaults.get("message_font_size", 12))
    font_weight = "bold" if str(defaults.get("message_font_bold", "true")).lower() == "true" else "normal"
    padding = defaults.get("message_padding", "10px 18px")
    shadow = defaults.get("message_shadow", "2px 2px 8px #222")
    z = int(defaults.get("message_z_index", 10000))
    if style_overrides:
        bg = style_overrides.get("bg", bg)
        fg = style_overrides.get("fg", fg)
        border = style_overrides.get("border", border)
        border_width = style_overrides.get("border_width", border_width)
        border_radius = style_overrides.get("border_radius", border_radius)
        font_size = style_overrides.get("font_size", font_size)
        font_weight = style_overrides.get("font_weight", font_weight)
        padding = style_overrides.get("padding", padding)
        shadow = style_overrides.get("shadow", shadow)
        z = style_overrides.get("z", z)
    msg = QLabel(message, parent)
    msg.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    msg.setAttribute(Qt.WA_TranslucentBackground)
    msg.setAlignment(Qt.AlignCenter)
    msg.setStyleSheet(f"""
        background: {bg};
        color: {fg};
        border: {border_width}px solid {border};
        border-radius: {border_radius}px;
        font-size: {font_size}pt;
        font-weight: {font_weight};
        padding: {padding};
        box-shadow: {shadow};
        z-index: {z};
    """)
    msg.adjustSize()
    parent_rect = parent.geometry()
    msg.move(
        parent_rect.x() + (parent_rect.width() - msg.width()) // 2,
        parent_rect.y() + (parent_rect.height() - msg.height()) // 2
    )
    msg.show()
    QTimer.singleShot(duration, msg.close)

class StylesheetForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stylesheet Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.default_font = QFont("Arial", 11)
        self.sidebar_width = 200
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Sidebar navigation
        sidebar = QListWidget()
        sidebar.setFixedWidth(self.sidebar_width + 50)  # Increase width by 50px
        sidebar.setFont(self.default_font)
        sidebar.setStyleSheet("background-color: #f0f0f0;")

        # Add navigation items in the desired order
        navigation_items = [
            "Teacher Defaults",  # First
            "Global Settings",   # Second
        ]
        # Add all forms alphabetically
        forms = ["Archive Manager", "Bulk Import Students", "Calendar View", "Launcher", "Mainform", "Metadata Form", "Monthly Summary", "Settings Form", "Student Form"]
        navigation_items.extend([f"Settings for {form}" for form in sorted(forms)])

        for name in navigation_items:
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignLeft)  # Align text to the left
            sidebar.addItem(item)

        # Stack for main content
        self.stack = QStackedWidget(self)
        self.stack.setFont(self.default_font)

        # Add pages to the stack
        self.stack.addWidget(self.create_teacher_defaults_page())
        self.stack.addWidget(self.create_global_settings_page())
        for form_name in sorted(forms):
            self.stack.addWidget(self.create_form_settings_page(form_name))

        # Connect navigation
        sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        sidebar.setCurrentRow(0)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

    def create_global_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel("Global Settings")
        label.setFont(self.default_font)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        form_layout = QFormLayout()
        global_settings = get_all_defaults()
        for key, value in global_settings.items():
            form_layout.addRow(key.replace("_", " ").capitalize() + ":", QLineEdit(str(value)))
        scroll_layout.addLayout(form_layout)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        save_button = QPushButton("Save")
        restore_button = QPushButton("Restore Defaults")
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(restore_button)
        layout.addLayout(button_layout)

        # Updated button styles to adhere to factory defaults.
        save_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")
        restore_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")

        return page

    def create_form_settings_page(self, form_name):
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel(f"Settings for {form_name}")
        label.setFont(self.default_font)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        form_layout = QFormLayout()
        form_settings = get_form_settings(form_name.replace(" ", ""))  # Remove spaces for DB lookup
        for key, value in form_settings.items():
            form_layout.addRow(key.replace("_", " ").capitalize() + ":", QLineEdit(str(value)))
        scroll_layout.addLayout(form_layout)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        save_button = QPushButton("Save")
        restore_button = QPushButton("Restore Defaults")
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(restore_button)
        layout.addLayout(button_layout)

        # Updated button styles to adhere to factory defaults.
        save_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")
        restore_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")

        return page

    def create_teacher_defaults_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(10, 10, 10, 10)  # Add consistent margins
        layout.setSpacing(10)  # Adjust spacing for better alignment

        label = QLabel("Teacher Defaults")
        label.setFont(self.default_font)
        label.setAlignment(Qt.AlignCenter)  # Center the title at the top
        layout.addWidget(label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        form_layout = QFormLayout()
        teacher_defaults = get_teacher_defaults()
        for key, value in teacher_defaults.items():
            form_layout.addRow(key.replace("_", " ").capitalize() + ":", QLineEdit(str(value)))
        scroll_layout.addLayout(form_layout)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        save_button = QPushButton("Save")
        restore_button = QPushButton("Restore Defaults")
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(restore_button)
        layout.addLayout(button_layout)

        # Updated button styles to adhere to factory defaults.
        save_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")
        restore_button.setStyleSheet("background-color: #1976d2; color: #ffffff; border: 1px solid #1976d2; font-size: 12pt; font-weight: normal; padding: 5px; hover { background-color: #1565c0; } pressed { background-color: #0d47a1; }")

        restore_button.clicked.connect(lambda: self.confirm_restore_defaults())

        return page

    def confirm_restore_defaults(self):
        reply = QMessageBox.question(self, 'Confirm Restore Defaults', 'Are you sure you want to restore defaults?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.restore_all_colors_fonts()  # Call with no arguments
            show_floating_message(self, "Defaults restored successfully.", 3000)
        else:
            show_floating_message(self, "Restore defaults canceled.", 3000)

    def _debug_save_settings(self, *args, **kwargs):
        print("[DEBUG] Save button clicked. Current values:", self._get_current_values())
        self.save_settings(*args, **kwargs)

    def _debug_restore_all_colors_fonts(self, *args, **kwargs):
        print("[DEBUG] Restore All Colors/Fonts button clicked.")
        self.restore_all_colors_fonts()  # Call with no arguments
        print("[DEBUG] After restore, current values:", self._get_current_values())

    def _debug_toggle_color_on_off(self, *args, **kwargs):
        print(f"[DEBUG] Toggle Color button clicked. Checked: {self.toggle_color_button.isChecked()}")
        self.toggle_color_on_off()  # Call with no arguments
        print("[DEBUG] After toggle, current values:", self._get_current_values())

    def _debug_close_with_prompt(self, *args, **kwargs):
        print("[DEBUG] Close button clicked. Has changes:", self._has_changes())
        self.close_with_prompt()  # Call with no arguments
