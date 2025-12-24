import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from .storage_panel import StorageTopologyPanel
from .dialogs import ScanResultDialog
from ..services.traffic_control import traffic_crtl
from ..services.detector import detector
from ..services.scanner import scanner
import threading
import time
import asyncio

class DashboardApp(ctk.CTk):
    """
    Pervis PRO 控制中心主界面
    """
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Pervis PRO Control Center")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=3) # Storage Panel (Left & Center)
        self.grid_columnconfigure(1, weight=1) # Control Panel (Right)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Main Content
        self.grid_rowconfigure(2, weight=0) # AI Monitor
        
        # Components
        self._create_header()
        self._create_storage_panel()
        self._create_control_panel()
        self._create_ai_monitor()
        
        # Run detection in background
        self.after(500, self.run_system_detection)

    def _create_header(self):
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        title = ctk.CTkLabel(self.header_frame, text="PERVIS PRO", font=("Roboto Black", 24))
        title.pack(side="left", padx=20, pady=10)
        
        self.status_indicator = ctk.CTkLabel(self.header_frame, text="● 系统启动中...", text_color="yellow", font=("Roboto Medium", 12))
        self.status_indicator.pack(side="right", padx=20)

    def _create_storage_panel(self):
        self.storage_frame = ctk.CTkFrame(self, corner_radius=10)
        self.storage_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.storage_frame, text="存储拓扑", font=("Roboto Medium", 14), text_color="gray").pack(anchor="w", padx=15, pady=10)
        
        # Embed the StorageTopologyPanel
        self.topology_panel = StorageTopologyPanel(
            self.storage_frame,
            on_import_click=self._on_click_import,
            on_scan_click=self._on_click_scan
        )
        self.topology_panel.pack(expand=True, fill="both", padx=5, pady=5)

    def _create_control_panel(self):
        self.control_frame = ctk.CTkFrame(self, corner_radius=10)
        self.control_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.control_frame, text="控制面板", font=("Roboto Medium", 14), text_color="gray").pack(anchor="w", padx=15, pady=10)
        
        # Services Toggles
        self._add_switch(self.control_frame, "后端 API", True)
        self._add_switch(self.control_frame, "Web 前端", True)
        self._add_switch(self.control_frame, "AI 自动标签", True)
        
        ctk.CTkLabel(self.control_frame, text="处理速度", font=("Roboto Medium", 12)).pack(anchor="w", padx=15, pady=(20, 5))
        
        # Traffic Slider
        self.speed_slider = ctk.CTkSlider(self.control_frame, from_=0, to=2, number_of_steps=2, command=self._on_speed_change)
        self.speed_slider.set(1) # Balanced
        self.speed_slider.pack(padx=15, pady=5, fill="x")
        
        self.speed_label = ctk.CTkLabel(self.control_frame, text="平衡模式", text_color="#3498DB")
        self.speed_label.pack(pady=0)
        
    def _create_ai_monitor(self):
        self.monitor_frame = ctk.CTkFrame(self, height=150, corner_radius=10)
        self.monitor_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.monitor_frame, text="AI 吞吐量监控", font=("Roboto Medium", 12), text_color="gray").pack(anchor="w", padx=15, pady=5)
        
        # Mock Viz
        self.viz_canvas = tk.Canvas(self.monitor_frame, height=100, bg="#2B2B2B", highlightthickness=0)
        self.viz_canvas.pack(fill="x", padx=10, pady=5)
        self.viz_canvas.create_text(200, 50, text="[AI WAVEFORM VISUALIZATION PLACEHOLDER]", fill="gray")

    def _add_switch(self, parent, text, default=False):
        switch = ctk.CTkSwitch(parent, text=text)
        if default: switch.select()
        switch.pack(padx=15, pady=10, anchor="w")
        return switch

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
        path = filedialog.askdirectory(title="选择要引入的文件夹")
        if path:
            print(f"User selected: {path}")
            # Immediately trigger scan
            self._on_click_scan(path)
            
    def _on_click_scan(self, path):
        """Handle Scan/Refresh"""
        # Show loading or status?
        self.status_indicator.configure(text=f"● 正在扫描: {path}...", text_color="yellow")
        
        def _run_scan():
            result = scanner.scan_directory(path)
            return result
            
        def _on_done(result):
            self.status_indicator.configure(text="● 系统在线 (正常)", text_color="#2ECC71")
            
            if result["status"] == "success":
                # Show Confirmation Dialog
                ScanResultDialog(self, result, on_confirm=lambda: self._start_processing(path, result))
                
                # Add to topology if not already there (simple check)
                exists = any(n["path"] == path for n in self.topology_panel.nas_nodes)
                if not exists:
                     self.topology_panel.add_nas_node(path, "online", f"{result['total_files']} Files")
            else:
                print(f"Scan failed: {result.get('message')}")

        threading.Thread(target=lambda: _on_done(_run_scan())).start()

    def _start_processing(self, path, scan_stats):
        """User confirmed processing"""
        print(f"STARTING PROCESSING FOR {path}")
        # Here we would call the backend API to kick off the job
        # For now, just update status
        self.status_indicator.configure(text=f"● 处理中: {scan_stats['new_files']} 个新文件...", text_color="#3498DB")
        
        # Determine mode
        mode = traffic_crtl.get_current_metrics()
        print(f"Using Mode: {mode['name']}")

    def run_system_detection(self):
        """运行后台检测并在完成后更新UI"""
        def _scan():
            result = asyncio.run(detector.run_full_scan())
            return result
            
        def _update_ui(result):
            # Update Header
            health = result["overall_health"]
            color = "#2ECC71" if health == "healthy" or health == "healthy" else "#E74C3C" 
            # Translate health status
            health_cn = "正常" if health == "healthy" else "异常"
            self.status_indicator.configure(text=f"● 系统在线 ({health_cn})", text_color=color)
            
            # Update Topology
            nas_devices = result["checks"]["network"]["nas_devices"]
            # Clear existing logic needed? for now just demonstration
            # In real app, we'd sync self.topology_panel.nas_nodes with nas_devices
            
        threading.Thread(target=lambda: _update_ui(_scan())).start()

if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
