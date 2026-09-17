"""
AI Navigator — Interactive Chat Endpoints
Routes chat messages to the selected AI tool's API proxy.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.tool import Tool
from schemas.chat_schema import ChatRequest, ChatResponse
from services.chat_service import execute_chat

router = APIRouter(prefix="/api/chat", tags=["AI Chat Interaction"])


@router.post("", response_model=ChatResponse)
async def chat_with_tool(
    chat_in: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Interact with an AI tool directly through AI Navigator.
    Validates API availability and proxies messages securely via the backend.
    """
    # 1. Fetch Tool from Database
    tool = db.query(Tool).filter(Tool.id == chat_in.tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Tool with ID {chat_in.tool_id} not found."
        )

    # 2. Verify API Support
    if tool.api_available == "no":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Direct interaction is not available for {tool.name}. "
                f"Please visit the official website: {tool.website}"
            )
        )

    # 3. Validate Message History
    if not chat_in.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat history cannot be empty."
        )

    # 4. Proxy Chat Execution
    try:
        response = await execute_chat(
            tool=tool,
            messages=chat_in.messages,
            model_override=chat_in.model
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with {tool.name} API: {str(e)}"
        )