import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.config import settings

BOT_PATTERNS = [
    re.compile(r"\[bot\]", re.IGNORECASE),
    re.compile(r"bot$", re.IGNORECASE),
    re.compile(r"-(ci|bot)$", re.IGNORECASE),
    re.compile(r"^(codecov|dependabot|github-actions|renovate|sonarcloud|stale|jenkins)", re.IGNORECASE),
]

KNOWN_BOT_ACCOUNTS = {
    "codecov",
    "dependabot[bot]",
    "dependabot",
    "github-actions[bot]",
    "github-actions",
    "renovate[bot]",
    "renovate",
    "sonarcloud[bot]",
    "stale[bot]",
}


def is_bot_account(username: Optional[str], account_id: Optional[str] = None) -> bool:
    """Detects whether a user account or comment author is an automated bot."""
    if not username and not account_id:
        return False

    name_to_check = (username or "").strip().lower()
    id_to_check = (account_id or "").strip().lower()

    if name_to_check in KNOWN_BOT_ACCOUNTS or id_to_check in KNOWN_BOT_ACCOUNTS:
        return True

    for pattern in BOT_PATTERNS:
        if pattern.search(name_to_check) or pattern.search(id_to_check):
            return True

    return False


@dataclass
class ReviewQualificationResult:
    has_review: bool
    review_date: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    review_type: Optional[str] = None  # FORMAL_REVIEW, INLINE_DIFF, GENERAL_COMMENT
    confidence_tier: Optional[str] = None  # HIGH, MEDIUM
    is_bot_filtered: bool = False
    first_bot_event_date: Optional[datetime] = None
    label: str = "Awaiting Review"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_review": self.has_review,
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "review_type": self.review_type,
            "confidence_tier": self.confidence_tier,
            "is_bot_filtered": self.is_bot_filtered,
            "first_bot_event_date": (
                self.first_bot_event_date.isoformat() if self.first_bot_event_date else None
            ),
            "label": self.label,
        }


def extract_qualifying_review(
    pr_author_id: str,
    pr_author_name: str,
    comments: List[Dict[str, Any]],
    tool_reviews: Optional[List[Dict[str, Any]]] = None,
    exclude_bots: Optional[bool] = None,
    include_normal_comments: Optional[bool] = None,
) -> ReviewQualificationResult:
    """
    Identifies the first genuine qualifying human review event for a pull request.
    Strictly filters author self-comments and automated bot messages.
    """
    should_exclude_bots = exclude_bots if exclude_bots is not None else settings.EXCLUDE_BOTS
    allow_normal = (
        include_normal_comments
        if include_normal_comments is not None
        else settings.INCLUDE_NORMAL_COMMENTS_AS_REVIEW
    )

    candidates: List[Dict[str, Any]] = []
    bot_event_detected = False
    first_bot_dt: Optional[datetime] = None

    # 1. Process formal GitHub tool reviews if available
    if tool_reviews:
        for r in tool_reviews:
            reviewer_name = r.get("user_name", "")
            reviewer_id = str(r.get("user_id", ""))
            state = (r.get("state") or "").upper()
            submitted_at = r.get("submitted_at")

            if not submitted_at:
                continue

            # Check bot
            if should_exclude_bots and is_bot_account(reviewer_name, reviewer_id):
                bot_event_detected = True
                if not first_bot_dt or submitted_at < first_bot_dt:
                    first_bot_dt = submitted_at
                continue

            # Check author self-review
            if reviewer_name.lower() == pr_author_name.lower() or reviewer_id == str(pr_author_id):
                continue

            if state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED"):
                candidates.append({
                    "date": submitted_at,
                    "reviewer_id": reviewer_id,
                    "reviewer_name": reviewer_name,
                    "review_type": f"FORMAL_REVIEW_{state}",
                    "confidence_tier": "HIGH",
                    "label": f"Formal Review ({state})",
                })

    # 2. Process domain layer pull_request_comments
    for c in comments:
        commenter_id = str(c.get("account_id") or "")
        commenter_name = str(c.get("author_name") or commenter_id)
        c_type = (c.get("type") or "NORMAL").upper()
        created_date = c.get("created_date")

        if not created_date:
            continue

        # Check bot
        if should_exclude_bots and is_bot_account(commenter_name, commenter_id):
            bot_event_detected = True
            if not first_bot_dt or created_date < first_bot_dt:
                first_bot_dt = created_date
            continue

        # Check author self-comment
        if commenter_id == str(pr_author_id) or commenter_name.lower() == pr_author_name.lower():
            continue

        if c_type in ("REVIEW", "DIFF"):
            candidates.append({
                "date": created_date,
                "reviewer_id": commenter_id,
                "reviewer_name": commenter_name,
                "review_type": "INLINE_DIFF" if c_type == "DIFF" else "FORMAL_REVIEW",
                "confidence_tier": "HIGH",
                "label": "Inline Code Review" if c_type == "DIFF" else "Formal Review Summary",
            })
        elif c_type == "NORMAL" and allow_normal:
            candidates.append({
                "date": created_date,
                "reviewer_id": commenter_id,
                "reviewer_name": commenter_name,
                "review_type": "GENERAL_COMMENT",
                "confidence_tier": "MEDIUM",
                "label": "Non-Author Discussion Comment",
            })

    if not candidates:
        return ReviewQualificationResult(
            has_review=False,
            is_bot_filtered=bot_event_detected,
            first_bot_event_date=first_bot_dt,
            label="Awaiting Qualifying Review",
        )

    # Sort candidates by date to select the earliest qualifying human review
    candidates.sort(key=lambda x: x["date"])
    first_review = candidates[0]

    return ReviewQualificationResult(
        has_review=True,
        review_date=first_review["date"],
        reviewer_id=first_review["reviewer_id"],
        reviewer_name=first_review["reviewer_name"],
        review_type=first_review["review_type"],
        confidence_tier=first_review["confidence_tier"],
        is_bot_filtered=bot_event_detected,
        first_bot_event_date=first_bot_dt,
        label=first_review["label"],
    )
