import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.database.models_app import BaseApp


def get_app_engine():
    """Initializes and returns the SQLite engine for application state."""
    db_url = settings.APP_DB_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        parent_dir = Path(db_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    return create_engine(
        db_url,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        pool_pre_ping=True,
    )


engine_app = get_app_engine()
SessionLocalApp = sessionmaker(autocommit=False, autoflush=False, bind=engine_app)


def init_app_db():
    """Creates SQLite tables for alert deduplication and audit logging."""
    BaseApp.metadata.create_all(bind=engine_app)


def get_app_db():
    """FastAPI dependency for accessing the application SQLite session."""
    db: Session = SessionLocalApp()
    try:
        yield db
    finally:
        db.close()

