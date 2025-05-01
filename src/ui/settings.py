import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

SETTINGS_PATH = "data/settings.json"
DEFAULT_PATH = "data/default.json"
THEMES_PATH = "data/themes.json"

class SettingsForm(tk.Toplevel):
    def __init__(self, parent, current_theme, on_theme_change):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("350x400")  # Adjusted size for specified fields
        self.center_window(350, 400)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.current_theme = current_theme
        self.on_theme_change = on_theme_change  # Callback to refresh Launcher
        self.themes = self.load_themes()
        self.default_settings = self.load_default_settings()

        # Create UI components
        self.create_widgets()

        # Handle close button (X)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
            return []
        try:
            with open(THEMES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [theme["name"] for theme in data["themes"]]
        except json.JSONDecodeError:
            return []

    def load_default_settings(self):
        """Load default settings from default.json."""
        if not os.path.exists(DEFAULT_PATH):
            return {}
        try:
            with open(DEFAULT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def create_widgets(self):
        """Create UI components for settings."""
        # Theme selection
        theme_frame = tk.Frame(self)
        theme_frame.pack(fill=tk.X, pady=5)
        tk.Label(
            theme_frame,
            text="Select Theme:",
            font=("Arial", 12, "bold"),
            anchor="e",
            width=12
        ).pack(side=tk.LEFT, padx=(5, 10))
        self.theme_var = tk.StringVar(value=self.current_theme)
        self.theme_dropdown = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=self.themes,
            state="readonly",
            font=("Arial", 12),
            width=13
        )
        self.theme_dropdown.pack(side=tk.LEFT, padx=(0, 5))

        # Default settings fields
        self.entries = {}
        fields_to_include = [
            "def_teacher",
            "def_teacherno",
            "def_coursehours",
            "def_classtime",
            "def_rate",
            "def_ccp",
            "def_travel",
            "def_bonus"
        ]
        for key in fields_to_include:
            value = self.default_settings.get(key, "")
            frame = tk.Frame(self)
            frame.pack(fill=tk.X, pady=5)
            tk.Label(
                frame,
                text=key.replace("def_", "").capitalize() + ":",
                font=("Arial", 12, "bold"),
                anchor="e",
                width=12
            ).pack(side=tk.LEFT, padx=(5, 10))
            entry = tk.Entry(frame, font=("Arial", 12), width=15)
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            self.entries[key] = entry

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save_settings,
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            width=10
        )
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_close,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
            width=10
        )
        cancel_button.pack(side=tk.RIGHT, padx=10)

    def save_settings(self):
        """Save the selected theme and default settings."""
        # Save theme to settings.json
        selected_theme = self.theme_var.get()
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump({"theme": selected_theme}, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save theme: {e}", parent=self)

        # Save default settings to default.json
        updated_settings = {key: entry.get() for key, entry in self.entries.items()}
        try:
            with open(DEFAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(updated_settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save default settings: {e}", parent=self)

        # Refresh Launcher with the new theme
        self.on_theme_change(selected_theme)
        self.destroy()

    def on_close(self):
        """Handle the close event for the settings window."""
        self.destroy()