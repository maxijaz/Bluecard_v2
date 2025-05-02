import tkinter as tk
from tkinter import ttk, messagebox
from src.logic.parser import save_data
import logging
import json
from tkcalendar import Calendar

class MetadataForm(tk.Toplevel):
    def __init__(self, parent, class_id, default_values, theme, on_metadata_save, context="launcher"):
        super().__init__(parent)
        self.class_id = class_id  # Class ID (e.g., OLO123)
        self.default_values = self.load_default_values() if not default_values else default_values  # Default values from default.json
        self.theme = theme  # UI theme
        self.on_metadata_save = on_metadata_save  # Callback to refresh Launcher or Mainform
        self.data = parent.data  # Reference to the main data dictionary
        self.is_edit = class_id is not None  # Determine if this is an edit or add operation
        self.context = context  # Context: "launcher" or "mainform"

        self.title("Add / Edit Class")
        self.geometry("900x500")  # Manually resized dimensions
        self.resizable(True, True)

        # Make the window topmost
        self.attributes("-topmost", True)

        # Create a scrollable canvas
        self.create_scrollable_canvas()

        # Create widgets inside the scrollable frame
        self.create_widgets()

        # Focus cursor on the first field (Class ID)
        self.entries["class_no"]["widget"].focus_set()

    def load_default_values(self):
        """Load default values from default.json."""
        try:
            with open("data/default.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Error", "Default values file (default.json) not found.", parent=self)
            return {}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error decoding default.json.", parent=self)
            return {}

    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def create_scrollable_canvas(self):
        """Create a scrollable canvas for the form."""
        self.canvas = tk.Canvas(self, bg="white")
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        # Add vertical scrollbar
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        # Add horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=h_scrollbar.set)

        # Pack the canvas
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create a window inside the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure scrolling
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def on_frame_configure(self, event):
        """Adjust the scroll region to match the size of the scrollable frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Resize the canvas frame to match the width of the canvas."""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def create_widgets(self):
        """Create the layout and fields for editing metadata."""
        fields = [
            ("Class No*:", "class_no"),
            ("Company*:", "Company"),
            ("Room:", "Room"),
            ("Consultant:", "Consultant"),
            ("Teacher:", "Teacher"),
            ("CourseBook:", "CourseBook"),
            ("Notes:", "Notes"),
            ("Course Hours:", "CourseHours"),
            ("Class Time:", "ClassTime"),
            ("Start Date:", "StartDate"),
            ("Finish Date:", "FinishDate"),  # Add FinishDate field
            ("Days:", "Days"),
            ("Time:", "Time"),
            ("Max Classes:", "MaxClasses"),
            ("Teacher No:", "TeacherNo"),
            ("Rate:", "rate"),
            ("CCP:", "ccp"),
            ("Travel:", "travel"),
            ("Bonus:", "bonus"),
        ]

        self.entries = {}

        # Add fields for Columns 1 & 2
        for i, field in enumerate(fields[:7]):  # First 7 fields go to Columns 1 & 2
            label_text = field[0]
            key = field[1]

            # Determine row and column positions
            row = i
            col = 0  # Column 0 for labels, Column 1 for entry fields

            # Add label
            tk.Label(self.scrollable_frame, text=label_text, font=("Arial", 12, "bold"), bg="white").grid(row=row, column=col, sticky="e", padx=10, pady=5)

            # Add entry field
            entry_bg = "yellow" if key in ["class_no", "Company"] else "white"  # Yellow for mandatory fields
            entry_var = tk.StringVar()
            entry = tk.Entry(self.scrollable_frame, textvariable=entry_var, width=30, bg=entry_bg, font=("Arial", 12))
            entry.grid(row=row, column=col + 1, padx=5, pady=5)

            # Add logic for [class_no] and [Company]
            if key == "class_no":
                def validate_class_no(*args):
                    value = entry_var.get().upper()  # Convert to uppercase
                    entry_var.set(value)
                entry_var.trace_add("write", validate_class_no)  # Trigger on value change

            if key == "Company":
                def validate_company(*args):
                    value = entry_var.get()
                    if value and not value[0].isupper():  # Ensure the first letter is uppercase
                        entry_var.set(value.capitalize())
                entry_var.trace_add("write", validate_company)  # Trigger on value change

            # Pre-fill with default or existing values
            if not self.is_edit:
                default_key = f"def_{key.lower()}"
                default_value = self.default_values.get(default_key, "")
                entry_var.set(default_value)
            else:
                existing_value = self.data.get("classes", {}).get(self.class_id, {}).get("metadata", {}).get(key, "")
                entry_var.set(existing_value)

            # Store the entry
            self.entries[key] = {"var": entry_var, "widget": entry}

        # Add fields for Columns 4 & 5
        for i, field in enumerate(fields[7:]):  # Remaining fields go to Columns 4 & 5
            label_text = field[0]
            key = field[1]

            # Determine row and column positions
            row = i
            col = 2  # Column 2 for labels, Column 3 for entry fields

            # Add label
            tk.Label(self.scrollable_frame, text=label_text, font=("Arial", 12, "bold"), bg="white").grid(row=row, column=col, sticky="e", padx=10, pady=5)

            # Add entry field
            entry_var = tk.StringVar()
            entry = tk.Entry(self.scrollable_frame, textvariable=entry_var, width=30, font=("Arial", 12))
            entry.grid(row=row, column=col + 1, padx=5, pady=5)

            # Pre-fill with default or existing values
            if not self.is_edit:
                default_key = f"def_{key.lower()}"
                default_value = self.default_values.get(default_key, "")
                entry_var.set(default_value)
            else:
                existing_value = self.data.get("classes", {}).get(self.class_id, {}).get("metadata", {}).get(key, "")
                entry_var.set(existing_value)

            # Store the entry
            self.entries[key] = {"var": entry_var, "widget": entry}

            # Add [Pick] button for StartDate and FinishDate
            if key in ["StartDate", "FinishDate"]:
                tk.Button(
                    self.scrollable_frame,
                    text="Pick",
                    font=("Arial", 10, "bold"),
                    bg="blue",
                    fg="white",
                    command=lambda k=key: self.open_date_picker(k),  # Pass the key to the date picker
                ).grid(row=row, column=col + 2, padx=5, pady=5)

        # Add Save and Cancel buttons
        button_frame = tk.Frame(self.scrollable_frame, bg="white")
        button_frame.grid(row=max(len(fields[:7]), len(fields[7:])) + 1, column=0, columnspan=5, pady=10)

        save_button = tk.Button(button_frame, text="Save", font=("Arial", 12, "bold"), bg="green", fg="white", command=self.save_metadata)
        save_button.pack(side="left", padx=10)

        cancel_button = tk.Button(button_frame, text="Cancel", font=("Arial", 12, "bold"), bg="red", fg="white", command=self.close_form)
        cancel_button.pack(side="left", padx=10)

        # Add a frame for the table and scrollbars
        table_frame = tk.Frame(self.scrollable_frame, bg="white")
        table_frame.grid(row=20, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        # Create a Treeview for the table
        self.table = ttk.Treeview(table_frame, columns=("Column1", "Column2", "Column3"), show="headings")
        self.table.heading("Column1", text="Column 1")
        self.table.heading("Column2", text="Column 2")
        self.table.heading("Column3", text="Column 3")

        # Add vertical scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        v_scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=v_scrollbar.set)

        # Add horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        self.table.configure(xscrollcommand=h_scrollbar.set)

        # Pack the table
        self.table.pack(fill="both", expand=True)

        # Populate the table with sample data
        for i in range(50):  # Example data
            self.table.insert("", "end", values=(f"Row {i+1} Col 1", f"Row {i+1} Col 2", f"Row {i+1} Col 3"))

        # Bind zoom functionality
        self.table_font_size = 10  # Default font size
        self.table.bind("<Control-MouseWheel>", self.zoom_table)

        # Add example label
        tk.Label(self.scrollable_frame, text="Example Label").grid(row=0, column=0)

        for i in range(50):  # Add 50 labels to test scrolling
            tk.Label(self.scrollable_frame, text=f"Label {i+1}").grid(row=i, column=0, padx=10, pady=5)

        print(self.scrollable_frame.winfo_width(), self.scrollable_frame.winfo_height())
        print(self.canvas.winfo_width(), self.canvas.winfo_height())
        print(self.canvas.bbox("all"))

    def zoom_table(self, event):
        """Zoom in or out on the table using Ctrl+MouseWheel."""
        if event.delta > 0:  # Zoom in
            self.table_font_size += 1
        elif event.delta < 0 and self.table_font_size > 1:  # Zoom out
            self.table_font_size -= 1

        # Update the font size of the table
        new_font = ("Arial", self.table_font_size)
        self.table.tag_configure("font", font=new_font)

        # Apply the new font to all rows
        for row in self.table.get_children():
            self.table.item(row, tags=("font",))

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

    def save_metadata(self):
        """Save metadata for the class."""
        logging.debug("Saving metadata...")
        class_no = self.entries["class_no"]["var"].get().strip().upper()  # Ensure class_no is uppercase

        # Validate that the class_no is unique
        if class_no in self.data.get("classes", {}) and not self.is_edit:
            messagebox.showerror(
                "Duplicate Class ID",
                f"Class ID '{class_no}' already exists. Please use a unique Class ID.",
                parent=self
            )
            logging.warning(f"Attempted to save duplicate Class ID: {class_no}")
            return

        # Collect metadata from the form
        metadata = {}
        for key, entry in self.entries.items():
            value = entry["var"].get().strip()

            # Apply formatting for specific fields
            if key == "class_no":
                value = value.upper()  # Ensure class_no is uppercase
            elif key == "Company":
                # Capitalize the first letter of each word while preserving existing uppercase letters
                value = " ".join(word if word.isupper() else word.capitalize() for word in value.split())

            metadata[key] = value

        # Save the metadata
        if not self.is_edit:
            # Add a new class
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}
            logging.debug(f"New class added: {class_no}")
        else:
            # Update an existing class
            self.data["classes"][self.class_id]["metadata"] = metadata
            logging.debug(f"Class {self.class_id} updated.")

        # Save the updated data to the file
        save_data(self.data)
        logging.debug("Data saved successfully.")

        # Handle context-specific behavior
        logging.debug(f"Context: {self.context}")
        if self.context == "launcher":
            logging.debug("Closing Launcher and opening Mainform...")
            try:
                # Open Mainform without relying on the destroyed Launcher
                from src.ui.mainform import Mainform  # Import Mainform
                self.master.destroy()  # Close the Launcher
                Mainform(None, class_no, self.data, self.theme).mainloop()  # Pass None as the parent
                logging.debug("Mainform opened successfully.")
            except Exception as e:
                logging.error(f"Failed to open Mainform: {e}")
        elif self.context == "mainform":
            logging.debug("Refreshing Mainform...")
            self.master.refresh()

        # Close the MetadataForm
        logging.debug("Closing MetadataForm...")
        self.destroy()

    def close_form(self):
        """Close the form and save defaults if adding a new class."""
        if self.class_id is None:
            # Ensure 'classes' key exists in self.data
            if "classes" not in self.data:
                self.data["classes"] = {}

            # Collect metadata with default values
            metadata = {key: entry["var"].get().strip() for key, entry in self.entries.items()}

            # Add the new class to the data
            class_no = metadata.get("class_no", f"OLO{len(self.data['classes']) + 1:03}")
            self.data["classes"][class_no] = {"metadata": metadata, "students": {}, "archive": "No"}

            save_data(self.data)  # Save to file
            self.on_metadata_save()  # Refresh Launcher

        self.destroy()  # Close the form

    def open_date_picker(self, key):
        """Open a calendar popup to select a date."""
        def set_date():
            """Set the selected date and close the popup."""
            selected_date = cal.get_date()  # Get the selected date
            self.entries[key]["var"].set(selected_date)  # Save the selected date
            popup.destroy()

        def cancel_date():
            """Close the popup without making changes."""
            popup.destroy()

        # Create a popup window
        popup = tk.Toplevel(self)
        popup.title("Select Date")
        popup.geometry("300x300")
        popup.configure(bg="white")
        popup.attributes("-topmost", True)  # Make the popup topmost

        # Center the popup on the screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 300) // 2  # Center horizontally (300 is the popup width)
        y = (screen_height - 300) // 2  # Center vertically (300 is the popup height)
        popup.geometry(f"300x300+{x}+{y}")

        # Add a calendar widget
        cal = Calendar(popup, selectmode="day", date_pattern="dd/mm/yyyy")  # Use dd/mm/yyyy for tkcalendar
        cal.pack(pady=20)

        # Add a frame for buttons
        button_frame = tk.Frame(popup, bg="white")
        button_frame.pack(pady=10)

        # Add OK and Cancel buttons
        tk.Button(button_frame, text="OK", command=set_date, bg="green", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel_date, bg="red", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

    def edit_metadata(self):
        """Open the Edit Metadata form."""
        MetadataForm(
            parent=self,
            class_id=self.class_id,
            default_values={},
            theme=self.theme,
            on_metadata_save=self.refresh,
            context="mainform"
        ).mainloop()

    def add_new_class(self):
        """Open the MetadataForm to add a new class."""
        logging.debug("Opening MetadataForm to add a new class...")
        MetadataForm(
            parent=self,
            class_id=None,
            default_values={},
            theme=self.theme,
            on_metadata_save=self.refresh,
            context="launcher"  # Pass context as "launcher"
        ).mainloop()
        logging.debug("MetadataForm closed.")