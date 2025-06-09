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
    get_message_defaults,
)
from logic.display import center_widget, scale_and_center, apply_window_flags

DB_PATH = os.path.join("data", "001attendance.db")
BACKUP_DIR = os.path.join("data", "backup")


class Launcher(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.font_prompt_shown = False
        # --- FIX: Initialize self.classes before any method that uses it ---
        self.classes = {row["class_no"]: row for row in get_all_classes()}
        # Load per table form_settings from DB 
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
        # Do NOT set max_width or max_height, so maximize is always available

        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        # Set global font size from per-form or global settings ---
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
        # Center the window on open
        self.center_window()

        # --- FIX: Set up layout and widgets ---
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.create_widgets()
        # --- END FIX ---

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
        self.table.horizontalHeader().setSectionsClickable(False)

    def set_table_column_widths(self):
        # This method is no longer used for stretching columns. Remove or leave empty.
        pass

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
        # --- Set columns to stretch after populating ---
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        # print(f"[DEBUG] Columns set to stretch after populate_table")

    def refresh_data(self):
        """Refresh the data and table in the Launcher."""
        self.classes = {row["class_no"]: row for row in get_all_classes()}
        self.populate_table()  # Refresh the table with the updated data
        # Do NOT call set_table_column_widths() here

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
        # --- PATCH: Ensure columns are stretched after show ---
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        # --- PATCH: Force a resize event to trigger column stretching ---
        self.resize(self.width() + 1, self.height())  # Nudge width by 1px
        self.resize(self.width() - 1, self.height())  # Restore width
        # --- DEBUG: Print column widths after show ---
        print(f"[DEBUG] After show_launcher: col0={self.table.columnWidth(0)}, col1={self.table.columnWidth(1)}, win_width={self.width()}")

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
        # Show a non-blocking confirmation dialog for 2 seconds using message defaults
        show_message_dialog(self, f"Class {class_id} ({company}) has been archived.")

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
        """Open the Monthly Summary as a top-level window (maximizable, resizable, standard window)."""
        from ui.monthly_summary import MonthlySummaryWindow
        # Store reference to prevent garbage collection
        if not hasattr(self, '_monthly_summary_windows'):
            self._monthly_summary_windows = []
        window = MonthlySummaryWindow()
        window.show()
        self._monthly_summary_windows.append(window)

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
        # --- PATCH: Use per-form settings if available, fallback to global defaults ---
        from PyQt5.QtGui import QFont
        form_settings = get_form_settings("Launcher") or {}
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
        # --- Force update of table data font size for instant effect ---
        if hasattr(self, 'table'):
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setFont(QFont(get_setting("font_family", "Segoe UI"), table_font_size))
            # Adjust row heights to fit new font size (more vertical padding)
            row_height = int(table_font_size * 2.4)
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
        # print(f"[DEBUG] Window location on open: x={self.x()}, y={self.y()}, width={self.width()}, height={self.height()}")

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
        # Do NOT call set_table_column_widths() here

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
        if hasattr(self, "table"):
            header = self.table.horizontalHeader()
            for col in range(self.table.columnCount()):
                header.setSectionResizeMode(col, QHeaderView.Stretch)
        # Print window size on every resize
        # print(f"[DEBUG] Window resized: width={self.width()}, height={self.height()}")

    def showEvent(self, event):
        super().showEvent(event)
        # print(f"[DEBUG] Window size after show: width={self.width()}, height={self.height()}")

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

def show_message_dialog(parent, text, duration=2000):
    from PyQt5.QtCore import QTimer, Qt
    from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
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
    msg_dialog.setModal(False)
    layout = QVBoxLayout(msg_dialog)
    label = QLabel(text)
    label.setStyleSheet(style)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    msg_dialog.adjustSize()
    screen = parent.window().screen() if hasattr(parent.window(), 'screen') else None
    if screen:
        scr_geo = screen.geometry()
        x = scr_geo.x() + (scr_geo.width() - msg_dialog.width()) // 2
        y = scr_geo.y() + (scr_geo.height() - msg_dialog.height()) // 2
    else:
        x = 400
        y = 300
    msg_dialog.move(x, y)
    msg_dialog.show()
    parent._msg_dialog = msg_dialog  # Keep reference to prevent GC
    QTimer.singleShot(duration, msg_dialog.close)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher(theme="default")
    launcher.show()
    sys.exit(app.exec_())