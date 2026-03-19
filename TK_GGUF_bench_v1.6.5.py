import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import re
import psutil 
from datetime import datetime

class GgufGui:
    def __init__(self, root):
        self.root = root
        self.root.title("GGUF Runner & Inspector v1.6.5")
        self.root.geometry("950x620") 
        self.process = None
        self.is_stopping = False

        # System hardware detection
        mem = psutil.virtual_memory()
        self.total_sys_ram_gb = mem.total / (1024**3)
        self.max_threads = psutil.cpu_count(logical=True)

        # --- 1. Model Selection ---
        tk.Label(root, text="Model File (GGUF):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.model_path = tk.StringVar()
        tk.Entry(root, textvariable=self.model_path, width=75).grid(row=0, column=1, padx=5)
        tk.Button(root, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        # --- 2. External Prompt File Selection ---
        tk.Label(root, text="Prompt File (.txt):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.prompt_file_path = tk.StringVar()
        tk.Entry(root, textvariable=self.prompt_file_path, width=75).grid(row=1, column=1, padx=5)
        tk.Button(root, text="Browse", command=self.browse_prompt_file).grid(row=1, column=2, padx=5)

        # --- 3. Custom Prompt (Text Box) ---
        tk.Label(root, text="Custom Prompt:").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        self.custom_prompt = tk.Text(root, height=3, width=75, font=("Arial", 9))
        self.custom_prompt.grid(row=2, column=1, padx=5, pady=5)
        self.custom_prompt.insert("1.0", "Explain the difference between CPU and GPU inference in simple terms.")

        # --- 4. Parameters ---
        param_frame = tk.Frame(root)
        param_frame.grid(row=3, column=0, columnspan=3, sticky="w", padx=10)
        
        tk.Label(param_frame, text="GPU Layers:").pack(side="left")
        self.ngl = tk.IntVar(value=0)
        tk.Spinbox(param_frame, from_=0, to=999, textvariable=self.ngl, width=5).pack(side="left", padx=5)

        tk.Label(param_frame, text=f"Threads (Max {self.max_threads}):").pack(side="left", padx=5)
        self.threads = tk.IntVar(value=3)
        tk.Spinbox(param_frame, from_=1, to=self.max_threads, textvariable=self.threads, width=5).pack(side="left", padx=5)

        tk.Label(param_frame, text="Context:").pack(side="left", padx=5)
        self.context = tk.IntVar(value=4096)
        tk.Spinbox(param_frame, from_=2048, to=128000, textvariable=self.context, width=8).pack(side="left", padx=5)

        # Added Predicted Tokens (-n)
        tk.Label(param_frame, text="Tokens (-n):").pack(side="left", padx=5)
        self.n_predict = tk.IntVar(value=200)
        tk.Spinbox(param_frame, from_=0, to=20000, textvariable=self.n_predict, width=7).pack(side="left", padx=5)

        # Reasoning Budget
        tk.Label(param_frame, text="Budget (-1 no limit, 0 no reasoning, 1 to 8192):").pack(side="left", padx=5)
        self.reasoning_budget = tk.IntVar(value=0)
        tk.Spinbox(param_frame, from_=-1, to=8192, textvariable=self.reasoning_budget, width=6).pack(side="left", padx=5)

        cb_frame = tk.Frame(root)
        cb_frame.grid(row=4, column=0, columnspan=3, sticky="w", padx=10)
        self.ctk_var, self.ctv_var, self.fa_var = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        tk.Checkbutton(cb_frame, text="Quantize K Cache", variable=self.ctk_var).pack(side="left", padx=5)
        tk.Checkbutton(cb_frame, text="Quantize V Cache", variable=self.ctv_var).pack(side="left", padx=5)
        tk.Checkbutton(cb_frame, text="Flash Attention", variable=self.fa_var).pack(side="left", padx=5)

        # --- 5. Info & Performance Panel ---
        info_frame = tk.LabelFrame(root, text=" Live Model Stats & Performance ", fg="blue", font=("Arial", 10, "bold"))
        info_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        
        self.stat_layers = tk.StringVar(value="Layers: -")
        self.stat_free_ram = tk.StringVar(value=f"System Available: {mem.available/(1024**3):.2f} GB")
        self.stat_model_ram = tk.StringVar(value="Weights: -")
        self.stat_kv_ram = tk.StringVar(value="KV Cache: -")
        self.stat_buffer_ram = tk.StringVar(value="Compute Buffer: -")
        self.stat_total_ram = tk.StringVar(value="Model Est. Total: -")
        self.stat_prompt_speed = tk.StringVar(value="Prompt: -")
        self.stat_gen_speed = tk.StringVar(value="Gen: -")

        tk.Label(info_frame, textvariable=self.stat_layers).grid(row=0, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_free_ram, fg="green").grid(row=0, column=1, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_model_ram).grid(row=1, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_kv_ram).grid(row=1, column=1, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_buffer_ram).grid(row=2, column=0, padx=20, sticky="w")
        self.ram_display = tk.Label(info_frame, textvariable=self.stat_total_ram, font=("Arial", 9, "bold"))
        self.ram_display.grid(row=2, column=1, padx=20, sticky="w")

        perf_label_frame = tk.Frame(info_frame)
        perf_label_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="w")
        tk.Label(perf_label_frame, textvariable=self.stat_prompt_speed, fg="purple", font=("Arial", 9, "bold")).pack(side="left", padx=20)
        tk.Label(perf_label_frame, textvariable=self.stat_gen_speed, fg="darkred", font=("Arial", 9, "bold")).pack(side="left", padx=20)

        # Visual Bar
        self.canvas_width = 840
        self.canvas = tk.Canvas(info_frame, width=self.canvas_width, height=25, bg="#e0e0e0", highlightthickness=1)
        self.canvas.grid(row=4, column=0, columnspan=2, padx=20, pady=5)
        
        legend_frame = tk.Frame(info_frame)
        legend_frame.grid(row=5, column=0, columnspan=2, pady=2)
        tk.Label(legend_frame, text="■ OS/Apps", fg="#999999").pack(side="left", padx=10)
        tk.Label(legend_frame, text="■ Model Total", fg="#3366cc").pack(side="left", padx=10)
        tk.Label(legend_frame, text="■ Projected Free", fg="#00FF00").pack(side="left", padx=10)

        # --- 6. Buttons ---
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=5)
        self.run_btn = tk.Button(btn_frame, text="Run Inference", command=lambda: self.start_task("run"), bg="#28a745", fg="white", width=12)
        self.run_btn.pack(side="left", padx=5)
        self.inspect_btn = tk.Button(btn_frame, text="Inspect Model", command=lambda: self.start_task("inspect"), bg="#007bff", fg="white", width=12)
        self.inspect_btn.pack(side="left", padx=5)
        tk.Button(btn_frame, text="Stop", command=self.stop_process, bg="#dc3545", fg="white", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Save Log", command=self.save_log, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear All", command=self.clear_all, width=10).pack(side="left", padx=5)

        self.status_label = tk.Label(root, text="System: Monitoring... | PID: None", fg="grey")
        self.status_label.grid(row=8, column=0, columnspan=3)

        self.output_text = tk.Text(root, height=12, width=120, font=("Consolas", 9))
        self.output_text.grid(row=9, column=0, columnspan=3, padx=10, pady=5)

        self.current_model_mib = self.current_kv_mib = self.current_compute_mib = 0.0
        self.current_mode = "run"
        self.draw_ram_bar(0)

    def browse_file(self):
        fn = filedialog.askopenfilename(filetypes=[("GGUF files", "*.gguf")])
        if fn: self.model_path.set(fn)

    def browse_prompt_file(self):
        fn = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if fn:
            self.prompt_file_path.set(fn)
            self.custom_prompt.delete("1.0", tk.END)
            self.custom_prompt.insert("1.0", f"[File Mode Active: {os.path.basename(fn)}]")
            self.custom_prompt.config(state="disabled", bg="#f0f0f0")

    def parse_line(self, line):
        if self.current_mode == "run" and "Prompt:" in line and "Generation:" in line:
            m = re.search(r"Prompt:\s+([\d\.]+)\s+t/s\s+\|\s+Generation:\s+([\d\.]+)\s+t/s", line)
            if m:
                self.stat_prompt_speed.set(f"Prompt: {m.group(1)} t/s")
                self.stat_gen_speed.set(f"Gen: {m.group(2)} t/s")

        if "Host" in line and "=" in line and "+" in line:
            m = re.search(r"\|\s+-\s+Host\s+\|\s+\d+\s+=\s+([\d\.]+)\s+\+\s+([\d\.]+)\s+\+\s+([\d\.]+)", line)
            if m:
                self.current_model_mib = float(m.group(1))
                self.current_kv_mib = float(m.group(2))
                self.current_compute_mib = float(m.group(3))
                self.stat_model_ram.set(f"Weights: {self.current_model_mib:.2f} MiB")
                self.stat_kv_ram.set(f"KV Cache: {self.current_kv_mib:.2f} MiB")
                self.stat_buffer_ram.set(f"Compute Buffer: {self.current_compute_mib:.2f} MiB")

        if "n_layer" in line:
            m = re.search(r"n_layer\s+=\s+(\d+)", line)
            if m: self.stat_layers.set(f"Layers: {m.group(1)}")

        # Legacy buffer updates
        if "model buffer size" in line:
            m = re.search(r"size\s+=\s+([\d\.]+)", line)
            if m and float(m.group(1)) > self.current_model_mib:
                self.current_model_mib = float(m.group(1))
                self.stat_model_ram.set(f"Weights: {self.current_model_mib:.2f} MiB")
        
        if "KV buffer size" in line:
            m = re.search(r"size\s+=\s+([\d\.]+)", line)
            if m and float(m.group(1)) > self.current_kv_mib:
                self.current_kv_mib = float(m.group(1))
                self.stat_kv_ram.set(f"KV Cache: {self.current_kv_mib:.2f} MiB")

        if "compute buffer size" in line:
            m = re.search(r"size\s+=\s+([\d\.]+)", line)
            if m and float(m.group(1)) > self.current_compute_mib:
                self.current_compute_mib = float(m.group(1))
                self.stat_buffer_ram.set(f"Compute Buffer: {self.current_compute_mib:.2f} MiB")
        
        self.update_total_ram_display()

    def update_total_ram_display(self):
        total_gb = (self.current_model_mib + self.current_kv_mib + self.current_compute_mib) / 1024
        self.stat_total_ram.set(f"Model Est. Total: {total_gb:.2f} GB")
        mem = psutil.virtual_memory()
        usage_ratio = (total_gb + (mem.total - mem.available)/(1024**3)) / self.total_sys_ram_gb
        self.ram_display.config(fg="red" if usage_ratio > 0.9 else "orange" if usage_ratio > 0.7 else "black")
        self.draw_ram_bar(total_gb)

    def draw_ram_bar(self, est_model_gb):
        self.canvas.delete("all")
        mem = psutil.virtual_memory()
        used_now_gb = (mem.total - mem.available) / (1024**3)
        px_used = (used_now_gb / self.total_sys_ram_gb) * self.canvas_width
        px_model = (est_model_gb / self.total_sys_ram_gb) * self.canvas_width
        self.canvas.create_rectangle(0, 0, self.canvas_width, 25, fill="#00FF00", outline="")
        self.canvas.create_rectangle(0, 0, px_used, 25, fill="#999999", outline="")
        color = "#3366cc"
        if (used_now_gb + est_model_gb) > self.total_sys_ram_gb: color = "#cc0000"
        self.canvas.create_rectangle(px_used, 0, min(self.canvas_width, px_used + px_model), 25, fill=color, outline="")
        future_free = max(0, self.total_sys_ram_gb - (used_now_gb + est_model_gb))
        self.stat_free_ram.set(f"System Available: {mem.available/(1024**3):.2f} GB (Projected: {future_free:.2f} GB)")

    def execute_command(self, cmd, is_inference):
        try:
            self.current_model_mib = self.current_kv_mib = self.current_compute_mib = 0.0
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, creationflags=0x08000000, errors="replace")
            self.status_label.config(text=f"Total System RAM: {self.total_sys_ram_gb:.2f} GB | PID: {self.process.pid}")
            
            while not self.is_stopping:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None: break
                if line:
                    self.output_text.insert(tk.END, line)
                    self.output_text.see(tk.END)
                    self.parse_line(line)
                    self.root.update_idletasks() 
            
            if self.process:
                self.process.stdout.close()
                self.process.wait()
            
            self.status_label.config(text=f"Total System RAM: {self.total_sys_ram_gb:.2f} GB | PID: None")
            self.is_stopping = False
            self.run_btn.config(state="normal"); self.inspect_btn.config(state="normal")
        except Exception as e: 
            messagebox.showerror("Error", str(e))
            self.is_stopping = False
            self.run_btn.config(state="normal"); self.inspect_btn.config(state="normal")

    def stop_process(self):
        if self.process:
            self.is_stopping = True
            self.process.terminate()
            self.output_text.insert(tk.END, "\n[User Terminated Process]\n")

    def save_log(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            return messagebox.showwarning("Empty", "No log content to save.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"GGUF_Bench_Log_{timestamp}.txt"
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename)
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Log saved to:\n{file_path}")

    def clear_all(self):
        self.output_text.delete(1.0, tk.END)
        self.prompt_file_path.set("")
        self.custom_prompt.config(state="normal", bg="white")
        self.custom_prompt.delete("1.0", tk.END)
        self.custom_prompt.insert("1.0", "Explain the difference between CPU and GPU inference in simple terms.")
        self.stat_prompt_speed.set("Prompt: -"); self.stat_gen_speed.set("Gen: -")
        self.current_model_mib = self.current_kv_mib = self.current_compute_mib = 0.0
        self.update_total_ram_display()

    def start_task(self, mode):
        if self.process and self.process.poll() is None:
            messagebox.showwarning("Busy", "A task is already running.")
            return

        if not self.model_path.get(): return messagebox.showerror("Error", "Select model.")
        
        self.current_mode = mode
        cmd = ['.\\llama-cli.exe', '-m', self.model_path.get(), '-ngl', str(self.ngl.get()), '-t', str(self.threads.get()), '--mmap', '-c', str(self.context.get()), '-st', '-lv', '3']
        
        cmd.extend(['--reasoning-budget', str(self.reasoning_budget.get())])
            
        if self.ctk_var.get(): cmd.extend(['-ctk', 'q8_0'])
        if self.ctv_var.get(): cmd.extend(['-ctv', 'q8_0'])
        if self.fa_var.get(): cmd.extend(['-fa', 'on'])
        
        is_inference = (mode == "run")
        if mode == "inspect": 
            cmd.extend(['-n', '0', '-p', '"Hi!"', '--no-display-prompt'])
        else: 
            if self.prompt_file_path.get():
                cmd.extend(['-f', self.prompt_file_path.get()])
            else:
                user_p = self.custom_prompt.get("1.0", tk.END).strip()
                cmd.extend(['-p', f'"{user_p}"'])
            # User choice for tokens
            cmd.extend(['-n', str(self.n_predict.get())])
        
        print(f"\nEXECUTING: {' '.join(cmd)}\n")
        self.output_text.delete(1.0, tk.END)
        self.run_btn.config(state="disabled"); self.inspect_btn.config(state="disabled")
        threading.Thread(target=self.execute_command, args=(cmd, is_inference), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = GgufGui(root)
    root.mainloop()