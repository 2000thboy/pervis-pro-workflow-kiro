import subprocess
import threading
import queue
import os
import sys
import webbrowser
import time

class ProcessManager:
    """
    负责管理后端和前端子进程，并捕获日志
    """
    def __init__(self, log_callback=None):
        self.dam_process = None
        self.backend_process = None
        self.frontend_process = None
        self.log_callback = log_callback
        self.is_running = False
        
    def log(self, source, message):
        """发送日志到UI"""
        if self.log_callback:
            timestamp = time.strftime("%H:%M:%S")
            self.log_callback(f"[{timestamp}] [{source}] {message}")
        print(f"[{source}] {message}")

    def start_all(self):
        """启动所有服务"""
        if self.is_running:
            self.log("SYS", "服务已在运行中...")
            return

        self.is_running = True
        self.log("SYS", "正在启动 Pervis PRO 服务...")

        threading.Thread(target=self._run_dam_backend, daemon=True).start()

        # 1. 启动后端 (Backend)
        threading.Thread(target=self._run_backend, daemon=True).start()
        
        # 2. 启动前端 (Frontend)
        threading.Thread(target=self._run_frontend, daemon=True).start()
        
        # 3. 延时打开浏览器
        threading.Thread(target=self._open_browser_delayed, daemon=True).start()

    def _run_backend(self):
        self.log("BACKEND", "正在启动 API Server (uvicorn)...")
        # Assuming we are in root, backend is in ./backend
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        backend_dir = os.path.join(root_dir, "backend")
        
        cmd = [sys.executable, "director_main.py"]
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace' # 防止中文乱码崩溃
            )
            
            # 实时读取日志
            for line in self.backend_process.stdout:
                self.log("API", line.strip())
                
        except Exception as e:
            self.log("BACKEND_ERR", str(e))
            self.is_running = False

    def _run_dam_backend(self):
        self.log("DAM", "正在启动 DAM API Server (uvicorn)...")
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        backend_dir = os.path.join(root_dir, "backend")

        cmd = [sys.executable, "dam_main.py"]

        try:
            self.dam_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )

            for line in self.dam_process.stdout:
                self.log("DAM_API", line.strip())

        except Exception as e:
            self.log("DAM_ERR", str(e))

    def _run_frontend(self):
        self.log("FRONTEND", "正在启动 Web Server (vite)...")
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        frontend_dir = os.path.join(root_dir, "frontend")
        
        # Check if node_modules exists
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            self.log("FRONTEND", "未检测到 node_modules，正在执行 npm install (可能需要几分钟)...")
            try:
                subprocess.check_call(["npm", "install"], cwd=frontend_dir, shell=True)
                self.log("FRONTEND", "依赖安装完成！")
            except Exception as e:
                self.log("FRONTEND_ERR", f"npm install 失败: {e}")
                return

        # shell=True for npm on windows
        cmd = "npm run dev" 
        
        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in self.frontend_process.stdout:
                # Filter spammy vite logs if needed
                self.log("WEB", line.strip())
                
        except Exception as e:
            self.log("FRONTEND_ERR", str(e))
            self.is_running = False

    def _open_browser_delayed(self):
        self.log("SYS", "等待服务就绪 (5秒)...")
        time.sleep(5)
        url = "http://localhost:3001" # Fixed: Vite now uses 3001
        self.log("SYS", f"正在打开浏览器: {url}")
        webbrowser.open(url)

    def restart_all(self):
        """重启所有服务"""
        self.log("SYS", "正在执行重启操作...")
        self.stop_all()
        # Give it a moment to release ports
        time.sleep(2)
        self.start_all()

    def stop_all(self):
        """停止服务"""
        self.is_running = False
        if self.dam_process:
            self.log("SYS", "停止DAM服务...")
            self.dam_process.terminate()
            self.dam_process = None
        if self.backend_process:
            self.log("SYS", "停止后端服务...")
            self.backend_process.terminate()
            self.backend_process = None # Clear reference
            
        if self.frontend_process:
            self.log("SYS", "停止前端服务...")
            # Windows kill process tree for shell=True
            try:
                subprocess.run(f"taskkill /F /T /PID {self.frontend_process.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
            self.frontend_process = None # Clear reference
        
        self.log("SYS", "所有服务已停止。")
            
process_manager = ProcessManager()
