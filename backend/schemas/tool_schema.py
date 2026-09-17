"""
Pydantic schemas for AI Tool management (CRUD).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    category: str
    subcategories: List[str] = []
    capabilities: List[str] = []
    target_users: List[str] = []
    skill_level: str = "all"        # beginner, intermediate, advanced, all
    pricing: str = "freemium"       # free, freemium, paid, enterprise
    strengths: List[str] = []
    weaknesses: List[str] = []
    api_available: str = "no"       # yes, no, limited
    website: str
    platform: str = "Web"
    input_types: List[str] = ["text"]
    output_types: List[str] = ["text"]
    quality_rating: int = Field(default=7, ge=1, le=10)
    ease_rating: int = Field(default=7, ge=1, le=10)
    speed_rating: int = Field(default=7, ge=1, le=10)
    active: bool = True


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    target_users: Optional[List[str]] = None
    skill_level: Optional[str] = None
    pricing: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    api_available: Optional[str] = None
    website: Optional[str] = None
    platform: Optional[str] = None
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    quality_rating: Optional[int] = Field(default=None, ge=1, le=10)
    ease_rating: Optional[int] = Field(default=None, ge=1, le=10)
    speed_rating: Optional[int] = Field(default=None, ge=1, le=10)
    active: Optional[bool] = None


class ToolResponse(ToolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int