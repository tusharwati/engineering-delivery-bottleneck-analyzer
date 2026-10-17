from sqlalchemy import create_engine
from app.database.schema_checker import verify_devlake_schema


def test_schema_checker_healthy(in_memory_devlake_engine):
    """Tests schema check against seeded DevLake database."""
    result = verify_devlake_schema(in_memory_devlake_engine)
    assert result.status == "HEALTHY"
    assert "pull_requests" in result.tables_found
    assert "pull_request_comments" in result.tables_found
    assert "repos" in result.tables_found
    assert len(result.missing_tables) == 0


def test_schema_checker_missing_tables():
    """Tests schema check against empty database."""
    empty_engine = create_engine("sqlite:///:memory:")
    result = verify_devlake_schema(empty_engine)
    assert result.status == "INCOMPATIBLE"
    assert "pull_requests" in result.missing_tables
    assert len(result.missing_tables) == 3

