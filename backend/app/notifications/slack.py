import json
import time
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings
from app.logger import logger, redact_sensitive


def format_slack_payload(
    pr_id: str,
    pr_title: str,
    repo_name: str,
    author_name: str,
    business_waiting_hours: float,
    calendar_waiting_hours: float,
    sla_target_hours: float,
    priority_score: int,
    priority_level: str,
    factors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Formats an explainable Slack webhook payload."""
    ratio_pct = int((business_waiting_hours / sla_target_hours) * 100) if sla_target_hours > 0 else 0
    emoji = "🚨" if priority_level == "CRITICAL" else ("⚠️" if priority_level == "HIGH" else "ℹ️")

    factor_text = "\n".join([f"• *{f.get('name')}*: {f.get('reason')} (+{f.get('score')} pts)" for f in factors])

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Review SLA Breach: {repo_name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Pull Request:* <https://github.com/|{pr_title}>\n*Author:* `{author_name}` | *Repository:* `{repo_name}`",
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Business Wait:* {business_waiting_hours:.1f}h ({ratio_pct}% of {sla_target_hours:.0f}h SLA)",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Wall-Clock Wait:* {calendar_waiting_hours:.1f}h",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Priority Score:* {priority_score}/100 (`{priority_level}`)",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Status:* Awaiting First Qualifying Review",
                },
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Bottleneck Urgency Rationale:*\n{factor_text}",
            },
        },
        {"type": "divider"},
    ]

    return {
        "text": f"{emoji} PR Review SLA Breach in {repo_name}: {pr_title} ({business_waiting_hours:.1f} business hours waiting)",
        "blocks": blocks,
    }


def send_slack_notification(
    payload: Dict[str, Any],
    webhook_url: Optional[str] = None,
    dry_run: Optional[bool] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Dispatches a Slack incoming webhook with dry-run support, token redaction, and retry logic.
    """
    url = webhook_url or settings.SLACK_WEBHOOK_URL
    is_dry_run = dry_run if dry_run is not None else settings.ALERT_DRY_RUN

    if is_dry_run or not url:
        logger.info(
            f"[DRY_RUN ALERT] Slack webhook would be dispatched (url={redact_sensitive(url or 'NONE')}):\n"
            f"{json.dumps(payload, indent=2)}"
        )
        return {
            "status": "DRY_RUN",
            "sent": False,
            "message": "Alert evaluated and logged in dry-run mode (no outbound HTTP call).",
            "payload": payload,
        }

    # Live delivery with retries
    headers = {"Content-Type": "application/json"}
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Slack alert successfully dispatched on attempt {attempt}")
                return {
                    "status": "SUCCESS",
                    "sent": True,
                    "status_code": response.status_code,
                    "message": "Alert successfully delivered to Slack.",
                }
        except Exception as exc:
            logger.warning(
                f"Slack alert delivery attempt {attempt}/{max_retries} failed: {redact_sensitive(str(exc))}"
            )
            if attempt < max_retries:
                time.sleep(1.0 * attempt)
            else:
                logger.error(f"Slack alert delivery failed permanently after {max_retries} attempts.")
                return {
                    "status": "FAILED",
                    "sent": False,
                    "error": redact_sensitive(str(exc)),
                    "message": "Slack alert delivery failed after multiple retries.",
                }

    return {"status": "FAILED", "sent": False, "message": "Unknown error in Slack notifier."}
