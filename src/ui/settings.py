import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from ui.launcher import Launcher

SETTINGS_PATH = "data/settings.json"
THEMES_PATH = "data/themes.json"

class SettingsForm(tk.Toplevel):
    def __init__(self, current_theme):
        super().__init__()
        self.title("Settings")
        self.geometry("300x150")
        self.center_window(300, 150)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.current_theme = current_theme
        self.themes = self.load_themes()

        # Create UI components
        self.create_widgets()

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def load_themes(self):
        """Load themes from themes.json."""
        if not os.path.exists(THEMES_PATH):
            messagebox.showerror("Error", "Themes file not found!")
            self.destroy()
            return []
        try:
            with open(THEMES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [theme["name"] for theme in data["themes"]]
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid themes.json format!")
            self.destroy()
            return []

    def create_widgets(self):
        # Dropdown for theme selection
        tk.Label(self, text="Select Theme:", font=("Arial", 12)).pack(pady=10)
        self.theme_var = tk.StringVar(value=self.current_theme)
        self.theme_dropdown = ttk.Combobox(self, textvariable=self.theme_var, values=self.themes, state="readonly")
        self.theme_dropdown.pack(pady=5)

        # Save button
        tk.Button(self, text="Save", command=self.save_theme).pack(pady=10)

    def save_theme(self):
        """Save the selected theme to settings.json and reopen the Launcher."""
        selected_theme = self.theme_var.get()
        if not selected_theme:
            messagebox.showwarning("Warning", "Please select a theme!")
            return
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"theme": selected_theme}, f, indent=4)
            messagebox.showinfo("Success", "Theme saved successfully!")
            self.destroy()
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            Launcher(root, selected_theme).mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save theme: {e}")