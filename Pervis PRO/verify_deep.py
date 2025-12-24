
import sys
import os
import threading
import time

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def log(msg):
    print(f"[VERIFY] {msg}")

def test_imports():
    log("Testing imports...")
    try:
        import customtkinter
        log("  [OK] customtkinter")
        
        from launcher.services.process_manager import process_manager
        log("  [OK] ProcessManager")
        
        from launcher.services.detector import detector
        log("  [OK] Detector")
        
        from launcher.ui.storage_panel import StorageTopologyPanel
        log("  [OK] StorageTopologyPanel (Import)")
        
        return True
    except ImportError as e:
        log(f"  [FAIL] Import Error: {e}")
        return False
    except Exception as e:
        log(f"  [FAIL] Unexpected Error: {e}")
        return False

def test_classes():
    log("Testing Class Initialization (Headless)...")
    try:
        # We can't fully instantiate UI widgets without a root tk, 
        # but we can check if the python files have syntax errors or immediate crashes
        
        # Check Detetor
        import asyncio
        from launcher.services.detector import detector
        # run_full_scan is async
        try:
            res = asyncio.run(detector.run_full_scan())
            drives = asyncio.run(detector.check_all_drives())
            log(f"  [OK] Detector Scan: {res.get('overall_health')} | Drives: {drives}")
        except RuntimeError:
            # If loop already running (unlikely here but possible)
            log("  [WARN] Async loop issue, skipping detector execution check")

        
        # Check Traffic Control
        from launcher.services.traffic_control import traffic_crtl
        mode = traffic_crtl.get_current_metrics()
        log(f"  [OK] Traffic Control: {mode['name']}")

        # Check Settings Page Logic
        from launcher.ui.pages.settings import SettingsPage
        if not hasattr(SettingsPage, '_on_click_import'):
            raise Exception("SettingsPage missing _on_click_import")
        log("  [OK] SettingsPage Logic Ported")
        
        return True
    except Exception as e:
        log(f"  [FAIL] Class Test Error: {e}")
        return False

if __name__ == "__main__":
    log("Starting Deep Verification...")
    if test_imports() and test_classes():
        log("✅ ALL CHECKS PASSED")
        sys.exit(0)
    else:
        log("❌ CHECKS FAILED")
        sys.exit(1)
