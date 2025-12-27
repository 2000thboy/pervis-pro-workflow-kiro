# -*- coding: utf-8 -*-
"""
Pervis PRO 一键启动器
简单易用的图形界面，适合程序小白
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import socket
import webbrowser
import time
from pathlib import Path

class PervisLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pervis PRO 启动器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 获取脚本所在目录
        self.base_dir = Path(__file__).parent.absolute()
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        
        # 进程引用
        self.dam_process = None
        self.backend_process = None
        self.frontend_process = None
        
        self.setup_ui()
        self.check_status()
        
    def setup_ui(self):
        """设置界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg="#1a1a2e", height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎬 Pervis PRO 启动器", 
            font=("微软雅黑", 18, "bold"),
            fg="#eee",
            bg="#1a1a2e"
        )
        title_label.pack(expand=True)
        
        # 主内容区
        main_frame = tk.Frame(self.root, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态显示区
        status_frame = tk.LabelFrame(main_frame, text="服务状态", font=("微软雅黑", 10))
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # DAM 后端状态
        dam_row = tk.Frame(status_frame)
        dam_row.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(dam_row, text="DAM 素材服务:", font=("微软雅黑", 10), width=15, anchor='w').pack(side=tk.LEFT)
        self.dam_status = tk.Label(dam_row, text="● 未运行", fg="gray", font=("微软雅黑", 10))
        self.dam_status.pack(side=tk.LEFT, padx=10)
        tk.Label(dam_row, text="端口 8001", fg="#888", font=("微软雅黑", 9)).pack(side=tk.RIGHT)
        
        # Director 后端状态
        backend_row = tk.Frame(status_frame)
        backend_row.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(backend_row, text="Director API:", font=("微软雅黑", 10), width=15, anchor='w').pack(side=tk.LEFT)
        self.backend_status = tk.Label(backend_row, text="● 未运行", fg="gray", font=("微软雅黑", 10))
        self.backend_status.pack(side=tk.LEFT, padx=10)
        tk.Label(backend_row, text="端口 8000", fg="#888", font=("微软雅黑", 9)).pack(side=tk.RIGHT)
        
        # 前端状态
        frontend_row = tk.Frame(status_frame)
        frontend_row.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(frontend_row, text="Web 前端:", font=("微软雅黑", 10), width=15, anchor='w').pack(side=tk.LEFT)
        self.frontend_status = tk.Label(frontend_row, text="● 未运行", fg="gray", font=("微软雅黑", 10))
        self.frontend_status.pack(side=tk.LEFT, padx=10)
        tk.Label(frontend_row, text="端口 3001", fg="#888", font=("微软雅黑", 9)).pack(side=tk.RIGHT)
        
        # 一键启动按钮
        self.start_all_btn = tk.Button(
            main_frame,
            text="🚀 一键启动全部服务",
            font=("微软雅黑", 14, "bold"),
            bg="#e94560",
            fg="white",
            activebackground="#ff6b6b",
            activeforeground="white",
            height=2,
            cursor="hand2",
            command=self.start_all
        )
        self.start_all_btn.pack(fill=tk.X, pady=(5, 10))
        
        # 控制按钮行
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹ 停止全部",
            font=("微软雅黑", 10),
            bg="#c0392b",
            fg="white",
            width=15,
            cursor="hand2",
            command=self.stop_all
        )
        self.stop_btn.pack(side=tk.LEFT, expand=True, padx=5)
        
        self.open_btn = tk.Button(
            control_frame,
            text="🌐 打开界面",
            font=("微软雅黑", 10),
            bg="#3498db",
            fg="white",
            width=15,
            cursor="hand2",
            command=lambda: webbrowser.open("http://localhost:3001")
        )
        self.open_btn.pack(side=tk.LEFT, expand=True, padx=5)
        
        self.api_btn = tk.Button(
            control_frame,
            text="📚 API文档",
            font=("微软雅黑", 10),
            bg="#9b59b6",
            fg="white",
            width=15,
            cursor="hand2",
            command=lambda: webbrowser.open("http://localhost:8000/docs")
        )
        self.api_btn.pack(side=tk.LEFT, expand=True, padx=5)
        
        # 日志区域
        log_frame = tk.LabelFrame(main_frame, text="运行日志", font=("微软雅黑", 10))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ddd",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部提示
        tip_label = tk.Label(
            self.root,
            text="提示: 首次启动可能需要等待依赖安装，请耐心等待",
            font=("微软雅黑", 9),
            fg="gray"
        )
        tip_label.pack(pady=5)
        
    def log(self, message, tag=None):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def check_port(self, port):
        """检查端口是否被占用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    
    def check_status(self):
        """检查服务状态"""
        # 检查 DAM
        if self.check_port(8001):
            self.dam_status.config(text="● 运行中", fg="#27ae60")
        else:
            self.dam_status.config(text="● 未运行", fg="gray")
            
        # 检查后端
        if self.check_port(8000):
            self.backend_status.config(text="● 运行中", fg="#27ae60")
        else:
            self.backend_status.config(text="● 未运行", fg="gray")
            
        # 检查前端
        if self.check_port(3001):
            self.frontend_status.config(text="● 运行中", fg="#27ae60")
        else:
            self.frontend_status.config(text="● 未运行", fg="gray")
            
        # 每3秒检查一次
        self.root.after(3000, self.check_status)
        
    def start_dam(self):
        """启动 DAM 服务"""
        if self.check_port(8001):
            self.log("DAM 服务已在运行")
            return
            
        self.log("正在启动 DAM 素材服务...")
        
        def run():
            try:
                dam_main = self.backend_dir / "dam_main.py"
                if not dam_main.exists():
                    self.root.after(0, lambda: self.log("⚠ dam_main.py 不存在，跳过 DAM 服务"))
                    return
                    
                cmd = f'start "DAM服务-8001" cmd /k "cd /d {self.backend_dir} && py dam_main.py"'
                subprocess.Popen(cmd, shell=True)
                self.root.after(0, lambda: self.log("✓ DAM 服务启动命令已发送"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ DAM 启动失败: {e}"))
                
        threading.Thread(target=run, daemon=True).start()
        
    def start_backend(self):
        """启动 Director 后端"""
        if self.check_port(8000):
            self.log("Director API 已在运行")
            return
            
        self.log("正在启动 Director API 服务...")
        
        def run():
            try:
                cmd = f'start "Director-API-8000" cmd /k "cd /d {self.backend_dir} && py director_main.py"'
                subprocess.Popen(cmd, shell=True)
                self.root.after(0, lambda: self.log("✓ Director API 启动命令已发送"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ Director 启动失败: {e}"))
                
        threading.Thread(target=run, daemon=True).start()
        
    def start_frontend(self):
        """启动前端"""
        if self.check_port(3001):
            self.log("前端服务已在运行")
            return
            
        self.log("正在启动前端服务...")
        
        node_modules = self.frontend_dir / "node_modules"
        
        def run():
            try:
                if not node_modules.exists():
                    self.root.after(0, lambda: self.log("首次运行，正在安装前端依赖（可能需要几分钟）..."))
                    cmd = f'start "前端-3001" cmd /k "cd /d {self.frontend_dir} && npm install && npm run dev"'
                else:
                    cmd = f'start "前端-3001" cmd /k "cd /d {self.frontend_dir} && npm run dev"'
                subprocess.Popen(cmd, shell=True)
                self.root.after(0, lambda: self.log("✓ 前端服务启动命令已发送"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ 前端启动失败: {e}"))
                
        threading.Thread(target=run, daemon=True).start()
        
    def start_all(self):
        """一键启动全部"""
        self.log("=" * 50)
        self.log("🚀 开始启动 Pervis PRO 全部服务...")
        self.log("=" * 50)
        
        # 1. 启动 DAM
        self.start_dam()
        
        # 2. 等待1秒后启动 Director
        def start_director():
            time.sleep(1)
            self.root.after(0, self.start_backend)
            
        threading.Thread(target=start_director, daemon=True).start()
        
        # 3. 等待2秒后启动前端
        def start_frontend_delayed():
            time.sleep(2)
            self.root.after(0, self.start_frontend)
            
            # 8秒后自动打开浏览器
            time.sleep(8)
            self.root.after(0, lambda: self.log("正在打开浏览器..."))
            webbrowser.open("http://localhost:3001")
            
        threading.Thread(target=start_frontend_delayed, daemon=True).start()
        
    def stop_all(self):
        """停止全部服务"""
        if messagebox.askyesno("确认", "确定要停止所有服务吗？"):
            self.log("正在停止所有服务...")
            try:
                # 杀死占用端口的进程
                os.system('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :8001 ^| findstr LISTENING\') do taskkill /F /PID %a 2>nul')
                os.system('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :8000 ^| findstr LISTENING\') do taskkill /F /PID %a 2>nul')
                os.system('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :3001 ^| findstr LISTENING\') do taskkill /F /PID %a 2>nul')
                self.log("✓ 停止命令已发送")
            except Exception as e:
                self.log(f"✗ 停止失败: {e}")
                
    def run(self):
        """运行启动器"""
        self.log("Pervis PRO 启动器已就绪")
        self.log("点击「一键启动全部服务」开始")
        self.root.mainloop()


if __name__ == "__main__":
    app = PervisLauncher()
    app.run()
