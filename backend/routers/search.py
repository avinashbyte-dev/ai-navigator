"""
AI Navigator — Search & Recommendation Endpoints
Processes natural language queries, classifies intent, ranks tools, and logs history.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.tool import Tool
from models.user import User
from models.history import SearchHistory
from schemas.search_schema import SearchRequest, SearchResponse
from services.intent_engine import analyze_intent
from services.recommender import rank_tools
from middleware.auth_middleware import get_optional_current_user

router = APIRouter(prefix="/api/search", tags=["Search & Recommendation"])


@router.post("", response_model=SearchResponse)
def search_and_recommend(
    search_in: SearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Main recommendation endpoint.
    1. Analyzes user task intent (category, budget, skill level, output type).
    2. Fetches all active tools from SQLite.
    3. Calculates multi-factor match scores and generates transparent reasoning.
    4. Automatically records search history for guest or authenticated users.
    """
    clean_query = search_in.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    # 1. Analyze Intent
    intent = analyze_intent(clean_query)

    # 2. Query Active Tools
    active_tools = db.query(Tool).filter(Tool.active == True).all()
    if not active_tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active AI tools found in the database. Please initialize the database with seed data."
        )

    # 3. Score & Rank Tools
    best_match, alternatives = rank_tools(active_tools, intent)
    if not best_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find suitable tool recommendations for this query."
        )

    # 4. Record to Search History
    history_entry = SearchHistory(
        user_id=current_user.id if current_user else None,
        query=clean_query,
        detected_category=intent.category,
        detected_intent=intent.model_dump(),
        best_tool_name=best_match.tool.name,
        best_tool_id=best_match.tool.id,
        match_score=best_match.overall_score
    )
    db.add(history_entry)
    db.commit()

    return SearchResponse(
        query=clean_query,
        intent=intent,
        best_match=best_match,
        alternatives=alternatives
    )