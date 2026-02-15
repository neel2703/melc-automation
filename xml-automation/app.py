"""
Simple tkinter UI for runSetting configuration.
Uses only Python standard library - no extra dependencies.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import subprocess
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils", "runsetting_config.json")
DEFAULT_CONFIG = {
    "stepCount": 56,
    "visualFieldCount": 3,
    "imageCountNegative": 4,
    "imageCountPositive": 4,
}


def load_config():
    """Load config from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
            if "imageCountNegative" not in cfg and cfg.get("visualFieldConfigs"):
                first = cfg["visualFieldConfigs"][0]
                cfg["imageCountNegative"] = first.get("imageCountNegative", 4)
                cfg["imageCountPositive"] = first.get("imageCountPositive", 4)
            return cfg
        except (json.JSONDecodeError, IOError, IndexError, KeyError):
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save config to JSON file."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def run_xml_gen():
    """Run the xml-gen script."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(app_dir, "utils", "xml-gen.py")
    # xml-gen expects to run from project root (uses paths like xml-automation/...)
    project_root = os.path.dirname(app_dir)
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"xml-gen.py not found at {script_path}")
        return
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            messagebox.showinfo("Success", "XML generated successfully: output.xml")
        else:
            messagebox.showerror(
                "Generation Failed",
                f"Error running xml-gen:\n{result.stderr or result.stdout}",
            )
    except subprocess.TimeoutExpired:
        messagebox.showerror("Error", "Generation timed out.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


class RunSettingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("runSetting Configuration")
        self.root.resizable(True, True)
        self.root.minsize(360, 200)

        self.config = load_config()
        self.entries = {}
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Step Count
        row1 = ttk.Frame(main)
        row1.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row1, text="stepCount:", width=18, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
        self.entries["stepCount"] = ttk.Entry(row1, width=10)
        self.entries["stepCount"].pack(side=tk.LEFT)
        self.entries["stepCount"].insert(0, str(self.config.get("stepCount", 56)))
        ttk.Label(row1, text="(number of incStep sections)").pack(side=tk.LEFT, padx=(8, 0))

        # Visual Field Count
        row2 = ttk.Frame(main)
        row2.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row2, text="visualFieldCount:", width=18, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
        self.entries["visualFieldCount"] = ttk.Entry(row2, width=8)
        self.entries["visualFieldCount"].pack(side=tk.LEFT)
        self.entries["visualFieldCount"].insert(
            0, str(self.config.get("visualFieldCount", 3))
        )

        # Stack (same for all FOVs)
        row3 = ttk.Frame(main)
        row3.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(row3, text="imageCountNegative:", width=18, anchor="e").pack(side=tk.LEFT, padx=(0, 6))
        self.entries["imageCountNegative"] = ttk.Entry(row3, width=6)
        self.entries["imageCountNegative"].pack(side=tk.LEFT, padx=(0, 12))
        self.entries["imageCountNegative"].insert(
            0, str(self.config.get("imageCountNegative", 4))
        )
        ttk.Label(row3, text="imageCountPositive:").pack(side=tk.LEFT, padx=(0, 4))
        self.entries["imageCountPositive"] = ttk.Entry(row3, width=6)
        self.entries["imageCountPositive"].pack(side=tk.LEFT)
        self.entries["imageCountPositive"].insert(
            0, str(self.config.get("imageCountPositive", 4))
        )
        ttk.Label(row3, text="(same for all FOVs)").pack(side=tk.LEFT, padx=(8, 0))

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Save Config", command=self.on_save).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Generate XML", command=self.on_generate).pack(
            side=tk.LEFT
        )

    def get_visual_field_count(self):
        try:
            n = int(self.entries["visualFieldCount"].get())
            return max(1, min(10, n))
        except ValueError:
            return 3

    def collect_config(self):
        try:
            step_count = int(self.entries["stepCount"].get())
            if step_count < 1:
                step_count = 1
        except ValueError:
            step_count = 56

        vf_count = self.get_visual_field_count()
        try:
            neg = int(self.entries["imageCountNegative"].get())
        except (ValueError, KeyError, tk.TclError):
            neg = 4
        try:
            pos = int(self.entries["imageCountPositive"].get())
        except (ValueError, KeyError, tk.TclError):
            pos = 4

        configs = [
            {"imageCountNegative": neg, "imageCountPositive": pos}
            for _ in range(vf_count)
        ]
        return {
            "stepCount": step_count,
            "visualFieldCount": vf_count,
            "imageCountNegative": neg,
            "imageCountPositive": pos,
            "visualFieldConfigs": configs,
        }

    def on_save(self):
        self.config = self.collect_config()
        save_config(self.config)
        messagebox.showinfo("Saved", "Config saved to runsetting_config.json")

    def on_generate(self):
        self.config = self.collect_config()
        save_config(self.config)
        run_xml_gen()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = RunSettingApp()
    app.run()
