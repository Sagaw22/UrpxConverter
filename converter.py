import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

def get_label(node):
    pl = node.get("programLabel")
    # Direct string label
    if isinstance(pl, str) and pl.strip():
        return pl
    # List label parts
    if isinstance(pl, list):
        parts = []
        for d in pl:
            if 'value' in d:
                parts.append(str(d['value']))
            elif 'translationKey' in d:
                key = d['translationKey']
                if key.startswith('program-node-label.'):
                    key = key[len('program-node-label.'):]
                key = key.replace('.', ' ').title()
                parts.append(key)
        label = " ".join(parts).strip()
        if label:
            return label
    # Fallback to contributedNode type
    cn = node.get('contributedNode', {}).get('type')
    if cn:
        label = cn.replace('ur-', '').replace('-', ' ').title()
        return label
    return "Unknown"

def urpx_to_script(urpx_path, output_folder):
    with open(urpx_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    func_name = data.get('application', {}) \
                   .get('applicationInfo', {}) \
                   .get('name', os.path.splitext(os.path.basename(urpx_path))[0])
    urscript = data.get('application', {}) \
                    .get('urscript', {}) \
                    .get('script', '')
    lines = [f"def {func_name}():", "  global _hidden_verificationVariable=0"]
    for line in urscript.splitlines():
        lines.append(f"  {line}")
    base = os.path.splitext(os.path.basename(urpx_path))[0]
    out_path = os.path.join(output_folder, f"{base}_converted.script")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return out_path

def urpx_to_txt(urpx_path, output_folder):
    with open(urpx_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build root
    root = {"name": "Program", "children": []}
    # Variables Setup (even if empty)
    vars_node = {"name": "Variables Setup", "children": []}
    for var in data.get("program", {}).get("variableDeclarations", []):
        vars_node["children"].append({"programLabel": var.get("name", "<anon>")})
    root["children"].append(vars_node)

    # Robot Program: use first function under ur-functions
    prog_children = data.get("program", {}).get("programContent", {}).get("children", [])
    func_nodes = []
    # Find functions node (type ur-functions)
    for node in prog_children:
        if node.get('contributedNode', {}).get('type') == 'ur-functions':
            func_nodes = node.get('children', [])
            break
    if func_nodes:
        main_func = func_nodes[0]
        prog_nodes = main_func.get('children', [])
    else:
        prog_nodes = []
    robot_node = {"name": "Robot Program", "children": []}
    for n in prog_nodes:
        robot_node["children"].append(n)
    root["children"].append(robot_node)

    # Walk and label
    def walk(node, indent=0, lines=None):
        if lines is None:
            lines = []
        lines.append("  " * indent + get_label(node))
        for child in node.get("children", []):
            walk(child, indent + 1, lines)
        return lines

    lines = walk(root)
    base = os.path.splitext(os.path.basename(urpx_path))[0]
    out_path = os.path.join(output_folder, f"{base}_converted.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return out_path

class URPXConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URPX Converter")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TButton', font=('Arial', 11), padding=8)
        style.configure('TLabel', font=('Arial', 10), padding=6)

        self.urpx_paths = []
        self.output_folder = None

        self.notebook = ttk.Notebook(root)
        self.tab_script = ttk.Frame(self.notebook)
        self.tab_txt = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_script, text="To .script")
        self.notebook.add(self.tab_txt, text="To .txt")
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # .script tab
        self.script_label = ttk.Label(self.tab_script, text="No URPX files selected")
        self.script_label.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Button(self.tab_script, text="Select URPX Files", command=self.select_urpx_files).pack(padx=10, pady=5)
        self.script_out_label = ttk.Label(self.tab_script, text="No output folder selected")
        self.script_out_label.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Button(self.tab_script, text="Select Output Folder", command=self.select_output_folder).pack(padx=10, pady=5)
        self.script_convert_btn = ttk.Button(self.tab_script, text="Convert", command=self.convert)
        self.script_convert_btn.config(width=20)
        self.script_convert_btn.pack(pady=(15, 10))

        # .txt tab
        self.txt_label = ttk.Label(self.tab_txt, text="No URPX files selected")
        self.txt_label.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Button(self.tab_txt, text="Select URPX Files", command=self.select_urpx_files).pack(padx=10, pady=5)
        self.txt_out_label = ttk.Label(self.tab_txt, text="No output folder selected")
        self.txt_out_label.pack(fill='x', padx=10, pady=(10, 5))
        ttk.Button(self.tab_txt, text="Select Output Folder", command=self.select_output_folder).pack(padx=10, pady=5)
        self.txt_convert_btn = ttk.Button(self.tab_txt, text="Convert", command=self.convert)
        self.txt_convert_btn.config(width=20)
        self.txt_convert_btn.pack(pady=(15, 10))

    def select_urpx_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("URPX Files", "*.urpx"), ("All Files", "*.*")],
            title="Select URPX files"
        )
        if not files:
            return
        self.urpx_paths = list(files)
        names = [os.path.basename(f) for f in files]
        tab = self.notebook.index(self.notebook.select())
        if tab == 0:
            self.script_label.config(text=", ".join(names))
        else:
            self.txt_label.config(text=", ".join(names))

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if not folder:
            return
        self.output_folder = folder
        tab = self.notebook.index(self.notebook.select())
        if tab == 0:
            self.script_out_label.config(text=folder)
        else:
            self.txt_out_label.config(text=folder)

    def convert(self):
        if not self.urpx_paths or not self.output_folder:
            messagebox.showwarning("Missing Info", "Select URPX files and output folder.")
            return
        errors, successes = [], []
        tab = self.notebook.index(self.notebook.select())
        for path in self.urpx_paths:
            try:
                out = urpx_to_script(path, self.output_folder) if tab == 0 else urpx_to_txt(path, self.output_folder)
                successes.append(os.path.basename(out))
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")
        if errors:
            messagebox.showerror("Conversion Errors", "\n".join(errors))
        else:
            messagebox.showinfo("Done", "Converted files:\n" + "\n".join(successes))

if __name__ == "__main__":
    root = tk.Tk()
    URPXConverterApp(root)
    root.mainloop()
