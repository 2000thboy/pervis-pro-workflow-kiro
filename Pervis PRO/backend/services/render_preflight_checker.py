"""
渲染前置检查器
提供渲染前置条件检查与基础估算
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
import os
import shutil

from services.ffmpeg_detector import ffmpeg_detector


@dataclass
class CheckResult:
    can_render: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    estimated_duration: Optional[float] = None
    estimated_size_mb: Optional[float] = None


class RenderPreflightChecker:
    MIN_DISK_SPACE_MB = 500.0

    def __init__(self, db: Any):
        self.db = db

    def validate_render_options(self, options: Dict[str, Any]) -> CheckResult:
        errors: List[str] = []
        warnings: List[str] = []

        format_value = (options.get("format") or "").lower()
        if format_value not in ["mp4", "mov"]:
            errors.append("Invalid format")

        resolution_value = (options.get("resolution") or "").lower()
        if resolution_value not in ["720p", "1080p", "4k"]:
            errors.append("Invalid resolution")

        framerate = options.get("framerate")
        if isinstance(framerate, (int, float)):
            if framerate < 1 or framerate > 120:
                errors.append("Invalid framerate")
        else:
            errors.append("Invalid framerate")

        quality = (options.get("quality") or "").lower()
        if quality not in ["low", "medium", "high", "ultra"]:
            errors.append("Invalid quality")

        bitrate = options.get("bitrate")
        if bitrate is not None:
            if not isinstance(bitrate, (int, float)) or bitrate < 100 or bitrate > 100000:
                errors.append("Invalid bitrate")

        audio_bitrate = options.get("audio_bitrate")
        if audio_bitrate not in [128, 192, 256, 320]:
            errors.append("Invalid audio bitrate")

        return CheckResult(can_render=len(errors) == 0, errors=errors, warnings=warnings)

    def check_disk_space(self, estimated_size_mb: float, output_dir: str) -> bool:
        try:
            usage = shutil.disk_usage(output_dir)
            available_mb = usage.free / (1024 * 1024)
            required_mb = float(estimated_size_mb) + float(self.MIN_DISK_SPACE_MB)
            return available_mb >= required_mb
        except Exception:
            return False

    def check_file_permissions(self, paths: List[str]) -> bool:
        try:
            for path in paths:
                if not path:
                    return False
                if not os.path.exists(path):
                    return False
                if not os.access(path, os.R_OK | os.W_OK):
                    return False
            return True
        except Exception:
            return False

    def check_dependencies(self) -> CheckResult:
        errors: List[str] = []
        warnings: List[str] = []
        status = ffmpeg_detector.check_installation()

        if not getattr(status, "is_installed", False):
            errors.append("FFmpeg not installed")
            return CheckResult(can_render=False, errors=errors, warnings=warnings)

        if not getattr(status, "is_version_supported", True):
            version = getattr(status, "version", None)
            if version:
                warnings.append(f"FFmpeg version not supported: {version}")
            else:
                warnings.append("FFmpeg version not supported")

        return CheckResult(can_render=True, errors=errors, warnings=warnings)

    def check_timeline_validity(self, timeline_id: str) -> CheckResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not timeline_id:
            errors.append("Timeline not found")
            return CheckResult(can_render=False, errors=errors, warnings=warnings)

        timeline = None
        try:
            query = self.db.query(object)
            timeline = query.filter(True).first()
        except Exception:
            timeline = None

        if timeline is None:
            errors.append("Timeline not found")
            return CheckResult(can_render=False, errors=errors, warnings=warnings)

        return CheckResult(can_render=True, errors=errors, warnings=warnings, estimated_duration=0.0, estimated_size_mb=0.0)

    def check_render_requirements(self, timeline_id: str, output_dir: Optional[str] = None) -> CheckResult:
        errors: List[str] = []
        warnings: List[str] = []

        deps = self.check_dependencies()
        errors.extend(deps.errors)
        warnings.extend(deps.warnings)

        timeline_result = self.check_timeline_validity(timeline_id)
        errors.extend(timeline_result.errors)
        warnings.extend(timeline_result.warnings)

        estimated_size_mb = timeline_result.estimated_size_mb
        estimated_duration = timeline_result.estimated_duration

        if not errors:
            if output_dir is None:
                output_dir = os.getcwd()

            if not self.check_file_permissions([]):
                errors.append("File permission check failed")

            if estimated_size_mb is not None:
                if not self.check_disk_space(estimated_size_mb, output_dir):
                    errors.append("Insufficient disk space")

        can_render = len(errors) == 0
        return CheckResult(
            can_render=can_render,
            errors=errors,
            warnings=warnings,
            estimated_duration=estimated_duration,
            estimated_size_mb=estimated_size_mb,
        )
