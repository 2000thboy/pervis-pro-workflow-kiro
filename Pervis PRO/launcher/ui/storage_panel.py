import tkinter as tk
import customtkinter as ctk
from typing import List, Dict

class StorageTopologyPanel(ctk.CTkFrame):
    """
    存储拓扑图面板 (Storage Topology)
    原本计划用于显示 Local -> NAS 的连接状态
    包含：
    1. 本地节点 (Local Node)
    2. 连接线 (Connection Line) - 动态颜色
    3. NAS 节点列表 (NAS Nodes)
    """
    
    def __init__(self, master, on_import_click=None, on_scan_click=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_import_click = on_import_click
        self.on_scan_click = on_scan_click
        
        self.grid_columnconfigure(0, weight=1) # Local
        self.grid_columnconfigure(1, weight=2) # Lines
        self.grid_columnconfigure(2, weight=1) # NAS
        
        # Local Node
        self.local_node = self._create_node("本地服务器", "运行中", 0, 0)
        
        # Container for NAS nodes
        self.nas_container = ctk.CTkFrame(self, fg_color="transparent")
        self.nas_container.grid(row=0, column=2, sticky="ns", padx=10, pady=10)
        
        # [NEW] Import Button Area
        self.import_btn = ctk.CTkButton(
            self.nas_container, 
            text="+ 引入文件夹", 
            fg_color="transparent", 
            border_width=1, 
            command=self._handle_import
        )
        self.import_btn.pack(side="bottom", pady=10, fill="x")
        
        # Canvas for drawing lines
        # Tkinter Canvas does not support 'transparent', so we must fallback to a solid color if parent is transparent
        bg_color = self._apply_appearance_mode(self._fg_color)
        if bg_color == "transparent":
            bg_color = "#2B2B2B" # Default dark background
            
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        
        # Mock Data
        self.nas_nodes = []
        self.add_nas_node("Z:\\Movies", "online", "12TB Used")
        self.add_nas_node("Y:\\Backups", "offline", "Disconnected")

        # Initial draw
        self.after(100, self.draw_connections)
        self.bind("<Configure>", lambda e: self.draw_connections())

    def _create_node(self, title, status, row, col, parent=None):
        """创建一个节点卡片"""
        if parent is None:
            parent = self
            
        is_online = status in ["online", "running", "运行中"]
        color = "#2ECC71" if is_online else "#E74C3C"
        bg_color = "#333333" if is_online else "#2C2C2C"
        
        # Outer Card
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=0, fg_color=bg_color)
        if parent == self:
             card.grid(row=row, column=col, padx=25, pady=25, sticky="ew")
        else:
             card.pack(fill="x", pady=12)
             
        # Header Strip (Color Coded)
        header = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=color)
        header.pack(fill="x", side="top")
            
        # Title
        icon = "🖥️" if parent == self else "💾"
        ctk.CTkLabel(card, text=f"{icon} {title}", font=("Roboto Medium", 15), text_color="#EEEEEE").pack(pady=(15, 5))
        
        # Status Badge
        status_text = status.upper()
        badge_color = color
        ctk.CTkLabel(card, text=f"• {status_text}", text_color=badge_color, font=("Roboto", 11, "bold")).pack(pady=(0, 10))
        
        return card

    def add_nas_node(self, path, status, info):
        """动态添加NAS节点"""
        # Insert before the Import button
        node = self._create_node(path, status, 0, 0, parent=self.nas_container)
        
        # Info
        ctk.CTkLabel(node, text=info, font=("Roboto", 11), text_color="gray").pack(pady=(0, 5))
        
        # Actions Row
        actions = ctk.CTkFrame(node, fg_color="transparent")
        actions.pack(pady=(0, 15))
        
        # Buttons
        if status == "online":
            ctk.CTkButton(actions, text="扫描", width=60, height=28, fg_color="#3498DB", hover_color="#2980B9",
                          font=("Roboto", 11), command=lambda p=path: self._handle_scan(p)).pack(side="left", padx=4)
            ctk.CTkButton(actions, text="↻", width=28, height=28, fg_color="#555555", hover_color="#666666",
                          font=("Roboto", 12), command=lambda p=path: self._handle_scan(p)).pack(side="left", padx=4)
        else:
            ctk.CTkButton(actions, text="重连", width=80, height=28, fg_color="#E67E22", hover_color="#D35400",
                          font=("Roboto", 11)).pack(side="left")
        
        self.nas_nodes.append({"widget": node, "status": status, "path": path})
        self.draw_connections()

    def _handle_import(self):
        if self.on_import_click:
            self.on_import_click()
            
    def _handle_scan(self, path):
        if self.on_scan_click:
            self.on_scan_click(path)

    def draw_connections(self):
        """绘制连线"""
        self.update_idletasks() # Force layout update to get correct width
        self.canvas.delete("all")
        bg_color = self._apply_appearance_mode(self._fg_color)
        if bg_color == "transparent":
            bg_color = "#2B2B2B"
        self.canvas.configure(bg=bg_color) # Update bg
        
        # Get Local Node coords (relative to canvas)
        # Note: This is tricky in grid layouts without update_idletasks.
        # We assume center of left side and center of right side items.
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 10: return # Not rendered yet
        
        start_x = 0
        start_y = h / 2
        
        for i, node_data in enumerate(self.nas_nodes):
            widget = node_data["widget"]
            status = node_data["status"]
            
            # Rough estimation of target Y (distribute evenly)
            # In a real app we'd get widget.winfo_y() mapped to canvas
            target_y = (h / (len(self.nas_nodes) + 1)) * (i + 1)
            target_x = w
            
            color = "#2ECC71" if status == "online" else "#E74C3C"
            dash = None if status == "online" else (5, 5)
            
            # Draw Bezier Curve
            # Start (Right side of local node area) -> End (Left side of target node)
            
            # Control points for sigmoid curve
            # P0 (Start) -> P1 (Control Right) -> P2 (Control Left) -> P3 (Target)
            
            c1_x = start_x + (w * 0.5) 
            c1_y = start_y
            
            c2_x = target_x - (w * 0.5)
            c2_y = target_y
            
            # Use line with smooth=True and multiple points to approximate curve
            # Or use explicit bezier math if simple smoothing isn't enough.
            # Tkinter create_line(..., smooth=True) works with 4 points for cubic bezier approximation
            
            self.canvas.create_line(
                start_x, start_y,
                c1_x, c1_y,
                c2_x, c2_y,
                target_x, target_y,
                fill=color, width=3, smooth=True, dash=dash
            )
            
            # Flow animation dot (Center of curve approximation)
            if status == "online":
                mid_x = (start_x + target_x) / 2
                mid_y = (start_y + target_y) / 2
                self.canvas.create_oval(mid_x-4, mid_y-4, mid_x+4, mid_y+4, fill="white", outline=color, width=2)

