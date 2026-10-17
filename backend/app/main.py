from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_alerts import router as alerts_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_health import router as health_router
from app.config import settings
from app.database.app_session import init_app_db
from app.database.devlake_session import engine_devlake
from app.database.schema_checker import verify_devlake_schema
from app.fixtures.seed_mock_devlake import seed_mock_devlake_database
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifespan handler.
    Initializes SQLite app store, auto-seeds mock data if needed, and checks schema.
    """
    logger.info("Initializing Engineering Delivery Bottleneck Analyzer...")

    # 1. Initialize local SQLite app store
    init_app_db()

    # 2. If using default local SQLite DevLake database and file does not exist, seed automatically
    if settings.DEVLAKE_DB_URL.startswith("sqlite:///"):
        db_path = settings.DEVLAKE_DB_URL.replace("sqlite:///", "")
        if not Path(db_path).exists():
            logger.info("Local mock DevLake database not found. Auto-seeding synthetic testbed...")
            seed_mock_devlake_database(settings.DEVLAKE_DB_URL)

    # 3. Perform pre-flight schema inspection
    schema_status = verify_devlake_schema(engine_devlake)
    logger.info(f"DevLake Pre-flight check: {schema_status.status} ({schema_status.message})")

    yield

    logger.info("Shutting down Engineering Delivery Bottleneck Analyzer.")


app = FastAPI(
    title="Engineering Delivery Bottleneck Analyzer",
    description=(
        "Companion analytics and context-aware review SLA service for Apache DevLake v1.0.2. "
        "Calculates business-hours review delay, qualifies reviews, benchmarks repositories, "
        "and prioritizes review queue bottlenecks with full explainability."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(alerts_router)


@app.get("/")
def root_index():
    return {
        "service": "Engineering Delivery Bottleneck Analyzer",
        "version": "0.1.0",
        "status": "ONLINE",
        "documentation": "/docs",
        "health": "/api/health",
        "pinned_devlake_version": "v1.0.2",
    }

