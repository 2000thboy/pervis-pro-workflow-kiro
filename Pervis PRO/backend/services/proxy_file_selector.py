from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, Iterable, List, Optional

from database import Asset, ProxyFile

logger = logging.getLogger(__name__)


class ProxyMode(str, Enum):
    ORIGINAL = "original"
    PROXY = "proxy"
    AUTO = "auto"
    SMART = "smart"


@dataclass
class ProxySelectionCriteria:
    target_resolution: Optional[str] = None
    performance_priority: bool = False
    quality_threshold: float = 0.7


@dataclass
class FileSelectionResult:
    asset_id: str
    selected_path: str
    is_proxy: bool
    proxy_path: Optional[str] = None
    selection_reason: str = ""
    performance_impact: str = "low"
    quality_impact: str = "none"


def _resolution_to_height(resolution: Optional[str]) -> int:
    if not resolution:
        return 0
    r = str(resolution).strip().lower()
    if r.endswith("p"):
        try:
            return int(r[:-1])
        except Exception:
            return 0
    if r == "4k":
        return 2160
    if r == "8k":
        return 4320
    return 0


def _estimate_performance_impact(file_size: Any) -> str:
    if not isinstance(file_size, (int, float)) or file_size < 0:
        return "high"
    if file_size < 5 * 1024 * 1024:
        return "low"
    if file_size < 50 * 1024 * 1024:
        return "medium"
    return "high"


