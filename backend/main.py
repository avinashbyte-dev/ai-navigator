"""
AI Navigator — Main Application Entry Point
Initializes the FastAPI application, database tables, seed data, CORS, and routers.
"""

import sys
import os
import json
import logging
from contextlib import asynccontextmanager

# Ensure the backend directory is in Python's search path to resolve relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import init_db, SessionLocal
from models.tool import Tool
from models.user import User
from services.auth_service import get_password_hash

# Import Routers
from routers import auth, search, tools, chat, compare, history

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_navigator")


def seed_database(db: Session):
    """
    Populates the database with initial AI tools and a default admin user
    if the database is currently empty.
    """
    # 1. Seed AI Tools
    try:
        tool_count = db.query(Tool).count()
        if tool_count == 0:
            seed_path = os.path.join(os.path.dirname(__file__), "data", "seed_tools.json")
            if os.path.exists(seed_path):
                with open(seed_path, "r", encoding="utf-8") as f:
                    tools_data = json.load(f)
                    for item in tools_data:
                        new_tool = Tool(**item)
                        db.add(new_tool)
                db.commit()
                logger.info(f"Successfully seeded {len(tools_data)} AI tools into database.")
            else:
                logger.warning(f"Seed file not found at: {seed_path}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding AI tools: {e}")

    # 2. Seed Default Administrator Account
    try:
        admin_user = db.query(User).filter(User.email == "admin@ainavigator.com").first()
        if not admin_user:
            admin = User(
                name="System Admin",
                email="admin@ainavigator.com",
                hashed_password=get_password_hash("admin123456"),
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created: admin@ainavigator.com (password: admin123456)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating default admin user: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that runs startup and shutdown tasks.
    """
    # Startup: Initialize tables and seed records
    logger.info("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} ready.")
    yield
    logger.info("Application shutting down.")


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent AI Recommendation and Unified AI Interaction Platform API",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
# Allows localhost and 127.0.0.1 on any port (like 5500 for Live Server) with cookie/auth support
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(tools.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(history.router)


@app.get("/", tags=["Health Check"])
def root():
    """
    API health check endpoint.
    """
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)