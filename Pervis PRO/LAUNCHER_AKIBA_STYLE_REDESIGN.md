# Launcher Redesign: Akiba Style

## User Goals
1.  **Visual Style**: "Akiba" style (Dark theme, Left Sidebar, Big "One-Click Start" button).
2.  **Functional**:
    -   **One-Click Start**: Start Backend + Frontend + Open Browser.
    -   **Embedded Console**: No more popping up CMD windows.
    -   **Folder Shortcuts**: Quick access to Assets/Outputs.
    -   **Version Management**: Placeholder for updates.

## UI Layout (CustomTkinter)

### 1. Structure (`launcher/ui/main_window.py`)
*   **Left Sidebar (Navigation)**:
    *   [Icon] Home (主页)
    *   [Icon] Console (控制台)
    *   [Icon] Settings (高级选项) - Traffic Control here
    *   [Icon] Versions (版本管理)
*   **Right Content Area**:
    *   Dynamic frame switching.

### 2. Pages

#### A. Home Page (`launcher/ui/pages/home.py`)
*   **Hero Banner**: "Pervis PRO" logo/text.
*   **Status Bar**: System Health (from Detector).
*   **Folder Shortcuts**:
    *   [📂 Assets] (L:\PreVis_Assets)
    *   [📂 Renders] (L:\PreVis_Storage\renders)
    *   [📂 Exports]
*   **Big Action Button**:
    *   **[ ▶ 一键启动 ]** (Bottom Right, Floating or Fixed).
    *   Triggers: `Start Backend` -> `Start Frontend` -> `Open Browser`.

#### B. Console Page (`launcher/ui/pages/console.py`)
*   `CTkTextbox` in read-only mode.
*   `stdout` / `stderr` redirection to this widget.
*   Shows logs from Subprocesses (Backend/Frontend).

#### C. Settings Page (`launcher/ui/pages/settings.py`)
*   Traffic Control Slider.
*   Storage Topology Panel (The visual map we built).

## Logic Layer (`launcher/services/process_manager.py`)
*   **`ProcessManager`**:
    *   `start_backend()`: `subprocess.Popen(..., stdout=PIPE, stderr=PIPE)`
    *   `start_frontend()`: `subprocess.Popen(...)`
    *   `stop_all()`: Cleanup on exit.
    *   `get_logs()`: Queue-based log reading to update UI safely.

## Implementation Steps
1.  **Refactor**: Create `launcher/ui/pages` package.
2.  **Verify Startup**: Confirm how to start Backend (`uvicorn`?) and Frontend (`npm`?).
3.  **Build UI**:
    *   Main Window (Sidebar).
    *   Home Page (Buttons).
    *   Console Page (Log Widget).
4.  **Integrate Logic**:
    *   Connect "One-Click Start" to `ProcessManager`.
    *   Wire Console output to UI.