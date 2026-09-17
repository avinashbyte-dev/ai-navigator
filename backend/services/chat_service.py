"""
AI Navigator — Chat Proxy Service
Routes user messages securely to authorized AI provider APIs.
"""

import logging
from typing import List, Optional
from openai import OpenAI
from config import settings
from models.tool import Tool
from schemas.chat_schema import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

# Initialize OpenAI client if key is present
client: Optional[OpenAI] = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


async def execute_chat(
    tool: Tool, 
    messages: List[ChatMessage], 
    model_override: Optional[str] = None
) -> ChatResponse:
    """
    Executes a chat completion against the selected AI tool's official API.
    Provides automated fallbacks if the API key is not configured in development.
    """
    if tool.api_available == "no":
        raise ValueError(f"Direct API interaction is not supported for {tool.name}.")

    # Format incoming message list for standard OpenAI/LLM chat completion format
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

    # Handle OpenAI-supported tools or generic LLM proxy
    if client:
        selected_model = model_override or ("gpt-4o" if "gpt-4" in tool.name.lower() else "gpt-3.5-turbo")
        
        # System instruction giving the AI context of its persona
        system_instruction = {
            "role": "system",
            "content": f"You are interacting through AI Navigator as {tool.name}. Provide helpful, accurate, and concise responses tailored to the user's task."
        }
        
        # Prepend system instruction if one isn't provided by user
        if not any(m["role"] == "system" for m in formatted_messages):
            formatted_messages.insert(0, system_instruction)

        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=1000
            )
            reply_text = response.choices[0].message.content or ""
            
            return ChatResponse(
                tool_id=tool.id,
                tool_name=tool.name,
                reply=reply_text,
                model_used=selected_model
            )
        except Exception as e:
            logger.error(f"Error communicating with AI provider API: {e}")
            raise RuntimeError(f"AI Provider error: {str(e)}")

    # Fallback simulation for local development without an active OpenAI API key
    latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "Hello")
    simulated_reply = (
        f"[Simulation Mode — {tool.name}]\n\n"
        f"I received your request: \"{latest_user_msg}\"\n\n"
        f"To enable live AI completions, add your OPENAI_API_KEY to backend/.env."
    )

    return ChatResponse(
        tool_id=tool.id,
        tool_name=tool.name,
        reply=simulated_reply,
        model_used="simulator-mode"
    )