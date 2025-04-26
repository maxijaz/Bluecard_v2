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
print(sys.path)

class Launcher(tk.Toplevel):
    def __init__(self, root, theme):
        super().__init__(root)
        self.theme = theme
        self.title("Bluecard Launcher")
        self.geometry("650x500")
        self.center_window(650, 500)
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
        # Table for class data
        self.tree = ttk.Treeview(self, columns=("Class No", "Company", "Archived"), show="headings")
        self.tree.heading("Class No", text="Class No")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Archived", text="Archived")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind double-click event to open the Mainform
        self.tree.bind("<Double-1>", self.on_double_click)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        buttons = tk.Frame(button_frame, bg=self["bg"])
        buttons.pack(anchor=tk.CENTER)

        tk.Button(buttons, text="Open", command=self.open_class, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Edit", command=self.edit_class, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Add New Class", command=self.add_new_class, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Archive", command=self.archive_class, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Archive Manager", command=self.open_archive_manager, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="TTR", command=self.placeholder_ttr, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Settings", command=self.open_settings, width=12).pack(side=tk.LEFT, padx=5)

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
        """Open the Settings form."""
        SettingsForm(self, self.theme, self.refresh).mainloop()

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