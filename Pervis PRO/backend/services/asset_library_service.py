# -*- coding: utf-8 -*-
"""
素材库管理服务

扩展现有 DAM 系统，提供素材库的 CRUD 操作和管理功能：
- 添加/编辑/删除素材库
- 扫描素材库
- 索引素材库（与现有 Asset 表集成）
- 项目关联管理
- 网络路径验证

与现有系统集成：
- 使用 database.py 中的 Asset 模型
- 使用 search_service.py 进行向量搜索
- 使用 batch_asset_indexing.py 进行批量索引

Requirements: 素材库管理系统
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# 默认支持的视频扩展名
DEFAULT_VIDEO_EXTENSIONS = [
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".mts", ".m2ts"
]

# 默认支持的图片扩展名
DEFAULT_IMAGE_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif",
    ".psd", ".ai", ".eps", ".svg"
]

# 默认支持的音频扩展名
DEFAULT_AUDIO_EXTENSIONS = [
    ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"
]


@dataclass
class ScanResult:
    """扫描结果"""
    total_files: int = 0
    video_files: int = 0
    image_files: int = 0
    audio_files: int = 0
    other_files: int = 0
    total_size_bytes: int = 0
    directories: List[str] = field(default_factory=list)
    file_list: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scan_duration_ms: float = 0
    # 与现有 Asset 表的关联
    existing_assets: int = 0  # 已在数据库中的素材数
    new_assets: int = 0  # 新发现的素材数
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "video_files": self.video_files,
            "image_files": self.image_files,
            "audio_files": self.audio_files,
            "other_files": self.other_files,
            "total_size_bytes": self.total_size_bytes,
            "total_size_display": self._format_size(self.total_size_bytes),
            "directories_count": len(self.directories),
            "errors_count": len(self.errors),
            "scan_duration_ms": self.scan_duration_ms,
            "existing_assets": self.existing_assets,
            "new_assets": self.new_assets,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.2f} {units[i]}"


class AssetLibraryService:
    """素材库管理服务"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def set_db(self, db: Session):
        """设置数据库会话"""
        self.db = db
    
    # ========================================
    # 素材库 CRUD 操作
    # ========================================
    
    def create_library(
        self,
        name: str,
        path: str,
        description: str = None,
        path_type: str = "local",
        network_host: str = None,
        network_share: str = None,
        is_default: bool = False,
        scan_subdirs: bool = True,
        file_extensions: List[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        创建素材库
        
        Args:
            name: 库名称
            path: 库路径
            description: 描述
            path_type: 路径类型 (local/network/smb/nfs)
            network_host: 网络主机
            network_share: 共享名称
            is_default: 是否为默认库
            scan_subdirs: 是否扫描子目录
            file_extensions: 支持的文件扩展名
            tags: 库标签
        """
        from models.asset_library import AssetLibrary
        
        # 验证路径
        path_valid, path_error = self.validate_path(path, path_type)
        if not path_valid:
            return {"success": False, "error": path_error}
        
        # 如果设为默认，取消其他默认库
        if is_default and self.db:
            self.db.query(AssetLibrary).filter(
                AssetLibrary.is_default == True
            ).update({"is_default": False})
        
        # 创建库
        library = AssetLibrary(
            name=name,
            path=path,
            description=description,
            path_type=path_type,
            network_host=network_host,
            network_share=network_share,
            is_default=is_default,
            scan_subdirs=scan_subdirs,
            file_extensions=file_extensions or DEFAULT_VIDEO_EXTENSIONS,
            tags=tags or []
        )
        
        if self.db:
            self.db.add(library)
            self.db.commit()
            self.db.refresh(library)
            return {"success": True, "library": library.to_dict()}
        
        return {"success": True, "library": {"name": name, "path": path}}
    
    def get_library(self, library_id: int) -> Optional[Dict[str, Any]]:
        """获取素材库详情"""
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return None
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        return library.to_dict() if library else None
    
    def list_libraries(
        self,
        active_only: bool = False,
        include_stats: bool = True
    ) -> List[Dict[str, Any]]:
        """列出所有素材库"""
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return []
        
        query = self.db.query(AssetLibrary)
        
        if active_only:
            query = query.filter(AssetLibrary.is_active == True)
        
        libraries = query.order_by(AssetLibrary.is_default.desc(), AssetLibrary.name).all()
        
        result = []
        for lib in libraries:
            lib_dict = lib.to_dict()
            if include_stats:
                lib_dict["is_accessible"] = self.check_path_accessible(lib.path)
            result.append(lib_dict)
        
        return result

    def update_library(
        self,
        library_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """更新素材库"""
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return {"success": False, "error": "素材库不存在"}
        
        # 如果更新路径，验证新路径
        if "path" in kwargs:
            path_type = kwargs.get("path_type", library.path_type)
            path_valid, path_error = self.validate_path(kwargs["path"], path_type)
            if not path_valid:
                return {"success": False, "error": path_error}
        
        # 如果设为默认，取消其他默认库
        if kwargs.get("is_default"):
            self.db.query(AssetLibrary).filter(
                AssetLibrary.id != library_id,
                AssetLibrary.is_default == True
            ).update({"is_default": False})
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(library, key):
                setattr(library, key, value)
        
        library.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(library)
        
        return {"success": True, "library": library.to_dict()}
    
    def delete_library(self, library_id: int) -> Dict[str, Any]:
        """删除素材库"""
        from models.asset_library import AssetLibrary, ProjectLibraryMapping
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return {"success": False, "error": "素材库不存在"}
        
        # 删除项目关联
        self.db.query(ProjectLibraryMapping).filter(
            ProjectLibraryMapping.library_id == library_id
        ).delete()
        
        # 删除库
        self.db.delete(library)
        self.db.commit()
        
        return {"success": True, "message": f"素材库 '{library.name}' 已删除"}
    
    # ========================================
    # 路径验证
    # ========================================
    
    def validate_path(self, path: str, path_type: str = "local") -> Tuple[bool, str]:
        """
        验证路径是否有效
        
        Returns:
            (is_valid, error_message)
        """
        if not path:
            return False, "路径不能为空"
        
        # 标准化路径
        path = os.path.normpath(path)
        
        if path_type == "local":
            # 本地路径验证
            if not os.path.exists(path):
                return False, f"路径不存在: {path}"
            if not os.path.isdir(path):
                return False, f"路径不是目录: {path}"
            if not os.access(path, os.R_OK):
                return False, f"路径无读取权限: {path}"
            return True, ""
        
        elif path_type in ("network", "smb", "nfs"):
            # 网络路径验证 (UNC 路径: \\server\share)
            if path.startswith("\\\\") or path.startswith("//"):
                try:
                    if os.path.exists(path):
                        return True, ""
                    else:
                        return False, f"网络路径不可访问: {path}"
                except Exception as e:
                    return False, f"网络路径验证失败: {e}"
            
            # 映射驱动器路径 (如 Z:\)
            if len(path) >= 2 and path[1] == ":":
                if os.path.exists(path):
                    return True, ""
                else:
                    return False, f"映射驱动器路径不可访问: {path}"
            
            return False, f"无效的网络路径格式: {path}"
        
        return False, f"不支持的路径类型: {path_type}"
    
    def check_path_accessible(self, path: str) -> bool:
        """检查路径是否可访问"""
        try:
            return os.path.exists(path) and os.access(path, os.R_OK)
        except Exception:
            return False
    
    # ========================================
    # 扫描功能
    # ========================================
    
    def scan_library(
        self,
        library_id: int,
        max_files: int = None,
        update_stats: bool = True
    ) -> ScanResult:
        """
        扫描素材库
        
        Args:
            library_id: 素材库ID
            max_files: 最大扫描文件数（用于预览）
            update_stats: 是否更新数据库统计
        """
        from models.asset_library import AssetLibrary
        
        result = ScanResult()
        start_time = datetime.now()
        
        if not self.db:
            result.errors.append("数据库未连接")
            return result
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            result.errors.append("素材库不存在")
            return result
        
        if not self.check_path_accessible(library.path):
            result.errors.append(f"路径不可访问: {library.path}")
            return result
        
        # 获取支持的扩展名
        extensions = set(library.file_extensions or DEFAULT_VIDEO_EXTENSIONS)
        exclude_patterns = library.exclude_patterns or []
        
        # 扫描文件
        try:
            for root, dirs, files in os.walk(library.path):
                # 检查是否应该排除此目录
                rel_path = os.path.relpath(root, library.path)
                if any(pattern in rel_path for pattern in exclude_patterns):
                    continue
                
                # 记录目录
                if rel_path != ".":
                    result.directories.append(rel_path)
                
                for filename in files:
                    # 检查最大文件数限制
                    if max_files and result.total_files >= max_files:
                        break
                    
                    ext = os.path.splitext(filename)[1].lower()
                    file_path = os.path.join(root, filename)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                    except Exception:
                        file_size = 0
                    
                    # 分类文件
                    if ext in extensions or ext in DEFAULT_VIDEO_EXTENSIONS:
                        result.video_files += 1
                        file_type = "video"
                    elif ext in DEFAULT_IMAGE_EXTENSIONS:
                        result.image_files += 1
                        file_type = "image"
                    elif ext in DEFAULT_AUDIO_EXTENSIONS:
                        result.audio_files += 1
                        file_type = "audio"
                    else:
                        result.other_files += 1
                        file_type = "other"
                        continue  # 跳过不支持的文件类型
                    
                    result.total_files += 1
                    result.total_size_bytes += file_size
                    
                    result.file_list.append({
                        "filename": filename,
                        "path": file_path,
                        "rel_path": os.path.relpath(file_path, library.path),
                        "size": file_size,
                        "type": file_type,
                        "extension": ext
                    })
                
                # 如果不扫描子目录，跳出
                if not library.scan_subdirs:
                    break
                
                # 检查最大文件数限制
                if max_files and result.total_files >= max_files:
                    break
                    
        except Exception as e:
            result.errors.append(f"扫描错误: {e}")
            logger.error(f"扫描素材库失败: {e}")
        
        # 计算扫描时间
        result.scan_duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 更新数据库统计
        if update_stats and not result.errors:
            library.total_assets = result.total_files
            library.total_size_bytes = result.total_size_bytes
            library.last_scan_at = datetime.utcnow()
            self.db.commit()
        
        return result

    # ========================================
    # 项目关联管理
    # ========================================
    
    def assign_library_to_project(
        self,
        project_id: str,
        library_id: int,
        is_primary: bool = False,
        priority: int = 0
    ) -> Dict[str, Any]:
        """将素材库分配给项目"""
        from models.asset_library import AssetLibrary, ProjectLibraryMapping
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        # 检查库是否存在
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return {"success": False, "error": "素材库不存在"}
        
        # 检查是否已关联
        existing = self.db.query(ProjectLibraryMapping).filter(
            ProjectLibraryMapping.project_id == project_id,
            ProjectLibraryMapping.library_id == library_id
        ).first()
        
        if existing:
            # 更新现有关联
            existing.is_primary = is_primary
            existing.priority = priority
            self.db.commit()
            return {"success": True, "message": "关联已更新", "mapping": existing.to_dict()}
        
        # 如果设为主库，取消其他主库
        if is_primary:
            self.db.query(ProjectLibraryMapping).filter(
                ProjectLibraryMapping.project_id == project_id,
                ProjectLibraryMapping.is_primary == True
            ).update({"is_primary": False})
        
        # 创建新关联
        mapping = ProjectLibraryMapping(
            project_id=project_id,
            library_id=library_id,
            is_primary=is_primary,
            priority=priority
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        return {"success": True, "message": "关联已创建", "mapping": mapping.to_dict()}
    
    def remove_library_from_project(
        self,
        project_id: str,
        library_id: int
    ) -> Dict[str, Any]:
        """从项目移除素材库"""
        from models.asset_library import ProjectLibraryMapping
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        deleted = self.db.query(ProjectLibraryMapping).filter(
            ProjectLibraryMapping.project_id == project_id,
            ProjectLibraryMapping.library_id == library_id
        ).delete()
        
        self.db.commit()
        
        if deleted:
            return {"success": True, "message": "关联已移除"}
        else:
            return {"success": False, "error": "关联不存在"}
    
    def get_project_libraries(
        self,
        project_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """获取项目关联的素材库"""
        from models.asset_library import AssetLibrary, ProjectLibraryMapping
        
        if not self.db:
            return []
        
        query = self.db.query(AssetLibrary, ProjectLibraryMapping).join(
            ProjectLibraryMapping,
            AssetLibrary.id == ProjectLibraryMapping.library_id
        ).filter(
            ProjectLibraryMapping.project_id == project_id
        )
        
        if active_only:
            query = query.filter(AssetLibrary.is_active == True)
        
        query = query.order_by(
            ProjectLibraryMapping.is_primary.desc(),
            ProjectLibraryMapping.priority
        )
        
        results = []
        for library, mapping in query.all():
            lib_dict = library.to_dict()
            lib_dict["is_primary"] = mapping.is_primary
            lib_dict["priority"] = mapping.priority
            lib_dict["is_accessible"] = self.check_path_accessible(library.path)
            results.append(lib_dict)
        
        return results
    
    def get_active_libraries_for_search(
        self,
        project_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取用于搜索的活动素材库
        
        如果指定了项目ID，返回项目关联的库
        否则返回所有激活的库
        """
        if project_id:
            libraries = self.get_project_libraries(project_id, active_only=True)
            if libraries:
                return libraries
        
        # 回退到所有激活的库
        return self.list_libraries(active_only=True)
    
    # ========================================
    # 快捷方法
    # ========================================
    
    def get_default_library(self) -> Optional[Dict[str, Any]]:
        """获取默认素材库"""
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return None
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.is_default == True,
            AssetLibrary.is_active == True
        ).first()
        
        return library.to_dict() if library else None
    
    def set_default_library(self, library_id: int) -> Dict[str, Any]:
        """设置默认素材库"""
        return self.update_library(library_id, is_default=True)
    
    def toggle_library_active(self, library_id: int) -> Dict[str, Any]:
        """切换素材库激活状态"""
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return {"success": False, "error": "素材库不存在"}
        
        library.is_active = not library.is_active
        library.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "success": True,
            "is_active": library.is_active,
            "message": f"素材库已{'激活' if library.is_active else '禁用'}"
        }

    # ========================================
    # 与现有 Asset 系统集成
    # ========================================
    
    def get_library_assets(
        self,
        library_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取素材库中的素材（从现有 Asset 表）
        
        通过 file_path 前缀匹配素材库路径
        """
        from models.asset_library import AssetLibrary
        from database import Asset
        
        if not self.db:
            return []
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return []
        
        # 通过路径前缀匹配
        assets = self.db.query(Asset).filter(
            Asset.file_path.like(f"{library.path}%")
        ).offset(offset).limit(limit).all()
        
        return [
            {
                "id": a.id,
                "filename": a.filename,
                "file_path": a.file_path,
                "mime_type": a.mime_type,
                "processing_status": a.processing_status,
                "tags": a.tags,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in assets
        ]
    
    def count_library_assets(self, library_id: int) -> int:
        """统计素材库中的素材数量"""
        from models.asset_library import AssetLibrary
        from database import Asset
        
        if not self.db:
            return 0
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return 0
        
        return self.db.query(Asset).filter(
            Asset.file_path.like(f"{library.path}%")
        ).count()
    
    def sync_library_stats(self, library_id: int) -> Dict[str, Any]:
        """
        同步素材库统计信息
        
        从 Asset 表统计已索引的素材数量
        """
        from models.asset_library import AssetLibrary
        
        if not self.db:
            return {"success": False, "error": "数据库未连接"}
        
        library = self.db.query(AssetLibrary).filter(
            AssetLibrary.id == library_id
        ).first()
        
        if not library:
            return {"success": False, "error": "素材库不存在"}
        
        # 统计已索引素材
        indexed_count = self.count_library_assets(library_id)
        
        # 更新统计
        library.indexed_assets = indexed_count
        library.is_indexed = indexed_count > 0
        library.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "success": True,
            "indexed_assets": indexed_count,
            "total_assets": library.total_assets,
            "index_percentage": (indexed_count / library.total_assets * 100) if library.total_assets > 0 else 0
        }
    
    def search_in_libraries(
        self,
        query: str,
        library_ids: List[int] = None,
        project_id: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        在指定素材库中搜索
        
        集成现有的搜索服务
        """
        # 获取要搜索的库
        if library_ids:
            libraries = [self.get_library(lid) for lid in library_ids]
            libraries = [l for l in libraries if l]
        elif project_id:
            libraries = self.get_project_libraries(project_id)
        else:
            libraries = self.list_libraries(active_only=True)
        
        if not libraries:
            return []
        
        # 获取库路径
        library_paths = [l["path"] for l in libraries]
        
        # 调用现有搜索服务
        try:
            from services.search_service import get_search_service
            search_service = get_search_service()
            
            # 搜索并过滤结果
            results = search_service.search(query, limit=limit * 2)
            
            # 过滤只返回指定库中的素材
            filtered_results = []
            for result in results:
                file_path = result.get("file_path", "")
                for lib_path in library_paths:
                    if file_path.startswith(lib_path):
                        filtered_results.append(result)
                        break
                
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    # ========================================
    # 从 .env 导入现有配置
    # ========================================
    
    def import_from_env(self) -> Dict[str, Any]:
        """
        从 .env 文件导入现有的 ASSET_ROOT 配置
        
        自动创建素材库记录
        """
        asset_root = os.getenv("ASSET_ROOT")
        
        if not asset_root:
            return {"success": False, "error": "ASSET_ROOT 未配置"}
        
        # 检查是否已存在
        from models.asset_library import AssetLibrary
        
        if self.db:
            existing = self.db.query(AssetLibrary).filter(
                AssetLibrary.path == asset_root
            ).first()
            
            if existing:
                return {
                    "success": True,
                    "message": "素材库已存在",
                    "library": existing.to_dict()
                }
        
        # 创建新库
        result = self.create_library(
            name="主素材库",
            path=asset_root,
            description="从 .env ASSET_ROOT 导入",
            path_type="network" if asset_root.startswith("\\\\") or ":" in asset_root else "local",
            is_default=True,
            tags=["imported", "main"]
        )
        
        return result
    
    def get_env_config(self) -> Dict[str, Any]:
        """获取当前 .env 配置"""
        return {
            "ASSET_ROOT": os.getenv("ASSET_ROOT", ""),
            "STORAGE_ROOT": os.getenv("STORAGE_ROOT", ""),
            "NETWORK_DRIVE": os.getenv("NETWORK_DRIVE", ""),
            "NETWORK_DRIVE_NAME": os.getenv("NETWORK_DRIVE_NAME", ""),
        }


# 全局服务实例
_asset_library_service: Optional[AssetLibraryService] = None


def get_asset_library_service(db: Session = None) -> AssetLibraryService:
    """获取素材库管理服务实例"""
    global _asset_library_service
    if _asset_library_service is None:
        _asset_library_service = AssetLibraryService(db)
    elif db:
        _asset_library_service.set_db(db)
    return _asset_library_service
