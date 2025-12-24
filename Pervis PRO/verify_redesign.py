import sys
import os

# Mock layout
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_redesign():
    print("Verifying Launcher Redesign...")
    try:
        print("1. Importing ProcessManager...")
        from launcher.services.process_manager import process_manager
        print("[OK] ProcessManager")
        
        print("2. Importing MainWindow...")
        from launcher.ui.main_window import MainWindow
        print("[OK] MainWindow")
        
        print("3. Importing Pages...")
        from launcher.ui.pages.home import HomePage
        from launcher.ui.pages.console import ConsolePage
        from launcher.ui.pages.settings import SettingsPage
        print("[OK] Pages imported")
        
    except ImportError as e:
        print(f"[FAIL] Import Error: {e}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")

if __name__ == "__main__":
    verify_redesign()
