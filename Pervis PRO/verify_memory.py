import sys
import os
# Add root to path so we can import backend services
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from services.memory_store import MemoryStore
    print("[TEST] Initializing MemoryStore...")
    store = MemoryStore()
    
    if not store.client:
        print("[FAIL] Client initialization failed")
        sys.exit(1)
        
    print("[TEST] Adding test memory...")
    # Mock a 512-dim vector
    test_vector = [0.1] * 512
    store.add_memory("test_asset_001", test_vector, {"type": "test", "timestamp": "2025-12-20"})
    
    print("[TEST] Querying memory...")
    results = store.search_similar(test_vector, limit=1)
    
    if results and results[0]['id'] == 'test_asset_001':
        print(f"[PASS] Successfully retrieved memory: {results[0]['id']} with score {results[0]['score']}")
    else:
        print(f"[FAIL] Query returned unexpected results: {results}")

    stats = store.get_stats()
    print(f"[INFO] DB Stats: {stats}")

except Exception as e:
    print(f"[ERROR] Verification failed: {e}")
    import traceback
    traceback.print_exc()
