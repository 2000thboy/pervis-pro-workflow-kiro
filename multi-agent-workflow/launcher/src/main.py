"""
桌面启动器主程序
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import requests
import time
import psutil
from typing import Optional
import structlog

# 配置日志
logger = structlog.get_logger(__name__)

# 设置外观模式和颜色主题
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class MultiAgentLauncher:
    """多Agent系统启动器"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("多Agent协作工作流系统启动器")
        self.root.geometry("800x600")
        
        # 系统状态
        self.backend_status = "未连接"
        self.frontend_status = "未连接"
        self.agents_status = {}
        
        # 创建界面
        self.create_widgets()
        
        # 启动状态监控
        self.start_monitoring()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 主标题
        title_label = ctk.CTkLabel(
            self.root,
            text="多Agent协作工作流系统",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # 系统状态框架
        status_frame = ctk.CTkFrame(self.root)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="系统状态",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        status_title.pack(pady=10)
        
        # 后端状态
        self.backend_status_label = ctk.CTkLabel(
            status_frame,
            text=f"后端服务: {self.backend_status}",
            font=ctk.CTkFont(size=14)
        )
        self.backend_status_label.pack(pady=5)
        
        # 前端状态
        self.frontend_status_label = ctk.CTkLabel(
            status_frame,
            text=f"前端界面: {self.frontend_status}",
            font=ctk.CTkFont(size=14)
        )
        self.frontend_status_label.pack(pady=5)
        
        # Agent状态
        self.agents_frame = ctk.CTkFrame(status_frame)
        self.agents_frame.pack(pady=10, padx=10, fill="x")
        
        agents_title = ctk.CTkLabel(
            self.agents_frame,
            text="Agent状态",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        agents_title.pack(pady=5)
        
        # 控制按钮框架
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=20, padx=20, fill="x")
        
        control_title = ctk.CTkLabel(
            control_frame,
            text="系统控制",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        control_title.pack(pady=10)
        
        # 按钮容器
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(pady=10, padx=10, fill="x")
        
        # 启动后端按钮
        self.start_backend_btn = ctk.CTkButton(
            button_frame,
            text="启动后端服务",
            command=self.start_backend,
            width=150
        )
        self.start_backend_btn.pack(side="left", padx=10, pady=10)
        
        # 启动前端按钮
        self.start_frontend_btn = ctk.CTkButton(
            button_frame,
            text="启动前端界面",
            command=self.start_frontend,
            width=150
        )
        self.start_frontend_btn.pack(side="left", padx=10, pady=10)
        
        # 打开Web界面按钮
        self.open_web_btn = ctk.CTkButton(
            button_frame,
            text="打开Web界面",
            command=self.open_web_interface,
            width=150
        )
        self.open_web_btn.pack(side="left", padx=10, pady=10)
        
        # 日志框架
        log_frame = ctk.CTkFrame(self.root)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="系统日志",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.pack(pady=5)
        
        # 日志文本框
        self.log_textbox = ctk.CTkTextbox(log_frame, height=200)
        self.log_textbox.pack(pady=5, padx=10, fill="both", expand=True)
        
        # 添加初始日志
        self.add_log("系统启动器已启动")
    
    def add_log(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_textbox.insert("end", log_message)
        self.log_textbox.see("end")
        logger.info(message)
    
    def check_backend_status(self) -> bool:
        """检查后端服务状态"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_frontend_status(self) -> bool:
        """检查前端服务状态"""
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def update_status(self):
        """更新系统状态"""
        # 检查后端状态
        if self.check_backend_status():
            self.backend_status = "运行中"
            self.backend_status_label.configure(text=f"后端服务: {self.backend_status}")
        else:
            self.backend_status = "未连接"
            self.backend_status_label.configure(text=f"后端服务: {self.backend_status}")
        
        # 检查前端状态
        if self.check_frontend_status():
            self.frontend_status = "运行中"
            self.frontend_status_label.configure(text=f"前端界面: {self.frontend_status}")
        else:
            self.frontend_status = "未连接"
            self.frontend_status_label.configure(text=f"前端界面: {self.frontend_status}")
    
    def start_monitoring(self):
        """启动状态监控"""
        def monitor():
            while True:
                try:
                    self.update_status()
                    time.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    logger.error(f"状态监控错误: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def start_backend(self):
        """启动后端服务"""
        def run_backend():
            try:
                self.add_log("正在启动后端服务...")
                # 这里应该启动后端服务
                # 暂时显示提示信息
                self.add_log("请手动启动后端服务: cd backend && python main.py")
            except Exception as e:
                self.add_log(f"启动后端服务失败: {e}")
        
        threading.Thread(target=run_backend, daemon=True).start()
    
    def start_frontend(self):
        """启动前端界面"""
        def run_frontend():
            try:
                self.add_log("正在启动前端界面...")
                # 这里应该启动前端服务
                # 暂时显示提示信息
                self.add_log("请手动启动前端服务: cd frontend && npm start")
            except Exception as e:
                self.add_log(f"启动前端界面失败: {e}")
        
        threading.Thread(target=run_frontend, daemon=True).start()
    
    def open_web_interface(self):
        """打开Web界面"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:3000")
            self.add_log("已打开Web界面")
        except Exception as e:
            self.add_log(f"打开Web界面失败: {e}")
    
    def run(self):
        """运行启动器"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.add_log("用户中断，正在退出...")
        except Exception as e:
            logger.error(f"启动器运行错误: {e}")
            messagebox.showerror("错误", f"启动器运行错误: {e}")


def main():
    """主函数"""
    try:
        launcher = MultiAgentLauncher()
        launcher.run()
    except Exception as e:
        logger.error(f"启动器初始化失败: {e}")
        messagebox.showerror("错误", f"启动器初始化失败: {e}")


if __name__ == "__main__":
    main()