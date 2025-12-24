
import asyncio
import httpx
import sys

# Mock Data
PROJECT_ID = "temp_session" # Assuming this exists or will fail gracefully, but we just want to check route existence

async def check_endpoints():
    base_url = "http://127.0.0.1:8000"
    print(f"Checking endpoints at {base_url}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Check Script Markdown Export
        # We expect 500 or 404 (Project not found) but NOT 404 (Not Found URL) or 405 or Import Error
        try:
            resp = await client.post(f"{base_url}/api/export/script", json={
                "project_id": "non_existent_project", 
                "format": "md"
            })
            print(f"POST /api/export/script (md): {resp.status_code}")
            # If 500 with 'Project not found' in detailed error -> Success (Route works)
            if resp.status_code == 500 and "Project not found" in resp.text:
                 print("✅ Script Markdown route valid (Logic executed)")
            elif resp.status_code == 200:
                 print("✅ Script Markdown route valid (Success)")
            else:
                 print(f"⚠️ Unexpected status: {resp.text}")

        except Exception as e:
            print(f"❌ Script check failed: {e}")

        # 2. Check NLE Export
        try:
            resp = await client.post(f"{base_url}/api/export/nle", json={
                "project_id": "non_existent_project",
                "format": "xml"
            })
            print(f"POST /api/export/nle (xml): {resp.status_code}")
            if resp.status_code == 500 and "Project not found" in resp.text:
                 print("✅ NLE XML route valid")
            elif resp.status_code == 200:
                 print("✅ NLE XML route valid")
            else:
                 print(f"⚠️ Unexpected status: {resp.text}")

        except Exception as e:
            print(f"❌ NLE check failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(check_endpoints())
    except KeyboardInterrupt:
        pass
