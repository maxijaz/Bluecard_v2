import tkinter as tk
from tkinter import ttk, messagebox
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager

class Mainform(tk.Toplevel):
    def __init__(self, master, class_id, data, theme):
        super().__init__(master)  # Pass the master to the Toplevel constructor
        self.class_id = class_id
        self.data = data
        self.theme = theme
        self.metadata = self.data["classes"][self.class_id]["metadata"]
        self.students = self.data["classes"][self.class_id]["students"]

        self.title(f"Class Information - {self.class_id}")
        self.geometry("1200x700")
        self.attributes("-topmost", True)  # Keep Mainform on top
        self.state("zoomed")  # Open maximized

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
        """Create the layout and fields for the Mainform."""
        # Header Section
        header_frame = tk.Frame(self, bg=self["bg"])
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        fields = [
            ("Company:", self.metadata.get("Company", "")),
            ("Consultant:", self.metadata.get("Consultant", "")),
            ("Teacher:", self.metadata.get("Teacher", "")),
            ("Room:", self.metadata.get("Room", "")),
            ("Course Book:", self.metadata.get("CourseBook", "")),
            ("Course Hours:", self.metadata.get("CourseHours", "")),
            ("Class Time (hrs):", self.metadata.get("ClassTime", "")),
            ("Max Classes:", self.metadata.get("MaxClasses", "")),
            ("Start Date:", self.metadata.get("StartDate", "")),
            ("Finish Date:", self.metadata.get("FinishDate", "")),
            ("Days:", self.metadata.get("Days", "")),
            ("Time:", self.metadata.get("Time", "")),
            ("Notes:", self.metadata.get("Notes", "")),
        ]

        for i, (label_text, value) in enumerate(fields):
            tk.Label(header_frame, text=label_text, font=("Arial", 12, "bold"), bg=self["bg"]).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            tk.Label(header_frame, text=value, font=("Arial", 12), bg=self["bg"]).grid(row=i, column=1, sticky="w", padx=10, pady=5)

        # Buttons Section
        button_frame = tk.Frame(self, bg=self["bg"])
        button_frame.pack(fill=tk.X, pady=10)

        buttons = [
            ("Add Student", self.add_student),
            ("Edit Student", self.edit_student),
            ("Remove Student", self.remove_student),
            ("Manage Students", self.manage_students),
            ("Add Date", self.placeholder),
            ("Edit Date", self.placeholder),
            ("Metadata", self.edit_metadata),
            ("Settings", self.open_settings),
        ]

        for i, (text, command) in enumerate(buttons):
            tk.Button(button_frame, text=text, command=command, width=15).grid(row=i // 4, column=i % 4, padx=10, pady=5)

        # Attendance Table
        attendance_frame = tk.Frame(self, bg=self["bg"])
        attendance_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(attendance_frame, text="Attendance Table", font=("Arial", 16, "bold"), bg=self["bg"]).pack(anchor="w", pady=5)

        # Define columns for attendance table
        columns = ["#", "Name", "Nickname", "Score"] + list(self.get_attendance_dates()) + ["P", "A", "L", "Attendance", "Pre-test", "Post-test"]
        self.tree = ttk.Treeview(attendance_frame, columns=columns, show="headings")

        # Configure column headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Populate attendance table
        self.populate_attendance_table()

    def get_attendance_dates(self):
        """Get all unique attendance dates from student data."""
        dates = set()
        for student_data in self.students.values():
            dates.update(student_data.get("attendance", {}).keys())
        return sorted(dates)

    def populate_attendance_table(self):
        """Populate the attendance table with student data."""
        for idx, (student_id, student_data) in enumerate(self.students.items(), start=1):
            if student_data.get("active", "Yes") == "Yes":  # Only show active students
                attendance = student_data.get("attendance", {})
                attendance_values = [attendance.get(date, "-") for date in self.get_attendance_dates()]
                present_count = sum(1 for v in attendance.values() if v == "P")
                absent_count = sum(1 for v in attendance.values() if v == "A")
                late_count = sum(1 for v in attendance.values() if v == "L")
                self.tree.insert("", tk.END, values=(
                    idx,
                    student_data["name"],
                    student_data["nickname"],
                    student_data["score"],
                    *attendance_values,
                    present_count,
                    absent_count,
                    late_count,
                    present_count,  # Total attendance
                    student_data["pre_test"],
                    student_data["post_test"],
                ))

    def add_student(self):
        """Open the Add Student form."""
        StudentForm(self, None, self.students, self.refresh).mainloop()

    def edit_student(self):
        """Open the Edit Student form for the selected student."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to edit.", parent=self)
            return
        student_name = self.tree.item(selected_item, "values")[1]
        student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
        if student_id:
            StudentForm(self, student_id, self.students, self.refresh).mainloop()

    def remove_student(self):
        """Remove the selected student."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to remove.", parent=self)
            return
        student_name = self.tree.item(selected_item, "values")[1]
        student_id = next((sid for sid, sdata in self.students.items() if sdata["name"] == student_name), None)
        if student_id:
            confirm = messagebox.askyesno("Remove Student", f"Are you sure you want to remove {student_name}?", parent=self)
            if confirm:
                self.students[student_id]["active"] = "No"
                save_data(self.data)
                self.refresh()

    def manage_students(self):
        """Open the Student Active Manager."""
        StudentManager(self, self.students, self.refresh).mainloop()

    def edit_metadata(self):
        """Open the Edit Metadata form."""
        MetadataForm(self, self.class_id, self.data, self.theme, self.refresh).mainloop()

    def open_settings(self):
        """Open the Settings form."""
        messagebox.showinfo("Settings", "Settings functionality is under development.", parent=self)

    def placeholder(self):
        """Placeholder for future functionality."""
        messagebox.showinfo("Placeholder", "This feature is under development.", parent=self)

    def refresh(self):
        """Refresh the Mainform."""
        for widget in self.winfo_children():
            widget.destroy()  # Clear all widgets
        self.create_widgets()  # Recreate widgets

    def on_close(self):
        """Handle Mainform close event."""
        from src.ui.launcher import Launcher  # Lazy import to avoid circular dependency
        self.destroy()  # Close the Mainform
        Launcher(self.master, self.theme).mainloop()  # Reopen the Launcher

if __name__ == "__main__":
    # Example usage
    data = load_data()
    app = Mainform("OLO123", data, "default")
    app.mainloop()