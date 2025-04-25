import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import load_data, save_data

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bluecard Launcher")
        self.geometry("800x600")

        # Load class data
        self.data = load_data()
        self.classes = self.data.get("classes", {})

        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        # Table for class data
        self.tree = ttk.Treeview(self, columns=("Class No", "Company", "Archived"), show="headings")
        self.tree.heading("Class No", text="Class No")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Archived", text="Archived")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Open", command=self.open_class).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_class).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add New Class", command=self.add_new_class).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Archive", command=self.archive_class).pack(side=tk.LEFT, padx=5)

    def populate_table(self):
        for class_id, class_data in self.classes.items():
            metadata = class_data.get("metadata", {})
            company = metadata.get("Company", "Unknown")
            archived = metadata.get("archive", "No")
            self.tree.insert("", tk.END, values=(class_id, company, archived))

    def open_class(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to open.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        messagebox.showinfo("Open Class", f"Opening class: {class_id}")
        # TODO: Open Mainform for the selected class

    def edit_class(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to edit.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        messagebox.showinfo("Edit Class", f"Editing class: {class_id}")
        # TODO: Open Metadata Editor for the selected class

    def add_new_class(self):
        messagebox.showinfo("Add New Class", "Opening Metadata Editor for a new class.")
        # TODO: Open Metadata Editor with a blank form

    def archive_class(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a class to archive.")
            return
        class_id = self.tree.item(selected_item, "values")[0]
        self.classes[class_id]["metadata"]["archive"] = "Yes"
        save_data(self.data)
        messagebox.showinfo("Archive Class", f"Class {class_id} archived.")
        self.tree.delete(selected_item)

if __name__ == "__main__":
    app = Launcher()
    app.mainloop()