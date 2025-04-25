import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import load_data, save_data

class Mainform(tk.Toplevel):
    def __init__(self, class_id, data):
        super().__init__()
        self.title("Class Information - MainForm")
        self.state("zoomed")  # Maximize the window
        self.resizable(True, True)

        # Store class data
        self.class_id = class_id
        self.data = data
        self.class_data = self.data["classes"].get(class_id, {})
        self.metadata = self.class_data.get("metadata", {})
        self.students = self.class_data.get("students", {})

        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Label(self, text="Class Information - MainForm", font=("Arial", 20, "bold"))
        header.pack(pady=10)

        # Metadata Section
        metadata_frame = tk.Frame(self)
        metadata_frame.pack(fill=tk.X, padx=10, pady=5)

        self.add_metadata_row(metadata_frame, "Company:", self.metadata.get("Company", "N/A"), 0)
        self.add_metadata_row(metadata_frame, "Consultant:", self.metadata.get("Consultant", "N/A"), 1)
        self.add_metadata_row(metadata_frame, "Teacher:", self.metadata.get("Teacher", "N/A"), 2)
        self.add_metadata_row(metadata_frame, "Room:", self.metadata.get("Room", "N/A"), 3)
        self.add_metadata_row(metadata_frame, "Course Book:", self.metadata.get("CourseBook", "N/A"), 4)
        self.add_metadata_row(metadata_frame, "Start Date:", self.metadata.get("StartDate", "N/A"), 5)
        self.add_metadata_row(metadata_frame, "Finish Date:", self.metadata.get("FinishDate", "N/A"), 6)
        self.add_metadata_row(metadata_frame, "Days:", self.metadata.get("Days", "N/A"), 7)
        self.add_metadata_row(metadata_frame, "Time:", self.metadata.get("Time", "N/A"), 8)
        self.add_metadata_row(metadata_frame, "Notes:", self.metadata.get("Notes", "N/A"), 9)

        # Attendance Table
        table_frame = tk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Name", "Nickname", "Score", "Attendance", "Pre-test", "Post-test"),
            show="headings",
        )
        self.tree.heading("Name", text="Name")
        self.tree.heading("Nickname", text="Nickname")
        self.tree.heading("Score", text="Score")
        self.tree.heading("Attendance", text="Attendance")
        self.tree.heading("Pre-test", text="Pre-test")
        self.tree.heading("Post-test", text="Post-test")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Populate table
        self.populate_table()

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)

        tk.Button(button_frame, text="Add Student", command=self.add_student).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit Student", command=self.edit_student).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Student", command=self.remove_student).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Manage Students", command=self.manage_students).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Date", command=self.add_date).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit Date", command=self.edit_date).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Metadata", command=self.edit_metadata).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Settings", command=self.open_settings).pack(side=tk.LEFT, padx=5)

    def add_metadata_row(self, frame, label, value, row):
        """Helper function to add a metadata row."""
        tk.Label(frame, text=label, font=("Arial", 14, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5)
        tk.Label(frame, text=value, font=("Arial", 14)).grid(row=row, column=1, sticky=tk.W)

    def populate_table(self):
        """Populate the attendance table with active students."""
        for student_id, student_data in self.students.items():
            if student_data.get("active", "No") == "Yes":
                name = student_data.get("name", "N/A")
                nickname = student_data.get("nickname", "N/A")
                score = student_data.get("score", "N/A")
                attendance = ", ".join(student_data.get("attendance", {}).keys())
                pre_test = student_data.get("pre_test", "N/A")
                post_test = student_data.get("post_test", "N/A")
                self.tree.insert("", tk.END, values=(name, nickname, score, attendance, pre_test, post_test))

    def add_student(self):
        messagebox.showinfo("Add Student", "Add Student functionality not implemented yet.")

    def edit_student(self):
        messagebox.showinfo("Edit Student", "Edit Student functionality not implemented yet.")

    def remove_student(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to remove.")
            return
        confirm = messagebox.askyesno("Remove Student", "Are you sure you want to remove this student?")
        if confirm:
            student_name = self.tree.item(selected_item, "values")[0]
            for student_id, student_data in self.students.items():
                if student_data.get("name") == student_name:
                    student_data["active"] = "No"
                    save_data(self.data)
                    self.tree.delete(selected_item)
                    break

    def manage_students(self):
        messagebox.showinfo("Manage Students", "Manage Students functionality not implemented yet.")

    def add_date(self):
        messagebox.showinfo("Add Date", "Add Date functionality not implemented yet.")

    def edit_date(self):
        messagebox.showinfo("Edit Date", "Edit Date functionality not implemented yet.")

    def edit_metadata(self):
        messagebox.showinfo("Metadata", "Metadata functionality not implemented yet.")

    def open_settings(self):
        messagebox.showinfo("Settings", "Settings functionality not implemented yet.")

if __name__ == "__main__":
    # Example usage
    data = load_data()
    app = Mainform("OLO123", data)
    app.mainloop()