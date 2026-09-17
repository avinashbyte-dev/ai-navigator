"""
AI Navigator — Recommendation & Scoring Engine
Calculates multi-factor match scores and generates transparent reasoning.
"""

from typing import List, Dict, Tuple, Optional
from models.tool import Tool
from schemas.search_schema import DetectedIntent, ToolMatch, ScoreBreakdown
from schemas.tool_schema import ToolResponse

DEFAULT_WEIGHTS = {
    "task": 0.35,
    "capability": 0.25,
    "skill": 0.15,
    "budget": 0.15,
    "ease": 0.10
}


def _calculate_task_score(tool: Tool, intent: DetectedIntent) -> int:
    if tool.category == intent.category:
        return 95
    if intent.category in (tool.subcategories or []):
        return 80
    if intent.secondary_category and (
        tool.category == intent.secondary_category or 
        intent.secondary_category in (tool.subcategories or [])
    ):
        return 65
    return 20


def _calculate_capability_score(tool: Tool, intent: DetectedIntent) -> int:
    target_category = intent.category.lower()
    tool_caps = [c.lower() for c in (tool.capabilities or [])]
    matches = sum(1 for cap in tool_caps if target_category in cap or any(word in cap for word in target_category.split("-")))
    return min(95, 50 + (matches * 15))


def _calculate_skill_score(tool: Tool, intent: DetectedIntent) -> int:
    if tool.skill_level == "all" or intent.skill_level == "any":
        return 90
    if tool.skill_level == intent.skill_level:
        return 95
    adjacent = {
        "beginner": ["intermediate"],
        "intermediate": ["beginner", "advanced"],
        "advanced": ["intermediate"]
    }
    if tool.skill_level in adjacent.get(intent.skill_level, []):
        return 60
    return 35


def _calculate_budget_score(tool: Tool, intent: DetectedIntent) -> int:
    if intent.budget == "any":
        return 85
    if intent.budget == "free preferred":
        if tool.pricing == "free":
            return 100
        if tool.pricing == "freemium":
            return 80
        return 30
    if intent.budget == "paid acceptable":
        return 90
    return 75


def _calculate_ease_score(tool: Tool) -> int:
    return min(100, max(0, tool.ease_rating * 10))


def generate_reasons(tool: Tool, intent: DetectedIntent, scores: ScoreBreakdown) -> List[str]:
    reasons = []
    if scores.task_score >= 80:
        reasons.append(f"Strong match for {intent.category.replace('-', ' ').title()} tasks")
    if scores.skill_score >= 80:
        reasons.append(f"Well-suited for {intent.skill_level} skill levels")
    if scores.budget_score >= 80:
        reasons.append(f"Fits your budget preference ({tool.pricing.capitalize()})")
    if scores.ease_score >= 80:
        reasons.append("High ease-of-use rating with minimal setup required")
    if tool.api_available == "yes":
        reasons.append("Official API available for direct platform integration")
    if tool.quality_rating >= 8:
        reasons.append(f"High output quality rating ({tool.quality_rating}/10)")
    if not reasons:
        reasons.append("Matches your stated technical requirements")
    return reasons


def generate_limitations(tool: Tool) -> List[str]:
    limitations = []
    if tool.weaknesses:
        limitations.extend([w.capitalize() for w in tool.weaknesses[:3]])
    if tool.pricing in ["paid", "enterprise"]:
        limitations.append("Requires a paid subscription for regular use")
    elif tool.pricing == "freemium":
        limitations.append("Advanced features and higher usage limits may require a paid plan")
    if tool.api_available == "no":
        limitations.append("Direct in-app interaction is currently unavailable")
    return limitations


def score_single_tool(
    tool: Tool, 
    intent: DetectedIntent, 
    weights: Optional[Dict[str, float]] = None
) -> ToolMatch:
    active_weights = weights or DEFAULT_WEIGHTS
    scores = ScoreBreakdown(
        task_score=_calculate_task_score(tool, intent),
        capability_score=_calculate_capability_score(tool, intent),
        skill_score=_calculate_skill_score(tool, intent),
        budget_score=_calculate_budget_score(tool, intent),
        ease_score=_calculate_ease_score(tool)
    )
    overall_raw = (
        scores.task_score * active_weights["task"] +
        scores.capability_score * active_weights["capability"] +
        scores.skill_score * active_weights["skill"] +
        scores.budget_score * active_weights["budget"] +
        scores.ease_score * active_weights["ease"]
    )
    overall_score = min(99, max(1, round(overall_raw)))

    return ToolMatch(
        tool=ToolResponse.model_validate(tool),
        overall_score=overall_score,
        scores=scores,
        reasons=generate_reasons(tool, intent, scores),
        limitations=generate_limitations(tool)
    )


def rank_tools(
    tools: List[Tool], 
    intent: DetectedIntent, 
    limit: int = 5
) -> Tuple[Optional[ToolMatch], List[ToolMatch]]:
    if not tools:
        return None, []
    matches = [score_single_tool(tool, intent) for tool in tools]
    matches.sort(key=lambda m: m.overall_score, reverse=True)
    best_match = matches[0] if matches else None
    alternatives = matches[1:limit] if len(matches) > 1 else []
    return best_match, alternatives