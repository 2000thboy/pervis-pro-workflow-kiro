# ⚠️ Initial System Startup Note

**Status**: Frontend-Backend Bridge Installed.

## Current Activity: AI Model Download
The backend is currently downloading the **CLIP (Vision)** and **BERT (Text)** models from HuggingFace to enable the new "Smart Build" and "Semantic Search" features.

- **File**: `pytorch_model.bin` (~1.5GB)
- **Status**: Downloading...
- **Impact**: The API (`localhost:8000`) will not respond to frontend requests until this download finishes.

## Action Required
Please wait for the backend console to show `Application startup complete.` before testing the "Smart Build" or "Search" buttons in the frontend. This is a one-time process.
