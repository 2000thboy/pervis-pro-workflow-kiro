import customtkinter as ctk
from launcher.ui.pages.home import HomePage
from launcher.ui.pages.console import ConsolePage
from launcher.ui.pages.settings import SettingsPage

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Pervis PRO Director - Launcher")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        
        # Grid Layout: Sidebar(0) + Content(1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Sidebar
        self._create_sidebar()
        
        # 2. Content Area
        self.content_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # Initialize Pages
        self.pages = {
            "home": HomePage(self.content_frame),
            "console": ConsolePage(self.content_frame),
            "settings": SettingsPage(self.content_frame),
            "versions": self._create_placeholder_page("版本管理 (Versions)\n\n当前版本: v0.2.0-beta\n检查更新功能开发中...")
        }
        
        # Show Start Page
        self.show_page("home")

    def _create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1) # Spacer at bottom
        
        # App Title/Logo Area
        ctk.CTkLabel(sidebar, text="Pervis PRO", font=("Impact", 20)).pack(pady=30)
        
        # Nav Buttons
        self._add_nav_btn(sidebar, "🏠 主页", "home")
        self._add_nav_btn(sidebar, "⚙️ 设置", "settings")
        self._add_nav_btn(sidebar, "📦 版本", "versions")
        self._add_nav_btn(sidebar, "📟 控制台", "console")
        
        # Version info at bottom
        ctk.CTkLabel(sidebar, text="v0.2.0", text_color="gray").pack(side="bottom", pady=20)

    def _add_nav_btn(self, parent, text, page_key):
        if not hasattr(self, 'nav_buttons'): self.nav_buttons = {}
        
        btn = ctk.CTkButton(
            parent, 
            text=text, 
            height=45,
            fg_color="transparent", 
            text_color="#9CA3AF",
            font=("Roboto Medium", 14),
            hover_color="#374151",
            anchor="w",
            command=lambda: self.show_page(page_key)
        )
        btn.pack(pady=4, padx=10, fill="x")
        self.nav_buttons[page_key] = btn

    def _create_placeholder_page(self, msg):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(frame, text=msg, font=("Roboto", 16)).pack(expand=True)
        return frame

    def show_page(self, page_key):
        # Hide all pages
        for p in self.pages.values():
            p.pack_forget()
            
        # Reset all nav buttons
        if hasattr(self, 'nav_buttons'):
            for key, btn in self.nav_buttons.items():
                btn.configure(fg_color="transparent", text_color="#9CA3AF", border_width=0)
        
        # Highlight active button
        if hasattr(self, 'nav_buttons') and page_key in self.nav_buttons:
            self.nav_buttons[page_key].configure(
                fg_color="#3498DB", 
                text_color="white",
                border_width=0
            )
        
        # Show selected
        self.pages[page_key].pack(fill="both", expand=True)
