# Launcher Import & Scan Feature Design

## User Requirements
1.  **Import Folder**: Manually add new source folders.
2.  **Pre-processing Prompt**: Remind/Ask user before processing.
3.  **Refresh Capability**: Re-scan existing folders.
4.  **New Content Detection**: Identify new files.
5.  **Statistics & Estimation**:
    -   File formats count.
    -   Estimated processing time.

## 1. Logic Layer (`launcher/services/scanner.py`)
We need a dedicated scanner (extending or separate from `detector.py`) to handle file system operations.

*   **`scan_directory(path)`**:
    *   Recursive walk.
    *   Filter by video extensions (`.mp4`, `.mkv`, `.mov`, etc.).
    *   New vs Old logic: For MVP, check if `.pervis` sidecar file exists or simple timestamp check.
    *   Returns: `ScanResult` object.

*   **`ScanResult` Structure**:
    ```json
    {
      "total_files": 12,
      "new_files": 5,
      "formats": {"mp4": 3, "mkv": 2},
      "total_size_gb": 15.4,
      "estimated_time_min": 20  // 5 files * 4 min/file
    }
    ```

## 2. UI Layer (`launcher/ui/`)

### A. New Dialog: `ScanConfirmationDialog`
A popup window showing the scan results.
*   **Title**: "New Content Detected"
*   **Body**:
    *   "Found 5 new video files."
    *   "Formats: MKV (2), MP4 (3)"
    *   "Estimated AI Processing Time: ~20 mins"
*   **Buttons**: [Process Now (Full Speed)] [Process Later (Silent)] [Cancel]

### B. `StorageTopologyPanel` Updates
*   Add **[+] Import Folder** button at the bottom of the NAS list.
*   Each node gets a **[↻]** (Refresh) icon button next to status.

## 3. Workflow
1.  User clicks **[+] Import**.
2.  Python `filedialog` opens -> User selects `D:\Footage`.
3.  App triggering `scanner.scan_directory('D:\Footage')`.
4.  **ScanConfirmationDialog** pops up with stats.
5.  User confirms.
6.  Folder added to Topology (Yellow -> Green).

## Implementation Steps
1.  Create `launcher/services/scanner.py`.
2.  Create `launcher/ui/dialogs.py` for the confirmation popup.
3.  Update `launcher/ui/storage_panel.py` actions.
4.  Wire it all up in `dashboard.py`.
