from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

# Standard evaluation anchor time (Monday 11:30 AM local Asia/Kolkata = 06:00 UTC)
# Using a relative anchor based on current time or fixed date ensures reproducible tests
NOW_ANCHOR = datetime(2026, 10, 19, 6, 0, 0, tzinfo=timezone.utc)  # A Monday at 11:30 AM IST (UTC 06:00)

SYNTHETIC_REPOS = [
    {
        "id": "github:GithubRepo:1:apache/devlake-core",
        "name": "apache/devlake-core",
        "url": "https://github.com/apache/devlake",
        "description": "Core backend pipeline, migration engine, and plugin runtime [SYNTHETIC DATA]",
    },
    {
        "id": "github:GithubRepo:1:apache/devlake-github-plugin",
        "name": "apache/devlake-github-plugin",
        "url": "https://github.com/apache/devlake/plugins/github",
        "description": "GitHub REST & GraphQL API data collector and normalizer [SYNTHETIC DATA]",
    },
    {
        "id": "github:GithubRepo:1:apache/devlake-config-ui",
        "name": "apache/devlake-config-ui",
        "url": "https://github.com/apache/devlake/config-ui",
        "description": "Administrative web UI for connections, projects, and scopes [SYNTHETIC DATA]",
    },
    {
        "id": "github:GithubRepo:1:apache/devlake-docs",
        "name": "apache/devlake-docs",
        "url": "https://github.com/apache/devlake/docs",
        "description": "Documentation website, tutorials, and schema specs [SYNTHETIC DATA]",
    },
]


