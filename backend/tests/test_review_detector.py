from datetime import datetime, timedelta, timezone
from app.analytics.review_detector import extract_qualifying_review, is_bot_account


def test_is_bot_account():
    """Verifies that automated bots and service accounts are identified."""
    assert is_bot_account("codecov[bot]") is True
    assert is_bot_account("codecov") is True
    assert is_bot_account("dependabot[bot]") is True
    assert is_bot_account("github-actions[bot]") is True
    assert is_bot_account("sonarcloud[bot]") is True
    assert is_bot_account("renovate[bot]") is True
    assert is_bot_account("jenkins-ci") is True
    assert is_bot_account("stale-bot") is True
    # Human developers must NOT be flagged as bots
    assert is_bot_account("alice_dev") is False
    assert is_bot_account("charlie-engineer") is False
    assert is_bot_account("bob") is False


def test_bot_and_author_comment_filtering():
    """
    Tests that bot comments and author comments are discarded,
    and genuine human reviews are selected.
    """
    now = datetime.now(timezone.utc)
    pr_created = now - timedelta(hours=10)

    comments = [
        # 1. Bot comment at T+30 seconds
        {
            "id": "c_bot",
            "account_id": "codecov[bot]",
            "author_name": "codecov[bot]",
            "created_date": pr_created + timedelta(seconds=30),
            "type": "NORMAL",
            "body": "Coverage report: 90%",
        },
        # 2. Author self-comment at T+5 minutes
        {
            "id": "c_author",
            "account_id": "author_123",
            "author_name": "alice_dev",
            "created_date": pr_created + timedelta(minutes=5),
            "type": "NORMAL",
            "body": "Please review this carefully.",
        },
        # 3. Third-party reviewer inline diff review at T+4 hours
        {
            "id": "c_reviewer",
            "account_id": "reviewer_456",
            "author_name": "bob_reviewer",
            "created_date": pr_created + timedelta(hours=4),
            "type": "DIFF",
            "body": "Consider extracting this helper function.",
        },
    ]

    res = extract_qualifying_review(
        pr_author_id="author_123",
        pr_author_name="alice_dev",
        comments=comments,
    )

    assert res.has_review is True
    assert res.reviewer_name == "bob_reviewer"
    assert res.review_type == "INLINE_DIFF"
    assert res.confidence_tier == "HIGH"
    assert res.is_bot_filtered is True
    assert res.review_date == pr_created + timedelta(hours=4)


def test_unreviewed_pr_with_bot_activity():
    """Tests an open PR that only has bot comments and no human review yet."""
    now = datetime.now(timezone.utc)
    comments = [
        {
            "id": "c1",
            "account_id": "github-actions[bot]",
            "author_name": "github-actions[bot]",
            "created_date": now - timedelta(hours=2),
            "type": "NORMAL",
            "body": "Build passed.",
        }
    ]

    res = extract_qualifying_review(
        pr_author_id="author_123",
        pr_author_name="alice_dev",
        comments=comments,
    )

    assert res.has_review is False
    assert res.is_bot_filtered is True
    assert res.review_date is None


def test_tool_reviews_recognition():
    """Tests that formal tool-layer reviews (APPROVED, CHANGES_REQUESTED) are prioritized."""
    now = datetime.now(timezone.utc)
    tool_reviews = [
        {
            "github_id": 999,
            "user_id": "reviewer_789",
            "user_name": "charlie_lead",
            "state": "APPROVED",
            "submitted_at": now - timedelta(hours=1),
            "body": "Ship it!",
        }
    ]

    res = extract_qualifying_review(
        pr_author_id="author_123",
        pr_author_name="alice_dev",
        comments=[],
        tool_reviews=tool_reviews,
    )

    assert res.has_review is True
    assert res.reviewer_name == "charlie_lead"
    assert res.review_type == "FORMAL_REVIEW_APPROVED"
    assert res.confidence_tier == "HIGH"
