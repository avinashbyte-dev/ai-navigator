"""
Pydantic schemas for direct AI Chat proxy interactions.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    tool_id: int
    messages: List[ChatMessage]
    model: Optional[str] = None


class ChatResponse(BaseModel):
    tool_id: int
    tool_name: str
    reply: str
    model_used: str