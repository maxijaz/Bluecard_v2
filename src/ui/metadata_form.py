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
        self.geometry("450x550")
        self.center_window(450, 550)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make MetadataForm always on top

        # Determine if this is an edit or add operation
        self.is_edit = class_id is not None

        # Debugging: Print the data being passed
        print(f"Initializing MetadataForm: is_edit={self.is_edit}, class_id={self.class_id}")
        print(f"Data: {self.data}")

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
        # Add a heading to display the Class ID
        heading = tk.Label(
            self,
            text=f"Class ID = {self.class_id}" if self.class_id else "New Class",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="blue"
        )
        heading.grid(row=0, column=0, columnspan=2, pady=10)

        # Fields for metadata
        fields = [
            ("Class No:", "class_no"),
            ("Company:", "Company"),
            ("Consultant:", "Consultant"),
            ("Teacher:", "Teacher"),
            ("Room:", "Room"),
            ("CourseBook:", "CourseBook"),
            ("CourseHours:", "CourseHours"),
            ("ClassTime:", "ClassTime"),
            ("MaxClasses:", "MaxClasses"),
            ("StartDate:", "StartDate"),
            ("FinishDate:", "FinishDate"),
            ("Days:", "Days"),
            ("Time:", "Time"),
            ("Notes:", "Notes"),
        ]

        self.entries = {}

        for i, (label_text, key) in enumerate(fields):
            tk.Label(self, text=label_text, font=("Arial", 12, "bold"), bg="white").grid(row=i + 1, column=0, sticky="e", padx=10, pady=5)

            if key == "class_no":
                if self.is_edit:
                    self.class_no_entry = tk.Entry(self, width=30, state="readonly", fg="black", font=("Arial", 12))
                    self.class_no_entry.configure(readonlybackground="yellow")
                    self.class_no_entry.insert(0, self.class_id)
                else:
                    self.class_no_entry = tk.Entry(self, width=30, fg="black", bg="white", font=("Arial", 12))
                    self.class_no_entry.insert(0, "")

                self.class_no_entry.grid(row=i + 1, column=1, padx=10, pady=5)
                self.entries[key] = self.class_no_entry
            else:
                entry = tk.Entry(self, width=30, bg="white", font=("Arial", 12))
                entry.grid(row=i + 1, column=1, padx=10, pady=5)
                entry.insert(0, self.data.get("classes", {}).get(self.class_id, {}).get("metadata", {}).get(key, ""))
                self.entries[key] = entry

        # Buttons
        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save", command=self.save_metadata, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.close_form, width=10).pack(side=tk.LEFT, padx=10)

    def save_metadata(self):
        """Save metadata for the class."""
        class_no = self.class_no_entry.get()

        if not class_no:
            messagebox.showerror("Error", "Class No cannot be empty!", parent=self)
            return

        # Save metadata
        metadata = {key: entry.get() for key, entry in self.entries.items() if key != "class_no"}

        if self.is_edit:
            self.data["classes"][self.class_id]["metadata"] = metadata
        else:
            if class_no in self.data["classes"]:
                messagebox.showerror("Error", f"Class No '{class_no}' already exists!", parent=self)
                return
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
            self.class_id = class_no
            self.is_edit = True
            self.class_no_entry.configure(state="readonly", readonlybackground="yellow")

        # Save changes to the data
        save_data(self.data)
        messagebox.showinfo("Success", "Metadata saved successfully!", parent=self)

        # Notify the parent to refresh
        self.on_metadata_save()

        # Close the form
        self.destroy()

    def close_form(self):
        """Close the form."""
        self.destroy()