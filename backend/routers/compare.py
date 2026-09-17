"""
AI Navigator — Comparison Endpoints
Compares 2 to 4 selected AI tools and generates feature summaries.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.tool import Tool
from schemas.search_schema import CompareRequest, CompareResponse
from schemas.tool_schema import ToolResponse

router = APIRouter(prefix="/api/compare", tags=["Comparison"])


def _generate_comparison_summary(tools: List[Tool]) -> str:
    """Generates an analytical summary highlighting relative strengths and trade-offs."""
    if not tools:
        return ""

    best_quality = max(tools, key=lambda t: t.quality_rating)
    easiest = max(tools, key=lambda t: t.ease_rating)
    fastest = max(tools, key=lambda t: t.speed_rating)

    free_or_freemium = [t for t in tools if t.pricing in ["free", "freemium"]]
    accessible_tool = free_or_freemium[0] if free_or_freemium else tools[0]

    summary_lines = [
        f"• Output Quality: {best_quality.name} holds the highest quality rating ({best_quality.quality_rating}/10) among the selected tools.",
        f"• Ease of Use: {easiest.name} offers the most accessible learning curve ({easiest.ease_rating}/10 ease rating).",
        f"• Speed & Latency: {fastest.name} provides the fastest turnaround ({fastest.speed_rating}/10 speed rating).",
        f"• Accessibility: {accessible_tool.name} provides the most cost-effective tier ({accessible_tool.pricing.capitalize()})."
    ]
    return "\n".join(summary_lines)


@router.post("", response_model=CompareResponse)
def compare_tools(
    payload: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare 2 to 4 tools side by side.
    Returns full metadata for each tool along with a generated comparative summary.
    """
    # 1. Fetch requested tools
    tools = db.query(Tool).filter(Tool.id.in_(payload.tool_ids), Tool.active == True).all()

    if len(tools) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 valid active tools are required for side-by-side comparison."
        )

    # 2. Convert to Pydantic responses
    tool_responses = [ToolResponse.model_validate(t) for t in tools]

    # 3. Generate summary
    summary = _generate_comparison_summary(tools)

    return CompareResponse(
        tools=tool_responses,
        summary=summary
    )