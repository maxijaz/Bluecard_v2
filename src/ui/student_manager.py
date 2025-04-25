import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data
from src.ui.student_form import StudentForm

class StudentManager(tk.Toplevel):
    def __init__(self, parent, students, refresh_callback):
        super().__init__(parent)
        self.students = students
        self.refresh_callback = refresh_callback

        self.title("Student Active Manager")
        self.geometry("650x500")
        self.center_window(650, 500)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.close_form)

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create the layout and fields for managing students."""
        self.tree = ttk.Treeview(self, columns=("Name", "Nickname", "Note", "Active"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Nickname", text="Nickname")
        self.tree.heading("Note", text="Note")
        self.tree.heading("Active", text="Active")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Edit", command=self.edit_student, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Active", command=self.set_active, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Not Active", command=self.set_inactive, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_student, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.close_form, width=12).pack(side=tk.LEFT, padx=5)

    def populate_table(self):
        """Populate the table with student data."""
        for student_id, student_data in self.students.items():
            self.tree.insert("", tk.END, values=(
                student_data["name"],
                student_data["nickname"],
                student_data["note"],
                student_data["active"],
            ))

    def edit_student(self):
        """Edit the selected student."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to edit.", parent=self)
            return
        student_name = self.tree.item(selected_item, "values")[0]
        student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
        if student_id:
            StudentForm(self, student_id, self.students, self.refresh_callback).mainloop()

    def set_active(self):
        """Set the selected student as active."""
        self.update_student_status("Yes")

    def set_inactive(self):
        """Set the selected student as inactive."""
        self.update_student_status("No")

    def update_student_status(self, status):
        """Update the active status of the selected student."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student.", parent=self)
            return
        student_name = self.tree.item(selected_item, "values")[0]
        student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
        if student_id:
            self.students[student_id]["active"] = status
            save_data(self.students)
            self.refresh_callback()
            self.populate_table()

    def delete_student(self):
        """Delete the selected student."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to delete.", parent=self)
            return
        student_name = self.tree.item(selected_item, "values")[0]
        student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
        if student_id:
            confirm = messagebox.askyesno("Delete Student", f"Are you sure you want to delete {student_name}?", parent=self)
            if confirm:
                del self.students[student_id]
                save_data(self.students)
                self.refresh_callback()
                self.populate_table()

    def close_form(self):
        """Close the form."""
        self.destroy()