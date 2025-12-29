# -*- coding: utf-8 -*-
"""
Pervis PRO 一键启动器
- 进程内嵌管理，关闭启动器自动终止所有服务
- 不开额外 CMD 窗口
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os
import socket
import webbrowser
import time
import atexit
from pathlib import Path

class PervisLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pervis PRO 启动器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.base_dir = Path(__file__).parent.absolute()
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        
        # 虚拟环境 Python 路径
        venv_python = self.backend_dir / "venv" / "Scripts" / "python.exe"
        self.python_cmd = str(venv_python) if venv_python.exists() else "py"
        
        # 配置 FFmpeg 路径
        self._setup_ffmpeg_path()
        
        # 子进程列表
        self.processes = []
        
        # 注册退出清理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.cleanup)
        
        self.setup_ui()
        self.check_status()
    
    def _setup_ffmpeg_path(self):
        """配置 FFmpeg 路径到环境变量"""
        ffmpeg_paths = [
            r"C:\ffmpeg\bin",
            r"C:\Program Files\ffmpeg\bin",
            r"C:\Program Files (x86)\ffmpeg\bin",
        ]
        
        current_path = os.environ.get("PATH", "")
        
        for ffmpeg_dir in ffmpeg_paths:
            ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                if ffmpeg_dir not in current_path:
                    os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
                    print(f"[FFmpeg] 已添加到 PATH: {ffmpeg_dir}")
                self.ffmpeg_path = ffmpeg_exe
                return
        
        self.ffmpeg_path = None
        
    def setup_ui(self):
        # 标题
        tk.Label(self.root, text="🎬 Pervis PRO 启动器", font=("微软雅黑", 18, "bold"), 
                 fg="#eee", bg="#1a1a2e", height=2).pack(fill=tk.X)
        
        main = tk.Frame(self.root, padx=20, pady=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # 状态区
        status_frame = tk.LabelFrame(main, text="服务状态", font=("微软雅黑", 10))
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        for name, port in [("Ollama AI", 11434), ("Director API", 8000), ("DAM 服务", 8001), ("Web 前端", 3000)]:
            row = tk.Frame(status_frame)
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=f"{name}:", font=("微软雅黑", 10), width=12, anchor='w').pack(side=tk.LEFT)
            label = tk.Label(row, text="● 未运行", fg="gray", font=("微软雅黑", 10))
            label.pack(side=tk.LEFT, padx=10)
            tk.Label(row, text=f":{port}", fg="#888", font=("Consolas", 9)).pack(side=tk.RIGHT)
            setattr(self, f"status_{port}", label)
        
        # 按钮
        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="🚀 一键启动", font=("微软雅黑", 14, "bold"), bg="#27ae60", fg="white",
                  height=2, command=self.start_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="⏹ 停止全部", font=("微软雅黑", 14), bg="#c0392b", fg="white",
                  height=2, command=self.stop_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # 快捷按钮
        quick = tk.Frame(main)
        quick.pack(fill=tk.X, pady=(0, 10))
        tk.Button(quick, text="🌐 打开界面", bg="#3498db", fg="white",
                  command=lambda: webbrowser.open("http://localhost:3000")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(quick, text="📚 API文档", bg="#9b59b6", fg="white",
                  command=lambda: webbrowser.open("http://localhost:8000/docs")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # 日志
        log_frame = tk.LabelFrame(main, text="运行日志", font=("微软雅黑", 10))
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#ddd")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def log(self, msg):
        self.root.after(0, lambda: (self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n"), self.log_text.see(tk.END)))
        
    def check_port(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    
    def check_status(self):
        for port in [11434, 8000, 8001, 3000]:
            label = getattr(self, f"status_{port}")
            if self.check_port(port):
                label.config(text="● 运行中", fg="#27ae60")
            else:
                label.config(text="● 未运行", fg="gray")
        self.root.after(3000, self.check_status)
    
    def start_process(self, name, cmd, cwd, shell=False):
        """启动子进程（无窗口）"""
        try:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
                                 encoding='utf-8', errors='replace', shell=shell)
            self.processes.append(p)
            self.log(f"✓ {name} 已启动 (PID: {p.pid})")
            # 后台读取日志
            threading.Thread(target=self._read_log, args=(name, p), daemon=True).start()
            return True
        except Exception as e:
            self.log(f"✗ {name} 启动失败: {e}")
            return False
    
    def _read_log(self, name, process):
        """读取进程日志"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.log(f"[{name}] {line.strip()}")
        except: pass
    
    def start_ollama(self):
        """启动 Ollama"""
        if self.check_port(11434):
            self.log("✓ Ollama 已在运行")
            return True
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            self.log("✗ Ollama 未安装，请访问 https://ollama.ai 安装")
            return False
        
        self.log("正在启动 Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        for _ in range(10):
            time.sleep(1)
            if self.check_port(11434):
                self.log("✓ Ollama 启动成功")
                return True
        self.log("⚠ Ollama 启动超时")
        return False
    
    def start_all(self):
        self.log("=" * 40)
        self.log("🚀 开始启动 Pervis PRO...")
        
        def run():
            # 1. Ollama
            self.start_ollama()
            time.sleep(1)
            
            # 2. DAM
            if not self.check_port(8001) and (self.backend_dir / "dam_main.py").exists():
                self.start_process("DAM", [self.python_cmd, "dam_main.py"], str(self.backend_dir))
            time.sleep(1)
            
            # 3. Director API
            if not self.check_port(8000):
                self.start_process("Director", [self.python_cmd, "director_main.py"], str(self.backend_dir))
            time.sleep(2)
            
            # 4. Frontend (Windows 需要用 npm.cmd)
            if not self.check_port(3000):
                if not (self.frontend_dir / "node_modules").exists():
                    self.log("首次运行，安装前端依赖...")
                    subprocess.run(["npm.cmd", "install"], cwd=str(self.frontend_dir), 
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
                self.start_process("Frontend", ["npm.cmd", "run", "dev"], str(self.frontend_dir), shell=True)
            
            # 等待前端启动后打开浏览器
            time.sleep(5)
            for _ in range(10):
                if self.check_port(3000):
                    self.log("正在打开浏览器...")
                    webbrowser.open("http://localhost:3000")
                    break
                time.sleep(1)
            
            self.log("✓ 启动完成")
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_all(self):
        if not messagebox.askyesno("确认", "确定停止所有服务？"):
            return
        self.log("正在停止所有服务...")
        self.cleanup()
        self.log("✓ 已停止")
    
    def cleanup(self):
        """清理所有子进程"""
        for p in self.processes:
            if p.poll() is None:
                try:
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)], 
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except: pass
        self.processes.clear()
        # 清理端口占用
        for port in [8000, 8001, 3000]:
            os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port} ^| findstr LISTENING\') do taskkill /F /PID %a 2>nul')
    
    def on_closing(self):
        if messagebox.askyesno("退出", "关闭启动器将停止所有服务，确定退出？"):
            self.cleanup()
            self.root.destroy()
    
    def run(self):
        self.log("Pervis PRO 启动器就绪")
        self.log(f"Python: {self.python_cmd}")
        self.log(f"Backend: {self.backend_dir}")
        self.log(f"Frontend: {self.frontend_dir}")
        if self.ffmpeg_path:
            self.log(f"FFmpeg: {self.ffmpeg_path} ✓")
        else:
            self.log("FFmpeg: 未检测到 (视频导出功能受限)")
        self.root.mainloop()

if __name__ == "__main__":
    PervisLauncher().run()
