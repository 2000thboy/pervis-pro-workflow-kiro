"""
素材数据模型
"""
from sqlalchemy import Column, String, Text, Integer, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from .base import BaseModel


class AssetType(Enum):
    """素材类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    MODEL_3D = "model_3d"


class Asset(BaseModel):
    """素材模型"""
    __tablename__ = "assets"
    
    name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    file_size = Column(Integer)
    checksum = Column(String(64))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    
    # 关系
    project = relationship("Project", backref="assets")
    
    def __repr__(self):
        return f"<Asset(name={self.name}, type={self.asset_type})>"