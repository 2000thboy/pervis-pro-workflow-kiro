import customtkinter as ctk
from launcher.services.traffic_control import traffic_crtl
import requests
import json
from tkinter import simpledialog, messagebox
from launcher.ui.storage_panel import StorageTopologyPanel
# Reuses existing components

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Traffic Control Section
        self._create_traffic_control()
        self._create_model_section()
        
        # 2. Storage Topology Section
        self._create_storage_section()
        
    def _create_traffic_control(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="性能控制 (Performance)", font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=10)
        
        self.speed_slider = ctk.CTkSlider(frame, from_=0, to=2, number_of_steps=2, command=self._on_speed_change)
        
        # Sync with current state
        modes = ["silent", "balanced", "performance"]
        current = traffic_crtl.current_mode
        if current in modes:
            self.speed_slider.set(modes.index(current))
        else:
            self.speed_slider.set(1)
            
        self.speed_slider.pack(fill="x", padx=15, pady=5)
        
        self.speed_label = ctk.CTkLabel(frame, text="平衡模式 (Balanced)", text_color="#3498DB")
        self.speed_label.pack(pady=(0, 10))

    def _create_storage_section(self):
        # We wrap the existing StorageTopologyPanel
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame, text="存储拓扑 (Storage)", font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=10)
        
        # Need to fix the import or ensure storage_panel is accessible
        self.topology = StorageTopologyPanel(
            frame,
            on_import_click=self._on_click_import,
            on_scan_click=self._on_click_scan
        )
        self.topology.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_model_section(self):
        # Model selection UI
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(frame, text="模型选择 (LLM Provider)", font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=10)

        self.model_var = ctk.StringVar(value="local")
        options = ["local", "gemini", "openai"]
        dropdown = ctk.CTkComboBox(frame, variable=self.model_var, values=options)
        dropdown.pack(fill="x", padx=15, pady=5)

        # Load current config from backend
        try:
            resp = requests.get("http://localhost:8000/api/config/model")
            if resp.ok:
                cfg = resp.json()
                self.model_var.set(cfg.get("provider", "local"))
        except Exception as e:
            print(f"Failed to load LLM config: {e}")

        # Save button
        save_btn = ctk.CTkButton(frame, text="保存配置", command=self._save_model_config)
        save_btn.pack(pady=10)

    def _save_model_config(self):
        provider = self.model_var.get()
        payload = {"provider": provider}
        if provider == "gemini":
            key = simpledialog.askstring("Gemini API Key", "请输入 Gemini API Key:")
            if not key:
                messagebox.showerror("错误", "Gemini API Key 不能为空")
                return
            payload["gemini_api_key"] = key
        elif provider == "openai":
            key = simpledialog.askstring("OpenAI API Key", "请输入 OpenAI API Key:")
            if not key:
                messagebox.showerror("错误", "OpenAI API Key 不能为空")
                return
            payload["openai_api_key"] = key
        try:
            resp = requests.post("http://localhost:8000/api/config/model", json=payload)
            if resp.ok:
                messagebox.showinfo("成功", "模型配置已保存，系统将自动重启后端")
                # Optional: trigger backend restart endpoint if exists
                try:
                    requests.post("http://localhost:8000/api/restart")
                except Exception:
                    pass
            else:
                messagebox.showerror("错误", f"保存失败: {resp.text}")
        except Exception as e:
            messagebox.showerror("错误", f"请求失败: {e}")

    def _on_speed_change(self, value):
        modes = ["silent", "balanced", "performance"]
        mode_key = modes[int(value)]
        
        result = traffic_crtl.set_mode(mode_key)
        mode_info = result["mode"]
        
        self.speed_label.configure(
            text=f"{mode_info['name']} ({mode_info['upload_rate_limit']})"
        )

    def _on_click_import(self):
        """Handle Import Folder Button"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择要引入的文件夹 (Select Folder)")
        if path:
            self._on_click_scan(path)
            
    def _on_click_scan(self, path):
        """Handle Scan/Refresh"""
        # We need a status indicator. For now print to console or pop up
        # Import scanner/dialogs locally to avoid circular imports if any
        from launcher.services.scanner import scanner
        from launcher.ui.dialogs import ScanResultDialog
        import threading
        
        print(f"Scanning: {path}")
        
        def _run_scan():
            result = scanner.scan_directory(path)
            return result
            
        def _on_done(result):
            if result["status"] == "success":
                # Show Confirmation Dialog
                ScanResultDialog(self, result, on_confirm=lambda: self._start_processing(path, result))
                
                # Add to topology if not already there (simple check)
                exists = any(n["path"] == path for n in self.topology.nas_nodes)
                if not exists:
                     self.topology.add_nas_node(path, "online", f"{result['total_files']} Files")
            else:
                print(f"Scan failed: {result.get('message')}")
 
        threading.Thread(target=lambda: _on_done(_run_scan())).start()

    def _start_processing(self, path, scan_stats):
        print(f"STARTING PROCESSING FOR {path}")
        # MVP: Just log it. Real app calls API.

