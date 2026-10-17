from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.logger import logger


def get_devlake_engine():
    """
    Initializes and returns the read-only SQLAlchemy engine for Apache DevLake.
    Supports SQLite (for local mock/seed), MySQL, and PostgreSQL.
    """
    db_url = settings.DEVLAKE_DB_URL

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        parent_dir = Path(db_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

    # For MySQL or PostgreSQL connections:
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
    )


engine_devlake = get_devlake_engine()
SessionLocalDevLake = sessionmaker(autocommit=False, autoflush=False, bind=engine_devlake)


def get_devlake_db():
    """FastAPI dependency for accessing the DevLake database (Read-Only)."""
    db: Session = SessionLocalDevLake()
    try:
        yield db
    finally:
        db.close()

