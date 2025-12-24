
import requests

BASE = "http://127.0.0.1:8000/api/script/analyze"

print(f"Testing {BASE}")

def test(url, method):
    try:
        if method == "POST":
            r = requests.post(url, json={"content": "TEST", "mode": "analytical", "project_id": "test"})
        else:
            r = requests.get(url)
        print(f"[{method}] {url} -> {r.status_code}")
        # print(r.text)
    except Exception as e:
        print(e)

test(BASE, "POST")
test(BASE + "/", "POST")
test(BASE, "GET")
