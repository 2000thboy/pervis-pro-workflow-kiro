import sys
import os
import traceback

# Add backend to path to match main.py behavior
sys.path.append(os.path.join(os.getcwd(), 'backend'))

modules = [
    "backend.database",
    "backend.routers.script",
    "backend.routers.assets",
    "backend.routers.search", 
    "backend.routers.feedback",
    "backend.routers.transcription",
    "backend.routers.multimodal",
    "backend.routers.batch", 
    "backend.routers.export",
    "backend.routers.tags",
    "backend.routers.vector",
    "backend.routers.timeline",
    "backend.routers.render",
    "backend.routers.analysis",
    "backend.routers.images",
    "backend.routers.projects",
    "backend.routers.autocut",
    "backend.routers.storage"
]

print("--- Testing Modules ---")
for mod in modules:
    try:
        __import__(mod)
        print(f"[OK] {mod}")
    except Exception as e:
        print(f"[FAIL] {mod}: {e}")
        # traceback.print_exc()

print("--- Done ---")
