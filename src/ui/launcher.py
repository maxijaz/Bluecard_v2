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
import subprocess

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
                for theme in themes:
                    if theme.get("name") == self.theme:
                        return theme
                for theme in themes:
                    if theme.get("name") == "default":
                        return theme
                return {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def load_default_settings(self):
        """Load default settings from default.json."""
        try:
            with open("data/default.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def apply_treeview_styles(self):
        """Apply styles for Treeview based on the selected theme."""
        style = ttk.Style()
        treeview_config = self.theme_config.get("treeview", {})
        style.configure(
            "Treeview",
            background=treeview_config.get("background", "white"),
            foreground=treeview_config.get("foreground", "black"),
            fieldbackground=treeview_config.get("fieldbackground", "white"),
            rowheight=treeview_config.get("rowheight", 30) + 5,
            font=("Arial", 18)
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 18, "bold"),
            background=treeview_config.get("heading", {}).get("background", "lightblue"),
            foreground=treeview_config.get("heading", {}).get("foreground", "black")
        )
        style.map(
            "Treeview",
            background=[("selected", "#1E90FF")],
            foreground=[("selected", "white")]
        )

    def configure_theme(self):
        """Apply the selected theme to the Launcher."""
        if self.theme == "dark":
            self.configure(bg="black")
        elif self.theme == "clam":
            self.configure(bg="lightblue")
        else:
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
            height=8,
            yscrollcommand=scrollbar.set,
            style="Treeview"
        )
        self.tree.heading("Class No", text="Class No", anchor="center")
        self.tree.heading("Company", text="Company", anchor="center")
        self.tree.heading("Archived", text="Arch", anchor="center")

        self.tree.column("Class No", width=130, anchor="w")
        self.tree.column("Company", width=200, anchor="w")
        self.tree.column("Archived", width=70, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.tree.yview)

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        buttons_inner_frame = tk.Frame(button_frame, bg=self["bg"])
        buttons_inner_frame.pack(anchor="center")

        btn_open = tk.Button(buttons_inner_frame, text="Open", command=self.open_class, width=10)
        btn_edit = tk.Button(buttons_inner_frame, text="Edit", command=self.edit_class, width=10)
        btn_add = tk.Button(buttons_inner_frame, text="Add Class", command=self.add_new_class, width=10)
        btn_archive = tk.Button(buttons_inner_frame, text="Archive", command=self.archive_class, width=10)
        btn_archive_manager = tk.Button(buttons_inner_frame, text="Arch Mger", command=self.open_archive_manager, width=10)
        btn_ttr = tk.Button(buttons_inner_frame, text="TTR", command=self.open_ttr_window, width=10)
        btn_settings = tk.Button(buttons_inner_frame, text="Settings", command=self.open_settings, width=10)

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
            return
        class_id = self.tree.item(selected_item, "values")[0]
        self.destroy()
        Mainform(self.master, class_id, self.data, self.theme).mainloop()

    def populate_table(self):
        """Populate the table with class data where archive = 'No', sorted by Company (A-Z)."""
        sorted_classes = sorted(
            self.classes.items(),
            key=lambda item: item[1].get("metadata", {}).get("Company", "Unknown")
        )
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
        self.destroy()
        Mainform(self.master, class_id, self.data, self.theme).mainloop()

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
        MetadataForm(
            parent=self,
            class_id=None,
            default_values={},
            theme=self.theme,
            on_metadata_save=self.refresh,
            context="launcher"  # Pass context as "launcher"
        ).mainloop()

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
        self.destroy()
        ArchiveManager(self.master, self.data, self.theme).mainloop()

    def open_ttr_window(self):
        """Open the TTR window by running test_scrollbar.py."""
        script_path = os.path.join("tests", "test_scrollbar.py")  # Adjust path to the script
        subprocess.Popen(["python", script_path])  # Launch the new script

    def open_settings(self):
        """Open the settings window."""
        SettingsForm(self, self.theme, self.refresh_launcher)

    def refresh_launcher(self, theme=None):
        """Refresh the launcher after settings are saved."""
        if theme:
            self.theme = theme
        self.theme_config = self.load_theme_config()
        self.configure_theme()
        self.refresh()

    def refresh(self):
        """Refresh the Launcher."""
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()

    def on_close(self):
        """Handle Launcher close event."""
        confirm = messagebox.askyesno("Exit", "Do you want to back up your data before exiting?", parent=self)
        if confirm:
            save_data(self.data)
        self.destroy()

    def generate_next_class_id(self, existing_class_ids):
        """Generate the next unique class ID."""
        existing_ids = [int(cid[3:]) for cid in existing_class_ids if cid.startswith("OLO")]
        next_id = max(existing_ids, default=0) + 1
        return f"OLO{next_id:03d}"

    def save_metadata(self):
        """Save metadata for the class."""
        logging.debug("Saving metadata...")
        class_no = self.entries["class_no"]["var"].get().strip().upper()  # Ensure class_no is uppercase

        # Validate that the class_no is unique
        if class_no in self.data.get("classes", {}) and not self.is_edit:
            messagebox.showerror(
                "Duplicate Class ID",
                f"Class ID '{class_no}' already exists. Please use a unique Class ID.",
                parent=self
            )
            logging.warning(f"Attempted to save duplicate Class ID: {class_no}")
            return

        # Collect metadata from the form
        metadata = {}
        for key, entry in self.entries.items():
            value = entry["var"].get().strip()

            # Apply formatting for specific fields
            if key == "class_no":
                value = value.upper()  # Ensure class_no is uppercase
            elif key == "Company":
                # Capitalize the first letter of each word while preserving existing uppercase letters
                value = " ".join(word if word.isupper() else word.capitalize() for word in value.split())

            metadata[key] = value

        # Save the metadata
        if not self.is_edit:
            # Add a new class
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
            logging.debug(f"New class added: {class_no}")
        else:
            # Update an existing class
            self.data["classes"][self.class_id]["metadata"] = metadata
            logging.debug(f"Class {self.class_id} updated.")

        # Save the updated data to the file
        save_data(self.data)

        # Handle context-specific behavior
        if self.context == "launcher":
            # Close the Launcher and open the Mainform with the new class
            self.master.destroy()  # Close the Launcher
            from src.ui.mainform import Mainform  # Import Mainform
            Mainform(self.master, class_no, self.data, self.theme).mainloop()
        elif self.context == "mainform":
            # Refresh the Mainform
            self.master.refresh()

        # Close the MetadataForm
        self.destroy()