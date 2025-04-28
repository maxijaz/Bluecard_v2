import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, default_values, theme, on_metadata_save):
        super().__init__(parent)
        self.class_id = class_id  # Class ID (e.g., OLO123)
        self.default_values = default_values  # Default values from default.json
        self.theme = theme  # UI theme
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher
        self.data = parent.data  # Reference to the main data dictionary
        self.is_edit = class_id is not None  # Determine if this is an edit or add operation

        self.title("Add / Edit Class")
        self.geometry("900x450")  # Manually resized dimensions
        self.resizable(False, False)

        # Make the window topmost
        self.attributes("-topmost", True)

        # Center the window
        self.center_window()

        # Create widgets
        self.create_widgets()

        # Focus cursor on the first field (Class ID)
        self.entries["class_no"].focus_set()

    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create the layout and fields for editing metadata."""
        fields = [
            ("Class No*:", "class_no"),
            ("Company*:", "Company"),
            ("Consultant:", "Consultant"),
            ("Teacher:", "Teacher"),
            ("Teacher No:", "TeacherNo"),
            ("Room:", "Room"),
            ("CourseBook:", "CourseBook"),
            ("Course Hours:", "CourseHours"),
            ("Class Time:", "ClassTime"),
            ("Max Classes:", "MaxClasses"),
            ("Start Date:", "StartDate"),
            ("Finish Date:", "FinishDate"),
            ("Days:", "Days"),
            ("Time:", "Time"),
            ("Notes:", "Notes"),
            ("Rate:", "rate"),
            ("CCP:", "ccp"),
            ("Travel:", "travel"),
            ("Bonus:", "bonus"),
        ]

        self.entries = {}

        # Create fields in 4-column layout
        for i, field in enumerate(fields):
            label_text = field[0]
            key = field[1]

            # Determine row and column positions
            row = i // 2  # Two fields per row
            col = (i % 2) * 2  # Column 0 or 2 for labels, 1 or 3 for metadata

            # Add label
            tk.Label(self, text=label_text, font=("Arial", 12, "bold"), bg="white").grid(row=row, column=col, sticky="e", padx=10, pady=5)

            # Add entry field
            entry_bg = "yellow" if key in ["class_no", "Company"] else "white"  # Yellow for mandatory fields
            entry = tk.Entry(self, width=30, bg=entry_bg, font=("Arial", 12))
            entry.grid(row=row, column=col + 1, padx=10, pady=5)

            # Pre-fill with default value if in Add Class mode
            if not self.is_edit:
                entry.insert(0, self.default_values.get(f"def_{key}", ""))
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

        # Ensure 'classes' key exists in self.data
        if "classes" not in self.data:
            self.data["classes"] = {}

        # Save metadata
        if self.class_id is None:
            # Add a new class with the collected metadata
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            # Update existing class metadata
            self.data["classes"][self.class_id]["metadata"] = metadata

        save_data(self.data)  # Save to file
        self.on_metadata_save()  # Refresh Launcher
        self.destroy()  # Close the form

    def close_form(self):
        """Close the form and save defaults if adding a new class."""
        if self.class_id is None:
            # Ensure 'classes' key exists in self.data
            if "classes" not in self.data:
                self.data["classes"] = {}

            # Collect metadata with default values
            metadata = {key: entry.get().strip() for key, entry in self.entries.items()}

            # Add the new class to the data
            class_no = metadata.get("class_no", f"OLO{len(self.data['classes']) + 1:03}")
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}

            save_data(self.data)  # Save to file
            self.on_metadata_save()  # Refresh Launcher

        self.destroy()  # Close the form