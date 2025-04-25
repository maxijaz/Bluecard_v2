import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, data, theme, on_metadata_save):
        super().__init__(parent)
        self.theme = theme
        self.class_id = class_id
        self.data = data
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher
        self.title("Add / Edit Class Information")
        self.geometry("650x650")
        self.center_window(650, 650)
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Make MetadataForm always on top

        # Apply theme
        self.configure_theme()

        # Load metadata for the selected class
        self.metadata = self.data["classes"].get(self.class_id, {}).get("metadata", {})

        # Create UI components
        self.create_widgets()

        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.close_form)

    def configure_theme(self):
        """Apply the selected theme to the Metadata Form."""
        if self.theme == "dark":
            self.configure(bg="black")
        elif self.theme == "clam":
            self.configure(bg="lightblue")
        else:  # Default theme
            self.configure(bg="white")

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
            tk.Label(self, text=label_text, font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="e", padx=10, pady=5)

            if key == "class_no":
                # Class No field is read-only
                entry = tk.Entry(self, width=40, state="readonly")
                entry.grid(row=i, column=1, padx=10, pady=5)
                entry.insert(0, self.class_id)  # Pre-fill with class ID
            else:
                entry = tk.Entry(self, width=40)
                entry.grid(row=i, column=1, padx=10, pady=5)
                entry.insert(0, self.metadata.get(key, ""))  # Pre-fill with existing data

            self.entries[key] = entry

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save", command=self.save_metadata, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=self.close_form, width=10).pack(side=tk.LEFT, padx=10)

    def save_metadata(self):
        """Save metadata for the class."""
        for key, entry in self.entries.items():
            if key != "class_no":  # Skip saving the read-only Class No field
                self.metadata[key] = entry.get()

        # Save changes to the data using parser.py
        try:
            self.data["classes"][self.class_id]["metadata"] = self.metadata
            save_data(self.data)  # Use parser.py to save data
            messagebox.showinfo("Success", "Metadata saved successfully!", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save metadata: {e}", parent=self)

        # Notify the parent to refresh
        self.on_metadata_save()

        # Close the form
        self.destroy()

    def close_form(self):
        """Close the Metadata Form."""
        self.destroy()