import tkinter as tk
from tkinter import ttk, messagebox
from logic.parser import save_data

class StudentForm(tk.Toplevel):
    def __init__(self, parent, student_id, students, refresh_callback):
        super().__init__(parent)
        self.student_id = student_id
        self.students = students
        self.refresh_callback = refresh_callback
        self.student_data = self.students.get(self.student_id, {}) if self.student_id else {}

        self.title("Add / Edit Student Information")
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
        """Create the layout and fields for editing student information."""
        fields = [
            ("Student ID:", "student_id"),
            ("Name:", "name"),
            ("Nickname:", "nickname"),
            ("Gender:", "gender"),
            ("Score:", "score"),
            ("Pre-Test:", "pre_test"),
            ("Post-Test:", "post_test"),
            ("Note:", "note"),
            ("Active:", "active"),
        ]

        self.entries = {}

        for i, (label_text, key) in enumerate(fields):
            tk.Label(self, text=label_text, font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="e", padx=10, pady=5)

            if key == "gender":
                # Gender toggle buttons
                gender_frame = tk.Frame(self)
                gender_frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")
                self.gender_var = tk.StringVar(value=self.student_data.get(key, "Female"))
                tk.Radiobutton(gender_frame, text="Male", variable=self.gender_var, value="Male").pack(side=tk.LEFT)
                tk.Radiobutton(gender_frame, text="Female", variable=self.gender_var, value="Female").pack(side=tk.LEFT)
            elif key == "active":
                # Active toggle buttons
                active_frame = tk.Frame(self)
                active_frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")
                self.active_var = tk.StringVar(value=self.student_data.get(key, "Yes"))
                tk.Radiobutton(active_frame, text="Yes", variable=self.active_var, value="Yes").pack(side=tk.LEFT)
                tk.Radiobutton(active_frame, text="No", variable=self.active_var, value="No").pack(side=tk.LEFT)
            else:
                entry = tk.Entry(self, width=40)
                entry.grid(row=i, column=1, padx=10, pady=5)
                entry.insert(0, self.student_data.get(key, ""))  # Pre-fill with existing data
                self.entries[key] = entry

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save", command=self.save_student, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.close_form, width=10).pack(side=tk.LEFT, padx=10)

    def save_student(self):
        """Save student information."""
        if not self.entries["name"].get():
            messagebox.showerror("Error", "Name is required.", parent=self)
            return

        student_data = {
            "name": self.entries["name"].get(),
            "nickname": self.entries["nickname"].get(),
            "gender": self.gender_var.get(),
            "score": self.entries["score"].get(),
            "pre_test": self.entries["pre_test"].get(),
            "post_test": self.entries["post_test"].get(),
            "note": self.entries["note"].get(),
            "active": self.active_var.get(),
            "attendance": self.student_data.get("attendance", {}),
        }

        if self.student_id:
            self.students[self.student_id] = student_data
        else:
            new_id = f"S{len(self.students) + 1:03}"
            self.students[new_id] = student_data

        save_data(self.students)
        self.refresh_callback()
        self.close_form()

    def close_form(self):
        """Close the form."""
        self.destroy()