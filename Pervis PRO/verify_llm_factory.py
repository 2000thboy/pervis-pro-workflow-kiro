import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Testing Import of llm_provider...")
    from services.llm_provider import get_llm_provider, LLMConfig
    print("SUCCESS: llm_provider imported.")
    
    print("Testing Factory Instantiation (Default: Gemini)...")
    # Default should be gemini
    provider = get_llm_provider()
    print(f"Provider Type: {type(provider)}")
    
    # Test Config Override Simulation
    print("Testing Config Override (Simulated Local)...")
    LLMConfig.PROVIDER = "local"
    local_provider = get_llm_provider()
    print(f"Provider Type: {type(local_provider)}")
    
    print("Testing Import of ScriptProcessor...")
    # Mock DB Session
    from unittest.mock import MagicMock
    db = MagicMock()
    
    # We need to mock 'services.gemini_client' inside script_processor if we didn't remove the import
    # But we did remove usage. Let's see if import remains.
    # The file has 'from services.gemini_client import GeminiClient' at top?
    # I didn't remove that import line in my edit, just the usage in __init__.
    # So it should be fine as long as the file exists.
    
    from services.script_processor import ScriptProcessor
    processor = ScriptProcessor(db)
    print("SUCCESS: ScriptProcessor instantiated.")
    print(f"Processor AI Client: {type(processor.ai_client)}")

except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
