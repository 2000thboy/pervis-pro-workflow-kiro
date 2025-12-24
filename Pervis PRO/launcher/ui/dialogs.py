import customtkinter as ctk

class ScanResultDialog(ctk.CTkToplevel):
    """
    扫描结果确认弹窗
    展示：新文件数量、格式统计、预估耗时
    """
    
    def __init__(self, master, scan_result, on_confirm):
        super().__init__(master)
        
        self.scan_result = scan_result
        self.on_confirm = on_confirm
        
        self.title("发现新内容")
        self.geometry("400x450")
        self.resizable(False, False)
        
        # Make modal
        self.transient(master)
        self.grab_set()
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Icon / Header
        ctk.CTkLabel(self, text="✨ 发现新素材", font=("Roboto Medium", 20)).pack(pady=(20, 10))
        
        # Stats Container
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        # Grid of stats
        self._add_stat(stats_frame, "新文件:", str(self.scan_result['new_files']), 0, 0)
        self._add_stat(stats_frame, "总大小:", self._format_size(self.scan_result['total_size_bytes']), 0, 1)
        self._add_stat(stats_frame, "格式:", self._fmt_formats(self.scan_result['formats']), 1, 0, colspan=2)
        
        # Est Time Highlighting
        time_frame = ctk.CTkFrame(self, fg_color="#2C3E50")
        time_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(time_frame, text="预估处理时间", font=("Roboto", 10), text_color="gray").pack(pady=(10, 0))
        ctk.CTkLabel(time_frame, text=f"~ {self.scan_result['estimated_time_min']} 分钟", font=("Roboto Black", 24), text_color="#3498DB").pack(pady=(0, 10))
        ctk.CTkLabel(time_frame, text="(后台运行模式)", font=("Roboto", 10)).pack(pady=(0, 10))
        
        # Actions
        ctk.CTkButton(self, text="开始处理", fg_color="#2ECC71", hover_color="#27AE60", command=self._on_ok).pack(pady=10, ipady=5, padx=20, fill="x")
        ctk.CTkButton(self, text="取消", fg_color="transparent", border_width=1, command=self.destroy).pack(pady=5, padx=20, fill="x")

    def _add_stat(self, parent, label, value, row, col, colspan=1):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, columnspan=colspan, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(f, text=label, font=("Roboto", 12), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(f, text=value, font=("Roboto Medium", 14)).pack(anchor="w")

    def _format_size(self, size):
        # Simple formatter reused
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def _fmt_formats(self, fmts):
        """ {'mp4': 5, 'mkv': 2} -> 'MP4(5), MKV(2)' """
        return ", ".join([f"{k.upper()[1:]}({v})" for k,v in fmts.items()])

    def _on_ok(self):
        self.on_confirm()
        self.destroy()
