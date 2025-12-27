# -*- coding: utf-8 -*-
"""
素材库配置模型

扩展现有 DAM 系统，支持多素材库管理，类似 Eagle 的库管理功能：
- 配置多个素材库（支持本地路径和局域网路径）
- 给每个库命名和备注
- 在项目中选择激活哪些库
- 支持库的启用/禁用状态
- 与现有 Asset 表关联

Requirements: 素材库管理系统
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

# 使用现有的 Base
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class AssetLibrary(Base):
    """
    素材库配置表
    
    与现有 Asset 表通过 library_id 关联
    """
    __tablename__ = "asset_libraries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="库名称")
    description = Column(Text, nullable=True, comment="库描述/备注")
    
    # 路径配置
    path = Column(String(500), nullable=False, comment="库路径（支持本地和网络路径）")
    path_type = Column(String(20), default="local", comment="路径类型: local/network/smb/nfs")
    
    # 网络配置（用于局域网路径）
    network_host = Column(String(200), nullable=True, comment="网络主机地址")
    network_share = Column(String(200), nullable=True, comment="共享名称")
    network_username = Column(String(100), nullable=True, comment="网络用户名")
    network_password = Column(String(200), nullable=True, comment="网络密码（加密存储）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_default = Column(Boolean, default=False, comment="是否为默认库")
    is_indexed = Column(Boolean, default=False, comment="是否已索引")
    
    # 统计信息
    total_assets = Column(Integer, default=0, comment="总素材数")
    indexed_assets = Column(Integer, default=0, comment="已索引素材数")
    total_size_bytes = Column(Integer, default=0, comment="总大小（字节）")
    last_scan_at = Column(DateTime, nullable=True, comment="最后扫描时间")
    last_index_at = Column(DateTime, nullable=True, comment="最后索引时间")

    # 配置选项
    scan_subdirs = Column(Boolean, default=True, comment="是否扫描子目录")
    file_extensions = Column(JSON, default=list, comment="支持的文件扩展名")
    exclude_patterns = Column(JSON, default=list, comment="排除的路径模式")
    
    # 元数据
    extra_metadata = Column("metadata", JSON, default=dict, comment="额外元数据")
    tags = Column(JSON, default=list, comment="库标签")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AssetLibrary(id={self.id}, name='{self.name}', path='{self.path}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "path_type": self.path_type,
            "network_host": self.network_host,
            "network_share": self.network_share,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_indexed": self.is_indexed,
            "total_assets": self.total_assets,
            "indexed_assets": self.indexed_assets,
            "total_size_bytes": self.total_size_bytes,
            "total_size_display": self._format_size(self.total_size_bytes),
            "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
            "last_index_at": self.last_index_at.isoformat() if self.last_index_at else None,
            "scan_subdirs": self.scan_subdirs,
            "file_extensions": self.file_extensions or [],
            "exclude_patterns": self.exclude_patterns or [],
            "metadata": self.extra_metadata or {},
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.2f} {units[i]}"


class ProjectLibraryMapping(Base):
    """项目-素材库关联表"""
    __tablename__ = "project_library_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), nullable=False, index=True, comment="项目ID")
    library_id = Column(Integer, nullable=False, index=True, comment="素材库ID")
    is_primary = Column(Boolean, default=False, comment="是否为主库")
    priority = Column(Integer, default=0, comment="优先级（数字越小优先级越高）")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProjectLibraryMapping(project_id='{self.project_id}', library_id={self.library_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "library_id": self.library_id,
            "is_primary": self.is_primary,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
