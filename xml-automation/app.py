"""
Simple tkinter UI for XML generation.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys


def run_xml_gen(xl_path):
    """Run the xml-gen script with the selected xl file."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(app_dir, "utils", "xml-gen.py")
    project_root = os.path.dirname(app_dir)
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"xml-gen.py not found at {script_path}")
        return
    try:
        result = subprocess.run(
            [sys.executable, script_path, xl_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            xml_path = os.path.splitext(xl_path)[0] + ".xml"
            messagebox.showinfo("Success", f"XML generated successfully:\n{xml_path}")
        else:
            messagebox.showerror(
                "Generation Failed",
                f"Error running xml-gen:\n{result.stderr or result.stdout}",
            )
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Generation timed out.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("XML Generator")
        self.root.resizable(True, True)
        self.root.minsize(500, 120)

        self.xl_path = tk.StringVar()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # File picker row
        file_row = ttk.Frame(main)
        file_row.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(file_row, text="Excel file:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Entry(file_row, textvariable=self.xl_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(file_row, text="Browse", command=self.browse).pack(side=tk.LEFT)

        # Generate button
        ttk.Button(main, text="Generate XML", command=self.on_generate).pack()

    def browse(self):
        path = filedialog.askopenfilename(
            title="Select Excel file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.xl_path.set(path)

    def on_generate(self):
        xl = self.xl_path.get().strip()
        if not xl:
            messagebox.showwarning("No file", "Please select an Excel file first.")
            return
        if not os.path.exists(xl):
            messagebox.showerror("Error", f"File not found:\n{xl}")
            return
        run_xml_gen(xl)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()