class ProxyFileSelector:
    def __init__(self, db):
        self.db = db

    def select_file(
        self,
        asset_id: Optional[str],
        mode: ProxyMode,
        criteria: Optional[ProxySelectionCriteria] = None,
    ) -> Optional[FileSelectionResult]:
        if not asset_id or not str(asset_id).strip():
            return None

        asset = self._get_asset(str(asset_id))
        if asset is None:
            return None

        original_path = getattr(asset, "file_path", None) or getattr(asset, "original_path", None)
        original_size = getattr(asset, "file_size", None)
        if not original_path:
            return None

        proxies = self._get_proxies(str(asset_id))
        if mode == ProxyMode.ORIGINAL:
            return self._original_result(str(asset_id), original_path, original_size, "ORIGINAL模式选择原始文件")

        if mode == ProxyMode.PROXY:
            best_proxy = self._pick_best_proxy(proxies, criteria)
            if best_proxy is None:
                return self._original_result(
                    str(asset_id), original_path, original_size, "没有可用的代理文件，回退到原始文件"
                )
            return self._proxy_result(str(asset_id), best_proxy, "PROXY模式选择代理文件")

        if mode == ProxyMode.AUTO:
            return self._auto_select(str(asset_id), asset, original_path, proxies)

        if mode == ProxyMode.SMART:
            criteria = criteria or ProxySelectionCriteria()
            return self._smart_select(str(asset_id), asset, original_path, proxies, criteria)

        return self._original_result(str(asset_id), original_path, original_size, "未知模式，回退到原始文件")

    def batch_select_files(
        self,
        asset_ids: Iterable[str],
        mode: ProxyMode,
        criteria: Optional[ProxySelectionCriteria] = None,
    ) -> Dict[str, FileSelectionResult]:
        results: Dict[str, FileSelectionResult] = {}
        for asset_id in asset_ids:
            result = self.select_file(asset_id, mode, criteria)
            if result is not None:
                results[str(asset_id)] = result
        return results

    def get_selection_summary(self, asset_id: str) -> dict:
        asset = self._get_asset(asset_id)
        proxies = self._get_proxies(asset_id)

        original_path = None
        original_size = None
        if asset is not None:
            original_path = getattr(asset, "file_path", None) or getattr(asset, "original_path", None)
            original_size = getattr(asset, "file_size", None)

        proxy_entries = []
        for p in proxies:
            proxy_entries.append(
                {
                    "proxy_path": getattr(p, "proxy_path", None),
                    "resolution": getattr(p, "resolution", None),
                    "file_size": getattr(p, "file_size", None),
                    "status": getattr(p, "status", None),
                }
            )

        recommendations = {
            "preview": {"mode": ProxyMode.AUTO.value, "target_resolution": "720p"},
            "editing": {"mode": ProxyMode.SMART.value, "target_resolution": "1080p"},
            "final_render": {"mode": ProxyMode.ORIGINAL.value},
        }

        return {
            "asset_id": asset_id,
            "original_file": {"path": original_path, "file_size": original_size},
            "proxy_files": proxy_entries,
            "recommendations": recommendations,
        }

    def optimize_selection_criteria(
        self, target_output: Dict[str, Any], system_resources: Dict[str, Any]
    ) -> ProxySelectionCriteria:
        resolution = target_output.get("resolution") if target_output else None
        quality = (target_output.get("quality") if target_output else None) or "medium"
        available_ram_gb = float(system_resources.get("available_ram_gb", 0) or 0)

        criteria = ProxySelectionCriteria(target_resolution=resolution)
        if available_ram_gb and available_ram_gb < 8:
            criteria.performance_priority = True

        if str(quality).lower() in {"high", "ultra"}:
            criteria.quality_threshold = 0.85
        elif str(quality).lower() in {"low"}:
            criteria.quality_threshold = 0.5
        else:
            criteria.quality_threshold = 0.7

        return criteria

    def _get_asset(self, asset_id: str):
        if hasattr(self.db, "assets") and isinstance(getattr(self.db, "assets"), dict):
            return self.db.assets.get(asset_id)
        try:
            return self.db.query(Asset).filter(Asset.id == asset_id).first()
        except Exception:
            return None

    def _get_proxies(self, asset_id: str) -> List[Any]:
        if hasattr(self.db, "proxy_files") and isinstance(getattr(self.db, "proxy_files"), dict):
            proxies = list(self.db.proxy_files.get(asset_id, []))
            return [p for p in proxies if getattr(p, "status", "completed") == "completed"]
        try:
            return (
                self.db.query(ProxyFile)
                .filter(ProxyFile.asset_id == asset_id, ProxyFile.status == "completed")
                .all()
            )
        except Exception:
            return []

    def _pick_best_proxy(self, proxies: List[Any], criteria: Optional[ProxySelectionCriteria]):
        if not proxies:
            return None
        if not criteria or not criteria.target_resolution:
            return sorted(proxies, key=lambda p: _resolution_to_height(getattr(p, "resolution", None)))[-1]

        target_h = _resolution_to_height(criteria.target_resolution)
        scored = []
        for p in proxies:
            h = _resolution_to_height(getattr(p, "resolution", None))
            scored.append((abs(h - target_h), -h, p))
        scored.sort(key=lambda x: (x[0], x[1]))
        return scored[0][2]

    def _original_result(
        self, asset_id: str, original_path: str, original_size: Any, reason: str
    ) -> FileSelectionResult:
        return FileSelectionResult(
            asset_id=asset_id,
            selected_path=original_path,
            is_proxy=False,
            proxy_path=None,
            selection_reason=reason,
            performance_impact=_estimate_performance_impact(original_size),
            quality_impact="none",
        )

    def _proxy_result(self, asset_id: str, proxy: Any, reason: str) -> FileSelectionResult:
        return FileSelectionResult(
            asset_id=asset_id,
            selected_path=getattr(proxy, "proxy_path", ""),
            is_proxy=True,
            proxy_path=getattr(proxy, "proxy_path", None),
            selection_reason=reason,
            performance_impact="low",
            quality_impact="minimal",
        )

    def _auto_select(self, asset_id: str, asset: Any, original_path: str, proxies: List[Any]):
        if not proxies:
            return self._original_result(
                asset_id, original_path, getattr(asset, "file_size", None), "AUTO模式无代理文件，选择原始文件"
            )

        original_size = getattr(asset, "file_size", None)
        if original_size is None:
            return self._proxy_result(asset_id, self._pick_best_proxy(proxies, None), "AUTO模式缺少大小信息，选择代理文件")

        best_proxy = self._pick_best_proxy(proxies, None)
        proxy_size = getattr(best_proxy, "file_size", None) if best_proxy else None

        if isinstance(original_size, (int, float)) and original_size >= 50 * 1024 * 1024:
            if best_proxy is not None:
                return self._proxy_result(asset_id, best_proxy, "AUTO模式大文件，优先代理文件")

        if (
            best_proxy is not None
            and isinstance(proxy_size, (int, float))
            and proxy_size < original_size
            and original_size > 2 * 1024 * 1024
            and (proxy_size / max(original_size, 1)) < 0.7
        ):
            return self._proxy_result(asset_id, best_proxy, "AUTO模式根据大小与性能选择代理文件")

        return self._original_result(asset_id, original_path, original_size, "AUTO模式选择原始文件")

    def _smart_select(
        self,
        asset_id: str,
        asset: Any,
        original_path: str,
        proxies: List[Any],
        criteria: ProxySelectionCriteria,
    ):
        if not proxies:
            return self._original_result(
                asset_id, original_path, getattr(asset, "file_size", None), "SMART模式无代理文件，选择原始文件"
            )

        best_proxy = self._pick_best_proxy(proxies, criteria)
        if best_proxy is None:
            return self._original_result(
                asset_id, original_path, getattr(asset, "file_size", None), "SMART模式未找到合适代理文件，选择原始文件"
            )

        if criteria.performance_priority:
            return self._proxy_result(asset_id, best_proxy, "SMART模式性能优先，选择代理文件")

        target_h = _resolution_to_height(criteria.target_resolution) if criteria.target_resolution else 0
        proxy_h = _resolution_to_height(getattr(best_proxy, "resolution", None))
        if target_h and proxy_h and proxy_h >= int(target_h * float(criteria.quality_threshold or 0.0)):
            result = self._proxy_result(asset_id, best_proxy, "SMART模式匹配目标分辨率，选择代理文件")
            result.quality_impact = "minimal"
            return result

        return self._original_result(
            asset_id, original_path, getattr(asset, "file_size", None), "SMART模式质量不足，选择原始文件"
        )
