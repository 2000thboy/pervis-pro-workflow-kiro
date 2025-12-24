import customtkinter as ctk
from launcher.services.process_manager import process_manager
import queue
import os

class ConsolePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Header for Controls
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(20, 0))
        
        # Left: View Switcher
        self.view_var = ctk.StringVar(value="System Logs")
        self.switcher = ctk.CTkSegmentedButton(
            self.header,
            values=["System Logs", "Iteration Roadmap", "Product PRD"],
            variable=self.view_var,
            command=self._on_view_change
        )
        self.switcher.pack(side="left")
        
        # Right: Action Buttons
        self.actions_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.actions_frame.pack(side="right")
        
        self.restart_btn = ctk.CTkButton(
            self.actions_frame, 
            text="↻ Restart Services", 
            width=120,
            fg_color="#F39C12", 
            hover_color="#D68910",
            command=self._on_restart
        )
        self.restart_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            self.actions_frame, 
            text="⏹ Stop All", 
            width=100,
            fg_color="#E74C3C", 
            hover_color="#C0392B",
            command=self._on_stop
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Content Display
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 12), text_color="#BDC3C7")
        self.text_area.pack(fill="both", expand=True, padx=20, pady=20)
        self.text_area.configure(state="disabled")
        
        # Log Queue
        self.log_queue = queue.Queue()
        self.log_buffer = []  # Keep a history of logs
        
        # Hook into process manager
        process_manager.log_callback = self._on_log_received
        
        # Start log processing loop
        self.after(100, self._process_log_queue)

    def _on_view_change(self, value):
        """Handle view switching"""
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        
        if value == "System Logs":
            self.text_area.configure(font=("Consolas", 12))
            # Restore log history
            for msg in self.log_buffer:
                self.text_area.insert("end", msg + "\n")
            self.text_area.see("end")
            
        elif value == "Iteration Roadmap":
            self.text_area.configure(font=("Microsoft YaHei UI", 13)) # Better font for reading
            self._load_document("ITERATION_STRATEGY_REPORT.md")
            
        elif value == "Product PRD":
            self.text_area.configure(font=("Microsoft YaHei UI", 13))
            self._load_document("PERVIS_PRO_PRODUCT_DOCUMENTATION.md")
            
        self.text_area.configure(state="disabled")

    def _load_document(self, filename):
        """Load markdown document into text area"""
        try:
            # Assuming these files are in the project root
            # We need to find the project root relative to this file
            # This file is in launcher/ui/pages/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            # Fallback for simple structure assumption if above is too deep
            # Actually, let's use the known absolute path structure or a relative fallback
            
            # Try to find the file in obvious locations
            possible_paths = [
                os.path.join(project_root, filename),
                os.path.join(os.getcwd(), filename),
                f"f:\\100KIRO project\\Pervis PRO\\{filename}" # Hardcoded based on user context
            ]
            
            content = f"Document not found: {filename}"
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    break
            
            self.text_area.insert("1.0", content)
            
        except Exception as e:
            self.text_area.insert("1.0", f"Error loading document: {str(e)}")

    def _on_restart(self):
        self.restart_btn.configure(state="disabled", text="Restarting...")
        process_manager.restart_all()
        # Reset button state after a delay
        self.after(3000, lambda: self.restart_btn.configure(state="normal", text="↻ Restart Services"))

    def _on_stop(self):
        process_manager.stop_all()
        self.stop_btn.configure(text="Stopped", state="disabled")
        self.after(2000, lambda: self.stop_btn.configure(text="⏹ Stop All", state="normal"))

    def _on_log_received(self, message):
        self.log_queue.put(message)

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_buffer.append(msg)
            
            # Only update UI if we are in Log view
            if self.view_var.get() == "System Logs":
                self.text_area.configure(state="normal")
                self.text_area.insert("end", msg + "\n")
                self.text_area.see("end")
                self.text_area.configure(state="disabled")
            
        self.after(100, self._process_log_queue)
