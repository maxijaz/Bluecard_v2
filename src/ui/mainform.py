import tkinter as tk
from tkinter import ttk, messagebox
from logic.parser import load_data, save_data
from ui.student_form import StudentForm
from .metadata_form import MetadataForm
from .student_manager import StudentManager
from datetime import datetime

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
        # Separator above the header label
        separator = tk.Frame(self, height=2, bg="black", bd=0, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=10, pady=1)

        # Header Section
        header_frame = tk.Frame(self, bg=self["bg"])
        header_frame.pack(fill=tk.X, padx=10, pady=1)

        # Header Label (Centered)
        header_label = tk.Label(header_frame, text="Class Information - MainForm", font=("Arial", 22, "bold"), bg=self["bg"])
        header_label.pack(side=tk.TOP, pady=1)

        # Separator under the header label
        separator = tk.Frame(self, height=2, bg="black", bd=0, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=20, pady=1)

        # Header Columns (1-9)
        header_columns_frame = tk.Frame(self, bg=self["bg"])
        header_columns_frame.pack(fill=tk.X, padx=10, pady=1)

        # Main Layout Frame
        layout_frame = tk.Frame(self, bg=self["bg"])
        layout_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=1)

        # Column 1 and Column 2: Metadata (Labels and Data)
        metadata_fields = [
            ("Company:", self.metadata.get("Company", "")),
            ("Consultant:", self.metadata.get("Consultant", "")),
            ("Teacher:", self.metadata.get("Teacher", "")),
            ("Room:", self.metadata.get("Room", "")),
            ("CourseBook:", self.metadata.get("CourseBook", "")),
        ]
        for i, (label_text, value) in enumerate(metadata_fields):
            tk.Label(layout_frame, text=label_text, font=("Arial", 10, "bold"), bg=self["bg"], anchor="w", width=12).grid(row=i, column=0, sticky="e", padx=1)
            data_box = tk.Text(layout_frame, font=("Arial", 10), bg="white", height=1, width=25, wrap="none", state="disabled")
            data_box.grid(row=i, column=1, sticky="w", padx=1)
            data_box.configure(state="normal")  # Temporarily enable editing to insert text
            data_box.insert("1.0", value)  # Insert the value
            data_box.configure(state="disabled")  # Disable editing again

        # Column 3 and Column 4: Additional Metadata (Labels and Data)
        additional_metadata_fields = [
            (
                "ClassHours:",
                f"{self.metadata.get('CourseHours', '')} / {self.metadata.get('ClassTime', '')} / "
                f"{self.metadata.get('MaxClasses', '')}"
            ),
            ("StartDate:", self.metadata.get("StartDate", "")),
            ("FinishDate:", self.metadata.get("FinishDate", "")),
            ("Days:", self.metadata.get("Days", "")),
            ("Time:", self.metadata.get("Time", "")),
            ("Notes:", self.metadata.get("Notes", "")),
        ]

        for i, (label_text, value) in enumerate(additional_metadata_fields):
            tk.Label(layout_frame, text=label_text, font=("Arial", 10, "bold"), bg=self["bg"], anchor="w", width=12).grid(
                row=i, column=2, sticky="e", padx=(5, 1)
            )
            data_box = tk.Text(layout_frame, font=("Arial", 10), bg="white", height=1, width=25, wrap="none", state="disabled")
            data_box.grid(row=i, column=3, sticky="w", padx=1)
            data_box.configure(state="normal")  # Temporarily enable editing to insert text
            data_box.insert("1.0", value)  # Insert the value
            data_box.configure(state="disabled")  # Disable editing again

        # Configure column weights for dynamic resizing
        layout_frame.columnconfigure(4, weight=1)  # Column 5 takes up remaining space
        layout_frame.columnconfigure(5, weight=0)  # Columns 6–9 do not expand
        layout_frame.columnconfigure(6, weight=0)
        layout_frame.columnconfigure(7, weight=0)
        layout_frame.columnconfigure(8, weight=0)

        # Column 5: Blank (Dynamic Width)
        tk.Label(layout_frame, text="", bg=self["bg"]).grid(row=0, column=4, rowspan=8, sticky="nsew")

        # Column 6: Buttons
        buttons_col_6 = [
            ("Add Ss", self.add_student),
            ("Edit Ss", self.edit_student),
            ("Remove Ss", self.remove_student),
            ("Manage Ss", self.manage_students),
        ]
        for i, (text, command) in enumerate(buttons_col_6):
            tk.Button(layout_frame, text=text, command=command, width=10).grid(row=i, column=5, sticky="e")

        # Column 7: Buttons
        buttons_col_7 = [
            ("Add Date", self.placeholder),
            ("Edit Date", self.placeholder),
            ("Metadata", self.edit_metadata),
            ("Unused 1", self.placeholder),
        ]
        for i, (text, command) in enumerate(buttons_col_7):
            tk.Button(layout_frame, text=text, command=command, width=10).grid(row=i, column=6, sticky="e")

        # Column 8: Buttons
        buttons_col_8 = [
            ("Unused 2", self.placeholder),
            ("Unused 3", self.placeholder),
            ("Unused 4", self.placeholder),
            ("Unused 5", self.placeholder),
        ]
        for i, (text, command) in enumerate(buttons_col_8):
            tk.Button(layout_frame, text=text, command=command, width=10).grid(row=i, column=7, sticky="e")

        # Column 9: Buttons
        buttons_col_9 = [
            ("Unused 6", self.placeholder),
            ("Unused 7", self.placeholder),
            ("Unused 8", self.placeholder),
            ("Unused 9", self.placeholder),
        ]
        for i, (text, command) in enumerate(buttons_col_9):
            tk.Button(layout_frame, text=text, command=command, width=10).grid(row=i, column=8, padx=(0, 5), sticky="e")

        # Separator above the header label
        separator = tk.Frame(self, height=2, bg="black", bd=0, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=10, pady=1)

        # Attendance Table Section
        attendance_frame = tk.Frame(self, bg=self["bg"])
        attendance_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=1)

        # Heading "Attendance Table"
        tk.Label(attendance_frame, text="Attendance Table", font=("Arial", 14, "bold"), bg=self["bg"]).pack(anchor="w", pady=1)

        # Separator above the header label
        separator = tk.Frame(self, height=2, bg="black", bd=0, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=10, pady=1)

        # Define columns for attendance table
        columns = ["#", "Name", "Nickname", "Score"] + list(self.get_attendance_dates()) + ["P", "A", "L", "Attendance", "Pre-test", "Post-test"]
        self.tree = ttk.Treeview(attendance_frame, columns=columns, show="headings")

        # Configure column headings
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), anchor="center", background="#e0e0e0")  # Gray background for headings
        style.configure("Treeview", font=("Arial", 12))  # Data: size 12, regular
        self.tree.configure(style="Treeview")  # Explicitly set the style for the Treeview

        # Configure row hover and selection styles
        style.map(
            "Treeview",
            background=[("selected", "#1E90FF")],  # Darker blue for selected rows
            foreground=[("selected", "white")],  # White text for selected rows
        )

        # Add hover effect using tags
        self.tree.tag_configure("hover", background="#d0e7ff")  # Light blue for hover

        for col in columns:
            if col == "#":
                self.tree.column(col, width=35, anchor="center")  # Fix width for "#"
            elif col == "Name":
                self.tree.column(col, width=150, anchor="w")  # Fix width for "Name", left-aligned
            elif col == "Nickname":
                self.tree.column(col, width=100, anchor="center")  # Fix width for "Nickname"
            elif col == "Score":
                self.tree.column(col, width=100, anchor="center")  # Fix width for "Score"
            else:
                self.tree.column(col, width=75, anchor="center")  # Default width for other columns
            self.tree.heading(col, text=col)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind hover events
        self.tree.bind("<Motion>", self.on_row_hover)
        self.tree.bind("<Leave>", self.on_row_leave)

        # Bind click event to toggle row selection
        self.tree.bind("<Button-1>", self.on_row_click)

        # Populate attendance table
        self.populate_attendance_table()

    def get_attendance_dates(self):
        """Get all unique attendance dates from student data and add empty columns to match MaxClasses."""
        dates = set()
        for student_data in self.students.values():
            attendance = student_data.get("attendance", {})
            dates.update(attendance.keys())  # Collect all dates in full-year format

        # Sort the existing dates
        sorted_dates = sorted(dates)

        # Get MaxClasses from metadata
        max_classes_str = self.metadata.get("MaxClasses", "20")
        max_classes = int(max_classes_str.split()[0])  # Extract the numeric part (e.g., "20" from "20 (1 hour remains)")

        # Add empty date columns if needed
        while len(sorted_dates) < max_classes:
            next_date = f"Empty-{len(sorted_dates) + 1}"  # Placeholder for empty columns
            sorted_dates.append(next_date)

        # Reformat dates for display
        return [
            datetime.strptime(date, "%d/%m/%Y").strftime("%d/%m/%y") if "Empty" not in date else date
            for date in sorted_dates
        ]

    def populate_attendance_table(self):
        """Populate the attendance table with student data."""
        # Get ClassTime from metadata
        class_time = float(self.metadata.get("ClassTime", "2") or "2")  # Default to 2 if missing
        running_total = 0  # Initialize running total

        # Add the first row for the running total
        attendance_dates = self.get_attendance_dates()
        running_total_values = []
        for date in attendance_dates:
            # Increment the running total for every column, including placeholders
            running_total += class_time
            # Format the running total: remove ".0" for whole numbers
            formatted_total = int(running_total) if running_total.is_integer() else running_total
            running_total_values.append(str(formatted_total))

        # Insert the running total row
        self.tree.insert(
            "",
            tk.END,
            values=(
                "",  # Empty for the first column
                "Running Total",  # Label for the row
                "",  # Empty for nickname
                "",  # Empty for score
                *running_total_values,  # Running total for date columns
                "",  # Empty for P
                "",  # Empty for A
                "",  # Empty for L
                "",  # Empty for Attendance
                "",  # Empty for Pre-test
                "",  # Empty for Post-test
            ),
            tags=("running_total",),  # Assign a tag for styling
        )

        # Add the remaining rows for student data
        for idx, (student_id, student_data) in enumerate(self.students.items(), start=1):
            if student_data.get("active", "Yes") == "Yes":  # Only show active students
                attendance = student_data.get("attendance", {})
                # Use reformatted dates for display
                attendance_values = [
                    attendance.get(
                        datetime.strptime(date, "%d/%m/%y").strftime("%d/%m/%Y"), "-"
                    ) if "Empty" not in date else "-"  # Skip placeholder columns
                    for date in attendance_dates
                ]
                present_count = sum(1 for v in attendance.values() if v == "P")
                absent_count = sum(1 for v in attendance.values() if v == "A")
                late_count = sum(1 for v in attendance.values() if v == "L")

                # Determine the tag for alternating row colors
                row_tag = "even" if idx % 2 != 0 else "odd"  # First row is white (even)

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
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
                    ),
                    tags=(row_tag,)  # Assign the tag
                )

        # Configure styles for the tags
        self.tree.tag_configure("running_total", background="#eaeaea", font=("Arial", 10))  # Small font for running total row
        self.tree.tag_configure("odd", background="#ffffff", font=("Arial", 12))  # Original font size for odd rows
        self.tree.tag_configure("even", background="#eaeaea", font=("Arial", 12))  # Original font size for even rows
        self.tree.tag_configure("hover", background="#d0e7ff", font=("Arial", 12))  # Original font size for hover

    def on_row_hover(self, event):
        """Handle row hover event."""
        row_id = self.tree.identify_row(event.y)  # Identify the row under the mouse pointer

        if row_id:
            # Check if the row is the running total row
            if "Running Total" in self.tree.item(row_id, "values"):
                # Reapply the running_total tag to preserve its font size
                self.tree.item(row_id, tags=("running_total",))
            else:
                # Apply hover effect to the current row
                self.tree.item(row_id, tags=("hover",))  # Apply the hover tag to the row

        # Reset the previous row's color
        for row in self.tree.get_children():
            if row != row_id:
                # Check if the row is the running total row
                if "Running Total" in self.tree.item(row, "values"):
                    # Reapply the running_total tag to preserve its font size
                    self.tree.item(row, tags=("running_total",))
                else:
                    # Reset the row's color based on its index
                    row_index = self.tree.index(row)
                    row_tag = "even" if row_index % 2 == 0 else "odd"  # Alternate colors
                    self.tree.item(row, tags=(row_tag,))

    def on_row_leave(self, event):
        """Handle row leave event."""
        for row_id in self.tree.get_children():
            # Check if the row is the running total row
            if "Running Total" in self.tree.item(row_id, "values"):
                # Reapply the running_total tag to preserve its font size
                self.tree.item(row_id, tags=("running_total",))
            else:
                # Reset the row's color based on its index
                row_index = self.tree.index(row_id)
                row_tag = "even" if row_index % 2 == 0 else "odd"  # Alternate colors
                self.tree.item(row_id, tags=(row_tag,))

    def on_row_click(self, event):
        """Handle row click event to toggle selection with a single click."""
        row_id = self.tree.identify_row(event.y)  # Identify the row under the mouse pointer

        if row_id:
            # Check if the row is already selected
            if row_id in self.tree.selection():
                # Unselect the row and restore its original color
                self.tree.selection_remove(row_id)
                row_index = self.tree.index(row_id)
                row_tag = "odd" if (row_index + 1) % 2 != 0 else "even"  # Adjust for header row
                self.tree.item(row_id, tags=(row_tag,))
            else:
                # Select the row
                self.tree.selection_set(row_id)

        # Prevent the default Treeview behavior
        return "break"

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
        StudentManager(self, self.data, self.class_id, self.refresh).mainloop()

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
        Launcher(self.master, self.theme).mainloop()

    def open_add_edit_student_form(self, student_data=None):
        """Open a form to add or edit a student."""
        form = tk.Toplevel(self)
        form.title("Add/Edit Student")
        form.geometry("400x300")
        form.configure(bg=self["bg"])

        # Name Field
        tk.Label(form, text="Name:", font=("Arial", 12, "bold"), bg=self["bg"]).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        name_var = tk.StringVar(value=student_data.get("Name", "") if student_data else "")
        name_entry = tk.Entry(form, textvariable=name_var, font=("Arial", 12), width=15)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        # Other Fields (Example: Nickname)
        tk.Label(form, text="Nickname:", font=("Arial", 12, "bold"), bg=self["bg"]).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        nickname_var = tk.StringVar(value=student_data.get("Nickname", "") if student_data else "")
        nickname_entry = tk.Entry(form, textvariable=nickname_var, font=("Arial", 12), width=15)
        nickname_entry.grid(row=1, column=1, padx=10, pady=10)

        # Save Button
        save_button = tk.Button(
            form,
            text="Save",
            command=lambda: self.save_student(form, name_var, nickname_var),
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            width=10
        )
        save_button.grid(row=2, column=0, padx=10, pady=20)

        # Cancel Button
        cancel_button = tk.Button(
            form,
            text="Cancel",
            command=form.destroy,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
            width=10
        )
        cancel_button.grid(row=2, column=1, padx=10, pady=20)

    def save_student(self, form, name_var, nickname_var):
        """Save the student data."""
        name = name_var.get().title()  # Capitalize each word in the name
        nickname = nickname_var.get()

        # Save the data (example logic)
        new_student = {
            "Name": name,
            "Nickname": nickname,
        }
        # Add logic to save `new_student` to the data source
        print(f"Saved student: {new_student}")

        form.destroy()  # Close the form

    def update_max_classes(self, *args):
        """Recalculate MaxClasses based on CourseHours and ClassTime."""
        try:
            course_hours = float(self.entries["CourseHours"]["var"].get() or 0)
            class_time = float(self.entries["ClassTime"]["var"].get() or 0)

            if course_hours > 0 and class_time > 0:
                full_classes = int(course_hours // class_time)  # Full classes
                remaining_hours = course_hours % class_time  # Remaining hours

                if remaining_hours > 0:
                    max_classes_display = f"{full_classes} ({remaining_hours} hour remains)"
                else:
                    max_classes_display = str(full_classes)

                self.entries["MaxClasses"]["var"].set(max_classes_display)
            else:
                self.entries["MaxClasses"]["var"].set("20")  # Default value
        except ValueError:
            self.entries["MaxClasses"]["var"].set("20")  # Default value if input is invalid

if __name__ == "__main__":
    # Example usage
    data = load_data()
    app = Mainform("OLO123", data, "default")
    app.mainloop()