"""
AI Navigator — Search History Model
Database table definition for recording user searches and recommendation results.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Optional foreign key — allows tracking both guest and logged-in searches
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Query and detected context
    query = Column(Text, nullable=False)
    detected_category = Column(String(50), nullable=False)
    detected_intent = Column(JSON, nullable=False)  # Stores the full intent snapshot
    
    # Matched outcome
    best_tool_name = Column(String(100), nullable=False)
    best_tool_id = Column(Integer, nullable=True)
    match_score = Column(Integer, nullable=False)
    
    # Timestamp
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Inverse relationship to User
    user = relationship("User", back_populates="history_entries")

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, user_id={self.user_id}, query='{self.query[:20]}...', score={self.match_score})>"