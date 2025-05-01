import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data, generate_next_student_id
from src.ui.student_form import StudentForm

class StudentManager(tk.Toplevel):
    def __init__(self, parent, students, refresh_callback):
        super().__init__(parent)
        self.students = students
        self.refresh_callback = refresh_callback

        self.title("Student Active Manager")
        self.geometry("675x500")
        self.center_window(675, 500)
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
        # Treeview for student data
        self.tree = ttk.Treeview(self, columns=("Name", "Nickname", "Note", "Active"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Nickname", text="Nickname")
        self.tree.heading("Note", text="Note")
        self.tree.heading("Active", text="Active")

        # Set column widths
        self.tree.column("Name", width=150, anchor="w")
        self.tree.column("Nickname", width=100, anchor="w")
        self.tree.column("Note", width=300, anchor="w")
        self.tree.column("Active", width=100, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add hover and click effects
        self.tree.bind("<Motion>", self.on_hover)
        self.tree.bind("<Button-1>", self.on_click)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        # Center the buttons
        buttons_inner_frame = tk.Frame(button_frame)
        buttons_inner_frame.pack(anchor="center")

        tk.Button(buttons_inner_frame, text="Edit", command=self.edit_student, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_inner_frame, text="Active", command=self.set_active, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_inner_frame, text="Not Active", command=self.set_inactive, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_inner_frame, text="Delete", command=self.delete_student, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_inner_frame, text="Cancel", command=self.close_form, width=12).pack(side=tk.LEFT, padx=5)

        # Add a button to test adding a new student
        tk.Button(self, text="Add Student", command=self.test_add_student, width=12).pack(side=tk.LEFT, padx=5)

    def on_hover(self, event):
        """Handle hover effect for Treeview rows."""
        row_id = self.tree.identify_row(event.y)
        # Reset hover effect for all rows
        for row in self.tree.get_children():
            self.tree.item(row, tags=())
        # Apply hover effect to the current row
        if row_id:
            self.tree.tag_configure("hover", background="#d0e7ff")  # Light blue for hover
            self.tree.item(row_id, tags=("hover",))

    def on_click(self, event):
        """Handle click effect for Treeview rows."""
        row_id = self.tree.identify_row(event.y)
        # Reset click effect for all rows
        for row in self.tree.get_children():
            self.tree.item(row, tags=())
        # Apply click effect to the current row
        if row_id:
            self.tree.tag_configure("selected", background="#1E90FF", foreground="white")  # Blue for selected row
            self.tree.item(row_id, tags=("selected",))

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
        self.refresh_data()  # Refresh data without closing the form

    def set_inactive(self):
        """Set the selected student as inactive."""
        self.update_student_status("No")
        self.refresh_data()  # Refresh data without closing the form

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
        """Delete the selected student from the class data."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a student to delete.", parent=self)
            return

        # Debug: Log the current state of the students dictionary
        print("[DEBUG] Current students data before deletion:", self.students)

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Delete Student",
            "Are you sure you want to delete the selected student(s)? This action cannot be undone.",
            parent=self
        )
        if not confirm:
            return

        # Delete each selected student
        for selected_item in selected_items:
            student_name = self.tree.item(selected_item, "values")[0]
            print(f"[DEBUG] Selected student name for deletion: {student_name}")  # Debug: Log the selected student name
            student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
            print(f"[DEBUG] Found student ID for deletion: {student_id}")  # Debug: Log the student ID
            if student_id:
                # Remove the student from the class data
                self.students.pop(student_id, None)
                print(f"[DEBUG] Deleted student ID: {student_id}")  # Debug: Log the deletion

        # Debug: Log the updated state of the students dictionary
        print("[DEBUG] Updated students data after deletion:", self.students)

        # Save the updated data to the JSON file
        save_data(self.students)

        # Refresh the table and Mainform
        self.refresh_data()

    def add_student(self, student_data: dict):
        """Add a new student to the class."""
        if not validate_student_data(student_data):
            return  # Do not proceed if validation fails

        # Generate a unique student ID
        new_student_id = generate_next_student_id(self.students)
        print(f"[DEBUG] Generated new student ID: {new_student_id}")

        # Add the new student to the dictionary
        self.students[new_student_id] = student_data
        print(f"[DEBUG] Added new student: {new_student_id} -> {student_data}")

        # Save the updated students data
        save_data(self.students)

        # Refresh the table and Mainform
        self.refresh_data()

    def refresh_data(self):
        """Refresh the data on the StudentManager and Mainform."""
        self.populate_table()  # Refresh the table in StudentManager
        self.refresh_callback()  # Refresh the Mainform

    def close_form(self):
        """Close the form."""
        self.destroy()

    def test_add_student(self):
        """Test adding a new student."""
        new_student = {
            "name": "New Student",
            "nickname": "Newbie",
            "gender": "Other",
            "score": "",
            "pre_test": "",
            "post_test": "",
            "note": "Test student",
            "active": "Yes",
            "attendance": {}
        }
        self.add_student(new_student)