"""Project-related database models."""

from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class Project(BaseModel):
    """Project model representing a film/video project."""
    __tablename__ = "projects"
    
    title = Column(String(255), nullable=False)
    logline = Column(Text)
    synopsis = Column(Text)
    script_raw = Column(Text)
    characters = Column(JSON)  # Store character data as JSON
    specs = Column(JSON)  # Store project specs as JSON
    current_stage = Column(String(50), default="ANALYSIS")
    
    # Relationships
    beats = relationship("Beat", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("ProjectAsset", back_populates="project", cascade="all, delete-orphan")


class Beat(BaseModel):
    """Beat model representing a visual moment in the script."""
    __tablename__ = "beats"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON)  # Store TagSchema as JSON
    duration = Column(Float, default=2.0)
    user_notes = Column(Text)
    main_asset_id = Column(UUID(as_uuid=True), ForeignKey("project_assets.id"))
    
    # Relationships
    project = relationship("Project", back_populates="beats")
    main_asset = relationship("ProjectAsset", foreign_keys=[main_asset_id])


class Character(BaseModel):
    """Character model for project characters."""
    __tablename__ = "characters"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="Extra")  # Protagonist, Antagonist, Supporting, Extra
    description = Column(Text)
    traits = Column(JSON)  # Store traits as JSON array
    avatar_url = Column(String(500))
    
    # Relationships
    project = relationship("Project")