def generate_synthetic_dataset(anchor_dt: datetime = NOW_ANCHOR) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generates a deterministic, realistic suite of synthetic repositories, pull requests,
    comments, and reviews to evaluate all edge cases.
    """
    pull_requests = []
    comments = []
    tool_reviews = []

    # --------------------------------------------------------------------------
    # 1. Historical Completed PRs (To establish valid baselines for each repo)
    # --------------------------------------------------------------------------
    # Each repo gets 15 historical merged PRs with varying pickup times
    for repo_idx, repo in enumerate(SYNTHETIC_REPOS):
        repo_id = repo["id"]
        # Core repo has longer pickup times; docs repo has very fast pickup times
        base_pickup_hours = [4.0, 6.0, 5.0, 2.0][repo_idx]

        for i in range(1, 16):
            pr_id = f"{repo_id}:PR_HIST_{i}"
            created_dt = anchor_dt - timedelta(days=25 - i, hours=i % 6)
            review_dt = created_dt + timedelta(hours=base_pickup_hours + (i % 4) * 1.5)
            merged_dt = review_dt + timedelta(hours=12)

            author_id = f"user_{10 + (i % 5)}"
            reviewer_id = f"user_{30 + (i % 3)}"

            pull_requests.append({
                "id": pr_id,
                "base_repo_id": repo_id,
                "title": f"[SYNTHETIC] Historical feature improvement #{i} in {repo['name']}",
                "status": "MERGED",
                "author_id": author_id,
                "author_name": f"contributor_{author_id}",
                "created_date": created_dt,
                "merged_date": merged_dt,
                "closed_date": merged_dt,
                "additions": 50 + (i * 20),
                "deletions": 10 + (i * 5),
                "comment_count": 3,
                "commit_count": 2,
            })

            # Qualifying review comment
            comments.append({
                "id": f"comment:hist:{pr_id}:1",
                "pull_request_id": pr_id,
                "account_id": reviewer_id,
                "author_name": f"reviewer_{reviewer_id}",
                "created_date": review_dt,
                "type": "REVIEW",
                "review_id": f"rev_hist_{i}",
                "body": "Looks solid! LGTM.",
            })

    # --------------------------------------------------------------------------
    # 2. Active Open PRs (Target Edge Cases & Bottlenecks)
    # --------------------------------------------------------------------------

    # PR 1: The Classic Weekend Bridge Edge Case
    # Created Friday at 18:00 IST (UTC 12:30). Anchor is Monday 11:30 IST (UTC 06:00).
    # Calendar wait = ~65 hours!
    # Business wait (09:30-18:30 IST) = 0.5h Friday + 2.0h Monday = 2.5 business hours!
    # Result: Well within 8.0h SLA! Naive calendar falsely alarms; Business-hours engine keeps it HEALTHY.
    p1_created = anchor_dt - timedelta(days=2, hours=17, minutes=30)  # Friday 18:00 IST
    pull_requests.append({
        "id": "github:GithubRepo:1:apache/devlake-core:PR_WEEKEND_BRIDGE",
        "base_repo_id": "github:GithubRepo:1:apache/devlake-core",
        "title": "[SYNTHETIC] Refactor MySQL connection pool keepalive (Weekend Bridge Test)",
        "status": "OPEN",
        "author_id": "user_dev_1",
        "author_name": "developer_alice",
        "created_date": p1_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 85,
        "deletions": 14,
        "comment_count": 0,
        "commit_count": 1,
    })

    # PR 2: Severe Weekday SLA Breach (Critical Bottleneck)
    # Created 3 business days ago (Wednesday morning at 10:00 IST)
    # Business wait = ~21.5 business hours (> 260% of 8h SLA). Priority score should be CRITICAL (>75).
    p2_created = anchor_dt - timedelta(days=4, hours=25, minutes=30)  # Wednesday 10:00 IST
    pull_requests.append({
        "id": "github:GithubRepo:1:apache/devlake-core:PR_SEVERE_BREACH",
        "base_repo_id": "github:GithubRepo:1:apache/devlake-core",
        "title": "[SYNTHETIC] Fix deadlock during parallel DORA metric transformation",
        "status": "OPEN",
        "author_id": "user_dev_2",
        "author_name": "developer_bob",
        "created_date": p2_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 450,
        "deletions": 120,
        "comment_count": 1,
        "commit_count": 4,
    })

    # PR 3: Compact Bugfix Waiting Long (High Urgency Quick-Win)
    # 35 lines changed, created Thursday at 11:00 IST (~11.5 business hours wait).
    # Small size + SLA breach gives it high priority score.
    p3_created = anchor_dt - timedelta(days=3, hours=24, minutes=30)  # Thursday 11:00 IST
    pull_requests.append({
        "id": "github:GithubRepo:1:apache/devlake-github-plugin:PR_QUICK_WIN",
        "base_repo_id": "github:GithubRepo:1:apache/devlake-github-plugin",
        "title": "[SYNTHETIC] Fix GraphQL pagination cursor off-by-one error",
        "status": "OPEN",
        "author_id": "user_dev_3",
        "author_name": "developer_charlie",
        "created_date": p3_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 28,
        "deletions": 7,
        "comment_count": 0,
        "commit_count": 1,
    })

    # PR 4: Bot & Author Contamination Test Case
    # Created Thursday afternoon. Has comments from `codecov[bot]` at T+45s and from author at T+10m.
    # NO human review yet. Native DevLake records pickup = 45s. Our engine correctly unmasks true delay!
    p4_created = anchor_dt - timedelta(days=3, hours=20)  # Thursday 15:30 IST
    p4_id = "github:GithubRepo:1:apache/devlake-github-plugin:PR_BOT_CONTAMINATED"
    pull_requests.append({
        "id": p4_id,
        "base_repo_id": "github:GithubRepo:1:apache/devlake-github-plugin",
        "title": "[SYNTHETIC] Add support for GitHub Enterprise Server PAT validation",
        "status": "OPEN",
        "author_id": "user_dev_4",
        "author_name": "developer_dan",
        "created_date": p4_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 140,
        "deletions": 30,
        "comment_count": 2,
        "commit_count": 2,
    })
    # Bot comment
    comments.append({
        "id": f"comment:{p4_id}:bot",
        "pull_request_id": p4_id,
        "account_id": "codecov[bot]",
        "author_name": "codecov[bot]",
        "created_date": p4_created + timedelta(seconds=45),
        "type": "NORMAL",
        "body": "Codecov report: 88.4% coverage. No impact on head commit.",
    })
    # Author self-comment
    comments.append({
        "id": f"comment:{p4_id}:author",
        "pull_request_id": p4_id,
        "account_id": "user_dev_4",
        "author_name": "developer_dan",
        "created_date": p4_created + timedelta(minutes=10),
        "type": "NORMAL",
        "body": "Verified locally against GHE v3.11 testbed.",
    })

    # PR 5: Draft / WIP PR Opened 16 business hours ago
    # Marked [Draft] in title. Should receive 0 points for readiness, keeping priority low.
    p5_created = anchor_dt - timedelta(days=3, hours=26)
    pull_requests.append({
        "id": "github:GithubRepo:1:apache/devlake-config-ui:PR_DRAFT_WIP",
        "base_repo_id": "github:GithubRepo:1:apache/devlake-config-ui",
        "title": "[Draft] WIP: Experimental React Flow pipeline visualizer",
        "status": "OPEN",
        "author_id": "user_dev_5",
        "author_name": "developer_elena",
        "created_date": p5_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 620,
        "deletions": 80,
        "comment_count": 0,
        "commit_count": 5,
    })

    # PR 6: Freshly Created PR (Healthy Window)
    # Created 1.0 hour ago Monday morning at 10:30 IST. Business wait = 1.0h. HEALTHY.
    p6_created = anchor_dt - timedelta(hours=1)
    pull_requests.append({
        "id": "github:GithubRepo:1:apache/devlake-docs:PR_FRESH_HEALTHY",
        "base_repo_id": "github:GithubRepo:1:apache/devlake-docs",
        "title": "[SYNTHETIC] Update installation guide for Windows 11 PowerShell bypass",
        "status": "OPEN",
        "author_id": "user_dev_6",
        "author_name": "developer_fiona",
        "created_date": p6_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 15,
        "deletions": 4,
        "comment_count": 0,
        "commit_count": 1,
    })

    # PR 7: Open PR That HAS Received A Qualifying Review (Already picked up)
    # Created Friday morning, reviewed Friday afternoon.
    # Should NOT appear in active unreviewed queue!
    p7_created = anchor_dt - timedelta(days=3, hours=5)
    p7_reviewed = p7_created + timedelta(hours=3)
    p7_id = "github:GithubRepo:1:apache/devlake-core:PR_ALREADY_REVIEWED"
    pull_requests.append({
        "id": p7_id,
        "base_repo_id": "github:GithubRepo:1:apache/devlake-core",
        "title": "[SYNTHETIC] Upgrade Go runtime dependencies to patch CVE-2024",
        "status": "OPEN",
        "author_id": "user_dev_7",
        "author_name": "developer_george",
        "created_date": p7_created,
        "merged_date": None,
        "closed_date": None,
        "additions": 12,
        "deletions": 12,
        "comment_count": 1,
        "commit_count": 1,
    })
    comments.append({
        "id": f"comment:{p7_id}:review",
        "pull_request_id": p7_id,
        "account_id": "user_reviewer_lead",
        "author_name": "lead_reviewer",
        "created_date": p7_reviewed,
        "type": "REVIEW",
        "review_id": "rev_formal_7",
        "body": "Approved! Clean dependency bumps.",
    })

    return {
        "repos": SYNTHETIC_REPOS,
        "pull_requests": pull_requests,
        "comments": comments,
        "tool_reviews": tool_reviews,
    }

