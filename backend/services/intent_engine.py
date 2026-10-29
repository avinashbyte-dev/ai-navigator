"""
AI Navigator — Intent Classification Engine
Analyzes user queries using OpenAI LLMs with deterministic rule-based fallback.
"""

import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings
from schemas.search_schema import DetectedIntent

logger = logging.getLogger(__name__)

def _is_valid_api_key(key: str) -> bool:
    return bool(key and key.strip() and not key.startswith("sk-your-") and len(key) > 20)

client: Optional[OpenAI] = OpenAI(api_key=settings.OPENAI_API_KEY) if _is_valid_api_key(settings.OPENAI_API_KEY) else None

KEYWORD_MAP = {
    "coding": ["code", "coding", "program", "programming", "python", "javascript", "typescript", "java", "c++", "rust", "html", "css", "sql", "debug", "developer", "software", "app development", "learn to code", "practice coding", "algorithm", "git", "backend", "frontend"],
    "writing": ["write", "writing", "essay", "blog", "article", "copywriting", "story", "novel", "content writing", "draft", "proofread", "grammar", "rephrase"],
    "content-creation": ["social media", "instagram", "youtube", "tiktok", "caption", "post", "content", "influencer", "engagement", "viral", "tweet", "linkedin post"],
    "image-generation": ["image", "picture", "photo", "illustration", "art", "draw", "generate image", "visual", "graphic", "cinematic image", "realistic image", "photorealistic", "render", "logo"],
    "video-generation": ["video", "film", "cinematic", "movie", "animation", "clip", "youtube video", "reel", "short film", "avatar video", "text to video"],
    "research": ["research", "paper", "study", "academic", "literature", "citation", "journal", "thesis", "analyze paper", "find papers", "scientific", "fact check"],
    "education": ["learn", "study", "tutor", "explain", "teach", "course", "lesson", "homework", "understand", "concept", "exam", "quiz"],
    "productivity": ["organize", "productivity", "workflow", "notes", "task", "schedule", "plan", "manage", "notion", "efficiency", "automation", "meeting notes"],
    "presentations": ["presentation", "slides", "powerpoint", "pitch", "deck", "keynote", "college presentation", "corporate presentation", "slide show"],
    "data-analysis": ["data", "analyze data", "statistics", "chart", "graph", "spreadsheet", "csv", "dataset", "visualization", "excel", "sql query", "pandas"],
    "music": ["music", "song", "beat", "melody", "compose", "lyrics", "audio track", "instrumental"],
    "audio": ["voice", "speech", "text to speech", "narration", "podcast", "voiceover", "clone voice", "dubbing", "audio editing"],
    "conversation": ["talk", "chat", "conversation", "companion", "bored", "friend", "discuss", "ask questions"],
    "design": ["design", "ui", "ux", "layout", "poster", "flyer", "graphic design", "figma", "wireframe"],
    "marketing": ["marketing", "ad", "advertisement", "campaign", "seo", "email marketing", "funnel", "conversion"],
    "translation": ["translate", "translation", "language", "multilingual", "localize", "spanish", "french", "german"]
}

BUDGET_KEYWORDS = {
    "free preferred": ["free", "no cost", "zero cost", "without paying", "cheap", "open source"],
    "paid acceptable": ["paid", "premium", "pro", "enterprise", "willing to pay", "budget is fine", "best quality"]
}

SKILL_KEYWORDS = {
    "beginner": ["beginner", "new to", "learning", "just starting", "basic", "simple", "easy", "novice", "student"],
    "intermediate": ["intermediate", "some experience", "familiar with", "moderate"],
    "advanced": ["advanced", "expert", "professional", "complex", "powerful", "production", "enterprise", "senior"]
}


def _heuristic_intent_analysis(query: str) -> Dict[str, Any]:
    lower = query.lower()

    category_scores: Dict[str, int] = {}
    for category, keywords in KEYWORD_MAP.items():
        score = sum(len(kw.split()) for kw in keywords if kw in lower)
        if score > 0:
            category_scores[category] = score

    sorted_categories = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    primary_category = sorted_categories[0][0] if sorted_categories else "conversation"
    secondary_category = sorted_categories[1][0] if len(sorted_categories) > 1 else None

    budget = "any"
    for label, terms in BUDGET_KEYWORDS.items():
        if any(term in lower for term in terms):
            budget = label
            break

    skill_level = "any"
    for label, terms in SKILL_KEYWORDS.items():
        if any(term in lower for term in terms):
            skill_level = label
            break

    purpose = "general"
    if any(k in lower for k in ["college", "school", "university", "class", "assignment", "homework"]):
        purpose = "education"
    elif any(k in lower for k in ["business", "corporate", "company", "client", "work", "job"]):
        purpose = "professional"
    elif any(k in lower for k in ["personal", "hobby", "fun", "side project"]):
        purpose = "personal"

    output_mapping = {
        "coding": "code", "writing": "text", "content-creation": "text",
        "image-generation": "image", "video-generation": "video", "music": "audio",
        "audio": "audio", "presentations": "presentation", "data-analysis": "chart", "design": "image"
    }
    output_type = output_mapping.get(primary_category, "text")

    return {
        "category": primary_category,
        "secondary_category": secondary_category,
        "purpose": purpose,
        "skill_level": skill_level,
        "budget": budget,
        "output_type": output_type,
        "priority": "quality"
    }


def _llm_intent_analysis(query: str) -> Optional[Dict[str, Any]]:
    if not client:
        return None

    system_prompt = (
        "You are the intent analysis engine for AI Navigator. "
        "Analyze the user's task request and return a structured JSON object with keys: "
        "category, secondary_category, purpose, skill_level, budget, output_type, priority. "
        "Only output valid JSON."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
    except Exception as e:
        logger.warning(f"OpenAI API intent parsing failed: {e}. Falling back to heuristic classifier.")
    
    return None


def analyze_intent(query: str) -> DetectedIntent:
    result = _llm_intent_analysis(query)
    if not result:
        result = _heuristic_intent_analysis(query)
    
    return DetectedIntent(
        category=result.get("category", "conversation"),
        secondary_category=result.get("secondary_category"),
        purpose=result.get("purpose", "general"),
        skill_level=result.get("skill_level", "any"),
        budget=result.get("budget", "any"),
        output_type=result.get("output_type", "text"),
        priority=result.get("priority", "quality")
    )