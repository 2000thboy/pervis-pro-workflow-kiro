import requests
import json
import time

def test_bridge():
    print("[TEST] Testing Frontend-Backend Bridge...")
    
    # 1. Health Check
    try:
        res = requests.get('http://127.0.0.1:8000/api/health')
        if res.status_code == 200:
            print("[PASS] Backend Health: OK")
        else:
            print(f"[FAIL] Backend Health: {res.status_code}")
            return
    except Exception as e:
        print(f"[FAIL] Backend not reachable: {e}")
        return

    # 2. Semantic Search (Simulating BeatBoard Search)
    payload = {
        "query_text": "dark cyberpunk rain",
        "beat_id": "test_beat_001",
        "limit": 5
    }
    try:
        res = requests.post('http://127.0.0.1:8000/api/search/semantic', json=payload)
        if res.status_code == 200:
            data = res.json()
            print(f"[PASS] Semantic Search: Found {data.get('total_matches')} matches")
            # print(data)
        else:
            print(f"[FAIL] Semantic Search: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[FAIL] Search API error: {e}")

    # 3. Script Analysis (Simulating Smart Build)
    script_payload = {
        "content": "EXT. CITY - DAY\nA cyberpunk city in rain.",
        "mode": "analytical",
        "project_id": "test_proj"
    }
    try:
        res = requests.post('http://127.0.0.1:8000/api/script/analyze', json=script_payload)
        if res.status_code == 200:
             print("[PASS] Script Analysis: OK")
        else:
             print(f"[FAIL] Script Analysis: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[FAIL] Analysis API error: {e}")

if __name__ == "__main__":
    test_bridge()
