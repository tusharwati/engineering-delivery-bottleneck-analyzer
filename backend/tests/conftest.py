import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.routes_alerts import router as alerts_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_health import router as health_router
from app.config import settings
from app.database.app_session import get_app_db
from app.database.devlake_session import get_devlake_db
from app.database.models_app import BaseApp
from app.fixtures.seed_mock_devlake import BaseDevLake, seed_mock_devlake_database
from app.main import app


@pytest.fixture(scope="session")
def in_memory_devlake_engine():
    """In-memory SQLite engine simulating DevLake database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    BaseDevLake.metadata.create_all(bind=engine)
    seed_mock_devlake_database("sqlite:///:memory:")
    return engine


@pytest.fixture(scope="session")
def in_memory_app_engine():
    """In-memory SQLite engine simulating local app state store."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    BaseApp.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def devlake_db_session(in_memory_devlake_engine):
    """Session for mock DevLake DB."""
    Session = sessionmaker(bind=in_memory_devlake_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app_db_session(in_memory_app_engine):
    """Session for local app state DB."""
    Session = sessionmaker(bind=in_memory_app_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(in_memory_devlake_engine, in_memory_app_engine):
    """FastAPI TestClient with overridden DB dependencies."""
    DevLakeSession = sessionmaker(bind=in_memory_devlake_engine)
    AppSession = sessionmaker(bind=in_memory_app_engine)

    def override_devlake_db():
        s = DevLakeSession()
        try:
            yield s
        finally:
            s.close()

    def override_app_db():
        s = AppSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_devlake_db] = override_devlake_db
    app.dependency_overrides[get_app_db] = override_app_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
