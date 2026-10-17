import os
from pathlib import Path
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
from app.database.app_session import init_app_db
from app.database.schema_checker import verify_devlake_schema
from app.fixtures.synthetic_data import generate_synthetic_dataset
from app.logger import logger

BaseDevLake = declarative_base()


class RepoModel(BaseDevLake):
    __tablename__ = "repos"
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)


class PullRequestModel(BaseDevLake):
    __tablename__ = "pull_requests"
    id = Column(String(255), primary_key=True)
    base_repo_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    status = Column(String(64), default="OPEN")
    author_id = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    created_date = Column(DateTime, nullable=False)
    merged_date = Column(DateTime, nullable=True)
    closed_date = Column(DateTime, nullable=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    commit_count = Column(Integer, default=0)


class PrCommentModel(BaseDevLake):
    __tablename__ = "pull_request_comments"
    id = Column(String(255), primary_key=True)
    pull_request_id = Column(String(255), nullable=False, index=True)
    account_id = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=True)
    created_date = Column(DateTime, nullable=False)
    type = Column(String(64), default="NORMAL")
    review_id = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)


class ToolGitHubReviewModel(BaseDevLake):
    __tablename__ = "_tool_github_pull_request_reviews"
    github_id = Column(Integer, primary_key=True)
    pull_request_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=False)
    state = Column(String(64), nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    body = Column(Text, nullable=True)


def seed_mock_devlake_database(db_url: str = None, engine = None):
    """
    Creates mock DevLake tables and seeds realistic synthetic data.
    Allows zero-dependency local startup without needing live MySQL or Docker.
    """
    if engine is None:
        target_url = db_url or settings.DEVLAKE_DB_URL
        logger.info(f"Seeding mock DevLake database at: {target_url}")

        if target_url.startswith("sqlite:///"):
            db_path = target_url.replace("sqlite:///", "")
            parent_dir = Path(db_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            target_url,
            connect_args={"check_same_thread": False} if "sqlite" in target_url else {},
        )

    # 1. Create tables
    BaseDevLake.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing records to ensure idempotent seeding
        session.query(PrCommentModel).delete()
        session.query(ToolGitHubReviewModel).delete()
        session.query(PullRequestModel).delete()
        session.query(RepoModel).delete()

        # Generate synthetic data
        dataset = generate_synthetic_dataset()

        # Insert repos
        for r in dataset["repos"]:
            session.add(RepoModel(
                id=r["id"],
                name=r["name"],
                url=r["url"],
                description=r["description"],
            ))

        # Insert PRs
        for pr in dataset["pull_requests"]:
            session.add(PullRequestModel(
                id=pr["id"],
                base_repo_id=pr["base_repo_id"],
                title=pr["title"],
                status=pr["status"],
                author_id=pr["author_id"],
                author_name=pr["author_name"],
                created_date=pr["created_date"],
                merged_date=pr["merged_date"],
                closed_date=pr["closed_date"],
                additions=pr["additions"],
                deletions=pr["deletions"],
                comment_count=pr["comment_count"],
                commit_count=pr["commit_count"],
            ))

        # Insert Comments
        for c in dataset["comments"]:
            session.add(PrCommentModel(
                id=c["id"],
                pull_request_id=c["pull_request_id"],
                account_id=c["account_id"],
                author_name=c.get("author_name"),
                created_date=c["created_date"],
                type=c["type"],
                review_id=c.get("review_id"),
                body=c.get("body"),
            ))

        session.commit()
        logger.info(
            f"Successfully seeded mock DevLake: {len(dataset['repos'])} repos, "
            f"{len(dataset['pull_requests'])} PRs, {len(dataset['comments'])} comments."
        )

        # 2. Also initialize local application database
        init_app_db()
        logger.info("Successfully initialized local application database.")

        # 3. Verify schema check
        check = verify_devlake_schema(engine)
        logger.info(f"Schema check result: {check.status} - {check.message}")

    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to seed mock DevLake database: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_mock_devlake_database()
