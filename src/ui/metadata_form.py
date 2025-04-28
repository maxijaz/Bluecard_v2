import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data
import logging

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
                # Normalize key to lowercase to match default.json keys
                default_key = f"def_{key.lower()}"
                default_value = self.default_values.get(default_key, f"[Missing default for {key}]")
                if default_key not in self.default_values:
                    logging.warning(f"Default value for {key} is missing in default.json")
                logging.debug(f"Default value for {key}: {default_value}")
                entry.insert(0, default_value)
            else:
                existing_value = self.data.get("classes", {}).get(self.class_id, {}).get("metadata", {}).get(key, "")
                entry.insert(0, existing_value)

            self.entries[key] = entry

        # Add Save and Cancel buttons
        button_frame = tk.Frame(self, bg="white")
        button_frame.grid(row=len(fields) // 2 + 1, column=0, columnspan=4, pady=10)

        save_button = tk.Button(button_frame, text="Save", font=("Arial", 12, "bold"), bg="green", fg="white", command=self.save_metadata)
        save_button.pack(side="left", padx=10)

        cancel_button = tk.Button(button_frame, text="Cancel", font=("Arial", 12, "bold"), bg="red", fg="white", command=self.close_form)
        cancel_button.pack(side="left", padx=10)

    def save_metadata(self):
        """Save metadata for the class."""
        logging.debug("Saving metadata...")
        class_no = self.entries["class_no"].get().strip()

        # Disable the Save button to prevent multiple clicks
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "Save":
                widget.config(state="disabled")

        # Check if ClassID already exists
        if class_no in self.data.get("classes", {}) and not self.is_edit:
            # Show error message as topmost and centered
            error_window = tk.Toplevel(self)
            error_window.title("Error")
            error_window.geometry("300x100")
            error_window.attributes("-topmost", True)

            # Center the error window
            error_window.update_idletasks()
            screen_width = error_window.winfo_screenwidth()
            screen_height = error_window.winfo_screenheight()
            x = (screen_width - error_window.winfo_width()) // 2
            y = (screen_height - error_window.winfo_height()) // 2
            error_window.geometry(f"300x100+{x}+{y}")

            tk.Label(error_window, text=f"ClassID '{class_no}' already exists.\nPlease use a unique ClassID.", font=("Arial", 10), fg="red").pack(pady=10)
            tk.Button(error_window, text="OK", command=error_window.destroy, font=("Arial", 10, "bold")).pack(pady=5)
            logging.warning(f"Attempted to save duplicate ClassID: {class_no}")
            return

        metadata = {}
        for key, entry in self.entries.items():
            metadata[key] = entry.get().strip()

        # Save the metadata
        if not self.is_edit:
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
        else:
            self.data["classes"][self.class_id]["metadata"] = metadata

        logging.debug(f"New class added: {class_no}")
        self.on_metadata_save()
        self.destroy()

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