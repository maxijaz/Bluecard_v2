import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, data, theme, on_metadata_save):
        super().__init__(parent)
        self.theme = theme
        self.class_id = class_id  # Class ID (e.g., OLO123)
        self.data = data
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher
        self.title("Add / Edit Class Information")
        self.geometry("450x650")
        self.center_window(450, 650)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make MetadataForm always on top

        # Determine if this is an edit or add operation
        self.is_edit = bool(self.class_id)
        self.metadata = self.data["classes"].get(self.class_id, {}).get("metadata", {}) if self.is_edit else {}

        # Debugging: Print class_id and metadata
        print(f"Class ID: {self.class_id}")
        print(f"Metadata: {self.metadata}")

        # Apply theme
        self.configure_theme()

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.close_form)

    def configure_theme(self):
        """Apply the selected theme to the Metadata Form."""
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

        # Bind double-click event to open the Edit Class form
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
        """Handle double-click on a table row to open the Edit Class form."""
        selected_item = self.tree.selection()
        if not selected_item:
            return  # Do nothing if no row is selected
        self.edit_class()

    def save_metadata(self):
        """Save metadata for the class."""
        if not self.entries["class_no"].get() and not self.is_edit:
            messagebox.showerror("Error", "Class No is required for new classes.", parent=self)
            return

        if not self.entries["Company"].get():
            messagebox.showerror("Error", "Company is required.", parent=self)
            return

        # Save metadata
        metadata = {key: entry.get() for key, entry in self.entries.items() if key != "class_no"}
        class_no = self.entries["class_no"].get()

        if self.is_edit:
            self.data["classes"][self.class_id]["metadata"] = metadata
        else:
            # Add new class
            if class_no in self.data["classes"]:
                messagebox.showerror("Error", f"Class No '{class_no}' already exists.", parent=self)
                return
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}

        # Save changes to the data
        try:
            save_data(self.data)
            messagebox.showinfo("Success", "Metadata saved successfully!", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save metadata: {e}", parent=self)

        # Notify the parent to refresh
        self.on_metadata_save()

        # Close the form
        self.destroy()

    def placeholder(self):
        """Placeholder for future functionality."""
        messagebox.showinfo("Placeholder", "This feature is under development.", parent=self)

    def close_form(self):
        """Close the Metadata Form."""
        self.destroy()