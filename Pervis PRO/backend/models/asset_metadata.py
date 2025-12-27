# -*- coding: utf-8 -*-
"""
AssetMetadata 数据模型
管理素材的缓存路径和版本信息
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class AssetMetadata(Base):
    """素材元数据表 - 管理缓存和代理文件"""
    __tablename__ = "asset_metadata"
    
    id = Column(String(36), primary_key=True)
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    
    # 原始文件路径
    original_path = Column(Text, nullable=True)
    original_size = Column(Integer, nullable=True)  # 字节
    original_hash = Column(String(64), nullable=True)  # SHA256
    
    # 缩略图路径
    thumbnail_path = Column(Text, nullable=True)
    thumbnail_size = Column(Integer, nullable=True)
    thumbnail_generated_at = Column(DateTime, nullable=True)
    
    # 代理文件路径（低分辨率预览）
    proxy_path = Column(Text, nullable=True)
    proxy_size = Column(Integer, nullable=True)
    proxy_resolution = Column(String(20), nullable=True)  # 如 "720p"
    proxy_generated_at = Column(DateTime, nullable=True)
    
    # 缓存版本控制
    cache_version = Column(Integer, default=1)
    last_verified_at = Column(DateTime, nullable=True)
    is_available = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AssetMetadata(id={self.id}, asset_id={self.asset_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "original_path": self.original_path,
            "original_size": self.original_size,
            "thumbnail_path": self.thumbnail_path,
            "proxy_path": self.proxy_path,
            "proxy_resolution": self.proxy_resolution,
            "cache_version": self.cache_version,
            "is_available": self.is_available,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
