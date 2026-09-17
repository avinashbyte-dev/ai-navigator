"""
Pydantic schemas for Intent Classification, Recommendations, and Tool Comparison.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from .tool_schema import ToolResponse


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)


class DetectedIntent(BaseModel):
    category: str
    secondary_category: Optional[str] = None
    purpose: str
    skill_level: str
    budget: str
    output_type: str
    priority: str = "quality"


class ScoreBreakdown(BaseModel):
    task_score: int
    capability_score: int
    skill_score: int
    budget_score: int
    ease_score: int


class ToolMatch(BaseModel):
    tool: ToolResponse
    overall_score: int
    scores: ScoreBreakdown
    reasons: List[str]
    limitations: List[str]


class SearchResponse(BaseModel):
    query: str
    intent: DetectedIntent
    best_match: ToolMatch
    alternatives: List[ToolMatch]


class CompareRequest(BaseModel):
    tool_ids: List[int] = Field(..., min_length=2, max_length=4)


class CompareResponse(BaseModel):
    tools: List[ToolResponse]
    summary: str