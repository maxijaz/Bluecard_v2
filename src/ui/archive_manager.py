import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import load_data, save_data

class ArchiveManager(tk.Toplevel):
    def __init__(self, parent, data, theme):
        super().__init__(parent)
        self.theme = theme
        self.title("Archive Manager")
        self.geometry("650x500")
        self.center_window(650, 500)
        self.resizable(False, False)

        # Apply theme
        self.configure_theme()

        # Load archived class data
        self.data = data
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

    def configure_theme(self):
        """Apply the selected theme to the Archive Manager."""
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
        # Table for archived class data
        self.tree = ttk.Treeview(self, columns=("Class No", "Company", "Archived"), show="headings")
        self.tree.heading("Class No", text="Class No")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Archived", text="Archived")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Restore", command=self.restore_class).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_class).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.close_manager).pack(side=tk.LEFT, padx=5)

    def populate_table(self):
        """Populate the table with archived class data."""
        for class_id, class_data in self.classes.items():
            metadata = class_data.get("metadata", {})
            if metadata.get("archive", "No") == "Yes":
                company = metadata.get("Company", "Unknown")
                archived = metadata.get("archive", "Yes")
                self.tree.insert("", tk.END, values=(class_id, company, archived))

    def restore_class(self):
        """Restore the selected archived class."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to restore.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Restore Class", f"Are you sure you want to restore class {class_id}?")
        if confirm:
            self.classes[class_id]["metadata"]["archive"] = "No"
            save_data(self.data)
            self.populate_table()

    def delete_class(self):
        """Delete the selected archived class."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to delete.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Delete Class", f"Are you sure you want to delete class {class_id}?")
        if confirm:
            del self.classes[class_id]
            save_data(self.data)
            self.populate_table()

    def close_manager(self):
        """Close the Archive Manager."""
        self.destroy()