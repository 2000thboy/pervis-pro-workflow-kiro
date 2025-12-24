import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_expansion():
    print("Verifying Launcher Expansion Features...")
    try:
        print("1. Checking Scanner Service...")
        from launcher.services.scanner import scanner
        print("[OK] Scanner imported")
        
        # Test scan logic on current dir
        res = scanner.scan_directory(".")
        print(f"   Scan Test: Found {res.get('total_files')} files. Status: {res.get('status')}")
        
        print("2. Checking Dialogs...")
        from launcher.ui.dialogs import ScanResultDialog
        print("[OK] Dialogs imported")
        
        print("3. Checking Dashboard Integration...")
        # Just check if methods exist in class (static analysisish)
        from launcher.ui.dashboard import DashboardApp
        if hasattr(DashboardApp, "_on_click_import") and hasattr(DashboardApp, "_on_click_scan"):
             print("[OK] Dashboard has Import/Scan handlers")
        else:
             print("[FAIL] Dashboard missing handlers")
             
    except ImportError as e:
        print(f"[FAIL] Import Error: {e}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")

if __name__ == "__main__":
    verify_expansion()
