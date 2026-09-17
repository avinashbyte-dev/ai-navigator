"""
AI Navigator — Configuration
Loads all settings from environment variables and the .env file.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()


class Settings:
    """
    Central configuration class.
    Every setting has a fallback default so the app does not crash
    if a variable is missing from .env during development.
    """

    # ---- App ----
    APP_NAME: str = os.getenv("APP_NAME", "AI Navigator")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ---- Database ----
    # Save the database in the parent folder to prevent auto-reloader loops
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///../ai_navigator.db")

    # ---- JWT Authentication ----
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # ---- OpenAI ----
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ---- CORS ----
    # Comma-separated list of allowed frontend origins
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")
    ]


# Single global instance — import this everywhere instead of creating new objects
settings = Settings()