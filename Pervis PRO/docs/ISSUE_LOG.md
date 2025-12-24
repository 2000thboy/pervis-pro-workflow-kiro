# Issue Log

## 2025-12-20: Frontend-Backend Disconnection (Critical)
**Status**: In Progress
**Severity**: High
**Description**: The Frontend (React) was operating in a "Mock Mode" for critical AI features (Script Analysis, Asset Search), completely disconnected from the Python Backend.
**Symptoms**:
- "Smart Build" was fake (using `mockDelay`).
- "Search" returned hardcoded mock data.
- "Random Example" forced a tab switch unnaturally.
**Root Cause**: `geminiService.ts` and `api.ts` were implemented as standalone prototypes without HTTP fetch logic to `localhost:8000`.
**Fix Strategy**:
1.  Upgrade `api.ts` to include `fetch` calls to backend endpoints.
2.  Refactor `geminiService.ts` to use these real API calls.
3.  Fix UX logic in `ScriptIngestion.tsx`.
