from typing import Any, Dict, List
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from app.logger import logger

REQUIRED_TABLES = {
    "pull_requests": [
        "id",
        "base_repo_id",
        "title",
        "status",
        "author_id",
        "author_name",
        "created_date",
    ],
    "pull_request_comments": [
        "id",
        "pull_request_id",
        "account_id",
        "created_date",
    ],
    "repos": [
        "id",
        "name",
    ],
}

OPTIONAL_TABLES = [
    "_tool_github_pull_request_reviews",
    "project_pr_metrics",
]


class SchemaCheckResult:
    def __init__(self):
        self.status: str = "HEALTHY"  # HEALTHY, WARNING, INCOMPATIBLE
        self.database_dialect: str = ""
        self.tables_found: List[str] = []
        self.missing_tables: List[str] = []
        self.missing_columns: Dict[str, List[str]] = {}
        self.has_tool_reviews: bool = False
        self.message: str = ""
        self.details: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "database_dialect": self.database_dialect,
            "tables_found": self.tables_found,
            "missing_tables": self.missing_tables,
            "missing_columns": self.missing_columns,
            "has_tool_reviews": self.has_tool_reviews,
            "message": self.message,
            "details": self.details,
        }


def verify_devlake_schema(engine: Engine) -> SchemaCheckResult:
    """
    Performs pre-flight inspection of the Apache DevLake schema.
    Verifies that required domain tables and columns exist before metric execution.
    """
    result = SchemaCheckResult()

    try:
        inspector = inspect(engine)
        result.database_dialect = engine.dialect.name
        existing_tables = set(inspector.get_table_names())
        result.tables_found = sorted(list(existing_tables))

        # Check required tables
        for table, required_cols in REQUIRED_TABLES.items():
            if table not in existing_tables:
                result.missing_tables.append(table)
                result.details.append(f"Required table '{table}' is missing from DevLake database.")
            else:
                # Check required columns
                existing_cols = {col["name"] for col in inspector.get_columns(table)}
                missing_for_table = [c for c in required_cols if c not in existing_cols]
                if missing_for_table:
                    result.missing_columns[table] = missing_for_table
                    result.details.append(
                        f"Table '{table}' is missing required columns: {missing_for_table}"
                    )

        # Check optional tool layer tables
        result.has_tool_reviews = "_tool_github_pull_request_reviews" in existing_tables

        if result.missing_tables:
            result.status = "INCOMPATIBLE"
            result.message = (
                f"DevLake schema check failed: Missing {len(result.missing_tables)} required tables. "
                "Ensure DevLake v1.0.2 migrations have executed or seed the mock database."
            )
            logger.warning(result.message)
        elif result.missing_columns:
            result.status = "WARNING"
            result.message = "DevLake schema has missing columns in domain tables."
            logger.warning(result.message)
        else:
            result.status = "HEALTHY"
            result.message = "DevLake schema verified successfully. All required domain tables and columns exist."
            logger.info(result.message)

    except Exception as exc:
        result.status = "INCOMPATIBLE"
        result.message = f"Failed to connect or inspect DevLake database: {str(exc)}"
        result.details.append(str(exc))
        logger.error(result.message)

    return result

