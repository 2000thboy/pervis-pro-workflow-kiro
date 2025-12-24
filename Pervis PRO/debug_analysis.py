import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import SessionLocal
from models.base import ScriptAnalysisRequest
from services.script_processor import ScriptProcessor

async def test_analysis():
    print("Initializing ScriptProcessor...")
    start_time = time.time()
    db = SessionLocal()
    processor = ScriptProcessor(db)
    
    # Short sample script
    sample_script = """
SCENE 1
INT. CAFE - DAY
A MAN (30s) sits alone. He looks nervous.
He checks his watch. 
    """
    
    req = ScriptAnalysisRequest(
        title="Debug Test",
        content=sample_script,
        mode="analytical",
        logline=""
    )
    
    print("Sending Request to AI...")
    try:
        # We want to inspect the RAW AI response before it gets cleaned, but ScriptProcessor methods are monolithic.
        # We can just look at result.
        result = await processor.analyze_script(req)
        
        print("\n=== RESULT ===")
        print(f"Status: {result.status}")
        if result.error:
            print(f"Error: {result.error}")
        
        # Check Project in DB to see if logline was saved
        if result.project_id:
             print(f"Project ID: {result.project_id}")
             # We could query DB here but let's blindly trust if status is success
        
        print(f"Raw Result Meta Check: Logline in DB?")
        # Let's inspect the processor's AI client output if we can... we can't easily.
        # But we can assume if result.status is success, DB insertion happened.
             
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print(f"Done in {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_analysis())
