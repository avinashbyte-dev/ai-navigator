"""
AI Navigator — Search History Endpoints
Allows users to retrieve and clear their past recommendations.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import User
from models.history import SearchHistory
from middleware.auth_middleware import get_current_active_user

router = APIRouter(prefix="/api/history", tags=["Search History"])


class HistoryItemResponse(BaseModel):
    id: int
    query: str
    detected_category: str
    best_tool_name: str
    match_score: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[HistoryItemResponse])
def get_user_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve recent search recommendations for the authenticated user (newest first).
    """
    history = db.query(SearchHistory)\
        .filter(SearchHistory.user_id == current_user.id)\
        .order_by(SearchHistory.created_at.desc())\
        .limit(30)\
        .all()
    
    return history


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_user_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete all search history records associated with the authenticated user.
    """
    db.query(SearchHistory)\
        .filter(SearchHistory.user_id == current_user.id)\
        .delete(synchronize_session=False)
    
    db.commit()
    return None