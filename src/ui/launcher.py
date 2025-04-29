import tkinter as tk
from tkinter import ttk, messagebox
from logic.parser import load_data, save_data
from ui.mainform import Mainform
from src.ui.settings import SettingsForm
from src.ui.archive_manager import ArchiveManager
from src.ui.metadata_form import MetadataForm
import os
import json
import logging

class Launcher(tk.Toplevel):
    def __init__(self, root, theme):
        super().__init__(root)
        self.theme = theme
        self.title("Bluecard Launcher")
        self.geometry("450x450")
        self.center_window(450, 450)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make Launcher always on top

        # Load theme configuration
        self.theme_config = self.load_theme_config()

        # Apply Treeview styles
        self.apply_treeview_styles()

        # Load default settings
        self.default_settings = self.load_default_settings()

        # Apply theme
        self.configure_theme()

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_theme_config(self):
        """Load theme configuration from themes.json."""
        try:
            with open("data/themes.json", "r", encoding="utf-8") as f:
                themes = json.load(f).get("themes", [])
                # Find the theme by name in the list
                for theme in themes:
                    if theme.get("name") == self.theme:
                        return theme
                # Fallback to the default theme
                for theme in themes:
                    if theme.get("name") == "default":
                        return theme
                return {}  # Return an empty config if no theme is found
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def load_default_settings(self):
        """Load default settings from default.json."""
        try:
            with open("data/default.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings
        except FileNotFoundError:
            # Log a warning if the default.json file is missing
            logging.warning("default.json not found. Using empty default settings.")
            return {}
        except json.JSONDecodeError as e:
            # Log an error if the JSON file is invalid
            logging.error(f"Error decoding default.json: {e}")
            return {}

    def apply_treeview_styles(self):
        """Apply styles for Treeview based on the selected theme."""
        style = ttk.Style()

        treeview_config = self.theme_config.get("treeview", {})
        background = treeview_config.get("background", "white")
        foreground = treeview_config.get("foreground", "black")
        fieldbackground = treeview_config.get("fieldbackground", "white")
        rowheight = treeview_config.get("rowheight", 30) + 5  # Increase row height by 5

        # Configure Treeview styles
        style.configure(
            "Treeview",
            background=background,
            foreground=foreground,
            fieldbackground=fieldbackground,
            rowheight=rowheight,
            font=("Arial", 18)  # Increase font size to 18
        )

        # Configure heading styles
        heading_config = treeview_config.get("heading", {})
        style.configure(
            "Treeview.Heading",
            font=("Arial", 18, "bold"),
            background=heading_config.get("background", "lightblue"),
            foreground=heading_config.get("foreground", "black")
        )

        # Configure selected row styles
        selected_config = treeview_config.get("selected", {})
        style.map(
            "Treeview",
            background=[("selected", "#1E90FF")],  # Darker blue for selected row
            foreground=[("selected", "white")]
        )

    def configure_theme(self):
        """Apply the selected theme to the Launcher."""
        if self.theme == "dark":
            self.configure(bg="black")
        elif self.theme == "clam":
            self.configure(bg="lightblue")
        else:  # Default theme
            self.configure(bg="white")

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create the table and buttons."""
        # Apply Treeview styles before creating the widget
        self.apply_treeview_styles()

        # Frame for the table and scrollbar
        table_frame = tk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Table for class data
        self.tree = ttk.Treeview(
            table_frame,
            columns=("Class No", "Company", "Archived"),
            show="headings",
            height=8,  # Limit to 8 rows
            yscrollcommand=scrollbar.set,
            style="Treeview"
        )
        self.tree.heading("Class No", text="Class No", anchor="center")  # Center-align header
        self.tree.heading("Company", text="Company", anchor="center")  # Center-align header
        self.tree.heading("Archived", text="Arch", anchor="center")  # Center-align header

        # Set column widths and justify data to the left
        self.tree.column("Class No", width=130, anchor="w")  # Left-align data
        self.tree.column("Company", width=200, anchor="w")  # Left-align data
        self.tree.column("Archived", width=70, anchor="center")  # Center-align header

        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.tree.yview)

        # Bind hover effect
        self.tree.bind("<Motion>", self.on_hover)

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        # Center the buttons
        buttons_inner_frame = tk.Frame(button_frame, bg=self["bg"])
        buttons_inner_frame.pack(anchor="center")

        # Arrange buttons with fixed width
        btn_open = tk.Button(buttons_inner_frame, text="Open", command=self.open_class, width=10)
        btn_edit = tk.Button(buttons_inner_frame, text="Edit", command=self.edit_class, width=10)
        btn_add = tk.Button(buttons_inner_frame, text="Add Class", command=self.add_new_class, width=10)
        btn_archive = tk.Button(buttons_inner_frame, text="Archive", command=self.archive_class, width=10)
        btn_archive_manager = tk.Button(buttons_inner_frame, text="Arch Mger", command=self.open_archive_manager, width=10)
        btn_ttr = tk.Button(buttons_inner_frame, text="TTR", command=self.placeholder_ttr, width=10)
        btn_settings = tk.Button(buttons_inner_frame, text="Settings", command=self.open_settings, width=10)

        # Use grid layout for two rows
        btn_open.grid(row=0, column=0, padx=5, pady=5)
        btn_edit.grid(row=0, column=1, padx=5, pady=5)
        btn_add.grid(row=0, column=2, padx=5, pady=5)
        btn_archive.grid(row=1, column=0, padx=5, pady=5)
        btn_archive_manager.grid(row=1, column=1, padx=5, pady=5)
        btn_ttr.grid(row=1, column=2, padx=5, pady=5)
        btn_settings.grid(row=1, column=3, padx=5, pady=5)

    def on_double_click(self, event):
        """Handle double-click on a table row to highlight and open the Mainform."""
        selected_item = self.tree.selection()
        if not selected_item:
            return  # Do nothing if no row is selected

        # Highlight the selected row in blue
        self.tree.tag_configure("selected", background="#1E90FF", foreground="white")  # Blue for selected row
        for row in self.tree.get_children():
            self.tree.item(row, tags=())  # Reset tags for all rows
        self.tree.item(selected_item, tags=("selected",))

        # Open the Mainform with the selected data
        class_id = self.tree.item(selected_item, "values")[0]
        self.destroy()  # Close the Launcher
        Mainform(self.master, class_id, self.data, self.theme).mainloop()  # Open the Mainform

    def on_hover(self, event):
        """Handle hover effect for Treeview rows."""
        row_id = self.tree.identify_row(event.y)
        # Reset hover effect for all rows
        for row in self.tree.get_children():
            self.tree.item(row, tags=())
        # Apply hover effect to the current row
        if row_id:
            self.tree.tag_configure("hover", background="#d0e7ff")  # Light blue for hover
            self.tree.item(row_id, tags=("hover",))

    def populate_table(self):
        """Populate the table with class data where archive = 'No', sorted by Company (A-Z)."""
        # Extract and sort the data by the 'Company' field
        sorted_classes = sorted(
            self.classes.items(),
            key=lambda item: item[1].get("metadata", {}).get("Company", "Unknown")
        )

        # Populate the Treeview with sorted data
        for class_id, class_data in sorted_classes:
            metadata = class_data.get("metadata", {})
            if metadata.get("archive", "No") == "No":
                company = metadata.get("Company", "Unknown")
                archived = metadata.get("archive", "No")
                self.tree.insert("", tk.END, values=(class_id, company, archived))

    def open_class(self):
        """Open the selected class in the Mainform."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to open.", parent=self)
            return
        class_id = self.tree.item(selected_item, "values")[0]
        self.destroy()  # Close the Launcher
        Mainform(self.master, class_id, self.data, self.theme).mainloop()  # Open the Mainform

    def edit_class(self):
        """Open the MetadataForm to edit an existing class."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to edit.", parent=self)
            return
        class_id = self.tree.item(selected_item, "values")[0]
        MetadataForm(self, class_id, self.data, self.theme, self.refresh).mainloop()

    def add_new_class(self):
        """Open the MetadataForm to add a new class."""
        MetadataForm(self, None, self.default_settings, self.theme, self.refresh).mainloop()

    def archive_class(self):
        """Archive the selected class."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to archive.", parent=self)
            return
        class_id = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Archive Class", f"Are you sure you want to archive class {class_id}?", parent=self)
        if confirm:
            self.classes[class_id]["metadata"]["archive"] = "Yes"
            save_data(self.data)
            self.refresh()

    def open_archive_manager(self):
        """Open the Archive Manager form."""
        self.destroy()  # Close the Launcher
        ArchiveManager(self.master, self.data, self.theme).mainloop()

    def placeholder_ttr(self):
        """Placeholder for TTR functionality."""
        messagebox.showinfo("TTR", "This feature is under development.", parent=self)

    def open_settings(self):
        """Open the settings window."""
        SettingsForm(self, self.theme, self.refresh_launcher)

    def refresh_launcher(self, theme=None):
        """Refresh the launcher after settings are saved."""
        if theme:
            self.theme = theme  # Update the theme if provided
        self.theme_config = self.load_theme_config()  # Reload theme configuration
        self.configure_theme()  # Apply the new theme
        self.refresh()  # Refresh the UI components

    def refresh(self):
        """Refresh the Launcher."""
        for widget in self.winfo_children():
            widget.destroy()  # Clear all widgets
        self.create_widgets()  # Recreate widgets

    def on_close(self):
        """Handle Launcher close event."""
        confirm = messagebox.askyesno("Exit", "Do you want to back up your data before exiting?", parent=self)
        if confirm:
            save_data(self.data)
        self.destroy()