"""
AI Navigator — AI Tool Model
Database table definition for AI tools in the system.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from database import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), index=True, nullable=False)
    
    # JSON-serialized list fields
    subcategories = Column(JSON, default=list, nullable=False)
    capabilities = Column(JSON, default=list, nullable=False)
    target_users = Column(JSON, default=list, nullable=False)
    
    # Categorical fields
    skill_level = Column(String(20), default="all", nullable=False)        # beginner, intermediate, advanced, all
    pricing = Column(String(20), default="freemium", nullable=False)       # free, freemium, paid, enterprise
    api_available = Column(String(10), default="no", nullable=False)       # yes, no, limited
    
    # Text lists
    strengths = Column(JSON, default=list, nullable=False)
    weaknesses = Column(JSON, default=list, nullable=False)
    
    # Platform & URL
    website = Column(String(255), nullable=False)
    platform = Column(String(100), default="Web", nullable=False)
    
    # Input/Output modalities
    input_types = Column(JSON, default=lambda: ["text"], nullable=False)
    output_types = Column(JSON, default=lambda: ["text"], nullable=False)
    
    # Metric ratings (1 - 10)
    quality_rating = Column(Integer, default=7, nullable=False)
    ease_rating = Column(Integer, default=7, nullable=False)
    speed_rating = Column(Integer, default=7, nullable=False)
    
    # Status flags
    active = Column(Boolean, default=True, index=True, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', category='{self.category}', active={self.active})>"