import tkinter as tk
from tkinter import messagebox
from src.ui.launcher import Launcher
from src.ui.metadata_form import MetadataForm

class Mainform(tk.Toplevel):
    def __init__(self, class_id, data, theme):
        super().__init__()
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.title(f"Mainform - Class {class_id}")
        self.geometry("800x600")
        self.resizable(True, True)

        # Apply theme
        self.configure_theme()

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_theme(self):
        """Apply the selected theme to the Mainform."""
        if self.theme == "dark":
            self.configure(bg="black")
        elif self.theme == "clam":
            self.configure(bg="lightblue")
        else:  # Default theme
            self.configure(bg="white")

    def create_widgets(self):
        # Header
        tk.Label(self, text=f"Mainform for Class {self.class_id}", font=("Arial", 16)).pack(pady=20)

        # Edit Metadata Button
        tk.Button(self, text="Edit Metadata", command=self.edit_metadata).pack(pady=10)

        # Close Button
        tk.Button(self, text="Close", command=self.on_close).pack(pady=10)

    def edit_metadata(self):
        """Open the MetadataForm to edit metadata for the current class."""
        MetadataForm(self, self.class_id, self.data, self.theme, self.refresh_mainform).mainloop()

    def refresh_mainform(self):
        """Refresh the Mainform after metadata is edited."""
        self.title(f"Mainform - Class {self.class_id}")
        # Add any additional refresh logic here (e.g., reload widgets)

    def on_close(self):
        """Handle Mainform close event and reopen Launcher."""
        self.destroy()
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        Launcher(root, self.theme).mainloop()

if __name__ == "__main__":
    # Example usage
    data = load_data()
    app = Mainform("OLO123", data, "default")
    app.mainloop()