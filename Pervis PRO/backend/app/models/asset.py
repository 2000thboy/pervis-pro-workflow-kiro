"""Asset-related database models."""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import BaseModel


class ProjectAsset(BaseModel):
    """Project asset model for video/image files."""
    __tablename__ = "project_assets"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    source = Column(String(50), default="upload")  # upload, external, generated, local
    tags = Column(JSON)  # Store tags as JSON
    metadata = Column(JSON)  # Store VideoMetadata as JSON
    
    # File paths (relative to configured roots)
    original_path = Column(String(500))
    proxy_path = Column(String(500))
    thumbnail_path = Column(String(500))
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, done, error
    
    # Relationships
    project = relationship("Project", back_populates="assets")
    vectors = relationship("AssetVector", back_populates="asset", cascade="all, delete-orphan")


class AssetVector(BaseModel):
    """Vector embeddings for asset content."""
    __tablename__ = "asset_vectors"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("project_assets.id"), nullable=False)
    vector = Column(Vector(384))  # MiniLM-L6-v2 dimension
    content_type = Column(String(50), nullable=False)  # transcript, description, tags
    content_text = Column(Text)  # Original text that was vectorized
    
    # Relationships
    asset = relationship("ProjectAsset", back_populates="vectors")