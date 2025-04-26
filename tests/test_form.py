import tkinter as tk
from tkinter import ttk

class TestForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Test Class No Field")
        self.geometry("300x200")
        self.configure(bg="white")

        # Apply a specific theme
        style = ttk.Style(self)
        style.theme_use("clam")  # Try "clam", "alt", or other themes

        # Create Class No field
        self.is_edit = False  # Change to True to simulate Edit Mode
        self.class_id = "OLO124" if self.is_edit else None

        tk.Label(self, text="Class No:", font=("Arial", 12, "bold"), bg="white").grid(row=0, column=0, sticky="e", padx=10, pady=5)

        if self.is_edit:
            self.class_no_entry = tk.Entry(self, width=40, state="readonly", fg="black", font=("Arial", 14))
            self.class_no_entry.configure(readonlybackground="yellow")  # Force background color for readonly state
            self.class_no_entry.insert(0, self.class_id)
        else:
            self.class_no_entry = tk.Entry(self, width=40, fg="black", bg="white", font=("Arial", 14))
            self.class_no_entry.insert(0, "")

        self.class_no_entry.grid(row=0, column=1, padx=10, pady=5)

        # Save button to simulate saving the form
        save_button = tk.Button(self, text="Save", command=self.save_class_no)
        save_button.grid(row=1, column=1, pady=10, sticky="e")

    def save_class_no(self):
        """Simulate saving the Class No and make the field read-only."""
        class_no = self.class_no_entry.get()
        if not class_no:
            tk.messagebox.showerror("Error", "Class No cannot be empty!")
            return

        # Simulate saving the class_no
        print(f"Class No saved: {class_no}")

        # Make the field read-only
        self.class_no_entry.configure(state="readonly", readonlybackground="yellow")
        tk.messagebox.showinfo("Success", "Class No is now locked!")

# Run the test form
if __name__ == "__main__":
    app = TestForm()
    app.mainloop()