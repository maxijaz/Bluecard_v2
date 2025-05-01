import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import load_data, save_data

class ArchiveManager(tk.Toplevel):
    def __init__(self, parent, data, theme):
        super().__init__(parent)
        self.parent = parent  # Reference to the parent window
        self.theme = theme
        self.title("Archive Manager")
        self.geometry("450x400")  # Adjusted window size
        self.center_window(450, 400)
        self.resizable(False, False)

        # Apply theme
        self.configure_theme()

        # Load archived class data
        self.data = data
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.close_manager)

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
        """Create the table and buttons."""
        # Frame for the table and scrollbar
        table_frame = tk.Frame(self, bg=self["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Table for archived class data
        self.tree = ttk.Treeview(
            table_frame,
            columns=("Class No", "Company", "Archived"),
            show="headings",
            height=8,  # Limit to 8 rows
            yscrollcommand=scrollbar.set
        )
        self.tree.heading("Class No", text="Class No", anchor="center")
        self.tree.heading("Company", text="Company", anchor="center")
        self.tree.heading("Archived", text="Archived", anchor="center")

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

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        # Center the buttons
        buttons_inner_frame = tk.Frame(button_frame, bg=self["bg"])
        buttons_inner_frame.pack(anchor="center")

        # Arrange buttons with fixed width
        btn_restore = tk.Button(buttons_inner_frame, text="Restore", command=self.restore_class, width=10)
        btn_delete = tk.Button(buttons_inner_frame, text="Delete", command=self.delete_class, width=10)
        btn_cancel = tk.Button(buttons_inner_frame, text="Cancel", command=self.close_manager, width=10)

        # Use grid layout for buttons
        btn_restore.grid(row=0, column=0, padx=5, pady=5)
        btn_delete.grid(row=0, column=1, padx=5, pady=5)
        btn_cancel.grid(row=0, column=2, padx=5, pady=5)

    def populate_table(self):
        """Populate the table with archived class data."""
        self.tree.delete(*self.tree.get_children())  # Clear existing rows
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
            save_data(self.data)  # Save changes to file
            self.populate_table()  # Refresh the table

    def delete_class(self):
        """Delete the selected archived class."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to delete.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno(
            "Delete Class",
            f"Delete {class_id}, this cannot be undone.",
            icon="warning",
            parent=self  # Ensure the dialog is modal to this window
        )
        if confirm:
            del self.classes[class_id]  # Delete the class
            save_data(self.data)  # Save changes to file
            self.populate_table()  # Refresh the table

    def close_manager(self):
        """Close the Archive Manager and reopen the Launcher."""
        self.destroy()  # Close the Archive Manager
        from src.ui.launcher import Launcher  # Lazy import to avoid circular import
        Launcher(self.parent, self.theme).mainloop()  # Reopen the Launcher