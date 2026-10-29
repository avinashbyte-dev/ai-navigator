from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import shutil
from config import settings

# If on Vercel, ensure seed db is copied to /tmp if not already present
if os.getenv("VERCEL"):
    tmp_db_file = "/tmp/ai_navigator.db"
    src_db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_navigator.db")
    if not os.path.exists(tmp_db_file) and os.path.exists(src_db_file):
        try:
            shutil.copyfile(src_db_file, tmp_db_file)
        except Exception:
            pass

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False


engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG 
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session for a single request,
    then guarantees it is closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Creates all database tables defined in the models if they do not exist yet.
    Called once on application startup.
    """
    # Import all models here so SQLAlchemy registers them before table creation
    import models.user
    import models.tool
    import models.history

    Base.metadata.create_all(bind=engine)