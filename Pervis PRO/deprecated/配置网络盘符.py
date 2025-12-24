#!/usr/bin/env python3
"""
PreVis PRO 网络盘符配置工具
专门用于配置L盘作为素材库
"""

import os
import sys
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class NetworkDriveConfigurator:
    """网络盘符配置器"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PreVis PRO - 网络盘符配置")
        self.root.geometry("700x600")
        self.root.configure(bg='#1e1e1e')
        
        # 检测网络驱动器
        self.network_drives = self.detect_network_drives()
        self.selected_drive = None
        
        self.setup_ui()
    
    def detect_network_drives(self):
        """检测网络驱动器"""
        drives = []
        
        # 检测L盘
        l_drive = Path("L:\\")
        if l_drive.exists():
            try:
                total, used, free = shutil.disk_usage(l_drive)
                drives.append({
                    'letter': 'L',
                    'name': '影片参考',
                    'path': 'L:\\',
                    'total_tb': total / (1024**4),
                    'free_tb': free / (1024**4),
                    'recommended': True
                })
            except:
                pass
        
        # 检测其他网络驱动器
        for letter in 'MNOPQRSTUVWXYZ':
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists() and letter != 'L':
                try:
                    total, used, free = shutil.disk_usage(drive_path)
                    drives.append({
                        'letter': letter,
                        'name': f'网络驱动器 {letter}',
                        'path': f'{letter}:\\',
                        'total_tb': total / (1024**4),
                        'free_tb': free / (1024**4),
                        'recommended': False
                    })
                except:
                    pass
        
        return drives
    
    def setup_ui(self):
        """设置用户界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill='x', pady=20)
        
        tk.Label(title_frame, text="网络盘符配置", 
                font=('Arial', 18, 'bold'), 
                fg='#fbbf24', bg='#1e1e1e').pack()
        tk.Label(title_frame, text="配置大容量网络存储作为素材库", 
                font=('Arial', 12), 
                fg='#9ca3af', bg='#1e1e1e').pack()
        
        # 网络驱动器列表
        drives_frame = tk.LabelFrame(self.root, text="可用网络驱动器", 
                                   font=('Arial', 12, 'bold'),
                                   fg='white', bg='#2d2d2d', bd=2)
        drives_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        if self.network_drives:
            for drive in self.network_drives:
                self.create_drive_card(drives_frame, drive)
        else:
            tk.Label(drives_frame, text="❌ 未检测到网络驱动器", 
                    font=('Arial', 14), fg='#ff6b6b', bg='#2d2d2d').pack(pady=50)
        
        # 配置预览
        preview_frame = tk.LabelFrame(self.root, text="配置预览", 
                                    font=('Arial', 12, 'bold'),
                                    fg='white', bg='#2d2d2d', bd=2)
        preview_frame.pack(fill='x', padx=20, pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=8, width=80,
                                  bg='#1e1e1e', fg='#00ff00', 
                                  font=('Consolas', 9))
        self.preview_text.pack(padx=10, pady=10)
        
        # 按钮区域
        button_frame = tk.Frame(self.root, bg='#1e1e1e')
        button_frame.pack(fill='x', padx=20, pady=10)
        
        self.apply_btn = tk.Button(button_frame, text="✅ 应用配置", 
                                 font=('Arial', 12, 'bold'),
                                 fg='white', bg='#28a745',
                                 padx=20, pady=10, state='disabled',
                                 command=self.apply_configuration)
        self.apply_btn.pack(side='left', padx=5)
        
        tk.Button(button_frame, text="🔄 刷新驱动器", 
                 font=('Arial', 10),
                 fg='white', bg='#17a2b8',
                 padx=15, pady=8,
                 command=self.refresh_drives).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="❌ 取消", 
                 font=('Arial', 10),
                 fg='white', bg='#dc3545',
                 padx=15, pady=8,
                 command=self.root.quit).pack(side='right', padx=5)
        
        # 显示初始预览
        self.update_preview()
    
    def create_drive_card(self, parent, drive):
        """创建驱动器卡片"""
        card_frame = tk.Frame(parent, bg='#374151', relief='raised', bd=2)
        card_frame.pack(fill='x', padx=10, pady=5)
        
        # 驱动器信息
        info_frame = tk.Frame(card_frame, bg='#374151')
        info_frame.pack(fill='x', padx=15, pady=10)
        
        # 标题行
        title_frame = tk.Frame(info_frame, bg='#374151')
        title_frame.pack(fill='x')
        
        drive_title = f"{drive['letter']}: - {drive['name']}"
        if drive['recommended']:
            drive_title += " ⭐ 推荐"
        
        tk.Label(title_frame, text=drive_title, 
                font=('Arial', 14, 'bold'), 
                fg='#fbbf24' if drive['recommended'] else '#ffffff', 
                bg='#374151').pack(side='left')
        
        # 容量信息
        capacity_text = f"总容量: {drive['total_tb']:.1f} TB  |  可用: {drive['free_tb']:.1f} TB"
        tk.Label(info_frame, text=capacity_text, 
                font=('Arial', 10), fg='#d1d5db', bg='#374151').pack(anchor='w', pady=(5, 0))
        
        # 路径信息
        tk.Label(info_frame, text=f"路径: {drive['path']}", 
                font=('Consolas', 9), fg='#9ca3af', bg='#374151').pack(anchor='w')
        
        # 选择按钮
        select_btn = tk.Button(info_frame, text="选择此驱动器", 
                             font=('Arial', 10, 'bold'),
                             fg='white', 
                             bg='#0078d4' if drive['recommended'] else '#6c757d',
                             padx=15, pady=5,
                             command=lambda d=drive: self.select_drive(d))
        select_btn.pack(anchor='w', pady=(10, 0))
    
    def select_drive(self, drive):
        """选择驱动器"""
        self.selected_drive = drive
        self.update_preview()
        self.apply_btn.config(state='normal')
        
        messagebox.showinfo("驱动器已选择", 
                          f"已选择 {drive['letter']}: ({drive['name']}) 作为素材库\n"
                          f"可用空间: {drive['free_tb']:.1f} TB")
    
    def update_preview(self):
        """更新配置预览"""
        self.preview_text.delete(1.0, tk.END)
        
        if self.selected_drive:
            drive = self.selected_drive
            preview = f"""
📁 素材库配置预览

选择的驱动器: {drive['letter']}: ({drive['name']})
可用空间: {drive['free_tb']:.1f} TB

将创建的目录结构:
{drive['path']}PreVis_Assets\\
├── originals\\          # 原始视频文件 (你上传的文件会存在这里)
├── proxies\\            # 代理文件 (系统自动生成的低分辨率版本)
├── thumbnails\\         # 缩略图 (系统自动生成的预览图)
└── audio\\              # 音频文件 (系统提取的音频)

{drive['path']}PreVis_Storage\\
├── renders\\            # 渲染输出 (最终视频输出)
├── exports\\            # 导出文件 (剧本、BeatBoard等)
└── temp\\               # 临时文件 (处理过程中的临时文件)

配置文件将更新为:
ASSET_ROOT={drive['path']}PreVis_Assets
STORAGE_ROOT={drive['path']}PreVis_Storage

📋 文件处理说明:
• 原始文件: 保持不变，存储在 originals\\ 目录
• 不会修改你的原始视频文件
• 不会添加 .txt 或其他后缀
• 系统会自动生成代理文件和缩略图到对应目录
• 数据库会记录文件信息和标签，但不修改原文件
            """
        else:
            preview = """
❌ 未选择驱动器

请从上方列表中选择一个网络驱动器作为素材库。

推荐选择 L: (影片参考) 驱动器，因为:
• 容量大 (6+ TB)
• 专门用于影片素材存储
• 网络访问稳定
            """
        
        self.preview_text.insert(1.0, preview.strip())
    
    def refresh_drives(self):
        """刷新驱动器列表"""
        self.network_drives = self.detect_network_drives()
        
        # 重新创建界面
        self.root.destroy()
        self.__init__()
        self.root.mainloop()
    
    def apply_configuration(self):
        """应用配置"""
        if not self.selected_drive:
            messagebox.showerror("错误", "请先选择一个驱动器")
            return
        
        # 在新线程中执行配置
        config_thread = threading.Thread(target=self.run_configuration)
        config_thread.daemon = True
        config_thread.start()
    
    def run_configuration(self):
        """运行配置过程"""
        try:
            drive = self.selected_drive
            
            # 1. 创建目录结构
            self.create_directory_structure(drive)
            
            # 2. 更新配置文件
            self.update_config_file(drive)
            
            # 3. 测试配置
            self.test_configuration(drive)
            
            messagebox.showinfo("配置完成", 
                              f"网络盘符配置成功！\n\n"
                              f"素材库: {drive['path']}PreVis_Assets\n"
                              f"存储库: {drive['path']}PreVis_Storage\n\n"
                              f"现在可以:\n"
                              f"• 将视频文件放入 {drive['path']}PreVis_Assets\\originals\\\n"
                              f"• 重启 PreVis PRO 以应用新配置")
            
        except Exception as e:
            messagebox.showerror("配置失败", f"配置过程中出现错误:\n{str(e)}")
    
    def create_directory_structure(self, drive):
        """创建目录结构"""
        directories = [
            Path(drive['path']) / "PreVis_Assets" / "originals",
            Path(drive['path']) / "PreVis_Assets" / "proxies",
            Path(drive['path']) / "PreVis_Assets" / "thumbnails",
            Path(drive['path']) / "PreVis_Assets" / "audio",
            Path(drive['path']) / "PreVis_Storage" / "renders",
            Path(drive['path']) / "PreVis_Storage" / "exports",
            Path(drive['path']) / "PreVis_Storage" / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def update_config_file(self, drive):
        """更新配置文件"""
        config_content = f"""ASSET_ROOT={drive['path']}PreVis_Assets
STORAGE_ROOT={drive['path']}PreVis_Storage
DATABASE_URL=sqlite:///./pervis_director.db
NETWORK_DRIVE={drive['letter']}
NETWORK_DRIVE_NAME={drive['name']}"""
        
        with open(".env", "w", encoding='utf-8') as f:
            f.write(config_content)
    
    def test_configuration(self, drive):
        """测试配置"""
        # 测试写入权限
        test_file = Path(drive['path']) / "PreVis_Assets" / "test_write.tmp"
        
        try:
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink()  # 删除测试文件
        except Exception as e:
            raise Exception(f"无法写入到网络驱动器: {e}")
    
    def run(self):
        """运行配置器"""
        self.root.mainloop()


if __name__ == "__main__":
    configurator = NetworkDriveConfigurator()
    configurator.run()