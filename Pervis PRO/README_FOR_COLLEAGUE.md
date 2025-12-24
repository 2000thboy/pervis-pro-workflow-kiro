# Pervis PRO - Developer Handover Guide

This project contains the Pervis PRO Full Stack Application (FastAPI Backend + React Frontend).

## Project Structure
- `backend/`: FastAPI Python application
- `frontend/`: React/Vite TypeScript application
- `launcher/`: Python-based Desktop Launcher Wrapper

## Prerequisites
1.  **Python 3.10+** (Ensure added to PATH)
2.  **Node.js 18+** & npm
3.  **Ollama** (Optional, for Local AI) - [Download](https://ollama.com)
4.  **FFmpeg** (Recommended for video processing)

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Configuration (.env)
The `backend/.env` file contains critical configuration.
- **Gemini Key**: Set `GEMINI_API_KEY`.
- **AI Provider**: Set `LLM_PROVIDER=gemini` or `local`.
- **Local AI**: If using `local`, ensure Ollama is running (`ollama run qwen2.5:14b`).

### 4. Running the Project
**Option A: Using the Launcher (Recommended)**
Run the startup script in the root directory:
```bash
python 启动_Pervis_PRO.py
```

**Option B: Manual Start (Debugging)**
*Terminal 1 (Backend):*
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

*Terminal 2 (Frontend):*
```bash
cd frontend
npm run dev
```

## Troubleshooting
- **AI Connection Failed**: Check `.env` settings and ensure your API Key is valid or Ollama is running.
- **Frontend Error**: Ensure Backend is running on port 8000.
