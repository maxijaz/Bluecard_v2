import tkinter as tk

root = tk.Tk()
root.title("Relief Styles")

reliefs = ['flat', 'raised', 'sunken', 'groove', 'ridge', 'solid']

for i, relief in enumerate(reliefs):
    frame = tk.Frame(root, relief=relief, borderwidth=5)
    frame.grid(row=0, column=i, padx=5, pady=10)
    label = tk.Label(frame, text=relief, width=10)
    label.pack(padx=5, pady=5)

root.mainloop()
