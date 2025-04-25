import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import load_data
from src.ui.settings import SettingsForm

class Launcher(tk.Toplevel):
    def __init__(self, root, theme):
        super().__init__(root)
        self.theme = theme
        self.title("Bluecard Launcher")
        self.geometry("450x450")
        self.center_window(450, 450)
        self.resizable(False, False)

        # Apply theme
        self.configure_theme()

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

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
        # Table for class data
        self.tree = ttk.Treeview(self, columns=("Class No", "Company", "Archived"), show="headings")
        self.tree.heading("Class No", text="Class No")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Archived", text="Archived")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate table
        self.populate_table()

        # Buttons (Centralized)
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        buttons = tk.Frame(button_frame, bg=self["bg"])
        buttons.pack(anchor=tk.CENTER)

        tk.Button(buttons, text="Open", command=self.open_class).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Settings", command=self.open_settings).pack(side=tk.LEFT, padx=5)

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
            messagebox.showwarning("No Selection", "Please select a class to open.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        self.destroy()  # Close the Launcher
        # Open Mainform (not shown here)

    def open_settings(self):
        """Open the Settings form."""
        self.destroy()  # Close the current Launcher
        SettingsForm(self, self.theme, self.reopen_launcher).mainloop()

    def reopen_launcher(self, new_theme):
        """Reopen the Launcher with the new theme."""
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        Launcher(root, new_theme).mainloop()