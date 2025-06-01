from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QWidget, QMessageBox, QApplication, QDialog,
    QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from logic.parser import load_data, save_data
from ui.mainform import Mainform
from ui.metadata_form import MetadataForm
from ui.archive_manager import ArchiveManager
from ui.settings import SettingsForm
from .calendar import CalendarView
from logic.update_dates import update_dates, add_date, remove_date, modify_date
from logic.date_utils import warn_if_start_date_not_in_days
import sys
import os
import shutil
import datetime
from datetime import datetime, timedelta
from ui.monthly_summary import get_summary_text
from logic.db_interface import (
    get_all_classes,
    get_class_by_id,
    insert_class,
    update_class,
    set_class_archived,
    get_all_defaults,
    get_form_settings,
)
from logic.display import center_widget, scale_and_center, apply_window_flags

DB_PATH = os.path.join("data", "001attendance.db")
BACKUP_DIR = os.path.join("data", "backup")


class Launcher(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.font_prompt_shown = False
        # --- PATCH: Load per-form settings from DB ---
        form_settings = get_form_settings("Launcher") or {}
        self.setWindowTitle("Bluecard Launcher")
        win_w = form_settings.get("window_width")
        win_h = form_settings.get("window_height")
        if win_w and win_h:
            self.resize(int(win_w), int(win_h))
        else:
            self.resize(650, 500)
        min_w = form_settings.get("min_width")
        min_h = form_settings.get("min_height")
        if min_w and min_h:
            self.setMinimumSize(int(min_w), int(min_h))
        max_w = form_settings.get("max_width")
        max_h = form_settings.get("max_height")
        if max_w and max_h:
            self.setMaximumSize(int(max_w), int(max_h))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # --- FONT SIZE PATCH: Set global font size from per-form or global settings ---
        from PyQt5.QtGui import QFont
        default_settings = get_all_defaults()
        def get_setting(key, fallback):
            return form_settings.get(key) if form_settings.get(key) not in (None, "") else default_settings.get(key, fallback)
        form_font_size = int(get_setting("font_size", 12))
        button_font_size = int(get_setting("button_font_size", form_font_size))
        table_font_size = int(get_setting("table_font_size", form_font_size))
        table_header_font_size = int(get_setting("table_header_font_size", form_font_size))
        form_bg_color = get_setting("bg_color", "#e3f2fd")
        button_bg_color = get_setting("button_bg_color", "#1976d2")
        button_fg_color = get_setting("button_fg_color", "#ffffff")
        table_bg_color = get_setting("table_bg_color", "#ffffff")
        table_fg_color = get_setting("table_fg_color", "#222222")
        table_header_bg_color = get_setting("table_header_bg_color", "#1976d2")
        table_header_fg_color = get_setting("table_header_fg_color", "#ffffff")
        table_header_font_size = int(get_setting("table_header_font_size", form_font_size))
        QApplication.instance().setFont(QFont(get_setting("font_family", "Segoe UI"), form_font_size))
        style = f"""
            QWidget {{ background-color: {form_bg_color}; }}
            QLabel, QLineEdit {{ font-size: {form_font_size}pt; }}
            QPushButton {{ background-color: {button_bg_color}; color: {button_fg_color}; font-size: {button_font_size}pt; }}
            QTableView, QTableWidget {{ background-color: {table_bg_color}; }}
            QHeaderView::section {{ background-color: {table_header_bg_color}; color: {table_header_fg_color}; font-size: {table_header_font_size}pt; }}
            QTableWidget::item {{ color: {table_fg_color}; font-size: {table_font_size}pt; }}
        """
        QApplication.instance().setStyleSheet(style)
        # --- Apply display preferences (center/scale) if not overridden by per-form settings ---
        if not win_w or not win_h:
            display_settings = default_settings
            scale = str(display_settings.get("scale_windows", "1")) == "1"
            center = str(display_settings.get("center_windows", "1")) == "1"
            width_ratio = float(display_settings.get("window_width_ratio", 0.6))
            height_ratio = float(display_settings.get("window_height_ratio", 0.6))
            if scale:
                scale_and_center(self, width_ratio, height_ratio)
            elif center:
                center_widget(self)
        # --- PATCH END ---

        # Load class data from DB
        self.classes = {row["class_no"]: row for row in get_all_classes()}

        # Main container widget
        container = QWidget()
        self.setCentralWidget(container)
        self.layout = QVBoxLayout(container)

        # Create UI components
        self.create_widgets()

        # Center the window on startup
        self.center_window()
        # --- Apply display preferences ---
        from logic.db_interface import get_all_defaults
        display_settings = get_all_defaults()
        from logic.display import center_widget, scale_and_center, apply_window_flags
        scale = str(display_settings.get("scale_windows", "1")) == "1"
        center = str(display_settings.get("center_windows", "1")) == "1"
        width_ratio = float(display_settings.get("window_width_ratio", 0.6))
        height_ratio = float(display_settings.get("window_height_ratio", 0.6))
        if scale:
            scale_and_center(self, width_ratio, height_ratio)
        elif center:
            center_widget(self)
        # Optionally, apply window flags if you want to control minimize/maximize
        # apply_window_flags(self, show_minimize=True, show_maximize=True)
        # print("[DEBUG] Launcher __init__ end")

    def create_widgets(self):
        """Create the table and buttons."""
        # Table for class data
        self.table = QTableWidget()
        self.table.setColumnCount(2)  # Only Class No and Company
        self.table.setHorizontalHeaderLabels(["Class No", "Company"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.layout.addWidget(self.table, stretch=1)  # Make table expand with window
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { padding-left: 18px; padding-right: 18px; }")
        # Remove or comment out setMaximumWidth, so table can stretch
        # self.table.setMaximumWidth(376)  # 180+180+16 for scrollbar

        # Dynamically set initial window size based on widest entry in each column
        from PyQt5.QtGui import QFontMetrics, QFont
        table_font_size = int(get_all_defaults().get("table_font_size", 12))
        table_header_font_size = int(get_all_defaults().get("table_header_font_size", 16))
        font = QFont("Segoe UI", table_font_size)
        header_font = QFont("Segoe UI", table_header_font_size)
        metrics = QFontMetrics(font)
        header_metrics = QFontMetrics(header_font)
        # Use max width for Class No (OLO12345678910) and Company (widest entry or header)
        class_no_width = metrics.width("OLO12345678910") + 36
        # For company, use header or a long sample value for initial sizing
        company_sample = "The Almighty Realm Of Luxury ARL"
        company_width = max(metrics.width(company_sample), header_metrics.width("Company")) + 36
        col_widths = [class_no_width, company_width]
        min_width = sum(col_widths) + 80
        min_height = int(table_header_font_size * 10) + 300
        # Remove or reduce minimum size constraints to allow shrinking
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        # Optionally, you can remove these lines entirely if you want no minimum size at all
        # self.setMinimumSize(300, 200)
        # self.resize(395, 300)  # You can uncomment and adjust this for a default size, but it won't block resizing
        # self.resize(min_width, min_height)  # You can keep this for initial size, but it won't block shrinking

        # Connect double-click event to open_class
        self.table.doubleClicked.connect(self.open_class)

        # Populate the table
        self.populate_table()

        # Buttons - Row 1
        button_layout_row1 = QHBoxLayout()

        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_class)
        button_layout_row1.addWidget(open_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_class)
        button_layout_row1.addWidget(edit_button)

        add_button = QPushButton("Add New Class")
        add_button.clicked.connect(self.add_new_class)
        button_layout_row1.addWidget(add_button)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        button_layout_row1.addWidget(settings_button)

        self.layout.addLayout(button_layout_row1)

        # Buttons - Row 2
        button_layout_row2 = QHBoxLayout()

        archive_button = QPushButton("Archive")
        archive_button.clicked.connect(self.archive_class)
        button_layout_row2.addWidget(archive_button)

        archive_manager_button = QPushButton("Archive Manager")
        archive_manager_button.clicked.connect(self.open_archive_manager)
        button_layout_row2.addWidget(archive_manager_button)

        ttr_button = QPushButton("TTR")
        ttr_button.clicked.connect(self.open_ttr)
        button_layout_row2.addWidget(ttr_button)

        # Add Stylesheet button after TTR
        stylesheet_button = QPushButton("Stylesheet")
        stylesheet_button.clicked.connect(self.open_stylesheet)
        button_layout_row2.addWidget(stylesheet_button)

        self.layout.addLayout(button_layout_row2)

        self.table.setStyleSheet("QTableWidget::item:focus { outline: none; }")

    def set_table_column_widths(self):
        """Set both columns to fixed width 180 and update resize mode (accounts for vertical scrollbar)."""
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 180)
        # print(f"[DEBUG] Actual column widths after set: {[self.table.columnWidth(0), self.table.columnWidth(1)]}")
        # print(f"[DEBUG] Table widget size: {self.table.size()}, minimumSize: {self.table.minimumSize()}, sizePolicy: {self.table.sizePolicy()}")
        # print(f"[DEBUG] Main window size: {self.size()}, minimumSize: {self.minimumSize()}")
        self.col_widths = [180, 180]
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Fixed)

    def populate_table(self):
        # print("[DEBUG] populate_table start")
        """Populate the table with class data where archive = 'No', sorted by company (A-Z)."""
        self.table.setRowCount(0)  # Clear the table before repopulating
        sorted_classes = sorted(
            self.classes.values(),
            key=lambda row: row.get("company", "Unknown")
        )
        for class_row in sorted_classes:
            if class_row.get("archive", "No") == "No":
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                item0 = QTableWidgetItem(class_row["class_no"])
                item1 = QTableWidgetItem(class_row.get("company", "Unknown"))
                from logic.db_interface import get_all_defaults
                from PyQt5.QtGui import QFont
                table_font_size = int(get_all_defaults().get("table_font_size", 12))
                font = QFont("Segoe UI", table_font_size)
                item0.setFont(font)
                item1.setFont(font)
                self.table.setItem(row_position, 0, item0)
                self.table.setItem(row_position, 1, item1)
        # --- Always set row height after populating ---
        table_font_size = int(get_all_defaults().get("table_font_size", 12))
        row_height = int(table_font_size * 2.4)
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, row_height)
        # --- Set column widths and resize mode using dedicated method ---
        self.set_table_column_widths()
        # print(f"[DEBUG] Columns set to fixed width {self.col_widths}")
        # print("[DEBUG] populate_table end")

    def refresh_data(self):
        """Refresh the data and table in the Launcher."""
        self.classes = {row["class_no"]: row for row in get_all_classes()}
        self.populate_table()  # Refresh the table with the updated data
        self.set_table_column_widths()  # Ensure columns are always reset after repopulating

    def open_class(self):
        """Open the selected class in the Mainform."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to open.")
            return

        class_id = self.table.item(selected_row, 0).text()
        # Fetch latest class data from DB
        class_data = get_class_by_id(class_id)
        self.mainform = Mainform(class_id, {"classes": {class_id: class_data}}, self.theme)
        self.mainform.showMaximized()  # Open the Mainform maximized
        self.mainform.closed.connect(self.show_launcher)  # Reopen Launcher when Mainform is closed
        self.hide()  # Hide the Launcher instead of closing it

    def show_launcher(self):
        """Reopen the Launcher and refresh its data."""
        self.refresh_data()  # Refresh the data and table
        self.show()
        self.center_window()

    def edit_class(self):
        """Edit the selected class."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a class to edit.")
            return
        selected_row = selected_items[0].row()
        class_id = self.table.item(selected_row, 0).text()
        defaults = self.load_defaults()
        class_data = get_class_by_id(class_id)
        metadata_form = MetadataForm(
            self,
            class_id,
            {"classes": {class_id: {"metadata": class_data}}},
            self.theme,
            self.refresh_table,
            defaults
        )
        metadata_form.class_saved.connect(self.refresh_data)  # Live update on save
        metadata_form.exec_()

    def add_new_class(self):
        """Add a new class with default values."""
        defaults = self.load_defaults()
        if not defaults:
            return

        def handle_class_saved(class_id):
            # After saving, refresh from DB
            self.refresh_data()
            self.open_mainform_after_save(class_id)

        metadata_form = MetadataForm(
            self, None, {"classes": {}}, self.theme, self.refresh_table, defaults, single_date_mode=True
        )
        metadata_form.class_saved.connect(handle_class_saved)  # Connect the signal

        metadata_form.exec_()  # Open the form as a modal dialog

    def archive_class(self):
        """Archive the selected class immediately (no Y/N confirmation, auto-closing message)."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a class to archive.")
            return

        class_id = self.table.item(selected_row, 0).text()
        company = self.table.item(selected_row, 1).text()
        set_class_archived(class_id, archived=True)
        self.refresh_data()
        # --- Ensure columns are stretched after refresh ---
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        # Show a non-blocking confirmation dialog for 2 seconds
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt5.QtGui import QFontMetrics, QFont
        dlg = QDialog(self)
        dlg.setWindowTitle("Archived")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.FramelessWindowHint | Qt.Tool)
        layout = QVBoxLayout(dlg)
        label_text = f"Class {class_id} ({company}) has been archived."
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        dlg.setLayout(layout)
        font = label.font() if hasattr(label, 'font') else QFont()
        metrics = QFontMetrics(font)
        text_width = metrics.width(label_text)
        dlg_width = max(text_width + 60, 400)
        dlg.setFixedSize(dlg_width, 80)
        dlg.show()
        QTimer.singleShot(2000, dlg.accept)

    def open_archive_manager(self):
        """Open the Archive Manager for all archived classes."""
        archived_classes = {
            row["class_no"]: row
            for row in get_all_classes()
            if row.get("archive", "Yes") == "Yes"
        }

        if not archived_classes:
            QMessageBox.information(self, "No Archived Classes", "There are no archived classes to manage.")
            return

        # Pass self.refresh_data as the callback for instant launcher refresh
        archive_manager = ArchiveManager(self, {"classes": archived_classes}, archived_classes, self.refresh_data)
        archive_manager.exec_()  # Open the Archive Manager as a modal dialog

    def open_ttr(self):
        """Open the TTR."""
        summary_text = get_summary_text(teacher_name="Paul R")  # Or use a variable for teacher
        dlg = MonthlySummaryDialog(summary_text, self)
        dlg.exec_()

    def open_stylesheet(self):
        from ui.stylesheet import StylesheetForm
        stylesheet_form = StylesheetForm(self)
        stylesheet_form.exec_()

    def open_settings(self):
        from ui.settings import SettingsForm
        settings_form = SettingsForm(self)
        settings_form.exec_()

    def apply_settings_and_theme(self, new_theme):
        """Apply theme and font size after settings are changed."""
        self.theme = new_theme
        # Apply font size and colors globally
        from logic.db_interface import get_all_defaults
        from PyQt5.QtGui import QFont
        default_settings = get_all_defaults()
        form_font_size = int(default_settings.get("form_font_size", 12))
        button_font_size = int(default_settings.get("button_font_size", form_font_size))
        table_font_size = int(default_settings.get("table_font_size", form_font_size))
        table_header_font_size = int(default_settings.get("table_header_font_size", form_font_size))
        form_bg_color = default_settings.get("form_bg_color", "#e3f2fd")
        button_bg_color = default_settings.get("button_bg_color", "#1976d2")
        button_fg_color = default_settings.get("button_fg_color", "#ffffff")
        table_bg_color = default_settings.get("table_bg_color", "#ffffff")
        table_fg_color = default_settings.get("table_fg_color", "#222222")
        table_header_bg_color = default_settings.get("table_header_bg_color", "#1976d2")
        table_header_fg_color = default_settings.get("table_header_fg_color", "#ffffff")
        table_header_font_size = int(default_settings.get("table_header_font_size", form_font_size))
        # Set the default font for general UI (form/metadata)
        QApplication.instance().setFont(QFont("Segoe UI", form_font_size))
        style = f"""
            QWidget {{ background-color: {form_bg_color}; }}
            QLabel, QLineEdit {{ font-size: {form_font_size}pt; }}
            QPushButton {{ background-color: {button_bg_color}; color: {button_fg_color}; font-size: {button_font_size}pt; }}
            QTableView, QTableWidget {{ background-color: {table_bg_color}; }}
            QHeaderView::section {{ background-color: {table_header_bg_color}; color: {table_header_fg_color}; font-size: {table_header_font_size}pt; }}
            QTableWidget::item {{ color: {table_fg_color}; font-size: {table_font_size}pt; }}
        """
        QApplication.instance().setStyleSheet(style)
        # --- Force update of table data font size for instant effect ---
        if hasattr(self, 'table'):
            from PyQt5.QtGui import QFont
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setFont(QFont("Segoe UI", table_font_size))
            # Adjust row heights to fit new font size (more vertical padding)
            row_height = int(table_font_size * 2.4)  # 2.4x font size for more padding
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, row_height)

    def refresh_table(self):
        """Refresh the table with updated class data."""
        self.populate_table()

    def load_defaults(self):
        """Load default values from the database."""
        return get_all_defaults()

    def center_window(self):
        """Center the Launcher window on the screen using the display utility."""
        center_widget(self)
        print(f"[DEBUG] Window location on open: x={self.x()}, y={self.y()}, width={self.width()}, height={self.height()}")

    def open_mainform_after_save(self, class_id):
        """Open the Mainform after saving a new class."""
        # Fetch latest class data from DB
        class_data = get_class_by_id(class_id)
        self.mainform = Mainform(class_id, {"classes": {class_id: class_data}}, self.theme)
        self.mainform.showMaximized()
        self.mainform.closed.connect(self.show_launcher)
        self.hide()

    def refresh_data(self):
        """Refresh the data and table in the Launcher."""
        self.classes = {row["class_no"]: row for row in get_all_classes()}
        self.populate_table()  # Refresh the table with the updated data
        self.set_table_column_widths()  # Ensure columns are always reset after repopulating

    def closeEvent(self, event):
        """Prompt for DB backup when closing the launcher."""
        reply = QMessageBox.question(
            self,
            "Backup Database",
            "Do you want to backup the database before exiting?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Yes:
            from ui.launcher import backup_sqlite_db
            backup_sqlite_db()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:  # Cancel
            event.ignore()  # Do not close the launcher

    def resizeEvent(self, event):
        super().resizeEvent(event)
        table_width = self.table.viewport().width()
        header = self.table.horizontalHeader()
        # Always stretch columns to fill available width when window is maximized or wide
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        # print(f"[DEBUG] resizeEvent: window size={self.size()}, table size={self.table.size()}, col_widths={[self.table.columnWidth(0), self.table.columnWidth(1)]}")
        # print(f"[DEBUG] After resizeEvent: {[self.table.columnWidth(0), self.table.columnWidth(1)]}")

def generate_dates(start_date_str, days_str, max_classes):
    """Generate a list of dates based on StartDate, Days, and MaxClasses."""
    # Parse StartDate
    try:
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    except ValueError:
        start_date = None  # If StartDate is invalid or missing

    # Parse Days into weekday indices (0=Monday, 1=Tuesday, ..., 6=Sunday)
    weekdays = []
    if days_str:
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        weekdays = [day_map[day.strip()] for day in days_str.split(",") if day.strip() in day_map]

    # Generate dates dynamically
    dates = []
    if start_date and weekdays:
        current_date = start_date
        while len(dates) < max_classes:
            if current_date.weekday() in weekdays:
                dates.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)  # Move to the next day

    # Fallback to placeholders if no valid dates are generated
    if not dates:
        dates = [f"Date{i + 1}" for i in range(max_classes)]

    return dates


class MonthlySummaryDialog(QDialog):
    def __init__(self, summary_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monthly Summary")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(summary_text)
        layout.addWidget(text_edit)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


def backup_sqlite_db():
    """Backup the SQLite DB to /data/backup/ with a timestamp."""
    if not os.path.exists(DB_PATH):
        print("No database file found to backup.")
        return
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # <-- PATCHED LINE
    backup_path = os.path.join(BACKUP_DIR, f"001attendance_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Database backed up to {backup_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher(theme="default")
    launcher.show()
    sys.exit(app.exec_())