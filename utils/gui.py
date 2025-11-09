import tkinter as tk
from tkinter import ttk, messagebox
import csv

# Read the class timetables from CSV file
# 
# @param filename -- Path to the CSV file
def read_class_csv(filename):
    timetables = {}
    
    # Read file and split into blocks
    with open(filename, "r",) as f:
        lines = [line.strip() for line in f if line.strip()]

    class_name = None
    current_block = []

    for line in lines:
        # Get all the class headers
        if line.startswith("---Class"):
            # Save previous class
            if class_name and current_block:
                reader = csv.reader(current_block)
                rows = list(reader)
                headers = rows[0]
                data = rows[1:]
                timetables[class_name] = (headers, data)
            # New class name
            class_name = line.replace("---", "").replace("Class", "").replace("---", "").strip()
            current_block = []
        else:
            current_block.append(line)

    # Save last one
    if class_name and current_block:
        reader = csv.reader(current_block)
        rows = list(reader)
        headers = rows[0]
        data = rows[1:]
        timetables[class_name] = (headers, data)

    return timetables

# Read the teacher timetables from CSV file
# 
# @param filename -- Path to the CSV file
def read_teacher_csv(filename):
    timetables = {}

    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    teacher_name = None
    current_block = []

    for line in lines:
        # Get the teacher headers
        if "," not in line and not line.startswith("Day"):
            # Save previous teacher
            if teacher_name and current_block:
                reader = csv.reader(current_block)
                rows = list(reader)
                headers = rows[0]
                data = rows[1:]
                timetables[teacher_name] = (headers, data)
            teacher_name = line.replace("———", "").replace("———", "").strip()
            current_block = []
        else:
            current_block.append(line)

    # Save last one
    if teacher_name and current_block:
        reader = csv.reader(current_block)
        rows = list(reader)
        headers = rows[0]
        data = rows[1:]
        timetables[teacher_name] = (headers, data)

    return timetables

# Display the timetable in a new window
#
# @param headers -- List of column headers
# @param data -- List of rows (each row is a list of values)
# @param title -- Title of the window
def show_timetable(headers, data, title):
    win = tk.Toplevel()
    win.title(title)
    win.geometry("1000x190")
    win.config(bg="#1E2761")

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, show="headings")
    tree["columns"] = headers

    for col in headers:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    for row in data:
        tree.insert("", "end", values=row)

    tree.pack(fill="both", expand=True)

    # Add vertical scrollbar
    scroll = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
    scroll.pack(side="right", fill="y")
    tree.configure(yscrollcommand=scroll.set)

# Button stuff :)
#
# @param class_var -- Tkinter StringVar for class selection
# @param class_tts -- Dictionary of class timetables
def load_class_tt(class_var, class_tts):
    name = class_var.get().strip()
    if not name:
        messagebox.showwarning("Input", "Please select a class.")
        return
    if name not in class_tts:
        messagebox.showerror("Not Found", f"No timetable found for class {name}.")
        return
    headers, data = class_tts[name]
    show_timetable(headers, data, f"Class Timetable - {name}")

def load_teacher_tt(teacher_var, teacher_tts):
    name = teacher_var.get().strip()
    if not name:
        messagebox.showwarning("Input", "Please select a teacher.")
        return
    if name not in teacher_tts:
        messagebox.showerror("Not Found", f"No timetable found for teacher {name}.")
        return
    headers, data = teacher_tts[name]
    show_timetable(headers, data, f"Teacher Timetable - {name}")

# The main GUI function
def main():
    root = tk.Tk()
    root.title("Timetables")
    root.geometry("500x300")
    root.config(bg="#1E2761")  # Deep blue background

    # Load CSVs
    class_tts = read_class_csv("ctt.csv")
    teacher_tts = read_teacher_csv("ttt.csv")

    # --- Class section ---
    tk.Label(root, text="Class", font=("Helvetica", 18, "bold"), fg="white", bg="#1E2761").grid(column=1, row=1, sticky=(tk.W, tk.E))
    class_var = tk.StringVar()
    class_menu = ttk.Combobox(root, textvariable=class_var, values=list(class_tts.keys()),
                              font=("Helvetica", 14), width=15, state="readonly")
    class_menu.grid(column=2, row=1, sticky=(tk.W, tk.E))
    tk.Button(root, text="Show Timetable", font=("Helvetica", 12, "bold"), bg="yellow",
              command=lambda: load_class_tt(class_var, class_tts)).grid(column=1, columnspan=2, row=2, sticky=(tk.W, tk.E))

    tk.Label(root, text="", font=("Helvetica", 14, "bold"), fg="white", bg="#1E2761").grid(column=1, columnspan=2, row=3, sticky=(tk.E, tk.W))

    # --- Teacher section ---
    tk.Label(root, text="Teacher", font=("Helvetica", 18, "bold"), fg="white", bg="#1E2761").grid(column=1, row=4, sticky=(tk.W, tk.E))
    teacher_var = tk.StringVar()
    teacher_menu = ttk.Combobox(root, textvariable=teacher_var, values=list(teacher_tts.keys()),
                              font=("Helvetica", 14), width=15, state="readonly")
    teacher_menu.grid(column=2, row=4, sticky=(tk.W, tk.E))
    tk.Button(root, text="Show Timetable", font=("Helvetica", 12, "bold"), bg="yellow",
              command=lambda: load_teacher_tt(teacher_var, teacher_tts)).grid(column=1, columnspan=2, row=5, sticky=(tk.W, tk.E))

    root.columnconfigure(2, weight=1)
    root.rowconfigure(5, weight=1)
    for i in root.winfo_children():
        i.grid_configure(padx=15, pady=10)

    root.mainloop()
