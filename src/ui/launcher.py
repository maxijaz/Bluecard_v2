import tkinter as tk
from tkinter import ttk, messagebox
from logic.parser import load_data, save_data
from ui.mainform import Mainform
from src.ui.settings import SettingsForm
from src.ui.archive_manager import ArchiveManager
from src.ui.metadata_form import MetadataForm
import os
import shutil
from datetime import datetime
import sys
import json
from tkinter import ttk

class Launcher(tk.Toplevel):
    def __init__(self, root, theme):
        super().__init__(root)
        self.theme = theme
        self.title("Bluecard Launcher")
        self.geometry("450x400")
        self.center_window(450,400)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make Launcher always on top

        # Apply theme
        self.configure_theme()

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
            yscrollcommand=scrollbar.set
        )
        self.tree.heading("Class No", text="Class No", anchor="center")
        self.tree.heading("Company", text="Company", anchor="center")
        self.tree.heading("Archived", text="Arch", anchor="center")

        # Set column widths
        self.tree.column("Class No", width=150, anchor="center")
        self.tree.column("Company", width=150, anchor="center")
        self.tree.column("Archived", width=100, anchor="center")

        # Apply custom font and padding to rows and headings
        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=("Arial", 18, "bold"), padding=(0, 5))  # Header font and padding
        style.configure("Treeview", font=("Arial", 16), rowheight=30)  # Row font and height

        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.tree.yview)

        # Bind double-click event to open the Mainform
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
        """Handle double-click on a table row to open the Mainform."""
        selected_item = self.tree.selection()
        if not selected_item:
            return  # Do nothing if no row is selected
        self.open_class()

    def populate_table(self):
        """Populate the table with class data where archive = 'No'."""
        for class_id, class_data in self.classes.items():
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
        MetadataForm(self, None, self.data, self.theme, self.refresh).mainloop()

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
        SettingsForm(self, "data/default.json", self.refresh_launcher)

    def refresh_launcher(self):
        """Refresh the launcher after settings are saved."""
        self.theme = self.load_theme()  # Reload theme or other settings
        self.configure_theme()

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

class SettingsForm(tk.Toplevel):
    def __init__(self, parent, settings_file, on_save_callback):
        super().__init__(parent)
        self.settings_file = settings_file
        self.on_save_callback = on_save_callback
        self.title("Settings")
        self.geometry("375x475")
        self.center_window(375, 475)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make SettingsForm always on top

        # Load settings
        self.settings = self.load_settings()

        # Create widgets
        self.create_widgets()

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def load_settings(self):
        """Load settings from the JSON file."""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_settings(self):
        """Save settings to the JSON file."""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            self.on_save_callback()  # Notify the parent to refresh
            self.destroy()  # Close the settings window
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}", parent=self)

    def create_widgets(self):
        """Create the layout and fields for settings."""
        # Heading
        heading = tk.Label(self, text="Set-up Default Values Here...", font=("Arial", 16, "bold"))
        heading.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        subheading = tk.Label(self, text="Values can be changed in metadata.", font=("Arial", 10), fg="gray")
        subheading.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Fields for settings
        fields = [
            ("Default Teacher", "def_teacher"),
            ("Teacher No", "def_teacher_no"),
            ("Course Hours", "def_course_hours"),
            ("Class Time", "def_class_time"),
            ("Rate", "def_rate"),
            ("CCP", "def_ccp"),
            ("Travel", "def_travel"),
            ("Bonus", "def_bonus"),
        ]

        self.entries = {}

        # Theme dropdown
        tk.Label(self, text="Theme:", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "normal"))
        theme_dropdown = ttk.Combobox(self, textvariable=self.theme_var, values=["normal", "dark", "light"], state="readonly", width=27)
        theme_dropdown.grid(row=2, column=1, padx=10, pady=5)

        # Add fields from default.json
        for i, (label_text, key) in enumerate(fields, start=3):
            tk.Label(self, text=label_text, font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            entry = tk.Entry(self, width=30)
            entry.insert(0, self.settings.get(key, ""))
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[key] = entry

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=len(fields) + 3, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save", command=self.on_save, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.LEFT, padx=10)

    def on_save(self):
        """Handle the save button click."""
        # Update settings from entries
        self.settings["theme"] = self.theme_var.get()
        for key, entry in self.entries.items():
            self.settings[key] = entry.get()

        # Save settings to file
        self.save_settings()