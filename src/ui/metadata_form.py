import tkinter as tk
from tkinter import messagebox
from src.logic.parser import save_data

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, data, theme, on_metadata_save):
        super().__init__(parent)
        self.theme = theme
        self.class_id = class_id
        self.data = data
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher or Mainform
        self.title("Metadata Form")
        self.geometry("400x300")
        self.center_window(400, 300)
        self.resizable(False, False)

        # Apply theme
        self.configure_theme()

        # Create UI components
        self.create_widgets()

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
        # Placeholder for metadata fields
        tk.Label(self, text=f"Editing Metadata for Class {self.class_id or 'New Class'}", font=("Arial", 16)).pack(pady=10)
        tk.Button(self, text="Save", command=self.save_metadata).pack(pady=10)
        tk.Button(self, text="Cancel", command=self.close_form).pack(pady=10)

    def save_metadata(self):
        """Save metadata for the class."""
        # Placeholder logic for saving metadata
        if self.class_id:
            messagebox.showinfo("Save Metadata", f"Metadata for class {self.class_id} saved.")
        else:
            messagebox.showinfo("Save Metadata", "New class metadata saved.")
        save_data(self.data)
        self.on_metadata_save()  # Trigger callback to refresh Launcher or Mainform
        self.destroy()

    def close_form(self):
        """Close the Metadata Form."""
        self.destroy()