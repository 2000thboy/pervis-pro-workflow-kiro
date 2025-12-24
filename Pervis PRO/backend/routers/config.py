import os
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ModelConfig(BaseModel):
    provider: str
    gemini_api_key: str | None = None
    openai_api_key: str | None = None

@router.get("/model")
async def get_model():
    return {
        "provider": os.getenv("LLM_PROVIDER", "gemini"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }

@router.post("/model")
async def set_model(cfg: ModelConfig):
    if cfg.provider not in ("local", "gemini", "openai"):
        raise HTTPException(status_code=400, detail="Invalid provider")
    # Resolve .env path (project root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(project_root, ".env")
    # Read existing lines
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []
    # Helper to replace or add a line
    def set_line(key: str, value: str):
        pattern = re.compile(rf"^{re.escape(key)}=.*$")
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[i] = f"{key}={value}\n"
                return
        lines.append(f"{key}={value}\n")
    set_line("LLM_PROVIDER", cfg.provider)
    if cfg.gemini_api_key is not None:
        set_line("GEMINI_API_KEY", cfg.gemini_api_key)
    if cfg.openai_api_key is not None:
        set_line("OPENAI_API_KEY", cfg.openai_api_key)
    # Write back
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return {"status": "ok"}
