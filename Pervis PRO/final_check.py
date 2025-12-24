
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        if r.status_code == 200:
            print("[PASS] Backend Health: OK")
            return True
        else:
            print(f"[FAIL] Backend Health: {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Backend Connection: {e}")
        return False

def test_script_analyze():
    print("Testing Script Analysis...")
    payload = {
        "content": "INT. OFFICE - DAY\nJohn sits at his desk.",
        "mode": "analytical",
        "project_id": "test_verification"
    }
    try:
        r = requests.post(f"{BASE_URL}/api/script/analyze", json=payload)
        if r.status_code == 200:
            data = r.json()
            beats = len(data.get("beats", []))
            print(f"[PASS] Script Analysis: {beats} beats found.")
            return True
        else:
            print(f"[FAIL] Script Analysis: {r.status_code} - {r.text[:100]}")
            return False
    except Exception as e:
        print(f"[FAIL] Script Analysis Error: {e}")
        return False

def test_sem_search():
    print("Testing Semantic Search...")
    try:
        # Search requires a 'query' param
        r = requests.get(f"{BASE_URL}/api/search/semantic", params={"query": "office desk"})
        if r.status_code == 200:
            data = r.json()
            # Depending on if we have mock data or real data, we might get empty results, 
            # but 200 OK means the router is working.
            print(f"[PASS] Semantic Search: OK (Response valid)")
            return True
        else:
            print(f"[FAIL] Semantic Search: {r.status_code} - {r.text[:100]}")
            return False
    except Exception as e:
        print(f"[FAIL] Semantic Search Error: {e}")
        return False

if __name__ == "__main__":
    print("--- STARTING FINAL CHECK ---")
    h = test_health()
    if h:
        test_script_analyze()
        test_sem_search()
    else:
        print("Skipping other tests due to health check failure.")
    print("--- CHECK COMPLETE ---")
