import tkinter as tk
from tkinter import ttk

class TestScrollbar(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TTR")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")  # Fullscreen
        self.attributes("-topmost", True)

        # Add a close button
        close_button = tk.Button(self, text="Close", font=("Arial", 12), bg="red", fg="white", command=self.destroy)
        close_button.pack(pady=10)

        # Create a frame for the frozen and scrollable tables
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a frame for the frozen columns
        frozen_frame = tk.Frame(main_frame)
        frozen_frame.pack(side="left", fill="y")

        # Create a frame for the scrollable columns
        scrollable_frame = tk.Frame(main_frame)
        scrollable_frame.pack(side="left", fill="both", expand=True)

        # Create a style for the Treeview to adjust row height
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)  # Set row height to 25 pixels

        # Create the frozen table (Treeview)
        frozen_table = ttk.Treeview(frozen_frame, columns=[f"Col {i}" for i in range(1, 5)], show="headings", height=20)
        for i in range(1, 5):
            frozen_table.heading(f"Col {i}", text=f"Column {i}")
            frozen_table.column(f"Col {i}", width=100, anchor="center")

        # Pack the frozen table
        frozen_table.pack(fill="y")

        # Create the scrollable table (Treeview)
        scrollable_table = ttk.Treeview(scrollable_frame, columns=[f"Col {i}" for i in range(5, 21)], show="headings", height=20)
        for i in range(5, 21):
            scrollable_table.heading(f"Col {i}", text=f"Column {i}")
            scrollable_table.column(f"Col {i}", width=100, anchor="center")

        # Add vertical scrollbar for both tables
        v_scrollbar = ttk.Scrollbar(scrollable_frame, orient="vertical")

        # Configure the scrollbar to control both tables
        def scroll_both(*args):
            # Synchronize the vertical scrolling of both tables
            frozen_table.yview(*args)
            scrollable_table.yview(*args)

        v_scrollbar.configure(command=scroll_both)
        v_scrollbar.pack(side="right", fill="y")

        # Link the scrollbar to both tables
        frozen_table.configure(yscrollcommand=lambda *args: v_scrollbar.set(*args))
        scrollable_table.configure(yscrollcommand=lambda *args: v_scrollbar.set(*args))

        # Add horizontal scrollbar for the scrollable table
        h_scrollbar = ttk.Scrollbar(scrollable_frame, orient="horizontal", command=scrollable_table.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        scrollable_table.configure(xscrollcommand=h_scrollbar.set)

        # Pack the scrollable table
        scrollable_table.pack(fill="both", expand=True)

        # Populate both tables with sample data
        for row in range(1, 31):  # Add 30 rows to trigger vertical scrolling
            frozen_table.insert("", "end", values=[f"Row {row} Col {col}" for col in range(1, 5)])
            scrollable_table.insert("", "end", values=[f"Row {row} Col {col}" for col in range(5, 21)])

        # Synchronize row selection between the two tables
        def sync_selection(event):
            try:
                # Determine which table triggered the event
                widget = event.widget

                if widget == frozen_table:
                    # A row was selected in the frozen table
                    selected_item = frozen_table.selection()
                    if selected_item:
                        index = frozen_table.index(selected_item[0])
                        if index < len(scrollable_table.get_children()):
                            # Highlight the corresponding row in the scrollable table
                            scrollable_table.selection_set(scrollable_table.get_children()[index])
                            scrollable_table.see(scrollable_table.get_children()[index])
                elif widget == scrollable_table:
                    # A row was selected in the scrollable table
                    selected_item = scrollable_table.selection()
                    if selected_item:
                        index = scrollable_table.index(selected_item[0])
                        if index < len(frozen_table.get_children()):
                            # Highlight the corresponding row in the frozen table
                            frozen_table.selection_set(frozen_table.get_children()[index])
                            frozen_table.see(frozen_table.get_children()[index])
            except Exception as e:
                print(f"Error in sync_selection: {e}")  # Debugging output

        frozen_table.bind("<<TreeviewSelect>>", sync_selection)
        scrollable_table.bind("<<TreeviewSelect>>", sync_selection)

        # Enhanced mouse wheel scrolling for tight synchronization
        def on_mouse_wheel(event):
            # Calculate the scroll delta
            delta = -1 if event.delta > 0 else 1

            # Get the current scroll position of the frozen table
            current_scroll = frozen_table.yview()

            # Calculate the new scroll position
            new_scroll = max(0, min(1, current_scroll[0] + delta * 0.1))

            # Apply the new scroll position to both tables
            frozen_table.yview_moveto(new_scroll)
            scrollable_table.yview_moveto(new_scroll)

        # Bind mouse wheel scrolling to both tables
        frozen_table.bind("<MouseWheel>", on_mouse_wheel)
        scrollable_table.bind("<MouseWheel>", on_mouse_wheel)


if __name__ == "__main__":
    app = TestScrollbar()
    app.mainloop()