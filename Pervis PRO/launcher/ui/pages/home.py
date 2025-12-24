import customtkinter as ctk
from launcher.services.process_manager import process_manager
from launcher.services.detector import detector
import threading
import os
import subprocess

class HomePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Main content center
        
        # 1. Hero / Header Section
        self._create_hero_section()
        
        # 2. Main Action Area (Folders & Info)
        self._create_info_area()
        
        # 3. Bottom Action Bar (One-Click Start)
        self._create_action_bar()
        
        # Auto-update status
        self.after(1000, self._update_status)

    def _create_hero_section(self):
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="ew", padx=40, pady=(20, 10))
        
        title = ctk.CTkLabel(hero, text="PERVIS PRO", font=("Impact", 42), text_color="#3498DB")
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(hero, text="AI-Powered Previsualization Assistant", font=("Roboto", 14), text_color="gray")
        subtitle.pack(anchor="w")

    def _create_info_area(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        
        # Left: Folders Quick Access
        ctk.CTkLabel(container, text="文件夹 (Quick Access)", font=("Roboto Medium", 16)).pack(anchor="w", pady=(0, 10))
        
        folders_grid = ctk.CTkFrame(container, fg_color="transparent")
        folders_grid.pack(fill="x", anchor="w")
        
        self._add_folder_btn(folders_grid, "📂 根目录", ".", 0, 0)
        self._add_folder_btn(folders_grid, "🎞️ 导入素材 (Input)", "L:\\PreVis_Assets\\originals", 0, 1)
        self._add_folder_btn(folders_grid, "🎬 渲染输出 (Output)", "L:\\PreVis_Storage\\renders", 0, 2)
        
        # Right: Announcements/Logs (Placeholder)
        # Using simple label for now mimicking the reference text area
        self.info_box = ctk.CTkTextbox(container, height=150, fg_color="#2B2B2B")
        self.info_box.pack(fill="x", pady=(30, 0))
        self.info_box.insert("1.0", "公告:\n• 欢迎使用 Pervis PRO 全新启动器\n• 请确保 L: 盘符已正确挂载\n• 如遇启动失败，请查看'控制台'页签")
        self.info_box.configure(state="disabled")

    def _add_folder_btn(self, parent, text, path, r, c):
        btn = ctk.CTkButton(
            parent, 
            text=text, 
            height=60,
            fg_color="#34495E", 
            hover_color="#2C3E50",
            command=lambda: self._open_path(path)
        )
        btn.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
        # parent.grid_columnconfigure(c, weight=1) # Distribute

    def _create_action_bar(self):
        bar = ctk.CTkFrame(self, height=100, fg_color="#1F1F1F") # Darker footer
        bar.grid(row=2, column=0, sticky="ew")
        
        # System Health
        self.health_label = ctk.CTkLabel(bar, text="● System Ready", font=("Roboto", 14), text_color="#2ECC71")
        self.health_label.pack(side="left", padx=40)
        
        # BIG START BUTTON
        self.start_btn = ctk.CTkButton(
            bar, 
            text="▶ 一键启动", 
            font=("Roboto Black", 24),
            width=200, 
            height=60, 
            corner_radius=30,
            fg_color="#3498DB", 
            hover_color="#2980B9",
            command=self._on_start_click
        )
        self.start_btn.pack(side="right", padx=40, pady=20)

    def _open_path(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            print(f"Failed to open {path}: {e}")

    def _on_start_click(self):
        self.start_btn.configure(state="disabled", text="启动中...", fg_color="#E67E22")
        process_manager.start_all()
        # Ensure console switches? Or just let user switch.

    def _update_status(self):
        # Run detailed check in thread to avoid freezing UI
        def _check():
            try:
                # We need a synchronous wrapper if detector is async
                # actually check_core_services is async. 
                # We can use asyncio.run or just manual socket check for speed in UI loop
                # Re-using detector's logic but synchronously for simple UI polling
                
                import socket
                def check_port(port):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.2)
                        return s.connect_ex(('127.0.0.1', port)) == 0

                api_ok = check_port(8000)
                dam_ok = check_port(8001)
                web_ok = check_port(3001) # Vite default is 3001 now
                # Note: Vite default is 5173 usually! Launcher defaults might need adjustment?
                # ProcessManager said 'npm run dev', typically 5173. 
                # Detector says 3000. Let's check 5173 as fallback.
                if not web_ok: web_ok = check_port(5173)
                if not web_ok: web_ok = check_port(3000) # Legacy fallback
                
                return api_ok, dam_ok, web_ok
            except:
                return False, False

        def _update_label(result):
             api, dam, web = result
             
             status_text = []
             if api: status_text.append("API ✓")
             else: status_text.append("API ✗")

             if dam: status_text.append("DAM ✓")
             else: status_text.append("DAM ✗")
             
             if web: status_text.append("Web ✓")
             else: status_text.append("Web ✗")
             
             full_text = " | ".join(status_text)
             
             if api and dam and web:
                 self.health_label.configure(text=f"● 正常运行 ({full_text})", text_color="#2ECC71")
                 # Only if process manager thinks it's running do we say "Running" on button
                 if process_manager.is_running:
                      self.start_btn.configure(state="disabled", text="运行中", fg_color="#27AE60")
                 else:
                      # Services are running externally (manual start)
                      self.health_label.configure(text=f"● 检测到外部服务 ({full_text})", text_color="#3498DB")
                      self.start_btn.configure(state="normal", text="▶ 一键启动", fg_color="#3498DB")
                      process_manager.is_running = False
                      
             elif process_manager.is_running:
                 # Process started but ports not ready yet
                 self.health_label.configure(text=f"● 启动中... ({full_text})", text_color="#F1C40F")
             else:
                 # FIX: When not running and ports closed, re-enable the button
                 self.health_label.configure(text=f"● 系统就绪 ({full_text})", text_color="gray")
                 self.start_btn.configure(state="normal", text="▶ 一键启动", fg_color="#3498DB")

        def _run_background_check():
            res = _check()
            # Schedule UI update on main thread
            self.after(0, lambda: _update_label(res))

        threading.Thread(target=_run_background_check).start()
        
        # Poll every 3 seconds
        self.after(3000, self._update_status)

