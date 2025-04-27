import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, data, theme, on_metadata_save):
        super().__init__(parent)
        self.theme = theme
        self.class_id = class_id  # Class ID (e.g., OLO124)
        self.data = data
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher
        self.title("Add / Edit Class Information")
        self.geometry("1000x500")  # width x height
        self.center_window(1000, 500)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make MetadataForm always on top

        # Determine if this is an edit or add operation
        self.is_edit = class_id is not None

        # Create widgets
        self.create_widgets()

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create the layout and fields for editing metadata."""
        fields = [
            ("Class No*:", "class_no", "def_class_no"),
            ("Company*:", "Company", "def_company"),
            ("Consultant:", "Consultant"),
            ("Teacher:", "Teacher", "def_teacher"),
            ("Teacher No:", "TeacherNo", "def_teacher_no"),
            ("Room:", "Room"),
            ("CourseBook:", "CourseBook"),
            ("Course Hours:", "CourseHours", "def_course_hours"),
            ("Class Time:", "ClassTime", "def_class_time"),
            ("Max Classes:", "MaxClasses"),
            ("Start Date:", "StartDate"),
            ("Finish Date:", "FinishDate"),
            ("Days:", "Days"),
            ("Time:", "Time"),
            ("Notes:", "Notes"),
            ("Rate:", "rate", "def_rate"),
            ("CCP:", "ccp", "def_ccp"),
            ("Travel:", "travel", "def_travel"),
            ("Bonus:", "bonus", "def_bonus"),
        ]

        self.entries = {}

        # Create fields in 4-column layout
        for i, field in enumerate(fields):
            label_text = field[0]
            key = field[1]
            default_key = field[2] if len(field) > 2 else None

            # Determine row and column positions
            row = i // 2  # Two fields per row
            col = (i % 2) * 2  # Column 0 or 2 for labels, 1 or 3 for metadata

            # Add label
            tk.Label(self, text=label_text, font=("Arial", 12, "bold"), bg="white").grid(row=row, column=col, sticky="e", padx=10, pady=5)

            # Add entry field
            entry_bg = "yellow" if key in ["class_no", "Company"] else "white"  # Yellow for mandatory fields
            entry = tk.Entry(self, width=30, bg=entry_bg, font=("Arial", 12))
            entry.grid(row=row, column=col + 1, padx=10, pady=5)

            # Pre-fill with default value if in Add Class mode and default_key is provided
            if not self.is_edit and default_key:
                default_value = self.data.get(default_key, "")
                entry.insert(0, default_value)
            else:
                # Pre-fill with existing metadata if in Edit Class mode
                entry.insert(0, self.data.get("classes", {}).get(self.class_id, {}).get("metadata", {}).get(key, ""))

            self.entries[key] = entry

        # Add mandatory message at the bottom
        tk.Label(self, text="      * = Mandatory (OLOxxx and Company)", font=("Arial", 10), fg="black", anchor="w").grid(
            row=(len(fields) + 1) // 2, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 5)
        )

        # Buttons
        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=(len(fields) + 2) // 2, column=0, columnspan=4, pady=20)

        tk.Button(button_frame, text="Save", command=self.save_metadata, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.close_form, width=10).pack(side=tk.LEFT, padx=10)

    def save_metadata(self):
        """Save metadata for the class."""
        # Validate mandatory fields
        class_no = self.entries["class_no"].get().strip()
        company = self.entries["Company"].get().strip()

        if not class_no or not company:
            # Highlight mandatory fields in yellow if empty
            if not class_no:
                self.entries["class_no"].config(bg="yellow")
            if not company:
                self.entries["Company"].config(bg="yellow")

            # Show error message
            messagebox.showerror("Validation Error", "Class No and Company are mandatory fields.", parent=self)
            return

        # Reset background color for mandatory fields
        self.entries["class_no"].config(bg="white")
        self.entries["Company"].config(bg="white")

        # Collect metadata
        metadata = {key: entry.get().strip() for key, entry in self.entries.items()}

        # Save metadata
        if self.class_id is None:
            # Generate a new class ID if adding a new class
            self.class_id = f"OLO{len(self.data.get('classes', {})) + 1:03}"
            self.data["classes"][self.class_id] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            # Update existing class metadata
            self.data["classes"][self.class_id]["metadata"] = metadata

        save_data(self.data)  # Save to file
        self.on_metadata_save()  # Refresh Launcher
        self.destroy()  # Close the form

    def close_form(self):
        """Close the form."""
        self.destroy()