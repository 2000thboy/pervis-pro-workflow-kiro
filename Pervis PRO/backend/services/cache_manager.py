# -*- coding: utf-8 -*-
"""
缓存管理服务

Feature: pervis-export-system
Task: 1.2 实现 CacheManager 缓存管理器

功能：
- 缩略图缓存管理
- 代理文件缓存管理
- LRU 缓存清理策略
- 素材可用性检查
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================

@dataclass
class CacheConfig:
    """缓存配置"""
    # 缓存目录
    cache_root: str = "data/cache"
    thumbnail_dir: str = "thumbnails"
    proxy_dir: str = "proxies"
    temp_dir: str = "temp"
    
    # 缓存大小限制 (MB)
    max_thumbnail_cache_mb: int = 500
    max_proxy_cache_mb: int = 2000
    max_temp_cache_mb: int = 200
    
    # 缓存过期时间 (天)
    thumbnail_expire_days: int = 30
    proxy_expire_days: int = 7
    temp_expire_days: int = 1
    
    # 缩略图设置
    thumbnail_width: int = 320
    thumbnail_height: int = 180
    thumbnail_format: str = "jpg"
    thumbnail_quality: int = 85
    
    # 代理文件设置
    proxy_resolution: str = "720p"
    proxy_bitrate: str = "2000k"
    proxy_format: str = "mp4"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    path: str
    size: int
    created_at: datetime
    accessed_at: datetime
    source_path: str = ""
    source_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# 缓存管理器
# ============================================================

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        # 缓存目录
        self.cache_root = Path(self.config.cache_root)
        self.thumbnail_path = self.cache_root / self.config.thumbnail_dir
        self.proxy_path = self.cache_root / self.config.proxy_dir
        self.temp_path = self.cache_root / self.config.temp_dir
        
        # 缓存索引
        self._thumbnail_index: Dict[str, CacheEntry] = {}
        self._proxy_index: Dict[str, CacheEntry] = {}
        
        # 索引文件路径
        self._index_file = self.cache_root / "cache_index.json"
        
        # 初始化目录
        self._ensure_directories()
        self._load_index()
    
    def _ensure_directories(self):
        """确保缓存目录存在"""
        for path in [self.thumbnail_path, self.proxy_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """加载缓存索引"""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for key, entry_data in data.get("thumbnails", {}).items():
                    self._thumbnail_index[key] = CacheEntry(
                        key=key,
                        path=entry_data["path"],
                        size=entry_data["size"],
                        created_at=datetime.fromisoformat(entry_data["created_at"]),
                        accessed_at=datetime.fromisoformat(entry_data["accessed_at"]),
                        source_path=entry_data.get("source_path", ""),
                        source_hash=entry_data.get("source_hash", ""),
                    )
                
                for key, entry_data in data.get("proxies", {}).items():
                    self._proxy_index[key] = CacheEntry(
                        key=key,
                        path=entry_data["path"],
                        size=entry_data["size"],
                        created_at=datetime.fromisoformat(entry_data["created_at"]),
                        accessed_at=datetime.fromisoformat(entry_data["accessed_at"]),
                        source_path=entry_data.get("source_path", ""),
                        source_hash=entry_data.get("source_hash", ""),
                    )
                
                logger.info(f"缓存索引已加载: {len(self._thumbnail_index)} 缩略图, {len(self._proxy_index)} 代理")
            except Exception as e:
                logger.warning(f"加载缓存索引失败: {e}")
    
    def _save_index(self):
        """保存缓存索引"""
        try:
            data = {
                "thumbnails": {
                    key: {
                        "path": entry.path,
                        "size": entry.size,
                        "created_at": entry.created_at.isoformat(),
                        "accessed_at": entry.accessed_at.isoformat(),
                        "source_path": entry.source_path,
                        "source_hash": entry.source_hash,
                    }
                    for key, entry in self._thumbnail_index.items()
                },
                "proxies": {
                    key: {
                        "path": entry.path,
                        "size": entry.size,
                        "created_at": entry.created_at.isoformat(),
                        "accessed_at": entry.accessed_at.isoformat(),
                        "source_path": entry.source_path,
                        "source_hash": entry.source_hash,
                    }
                    for key, entry in self._proxy_index.items()
                },
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存索引失败: {e}")
    
    def _get_cache_key(self, source_path: str, cache_type: str = "thumbnail") -> str:
        """生成缓存键"""
        # 使用文件路径和修改时间生成唯一键
        try:
            stat = os.stat(source_path)
            content = f"{source_path}:{stat.st_size}:{stat.st_mtime}:{cache_type}"
        except:
            content = f"{source_path}:{cache_type}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_source_hash(self, source_path: str) -> str:
        """获取源文件哈希"""
        try:
            stat = os.stat(source_path)
            content = f"{stat.st_size}:{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except:
            return ""
    
    # ============================================================
    # 缩略图缓存
    # ============================================================
    
    async def ensure_thumbnail(
        self,
        source_path: str,
        timestamp: float = 0.0,
        force: bool = False,
    ) -> Optional[str]:
        """
        确保缩略图存在
        
        Args:
            source_path: 源视频路径
            timestamp: 提取帧的时间戳（秒）
            force: 是否强制重新生成
            
        Returns:
            缩略图路径，失败返回 None
        """
        if not os.path.exists(source_path):
            logger.error(f"源文件不存在: {source_path}")
            return None
        
        cache_key = self._get_cache_key(source_path, f"thumb_{timestamp}")
        
        # 检查缓存
        if not force and cache_key in self._thumbnail_index:
            entry = self._thumbnail_index[cache_key]
            if os.path.exists(entry.path):
                # 更新访问时间
                entry.accessed_at = datetime.now()
                return entry.path
        
        # 生成缩略图
        try:
            from .ffmpeg_wrapper import FFmpegWrapper
            
            ffmpeg = FFmpegWrapper()
            
            # 生成输出路径
            ext = self.config.thumbnail_format
            output_path = str(self.thumbnail_path / f"{cache_key}.{ext}")
            
            # 提取帧
            success = ffmpeg.extract_frame(
                source_path,
                output_path,
                timestamp=timestamp,
                width=self.config.thumbnail_width,
                height=self.config.thumbnail_height,
            )
            
            if success and os.path.exists(output_path):
                # 添加到索引
                self._thumbnail_index[cache_key] = CacheEntry(
                    key=cache_key,
                    path=output_path,
                    size=os.path.getsize(output_path),
                    created_at=datetime.now(),
                    accessed_at=datetime.now(),
                    source_path=source_path,
                    source_hash=self._get_source_hash(source_path),
                )
                self._save_index()
                
                return output_path
            
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
        
        return None
    
    def get_thumbnail(self, source_path: str, timestamp: float = 0.0) -> Optional[str]:
        """获取缩略图路径（不生成）"""
        cache_key = self._get_cache_key(source_path, f"thumb_{timestamp}")
        
        if cache_key in self._thumbnail_index:
            entry = self._thumbnail_index[cache_key]
            if os.path.exists(entry.path):
                entry.accessed_at = datetime.now()
                return entry.path
        
        return None

    
    # ============================================================
    # 代理文件缓存
    # ============================================================
    
    async def ensure_proxy(
        self,
        source_path: str,
        force: bool = False,
    ) -> Optional[str]:
        """
        确保代理文件存在
        
        Args:
            source_path: 源视频路径
            force: 是否强制重新生成
            
        Returns:
            代理文件路径，失败返回 None
        """
        if not os.path.exists(source_path):
            logger.error(f"源文件不存在: {source_path}")
            return None
        
        cache_key = self._get_cache_key(source_path, "proxy")
        
        # 检查缓存
        if not force and cache_key in self._proxy_index:
            entry = self._proxy_index[cache_key]
            if os.path.exists(entry.path):
                entry.accessed_at = datetime.now()
                return entry.path
        
        # 生成代理文件
        try:
            from .ffmpeg_wrapper import FFmpegWrapper
            
            ffmpeg = FFmpegWrapper()
            
            # 生成输出路径
            ext = self.config.proxy_format
            output_path = str(self.proxy_path / f"{cache_key}.{ext}")
            
            # 转码为代理
            success = ffmpeg.create_proxy(
                source_path,
                output_path,
                resolution=self.config.proxy_resolution,
                bitrate=self.config.proxy_bitrate,
            )
            
            if success and os.path.exists(output_path):
                self._proxy_index[cache_key] = CacheEntry(
                    key=cache_key,
                    path=output_path,
                    size=os.path.getsize(output_path),
                    created_at=datetime.now(),
                    accessed_at=datetime.now(),
                    source_path=source_path,
                    source_hash=self._get_source_hash(source_path),
                )
                self._save_index()
                
                return output_path
            
        except Exception as e:
            logger.error(f"生成代理文件失败: {e}")
        
        return None
    
    def get_proxy(self, source_path: str) -> Optional[str]:
        """获取代理文件路径（不生成）"""
        cache_key = self._get_cache_key(source_path, "proxy")
        
        if cache_key in self._proxy_index:
            entry = self._proxy_index[cache_key]
            if os.path.exists(entry.path):
                entry.accessed_at = datetime.now()
                return entry.path
        
        return None
    
    # ============================================================
    # 素材可用性检查
    # ============================================================
    
    def verify_asset_availability(self, asset_path: str) -> Dict[str, Any]:
        """
        验证素材可用性
        
        Args:
            asset_path: 素材文件路径
            
        Returns:
            可用性检查结果
        """
        result = {
            "path": asset_path,
            "exists": False,
            "readable": False,
            "size": 0,
            "has_thumbnail": False,
            "has_proxy": False,
            "errors": [],
        }
        
        # 检查文件存在
        if not os.path.exists(asset_path):
            result["errors"].append("文件不存在")
            return result
        
        result["exists"] = True
        
        # 检查可读性
        try:
            with open(asset_path, "rb") as f:
                f.read(1024)
            result["readable"] = True
        except Exception as e:
            result["errors"].append(f"文件不可读: {e}")
            return result
        
        # 获取文件大小
        try:
            result["size"] = os.path.getsize(asset_path)
        except:
            pass
        
        # 检查缩略图
        result["has_thumbnail"] = self.get_thumbnail(asset_path) is not None
        
        # 检查代理
        result["has_proxy"] = self.get_proxy(asset_path) is not None
        
        return result
    
    def verify_assets_batch(self, asset_paths: List[str]) -> Dict[str, Any]:
        """批量验证素材可用性"""
        results = {
            "total": len(asset_paths),
            "available": 0,
            "missing": 0,
            "errors": [],
            "details": [],
        }
        
        for path in asset_paths:
            check = self.verify_asset_availability(path)
            results["details"].append(check)
            
            if check["exists"] and check["readable"]:
                results["available"] += 1
            else:
                results["missing"] += 1
                results["errors"].extend(check["errors"])
        
        return results
    
    # ============================================================
    # 缓存清理
    # ============================================================
    
    def cleanup_expired(self) -> Dict[str, int]:
        """清理过期缓存"""
        cleaned = {"thumbnails": 0, "proxies": 0, "temp": 0}
        
        now = datetime.now()
        
        # 清理过期缩略图
        thumb_expire = timedelta(days=self.config.thumbnail_expire_days)
        expired_thumbs = [
            key for key, entry in self._thumbnail_index.items()
            if now - entry.accessed_at > thumb_expire
        ]
        
        for key in expired_thumbs:
            entry = self._thumbnail_index.pop(key)
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
                    cleaned["thumbnails"] += 1
            except:
                pass
        
        # 清理过期代理
        proxy_expire = timedelta(days=self.config.proxy_expire_days)
        expired_proxies = [
            key for key, entry in self._proxy_index.items()
            if now - entry.accessed_at > proxy_expire
        ]
        
        for key in expired_proxies:
            entry = self._proxy_index.pop(key)
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
                    cleaned["proxies"] += 1
            except:
                pass
        
        # 清理临时文件
        temp_expire = timedelta(days=self.config.temp_expire_days)
        for file in self.temp_path.iterdir():
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if now - mtime > temp_expire:
                    file.unlink()
                    cleaned["temp"] += 1
            except:
                pass
        
        self._save_index()
        
        logger.info(f"缓存清理完成: {cleaned}")
        return cleaned
    
    def cleanup_lru(self, cache_type: str = "thumbnail", target_mb: int = None) -> int:
        """
        LRU 缓存清理
        
        Args:
            cache_type: 缓存类型 (thumbnail, proxy)
            target_mb: 目标大小 (MB)，None 使用配置值
            
        Returns:
            清理的文件数
        """
        if cache_type == "thumbnail":
            index = self._thumbnail_index
            max_mb = target_mb or self.config.max_thumbnail_cache_mb
        elif cache_type == "proxy":
            index = self._proxy_index
            max_mb = target_mb or self.config.max_proxy_cache_mb
        else:
            return 0
        
        # 计算当前大小
        current_size = sum(entry.size for entry in index.values())
        max_size = max_mb * 1024 * 1024
        
        if current_size <= max_size:
            return 0
        
        # 按访问时间排序（最旧的在前）
        sorted_entries = sorted(
            index.items(),
            key=lambda x: x[1].accessed_at
        )
        
        cleaned = 0
        
        for key, entry in sorted_entries:
            if current_size <= max_size:
                break
            
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
                current_size -= entry.size
                del index[key]
                cleaned += 1
            except:
                pass
        
        self._save_index()
        
        logger.info(f"LRU 清理 {cache_type}: 删除 {cleaned} 个文件")
        return cleaned
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        thumb_size = sum(e.size for e in self._thumbnail_index.values())
        proxy_size = sum(e.size for e in self._proxy_index.values())
        
        return {
            "thumbnails": {
                "count": len(self._thumbnail_index),
                "size_mb": round(thumb_size / 1024 / 1024, 2),
                "max_mb": self.config.max_thumbnail_cache_mb,
            },
            "proxies": {
                "count": len(self._proxy_index),
                "size_mb": round(proxy_size / 1024 / 1024, 2),
                "max_mb": self.config.max_proxy_cache_mb,
            },
            "paths": {
                "cache_root": str(self.cache_root),
                "thumbnail_dir": str(self.thumbnail_path),
                "proxy_dir": str(self.proxy_path),
                "temp_dir": str(self.temp_path),
            },
        }
    
    def clear_all(self) -> Dict[str, int]:
        """清空所有缓存"""
        cleared = {"thumbnails": 0, "proxies": 0, "temp": 0}
        
        # 清空缩略图
        for key, entry in list(self._thumbnail_index.items()):
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
                    cleared["thumbnails"] += 1
            except:
                pass
        self._thumbnail_index.clear()
        
        # 清空代理
        for key, entry in list(self._proxy_index.items()):
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
                    cleared["proxies"] += 1
            except:
                pass
        self._proxy_index.clear()
        
        # 清空临时文件
        for file in self.temp_path.iterdir():
            try:
                file.unlink()
                cleared["temp"] += 1
            except:
                pass
        
        self._save_index()
        
        logger.info(f"缓存已清空: {cleared}")
        return cleared


# ============================================================
# 全局实例
# ============================================================

_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager
