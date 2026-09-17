"""
AI Navigator — AI Tools Management Endpoints
Public endpoints for listing and viewing tools; Admin-restricted endpoints for CRUD operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models.tool import Tool
from models.user import User
from schemas.tool_schema import ToolCreate, ToolUpdate, ToolResponse
from middleware.auth_middleware import get_current_admin_user

router = APIRouter(prefix="/api/tools", tags=["AI Tools"])


@router.get("", response_model=List[ToolResponse])
def list_tools(
    category: Optional[str] = Query(None, description="Filter tools by category"),
    pricing: Optional[str] = Query(None, description="Filter by pricing model (free, freemium, paid)"),
    search: Optional[str] = Query(None, description="Search tools by name or description keyword"),
    active_only: bool = Query(True, description="Only return active tools"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of AI tools with optional filtering by category, pricing, active status, or keyword search.
    """
    query = db.query(Tool)

    if active_only:
        query = query.filter(Tool.active == True)
    
    if category and category != "all":
        query = query.filter(Tool.category == category.lower())

    if pricing and pricing != "all":
        query = query.filter(Tool.pricing == pricing.lower())

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (Tool.name.ilike(search_term)) | 
            (Tool.description.ilike(search_term))
        )

    return query.order_by(Tool.quality_rating.desc()).all()


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full details for a single AI tool by its database ID.
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Tool with ID {tool_id} not found."
        )
    return tool


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def create_tool(
    tool_in: ToolCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Register a new AI tool. Requires Administrator privileges.
    """
    # Check for name uniqueness
    existing = db.query(Tool).filter(Tool.name.ilike(tool_in.name.strip())).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A tool named '{tool_in.name}' already exists."
        )

    # Convert Pydantic model to SQLAlchemy instance
    new_tool = Tool(**tool_in.model_dump())
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)

    return new_tool


@router.put("/{tool_id}", response_model=ToolResponse)
def update_tool(
    tool_id: int,
    tool_in: ToolUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Update an existing AI tool's metadata or status. Requires Administrator privileges.
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Tool with ID {tool_id} not found."
        )

    # Partial update: only apply fields that were explicitly provided
    update_data = tool_in.model_dump(exclude_unset=True)
    
    # If updating name, check for duplicate conflicts
    if "name" in update_data and update_data["name"]:
        name_conflict = db.query(Tool).filter(
            Tool.name.ilike(update_data["name"].strip()),
            Tool.id != tool_id
        ).first()
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another tool with the name '{update_data['name']}' already exists."
            )

    for field, value in update_data.items():
        setattr(tool, field, value)

    db.commit()
    db.refresh(tool)
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Permanently remove an AI tool from the database. Requires Administrator privileges.
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Tool with ID {tool_id} not found."
        )

    db.delete(tool)
    db.commit()
    return None