import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_modules():
    print("Verifying modules...")
    try:
        from launcher.services.detector import detector
        print("[OK] detector imported")
        
        from launcher.services.traffic_control import traffic_crtl
        print("[OK] traffic_control imported")
        
        # UI module imports might fail if tk is not available in headless env, but let's try importing
        try:
            from launcher.ui.storage_panel import StorageTopologyPanel
            print("[OK] storage_panel imported")
        except Exception as e:
            print(f"[WARN] storage_panel import failed (expected if headless): {e}")

        try:
            from launcher.ui.dashboard import DashboardApp
            print("[OK] dashboard imported")
        except Exception as e:
            print(f"[WARN] dashboard import failed (expected if headless): {e}")
            
    except ImportError as e:
        print(f"[FAIL] Import Error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
        
    return True

def verify_detector_logic():
    print("\nVerifying detector logic...")
    try:
        from launcher.services.detector import detector
        async def run_check():
            res = await detector.run_full_scan()
            print(f"[OK] Detector scan result keys: {res.keys()}")
            
        asyncio.run(run_check())
    except Exception as e:
        print(f"[FAIL] Detector logic failed: {e}")

if __name__ == "__main__":
    if verify_modules():
        verify_detector_logic()
