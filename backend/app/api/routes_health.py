from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database.devlake_session import engine_devlake, get_devlake_db
from app.database.schema_checker import verify_devlake_schema

router = APIRouter(tags=["Health & Status"])


@router.get("/health", summary="Basic Health Check")
@router.get("/api/health", summary="API Health Check")
def health_check(db: Session = Depends(get_devlake_db)):
    """
    Performs real-time health verification of the service and DevLake database connectivity.
    """
    db_connected = False
    db_error = None

    try:
        db.execute(text("SELECT 1;"))
        db_connected = True
    except Exception as exc:
        db_error = str(exc)

    resp_data = {
        "service": "engineering-delivery-bottleneck-analyzer",
        "status": "UP" if db_connected else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pinned_devlake_version": "v1.0.2",
        "database_connected": db_connected,
        "database_url_dialect": engine_devlake.dialect.name,
        "timezone": settings.TIMEZONE,
        "working_schedule": f"{settings.WORK_START_TIME} - {settings.WORK_END_TIME} ({settings.WORK_DAYS})",
        "review_sla_hours": settings.REVIEW_SLA_HOURS,
    }

    if not db_connected:
        resp_data["database_error"] = db_error
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=resp_data)

    return resp_data


@router.get("/api/schema-check", summary="DevLake Schema Pre-Flight Inspection")
def schema_check():
    """
    Validates that required Apache DevLake domain and tool tables/columns exist.
    """
    result = verify_devlake_schema(engine_devlake)
    return result.to_dict()

