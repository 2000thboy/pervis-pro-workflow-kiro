from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import os
import threading
from typing import Dict, Optional, Set

import psutil

logger = logging.getLogger(__name__)


class RenderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RenderProgress:
    task_id: str
    status: RenderStatus = RenderStatus.PENDING
    progress: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class RenderResource:
    temp_files: Set[str] = field(default_factory=set)
    process_ids: Set[int] = field(default_factory=set)


class RenderStateManager:
    def __init__(self, db):
        self.db = db
        self._lock = threading.RLock()
        self._progress: Dict[str, RenderProgress] = {}
        self._resources: Dict[str, RenderResource] = {}
        self._cancelled: Set[str] = set()
        self._progress_callbacks: Dict[str, list] = {}

    def create_render_task(self, task_id: str, total_steps: int = 0) -> RenderProgress:
        with self._lock:
            self._cancelled.discard(task_id)
            progress = RenderProgress(task_id=task_id, total_steps=total_steps)
            self._progress[task_id] = progress
            self._resources.setdefault(task_id, RenderResource())
            return progress

    def get_progress(self, task_id: str) -> Optional[RenderProgress]:
        if not task_id:
            return None
        with self._lock:
            return self._progress.get(task_id)

    def update_progress(self, task_id: str, progress: float, current_step: str = "") -> bool:
        if not task_id:
            return False
        with self._lock:
            state = self._progress.get(task_id)
            if state is None:
                return False
            clamped = max(0.0, min(100.0, float(progress)))
            state.progress = clamped
            state.current_step = current_step if current_step is not None else ""
            if state.started_at is None and clamped > 0.0 and state.status == RenderStatus.PENDING:
                state.status = RenderStatus.PROCESSING
                state.started_at = datetime.utcnow()
            callbacks = list(self._progress_callbacks.get(task_id, []))

        for cb in callbacks:
            try:
                cb(state)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        return True

    def set_status(self, task_id: str, status: RenderStatus) -> bool:
        if not task_id:
            return False
        with self._lock:
            state = self._progress.get(task_id)
            if state is None:
                return False
            state.status = status
            if status == RenderStatus.PROCESSING and state.started_at is None:
                state.started_at = datetime.utcnow()
            if status in {RenderStatus.COMPLETED, RenderStatus.FAILED, RenderStatus.CANCELLED}:
                state.completed_at = datetime.utcnow()
            return True

    def cancel_task(self, task_id: str) -> bool:
        if not task_id:
            return False
        with self._lock:
            state = self._progress.get(task_id)
            if state is None:
                return False
            self._cancelled.add(task_id)
            state.status = RenderStatus.CANCELLED
            state.completed_at = datetime.utcnow()
            return True

    def is_cancelled(self, task_id: str) -> bool:
        if not task_id:
            return False
        with self._lock:
            return task_id in self._cancelled

    def add_temp_file(self, task_id: str, file_path: str) -> None:
        if not task_id or not file_path:
            return
        with self._lock:
            self._resources.setdefault(task_id, RenderResource()).temp_files.add(file_path)

    def add_process(self, task_id: str, pid: int) -> None:
        if not task_id or pid is None:
            return
        try:
            pid_int = int(pid)
        except Exception:
            return
        with self._lock:
            self._resources.setdefault(task_id, RenderResource()).process_ids.add(pid_int)

    def get_resource_usage(self, task_id: str) -> Optional[dict]:
        if not task_id:
            return None
        with self._lock:
            resources = self._resources.get(task_id)
            if resources is None or task_id not in self._progress:
                return None
            return {
                "temp_files_count": len(resources.temp_files),
                "active_processes": len(resources.process_ids),
            }

    def cleanup_task(self, task_id: str) -> bool:
        if not task_id:
            return True

        with self._lock:
            resources = self._resources.pop(task_id, None)
            self._progress.pop(task_id, None)
            self._cancelled.discard(task_id)
            self._progress_callbacks.pop(task_id, None)

        logger.info(f"Cleaning up resources for task {task_id}")

        if resources is None:
            return True

        for file_path in list(resources.temp_files):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                continue

        for pid in list(resources.process_ids):
            try:
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    process.terminate()
            except Exception:
                continue

        return True

    def register_progress_callback(self, task_id: str, callback) -> bool:
        if not task_id or callback is None:
            return False
        with self._lock:
            if task_id not in self._progress:
                return False
            self._progress_callbacks.setdefault(task_id, []).append(callback)
            return True

    def get_active_tasks(self) -> list:
        with self._lock:
            return [
                task_id
                for task_id, progress in self._progress.items()
                if progress.status in {RenderStatus.PENDING, RenderStatus.PROCESSING}
            ]


def _ensure_backend_alias() -> None:
    import sys
    import types

    module = sys.modules[__name__]

    backend = sys.modules.get("backend")
    if backend is None:
        backend = types.ModuleType("backend")
        backend.__path__ = []
        sys.modules["backend"] = backend

    backend_services = sys.modules.get("backend.services")
    if backend_services is None:
        backend_services = types.ModuleType("backend.services")
        backend_services.__path__ = []
        sys.modules["backend.services"] = backend_services

    sys.modules.setdefault("backend.services.render_state_manager", module)


_ensure_backend_alias()
